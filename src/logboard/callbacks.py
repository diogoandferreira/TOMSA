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

LOGS_DIR = Path(__file__).resolve().parents[2] / 'logs'
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

CHART_FONT = {'family': 'Arial, sans-serif', 'size': 12, 'color': '#334155'}
GRID_COLOR = '#e2e8f0'

def style_time_series(figure, y_title):
    figure.update_layout(
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        font=CHART_FONT,
        margin=dict(l=65, r=25, b=55, t=25),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#0f172a',
            bordercolor='#0f172a',
            font=dict(color='#ffffff')
        ),
        xaxis=dict(
            title=dict(text='Tempo decorrido (s)', standoff=12),
            showline=True,
            linecolor=GRID_COLOR,
            linewidth=1,
            gridcolor=GRID_COLOR,
            zeroline=False,
            ticks='outside',
            tickcolor=GRID_COLOR
        ),
        yaxis=dict(
            title=dict(text=y_title, standoff=12),
            showline=True,
            linecolor=GRID_COLOR,
            linewidth=1,
            gridcolor=GRID_COLOR,
            zeroline=False,
            ticks='outside',
            tickcolor=GRID_COLOR
        )
    )

@lru_cache(maxsize=8)
def load_log(file_path, modified_time):
    return pd.read_csv(file_path, usecols=lambda column: column in LOG_COLUMNS)

#Carrega os ficheiros provenientes do dropdown, para all colcoca todos
def get_log_files(selected_value):
    if not selected_value:
        return []
    if selected_value == 'all':
        return sorted(glob.glob(str(LOGS_DIR / '*.csv')))
    return [selected_value]

# Coloca o timestamp em segundos apartir do primeiro intstante
def get_timestamp_time(df):
    if 'header.stamp.secs' in df.columns:
        timestamps = pd.to_numeric(df['header.stamp.secs'], errors='coerce').to_numpy(dtype=float)
        if 'header.stamp.nsecs' in df.columns:
            nanoseconds = pd.to_numeric(df['header.stamp.nsecs'], errors='coerce').fillna(0).to_numpy(dtype=float)
            timestamps += nanoseconds / 1_000_000_000
        return timestamps - timestamps[0]
    return np.arange(len(df), dtype=float)

#Converte o tempo para o formato mm:ss
def format_duration(seconds):
    total_seconds = max(0, int(seconds))
    minutes, seconds = divmod(total_seconds, 60)
    return f'{minutes:02d}:{seconds:02d}'


