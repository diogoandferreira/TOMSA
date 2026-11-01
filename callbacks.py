from dash import Output, Input, State, ctx, no_update, html
import os
import glob
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash_leaflet as dl
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache

from config import CONFIG, LOGS_DIR, robot_color, robot_label

LOG_COLUMNS = {
    'header.stamp.secs',
    'header.stamp.nsecs',
    'pose.pose.position.x',
    'pose.pose.position.y',
    'pose.pose.position.z',
    'pose.pose.orientation.x',
    'pose.pose.orientation.y',
    'pose.pose.orientation.z',
    'pose.pose.orientation.w',
    'twist.twist.linear.x',
    'twist.twist.linear.y',
}

CHART_FONT = {'family': 'IBM Plex Sans, Arial, sans-serif', 'size': 12, 'color': '#334155'}
GRID_COLOR = '#e2e8f0'

COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']


# --------------------------------------------------------------------------- utilitários
def style_time_series(figure, y_title, max_time):
    """Eixo X fixo em [0, duração total] para o gráfico não "esticar" durante o replay."""
    axis_style = dict(
        showline=True, linecolor=GRID_COLOR, linewidth=1,
        gridcolor=GRID_COLOR, zeroline=False,
        ticks='outside', tickcolor=GRID_COLOR,
    )
    figure.update_layout(
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        font=CHART_FONT,
        margin=dict(l=65, r=25, b=55, t=25),
        hovermode=False,
        uirevision='time-series',
        xaxis=dict(title=dict(text='Tempo decorrido (s)', standoff=12),
                   range=[0, max(max_time, 0.1)], **axis_style),
        yaxis=dict(title=dict(text=y_title, standoff=12), **axis_style),
    )


@lru_cache(maxsize=8)
def load_log(file_path, modified_time):
    return pd.read_csv(file_path, usecols=lambda column: column in LOG_COLUMNS)


@lru_cache(maxsize=16)
def get_bounds(file_path, modified_time):
    """Limites (min, max) de x, y, z do LOG INTEIRO. Servem para fixar os eixos."""
    df = load_log(file_path, modified_time)

    def span(column):
        if column in df.columns and not df.empty:
            values = pd.to_numeric(df[column], errors='coerce').dropna()
            if len(values):
                return float(values.min()), float(values.max())
        return None

    return span('pose.pose.position.x'), span('pose.pose.position.y'), span('pose.pose.position.z')


def get_sea_level():
    """Cota da superfície do mar = z mais alto de TODOS os logs (referência comum a todos os robots)."""

    tops = []
    for file_path in sorted(glob.glob(str(LOGS_DIR / '*.csv'))):
        bz = get_bounds(file_path, Path(file_path).stat().st_mtime_ns)[2]
        if bz:
            tops.append(bz[1])
    return max(tops, default=0.0)


def get_log_files(selected_value):
    if not selected_value:
        return []
    if selected_value == 'all':
        return sorted(glob.glob(str(LOGS_DIR / '*.csv')))
    return [selected_value]


def get_timestamp_time(df):
    if 'header.stamp.secs' in df.columns:
        timestamps = pd.to_numeric(df['header.stamp.secs'], errors='coerce').to_numpy(dtype=float)
        if 'header.stamp.nsecs' in df.columns:
            nanoseconds = pd.to_numeric(df['header.stamp.nsecs'], errors='coerce').fillna(0).to_numpy(dtype=float)
            timestamps += nanoseconds / 1_000_000_000
        return timestamps - timestamps[0]
    return np.arange(len(df), dtype=float)


def format_duration(seconds):
    total_seconds = max(0, int(seconds))
    minutes, seconds = divmod(total_seconds, 60)
    return f'{minutes:02d}:{seconds:02d}'


def merge_span(current, new):
    """Junta dois intervalos (min, max), ignorando None."""
    if new is None:
        return current
    if current is None:
        return new
    return (min(current[0], new[0]), max(current[1], new[1]))


def collect_bounds(log_files):
    """Limites x, y, z (log inteiro) de um conjunto de ficheiros."""
    full_x = full_y = full_z = None
    for file_path in log_files:
        bx, by, bz = get_bounds(file_path, Path(file_path).stat().st_mtime_ns)
        full_x, full_y, full_z = merge_span(full_x, bx), merge_span(full_y, by), merge_span(full_z, bz)
    return full_x, full_y, full_z


