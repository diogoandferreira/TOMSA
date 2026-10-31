# TOMSA: Análise de logs

Dashboard web em Python/Dash que reproduz missões a partir de logs ROS (CSV) e mostra as trajetórias de vários robots num mapa 2D, numa vista 3D e num radar de distâncias calculado em coordenadas NED.

Trabalho de TOMSA, ISEP (MEEC/SA), 2026.

## Funcionalidades

- **Mapa 2D** (OpenStreetMap + OpenSeaMap) 

- **Vista 3D** 

- **Reprodução da missão:** 

- **Gráficos** 

- **Radar de distâncias:**

- **Configuração em YAML** (`config.yaml`): pasta dos logs, mapa, reprodução, cores e nomes dos robots, origem do radar.

## Estrutura do projeto

```
TOMSA/
├── README.md
├── requirements.txt
├── app.py                     # arranque da aplicação
├── layout.py                  # estrutura da página
├── callbacks.py               # lógica: replay, 3D, radar, gráficos
├── config.py                  # leitura do config.yaml
├── config.yaml                # configuração
├── assets/
│   └── custom.css             # estilos (carregados automaticamente pelo Dash)
├── logs/                      # logs CSV dos robots (um ficheiro por robot)
│   ├── robot1_s1.csv
│   ├── robot4_s1.csv
│   └── robot7_s1.csv
└── TOMSA_TL2_GRUPO12.ipynb    # relatório
```

A pasta dos logs é indicada em `config.yaml` (`logs_dir: logs`), relativa à pasta onde está o `config.yaml`.

## Requisitos

- Python 3.11 ou superior (desenvolvido em Python 3.14, com miniconda).
- Ligação à internet.

## Instalação passo a passo

### 1. Obter o código

```bash
git clone <URL-DO-REPOSITÓRIO> TOMSA
cd TOMSA
```

### 2. Criar um ambiente isolado

Com conda:

```bash
conda create -n tomsa python=3.12 -y
conda activate tomsa
```

Ou com `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate         
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

Para confirmar a instalação:

```bash
pip show dash dash-leaflet plotly pandas pyyaml pymap3d
```

O Dash tem de ser da versão 4 ou superior.

### 4. Ajustar a configuração (opcional)

Edita `config.yaml`. As opções estão descritas na secção seguinte.

### 5. Arrancar o dashboard

```bash
python app.py
```

Abre no browser: **http://127.0.0.1:8051**

Para parar o servidor, usa Ctrl+C no terminal.


## Formato dos logs

CSV com cabeçalho e as colunas seguintes (as restantes são ignoradas):

| Informação temporal
| Referenciais
| Pose
| Velocidades


## Configuração (`config.yaml`)

| Chave | O que faz |
|---|---|
| `logs_dir` | Pasta dos logs, relativa à pasta do `config.yaml` (por defeito `logs`) |
| `map.center`, `map.zoom` | Centro `[lat, lon]` e zoom inicial do mapa 2D |
| `playback.interval_ms` | Período do relógio da reprodução (ms) |
| `playback.speeds`, `playback.default_speed` | Velocidades disponíveis e velocidade inicial |
| `radar.reference` | Referência do radar ao arrancar: `origin`, o nome de um CSV, ou `null` (primeiro log) |
| `radar.origin.lat/lon/h` | Origem NED do radar; `null` usa o primeiro ponto do primeiro log, com `h` na superfície do mar |
| `colors` | Paleta usada quando um robot não tem cor própria |
| `robots` | Nome (`label`) e cor de cada robot, indexados pelo nome do CSV |

Exemplo da referência inicial da missão:

O ficheiro só é lido no arranque: depois de o editar, reinicia o servidor. Se faltar o ficheiro ou alguma chave, usam-se valores por defeito.


## Utilização

1. Escolhe no cabeçalho um robot, ou "Todas as trajetórias".
2. Usa o botão **Reproduzir**, o seletor de velocidade e o slider de tempo, na barra de baixo.
3. Na vista 3D podes rodar e fazer zoom com o rato.
4. No radar, escolhe a referência: "Ponto inicial" ou um robot. O raio é a distância horizontal em metros e o ângulo é o azimute, a partir do norte, no sentido horário.

## Referenciais e contas

As posições (lat, lon, h) são convertidas para ECEF (elipsoide WGS84) e depois para NED, com origem na referência escolhida. Daí saem a distância horizontal, a distância 3D e o azimute. Esta conversão é a que está validada em `validate_ned.py`.
