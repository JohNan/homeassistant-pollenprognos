"""Pollenprognos Custom Update Version."""
NAME = "Pollenprognos"
VERSION = '1.0.0'
DOMAIN = 'pollenprognos'

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

CONF_CITY = 'conf_city'
CONF_ALLERGENS = 'conf_allergens'
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
    'ambrosia': 'mdi:leaf',
    'asp': 'mdi:leaf',
    'bok': 'mdi:leaf',
    'bjork': 'mdi:leaf',
    'ek': 'mdi:leaf',
    'grabo': 'mdi:flower',
    'gras': 'mdi:flower',
    'hassel': 'mdi:leaf',
    'salg_vide': 'mdi:leaf',
    'default': 'mdi:leaf'
}
