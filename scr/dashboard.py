from dash import Dash, html, dcc, callback, Output, Input
import os
import glob
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import dash_leaflet as dl

df = pd.read_csv('../logs/robot1_s1.csv')

app = Dash(__name__)

def get_log_options():
    log_files = glob.glob('../logs/*.csv')
    # Criar a lista normal com os ficheiros individuais
    options = [{'label': os.path.basename(f), 'value': f} for f in log_files]
    
    # Inserir a opção no topo para ver todas as trajetórias em conjunto
    options.insert(0, {'label': ' Todas as Trajetórias ', 'value': 'all'})
    
    return options



app.layout = html.Div([

    html.H1("Dashboard TOMSA", style={'textAlign': 'center'}),
        
        html.Div([
            html.Label("Selecionar Vista / Ficheiro de Log:"),
            dcc.Dropdown(
                id='dropdown-log-selector',
                options=get_log_options(),
                value='all', # Define 'all' como a opção inicial por defeito
                clearable=False
            )
        ], style={'width': '50%', 'margin': '0 auto', 'paddingBottom': '20px'}),

    html.Div([
            # O Mapa
            html.Div([
                dl.Map(
                    id='map-global-view',
                    center=[41.4520, -8.8132],
                    zoom=16.5, 
                    children=[
                        dl.TileLayer(),
                        dl.TileLayer(
                            url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
                            attribution='&copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                        ),
                        dl.LayerGroup(id='trajectory-layer')
                    ],
                    style={'width': '100%', 'height': '70vh', 'borderRadius': '8px'}
                )
            ], style={'flex': '4', 'marginRight': '20px'}),
            
            # Caixa de Legenda Lateral Fixa (Garante que aparece sempre)
            html.Div([
                html.H3("Legenda", style={'marginTop': '0', 'fontSize': '16px', 'borderBottom': '1px solid #ccc', 'paddingBottom': '8px'}),
                html.Div(id='legend-items-container', style={'maxHeight': '65vh', 'overflowY': 'auto'})
            ], style={
                'flex': '1',
                'backgroundColor': '#f9f9f9',
                'padding': '15px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'fontFamily': 'sans-serif'
            })
        ], style={'display': 'flex', 'width': '90%', 'margin': '0 auto'})


])

@callback(
    [Output('trajectory-layer', 'children'),
     Output('legend-items-container', 'children')],
    Input('dropdown-log-selector', 'value')
)

def update_map_trajectory(selected_value):
    if not selected_value:
        return [], []
    
    # Lista para acumular os elementos gráficos (linhas e marcadores) que vão para o mapa
    map_elements = []
    legend_elements = []
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    # Se o utilizador escolheu a opção 'all', processamos todos os ficheiros da pasta
    if selected_value == 'all':
        log_files = glob.glob('../logs/*.csv')
        
        # Paleta simples de cores para distinguir os robôs/trajetórias visualmente
        colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkcyan']
        
        for i, file_path in enumerate(log_files):
            df = pd.read_csv(file_path)
            if df.empty:
                continue
                
            lats = df['pose.pose.position.x']
            lons = df['pose.pose.position.y']
            positions = list(zip(lats, lons))
            
            color = colors[i % len(colors)]
            filename = os.path.basename(file_path)
            
            # Adicionar a linha da trajetória de cada robô com uma cor distinta
            map_elements.append(
                dl.Polyline(positions=positions, color=color, weight=3, opacity=0.8)
            )
            
            # Adicionar o marcador da posição atual no fim da trajetória
            map_elements.append(
                dl.Marker(
                    position=[lats.iloc[-1], lons.iloc[-1]],
                    children=dl.Tooltip(f"Robô/Log: {filename}")
                )
            )

            legend_elements.append(
                html.Div([
                    html.Span(style={
                        'display': 'inline-block',
                        'width': '14px',
                        'height': '14px',
                        'backgroundColor': color,
                        'marginRight': '8px',
                        'borderRadius': '3px',
                        'verticalAlign': 'middle'
                    }),
                    html.Span(filename, style={'fontSize': '13px', 'wordBreak': 'break-all'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'})
            )
            
    else:
        # Comportamento normal: carregar apenas o ficheiro selecionado no dropdown
        df = pd.read_csv(selected_value)
        if not df.empty:
            lats = df['pose.pose.position.x']
            lons = df['pose.pose.position.y']
            positions = list(zip(lats, lons))
            filename = os.path.basename(selected_value)
            
            map_elements.append(
                dl.Polyline(positions=positions, color='blue', weight=4)
            )
            map_elements.append(
                dl.Marker(
                    position=[lats.iloc[-1], lons.iloc[-1]],
                    children=dl.Tooltip(f"Posição Atual - {filename}")
                )
            )
            legend_elements.append(
                html.Div([
                    html.Span(style={
                        'display': 'inline-block',
                        'width': '14px',
                        'height': '14px',
                        'backgroundColor': '#1f77b4',
                        'marginRight': '8px',
                        'borderRadius': '3px',
                        'verticalAlign': 'middle'
                    }),
                    html.Span(filename, style={'fontSize': '13px', 'wordBreak': 'break-all'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'})
            )
            
    return map_elements,legend_elements

# 5. Executar o servidor local
if __name__ == '__main__':
    app.run(debug=True, port=8050)