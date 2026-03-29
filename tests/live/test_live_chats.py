import time
from io import BytesIO

import pytest

from vk_teams_async_bot.errors import APIError
from vk_teams_async_bot.types.chat import ChatInfoGroup, ChatInfoPrivate
from vk_teams_async_bot.types.enums import ChatAction
from vk_teams_async_bot.types.response import (
    AdminsResponse,
    MembersResponse,
    OkResponse,
    OkWithDescriptionResponse,
    UsersResponse,
)
from vk_teams_async_bot.types.user import UserAdmin

pytestmark = pytest.mark.live

# Minimal 1x1 PNG for avatar tests
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB\x82"
)


class TestChatInfo:
    async def test_get_chat_info_private(self, bot, test_user_id):
        result = await bot.get_chat_info(chat_id=test_user_id)
        assert isinstance(result, ChatInfoPrivate)
        assert result.type == "private"

    async def test_get_chat_info_private_all_fields(self, bot, test_user_id):
        result = await bot.get_chat_info(chat_id=test_user_id)
        assert isinstance(result, ChatInfoPrivate)
        assert result.type == "private"
        assert result.first_name is not None
        assert isinstance(result.first_name, str)
        assert result.is_bot is not None
        assert isinstance(result.is_bot, bool)
        if result.nick is not None:
            assert isinstance(result.nick, str)

    async def test_get_chat_info_group(self, bot, test_group_id):
        result = await bot.get_chat_info(chat_id=test_group_id)
        assert isinstance(result, ChatInfoGroup)
        assert result.type == "group"
        assert result.title is not None

    async def test_get_chat_info_group_all_fields(self, bot, test_group_id):
        result = await bot.get_chat_info(chat_id=test_group_id)
        assert isinstance(result, ChatInfoGroup)
        assert result.type == "group"
        assert isinstance(result.title, str)
        assert len(result.title) > 0
        if result.about is not None:
            assert isinstance(result.about, str)
        if result.rules is not None:
            assert isinstance(result.rules, str)
        if result.public is not None:
            assert isinstance(result.public, bool)

    async def test_get_chat_admins(self, bot, test_group_id):
        result = await bot.get_chat_admins(chat_id=test_group_id)
        assert isinstance(result, AdminsResponse)
        assert isinstance(result.admins, list)
        assert len(result.admins) > 0
        assert isinstance(result.admins[0], UserAdmin)

    async def test_get_chat_admins_all_fields(self, bot, test_group_id):
        result = await bot.get_chat_admins(chat_id=test_group_id)
        assert isinstance(result, AdminsResponse)
        assert len(result.admins) > 0
        for admin in result.admins:
            assert isinstance(admin, UserAdmin)
            assert isinstance(admin.user_id, str)
            assert len(admin.user_id) > 0
            if admin.creator is not None:
                assert isinstance(admin.creator, bool)

    async def test_get_chat_members(self, bot, test_group_id):
        result = await bot.get_chat_members(chat_id=test_group_id)
        assert isinstance(result, MembersResponse)
        assert isinstance(result.members, list)
        assert len(result.members) > 0

    async def test_get_chat_members_contains_bot(self, bot, test_group_id):
        self_info = await bot.get_self()
        result = await bot.get_chat_members(chat_id=test_group_id)
        assert isinstance(result, MembersResponse)
        member_ids = [m.user_id for m in result.members]
        assert self_info.user_id in member_ids

    async def test_get_blocked_users(self, bot, test_group_id):
        result = await bot.get_blocked_users(chat_id=test_group_id)
        assert isinstance(result, UsersResponse)
        assert isinstance(result.users, list)

    async def test_get_pending_users(self, bot, test_group_id):
        result = await bot.get_pending_users(chat_id=test_group_id)
        assert isinstance(result, UsersResponse)
        assert isinstance(result.users, list)

    async def test_send_chat_actions_typing(self, bot, test_user_id):
        result = await bot.send_chat_actions(
            chat_id=test_user_id,
            actions=[ChatAction.TYPING],
        )
        assert isinstance(result, OkResponse)
        assert result.ok is True

    async def test_send_chat_actions_looking(self, bot, test_user_id):
        result = await bot.send_chat_actions(
            chat_id=test_user_id,
            actions=[ChatAction.LOOKING],
        )
        assert isinstance(result, OkResponse)
        assert result.ok is True


class TestChatModification:
    async def test_set_chat_title(self, bot, test_group_id):
        ts = int(time.time())
        result = await bot.set_chat_title(
            chat_id=test_group_id,
            title=f"Test Title {ts}",
        )
        assert isinstance(result, OkResponse)
        assert result.ok is True

    async def test_group_settings_roundtrip(self, bot, test_group_id):
        ts = int(time.time())
        title = f"Roundtrip {ts}"
        about = f"About {ts}"
        rules = f"Rules {ts}"

        await bot.set_chat_title(chat_id=test_group_id, title=title)
        await bot.set_chat_about(chat_id=test_group_id, about=about)
        await bot.set_chat_rules(chat_id=test_group_id, rules=rules)

        info = await bot.get_chat_info(chat_id=test_group_id)
        assert isinstance(info, ChatInfoGroup)
        assert info.title == title
        assert info.about == about
        assert info.rules == rules

    async def test_set_chat_about(self, bot, test_group_id):
        result = await bot.set_chat_about(
            chat_id=test_group_id,
            about="Live test about",
        )
        assert isinstance(result, OkResponse)
        assert result.ok is True

    async def test_set_chat_rules(self, bot, test_group_id):
        result = await bot.set_chat_rules(
            chat_id=test_group_id,
            rules="Live test rules",
        )
        assert isinstance(result, OkResponse)
        assert result.ok is True

    async def test_pin_unpin_message(self, bot, test_group_id):
        msg = await bot.send_text(chat_id=test_group_id, text="live test: pin me")

        pin_result = await bot.pin_message(chat_id=test_group_id, msg_id=msg.msg_id)
        assert isinstance(pin_result, OkResponse)
        assert pin_result.ok is True

        unpin_result = await bot.unpin_message(chat_id=test_group_id, msg_id=msg.msg_id)
        assert isinstance(unpin_result, OkResponse)
        assert unpin_result.ok is True

    async def test_set_chat_avatar(self, bot, test_group_id):
        image = ("avatar.png", BytesIO(TINY_PNG), "image/png")
        result = await bot.set_chat_avatar(
            chat_id=test_group_id,
            image=image,
        )
        assert isinstance(result, OkWithDescriptionResponse)
        assert result.ok is True


class TestChatMembers:
    async def test_delete_chat_members(self, bot, test_group_id, second_user_id):
        result = await bot.delete_chat_members(
            chat_id=test_group_id,
            members=[second_user_id],
        )
        assert isinstance(result, OkResponse)
        assert result.ok is True

    async def test_block_unblock_user(self, bot, test_group_id, second_user_id):
        block_result = await bot.block_user(
            chat_id=test_group_id,
            user_id=second_user_id,
        )
        assert isinstance(block_result, OkResponse)
        assert block_result.ok is True

        unblock_result = await bot.unblock_user(
            chat_id=test_group_id,
            user_id=second_user_id,
        )
        assert isinstance(unblock_result, OkResponse)
        assert unblock_result.ok is True

    async def test_resolve_pending(self, bot, test_group_id):
        try:
            result = await bot.resolve_pending(
                chat_id=test_group_id,
                approve=True,
                everyone=True,
            )
            assert isinstance(result, OkResponse)
            assert result.ok is True
        except APIError as exc:
            if "not pending or nobody in pending list" in str(exc):
                pytest.skip("no pending users in test group")
            raise
