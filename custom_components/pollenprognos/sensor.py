"""
Support for getting current pollen levels
"""

import logging
import json

from collections import namedtuple
from datetime import timedelta
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import ENTITY_ID_FORMAT

from dateutil import parser
from datetime import datetime
from .const import VERSION, DOMAIN, SENSOR_ICONS, CONF_CITY, CONF_ALLERGENS, CONF_NAME
from .entity import PollenEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.data:
        return False

    city = next(item for item in coordinator.data.get('cities', []).get('cities', []) if item["id"] == entry.data[CONF_CITY])
    allergens = {pollen['type_code']: pollen['type'] for pollen in city.get('pollen', []) if pollen['type_code'] in entry.data[CONF_ALLERGENS]}
    async_add_devices([
        PollenSensor(name, allergen, coordinator, entry)
        for (allergen, name) in allergens.items()
    ])

    return True


class PollenSensor(PollenEntity):
    """Representation of a Pollen sensor."""

    def __init__(self, name, allergen_type, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._allergen_type = allergen_type
        self._name = name
        self.entity_id = ENTITY_ID_FORMAT.format(f"pollen_{self.config_entry.data[CONF_NAME]}_{self._allergen_type}")

    @property
    def _allergen(self):
        city = next(item for item in self.coordinator.data.get('cities', []).get('cities', []) if
                    item["id"] == self.config_entry.data[CONF_CITY])
        return next(item for item in city.get('pollen', []) if item['type_code'] == self._allergen_type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        today = next(item for item in self._allergen.get('days', []) if item['day'] == 0)
        state = today.get('level', 'n/a')
        return 0 if state == -1 else state

    @property
    def extra_state_attributes(self):
        attributes = {day['date_realtive']: day['level'] for day in self._allergen.get('days', []) if day['day'] != 0}
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return SENSOR_ICONS.get(self._allergen_type, 'default')