def register_callbacks(app):
    @app.callback(  #define o tempo máximo do slider
        Output('timestamp-slider', 'max'),
        Input('dropdown-log-selector', 'value')
    )
    #define o tempo máximo do slider de acordo com o ficheiro selecionado
    def update_playback_range(selected_value):
        durations = []
        for file_path in get_log_files(selected_value):
            modified_time = Path(file_path).stat().st_mtime_ns
            df = load_log(file_path, modified_time)
            if not df.empty:
                durations.append(float(get_timestamp_time(df)[-1]))
        return max(max(durations, default=0), 0.1)

    @app.callback( #Controla o play e stop do botão do slider
        [Output('timestamp-slider', 'value'),
         Output('playback-interval', 'disabled'),
         Output('playback-button', 'children')],
        [Input('playback-button', 'n_clicks'),
         Input('playback-interval', 'n_intervals'),
         Input('dropdown-log-selector', 'value')],
        [State('timestamp-slider', 'value'),
         State('timestamp-slider', 'max'),
         State('playback-interval', 'disabled')]
    )

    #Controla o play e stop do botão do slider 
    def control_playback(n_clicks, n_intervals, selected_value, current_time, max_time, paused):
        trigger = ctx.triggered_id
        if trigger == 'dropdown-log-selector':
            return 0, True, '▶ Reproduzir'
        if trigger == 'playback-button':
            if paused:
                start_time = 0 if current_time >= max_time else current_time
                return start_time, False, '⏸ Pausar'
            return current_time, True, '▶ Reproduzir'
        if trigger == 'playback-interval':
            next_time = min(current_time + 0.5, max_time)
            finished = next_time >= max_time
            return next_time, finished, '▶ Reproduzir' if finished else '⏸ Pausar'
        return no_update, no_update, no_update

    @app.callback( #DEsenha os gráficos
        [Output('trajectory-layer-2d', 'children'),
         Output('graph-3d-view', 'figure'),
         Output('graph-depth-view', 'figure'),
         Output('graph-speed-view', 'figure'),
         Output('legend-items-container', 'children'),
         Output('timestamp-items-container', 'children'),
         Output('playback-time-label', 'children')],
        [Input('dropdown-log-selector', 'value'),
         Input('timestamp-slider', 'value'),
         Input('timestamp-slider', 'max')]
    )

    #Desenha os gráficos de acordo com o ficheiro selecionado e o tempo do slider
    def update_dashboards(selected_value, current_time, max_time):
        if not selected_value:
            return [], go.Figure(), go.Figure(), go.Figure(), [], [], '00:00 / 00:00'
        
        map_elements_2d = [] 
        fig_3d = go.Figure()
        legend_elements = []
        timestamp_elements = []
        fig_depth = go.Figure()
        fig_speed = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
        log_files = get_log_files(selected_value)

        def get_z_values(df):
            if 'pose.pose.position.z' in df.columns:
                return df['pose.pose.position.z']
            return np.zeros(len(df))
        
        def get_timestamp(df):
            if 'header.stamp.secs' in df.columns:
                return df['header.stamp.secs']
            return None

        def time(secs):
            return datetime.fromtimestamp(float(secs), tz=timezone.utc).strftime('%d/%m/%Y %H:%M:%S')
        
        for i, file_path in enumerate(log_files):
            modified_time = Path(file_path).stat().st_mtime_ns
            df = load_log(file_path, modified_time)
            if df.empty:
                continue

            elapsed = get_timestamp_time(df)
            timestamp = get_timestamp(df)
            visible = elapsed <= current_time
            if not visible.any():
                continue
            
            # Filtrar os dados apenas até ao tempo atual (slider)
            visible_df = df.loc[visible]
            visible_elapsed = elapsed[visible]
            
            # Extrair arrays numpy diretamente
            x_vals = visible_df['pose.pose.position.x'].to_numpy()
            y_vals = visible_df['pose.pose.position.y'].to_numpy()
            z_vals = get_z_values(visible_df)
            if hasattr(z_vals, 'to_numpy'):
                z_vals = z_vals.to_numpy()

            speed = None
            if 'twist.twist.linear.x' in visible_df.columns and 'twist.twist.linear.y' in visible_df.columns:
                speed = np.sqrt(
                    visible_df['twist.twist.linear.x'].to_numpy() ** 2
                    + visible_df['twist.twist.linear.y'].to_numpy() ** 2
                )

            positions_2d = list(zip(x_vals, y_vals))
            color = colors[i % len(colors)]
            filename = os.path.basename(file_path)
            
            # --- Mapa 2D ---
            map_elements_2d.append(
                dl.Polyline(positions=positions_2d, color=color, weight=4, opacity=0.9)
            )
            if positions_2d:
                map_elements_2d.append(
                    dl.CircleMarker(
                        center=positions_2d[0],
                        radius=4,
                        color='#ffffff',
                        weight=2,
                        fillColor=color,
                        fillOpacity=1
                    )
                )
                map_elements_2d.append(
                    dl.Marker(
                        position=positions_2d[-1],
                        children=dl.Tooltip(f"Posição atual: {filename}")
                    )
                )
            
            # --- Gráfico 3D ---
            fig_3d.add_trace(go.Scatter3d(
                x=x_vals, y=y_vals, z=z_vals,
                mode='lines',
                name=filename,
                line=dict(color=color, width=5),
                opacity=0.8
            ))
            
            if len(x_vals) > 0:
                fig_3d.add_trace(go.Scatter3d(
                    x=[x_vals[-1]], y=[y_vals[-1]], z=[z_vals[-1]],
                    mode='markers',
                    marker=dict(size=7, color=color, line=dict(color='#ffffff', width=1)),
                    showlegend=False,
                    text=f"Posição atual: {filename}"
                ))

            # --- Legenda ---
            legend_elements.append(
                html.Div([
                    html.Span(style={
                        'display': 'inline-block',
                        'width': '12px',
                        'height': '12px',
                        'backgroundColor': color,
                        'marginRight': '6px',
                        'borderRadius': '3px',
                        'verticalAlign': 'middle'
                    }),
                    html.Span(filename, style={'fontSize': '12px', 'wordBreak': 'break-all'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '6px'})
            )

            # --- Timestamp ---
            if timestamp is None:
                detalhes = [html.Div("Sem timestamp no log", style={'fontSize': '12px'})]
            else:
                t0, t1 = timestamp.iloc[0], timestamp.iloc[-1]
                detalhes = [
                    html.Div(f"Início: {time(t0)} UTC", style={'fontSize': '12px'}),
                    html.Div(f"Fim: {time(t1)} UTC", style={'fontSize': '12px'}),
                    html.Div(f"Duração: {int(t1 - t0)/60:.0f} min", style={'fontSize': '12px'}),
                ]
     
            timestamp_elements.append(
                html.Div(
                    [html.Div(filename, style={'fontWeight': 'bold', 'color': color,
                                               'fontSize': '12px', 'wordBreak': 'break-all'})]
                    + detalhes,
                    style={'marginBottom': '10px'}
                )
            )

            # --- Gráficos 2D (Profundidade e Velocidade) ---
            fig_depth.add_trace(go.Scatter(
                x=visible_elapsed,
                y=z_vals,
                mode='lines',
                name=filename,
                line=dict(color=color, width=3, shape='spline', smoothing=1.1),
                opacity=0.8
            ))

            if speed is not None:
                fig_speed.add_trace(go.Scatter(
                    x=visible_elapsed,
                    y=speed,
                    mode='lines',
                    name=filename,
                    line=dict(color=color, width=3, shape='spline', smoothing=1.1)
                ))

            

        # --- Layouts Finais ---
        fig_3d.update_layout(
            template='plotly_white',
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            font=CHART_FONT,
            scene=dict(
                xaxis=dict(
                    title='Latitude (°)',
                    backgroundcolor='#f8fafc',
                    gridcolor=GRID_COLOR,
                    zerolinecolor='#cbd5e1',
                    showbackground=True
                ),
                yaxis=dict(
                    title='Longitude (°)',
                    backgroundcolor='#f8fafc',
                    gridcolor=GRID_COLOR,
                    zerolinecolor='#cbd5e1',
                    showbackground=True
                ),
                zaxis=dict(
                    title='Profundidade (m)',
                    backgroundcolor='#f8fafc',
                    gridcolor=GRID_COLOR,
                    zerolinecolor='#cbd5e1',
                    showbackground=True
                ),
                aspectmode='auto',
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
            ),
            margin=dict(l=0, r=0, b=0, t=10),
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                bgcolor='rgba(255,255,255,0.75)'
            ),
            hoverlabel=dict(
                bgcolor='#0f172a',
                bordercolor='#0f172a',
                font=dict(color='#ffffff')
            )
        )

        style_time_series(fig_depth, 'Profundidade (m)')
        style_time_series(fig_speed, 'Velocidade (m/s)')
                
        time_label = f'{format_duration(current_time)} / {format_duration(max_time)}'
        return map_elements_2d, fig_3d, fig_depth, fig_speed, legend_elements, timestamp_elements, time_label
