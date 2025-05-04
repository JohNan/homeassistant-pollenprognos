"""
Support for getting current pollen levels
"""

import logging

from datetime import datetime, timedelta
from typing import Optional, Dict

from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription

from . import PollenprognosConfigEntry, PollenprognosDataUpdateCoordinator
from .api import WeeklyPollenForecast, PollenType, DailyForecast, PollenForecast
from .const import SENSOR_ICONS, CONF_ALLERGENS, CONF_NAME, CONF_NUMERIC_STATE
from .entity import PollenEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: PollenprognosConfigEntry,
        async_add_devices
):
    """Setup sensor platform."""
    coordinator = entry.runtime_data
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

    def __init__(
            self,
            pollen_type: PollenType,
            coordinator: PollenprognosDataUpdateCoordinator,
            config_entry: PollenprognosConfigEntry
    ):
        super().__init__(coordinator, config_entry)
        self._use_numeric_state = config_entry.data.get(CONF_NUMERIC_STATE, False)
        self._pollen_type = pollen_type
        self.entity_id = ENTITY_ID_FORMAT.format(f"pollen_{self.config_entry.data[CONF_NAME]}_{self._pollen_type.name}")
        self.entity_description = EntityDescription(
            device_class=SensorDeviceClass.ENUM if not self._use_numeric_state else None,
            key=self._pollen_type.id,
        )

    @property
    def forecast(self) -> Optional[PollenForecast]:
        return self.coordinator.data.get(self._pollen_type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._pollen_type.name

    @property
    def state(self):
        """Return the state of the device."""
        return self._get_allergen_state(self._use_numeric_state)

    def get_today_forecast(self) -> Optional[DailyForecast]:
        if not self.forecast:
            return None
        today_str = datetime.now().strftime('%Y-%m-%dT00:00:00')
        return self.forecast.get(today_str)

    def get_tomorrow_forecast(self) -> Optional[DailyForecast]:
        if not self.forecast:
            return None
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')
        return self.forecast.get(tomorrow_str)

    def _get_allergen_state(self, numeric_state: bool):
        today = self.get_today_forecast()
        if today:
            return today['level'] if numeric_state else today['level_name']
        return 0 if numeric_state else 'n/a'

    @property
    def extra_state_attributes(self):
        attributes = {
            'forecast': list(self.forecast.values()),
            'tomorrow_raw': self.get_tomorrow_forecast() or "n/a",
            'tomorrow_numeric_state': self.get_tomorrow_forecast().get('level', 0) if self.get_tomorrow_forecast() else None,
            'tomorrow_named_state': self.get_tomorrow_forecast().get('level_name', 0) if self.get_tomorrow_forecast() else None,
            'raw': self.get_today_forecast() or "n/a",
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
