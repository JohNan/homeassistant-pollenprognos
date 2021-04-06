import asyncio
import logging
import socket

import aiohttp
import async_timeout

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {
    "Content-type": "application/json; charset=UTF-8",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G955F Build/PPR1.180610.011)",
}


class PollenApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        url = "https://pollenkoll.se/wp-json/pollenkoll/v1/app-complete?secret=830842cf-4d86-412d-a343-16edc27f5c75&platform=android&version=3"
        return await self.api_wrapper("get", url)

    async def api_wrapper(
            self, method: str, url: str, data: dict = {}, headers: dict = {}
    ) -> dict:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT, loop=asyncio.get_event_loop()):
                if method == "get":
                    response = await self._session.get(url, headers=headers)
                    return await response.json()

                elif method == "put":
                    await self._session.put(url, headers=headers, json=data)

                elif method == "patch":
                    await self._session.patch(url, headers=headers, json=data)

                elif method == "post":
                    await self._session.post(url, headers=headers, json=data)

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