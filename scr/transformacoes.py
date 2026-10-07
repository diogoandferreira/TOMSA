import numpy as np
import pandas as pd

# Carregar os dados de log
df = pd.read_csv('../logs/robot1_s1.csv')

# Referência inicial da superfície fornecida pelo projeto (Aguçadoura)
lat0 = 41.45201666666667
lon0 = -8.81322222222222
h0 = 55.44791126176966

print("Referência inicial carregada com sucesso.")