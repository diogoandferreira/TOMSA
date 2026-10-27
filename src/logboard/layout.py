from dash import html, dcc
import os
import glob
from pathlib import Path
import dash_leaflet as dl

LOGS_DIR = Path(__file__).resolve().parents[2] / 'logs'

def get_log_options():
    log_files = glob.glob(str(LOGS_DIR / '*.csv'))
    options = [{'label': os.path.basename(f), 'value': f} for f in log_files]
    options.insert(0, {'label': ' Todas as Trajetórias ', 'value': 'all'})
    return options

def create_layout():
    dashboard = html.Div([

        html.H1("Dashboard TOMSA - Vista Superior/Inferior", style={'textAlign': 'center'}),
            
        html.Div([
            html.Label("Selecionar Vista / Ficheiro de Log:"),
            dcc.Dropdown(
                id='dropdown-log-selector',
                options=get_log_options(),
                value='all',
                clearable=False
            )
        ], style={'width': '50%', 'margin': '0 auto', 'paddingBottom': '20px'}),

        html.Div([
            
            # --- LINHA SUPERIOR: MAPA 2D + LEGENDA ---
            html.Div([
                # 1. Mapa 2D (OpenSeaMap)
                html.Div([
                    html.H3("Mapa 2D (OpenSeaMap)", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
                    dl.Map(
                        id='map-global-view',
                        center=[41.4520, -8.8132],
                        zoom=17,
                        children=[
                            dl.TileLayer(),
                            dl.TileLayer(
                                url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
                                attribution='&copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                            ),
                            dl.LayerGroup(id='trajectory-layer-2d')
                        ],
                        style={'width': '100%', 'height': '55vh', 'borderRadius': '8px'}
                    )
                ], style={'flex': '4', 'marginRight': '10px'}),
                
                # 2. Legenda
                html.Div([
                    html.H3("Legenda", style={'marginTop': '0', 'fontSize': '15px', 'borderBottom': '1px solid #ccc', 'paddingBottom': '8px'}),
                    html.Div(id='legend-items-container', style={'maxHeight': '50vh', 'overflowY': 'auto'})
                ], className='dashboard-card', style={'flex': '1', 'marginLeft': '10px'})
            ], style={'display': 'flex', 'width': '100%', 'marginBottom': '15px'}),

            # --- LINHA INFERIOR: GRÁFICO 3D + TIMESTAMP (Na ordem que pediste) ---
            html.Div([
                # 3. Gráfico 3D (Plotly)
                html.Div([
                    html.H3("Vista 3D", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
                    dcc.Graph(
                        id='graph-3d-view',
                        style={'width': '100%', 'height': '55vh', 'borderRadius': '8px'}
                    )
                ], style={'flex': '4', 'marginLeft': '0', 'marginRight': '10px'}),

                # 4. Timestamp
                html.Div([
                    html.H3("TimeStamp", style={'marginTop': '0', 'fontSize': '15px', 'borderBottom': '1px solid #ccc', 'paddingBottom': '8px'}),
                    html.Div(id='timestamp-items-container', style={'maxHeight': '50vh', 'overflowY': 'auto'})
                ], className='dashboard-card', style={'flex': '1', 'marginRight': '0'})
            ], style={'display': 'flex', 'width': '100%'}),
            
            #Grafico profundidade x tempo
            html.Div([
                
                # Gráfico 1: Profundidade x Tempo (Coluna Esquerda)
                html.Div([
                    html.H3("Profundidade x Tempo", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
                    dcc.Graph(
                        id='graph-depth-view',
                        style={'width': '100%', 'height': '40vh', 'borderRadius': '8px'}
                    )
                ], style={'flex': '1', 'marginRight': '10px'}),
                
                # Gráfico 2: Velocidade Linear (Coluna Direita)
                html.Div([
                    html.H3("Velocidade Linear ao Longo do Tempo", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
                    dcc.Graph(
                        id='graph-speed-view',
                        style={'width': '100%', 'height': '40vh', 'borderRadius': '8px'}
                    )
                ], style={'flex': '1', 'marginLeft': '10px'})

            ], style={
                'display': 'flex', 
                'width': '98%', 
                'margin': '20px auto', 
                'backgroundColor': '#f9f9f9', 
                'padding': '15px', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        ], style={'width': '98%', 'margin': '0 auto'})
    ], style={'paddingBottom': '100px'})

    return html.Div([
        dashboard,
        html.Div([
            html.Button(
                '▶ Reproduzir',
                id='playback-button',
                n_clicks=0,
                style={'minWidth': '125px'}
            ),
            html.Div([
                html.Div(id='playback-time-label', children='00:00 / 00:00',
                         style={'fontVariantNumeric': 'tabular-nums', 'textAlign': 'center'}),
                dcc.Slider(
                    id='timestamp-slider',
                    min=0,
                    max=1,
                    step=0.1,
                    value=0,
                    marks=None,
                    tooltip={'placement': 'top', 'always_visible': False}
                )
            ], style={'flex': '1', 'minWidth': '200px'}),
            dcc.Interval(id='playback-interval', interval=500, n_intervals=0, disabled=True)
        ], style={
            'position': 'fixed',
            'bottom': '0',
            'left': '0',
            'width': '100%',
            'boxSizing': 'border-box',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '20px',
            'padding': '12px 24px',
            'backgroundColor': '#fff',
            'borderTop': '1px solid #ccc',
            'boxShadow': '0 -2px 8px rgba(0,0,0,0.12)',
            'zIndex': '1000'
        })
    ])