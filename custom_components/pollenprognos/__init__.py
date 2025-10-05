"""Pollenprognos Custom Component."""
import logging
from datetime import timedelta, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed, DataUpdateCoordinator

from .api import PollenApi, WeeklyPollenForecast
from .const import DOMAIN, CONF_URL, CONF_CITY

_LOGGER: logging.Logger = logging.getLogger(__package__)
PLATFORMS = [Platform.SENSOR]
SCAN_INTERVAL = timedelta(hours=4)

type PollenprognosConfigEntry = ConfigEntry[PollenprognosDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PollenprognosConfigEntry):
    """Set up this integration using UI."""
    client = PollenApi(session=async_get_clientsession(hass))

    coordinator = PollenprognosDataUpdateCoordinator(hass, client=client, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PollenprognosConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: PollenprognosConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


class PollenprognosDataUpdateCoordinator(DataUpdateCoordinator[WeeklyPollenForecast]):
    """Class to manage fetching data from the API."""

    def __init__(
            self,
            hass: HomeAssistant,
            entry: PollenprognosConfigEntry,
            client: PollenApi
    ) -> None:
        """Initialize."""
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._entry = entry
        self._api = client
        self._region_id = self._entry.data[CONF_CITY]
        self.last_updated = None

    async def _async_setup(self):
        await self._api.async_get_pollen_level_definitions()
        await self._api.async_get_pollen_types()

    async def _async_update_data(self):
        """Update data via library."""
        try:
            data = await self._api.async_get_forecast(region_id=self._region_id)
            self.last_updated = datetime.now()
            return data
        except Exception as exception:
            raise UpdateFailed() from exception
