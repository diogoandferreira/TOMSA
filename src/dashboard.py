from dash import Dash, html, dcc, callback, Output, Input
import os
import glob
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash_leaflet as dl
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import matplotlib.animation as animation

app = Dash(__name__)

def get_log_options():
    log_files = glob.glob('../logs/*.csv')
    options = [{'label': os.path.basename(f), 'value': f} for f in log_files]
    options.insert(0, {'label': ' Todas as Trajetórias ', 'value': 'all'})
    return options

app.layout = html.Div([

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
        
        #  MAPA 2D  LEGENDA
        html.Div([
            # 1. Mapa 2D (OpenSeaMap) - Ocupa o maior espaço horizonta
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
                    style={'width': '100%', 'height': '55vh', 'borderRadius': '8px'}
                )
            ], style={'flex': '4', 'marginRight': '10px'}),
            
            # 2. Legenda
            html.Div([
                html.H3("Legenda", style={'marginTop': '0', 'fontSize': '15px', 'borderBottom': '1px solid #ccc', 'paddingBottom': '8px'}),
                html.Div(id='legend-items-container', style={'maxHeight': '50vh', 'overflowY': 'auto'})
            ], style={
                'flex': '1',
                'marginLeft': '10px',
                'backgroundColor': '#f9f9f9',
                'padding': '15px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'fontFamily': 'sans-serif'
            })
        ], style={'display': 'flex', 'width': '100%', 'marginBottom': '15px'}),

        # TIMESTAMP GRÁFICO 3D 
        html.Div([
            # 3. Gráfico 3D (Plotly)
            html.Div([
                            html.H3("Vista 3D", style={'textAlign': 'center', 'fontSize': '15px', 'marginTop': '0'}),
                            dcc.Graph(
                                id='graph-3d-view',
                                style={'width': '100%', 'height': '55vh', 'borderRadius': '8px'}
                            )
                        ], style={'flex': '4', 'marginLeft': '10px'}),

            # 4.  Timestamp
            html.Div([
                            html.H3("TimeStamp", style={'marginTop': '0', 'fontSize': '15px', 'borderBottom': '1px solid #ccc', 'paddingBottom': '8px'}),
                            html.Div(id='timestamp-items-container', style={'maxHeight': '50vh', 'overflowY': 'auto'})
                        ], style={
                            'flex': '1',
                            'marginRight': '10px',
                            'backgroundColor': '#f9f9f9',
                            'padding': '15px',
                            'borderRadius': '8px',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                            'fontFamily': 'sans-serif'
                        })
        ], style={'display': 'flex', 'width': '100%'})

    ], style={'width': '98%', 'margin': '0 auto'})
])


@callback(
    [Output('trajectory-layer-2d', 'children'),
     Output('graph-3d-view', 'figure'),
     Output('legend-items-container', 'children'),
     Output('timestamp-items-container', 'children')],
    Input('dropdown-log-selector', 'value')
)

def update_dashboards(selected_value):
    if not selected_value:
        return [], go.Figure(), [], []
    
    map_elements_2d = []
    fig_3d = go.Figure()
    legend_elements = []
    timestamp_elements = []
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

    log_files = [selected_value] if selected_value != 'all' else glob.glob('../logs/*.csv')

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

        df = pd.read_csv(file_path)
        if df.empty:
            continue
        
        x = df['pose.pose.position.x']
        y = df['pose.pose.position.y']
        z = get_z_values(df)
        timestamp = get_timestamp(df)
        
        positions_2d = list(zip(x, y))
        color = colors[i % len(colors)]
        filename = os.path.basename(file_path)
        
        # --- Mapa 2D ---
        map_elements_2d.append(
            dl.Polyline(positions=positions_2d, color=color, weight=3, opacity=0.8)
        )
        map_elements_2d.append(
            dl.Marker(
                position=positions_2d[-1],
                children=dl.Tooltip(f"Log: {filename}")
            )
        )


        
        # --- Gráfico 3D ---
        fig_3d.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            name=filename,
            line=dict(color=color, width=4),
            opacity=0.8
        ))
        
        fig_3d.add_trace(go.Scatter3d(
            x=[x.iloc[-1]], y=[y.iloc[-1]], z=[z.iloc[-1]],
            mode='markers',
            marker=dict(size=6, color=color),
            showlegend=False,
            text=f"Fim: {filename}"
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


        if timestamp is None:
            detalhes = [html.Div("Sem timestamp no log", style={'fontSize': '12px'})]
        else:
            t0, t1 = timestamp.iloc[0], timestamp.iloc[-1]
            detalhes = [
                html.Div(f"Início: {time(t0)} UTC", style={'fontSize': '12px'}),
                html.Div(f"Fim: {time(t1)} UTC", style={'fontSize': '12px'}),
                html.Div(f"Duração: {int(t1 - t0)/60:.0f} min", style={'fontSize': '12px'}), # se seg, horas, min
            ]
 
        timestamp_elements.append(
            html.Div(
                [html.Div(filename, style={'fontWeight': 'bold', 'color': color,
                                           'fontSize': '12px', 'wordBreak': 'break-all'})]
                + detalhes,
                style={'marginBottom': '10px'}
            )
        )

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
            
    return map_elements_2d, fig_3d, legend_elements, timestamp_elements

if __name__ == '__main__':
    app.run(debug=True, port=8050)

