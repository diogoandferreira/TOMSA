import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# 1. Definir a rota (exemplo: uma espiral)
t = np.linspace(0, 4 * np.pi, 200)
x = t * np.sin(t)
y = t * np.cos(t)

# 2. Configurar a figura e os eixos do gráfico
fig, ax = plt.subplots(figsize=(6, 6))
ax.plot(x, y, label='Rota', color='blue', linestyle='--', alpha=0.6)
# Criar o símbolo (ponto vermelho 'ro') que vai percorrer a rota
simbolo, = ax.plot([], [], 'ro', markersize=8, label='Objeto')

# 3. Função de inicialização do gráfico
def init():
    ax.set_xlim(min(x) - 1, max(x) + 1)
    ax.set_ylim(min(y) - 1, max(y) + 1)
    ax.legend()
    return simbolo,

# 4. Função de atualização (chamada a cada frame)
def atualizar(frame):
    # Atualiza a posição do símbolo com as coordenadas atuais da rota
    simbolo.set_data([x[frame]], [y[frame]])
    return simbolo,

# 5. Criar a animação
# 'interval' define o tempo entre frames em milissegundos
ani = animation.FuncAnimation(
    fig, 
    atualizar, 
    frames=len(t), 
    init_func=init, 
    blit=True, 
    interval=30
)

plt.title("Símbolo a Percorrer a Rota")
plt.grid(True)
plt.show()
