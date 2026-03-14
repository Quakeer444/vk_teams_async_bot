from __future__ import annotations

import asyncio
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    from aioresponses import aioresponses
except ImportError:
    pytest.skip("aioresponses required", allow_module_level=True)

from vk_teams_async_bot.client.retry import RetryPolicy
from vk_teams_async_bot.client.session import VKTeamsSession
from vk_teams_async_bot.errors import APIError, NetworkError, ServerError, TimeoutError

BASE_URL = "https://api.example.com"
BASE_PATH = "/bot/v1"
TOKEN = "test-token-123"
FULL_URL = f"{BASE_URL}{BASE_PATH}"

# Use regex patterns for URL matching (aioresponses 0.7.8 + aiohttp 3.13.x compat)
SELF_GET = re.compile(r".*/bot/v1/self/get")
SEND_TEXT = re.compile(r".*/bot/v1/messages/sendText")


@pytest.fixture
def no_retry_policy() -> RetryPolicy:
    """Policy that disables retries for simple tests."""
    return RetryPolicy(max_retries=0)


@pytest.fixture
def fast_retry_policy() -> RetryPolicy:
    """Policy with fast retries for retry tests."""
    return RetryPolicy(max_retries=2, base_delay=0.0, max_delay=0.0, jitter=False)


# -- Success cases ---------------------------------------------------------


class TestSuccessResponses:
    @pytest.mark.asyncio
    async def test_get_200_ok_true(self, no_retry_policy: RetryPolicy) -> None:
        """HTTP 200 with ok=true returns the parsed dict."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": True, "nick": "bot"})
                result = await session.get("/self/get")

            assert result == {"ok": True, "nick": "bot"}

    @pytest.mark.asyncio
    async def test_post_200_ok_true(self, no_retry_policy: RetryPolicy) -> None:
        """POST with HTTP 200 and ok=true returns the parsed dict."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.post(SEND_TEXT, payload={"ok": True, "msgId": "abc123"})
                result = await session.post("/messages/sendText", chatId="chat1", text="hi")

            assert result == {"ok": True, "msgId": "abc123"}

    @pytest.mark.asyncio
    async def test_token_added_to_params(self, no_retry_policy: RetryPolicy) -> None:
        """Bot token is automatically injected into query params."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": True})
                await session.get("/self/get")

                # Inspect the request that was actually made
                key = next(iter(m.requests.keys()))
                call_args = m.requests[key]
                request_params = call_args[0].kwargs.get("params", {})
                assert request_params.get("token") == TOKEN


# -- Error cases -----------------------------------------------------------


class TestErrorResponses:
    @pytest.mark.asyncio
    async def test_200_ok_false_raises_api_error(self, no_retry_policy: RetryPolicy) -> None:
        """HTTP 200 with ok=false raises APIError."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": False, "description": "Invalid token"})
                with pytest.raises(APIError) as exc_info:
                    await session.get("/self/get")

                assert exc_info.value.status_code == 200
                assert "Invalid token" in exc_info.value.description

    @pytest.mark.asyncio
    async def test_4xx_raises_api_error(self, no_retry_policy: RetryPolicy) -> None:
        """HTTP 4xx raises APIError."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, status=400, payload={"ok": False, "description": "Bad request"})
                with pytest.raises(APIError) as exc_info:
                    await session.get("/self/get")

                assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_5xx_raises_server_error(self, no_retry_policy: RetryPolicy) -> None:
        """HTTP 5xx raises ServerError."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, status=500, payload={"ok": False, "description": "Internal error"})
                with pytest.raises(ServerError) as exc_info:
                    await session.get("/self/get")

                assert exc_info.value.status_code == 500


# -- Retry behaviour -------------------------------------------------------


class TestRetryBehaviour:
    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, fast_retry_policy: RetryPolicy) -> None:
        """ServerError triggers retries, success on final attempt."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                # First two attempts fail with 500, third succeeds
                m.get(SELF_GET, status=500, payload={"ok": False, "description": "err"})
                m.get(SELF_GET, status=500, payload={"ok": False, "description": "err"})
                m.get(SELF_GET, payload={"ok": True, "data": "ok"})

                result = await session.get("/self/get")

            assert result == {"ok": True, "data": "ok"}

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, fast_retry_policy: RetryPolicy) -> None:
        """TimeoutError triggers retries."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, exception=asyncio.TimeoutError())
                m.get(SELF_GET, payload={"ok": True})

                result = await session.get("/self/get")

            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, fast_retry_policy: RetryPolicy) -> None:
        """Connection errors (NetworkError) trigger retries."""
        import aiohttp

        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, exception=aiohttp.ClientConnectionError("Connection refused"))
                m.get(SELF_GET, payload={"ok": True})

                result = await session.get("/self/get")

            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises(self, fast_retry_policy: RetryPolicy) -> None:
        """When all retries are exhausted the final error is raised."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                for _ in range(3):
                    m.get(SELF_GET, status=500, payload={"ok": False, "description": "down"})

                with pytest.raises(ServerError):
                    await session.get("/self/get")


# -- Context manager -------------------------------------------------------


class TestContextManager:
    @pytest.mark.asyncio
    async def test_context_manager_opens_and_closes(self) -> None:
        """Session is created on enter and closed on exit."""
        session = VKTeamsSession(BASE_URL, BASE_PATH, TOKEN)

        async with session:
            assert session._session is not None
            assert not session._session.closed

        assert session._session is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self) -> None:
        """Calling close multiple times does not raise."""
        session = VKTeamsSession(BASE_URL, BASE_PATH, TOKEN)
        async with session:
            pass
        # Second close should be safe
        await session.close()
