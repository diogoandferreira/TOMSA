from dash import html, dcc
import os
import glob
from pathlib import Path
import dash_leaflet as dl

from config import CONFIG, LOGS_DIR, pick_radar_ref, robot_label

def get_log_options():
    log_files = sorted(glob.glob(str(LOGS_DIR / '*.csv')))
    options = [{'label': robot_label(f), 'value': f} for f in log_files]
    options.insert(0, {'label': 'Todas as trajetórias', 'value': 'all'})
    return options


def card(title, body, class_name='', body_class='card-body'):
    """Cartão genérico: título + conteúdo."""
    return html.Section([
        html.H3(title, className='card-title'),
        html.Div(body, className=body_class),
    ], className=f'card {class_name}'.strip())


def create_layout():
    header = html.Header([
        html.Div([
            html.H1('Análise de logs'),
            html.P('Trajetórias, profundidade e velocidade a partir de logs ROS', className='subtitle'),
        ]),
        html.Div([
            html.Label('Ficheiro de log', htmlFor='dropdown-log-selector'),
            dcc.Dropdown(
                id='dropdown-log-selector',
                options=get_log_options(),
                value='all',
                clearable=False,
                searchable=False,
            ),
        ], className='log-picker'),
    ], className='app-header')

    # Linha 1: mapa 2D + legenda
    row_map = html.Div([
        card('Mapa 2D', dl.Map(
            id='map-global-view',
            center=CONFIG['map']['center'],
            zoom=CONFIG['map']['zoom'],
            children=[
                dl.TileLayer(),
                dl.TileLayer(
                    url='https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
                    attribution='&copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors',
                ),
                dl.LayerGroup(id='trajectory-layer-2d'),
            ],
            className='map',
        ), class_name='card-main', body_class='card-body flush'),
        card('Legenda', html.Div(id='legend-items-container'), class_name='card-side'),
    ], className='row')

    # Linha 2: vista 3D (com bússola sobreposta) + timestamps
    row_3d = html.Div([
        card('Vista 3D', html.Div([
            dcc.Graph(id='graph-3d-view', className='graph-3d'),
            html.Div(
                dcc.Graph(id='compass-view', config={'displayModeBar': False}),
                className='compass',
            ),
        ], className='graph-3d-wrap'), class_name='card-main', body_class='card-body flush'),
        card('Timestamps', html.Div(id='timestamp-items-container'), class_name='card-side'),
    ], className='row')

    # Linha 3: séries temporais
    row_charts = html.Div([
        card('Profundidade', dcc.Graph(id='graph-depth-view', className='graph-ts'), class_name='card-half'),
        card('Velocidade linear', dcc.Graph(id='graph-speed-view', className='graph-ts'), class_name='card-half'),
    ], className='row')

    #Linha 3:Radar
    row_radar = html.Div([
        card('Radar: distância entre robots', html.Div([
            dcc.Dropdown(
                id='radar-ref-selector',
                options=[{'label': 'Ponto inical', 'value': 'origin'}]
                        + [o for o in get_log_options() if o['value'] != 'all'],
                value=pick_radar_ref([o['value'] for o in get_log_options() if o['value'] != 'all']),
                clearable=False,
                searchable=False,
            ),
            dcc.Graph(id='radar-view', style={'height': '45vh'}),
        ]), class_name='card-main'),
        card('Distâncias', html.Div(id='radar-distances'), class_name='card-side'),
    ], className='row')


    playback_bar = html.Footer([
        html.Button('▶ Reproduzir', id='playback-button', n_clicks=0, className='btn-play'),
        dcc.Dropdown(
            id='speed-selector',
            options=[{'label': f'{v}x', 'value': v} for v in CONFIG['playback']['speeds']],
            value=CONFIG['playback']['default_speed'],
            clearable=False,
            searchable=False,
            className='speed-picker',
        ),
        html.Div(id='playback-time-label', children='00:00 / 00:00', className='time-label'),
        html.Div([
            dcc.Slider(
                id='timestamp-slider',
                min=0, max=1, step=0.1, value=0,
                marks=None, tooltip=None,
                updatemode='drag',
            ),
        ], className='slider-wrap'),
        dcc.Interval(id='playback-interval', interval=CONFIG['playback']['interval_ms'], n_intervals=0, disabled=True),
    ], className='playback-bar')

    return html.Div([
        header,
        html.Main([row_map, row_3d, row_radar, row_charts], className='content'),
        playback_bar,
        dcc.Store(id='traces3d-store'),   # dados 3D do instante atual (enviados ao browser)
        dcc.Store(id='restyle-dummy'),    # saída fictícia do callback JS que atualiza o 3D
    ], className='app-shell')