"""Error scenario live tests: invalid IDs and edge cases."""

from io import BytesIO

import pytest

from vk_teams_async_bot.errors import APIError

pytestmark = pytest.mark.live


# -- Invalid ID scenarios ------------------------------------------------------


async def test_send_text_invalid_chat_id(bot):
    with pytest.raises(APIError):
        await bot.send_text(chat_id="nonexistent_chat_12345", text="test")


async def test_edit_text_invalid_msg_id(bot, test_user_id):
    with pytest.raises(APIError):
        await bot.edit_text(
            chat_id=test_user_id,
            msg_id="999999999999",
            text="edited",
        )


async def test_delete_invalid_msg_id(bot, test_user_id):
    with pytest.raises(APIError):
        await bot.delete_messages(
            chat_id=test_user_id,
            msg_id="999999999999",
        )


async def test_get_file_info_invalid(bot):
    with pytest.raises(APIError):
        await bot.get_file_info(file_id="nonexistent_file_id_99999")


async def test_get_chat_info_invalid(bot):
    with pytest.raises(APIError):
        await bot.get_chat_info(chat_id="nonexistent_chat_99999")


# -- Edge case scenarios -------------------------------------------------------


async def test_send_empty_text(bot, test_user_id):
    with pytest.raises(APIError):
        await bot.send_text(chat_id=test_user_id, text="")


async def test_send_very_long_text(bot, test_user_id):
    long_text = "A" * 4097
    try:
        result = await bot.send_text(chat_id=test_user_id, text=long_text)
        assert result.ok is True
    except APIError:
        pass


async def test_delete_already_deleted(bot, test_user_id):
    msg = await bot.send_text(chat_id=test_user_id, text="live test: double delete")
    await bot.delete_messages(chat_id=test_user_id, msg_id=msg.msg_id)
    with pytest.raises(APIError):
        await bot.delete_messages(chat_id=test_user_id, msg_id=msg.msg_id)


async def test_block_already_blocked(bot, test_group_id, second_user_id):
    await bot.block_user(chat_id=test_group_id, user_id=second_user_id)
    try:
        await bot.block_user(chat_id=test_group_id, user_id=second_user_id)
    except APIError:
        pass
    finally:
        await bot.unblock_user(chat_id=test_group_id, user_id=second_user_id)
