import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- PASSO 1: Carregar os dados de log ---
# Lê o ficheiro CSV do robô que está na pasta de logs
df = pd.read_csv('../logs/robot7_s1.csv')

# --- PASSO 2: Definir a referência inicial da Aguçadoura ---
# Estes valores marcam a origem geodética local (latitude e longitude de referência)
lat0 = 41.45201666666667
lon0 = -8.81322222222222

# Extrai os valores brutos de latitude e longitude do ficheiro de log
lat = df['pose.pose.position.x'].values
lon = df['pose.pose.position.y'].values

# --- PASSO 3: Mudança de Base / Conversão para Coordenadas Cartesianas (NED) ---
# Multiplicamos a diferença geográfica por fatores de conversão aproximados 
# para transformar graus em metros (referencial North-East-Down no plano local)
d_north = (lat - lat0) * 111132.92
d_east = (lon - lon0) * 85393.55

# --- PASSO 4: Desenhar o Gráfico com Matplotlib ---
plt.figure(figsize=(8, 6))

# Cria uma linha a azul ligando as posições (East, North) do robô
plt.plot(d_east, d_north, label='Trajetória do Robô', color='blue', linewidth=2)

# Adiciona título e rótulos aos eixos (medidos em metros a partir da origem)
plt.title('Visualização da Trajetória do Robô (Referencial Local NED)')
plt.xlabel('Eixo Este / East (metros)')
plt.ylabel('Eixo Norte / North (metros)')

# Mostra a grelha de fundo para facilitar a leitura visual
plt.grid(True)
plt.legend()

# Exibe o gráfico numa janela interativa
plt.show()
