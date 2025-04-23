"""Pollenprognos Custom Component."""
import asyncio
import logging
from datetime import timedelta, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed, DataUpdateCoordinator
from .api import PollenApi
from .const import DOMAIN, PLATFORMS, CONF_URL, CONF_CITY

SCAN_INTERVAL = timedelta(hours=4)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    client = PollenApi(hass)

    coordinator = PollenprognosDataUpdateCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady
    
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        coordinator.platforms.append(platform)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

class PollenprognosDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
            self, hass: HomeAssistant, client: PollenApi
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.last_updated = None

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_setup(self):
        await self.api.async_get_pollen_level_definitions()
        await self.api.async_get_pollen_types()

    async def _async_update_data(self):
        """Update data via library."""
        try:
            data = await self.api.async_get_forecast()
            self.last_updated = datetime.now()
            return data
        except Exception as exception:
            raise UpdateFailed() from exception
