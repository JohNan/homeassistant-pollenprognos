"""
Support for getting current pollen levels from Pollenkollen.se
Visit https://pollenkoll.se/pollenprognos/ to find available cities
Visit https://pollenkoll.se/pollenprognos-ostersund/ to find available states

Example configuration

sensor:
  - platform: pollenkoll
    sensors:
      - city: Stockholm
        state: Gräs
      - city: Östersund
        state: Hassel
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

_LOGGER = logging.getLogger(__name__)
_ENDPOINT = 'https://pollenkoll.se/wp-content/themes/pollenkoll/api/get_cities.php'

ATTR_POLLEN = 'pollen'
ATTR_TODAY = 'day0_value'
ATTR_TYPE = 'type'

DEFAULT_NAME = 'Pollenkoll'
DEFAULT_VERIFY_SSL = True
CONF_SENSORS = 'sensors'

SCAN_INTERVAL = timedelta(hours=12)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_SENSORS, default=[]): cv.ensure_list,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the PVOutput sensor."""
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
    """Representation of a PVOutput sensor."""

    def __init__(self, rest, name, item):
        """Initialize a PVOutput sensor."""
        self._rest = rest
        self._item = item
        self._city = item['city']
        self._state = None
        self._name = name + " " +item['city']
        self._pollen = None
        self._result = None
        self._status = namedtuple(
            'status', [ATTR_POLLEN, ATTR_TODAY, ATTR_TYPE])

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
        if self._pollen is not None:
            return self._pollen

    def update(self):
        """Get the latest data from the PVOutput API and updates the state."""
        try:
            pollen = {}
            self._rest.update()
            self._result = json.loads(self._rest.data)

            for item in self._result:
                if item['name'] in self._city:
                    pollen = item['pollen'];

            self._pollen = {}

            for item in pollen:
                if item['type'] == self._item['state']:
                    self._state = item['type'] + ": " + item['day0_value']
                self._pollen.update({item['type']: item['day0_value']})

        except TypeError as e:
            self._result = None
            _LOGGER.error(
                "Unable to fetch data from Pollenkoll. " + str(e))
