import numpy as np
import plotly.graph_objects as go

# 1. Gerar uma trajetória pequena (exemplo: uma hélice)
t = np.linspace(0, 10, 40)
x = np.cos(t)
y = np.sin(t)
z = t * 0.2

fig = go.Figure()

# Linha de fundo estática para mostrar a rota completa
fig.add_trace(go.Scatter3d(
    x=x, y=y, z=z,
    mode='lines',
    name='Trajetória Completa',
    line=dict(color='gray', width=3, dash='dash')
))

# 2. Criar os frames da animação para cada ponto do percurso
frames = []
axis_length = 0.25

for i in range(len(t)):
    px, py, pz = x[i], y[i], z[i]
    
    # Calcular direção tangente (Eixo X do corpo - Vermelho)
    if i < len(t) - 1:
        vx = x[i+1] - x[i]
        vy = y[i+1] - y[i]
        vz = z[i+1] - z[i]
    else:
        vx = x[i] - x[i-1]
        vy = y[i] - y[i-1]
        vz = z[i] - z[i-1]
        
    norm = np.sqrt(vx**2 + vy**2 + vz**2)
    if norm > 0:
        ux, uy, uz = vx/norm, vy/norm, vz/norm
    else:
        ux, uy, uz = 1, 0, 0

    # Eixo Y local (Verde) - Direção lateral ortogonal
    ny, nx = -uy, ux

    # Cada frame contém os dados da posição atual do corpo e dos respetivos 3 eixos
    frame_data = [
        # Trajetória estática mantida no fundo
        go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color='gray', width=3, dash='dash')),
        # Ponto do corpo em movimento
        go.Scatter3d(x=[px], y=[py], z=[pz], mode='markers', marker=dict(size=6, color='black')),
        # Eixo X (Vermelho)
        go.Scatter3d(x=[px, px + axis_length * ux], y=[py, py + axis_length * uy], z=[pz, pz + axis_length * uz], mode='lines', line=dict(color='red', width=5)),
        # Eixo Y (Verde)
        go.Scatter3d(x=[px, px + axis_length * nx], y=[py, py + axis_length * ny], z=[pz, pz], mode='lines', line=dict(color='green', width=5)),
        # Eixo Z (Azul)
        go.Scatter3d(x=[px, px], y=[py, py], z=[pz, pz + axis_length], mode='lines', line=dict(color='blue', width=5))
    ]
    frames.append(go.Frame(data=frame_data, name=str(i)))

# 3. Adicionar o estado inicial (frame 0) à figura principal
px, py, pz = x[0], y[0], z[0]
ux, uy, uz = 1, 0, 0
nx, ny = 0, 1

fig.add_trace(go.Scatter3d(x=[px], y=[py], z=[pz], mode='markers', marker=dict(size=6, color='black'), name='Corpo'))
fig.add_trace(go.Scatter3d(x=[px, px + axis_length * ux], y=[py, py + axis_length * uy], z=[pz, pz + axis_length * uz], mode='lines', line=dict(color='red', width=5), name='Eixo X'))
fig.add_trace(go.Scatter3d(x=[px, px + axis_length * nx], y=[py, py + axis_length * ny], z=[pz, pz], mode='lines', line=dict(color='green', width=5), name='Eixo Y'))
fig.add_trace(go.Scatter3d(x=[px, px], y=[py, py], z=[pz, pz + axis_length], mode='lines', line=dict(color='blue', width=5), name='Eixo Z'))

fig.frames = frames

# 4. Configurar controlos de animação (Botões Play / Pause) e layout
fig.update_layout(
    title="Animação do Corpo e Eixos Locais em Movimento",
    scene=dict(
        xaxis_title='X (m)',
        yaxis_title='Y (m)',
        zaxis_title='Z (m)',
        aspectmode='auto'
    ),
    updatemenus=[dict(
        type="buttons",
        buttons=[
            dict(label="Play", method="animate", args=[None, {"frame": {"duration": 150, "redraw": True}, "fromcurrent": True}]),
            dict(label="Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
        ],
        direction="left",
        pad={"r": 10, "t": 10},
        showactive=False,
        x=0.1,
        xanchor="right",
        y=0,
        yanchor="top"
    )],
    margin=dict(l=0, r=0, b=0, t=40)
)

fig.show()