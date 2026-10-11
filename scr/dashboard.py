import pandas as pd
import plotly.graph_objects as go

# 1. Dicionário com os 3 robôs e as respetivas cores para identificação
robos = {
    'Robô 1': {'arquivo': '../logs/robot1_s1.csv', 'cor': 'blue'},
    'Robô 2': {'arquivo': '../logs/robot4_s1.csv', 'cor': 'red'},
    'Robô 3': {'arquivo': '../logs/robot7_s1.csv', 'cor': 'green'},
}

# 2. Inicializar a figura do gráfico com suporte para mapas modernos
fig = go.Figure()

for nome, info in robos.items():
    try:
        # Carregar o CSV do log
        df = pd.read_csv(info['arquivo'])
        
        lat = df['pose.pose.position.x']
        lon = df['pose.pose.position.y']
        
        # Adicionar a linha da trajetória completa do robô (usando Scattermap)
        fig.add_trace(go.Scattermap(
            lat=lat,
            lon=lon,
            mode='lines',
            name=f'Trajetória {nome}',
            line=dict(width=3, color=info['cor'])
        ))
        
        # Adicionar o marcador da posição atual (último ponto do registo)
        fig.add_trace(go.Scattermap(
            lat=[lat.iloc[-1]],
            lon=[lon.iloc[-1]],
            mode='markers+text',
            name=f'{nome} (Atual)',
            marker=dict(size=12, color=info['cor']),
            text=[nome],
            textposition='top right'
        ))
        
    except FileNotFoundError:
        print(f"Aviso: Ficheiro não encontrado para o {nome} em {info['arquivo']}.")

fig.update_layout(
    title="Global View: Trajetórias e Posições Atuais dos 3 Robôs sobre Mapa Open Source",
    map=dict(
        style="open-street-map",  # Utiliza os mapas abertos e gratuitos do OpenStreetMap
        zoom=13,                  # Nível de zoom inicial centrado na zona da missão
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    height=750
)

# 4. Abrir o mapa interativo no navegador web
fig.show()