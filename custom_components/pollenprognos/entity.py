"""PollenEntity class"""
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION, CONF_NAME


class PollenEntity(CoordinatorEntity):
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-{self.name}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.config_entry.data[CONF_NAME])},
            "name": f"{NAME} {self.config_entry.data[CONF_NAME]}",
            "model": VERSION,
            "manufacturer": "Pollenprognos",
        }

    @property
    def add_state_attributes(self):
        """Return the state attributes."""
        return {
            "update_success": self.coordinator.last_update_success,
            "last_updated": self.coordinator.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.coordinator.last_updated else None
        }
