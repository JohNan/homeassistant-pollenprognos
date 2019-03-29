"""
Support for getting current pollen levels from Klart.se
Visit https://www.klart.se/se/pollenprognoser/ to find available cities

States
0 = None
1 = Low
2 = Medium
3 = High
4 = Extra high

Example configuration

sensor:
  - platform: pollenniva
    scan_interval: 4 (default, optional)
    sensors:
      - city: Stockholm
        allergen: Gräs
      - city: Stockholm
        allergen: Hassel
      - city: Östersund
        allergen: Hassel
"""

import logging
import json

from collections import namedtuple
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.sensor.rest import RestData
from homeassistant.const import (CONF_NAME)
from dateutil import parser
from datetime import datetime

_LOGGER = logging.getLogger(__name__)
_ENDPOINT = 'https://api.klart.se/v2/pollen'

STATES = {
    0: "None",
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Extra high"
}

STATES_SV = {
    0: "Inga",
    1: "Låg",
    2: "Måttlig",
    3: "Hög",
    4: "Extra hög"
}

DEFAULT_NAME = 'Pollennivå'
DEFAULT_INTERVAL = 4
DEFAULT_VERIFY_SSL = True
CONF_SENSORS = 'sensors'
CONF_INTERVAL = 'scan_interval'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): cv.string,
    vol.Required(CONF_SENSORS, default=[]): cv.ensure_list,
})

SCAN_INTERVAL = timedelta(hours=DEFAULT_INTERVAL)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Pollen sensor."""
    name = config.get(CONF_NAME)
    sensors = config.get(CONF_SENSORS)
    method = 'GET'
    payload = ''
    auth = ''
    verify_ssl = DEFAULT_VERIFY_SSL
    headers = {}

    rest = RestData(method, _ENDPOINT, auth, headers, payload, verify_ssl)
    rest.update()

    if rest.data is None:
        _LOGGER.error("Unable to fetch data from Pollenkollen")
        return False

    for item in sensors:
        add_devices([PollenkollSensor(rest, name, item)], True)


# pylint: disable=no-member
class PollenkollSensor(Entity):
    """Representation of a Pollen sensor."""

    def __init__(self, rest, name, item):
        """Initialize a Pollen sensor."""
        self._rest = rest
        self._item = item
        self._city = item['city']
        self._state = None
        self._allergen = item['allergen']
        self._name = name + " " + self._city + " " + self._allergen
        self._attributes = None
        self._result = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        if self._state is not None:
            return self._state
        return None

    @property
    def device_state_attributes(self):
        """Return the state attributes of the monitored installation."""
        if self._attributes is not None:
            return self._attributes

    def update(self):
        """Get the latest data from the PVOutput API and updates the state."""
        try:
            pollen = {}
            self._rest.update()
            self._result = json.loads(self._rest.data)

            for item in self._result['items']:
                if item['name'] in self._city:
                    pollen = item['types']

            self._attributes = {}

            for item in pollen:
                for level in item['levels']:
                    dt = parser.parse(level['date'])
                    date = dt.strftime("%Y-%m-%d")
                    if date == datetime.now().strftime("%Y-%m-%d"):
                        if item['name'] == self._allergen:
                            self._state = level['level']
                            self._attributes.update({"alergen_name": item['name']})
                            self._attributes.update({"state_string": STATES.get(self._state)})
                            self._attributes.update({"state_string_sv": STATES_SV.get(self._state)})
                            self._attributes.update({"mapUrl": item['mapUrl']})
                            self._attributes.update({"season_from": item['season']['from']})
                            self._attributes.update({"season_to": item['season']['to']})

        except TypeError as e:
            self._result = None
            _LOGGER.error(
                "Unable to fetch data from Pollenkoll. " + str(e))
