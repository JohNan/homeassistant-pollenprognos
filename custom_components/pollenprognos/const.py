from enum import Enum
"""Pollenprognos Custom Update Version."""
NAME = "Pollenprognos"
VERSION = '1.0.0'
DOMAIN = 'pollenprognos'

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

CONF_CITY = 'conf_city'
CONF_ALLERGENS = 'conf_allergens'
CONF_NUMERIC_STATE = 'conf_numeric_state'
CONF_ALLERGENS_MAP = 'conf_allergens_map'
CONF_NAME = 'conf_name'
CONF_URL = 'conf_url'

STATES = {
    "i.h.": 0,
    "L": 1,
    "L-M": 2,
    "M": 3,
    "M-H": 4,
    "H": 5,
    "H-H+": 6,
    "H+": 7
}

SENSOR_ICONS = {
    'al': 'mdi:leaf',
    'alm': 'mdi:leaf',
    'malörtsambrosia': 'mdi:leaf',
    'asp': 'mdi:leaf',
    'bok': 'mdi:leaf',
    'björk': 'mdi:leaf',
    'ek': 'mdi:leaf',
    'gråbo': 'mdi:flower',
    'gräs': 'mdi:flower',
    'hassel': 'mdi:leaf',
    'sälg och viden': 'mdi:leaf',
    'default': 'mdi:leaf'
}

BASE_URL = 'https://api.pollenrapporten.se'

class Endpoints(Enum):
    POLLEN_TYPES = '/v1/pollen-types'
    REGIONS = '/v1/regions'
    FORECASTS = '/v1/forecasts'
    POLLEN_LEVEL_DEFINITIONS = '/v1/pollen-level-definitions'