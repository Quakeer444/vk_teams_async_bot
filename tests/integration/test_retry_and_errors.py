"""Integration tests: retry under 5xx, timeout, ok=false handling."""

import re

import pytest

try:
    from aioresponses import aioresponses
except ImportError:
    pytest.skip("aioresponses required", allow_module_level=True)

from vk_teams_async_bot.client.retry import RetryPolicy
from vk_teams_async_bot.client.session import VKTeamsSession
from vk_teams_async_bot.errors import APIError, RateLimitError, ServerError

BASE_URL = "https://api.test.example.com"
BASE_PATH = "/bot/v1"
TOKEN = "test-token"

SELF_GET = re.compile(r".*/bot/v1/self/get")
SEND_TEXT = re.compile(r".*/bot/v1/messages/sendText")


def _make_session(max_retries: int = 2) -> VKTeamsSession:
    return VKTeamsSession(
        BASE_URL,
        BASE_PATH,
        TOKEN,
        timeout=5,
        retry_policy=RetryPolicy(
            max_retries=max_retries,
            base_delay=0.0,
            max_delay=0.0,
            jitter=False,
        ),
    )


class TestRetryBehavior:
    @pytest.mark.asyncio
    async def test_5xx_retries_and_succeeds(self):
        async with _make_session(max_retries=2) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"description": "err"}, status=500)
                m.get(SELF_GET, payload={"ok": True, "userId": "bot1"})
                result = await session.get("/self/get")
                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_5xx_exhausts_retries(self):
        async with _make_session(max_retries=1) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"description": "err"}, status=500)
                m.get(SELF_GET, payload={"description": "err"}, status=500)
                with pytest.raises(ServerError) as exc_info:
                    await session.get("/self/get")
                assert exc_info.value.status_code == 500


class TestOkFalseHandling:
    @pytest.mark.asyncio
    async def test_http_200_ok_false_raises_api_error(self):
        async with _make_session(max_retries=0) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": False, "description": "Invalid token"})
                with pytest.raises(APIError) as exc_info:
                    await session.get("/self/get")
                assert "Invalid token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_200_ok_true_succeeds(self):
        async with _make_session(max_retries=0) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": True, "userId": "bot1"})
                result = await session.get("/self/get")
                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_4xx_raises_api_error(self):
        async with _make_session(max_retries=0) as session:
            with aioresponses() as m:
                m.get(
                    SELF_GET,
                    payload={"ok": False, "description": "Not found"},
                    status=404,
                )
                with pytest.raises(APIError) as exc_info:
                    await session.get("/self/get")
                assert exc_info.value.status_code == 404


class TestRateLimitRetry:
    @pytest.mark.asyncio
    async def test_rate_limit_200_retries_and_succeeds(self):
        """HTTP 200 rate limit response retries and succeeds."""
        async with _make_session(max_retries=2) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": False, "description": "Ratelimit"})
                m.get(SELF_GET, payload={"ok": True, "userId": "bot1"})
                result = await session.get("/self/get")
                assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_rate_limit_post_retries_and_succeeds(self):
        """POST rate limit is retried (server did not execute the request)."""
        async with _make_session(max_retries=2) as session:
            with aioresponses() as m:
                m.post(SEND_TEXT, payload={"ok": False, "description": "Ratelimit"})
                m.post(SEND_TEXT, payload={"ok": True, "msgId": "abc"})
                result = await session.post(
                    "/messages/sendText", chatId="c1", text="hi"
                )
                assert result == {"ok": True, "msgId": "abc"}
