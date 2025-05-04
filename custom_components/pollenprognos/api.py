import asyncio
import logging
import socket
from dataclasses import dataclass
from typing import Any, Dict

import aiohttp
import async_timeout
from aiohttp import ClientSession

from .const import BASE_URL, Endpoints

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {
    "accept": "application/json"
}

type WeeklyPollenForecast = Dict[PollenType, Dict[str, Dict[str, str]]]
type PollenForecast = Dict[str, Dict[str, str]]
type DailyForecast = Dict[str, str]


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
    level: int
    named_level: str
    time: str


@dataclass
class City:
    region_id: str
    name: str


class PollenApi:
    _pollen_types: list[PollenType] = None
    _cities: list[City] = None
    _pollen_level_definitions: list[str] = None

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_pollen_types(self) -> list[PollenType]:
        if self._pollen_types is None:
            response = await self.get_request(f"{BASE_URL}{Endpoints.POLLEN_TYPES}")
            self._pollen_types = [
                PollenType(pollen['id'], pollen['name'])
                for pollen in response.get('items', [])
            ]
        return self._pollen_types

    async def async_get_cities(self) -> list[City]:
        if self._cities is None:
            response = await self.get_request(f"{BASE_URL}{Endpoints.REGIONS}")
            self._cities = [
                City(city['id'], city['name'])
                for city in response.get('items', [])
            ]
        return self._cities

    async def async_get_forecast(self, region_id: str = ''):
        if self._cities is None:
            await self.async_get_cities()
        if region_id is None or region_id == '':
            _LOGGER.warning(f"No region id provided. Defaulting to '{self._cities[0].name}'.")
            region_id = self._cities[0].region_id

        try:
            response = await self.get_request(
                f"{BASE_URL}{Endpoints.FORECASTS}?region_id={region_id}&current=true"
            )
            forecast: WeeklyPollenForecast = {pollen: {} for pollen in self._pollen_types}
            for item in response.get('items', [])[0].get('levelSeries', []):
                pollen_id = item['pollenId']
                forecast[pollen_id][item['time']] = {
                    'time': item['time'],
                    'level_name': self._pollen_level_definitions[item['level']],
                    'level': item['level'],
                }

            return forecast
        except Exception as err:  # pylint: disable=broad-except
            raise err

    async def async_get_pollen_level_definitions(self):
        if self._pollen_level_definitions is None:
            response = await self.get_request(
                f"{BASE_URL}{Endpoints.POLLEN_LEVEL_DEFINITIONS}"
            )
            self._pollen_level_definitions = [item['name'] for item in response.get('items', [])]
        return self._pollen_level_definitions

    async def get_request(self, url: str) -> bool | Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                response = await self._session.get(url)
                return await response.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
            raise exception

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
            raise exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
            raise exception
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
            raise exception
