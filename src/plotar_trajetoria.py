import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Carregar os dados
df = pd.read_csv('../logs/robot7_s1.csv')

#  referência inicial da Aguçadoura 
lat0 = 41.45201666666667
lon0 = -8.81322222222222

# Extrai os valores brutos de latitude e longitude do ficheiro de log
lat = df['pose.pose.position.x'].values
lon = df['pose.pose.position.y'].values

d_north = (lat - lat0) * 111132.92
d_east = (lon - lon0) * 85393.55

#  Desenhar o Gráfico com Matplotlib
plt.figure(figsize=(8, 6))

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
from pathlib import Path

# --- Parâmetros ---
DATA_DIR = Path('../TL2026')                       # pasta dos CSV
ROBOTS = {1: 'tab:red', 4: 'tab:green', 7: 'tab:blue'}
lat0, lon0 = 41.45201666666667, -8.81322222222222  # origem (Aguçadoura)
H0 = 56.0     # altura da superfície do mar nos dados (m); ajustar
EXAG = 3      # exagero vertical (~30 m de profundidade vs ~150 m na horizontal)

M_LAT = 111132.92
M_LON = 111320 * np.cos(np.radians(lat0))

def load(robot_id):
    df = pd.read_csv(DATA_DIR / f'robot{robot_id}_s1.csv',
                     usecols=['Time', 'pose.pose.position.x',
                              'pose.pose.position.y', 'pose.pose.position.z'])
    north = (df['pose.pose.position.x'] - lat0) * M_LAT
    east = (df['pose.pose.position.y'] - lon0) * M_LON
    down = H0 - df['pose.pose.position.z']         
    return east.values, north.values, down.values

fig = plt.figure(figsize=(9, 7))
ax = fig.add_subplot(projection='3d')

allx, ally, allz = [], [], []
for rid, color in ROBOTS.items():
    e, n, d = load(rid)
    ax.plot(e, n, d, color=color, lw=1.2, label=f'Robot {rid}')
    ax.scatter(e[0], n[0], d[0], color=color, marker='o', s=40)     # início
    ax.scatter(e[-1], n[-1], d[-1], color=color, marker='X', s=60)  # fim
    allx += [e.min(), e.max()]; ally += [n.min(), n.max()]; allz += [d.min(), d.max()]

# plano da superfície da água (profundidade = 0)
xx, yy = np.meshgrid([min(allx), max(allx)], [min(ally), max(ally)])
ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.15, color='cyan')

ax.set_xlabel('East (m)'); ax.set_ylabel('North (m)'); ax.set_zlabel('Down / profundidade (m)')
ax.invert_zaxis()                                  # profundidade aumenta para baixo
ax.set_box_aspect((np.ptp(allx), np.ptp(ally), max(np.ptp(allz), 1) * EXAG))
ax.set_title('Trajetórias 3D (referencial local NED)')
ax.legend()
plt.show()
