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
from vk_teams_async_bot.errors import (
    APIError,
    NetworkError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

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
                result = await session.post(
                    "/messages/sendText", chatId="chat1", text="hi"
                )

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
    async def test_200_ok_false_raises_api_error(
        self, no_retry_policy: RetryPolicy
    ) -> None:
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
                m.get(
                    SELF_GET,
                    status=400,
                    payload={"ok": False, "description": "Bad request"},
                )
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
                m.get(
                    SELF_GET,
                    status=500,
                    payload={"ok": False, "description": "Internal error"},
                )
                with pytest.raises(ServerError) as exc_info:
                    await session.get("/self/get")

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(
        self, no_retry_policy: RetryPolicy
    ) -> None:
        """HTTP 429 raises RateLimitError."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(
                    SELF_GET,
                    status=429,
                    payload={"ok": False, "description": "Too many requests"},
                )
                with pytest.raises(RateLimitError) as exc_info:
                    await session.get("/self/get")

                assert exc_info.value.status_code == 429
                assert "Too many requests" in exc_info.value.description


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
    async def test_retry_on_connection_error(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """Connection errors (NetworkError) trigger retries."""
        import aiohttp

        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(
                    SELF_GET,
                    exception=aiohttp.ClientConnectionError("Connection refused"),
                )
                m.get(SELF_GET, payload={"ok": True})

                result = await session.get("/self/get")

            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """When all retries are exhausted the final error is raised."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                for _ in range(3):
                    m.get(
                        SELF_GET,
                        status=500,
                        payload={"ok": False, "description": "down"},
                    )

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


# -- _build_params ---------------------------------------------------------


class TestBuildParams:
    def test_build_params_expands_list_to_repeated_query_params(self):
        """Verify _build_params correctly expands lists into repeated tuples."""
        session = VKTeamsSession(
            base_url="https://example.com",
            base_path="/bot/v1",
            bot_token="tok",
        )
        result = session._build_params({"chatId": "c1", "msgId": [1, 2, 3]})
        assert isinstance(result, list)
        assert ("msgId", 1) in result
        assert ("msgId", 2) in result
        assert ("msgId", 3) in result
        assert ("chatId", "c1") in result


# -- download() ------------------------------------------------------------

DOWNLOAD_URL = "https://files.example.com/f1"
DOWNLOAD_URL_RE = re.compile(r"https://files\.example\.com/f1")


class TestSessionDownload:
    @pytest.mark.asyncio
    async def test_download_returns_bytes(self, no_retry_policy: RetryPolicy) -> None:
        """Happy path: download returns file content as bytes."""
        session = VKTeamsSession(
            BASE_URL,
            BASE_PATH,
            TOKEN,
            retry_policy=no_retry_policy,
        )
        with aioresponses() as m:
            m.get(DOWNLOAD_URL_RE, body=b"file content")
            result = await session.download(DOWNLOAD_URL)
        assert result == b"file content"

    @pytest.mark.asyncio
    async def test_download_reuses_session(self, no_retry_policy: RetryPolicy) -> None:
        """download() reuses a dedicated download session across calls."""
        session = VKTeamsSession(
            BASE_URL,
            BASE_PATH,
            TOKEN,
            retry_policy=no_retry_policy,
        )
        with aioresponses() as m:
            m.get(DOWNLOAD_URL_RE, body=b"first")
            m.get(DOWNLOAD_URL_RE, body=b"second")
            await session.download(DOWNLOAD_URL)
            dl_session = session._download_session
            await session.download(DOWNLOAD_URL)
            # Same session object reused for second download
            assert session._download_session is dl_session
        await session.close()

    @pytest.mark.asyncio
    async def test_download_retries_on_server_error(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """First call returns 500, second 200. Assert retry works."""
        session = VKTeamsSession(
            BASE_URL,
            BASE_PATH,
            TOKEN,
            retry_policy=fast_retry_policy,
        )
        with aioresponses() as m:
            m.get(DOWNLOAD_URL_RE, status=500)
            m.get(DOWNLOAD_URL_RE, body=b"ok")
            result = await session.download(DOWNLOAD_URL)
        assert result == b"ok"

    @pytest.mark.asyncio
    async def test_download_no_retry_on_client_error(
        self, no_retry_policy: RetryPolicy
    ) -> None:
        """404 raises APIError immediately."""
        session = VKTeamsSession(
            BASE_URL,
            BASE_PATH,
            TOKEN,
            retry_policy=no_retry_policy,
        )
        with aioresponses() as m:
            m.get(DOWNLOAD_URL_RE, status=404)
            with pytest.raises(APIError) as exc_info:
                await session.download(DOWNLOAD_URL)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_download_retries_on_network_error(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """Network error triggers retry, raises NetworkError on exhaustion."""
        import aiohttp as _aiohttp

        session = VKTeamsSession(
            BASE_URL,
            BASE_PATH,
            TOKEN,
            retry_policy=fast_retry_policy,
        )
        with aioresponses() as m:
            for _ in range(3):
                m.get(
                    DOWNLOAD_URL_RE,
                    exception=_aiohttp.ClientConnectionError("conn refused"),
                )
            with pytest.raises(NetworkError):
                await session.download(DOWNLOAD_URL)

    @pytest.mark.asyncio
    async def test_post_does_not_retry_by_default(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """POST requests are not retried by default to prevent duplicates."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.post(
                    SEND_TEXT, status=500, payload={"ok": False, "description": "err"}
                )
                with pytest.raises(ServerError):
                    await session.post("/messages/sendText", chatId="c1", text="hi")

    @pytest.mark.asyncio
    async def test_post_with_idempotent_retries_on_server_error(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """POST with idempotent=True should retry on 500."""
        SEND_FILE = re.compile(r".*/bot/v1/messages/sendFile")
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.post(
                    SEND_FILE,
                    status=500,
                    payload={"ok": False, "description": "err"},
                )
                m.post(SEND_FILE, payload={"ok": True})
                result = await session.post("/messages/sendFile", idempotent=True)
                assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_ensure_session_concurrent_calls(self) -> None:
        """Multiple concurrent _ensure_session calls create only one session."""
        session = VKTeamsSession(BASE_URL, BASE_PATH, TOKEN)
        results = await asyncio.gather(
            session._ensure_session(),
            session._ensure_session(),
            session._ensure_session(),
        )
        assert results[0] is results[1] is results[2]
        await session.close()

    @pytest.mark.asyncio
    async def test_download_retries_on_timeout(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """Timeout triggers retry, raises TimeoutError on exhaustion."""
        session = VKTeamsSession(
            BASE_URL,
            BASE_PATH,
            TOKEN,
            retry_policy=fast_retry_policy,
        )
        with aioresponses() as m:
            for _ in range(3):
                m.get(DOWNLOAD_URL_RE, exception=asyncio.TimeoutError())
            with pytest.raises(TimeoutError):
                await session.download(DOWNLOAD_URL)

    @pytest.mark.asyncio
    async def test_200_ok_false_ratelimit_raises_rate_limit_error(
        self, no_retry_policy: RetryPolicy
    ) -> None:
        """HTTP 200 with ok=false and description=Ratelimit raises RateLimitError."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": False, "description": "Ratelimit"})
                with pytest.raises(RateLimitError) as exc_info:
                    await session.get("/self/get")

                assert exc_info.value.status_code == 200
                assert exc_info.value.description == "Ratelimit"

    @pytest.mark.asyncio
    async def test_rate_limit_retries_on_get(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """Rate limit is retried on GET requests."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": False, "description": "Ratelimit"})
                m.get(SELF_GET, payload={"ok": True, "data": "ok"})

                result = await session.get("/self/get")
            assert result == {"ok": True, "data": "ok"}

    @pytest.mark.asyncio
    async def test_rate_limit_retries_on_post(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """Rate limit is retried on POST (server did not execute the request)."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                m.post(SEND_TEXT, payload={"ok": False, "description": "Ratelimit"})
                m.post(SEND_TEXT, payload={"ok": True, "msgId": "abc"})

                result = await session.post(
                    "/messages/sendText", chatId="c1", text="hi"
                )
            assert result == {"ok": True, "msgId": "abc"}

    @pytest.mark.asyncio
    async def test_rate_limit_exhaustion_raises(
        self, fast_retry_policy: RetryPolicy
    ) -> None:
        """When all rate limit retries are exhausted, RateLimitError is raised."""
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=fast_retry_policy
        ) as session:
            with aioresponses() as m:
                for _ in range(3):
                    m.post(
                        SEND_TEXT,
                        payload={"ok": False, "description": "Ratelimit"},
                    )

                with pytest.raises(RateLimitError):
                    await session.post("/messages/sendText", chatId="c1", text="hi")

    @pytest.mark.asyncio
    async def test_download_rejects_oversized_response(
        self, no_retry_policy: RetryPolicy
    ) -> None:
        """Download should reject responses exceeding max_download_size."""
        large_body = b"x" * 1024  # 1KB
        async with VKTeamsSession(
            BASE_URL, BASE_PATH, TOKEN, retry_policy=no_retry_policy
        ) as session:
            session._max_download_size = 512  # 512 bytes limit
            with aioresponses() as m:
                m.get(DOWNLOAD_URL_RE, body=large_body)
                with pytest.raises(APIError, match="exceeds maximum"):
                    await session.download(DOWNLOAD_URL)
