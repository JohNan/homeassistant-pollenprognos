"""PollenEntity class"""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PollenprognosConfigEntry, PollenprognosDataUpdateCoordinator
from .const import DOMAIN, NAME, CONF_NAME


class PollenEntity(CoordinatorEntity):
    _attr_attribution = "Palynologiska laboratoriet vid Naturhistoriska riksmuseet"

    def __init__(
            self,
            coordinator: PollenprognosDataUpdateCoordinator,
            config_entry: PollenprognosConfigEntry
    ):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.data[CONF_NAME])},
            name=f"{NAME} {self.config_entry.data[CONF_NAME]}"
        )

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-{self.name}"

    @property
    def add_state_attributes(self):
        """Return the state attributes."""
        return {
            "update_success": self.coordinator.last_update_success,
            "last_updated": self.coordinator.last_updated.strftime(
                "%Y-%m-%d %H:%M:%S") if self.coordinator.last_updated else None
        }
