import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


lat0= 41.45201666666667
lon0= -8.81322222222222

lat0_rad = np.radians(lat0)
lon0_rad = np.radians(lon0)

# Carregar os dados de log
df = pd.read_csv('../logs/robot1_s1.csv')


# Extrair as colunas de posição (x, y, z) do DataFrame
x_poses= df['pose.pose.position.x'].values
y_poses= df['pose.pose.position.y'].values
z_poses= df['pose.pose.position.z'].values


plt.figure(figsize=(8, 6))
plt.plot(x_poses, y_poses, label='Trajetória do Robô', color='blue', linewidth=2)
plt.title('Visualização da Trajetória do Robô') 
plt.xlabel('X (m)')
plt.ylabel('Y (m)')
plt.legend()
plt.grid(True)
plt.show()  
