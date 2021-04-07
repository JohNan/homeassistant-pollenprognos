import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .api import PollenApi
from homeassistant import config_entries
from .const import DOMAIN, CONF_ALLERGENS, CONF_NAME, CONF_CITY, CONF_URL
from homeassistant.helpers.aiohttp_client import async_create_clientsession

_LOGGER: logging.Logger = logging.getLogger(__package__)


class PollenprognosFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.data = None
        self.task_fetch_cities = None
        self._init_info = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            try:
                cv.url(user_input.get(CONF_URL, ""))
                self._init_info[CONF_URL] = user_input[CONF_URL]
                return await self.async_step_fetch_cities(url=user_input.get(CONF_URL, ""))
            except vol.Invalid:
                errors["base"] = "bad_host"

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=""): str
                }
            )
        )

    async def async_step_fetch_cities(self, url=None):
        if not self.task_fetch_cities:
            self.task_fetch_cities = self.hass.async_create_task(self._async_task_fetch_cities(url))
            return self.async_show_progress(
                step_id="fetch_cities",
                progress_action="fetch_cities",
            )

        # noinspection PyBroadException
        try:
            await self.task_fetch_cities
        except Exception:  # pylint: disable=broad-except
            return self.async_show_progress_done(next_step_id="fetch_failed")

        if self.data is None:
            return self.async_show_progress_done(next_step_id="fetch_failed")

        return self.async_show_progress_done(next_step_id="select_city")

    async def async_step_fetch_failed(self, user_input=None):
        """Fetching pollen data failed."""
        return self.async_abort(reason="fetch_data_failed")

    async def async_step_select_city(self, user_input=None):
        if user_input is not None:
            self._init_info[CONF_CITY] = user_input[CONF_CITY]
            self._init_info[CONF_NAME] = next(item for item in self.data.get('cities', []).get('cities', []) if
                 item["id"] == self._init_info[CONF_CITY])['name']
            return await self.async_step_select_pollen()

        cities = {city['id']: city['name'] for city in self.data.get('cities', []).get('cities', []) }
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
            await self.async_set_unique_id(f"{self._init_info[CONF_CITY]}-{self._init_info[CONF_NAME]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._init_info[CONF_NAME], data=self._init_info
            )

        pollen = {pollen['type_code']: pollen['type'] for pollen in self.data.get('pollen_types', [])}
        return self.async_show_form(
            step_id="select_pollen",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ALLERGENS, default=list(pollen.keys())): cv.multi_select(pollen)
                }
            )
        )

    async def _async_task_fetch_cities(self, url):
        try:
            session = async_create_clientsession(self.hass)
            client = PollenApi(session, url)
            self.data = await client.async_get_data()
            _LOGGER.debug("Fetched data: %s", self.data)
        finally:
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
            )