def compute_ranges(full_x, full_y, full_z, sea_z):
    """Intervalos fixos dos eixos: x, y, z do 3D (mar em z=0, no topo) e profundidade."""
    x_range = y_range = None
    depth_range = [0, 55]            # gráfico de profundidade (invertido: 0 em cima)
    z_range_3d = [-55, 2]            # 3D: z normal, mar em z = 0 (o ponto mais alto)

    if full_x:
        pad_x = max((full_x[1] - full_x[0]) * 0.1, 1e-4)
        x_range = [full_x[0] - pad_x, full_x[1] + pad_x]
    if full_y:
        pad_y = max((full_y[1] - full_y[0]) * 0.1, 1e-4)
        y_range = [full_y[0] - pad_y, full_y[1] + pad_y]
    if full_z:
        depths = (sea_z - full_z[1], sea_z - full_z[0])
        d_min, d_max = min(depths[0], 0), max(depths[1], 0)
        pad_z = max((d_max - d_min) * 0.05, 1)
        depth_range = [d_max + pad_z, d_min]
        z_range_3d = [-(d_max + pad_z), -d_min + pad_z * 0.3]   # superfície no topo

    return x_range, y_range, depth_range, z_range_3d


WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3


def geodetic_to_ecef(lat, lon, h):
    lat, lon = np.radians(lat), np.radians(lon)
    n = WGS84_A / np.sqrt(1 - WGS84_E2 * np.sin(lat) ** 2)
    return np.array([(n + h) * np.cos(lat) * np.cos(lon),
                     (n + h) * np.cos(lat) * np.sin(lon),
                     (n * (1 - WGS84_E2) + h) * np.sin(lat)])


def geodetic_to_ned(lat, lon, h, lat0, lon0, h0):
    """Posição (lat, lon, h) em metros norte/este/baixo, com origem em (lat0, lon0, h0)."""
    d = geodetic_to_ecef(lat, lon, h) - geodetic_to_ecef(lat0, lon0, h0)
    p, l = np.radians(lat0), np.radians(lon0)
    north = -np.sin(p) * np.cos(l) * d[0] - np.sin(p) * np.sin(l) * d[1] + np.cos(p) * d[2]
    east = -np.sin(l) * d[0] + np.cos(l) * d[1]
    down = -np.cos(p) * np.cos(l) * d[0] - np.cos(p) * np.sin(l) * d[1] - np.sin(p) * d[2]
    return float(north), float(east), float(down)


def position_at(file_path, t):
    """Última posição (lat, lon, z) do robot até ao instante t."""
    df = load_log(file_path, Path(file_path).stat().st_mtime_ns)
    if df.empty:
        return None
    elapsed = get_timestamp_time(df)
    idx = max(int(np.searchsorted(elapsed, t, side='right')) - 1, 0)
    row = df.iloc[idx]
    z = float(row['pose.pose.position.z']) if 'pose.pose.position.z' in df.columns else 0.0
    return float(row['pose.pose.position.x']), float(row['pose.pose.position.y']), z

def get_origin(): # Descobrir o ponto incial dado e colocar em NED
    cfg = CONFIG['radar']['origin']
    if cfg['lat'] is not None and cfg['lon'] is not None:
        h0 = cfg['h'] if cfg['h'] is not None else get_sea_level()
        return float(cfg['lat']), float(cfg['lon']), float(h0)
    files = sorted(glob.glob(str(LOGS_DIR / '*.csv')))
    first = position_at(files[0], 0) if files else None
    if first is None:
        return None
    return first[0], first[1], get_sea_level()



