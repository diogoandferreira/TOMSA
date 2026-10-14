from dash import Dash, html, dcc, callback, Output, Input, State
import os
import glob
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash_leaflet as dl

app = Dash(__name__)

def get_log_options():
    log_files = glob.glob('../logs/*.csv')
    options = [{'label': os.path.basename(f), 'value': f} for f in log_files]
    options.insert(0, {'label': ' Todas as Trajetórias ', 'value': 'all'})
    return options

app.layout = html.Div([

    html.H1("Dashboard TOMSA - Vista Híbrida 2D + 3D Animado", style={'textAlign': 'center'}),
        
    html.Div([
        html.Label("Selecionar Vista / Ficheiro de Log:"),
        dcc.Dropdown(
            id='dropdown-log-selector',
            options=get_log_options(),
            value='all',
            clearable=False
        )
    ], style={'width': '50%', 'margin': '0 auto', 'paddingBottom': '20px'}),

    # Layout Principal: Esquerda (2D) | Direita (3D) | Legenda
    html.Div([
        
        # 1. MAPA 2D (Leaflet)
        html.Div([
            html.H3("Mapa 2D (OpenSeaMap)", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
            dl.Map(
                id='map-global-view',
                center=[41.4520, -8.8132],
                zoom=14, 
                children=[
                    dl.TileLayer(),
                    dl.TileLayer(
                        url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
                        attribution='&copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                    ),
                    dl.LayerGroup(id='trajectory-layer-2d')
                ],
                style={'width': '100%', 'height': '65vh', 'borderRadius': '8px'}
            )
        ], style={'flex': '1', 'marginRight': '10px'}),
        
        # 2. GRÁFICO 3D (Plotly - Rotas garantidas em 3D)
        html.Div([
            html.H3("Vista rotas 3D", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
            dcc.Graph(
                id='graph-3d-view',
                style={'width': '100%', 'height': '65vh', 'borderRadius': '8px'}
            )
        ], style={'flex': '1', 'marginLeft': '10px'}),
        
        # 3. LEGENDA LATERAL
        html.Div([
            html.H3("Legenda da dashboard", style={'marginTop': '0', 'fontSize': '15px', 'borderBottom': '1px solid #ccc', 'paddingBottom': '8px'}),
            html.Div(id='legend-items-container', style={'maxHeight': '60vh', 'overflowY': 'auto'})
        ], style={
            'flex': '0.4',
            'marginLeft': '10px',
            'backgroundColor': '#f9f9f9',
            'padding': '15px',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'fontFamily': 'sans-serif'
        })
    ], style={'display': 'flex', 'width': '98%', 'margin': '0 auto'}),

    # 4. Controlos de Animação
    html.Div([
        html.Button("Play / Pause", id='btn-play-pause', n_clicks=0, style={'padding': '8px 16px', 'backgroundColor': '#1f77b4', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer', 'marginRight': '10px'}),
        html.Button("Reiniciar", id='btn-reset', n_clicks=0, style={'padding': '8px 16px', 'backgroundColor': '#d62728', 'color': 'white', 'border': 'none', 'borderRadius': '4px', 'cursor': 'pointer'}),
        dcc.Interval(id='animation-interval', interval=200, n_intervals=0, disabled=True),
        dcc.Store(id='store-frame-index', data=0)
    ], style={'width': '98%', 'margin': '15px auto', 'textAlign': 'center'})

])

@callback(
    [Output('animation-interval', 'disabled'),
     Output('store-frame-index', 'data')],
    [Input('btn-play-pause', 'n_clicks'),
     Input('btn-reset', 'n_clicks'),
     Input('dropdown-log-selector', 'value')],
    [State('animation-interval', 'disabled'),
     State('store-frame-index', 'data')]
)
def control_animation(n_play, n_reset, selected_log, is_disabled, current_frame):
    ctx = callback.triggered_id
    if ctx == 'dropdown-log-selector' or ctx == 'btn-reset':
        return True, 0
    if ctx == 'btn-play-pause':
        return not is_disabled, current_frame
    return is_disabled, current_frame

@callback(
    [Output('trajectory-layer-2d', 'children'),
     Output('graph-3d-view', 'figure'),
     Output('legend-items-container', 'children'),
     Output('store-frame-index', 'data', allow_duplicate=True)],
    [Input('animation-interval', 'n_intervals'),
     Input('dropdown-log-selector', 'value')],
    [State('store-frame-index', 'data')],
    prevent_initial_call=True
)
def update_dashboards(n_intervals, selected_value, frame_index):
    if not selected_value:
        return [], go.Figure(), [], 0
    
    map_elements_2d = []
    fig_3d = go.Figure()
    legend_elements = []
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    def get_z_values(df):
        if 'pose.pose.position.z' in df.columns:
            return df['pose.pose.position.z']
        return np.zeros(len(df))

    log_files = [selected_value] if selected_value != 'all' else glob.glob('../logs/*.csv')
    max_len = 0
    
    for i, file_path in enumerate(log_files):
        df = pd.read_csv(file_path)
        if df.empty:
            continue
        
        if len(df) > max_len:
            max_len = len(df)
            
        x = df['pose.pose.position.x']
        y = df['pose.pose.position.y']
        z = get_z_values(df)
        
        # Nota: Se x e y forem metros (local), no gráfico 3D aparecem perfeitamente.
        # No 2D, se não forem lat/lon, filtramos para não rebentar o mapa.
        positions_2d = list(zip(x, y))
        color = colors[i % len(colors)]
        filename = os.path.basename(file_path)
        
        # 1. Gráfico 3D (Plotly) - Funciona sempre com coordenadas métricas ou geodésicas
        fig_3d.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            name=filename,
            line=dict(color=color, width=3),
            opacity=0.3,
            showlegend=False
        ))
        
        idx = min(frame_index, len(df) - 1)
        curr_x, curr_y, curr_z = x.iloc[idx], y.iloc[idx], z.iloc[idx]
        
        fig_3d.add_trace(go.Scatter3d(
            x=[curr_x], y=[curr_y], z=[curr_z],
            mode='markers',
            marker=dict(size=8, color=color, symbol='diamond'),
            showlegend=False,
            text=f"Robô: {filename}"
        ))

        # 2. Mapa 2D (Só adiciona se estiver num intervalo de Lat/Lon válido, ex: Portugal continental)
        if (30 <= x.iloc[0] <= 50) and (-20 <= y.iloc[0] <= 0):
            map_elements_2d.append(dl.Polyline(positions=positions_2d, color=color, weight=2, opacity=0.4))
            map_elements_2d.append(dl.Marker(position=[curr_x, curr_y], children=dl.Tooltip(f"{filename} (Frame: {idx})")))

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

    next_frame = (frame_index + 1) % max_len if max_len > 0 else 0

    fig_3d.update_layout(
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z / Altitude (m)',
            aspectmode='auto'
        ),
        margin=dict(l=0, r=0, b=0, t=10),
        showlegend=False
    )
            
    return map_elements_2d, fig_3d, legend_elements, next_frame

if __name__ == '__main__':
    app.run(debug=True, port=8050)