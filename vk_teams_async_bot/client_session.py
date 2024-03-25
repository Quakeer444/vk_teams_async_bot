import asyncio
import logging
from typing import TypeAlias

import aiohttp
from aiohttp import ClientSession, FormData

from vk_teams_async_bot.errors import ResponseStatus500orHigherError
from vk_teams_async_bot.helpers import retry_on_500_or_higher_response

logger = logging.getLogger(__name__)

Seconds: TypeAlias = int


class VKTeamsSession:
    """
    Interaction with VK Teams API.
    Creates a session and makes GET/POST requests
    """

    _session: ClientSession | None = None

    def __init__(
        self,
        base_url: str,
        base_path: str,
        bot_token: str,
        timeout_session: Seconds,
    ):
        self.base_url = base_url
        self.base_path = base_path
        self.bot_token = bot_token
        self.timeout_session = timeout_session
        self.delay_between_retries: None | int = None

    async def _create_session(self) -> None:
        """Creating an aiohttp session"""
        self._session = aiohttp.ClientSession(
            base_url=self.base_url,
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=self.timeout_session),
            loop=asyncio.get_event_loop(),
            connector=aiohttp.TCPConnector(ssl=False),
        )
        logger.debug(f"The session was created successfully. {self._session}")

    async def _check_session(self) -> None:
        """Checking the existence of an open aiohttp session"""
        if not self._session:
            logger.debug("Starting creating a new session")
            await self._create_session()

    @retry_on_500_or_higher_response
    async def get_request(
        self, endpoint: str, _count_request_retries: int, **kwargs
    ) -> dict | None:
        """
        GET request

        :param endpoint: endpoint VK Teams API
        :param _count_request_retries: Number of request retries in case of
               500+ code response from server VK Teams
        :param kwargs: Request params

        :return:
        """
        await self._check_session()

        params = {"token": self.bot_token, **kwargs}
        [params.pop(key) for key, value in params.copy().items() if value is None]

        try:
            if self._session:
                response = await self._session.get(
                    url=f"{self.base_path}{endpoint}", params=params
                )
                response_text = await response.text()
                if not response_text.count('{"events": [], "ok": true}'):
                    logger.debug(f"{response.status} {response_text}")

                response_json = await response.json()
                return response_json
            return None

        except aiohttp.ClientResponseError as err:
            if err.status >= 500:
                raise ResponseStatus500orHigherError(err)
            logger.error(err)
            raise

        except Exception as err:
            logger.error(f"Unknown error {err}", exc_info=True)
            raise

    @retry_on_500_or_higher_response
    async def post_request(
        self,
        endpoint: str,
        _count_request_retries: int,
        body: FormData | dict,
        **kwargs,
    ) -> dict | None:
        """
        POST request

        :param endpoint: endpoint VK Teams API
        :param _count_request_retries: Number of request retries in case of
               500+ code response from server VK Teams
        :param body: Request body
        :param kwargs: Request params
        :return:
        """
        await self._check_session()

        params = {"token": self.bot_token, **kwargs}
        [params.pop(key) for key, value in params.copy().items() if value is None]

        try:
            if self._session:
                response = await self._session.post(
                    url=f"{self.base_path}{endpoint}", params=params, data=body
                )
                response_text = await response.text()
                if not response_text.count('{"events": [], "ok": true}'):
                    logger.debug(f"{response.status} {response_text}")

                response_json = await response.json()
                return response_json
            return None

        except aiohttp.ClientResponseError as err:
            if err.status >= 500:
                raise ResponseStatus500orHigherError(err)
            logger.error(err)
            raise

        except Exception as err:
            logger.error(f"Unknown error {err}", exc_info=True)
            raise
