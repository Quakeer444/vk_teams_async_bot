import asyncio
from io import BytesIO
from pathlib import Path

import pytest

from vk_teams_async_bot import InlineKeyboardMarkup, KeyboardButton
from vk_teams_async_bot.errors import APIError
from vk_teams_async_bot.types.enums import ParseMode
from vk_teams_async_bot.types.response import (
    FileUploadResponse,
    MessageResponse,
    OkResponse,
)

pytestmark = pytest.mark.live


async def test_send_text_plain(bot, test_user_id):
    result = await bot.send_text(chat_id=test_user_id, text="live test: plain text")
    assert isinstance(result, MessageResponse)
    assert result.ok is True
    assert isinstance(result.msg_id, str)


async def test_send_text_markdown(bot, test_user_id):
    result = await bot.send_text(
        chat_id=test_user_id,
        text="live test: *bold*",
        parse_mode=ParseMode.MARKDOWNV2,
    )
    assert isinstance(result, MessageResponse)
    assert result.ok is True


async def test_send_text_html(bot, test_user_id):
    result = await bot.send_text(
        chat_id=test_user_id,
        text="live test: <b>bold</b>",
        parse_mode=ParseMode.HTML,
    )
    assert isinstance(result, MessageResponse)
    assert result.ok is True


async def test_send_text_to_group(bot, test_group_id):
    result = await bot.send_text(chat_id=test_group_id, text="live test: group message")
    assert isinstance(result, MessageResponse)
    assert result.ok is True


async def test_send_text_with_keyboard(bot, test_user_id):
    kb = InlineKeyboardMarkup()
    kb.add(KeyboardButton("Test Button", callback_data="test_cb"))
    result = await bot.send_text(
        chat_id=test_user_id,
        text="live test: keyboard",
        inline_keyboard_markup=kb,
    )
    assert isinstance(result, MessageResponse)
    assert result.ok is True


async def test_send_text_with_reply(bot, test_user_id):
    original = await bot.send_text(chat_id=test_user_id, text="live test: original")
    result = await bot.send_text(
        chat_id=test_user_id,
        text="live test: reply",
        reply_msg_id=original.msg_id,
    )
    assert isinstance(result, MessageResponse)
    assert result.ok is True


async def test_send_text_with_forward(bot, test_user_id):
    original = await bot.send_text(chat_id=test_user_id, text="live test: to forward")
    result = await bot.send_text(
        chat_id=test_user_id,
        text="live test: forwarded",
        forward_chat_id=test_user_id,
        forward_msg_id=original.msg_id,
    )
    assert isinstance(result, MessageResponse)
    assert result.ok is True


async def test_edit_text(bot, test_user_id):
    msg = await bot.send_text(chat_id=test_user_id, text="live test: before edit")
    result = await bot.edit_text(
        chat_id=test_user_id,
        msg_id=msg.msg_id,
        text="live test: after edit",
    )
    assert isinstance(result, OkResponse)
    assert result.ok is True


async def test_delete_messages_single(bot, test_user_id):
    msg = await bot.send_text(chat_id=test_user_id, text="live test: delete me")
    result = await bot.delete_messages(chat_id=test_user_id, msg_id=msg.msg_id)
    assert isinstance(result, OkResponse)
    assert result.ok is True


async def test_delete_messages_batch(bot, test_user_id):
    msg1 = await bot.send_text(chat_id=test_user_id, text="live test: delete batch 1")
    msg2 = await bot.send_text(chat_id=test_user_id, text="live test: delete batch 2")
    result = await bot.delete_messages(
        chat_id=test_user_id,
        msg_id=[msg1.msg_id, msg2.msg_id],
    )
    assert isinstance(result, OkResponse)
    assert result.ok is True


async def test_send_file_upload(bot, test_user_id):
    content = BytesIO(b"live test file content")
    result = await bot.send_file(
        chat_id=test_user_id,
        file=("test.txt", content, "text/plain"),
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True
    assert isinstance(result.file_id, str)


async def test_send_file_by_id(bot, test_user_id):
    content = BytesIO(b"live test file for resend")
    upload = await bot.send_file(
        chat_id=test_user_id,
        file=("resend.txt", content, "text/plain"),
    )
    result = await bot.send_file(
        chat_id=test_user_id,
        file_id=upload.file_id,
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_send_file_with_caption(bot, test_user_id):
    content = BytesIO(b"live test file with caption")
    result = await bot.send_file(
        chat_id=test_user_id,
        file=("caption.txt", content, "text/plain"),
        caption="live test caption",
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_send_voice_upload(bot, test_user_id, fixtures_dir):
    mp3_path = fixtures_dir / "test.mp3"
    result = await bot.send_voice(
        chat_id=test_user_id,
        file=str(mp3_path),
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_send_photo_to_user(bot, test_user_id, fixtures_dir):
    png_path = fixtures_dir / "test.png"
    result = await bot.send_file(
        chat_id=test_user_id,
        file=str(png_path),
        caption="live test: photo to user",
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_send_photo_to_group(bot, test_group_id, fixtures_dir):
    png_path = fixtures_dir / "test.png"
    result = await bot.send_file(
        chat_id=test_group_id,
        file=str(png_path),
        caption="live test: photo to group",
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_send_csv_file(bot, test_user_id, fixtures_dir):
    csv_path = fixtures_dir / "test.csv"
    result = await bot.send_file(
        chat_id=test_user_id,
        file=str(csv_path),
        caption="live test: CSV file",
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_send_xlsx_file(bot, test_user_id, fixtures_dir):
    xlsx_path = fixtures_dir / "test.xlsx"
    result = await bot.send_file(
        chat_id=test_user_id,
        file=str(xlsx_path),
        caption="live test: XLSX file",
    )
    assert isinstance(result, FileUploadResponse)
    assert result.ok is True


async def test_answer_callback_query_fake(bot):
    """answer_callback_query requires a real callback from a user click.
    We verify the method shape by calling with a fake queryId and
    expecting an error response (the API returns ok=false)."""
    with pytest.raises(APIError):
        await bot.answer_callback_query(query_id="fake_query_id_000")
