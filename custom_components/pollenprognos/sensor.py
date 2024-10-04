"""
Support for getting current pollen levels
"""

import logging

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from .const import DOMAIN, SENSOR_ICONS, CONF_CITY, CONF_ALLERGENS, CONF_NAME, CONF_ALLERGENS_MAP
from .entity import PollenEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.data:
        return False

    pollen_map = entry.data[CONF_ALLERGENS_MAP]
    pollens = coordinator.data.get('items', [])

    if len(pollens) == 0:
        return False

    allergens = {pollen['pollenId'] : pollen_map[pollen['pollenId']]  for pollen in pollens[0].get('levelSeries', {}) if
                 pollen['pollenId'] in entry.data[CONF_ALLERGENS]}
    async_add_devices([
        PollenSensor(name, allergen, coordinator, entry)
        for (allergen, name) in allergens.items()
    ])

    return True


class PollenSensor(PollenEntity):
    """Representation of a Pollen sensor."""

    def __init__(self, name, allergen_id, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._allergen_id = allergen_id
        self._name = name
        self.entity_id = ENTITY_ID_FORMAT.format(f"pollen_{self.config_entry.data[CONF_NAME]}_{self._allergen_id}")

    @property
    def _allergen(self):
        cities = self.coordinator.data.get('items', [])
        if len(cities) == 0:
            return None

        return next(item for item in cities[0].get('levelSeries', []) if item['pollenId'] == self._allergen_id)

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
        return SENSOR_ICONS.get(self._allergen_id, 'default')
