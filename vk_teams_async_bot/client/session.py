from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientSession, FormData

from vk_teams_async_bot.errors import (
    APIError,
    NetworkError,
    ServerError,
    SessionError,
    TimeoutError,
)

from .retry import RetryPolicy, exponential_backoff_with_jitter

logger = logging.getLogger(__name__)

# Errors that are safe to retry automatically
_RETRIABLE_ERRORS = (ServerError, NetworkError, TimeoutError)


class VKTeamsSession:
    """HTTP client for VK Teams Bot API.

    Manages an aiohttp session, adds the bot token to every request,
    handles response parsing, error mapping, and automatic retries.

    Usage::

        async with VKTeamsSession(base_url, base_path, token) as session:
            result = await session.get("/self/get")
    """

    def __init__(
        self,
        base_url: str,
        base_path: str,
        bot_token: str,
        timeout: int = 30,
        ssl: bool | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._base_url = base_url
        self._base_path = base_path
        self._bot_token = bot_token
        self._timeout = timeout
        self._ssl = ssl
        self._retry_policy = retry_policy or RetryPolicy()
        self._session: ClientSession | None = None

    # -- Context manager protocol ------------------------------------------

    async def __aenter__(self) -> VKTeamsSession:
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()

    # -- Public API --------------------------------------------------------

    async def get(self, endpoint: str, **params: Any) -> dict:
        """Execute a GET request against the Bot API.

        The bot token is injected automatically.  None-valued params
        are stripped before sending.
        """
        clean_params = self._build_params(params)
        return await self._request_with_retry(
            "GET",
            endpoint,
            params=clean_params,
        )

    async def post(
        self,
        endpoint: str,
        data: FormData | dict | None = None,
        **params: Any,
    ) -> dict:
        """Execute a POST request against the Bot API.

        The bot token is injected into query params.  ``data`` is sent
        as the request body (form-data or JSON-serialisable dict).
        """
        clean_params = self._build_params(params)
        return await self._request_with_retry(
            "POST",
            endpoint,
            params=clean_params,
            data=data,
        )

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Session closed")
        self._session = None

    # -- Internal helpers --------------------------------------------------

    def _build_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Merge token into params and drop None values."""
        merged = {"token": self._bot_token, **params}
        return {k: v for k, v in merged.items() if v is not None}

    async def _ensure_session(self) -> ClientSession:
        """Return the existing session or create a new one."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self._base_url,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                connector=aiohttp.TCPConnector(ssl=self._ssl),
            )
            logger.debug("Session created: %s", self._session)
        return self._session

    async def _do_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """Execute a single HTTP request and handle the response."""
        session = await self._ensure_session()
        url = f"{self._base_path}{endpoint}"

        try:
            response = await session.request(method, url, **kwargs)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"Request timed out: {method} {endpoint}") from exc
        except aiohttp.ClientResponseError as exc:
            if exc.status >= 500:
                raise ServerError(exc.status, str(exc.message)) from exc
            raise APIError(exc.status, str(exc.message)) from exc
        except aiohttp.ClientError as exc:
            raise NetworkError(str(exc)) from exc

        return await self._handle_response(response)

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> dict:
        """Parse JSON body, inspect ``ok`` field, raise on errors."""
        status = response.status

        try:
            body: dict = await response.json()
        except Exception as exc:
            raise APIError(
                status,
                f"Failed to decode JSON response (HTTP {status})",
            ) from exc

        # 5xx -- server error
        if status >= 500:
            description = body.get("description", f"Server error (HTTP {status})")
            raise ServerError(status, description)

        # 4xx -- client / API error
        if status >= 400:
            description = body.get("description", f"Client error (HTTP {status})")
            raise APIError(status, description)

        # 2xx with ok=false -- logical API error
        ok_flag = body.get("ok", True)
        if not ok_flag:
            description = body.get("description", "Unknown API error")
            raise APIError(status, description)

        return body

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict:
        """Wrap ``_do_request`` with retry logic driven by RetryPolicy.

        Only retriable errors (ServerError, NetworkError, TimeoutError)
        trigger a retry.  All other exceptions propagate immediately.
        """
        policy = self._retry_policy
        last_error: Exception | None = None

        for attempt in range(1 + policy.max_retries):
            try:
                return await self._do_request(method, endpoint, **kwargs)
            except _RETRIABLE_ERRORS as exc:
                last_error = exc
                if attempt < policy.max_retries:
                    delay = await exponential_backoff_with_jitter(policy, attempt)
                    logger.warning(
                        "Retry %d/%d after %.2fs for %s %s: %s",
                        attempt + 1,
                        policy.max_retries,
                        delay,
                        method,
                        endpoint,
                        exc,
                    )
                    continue
                # Exhausted retries -- fall through to raise
                break

        if last_error is not None:
            raise last_error

        # Should be unreachable, but satisfy type checker
        raise SessionError("Request failed with no error captured")  # pragma: no cover
