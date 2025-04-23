"""
Support for getting current pollen levels
"""

import logging

from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorDeviceClass
from homeassistant.helpers.entity import EntityDescription

from .const import DOMAIN, SENSOR_ICONS, CONF_CITY, CONF_ALLERGENS, CONF_NAME, CONF_ALLERGENS_MAP, CONF_NUMERIC_STATE
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
        self._use_numeric_state = config_entry.data.get(CONF_NUMERIC_STATE, False)
        self._pollen_type = pollen_type
        self.entity_id = ENTITY_ID_FORMAT.format(f"pollen_{self.config_entry.data[CONF_NAME]}_{self._pollen_type.name}")
        self.entity_description = EntityDescription(
            device_class=SensorDeviceClass.ENUM if not self._use_numeric_state else None,
            key=self._pollen_type.id,
        )


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
        return self._get_allergen_state(self._use_numeric_state)

    def _get_allergen_state(self, numeric_state: bool):
        allergen = next(self._allergen)
        if allergen and allergen[-1]:
            if numeric_state:
                return allergen[-1]['level']
            else:
                return allergen[-1]['level_name']

        if numeric_state:
            return 0
        else:
            return 'n/a'

    @property
    def extra_state_attributes(self):
        attributes = {
            'forecast': dict(self._allergen),
            'tomorrow_raw': list(self._allergen)[1] if len(list(self._allergen)) > 1 else "n/a",
            'tomorrow_numeric_state': list(self._allergen)[1][-1]['level'] if len(list(self._allergen)) > 1 else 0,
            'tomorrow_named_state': list(self._allergen)[1][-1]['level_name'] if len(list(self._allergen)) > 1 else "n/a",
            'numeric_state': self._get_allergen_state(numeric_state=True),
            'named_state': self._get_allergen_state(numeric_state=False),
        }
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return SENSOR_ICONS.get(self._pollen_type.name.lower(), 'default')
