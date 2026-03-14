"""Integration tests: session lifecycle (open, request, close)."""

import re

import pytest

try:
    from aioresponses import aioresponses
except ImportError:
    pytest.skip("aioresponses required", allow_module_level=True)

from vk_teams_async_bot.client.session import VKTeamsSession

BASE_URL = "https://api.test.example.com"
BASE_PATH = "/bot/v1"
TOKEN = "test-token"

SELF_GET = re.compile(r".*/bot/v1/self/get")


def _make_session() -> VKTeamsSession:
    return VKTeamsSession(BASE_URL, BASE_PATH, TOKEN, timeout=5)


class TestSessionLifecycle:
    @pytest.mark.asyncio
    async def test_context_manager_opens_and_closes(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.get(SELF_GET, payload={"ok": True, "userId": "bot1"})
                result = await session.get("/self/get")
                assert result["ok"] is True

        assert session._session is None

    @pytest.mark.asyncio
    async def test_session_auto_creates_on_request(self):
        session = _make_session()
        with aioresponses() as m:
            m.get(SELF_GET, payload={"ok": True, "userId": "bot1"})
            result = await session.get("/self/get")
            assert result["ok"] is True
            assert session._session is not None

        await session.close()
        assert session._session is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        session = _make_session()
        await session.close()
        await session.close()
        assert session._session is None

    @pytest.mark.asyncio
    async def test_multiple_requests_reuse_session(self):
        async with _make_session() as session:
            with aioresponses() as m:
                for _ in range(3):
                    m.get(SELF_GET, payload={"ok": True, "userId": "bot1"})

                sess_obj = session._session
                await session.get("/self/get")
                await session.get("/self/get")
                await session.get("/self/get")
                assert session._session is sess_obj
