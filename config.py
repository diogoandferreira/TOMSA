import copy
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'config.yaml'

DEFAULTS = {
    'logs_dir': 'logs',
    'map': {'center': [41.4520, -8.8132], 'zoom': 17},
    'playback': {'interval_ms': 500, 'speeds': [1, 2, 5, 10, 30, 60], 'default_speed': 1},
    'radar': {'reference': None, 'origin': {'lat': None, 'lon': None, 'h': None}},
    'colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'],
    'robots': {},
}


def _merge(base, override):
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict) and key != 'robots':
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path=CONFIG_PATH):
    try:
        with open(path, encoding='utf-8') as f:
            user = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f'[config] {path} não encontrado; a usar valores por defeito.')
        user = {}
    except yaml.YAMLError as error:
        raise SystemExit(f'[config] YAML inválido em {path}:\n{error}')
    if not isinstance(user, dict):
        raise SystemExit(f'[config] {path} tem de ser um mapa chave: valor.')

    config = _merge(DEFAULTS, user)
    pb = config['playback']
    if pb['interval_ms'] <= 0 or not pb['speeds'] or pb['default_speed'] not in pb['speeds']:
        raise SystemExit('[config] playback inválido: interval_ms > 0, speeds não vazio e default_speed em speeds.')
    return config


CONFIG = load_config()
LOGS_DIR = (BASE_DIR / CONFIG['logs_dir']).resolve()


def robot_color(file_path, index):
    name = Path(file_path).name
    custom = CONFIG['robots'].get(name, {}).get('color')
    return custom or CONFIG['colors'][index % len(CONFIG['colors'])]


def robot_label(file_path):
    name = Path(file_path).name
    return CONFIG['robots'].get(name, {}).get('label') or Path(file_path).stem


def pick_radar_ref(file_paths):
    """Ficheiro de referência do radar: o do YAML se existir, senão o primeiro."""
    wanted = CONFIG['radar']['reference']
    for path in file_paths:
        if wanted and Path(path).name == wanted:
            return path
    return file_paths[0] if file_paths else None