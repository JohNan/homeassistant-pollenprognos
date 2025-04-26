import asyncio
import enum
import logging
import socket
import urllib.parse
from sqlite3.dbapi2 import paramstyle
from typing import Dict
from dataclasses import dataclass
from .const import BASE_URL, Endpoints

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {
    "accept": "application/json"
}

@dataclass
class PollenType:
    id: str
    name: str

    def __hash__(self):
        return hash((self.id))
    
    def __eq__(self, other):
        if isinstance(other, PollenType):
            return self.id == other.id
        elif isinstance(other, str):
            return self.id == other
        return False
    
@dataclass
class Pollen:
    pollen_type: PollenType
    level: str
    time: str

@dataclass
class City:
    region_id: str
    name: str

class Forecast:
    city: City
    pollen_levels: list[Pollen]

    def __init__(self, city: City, pollen_levels: list[Pollen]):
        self.city = city
        self.pollen_levels = pollen_levels

class PollenApi:
    pollen_types: list[PollenType] = None
    cities: list[City] = None
    forecast: dict[PollenType, dict[str, dict[str, str]]] = None
    pollen_level_definitions: list[str] = None

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def async_get_pollen_types(self) -> list[PollenType]:
        if self.pollen_types is None:
            response = await self.request(
                "get",
                BASE_URL + Endpoints.POLLEN_TYPES.value
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
                BASE_URL + Endpoints.REGIONS.value
            )
            self.cities = [
                City(city['id'], city['name'])
                for city in response.get('items', [])
            ]
        return self.cities

    async def async_get_forecast(self, region_id: str = ''):
        if self.forecast is None:
            if self.cities is None:
                await self.async_get_cities()
            if region_id == '':
                region_id = self.cities[0].region_id
            response = await self.request(
                "get",
                f"{BASE_URL}{Endpoints.FORECASTS.value}?region_id={region_id}&current=true"
            )
            forecast = {pollen: {} for pollen in self.pollen_types}
            for item in response.get('items',[])[0].get('levelSeries',[]):
                pollen_id = item['pollenId']
                forecast[pollen_id][item['time']] = {
                    'level_name': self.pollen_level_definitions[item['level']],
                    'level': item['level'],
                }
            self.forecast = forecast
        return self.forecast
    
    async def async_get_pollen_level_definitions(self):
        if self.pollen_level_definitions is None:
            response = await self.request(
                "get",
                BASE_URL + Endpoints.POLLEN_LEVEL_DEFINITIONS.value
            )
            self.pollen_level_definitions = [item['name'] for item in response.get('items', [])]
        return self.pollen_level_definitions

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
