"""
Support for getting current pollen levels
"""

import logging

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from .const import DOMAIN, SENSOR_ICONS, CONF_CITY, CONF_ALLERGENS, CONF_NAME, CONF_ALLERGENS_MAP
from .entity import PollenEntity
from .api import PollenType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.data:
        return False

    pollens = coordinator.data

    if len(pollens) == 0:
        return False
    async_add_devices([
        PollenSensor(pollen, coordinator, entry)
        for pollen in pollens if pollen.id in entry.data[CONF_ALLERGENS]
    ])

    return True


class PollenSensor(PollenEntity):
    """Representation of a Pollen sensor."""

    def __init__(self, pollen_type: PollenType, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._pollen_type = pollen_type
        self.entity_id = ENTITY_ID_FORMAT.format(f"pollen_{self.config_entry.data[CONF_NAME]}_{self._pollen_type.id}")

    @property
    def _allergen(self):
        return iter(self.coordinator.data[self._pollen_type].items())

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._pollen_type.name

    @property
    def state(self):
        """Return the state of the device."""
        return next(self._allergen, (-1,))[-1]

    @property
    def extra_state_attributes(self):
        attributes = {'forecast': dict(self._allergen)}
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return SENSOR_ICONS.get(self._pollen_type.id, 'default')
