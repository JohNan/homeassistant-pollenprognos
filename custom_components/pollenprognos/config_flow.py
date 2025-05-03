import asyncio
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PollenApi
from .const import DOMAIN, CONF_ALLERGENS, CONF_NAME, CONF_CITY, CONF_NUMERIC_STATE

_LOGGER: logging.Logger = logging.getLogger(__package__)


class PollenprognosFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    fetch_cities_task: asyncio.Task | None = None
    fetch_pollen_types_task: asyncio.Task | None = None
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.data = None
        self.pollen_types = None
        self._init_info = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        try:
            return await self.async_step_select_city()
        except vol.Invalid:
            errors["base"] = "bad_host"

        return self.async_show_form(
            step_id="user",
            errors=errors
        )

    async def async_step_fetch_cities(self, user_input=None):
        if not self.fetch_cities_task:
            self.fetch_cities_task = self.hass.async_create_task(
                self._async_task_fetch_cities(),
                "Fetch cities",
                eager_start=False,
            )

        if not self.fetch_cities_task.done():
            return self.async_show_progress(
                step_id="fetch_cities",
                progress_action="fetch_cities",
                progress_task=self.fetch_cities_task
            )

        try:
            await self.fetch_cities_task
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Failed to fetched cities", err)
            return self.async_show_progress_done(next_step_id="fetch_failed")
        finally:
            self.fetch_cities_task = None

        return self.async_show_progress_done(next_step_id="select_city")

    async def async_step_fetch_pollen_types(self, user_input=None):
        if not self.fetch_pollen_types_task:
            self.fetch_pollen_types_task = self.hass.async_create_task(
                self._async_task_fetch_pollen_types(),
                "Fetch pollen types",
                eager_start=False,
            )

        if not self.fetch_pollen_types_task.done():
            return self.async_show_progress(
                step_id="fetch_pollen_types",
                progress_action="fetch_pollen_types",
                progress_task=self.fetch_pollen_types_task
            )

        try:
            await self.fetch_pollen_types_task
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Failed to fetch pollen types", err)
            return self.async_show_progress_done(next_step_id="fetch_failed")
        finally:
            self.fetch_pollen_types_task = None

        return self.async_show_progress_done(next_step_id="select_pollen")

    async def async_step_fetch_failed(self, user_input=None):
        """Fetching pollen data failed."""
        return self.async_abort(reason="fetch_data_failed")

    async def async_step_select_city(self, user_input=None):
        if user_input is not None:
            self._init_info[CONF_CITY] = user_input[CONF_CITY]
            self._init_info[CONF_NAME] = next(item for item in self.data if item.region_id == self._init_info[CONF_CITY]).name
            return await self.async_step_select_pollen()

        if self.data is None:
            await self._async_task_fetch_cities()

        cities = {city.region_id: city.name for city in self.data}
        return self.async_show_form(
            step_id="select_city",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY, default=list(cities.keys())): vol.In(cities)
                }
            )
        )

    async def async_step_select_pollen(self, user_input=None):
        if user_input is not None:
            self._init_info[CONF_ALLERGENS] = user_input[CONF_ALLERGENS]
            self._init_info[CONF_NUMERIC_STATE] = user_input[CONF_NUMERIC_STATE]
            await self.async_set_unique_id(f"{self._init_info[CONF_CITY]}-{self._init_info[CONF_NAME]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._init_info[CONF_NAME], data=self._init_info
            )

        if self.pollen_types is None:
            await self._async_task_fetch_pollen_types()

        pollen = {pollen.id: pollen.name for pollen in self.pollen_types}

        return self.async_show_form(
            step_id="select_pollen",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ALLERGENS, default=list(pollen.keys())): cv.multi_select(pollen),
                    vol.Optional(CONF_NUMERIC_STATE, default=False): bool
                }
            )
        )

    async def _async_task_fetch_cities(self):
        client = PollenApi(session=async_get_clientsession(self.hass))
        self.data = await client.async_get_cities()
        _LOGGER.debug("Fetched data: %s", self.data)

    async def _async_task_fetch_pollen_types(self):
        client = PollenApi(session=async_get_clientsession(self.hass))
        self.pollen_types = await client.async_get_pollen_types()
        _LOGGER.debug("Fetched data: %s", self.pollen_types)
