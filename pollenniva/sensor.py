"""
Support for getting current pollen levels from Pollenkollen.se
Visit https://pollenkoll.se/pollenprognos/ to find available cities
Visit https://pollenkoll.se/pollenprognos-ostersund/ to find available allergens

Example configuration

sensor:
  - platform: pollenniva
    scan_interval: 14400 # (default=14400 seconds (4 hours), optional)
    state_as_string: false # (default=false, optional, show states as strings as per STATES below)
    sensors:
      - city: Stockholm
        days_to_track: 4 # (default=4, values 1-4, optional)
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
from homeassistant.const import (CONF_NAME, CONF_SCAN_INTERVAL)
from homeassistant.util import Throttle
from dateutil import parser
from datetime import datetime
from .const import VERSION

_LOGGER = logging.getLogger(__name__)
_ENDPOINT = 'https://pollenkoll.se/wp-content/themes/pollenkoll/api/get_all.json'

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

DEFAULT_NAME = 'Pollennivå'
DEFAULT_STATE_AS_STRING = False
DEFAULT_DAYS_TO_TRACK = 3

CONF_SENSORS = 'sensors'
CONF_INTERVAL = 'scan_interval'
CONF_STATE_AS_STRING = 'state_as_string'
CONF_DAYS_TO_TRACK = 'days_to_track'
CONF_ALLERGENS = 'allergens'
CONF_CITY = 'city'

SENSOR_SCHEMA = vol.Schema({
    vol.Required(CONF_CITY): cv.string,
    vol.Optional(CONF_ALLERGENS, []): cv.ensure_list,
    vol.Optional(CONF_DAYS_TO_TRACK, default=DEFAULT_DAYS_TO_TRACK):
        vol.All(vol.Coerce(int), vol.Range(min=1, max=4), msg="Only a value between 0-4 is valid"),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_STATE_AS_STRING, default=DEFAULT_STATE_AS_STRING): cv.boolean,
    vol.Required(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
})

SCAN_INTERVAL = timedelta(seconds=14400)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Pollen sensor."""
    name = config.get(CONF_NAME)
    sensors = config.get(CONF_SENSORS)
    state_as_string = config.get(CONF_STATE_AS_STRING)
    scan_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    api = PollenkollAPI(scan_interval)

    devices = []

    for sensor in sensors:
        if CONF_DAYS_TO_TRACK in sensor:
            days_to_track = sensor.get(CONF_DAYS_TO_TRACK, DEFAULT_DAYS_TO_TRACK)
            for day in range(days_to_track):
                for allergen in sensor[CONF_ALLERGENS]:
                    devices.append(PollennivaSensor(api, name, sensor, allergen, state_as_string, day))
        else:
            for allergen in sensor[CONF_ALLERGENS]:
                devices.append(PollennivaSensor(api, name, sensor, allergen, state_as_string))

    add_devices(devices, True)


class PollennivaSensor(Entity):
    """Representation of a Pollen sensor."""

    def __init__(self, api, name, sensor, allergen, state_as_string, day=0):
        """Initialize a Pollen sensor."""
        self._state_as_string = state_as_string
        self._api = api
        self._item = sensor
        self._city = sensor['city']
        self._state = None
        self._day = day
        self._allergen = allergen
        self._name = "{} {} {} day {}".format(name, self._city, self._allergen, str(self._day))
        self._attributes = None

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
        pollen = {}
        self._attributes = {}
        self._api.update()

        for cities in self._api.data:
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


class PollenkollAPI:
    """Get the latest data from Pollenkoll"""

    def __init__(self, interval):
        self._rest = RestData('GET', _ENDPOINT, None, None, None, True)
        self.data = None
        self.available = True
        self.update = Throttle(interval)(self._update)

    def _update(self):
        """Get the data"""
        try:
            self._rest.update()
            self.data = json.loads(self._rest.data)
        except TypeError:
            _LOGGER.error("Unable to fetch data from Pollenkoll. " + str(e))
            self.available = False