# --------------------------------------------------------------------------- JS (corre no browser)
# Atualiza só os dados dos traços 3D com Plotly.restyle: o layout e a câmara não são tocados,
# por isso o utilizador pode rodar/fazer zoom à vontade durante a reprodução.
RESTYLE_3D_JS = """
function(data, figure) {
    const nu = window.dash_clientside.no_update;
    if (!data || !data.idx || data.idx.length === 0) { return nu; }
    return new Promise(function(resolve) {
        setTimeout(function() {
            const gd = document.querySelector('#graph-3d-view .js-plotly-plot');
            if (gd && gd.layout && gd.layout.meta === data.key && gd.data && gd.data.length > Math.max.apply(null, data.idx)) {
                Plotly.restyle(gd, {x: data.x, y: data.y, z: data.z}, data.idx);
            }
            resolve(nu);
        }, 0);
    });
}
"""


# --------------------------------------------------------------------------- callbacks
def register_callbacks(app):
    @app.callback(
        Output('timestamp-slider', 'max'),
        Input('dropdown-log-selector', 'value')
    )
    def update_playback_range(selected_value):
        durations = []
        for file_path in get_log_files(selected_value):
            modified_time = Path(file_path).stat().st_mtime_ns
            df = load_log(file_path, modified_time)
            if not df.empty:
                durations.append(float(get_timestamp_time(df)[-1]))
        return max(max(durations, default=0), 0.1)

    @app.callback(
        [Output('timestamp-slider', 'value'),
         Output('playback-interval', 'disabled'),
         Output('playback-button', 'children')],
        [Input('playback-button', 'n_clicks'),
         Input('playback-interval', 'n_intervals'),
         Input('dropdown-log-selector', 'value')],
        [State('timestamp-slider', 'value'),
         State('timestamp-slider', 'max'),
         State('playback-interval', 'disabled'),
         State('speed-selector', 'value')]
    )
    def control_playback(n_clicks, n_intervals, selected_value, current_time, max_time, paused, speed):
        trigger = ctx.triggered_id
        if trigger == 'dropdown-log-selector':
            return 0, True, '▶ Reproduzir'
        if trigger == 'playback-button':
            if paused:
                start_time = 0 if current_time >= max_time else current_time
                return start_time, False, '⏸ Pausar'
            return current_time, True, '▶ Reproduzir'
        if trigger == 'playback-interval':
            step = CONFIG['playback']['interval_ms'] / 1000 * (speed if speed else 1)
            next_time = min(current_time + step, max_time)
            finished = next_time >= max_time
            return next_time, finished, '▶ Reproduzir' if finished else '⏸ Pausar'
        return no_update, no_update, no_update

    # ---- Figura 3D: construída UMA vez por ficheiro selecionado (traços vazios + eixos fixos)
    @app.callback(
        Output('graph-3d-view', 'figure'),
        Input('dropdown-log-selector', 'value')
    )
    def build_3d_figure(selected_value):
        fig = go.Figure()
        if not selected_value:
            return fig

        log_files = get_log_files(selected_value)
        sea_z = get_sea_level()
        full_x, full_y, full_z = collect_bounds(log_files)
        x_range, y_range, _, z_range_3d = compute_ranges(full_x, full_y, full_z, sea_z)
        tick_vals = np.linspace(z_range_3d[0], 0, 5)

        # Ordem fixa: para o robot i, traço 2*i = linha, traço 2*i+1 = marcador da posição atual
        for i, file_path in enumerate(log_files):
            color = robot_color(file_path, i)
            fig.add_trace(go.Scatter3d(x=[], y=[], z=[], mode='lines', name=robot_label(file_path),
                                       line=dict(color=color, width=5), opacity=0.8))
            fig.add_trace(go.Scatter3d(x=[], y=[], z=[], mode='markers', showlegend=False,
                                       marker=dict(size=7, color=color, line=dict(color='#ffffff', width=1))))

        if x_range and y_range:
            fig.add_trace(go.Surface(
                x=x_range, y=y_range, z=[[0, 0], [0, 0]],
                colorscale=[[0, '#0077be'], [1, '#0077be']],
                opacity=0.4, showscale=False, hoverinfo='skip',
                name='Superfície do Mar'
            ))

        axis_style = dict(backgroundcolor='#f8fafc', gridcolor=GRID_COLOR, zerolinecolor='#cbd5e1',
                          showbackground=True, nticks=4, tickformat='.5f')

        fig.update_layout(
            template='plotly_white', paper_bgcolor='#ffffff', plot_bgcolor='#ffffff', font=CHART_FONT,
            meta=selected_value,          # o JS confirma que a figura é a certa antes de atualizar
            uirevision=selected_value,
            scene=dict(
                xaxis=dict(title="Latitude",range=x_range, **axis_style),
                yaxis=dict(title="Longitude",range=y_range, **axis_style),
                zaxis=dict(title="Profundidade",range=z_range_3d, tickvals=tick_vals,
                           ticktext=[f'{-v:.0f}' for v in tick_vals], **axis_style),
                aspectmode='manual',
                aspectratio=dict(x=1.3, y=1.3, z=0.7),
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
            ),
            margin=dict(l=0, r=0, b=0, t=10), showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, bgcolor='rgba(255,255,255,0.75)'),
            hoverlabel=dict(bgcolor='#0f172a', bordercolor='#0f172a', font=dict(color='#ffffff'))
        )
        return fig

    # ---- Atualização dos dados 3D no browser (sem mexer na câmara)
    app.clientside_callback(
        RESTYLE_3D_JS,
        Output('restyle-dummy', 'data'),
        Input('traces3d-store', 'data'),
        Input('graph-3d-view', 'figure'),
    )

    @app.callback(
        [Output('radar-view', 'figure'), Output('radar-distances', 'children')],
        [Input('radar-ref-selector', 'value'), Input('timestamp-slider', 'value')]
    )
    def update_radar(ref_file, current_time):
        fig = go.Figure()
        if ref_file == 'origin':
            ref = get_origin()
        else:
            ref = position_at(ref_file, current_time) if ref_file else None
        
        if ref is None:
            return fig, []

        lat0, lon0, z0 = ref
        items, r_max = [], 10.0
        
        fig.add_trace(go.Scatterpolar(r=[0], theta=[0], mode='markers', hoverinfo='skip',
                                      marker=dict(symbol='star', size=20, color='#ffd34d',
                                                  line=dict(color='#ffffff', width=1))))

        for i, file_path in enumerate(sorted(glob.glob(str(LOGS_DIR / '*.csv')))):
            if file_path == ref_file:
                continue
            pos = position_at(file_path, current_time)
            if pos is None:
                continue

            north, east, dz = geodetic_to_ned(pos[0], pos[1], pos[2], lat0, lon0, z0)  

            horizontal = float(np.hypot(north, east))
            dist_3d = float(np.sqrt(north**2 + east**2 + dz**2))
            azimuth = float((np.degrees(np.arctan2(east, north)) + 360) % 360)   # 0° = norte, sentido horário
            color, name = robot_color(file_path, i), robot_label(file_path)
            r_max = max(r_max, horizontal)

            fig.add_trace(go.Scatterpolar(
                r=[horizontal], theta=[azimuth], mode='markers+text',
                text=[f'{name}<br>{dist_3d:.0f} m'], textposition='top center',
                textfont=dict(color='#ffffff', size=13), hoverinfo='skip',
                marker=dict(size=16, color=color, line=dict(color='#ffffff', width=2))))
            
            items.append(html.Div([
                html.Div(name, className='ts-name', style={'color': color}),
                html.Div(f'Distância 3D: {dist_3d:.1f} m'),
                html.Div(f'Horizontal: {horizontal:.1f} m · Azimute: {azimuth:.0f}°'),
                html.Div(f'Diferença de profundidade: {abs(dz):.1f} m'),
            ], className='ts-item'))

        fig.update_layout(
            paper_bgcolor='#0b1f2a',
            font=dict(family='IBM Plex Sans, Arial, sans-serif', color='#d7f5ec'),
            showlegend=False, margin=dict(l=50, r=50, t=30, b=30),
            polar=dict(
                bgcolor='#0f2d3a',
                angularaxis=dict(direction='clockwise', rotation=90,
                                 tickvals=[0, 90, 180, 270], ticktext=['N', 'E', 'S', 'O'],
                                 gridcolor='#2a6f73', linecolor='#2a6f73',
                                 tickfont=dict(size=15, color='#ffffff')),
                radialaxis=dict(range=[0, r_max * 1.2], ticksuffix=' m',
                                angle=0, tickangle=0, showline=True,
                                gridcolor='#2a6f73', linecolor='#2fe0b0',
                                tickfont=dict(size=12, color='#7fe9c9')),
            ),
        )
        return fig, items


    # ---- Restantes painéis, a cada instante
    @app.callback(
        [Output('trajectory-layer-2d', 'children'),
         Output('traces3d-store', 'data'),
         Output('compass-view', 'figure'),
         Output('graph-depth-view', 'figure'),
         Output('graph-speed-view', 'figure'),
         Output('legend-items-container', 'children'),
         Output('timestamp-items-container', 'children'),
         Output('playback-time-label', 'children')],
        [Input('dropdown-log-selector', 'value'),
         Input('timestamp-slider', 'value'),
         Input('timestamp-slider', 'max')]
    )
    def update_dashboards(selected_value, current_time, max_time):
        if not selected_value:
            return [], None, go.Figure(), go.Figure(), go.Figure(), [], [], '00:00 / 00:00'

        map_elements_2d = []
        fig_depth = go.Figure()
        fig_speed = go.Figure()
        legend_elements = []
        timestamp_elements = []
        store_3d = {'key': selected_value, 'idx': [], 'x': [], 'y': [], 'z': []}

        fig_compass = go.Figure()
        fig_compass.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            scene=dict(
                xaxis=dict(visible=False, range=[-1.2, 1.2]),
                yaxis=dict(visible=False, range=[-1.2, 1.2]),
                zaxis=dict(visible=False, range=[-1.2, 1.2]),
                aspectmode='cube',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            margin=dict(l=0, r=0, b=0, t=0), showlegend=False
        )

        def draw_cad_arrow(fig, name, color, x, y, z):
            fig.add_trace(go.Scatter3d(x=[0, x], y=[0, y], z=[0, z], mode='lines+text', line=dict(color=color, width=6), text=['', name], textfont=dict(color=color, size=14), textposition='top center', hoverinfo='skip'))
            fig.add_trace(go.Cone(x=[x], y=[y], z=[z], u=[x], v=[y], w=[z], sizemode="absolute", sizeref=0.2, anchor="tail", colorscale=[[0, color], [1, color]], showscale=False, hoverinfo='skip'))

        log_files = get_log_files(selected_value)
        sea_z = get_sea_level()
        _, _, depth_range, _ = compute_ranges(*collect_bounds(log_files), sea_z)

        for i, file_path in enumerate(log_files):
            modified_time = Path(file_path).stat().st_mtime_ns
            df = load_log(file_path, modified_time)
            if df.empty:
                continue

            elapsed = get_timestamp_time(df)

            # Tolerância para imprecisões numéricas no instante zero
            time_threshold = 0.001 if current_time == 0 else current_time
            visible = elapsed <= time_threshold

            # Se nenhum ponto for apanhado, força a inclusão do primeiro registo
            if not visible.any():
                visible_df = df.iloc[:1]
                visible_elapsed = np.array([0.0])
            else:
                visible_df = df.loc[visible]
                visible_elapsed = elapsed[visible]

            x_vals = visible_df['pose.pose.position.x'].to_numpy()
            y_vals = visible_df['pose.pose.position.y'].to_numpy()

            z_vals = np.zeros(len(visible_df))
            if 'pose.pose.position.z' in visible_df.columns:
                z_vals = visible_df['pose.pose.position.z'].to_numpy()
            
            depth_vals = sea_z - z_vals 

            speed = None
            if 'twist.twist.linear.x' in visible_df.columns and 'twist.twist.linear.y' in visible_df.columns:
                speed = np.sqrt(visible_df['twist.twist.linear.x'].to_numpy()**2 + visible_df['twist.twist.linear.y'].to_numpy()**2)

            positions_2d = list(zip(x_vals, y_vals))
            
            color = robot_color(file_path, i)
            filename = robot_label(file_path)
            
            map_elements_2d.append(dl.Polyline(positions=positions_2d, color=color, weight=4, opacity=0.9))

            if positions_2d:
                map_elements_2d.append(dl.CircleMarker(center=positions_2d[0], radius=4, color='#ffffff', weight=2, fillColor=color, fillOpacity=1))

                heading = 0
                if len(positions_2d) > 1:
                    lat1, lon1 = positions_2d[-2]
                    lat2, lon2 = positions_2d[-1]
                    heading = np.degrees(np.arctan2(lon2 - lon1, lat2 - lat1))

                arrow_html = f'''
                <div style="transform: rotate({heading}deg); width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0px 0px 2px white) drop-shadow(0px 0px 1px white);">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22V2M5 9l7-7 7 7"/>
                    </svg>
                </div>
                '''

                map_elements_2d.append(dl.DivMarker(
                    position=positions_2d[-1],
                    iconOptions=dict(html=arrow_html, className="", iconSize=[24, 24], iconAnchor=[12, 12]),
                    children=dl.Tooltip(f"Posição atual: {filename}")
                ))

            # Dados 3D: linha (traço 2*i) e marcador da posição atual (traço 2*i+1)
            z_plot = (-depth_vals).tolist()
            store_3d['idx'] += [2 * i, 2 * i + 1]
            store_3d['x'] += [x_vals.tolist(), [float(x_vals[-1])]]
            store_3d['y'] += [y_vals.tolist(), [float(y_vals[-1])]]
            store_3d['z'] += [z_plot, [z_plot[-1]]]

            if len(fig_compass.data) == 0:
                fig_compass.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode='markers', marker=dict(size=0, color='rgba(0,0,0,0)'), hoverinfo='skip'))

            if len(x_vals) > 0 and selected_value != 'all' and 'pose.pose.orientation.x' in visible_df.columns:
                qx, qy = visible_df['pose.pose.orientation.x'].iloc[-1], visible_df['pose.pose.orientation.y'].iloc[-1]
                qz, qw = visible_df['pose.pose.orientation.z'].iloc[-1], visible_df['pose.pose.orientation.w'].iloc[-1]

                R11, R21, R31 = 1 - 2*qy**2 - 2*qz**2, 2*qx*qy + 2*qw*qz, 2*qx*qz - 2*qw*qy
                R12, R22, R32 = 2*qx*qy - 2*qw*qz, 1 - 2*qx**2 - 2*qz**2, 2*qy*qz + 2*qw*qx
                R13, R23, R33 = 2*qx*qz + 2*qw*qy, 2*qy*qz - 2*qw*qx, 1 - 2*qx**2 - 2*qy**2

                draw_cad_arrow(fig_compass, 'X', 'red', R11, R21, R31)
                draw_cad_arrow(fig_compass, 'Y', 'green', R12, R22, R32)
                draw_cad_arrow(fig_compass, 'Z', 'blue', R13, R23, R33)

            legend_elements.append(html.Div([
                html.Span(className='legend-swatch', style={'backgroundColor': color}),
                html.Span(filename),
            ], className='legend-item'))

            if 'header.stamp.secs' in df.columns:
                t0, t1 = df['header.stamp.secs'].iloc[0], df['header.stamp.secs'].iloc[-1]

                def time_format(secs):
                    return datetime.fromtimestamp(float(secs), tz=timezone.utc).strftime('%d/%m/%Y %H:%M:%S')

                timestamp_elements.append(html.Div([
                    html.Div(filename, className='ts-name', style={'color': color}),
                    html.Div(f"Início: {time_format(t0)} UTC"),
                    html.Div(f"Fim: {time_format(t1)} UTC"),
                    html.Div(f"Duração: {int(t1 - t0)/60:.0f} min"),
                ], className='ts-item'))

            fig_depth.add_trace(go.Scatter(x=visible_elapsed, y=depth_vals, mode='lines', name=filename, line=dict(color=color, width=3, shape='spline', smoothing=1.1), opacity=0.8))

            if speed is not None:
                fig_speed.add_trace(go.Scatter(x=visible_elapsed, y=speed, mode='lines', name=filename, line=dict(color=color, width=3, shape='spline', smoothing=1.1)))

        style_time_series(fig_depth, 'Profundidade (m)', current_time)
        style_time_series(fig_speed, 'Velocidade (m/s)', current_time)
        fig_depth.update_yaxes(range=depth_range)

        time_label = f'{format_duration(current_time)} / {format_duration(max_time)}'

        return map_elements_2d, store_3d, fig_compass, fig_depth, fig_speed, legend_elements, timestamp_elements, time_label