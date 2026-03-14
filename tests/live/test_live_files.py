from io import BytesIO

import pytest

from vk_teams_async_bot.types.file import FileInfo
from vk_teams_async_bot.types.response import FileUploadResponse

pytestmark = pytest.mark.live


async def test_get_file_info(bot, test_user_id):
    content = BytesIO(b"live test file for info")
    upload = await bot.send_file(
        chat_id=test_user_id,
        file=("info_test.txt", content, "text/plain"),
    )
    assert isinstance(upload, FileUploadResponse)

    file_info = await bot.get_file_info(file_id=upload.file_id)
    assert isinstance(file_info, FileInfo)
    assert file_info.type is not None
    assert file_info.size > 0
    assert file_info.filename is not None
    assert file_info.url is not None


async def test_download_file(bot, test_user_id):
    file_content = b"live test download content"
    upload = await bot.send_file(
        chat_id=test_user_id,
        file=("download_test.txt", BytesIO(file_content), "text/plain"),
    )
    file_info = await bot.get_file_info(file_id=upload.file_id)

    data = await bot.download_file(file_info.url)
    assert isinstance(data, bytes)
    assert len(data) == file_info.size
