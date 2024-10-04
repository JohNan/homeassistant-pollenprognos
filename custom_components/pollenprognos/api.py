import asyncio
import enum
import logging
import socket
import urllib.parse
from sqlite3.dbapi2 import paramstyle
from typing import Dict

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {
    "accept": "application/json"
}

class PollenType:
    id: str
    name: str

    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

class Pollen:
    pollen_type: PollenType
    level: str
    time: str


class City:
    region_id: str
    name: str

    def __init__(self, region_id: str, name: str):
        self.region_id = region_id
        self.name = name

class Forecast:
    city: City
    pollen_levels: list[Pollen]

    def __init__(self, city: City, pollen_levels: list[Pollen]):
        self.city = city
        self.pollen_levels = pollen_levels

class PollenApi:
    pollen_types: list[PollenType] = None
    cities: list[City] = None

    def __init__(self, hass: HomeAssistant, url) -> None:
        self._hass = hass
        self._url: str = url

    async def async_get_pollen_types(self) -> list[PollenType]:
        if self.pollen_types is None:
            response = await self.request(
                "get",
                "https://api.pollenrapporten.se/v1/pollen-types?offset=0&limit=100"
            )
            self.pollen_types = [
                PollenType(pollen['id'], pollen['name'])
                for pollen in response.get('items', [])
            ]

        return self.pollen_types

    async def async_get_cities(self) -> list[City]:
        if self.cities is None:
            response = await self.request(
                "get",
                "https://api.pollenrapporten.se/v1/regions?offset=0&limit=100"
            )
            self.cities = [
                City(pollen['id'], pollen['name'])
                for pollen in response.get('items', [])
            ]

        return self.cities

    async def async_get_forecast(self, region_id: str) -> list[City]:
        response = await self.request(
            "get",
            f"https://api.pollenrapporten.se/v1/forecasts?region_id={region_id}&offset=0&limit=100"
        )

        return self.cities

    async def async_request_(self, query_params=dict) -> dict:
        """Get data from the API."""
        url_parts = urllib.parse.urlparse(self._url)
        query = dict(urllib.parse.parse_qsl(url_parts.query))
        query.update(query_params)
        url = url_parts._replace(query=urllib.parse.urlencode(query)).geturl()
        return await self.request("get", url)

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        return await self.request("get", self._url)

    async def async_get_data_with_params(self, query_params=dict) -> dict:
        """Get data from the API."""
        url_parts = urllib.parse.urlparse(self._url)
        query = dict(urllib.parse.parse_qsl(url_parts.query))
        query.update(query_params)
        url = url_parts._replace(query=urllib.parse.urlencode(query)).geturl()
        return await self.request("get", url)

    async def request(
            self, method: str, url: str, data: dict = {}, headers: dict = {}
    ) -> dict:
        """Get information from the API."""
        try:
            session = async_get_clientsession(self._hass)
            async with async_timeout.timeout(TIMEOUT):
                if method == "get":
                    response = await session.get(url, headers=headers)
                    return await response.json()

                elif method == "put":
                    await session.put(url, headers=headers, json=data)

                elif method == "patch":
                    await session.patch(url, headers=headers, json=data)

                elif method == "post":
                    await session.post(url, headers=headers, json=data)

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
