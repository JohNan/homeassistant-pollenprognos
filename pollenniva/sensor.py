"""
Support for getting current pollen levels from Pollenkollen.se
Visit https://pollenkoll.se/pollenprognos/ to find available cities
Visit https://pollenkoll.se/pollenprognos-ostersund/ to find available allergens

Example configuration

sensor:
  - platform: pollenniva
    scan_interval: 4 # (default, optional)
    state_as_string: false # (default, optional, show states as strings as per STATES below)
    sensors:
      - city: Stockholm
        days_to_track: 3 # (0-4, optional)
        allergens:
          - Gräs
          - Hassel
      - city: Östersund
        allergens:
          - Hassel
"""

import logging
import json

from collections import namedtuple
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.rest.sensor import RestData
from homeassistant.const import (CONF_NAME)
from dateutil import parser
from datetime import datetime

_LOGGER = logging.getLogger(__name__)
_ENDPOINT = 'https://pollenkoll.se/wp-content/themes/pollenkoll/api/get_all.json'

VERSION = '1.0.0'

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

DEFAULT_NAME = 'Pollennivå'
DEFAULT_STATE_AS_STRING = False
DEFAULT_VERIFY_SSL = True
CONF_SENSORS = 'sensors'
CONF_INTERVAL = 'scan_interval'
CONF_STATE_AS_STRING = 'state_as_string'

SENSOR_OPTIONS = {
    'city': ('Stad'),
    'allergens': ('Allergener'),
    'days_to_track': ('Antal dagar framåt (0-3)')
}

SENSOR_ICONS = {
    'Al': 'mdi:leaf',
    'Alm': 'mdi:leaf',
    'Asp': 'mdi:leaf',
    'Björk': 'mdi:leaf',
    'Ek': 'mdi:leaf',
    'Gråbo': 'mdi:flower',
    'Gräs': 'mdi:flower',
    'Hassel': 'mdi:leaf',
    'Sälg': 'mdi:leaf',
    'default': 'mdi:leaf'
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_STATE_AS_STRING, default=DEFAULT_STATE_AS_STRING): cv.boolean,
    vol.Required(CONF_SENSORS, default=[]): vol.Optional(cv.ensure_list, [vol.In(SENSOR_OPTIONS)]),
})

SCAN_INTERVAL = timedelta(hours=4)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Pollen sensor."""
    name = config.get(CONF_NAME)
    sensors = config.get(CONF_SENSORS)
    state_as_string = config.get(CONF_STATE_AS_STRING)
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

    devices = []

    for sensor in sensors:
        if 'days_to_track' in sensor:
            for day in range(int(sensor['days_to_track'])):
                for allergen in sensor['allergens']:
                    devices.append(PollenkollSensor(rest, name, sensor, allergen, state_as_string, day))
        else:
            for allergen in sensor['allergens']:
                devices.append(PollenkollSensor(rest, name, sensor, allergen, state_as_string))

    add_devices(devices, True)


# pylint: disable=no-member
class PollenkollSensor(Entity):
    """Representation of a Pollen sensor."""

    def __init__(self, rest, name, sensor, allergen, state_as_string, day=0):
        """Initialize a Pollen sensor."""
        self._state_as_string = state_as_string
        self._rest = rest
        self._item = sensor
        self._city = sensor['city']
        self._state = None
        self._day = day
        self._allergen = allergen
        self._name = "{} {} {} day {}".format(name, self._city, self._allergen, str(self._day))
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

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        if self._allergen in SENSOR_ICONS:
            return SENSOR_ICONS[self._allergen]
        return SENSOR_ICONS['default']

    def update(self):
        """Get the latest data from the API and updates the state."""
        try:
            pollen = {}
            self._rest.update()
            self._result = json.loads(self._rest.data)
            self._attributes = {}

            for cities in self._result:
                for city in cities['CitiesData']:
                    if city['name'] in self._city:
                        self._attributes.update({"last_modified": city['date_mod']})
                        self._attributes.update({"city": city['name']})
                        pollen = city['pollen']

            for allergen in pollen:
                if allergen['type'] == self._allergen:
                    day_value = 'day' + str(self._day) + '_value'
                    if day_value in allergen:
                        if self._state_as_string is False and allergen[day_value] in STATES:
                            value = STATES[allergen[day_value]]
                        else:
                            value = allergen[day_value]
                        self._state = value
                        self._attributes.update({"allergen": allergen['type']})
                        self._attributes.update({"level": allergen[day_value]})
                        self._attributes.update({"relative_day": allergen['day' + str(self._day) + '_relative_date']})
                        self._attributes.update({"day": allergen['day' + str(self._day) + '_name']})
                        self._attributes.update({"date": allergen['day' + str(self._day) + '_date']})
                        self._attributes.update({"description": allergen['day' + str(self._day) + '_desc']})

        except TypeError as e:
            self._result = None
            _LOGGER.error(
                "Unable to fetch data from Pollenkoll. " + str(e))
