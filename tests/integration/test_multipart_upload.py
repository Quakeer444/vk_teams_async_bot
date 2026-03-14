"""Integration tests: multipart upload path."""

import re
from io import BytesIO

import pytest

try:
    from aioresponses import aioresponses
except ImportError:
    pytest.skip("aioresponses required", allow_module_level=True)

from vk_teams_async_bot.client.retry import RetryPolicy
from vk_teams_async_bot.client.session import VKTeamsSession
from vk_teams_async_bot.methods.messages import MessageMethods
from vk_teams_async_bot.types.response import FileUploadResponse, MessageResponse

BASE_URL = "https://api.test.example.com"
BASE_PATH = "/bot/v1"
TOKEN = "test-token"

SEND_FILE = re.compile(r".*/bot/v1/messages/sendFile")


class FakeMessageClient(MessageMethods):
    def __init__(self, session):
        self._session = session


def _make_session() -> VKTeamsSession:
    return VKTeamsSession(
        BASE_URL, BASE_PATH, TOKEN, timeout=5,
        retry_policy=RetryPolicy(max_retries=0),
    )


class TestMultipartUpload:
    @pytest.mark.asyncio
    async def test_send_file_by_upload(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        async with _make_session() as session:
            with aioresponses() as m:
                m.post(
                    SEND_FILE,
                    payload={"ok": True, "msgId": "msg1", "fileId": "file123"},
                )
                client = FakeMessageClient(session)
                result = await client.send_file(
                    chat_id="chat1", file=str(test_file), caption="test file",
                )
                assert isinstance(result, FileUploadResponse)
                assert result.file_id == "file123"

    @pytest.mark.asyncio
    async def test_send_file_by_tuple(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.post(
                    SEND_FILE,
                    payload={"ok": True, "msgId": "msg1", "fileId": "file456"},
                )
                file_obj = BytesIO(b"binary content")
                client = FakeMessageClient(session)
                result = await client.send_file(
                    chat_id="chat1",
                    file=("doc.pdf", file_obj, "application/pdf"),
                )
                assert isinstance(result, FileUploadResponse)
                assert result.file_id == "file456"

    @pytest.mark.asyncio
    async def test_send_file_by_id(self):
        async with _make_session() as session:
            with aioresponses() as m:
                m.get(SEND_FILE, payload={"ok": True, "msgId": "msg2"})
                client = FakeMessageClient(session)
                result = await client.send_file(
                    chat_id="chat1", file_id="existing_file_id",
                )
                assert isinstance(result, MessageResponse)
