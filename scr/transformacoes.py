import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

lat0 = 41.45201666666667
lon0 = -8.81322222222222
h0 = 55.44791126176966

def geodetic_to_ecef(lat_deg, lon_deg, alt):
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = 2 * f - f**2
    lat_rad = np.radians(lat_deg)
    lon_rad = np.radians(lon_deg)
    N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
    X = (N + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    Y = (N + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    Z = (N * (1 - e2) + alt) * np.sin(lat_rad)
    return np.array([X, Y, Z])

p0 = geodetic_to_ecef(lat0, lon0, h0)

# Matriz de Rotação R (3x3)
lat0_rad = np.radians(lat0)
lon0_rad = np.radians(lon0)
sin_lat, cos_lat = np.sin(lat0_rad), np.cos(lat0_rad)
sin_lon, cos_lon = np.sin(lon0_rad), np.cos(lon0_rad)

R = np.array([
    [-sin_lat * cos_lon, -sin_lat * sin_lon,  cos_lat],
    [-sin_lon,           cos_lon,            0      ],
    [-cos_lat * cos_lon, -cos_lat * sin_lon, -sin_lat]
])

# Carregar os dados de log
df = pd.read_csv('../logs/robot1_s1.csv')

# Extrair as colunas de posição (x, y, z) do DataFrame
x_poses = df['pose.pose.position.x'].values
y_poses = df['pose.pose.position.y'].values
z_poses = df['pose.pose.position.z'].values

coordenadas_ned = []

for lat, lon, h in zip(x_poses, y_poses, z_poses):
    p = geodetic_to_ecef(lat, lon, h)
    delta_p = p - p0
    ned_vector = R @ delta_p
    coordenadas_ned.append(ned_vector)

coordenadas_ned = np.array(coordenadas_ned)

# Extrair Este (Y do NED) e Norte (X do NED) em metros
east = coordenadas_ned[:, 1]
north = coordenadas_ned[:, 0]



plt.figure(figsize=(8, 6))
plt.plot(east, north, label='Trajetória do Robô (NED)', color='blue', linewidth=2)
plt.title('Visualização da Trajetória do Robô (Referencial Local NED)')
plt.xlabel('Eixo Este (metros)')
plt.ylabel('Eixo Norte (metros)')
plt.grid(True)
plt.legend()

plt.show()