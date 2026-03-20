from __future__ import annotations

import asyncio
import logging
import ssl as ssl_lib
from typing import Any

import aiohttp
from aiohttp import ClientSession, FormData

from vk_teams_async_bot.errors import (
    APIError,
    NetworkError,
    RateLimitError,
    ServerError,
    SessionError,
    TimeoutError,
)

from .log_filter import TokenSanitizingFilter
from .retry import RetryPolicy, exponential_backoff_with_jitter

logger = logging.getLogger(__name__)

# Errors that are safe to retry automatically
_RETRIABLE_ERRORS = (ServerError, NetworkError, TimeoutError)


def _parse_retry_after(response: aiohttp.ClientResponse) -> float | None:
    """Extract ``Retry-After`` header value as float, or None if absent."""
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


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
        ssl: bool | ssl_lib.SSLContext | None = None,
        retry_policy: RetryPolicy | None = None,
        max_download_size: int = 100 * 1024 * 1024,  # 100MB
    ) -> None:
        self._base_url = base_url
        self._base_path = base_path
        self._bot_token = bot_token
        self._timeout = timeout
        self._ssl: bool | ssl_lib.SSLContext | None = ssl
        self._retry_policy = retry_policy or RetryPolicy()
        self._max_download_size = max_download_size
        self._session: ClientSession | None = None
        self._download_session: ClientSession | None = None
        self._session_lock = asyncio.Lock()
        # Remove any existing TokenSanitizingFilter before adding new one
        for f in logger.filters[:]:
            if isinstance(f, TokenSanitizingFilter):
                logger.removeFilter(f)
        logger.addFilter(TokenSanitizingFilter(bot_token))

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
        idempotent: bool = False,
        **params: Any,
    ) -> dict:
        """Execute a POST request against the Bot API.

        The bot token is injected into query params.  ``data`` is sent
        as the request body (form-data or JSON-serialisable dict).

        When ``idempotent`` is True, the request will be retried on
        server errors just like GET requests.  Use this for operations
        that are safe to repeat (e.g. file uploads with deduplication).
        """
        clean_params = self._build_params(params)
        return await self._request_with_retry(
            "POST",
            endpoint,
            idempotent=idempotent,
            params=clean_params,
            data=data,
        )

    async def close(self) -> None:
        """Close the underlying aiohttp sessions."""
        try:
            if self._download_session and not self._download_session.closed:
                await self._download_session.close()
        finally:
            self._download_session = None
            if self._session and not self._session.closed:
                await self._session.close()
                logger.debug("Session closed")
            self._session = None

    async def download(self, url: str) -> bytes:
        """Download a file from an arbitrary URL.

        Uses a dedicated download session (no base_url, reused across calls).
        Shares the same SSL/connector/timeout settings as API requests.
        Wraps errors into library exceptions (NetworkError, TimeoutError, etc.).
        """
        session = await self._ensure_download_session()
        policy = self._retry_policy
        last_error: Exception | None = None

        for attempt in range(1 + policy.max_retries):
            try:
                async with session.get(url) as resp:
                    if resp.status >= 500:
                        raise ServerError(
                            resp.status, f"Server error downloading {url}"
                        )
                    if resp.status >= 400:
                        raise APIError(
                            resp.status, f"HTTP {resp.status} downloading {url}"
                        )
                    content_length = resp.content_length
                    if (
                        content_length is not None
                        and content_length > self._max_download_size
                    ):
                        raise APIError(
                            resp.status,
                            f"File size {content_length} exceeds maximum "
                            f"download size {self._max_download_size}",
                        )

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in resp.content.iter_chunked(64 * 1024):
                        total += len(chunk)
                        if total > self._max_download_size:
                            raise APIError(
                                resp.status,
                                f"Download size exceeds maximum "
                                f"{self._max_download_size}",
                            )
                        chunks.append(chunk)
                    return b"".join(chunks)
            except _RETRIABLE_ERRORS as exc:
                last_error = exc
                if attempt < policy.max_retries:
                    await exponential_backoff_with_jitter(policy, attempt)
                    continue
                break
            except asyncio.TimeoutError as exc:
                last_error = TimeoutError(f"Download timed out: {url}")
                last_error.__cause__ = exc
                if attempt < policy.max_retries:
                    await exponential_backoff_with_jitter(policy, attempt)
                    continue
                break
            except aiohttp.ClientError as exc:
                last_error = NetworkError(str(exc))
                last_error.__cause__ = exc
                if attempt < policy.max_retries:
                    await exponential_backoff_with_jitter(policy, attempt)
                    continue
                break

        if last_error is not None:
            raise last_error
        raise SessionError("Download failed with no error captured")  # pragma: no cover

    # -- Internal helpers --------------------------------------------------

    def _build_params(
        self, params: dict[str, Any]
    ) -> dict[str, Any] | list[tuple[str, Any]]:
        """Merge token into params and drop None values.

        If any value is a list, returns a list of tuples so aiohttp
        sends repeated query parameters (e.g. ``msgId=1&msgId=2``).
        """
        merged = {"token": self._bot_token, **params}
        has_list = any(isinstance(v, list) for v in merged.values())
        if not has_list:
            return {k: v for k, v in merged.items() if v is not None}
        result: list[tuple[str, Any]] = []
        for k, v in merged.items():
            if v is None:
                continue
            if isinstance(v, list):
                for item in v:
                    result.append((k, item))
            else:
                result.append((k, v))
        return result

    def _make_connector(self) -> aiohttp.TCPConnector:
        """Create a TCPConnector with the configured SSL settings."""
        if self._ssl is not None:
            return aiohttp.TCPConnector(ssl=self._ssl)
        return aiohttp.TCPConnector()

    async def _ensure_download_session(self) -> ClientSession:
        """Return the download session (no base_url) or create a new one."""
        if self._download_session is not None and not self._download_session.closed:
            return self._download_session
        async with self._session_lock:
            if self._download_session is None or self._download_session.closed:
                self._download_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self._timeout),
                    connector=self._make_connector(),
                )
                logger.debug("Download session created")
            return self._download_session

    async def _ensure_session(self) -> ClientSession:
        """Return the existing session or create a new one (thread-safe)."""
        if self._session is not None and not self._session.closed:
            return self._session
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    base_url=self._base_url,
                    timeout=aiohttp.ClientTimeout(total=self._timeout),
                    connector=self._make_connector(),
                )
                logger.debug("Session created for %s%s", self._base_url, self._base_path)
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

        # 429 -- rate limited
        if status == 429:
            description = body.get("description", "Rate limited (HTTP 429)")
            retry_after = _parse_retry_after(response)
            raise RateLimitError(status, description, retry_after=retry_after)

        # 4xx -- client / API error
        if status >= 400:
            description = body.get("description", f"Client error (HTTP {status})")
            raise APIError(status, description)

        # 2xx with ok=false -- logical API error
        ok_flag = body.get("ok", True)
        if not ok_flag:
            description = body.get("description", "Unknown API error")
            if description == "Ratelimit":
                retry_after = _parse_retry_after(response)
                raise RateLimitError(status, description, retry_after=retry_after)
            raise APIError(status, description)

        return body

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        *,
        idempotent: bool | None = None,
        **kwargs: Any,
    ) -> dict:
        """Wrap ``_do_request`` with retry logic driven by RetryPolicy.

        RateLimitError is always retried regardless of idempotency -- the
        server has not executed the request, so it is safe to repeat.

        Other retriable errors (ServerError, NetworkError, TimeoutError)
        are only retried for idempotent requests.
        """
        if idempotent is None:
            idempotent = method.upper() != "POST"
        policy = self._retry_policy
        last_error: Exception | None = None

        for attempt in range(1 + policy.max_retries):
            try:
                return await self._do_request(method, endpoint, **kwargs)
            except RateLimitError as exc:
                last_error = exc
                if attempt < policy.max_retries:
                    if exc.retry_after is not None:
                        delay = exc.retry_after
                        await asyncio.sleep(delay)
                    else:
                        delay = await exponential_backoff_with_jitter(policy, attempt)
                    logger.warning(
                        "Rate limited, retry %d/%d after %.2fs for %s %s",
                        attempt + 1,
                        policy.max_retries,
                        delay,
                        method,
                        endpoint,
                    )
                    continue
                break
            except _RETRIABLE_ERRORS as exc:
                last_error = exc
                if not idempotent:
                    raise
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
                break

        if last_error is not None:
            raise last_error

        # Should be unreachable, but satisfy type checker
        raise SessionError("Request failed with no error captured")  # pragma: no cover
