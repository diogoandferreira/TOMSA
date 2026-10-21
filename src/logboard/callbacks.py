from dash import Output, Input, html
import os
import glob
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash_leaflet as dl
from datetime import datetime, timezone

def register_callbacks(app):
    @app.callback(
        [Output('trajectory-layer-2d', 'children'),
         Output('graph-3d-view', 'figure'),
         Output('graph-depth-view', 'figure'),
         Output('graph-speed-view', 'figure'),
         Output('legend-items-container', 'children'),
         Output('timestamp-items-container', 'children')],
        Input('dropdown-log-selector', 'value')
    )
    def update_dashboards(selected_value):
        if not selected_value:
            return [], go.Figure(), [], [], [], []
        
        map_elements_2d = []
        fig_3d = go.Figure()
        legend_elements = []
        timestamp_elements = []
        fig_depth = go.Figure()
        fig_speed = go.Figure()
        
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

            if timestamp is not None:
                t_relativo = timestamp - timestamp.iloc[0]

                fig_depth.add_trace(go.Scatter(
                    x=t_relativo,
                    y=z,
                    mode='lines',
                    name=filename,
                    line=dict(color=color, width=2.5),
                    opacity=0.8
                ))

            if 'twist.twist.linear.x' in df.columns and 'twist.twist.linear.y' in df.columns:
                v_x = df['twist.twist.linear.x']
                v_y = df['twist.twist.linear.y']
                speed = np.sqrt(v_x**2 + v_y**2)
    
                t_relativo = timestamp - timestamp.iloc[0] if timestamp is not None else range(len(speed))
                
                fig_speed.add_trace(go.Scatter(
                    x=t_relativo,
                    y=speed,
                    mode='lines',
                    name=filename,
                    line=dict(color=color, width=2)
                ))

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

        fig_depth.update_layout(
            xaxis_title='Tempo (s)',
            yaxis_title='Profundidade (m)',
            margin=dict(l=40, r=20, b=40, t=20),
            hovermode='closest',
            showlegend=False    
        )
        fig_speed.update_layout(
            xaxis_title='Tempo (s)',
            yaxis_title='Velocidade Linear (m/s)',
            margin=dict(l=40, r=20, b=40, t=20),
            hovermode='closest',
            showlegend=False
        )


                
        return map_elements_2d, fig_3d, fig_depth, fig_speed, legend_elements, timestamp_elements