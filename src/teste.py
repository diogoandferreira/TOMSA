import matplotlib.pyplot as plt
import numpy as np
import pymap3d as pm

lat, lon, alt = 41.4524366841726, -8.81236126943227, 56.7327584009618
x, y, z = pm.ecef2geodetic(lat, lon, alt)
print(x, y, z)

fig = plt.figure(figsize=(7, 7))
ax = fig.add_subplot(projection='3d')

# elipsoide WGS84 em wireframe (referência visual)
a, b = 6378137.0, 6356752.314245
u, v = np.meshgrid(np.linspace(0, 2*np.pi, 40), np.linspace(0, np.pi, 20))
ax.plot_wireframe(a*np.cos(u)*np.sin(v), a*np.sin(u)*np.sin(v), b*np.cos(v),
                  color='lightgray', linewidth=0.4)

ax.scatter(x, y, z, color='red', s=40, label='Robot')
ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)'); ax.set_zlabel('Z (m)')
ax.set_box_aspect((1, 1, 1))
ax.legend()
plt.show()