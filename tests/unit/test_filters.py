"""Tests for vk_teams_async_bot.filters package."""

from __future__ import annotations

import pytest

from vk_teams_async_bot.filters.base import AndFilter, FilterBase, NotFilter, OrFilter
from vk_teams_async_bot.filters.callback import (
    CallbackDataFilter,
    CallbackDataRegexpFilter,
)
from vk_teams_async_bot.filters.composite import (
    MessageTextPartFromNickFilter,
    RegexpTextPartsFilter,
)
from vk_teams_async_bot.filters.message import (
    CommandFilter,
    MessageFilter,
    RegexpFilter,
    TagFilter,
)
from vk_teams_async_bot.filters.parts import (
    FileFilter,
    ForwardFilter,
    MentionFilter,
    ReplyFilter,
    StickerFilter,
    VoiceFilter,
)
from vk_teams_async_bot.filters.state import StateFilter
from vk_teams_async_bot.fsm.state import State, StatesGroup
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage
from vk_teams_async_bot.types.enums import ChatType, EventType, Parts
from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    DeletedMessageEvent,
    EditedMessageEvent,
    LeftChatMembersEvent,
    NewChatMembersEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    UnpinnedMessageEvent,
)
from vk_teams_async_bot.types.event_chat import EventChatRef
from vk_teams_async_bot.types.message import (
    FilePart,
    FilePartPayload,
    ForwardPart,
    ForwardPartPayload,
    MentionPart,
    NestedMessage,
    ReplyPart,
    ReplyPartPayload,
    StickerPart,
    StickerPartPayload,
    VoicePart,
)
from vk_teams_async_bot.types.user import User


# -- Helpers --


def _chat(chat_id: str = "chat1") -> EventChatRef:
    return EventChatRef(chatId=chat_id, type=ChatType.PRIVATE)


def _user(user_id: str = "user1", nick: str | None = None) -> User:
    return User(userId=user_id, firstName="Alice", nick=nick)


def _new_message(
    text: str | None = "hello",
    parts: list | None = None,
    chat_id: str = "chat1",
    user_id: str = "user1",
    nick: str | None = None,
) -> NewMessageEvent:
    return NewMessageEvent(
        eventId=1,
        type=EventType.NEW_MESSAGE,
        chat=_chat(chat_id),
        **{"from": _user(user_id, nick)},
        msgId="msg1",
        text=text,
        parts=parts,
    )


def _callback_query(
    callback_data: str = "btn_ok",
    chat_id: str = "chat1",
    user_id: str = "user1",
) -> CallbackQueryEvent:
    return CallbackQueryEvent(
        eventId=2,
        type=EventType.CALLBACK_QUERY,
        chat=_chat(chat_id),
        **{"from": _user(user_id)},
        queryId="q1",
        callbackData=callback_data,
    )


def _edited_message(
    text: str | None = "edited",
    chat_id: str = "chat1",
    user_id: str = "user1",
) -> EditedMessageEvent:
    return EditedMessageEvent(
        eventId=3,
        type=EventType.EDITED_MESSAGE,
        chat=_chat(chat_id),
        **{"from": _user(user_id)},
        msgId="msg1",
        text=text,
    )


def _deleted_message() -> DeletedMessageEvent:
    return DeletedMessageEvent(
        eventId=4,
        type=EventType.DELETED_MESSAGE,
        chat=_chat(),
        msgId="msg1",
    )


def _pinned_message() -> PinnedMessageEvent:
    return PinnedMessageEvent(
        eventId=5,
        type=EventType.PINNED_MESSAGE,
        chat=_chat(),
        **{"from": _user()},
        msgId="msg1",
        text="pinned text",
    )


def _unpinned_message() -> UnpinnedMessageEvent:
    return UnpinnedMessageEvent(
        eventId=6,
        type=EventType.UNPINNED_MESSAGE,
        chat=_chat(),
        msgId="msg1",
    )


def _new_chat_members() -> NewChatMembersEvent:
    return NewChatMembersEvent(
        eventId=7,
        type=EventType.NEW_CHAT_MEMBERS,
        chat=_chat(),
        newMembers=[_user("u2")],
        addedBy=_user("u1"),
    )


def _left_chat_members() -> LeftChatMembersEvent:
    return LeftChatMembersEvent(
        eventId=8,
        type=EventType.LEFT_CHAT_MEMBERS,
        chat=_chat(),
        leftMembers=[_user("u2")],
        removedBy=_user("u1"),
    )


def _nested_message(
    text: str = "fwd text",
    nick: str | None = None,
) -> NestedMessage:
    return NestedMessage(
        **{"from": _user("u_fwd", nick)},
        msgId="fwd1",
        text=text,
    )


def _file_part() -> FilePart:
    return FilePart(
        type=Parts.FILE,
        payload=FilePartPayload(fileId="f1"),
    )


def _sticker_part() -> StickerPart:
    return StickerPart(
        type=Parts.STICKER,
        payload=StickerPartPayload(fileId="s1"),
    )


def _mention_part() -> MentionPart:
    return MentionPart(
        type=Parts.MENTION,
        payload=_user("mentioned_user"),
    )


def _voice_part() -> VoicePart:
    return VoicePart(
        type=Parts.VOICE,
        payload=FilePartPayload(fileId="v1"),
    )


def _forward_part(text: str = "fwd text", nick: str | None = None) -> ForwardPart:
    return ForwardPart(
        type=Parts.FORWARD,
        payload=ForwardPartPayload(message=_nested_message(text, nick)),
    )


def _reply_part(text: str = "reply text", nick: str | None = None) -> ReplyPart:
    return ReplyPart(
        type=Parts.REPLY,
        payload=ReplyPartPayload(message=_nested_message(text, nick)),
    )


# -- MessageFilter --


class TestMessageFilter:
    def test_matches_new_message(self):
        f = MessageFilter()
        assert f(_new_message()) is True

    def test_rejects_callback(self):
        f = MessageFilter()
        assert f(_callback_query()) is False

    def test_rejects_edited(self):
        f = MessageFilter()
        assert f(_edited_message()) is False


# -- RegexpFilter --


class TestRegexpFilter:
    def test_matching_text(self):
        f = RegexpFilter(r"hel+o")
        assert f(_new_message("hello")) is True

    def test_non_matching_text(self):
        f = RegexpFilter(r"^goodbye$")
        assert f(_new_message("hello")) is False

    def test_none_text(self):
        f = RegexpFilter(r"anything")
        assert f(_new_message(text=None)) is False

    def test_wrong_event_type(self):
        f = RegexpFilter(r".*")
        assert f(_callback_query()) is False


# -- CommandFilter --


class TestCommandFilter:
    def test_matches_command(self):
        f = CommandFilter("start")
        assert f(_new_message("/start")) is True

    def test_matches_command_with_args(self):
        f = CommandFilter("help")
        assert f(_new_message("/help arg1 arg2")) is True

    def test_no_prefix(self):
        f = CommandFilter("start")
        assert f(_new_message("start")) is False

    def test_wrong_command(self):
        f = CommandFilter("start")
        assert f(_new_message("/help")) is False

    def test_empty_text(self):
        f = CommandFilter("start")
        assert f(_new_message(text=None)) is False

    def test_wrong_event_type(self):
        f = CommandFilter("start")
        assert f(_callback_query()) is False

    def test_command_with_leading_spaces(self):
        f = CommandFilter("start")
        assert f(_new_message("  /start")) is True

    def test_command_with_slash_prefix_stripped(self):
        f = CommandFilter("/start")
        assert f(_new_message("/start")) is True
        assert f.command == "start"


# -- TagFilter --


class TestTagFilter:
    def test_matching_tag(self):
        f = TagFilter(["tag1", "tag2"])
        assert f(_new_message("tag1")) is True

    def test_non_matching_tag(self):
        f = TagFilter(["tag1", "tag2"])
        assert f(_new_message("tag3")) is False

    def test_none_text(self):
        f = TagFilter(["tag1"])
        assert f(_new_message(text=None)) is False

    def test_wrong_event_type(self):
        f = TagFilter(["tag1"])
        assert f(_callback_query()) is False


# -- CallbackDataFilter --


class TestCallbackDataFilter:
    def test_matching(self):
        f = CallbackDataFilter("btn_ok")
        assert f(_callback_query("btn_ok")) is True

    def test_non_matching(self):
        f = CallbackDataFilter("btn_cancel")
        assert f(_callback_query("btn_ok")) is False

    def test_wrong_event_type(self):
        f = CallbackDataFilter("btn_ok")
        assert f(_new_message()) is False


# -- CallbackDataRegexpFilter --


class TestCallbackDataRegexpFilter:
    def test_matching(self):
        f = CallbackDataRegexpFilter(r"^btn_")
        assert f(_callback_query("btn_ok")) is True

    def test_non_matching(self):
        f = CallbackDataRegexpFilter(r"^action_")
        assert f(_callback_query("btn_ok")) is False

    def test_wrong_event_type(self):
        f = CallbackDataRegexpFilter(r".*")
        assert f(_new_message()) is False


# -- Filter Composition --


class TestFilterComposition:
    def test_and_both_true(self):
        f = MessageFilter() & RegexpFilter(r"hello")
        assert isinstance(f, AndFilter)
        assert f(_new_message("hello")) is True

    def test_and_one_false(self):
        f = MessageFilter() & RegexpFilter(r"goodbye")
        assert f(_new_message("hello")) is False

    def test_or_one_true(self):
        f = RegexpFilter(r"hello") | RegexpFilter(r"goodbye")
        assert isinstance(f, OrFilter)
        assert f(_new_message("hello")) is True

    def test_or_both_false(self):
        f = RegexpFilter(r"^x$") | RegexpFilter(r"^y$")
        assert f(_new_message("hello")) is False

    def test_not_true_becomes_false(self):
        f = ~MessageFilter()
        assert isinstance(f, NotFilter)
        assert f(_new_message()) is False

    def test_not_false_becomes_true(self):
        f = ~MessageFilter()
        assert f(_callback_query()) is True

    def test_complex_composition(self):
        f = (MessageFilter() & RegexpFilter(r"hello")) | CallbackDataFilter("btn_ok")
        assert f(_new_message("hello")) is True
        assert f(_callback_query("btn_ok")) is True
        assert f(_new_message("goodbye")) is False


# -- Part Filters --


class TestFileFilter:
    def test_matching(self):
        f = FileFilter()
        assert f(_new_message(parts=[_file_part()])) is True

    def test_no_parts(self):
        f = FileFilter()
        assert f(_new_message(parts=None)) is False

    def test_empty_parts(self):
        f = FileFilter()
        assert f(_new_message(parts=[])) is False

    def test_wrong_part_type(self):
        f = FileFilter()
        assert f(_new_message(parts=[_sticker_part()])) is False

    def test_wrong_event(self):
        f = FileFilter()
        assert f(_callback_query()) is False


class TestReplyFilter:
    def test_matching(self):
        f = ReplyFilter()
        assert f(_new_message(parts=[_reply_part()])) is True

    def test_no_reply(self):
        f = ReplyFilter()
        assert f(_new_message(parts=[_file_part()])) is False

    def test_no_parts(self):
        f = ReplyFilter()
        assert f(_new_message(parts=None)) is False


class TestForwardFilter:
    def test_matching(self):
        f = ForwardFilter()
        assert f(_new_message(parts=[_forward_part()])) is True

    def test_no_forward(self):
        f = ForwardFilter()
        assert f(_new_message(parts=[_file_part()])) is False


class TestVoiceFilter:
    def test_matching(self):
        f = VoiceFilter()
        assert f(_new_message(parts=[_voice_part()])) is True

    def test_no_voice(self):
        f = VoiceFilter()
        assert f(_new_message(parts=[_file_part()])) is False


class TestStickerFilter:
    def test_matching(self):
        f = StickerFilter()
        assert f(_new_message(parts=[_sticker_part()])) is True

    def test_no_sticker(self):
        f = StickerFilter()
        assert f(_new_message(parts=[_file_part()])) is False


class TestMentionFilter:
    def test_matching(self):
        f = MentionFilter()
        assert f(_new_message(parts=[_mention_part()])) is True

    def test_no_mention(self):
        f = MentionFilter()
        assert f(_new_message(parts=[_file_part()])) is False

    def test_wrong_event_type(self):
        f = MentionFilter()
        assert f(_callback_query()) is False


# -- RegexpTextPartsFilter --


class TestRegexpTextPartsFilter:
    def test_matches_forward_text(self):
        f = RegexpTextPartsFilter(r"fwd")
        event = _new_message(parts=[_forward_part("fwd text")])
        assert f(event) is True

    def test_matches_reply_text(self):
        f = RegexpTextPartsFilter(r"reply")
        event = _new_message(parts=[_reply_part("reply text")])
        assert f(event) is True

    def test_no_match(self):
        f = RegexpTextPartsFilter(r"^absent$")
        event = _new_message(parts=[_forward_part("fwd text")])
        assert f(event) is False

    def test_no_parts(self):
        f = RegexpTextPartsFilter(r".*")
        event = _new_message(parts=None)
        assert f(event) is False

    def test_non_forward_reply_parts(self):
        f = RegexpTextPartsFilter(r".*")
        event = _new_message(parts=[_file_part()])
        assert f(event) is False

    def test_wrong_event_type(self):
        f = RegexpTextPartsFilter(r".*")
        assert f(_callback_query()) is False


# -- MessageTextPartFromNickFilter --


class TestMessageTextPartFromNickFilter:
    def test_any_mode_matching(self):
        f = MessageTextPartFromNickFilter("bot_nick")
        event = _new_message(parts=[
            _forward_part("text1", nick="bot_nick"),
            _forward_part("text2", nick="other"),
        ])
        assert f(event) is True

    def test_any_mode_no_match(self):
        f = MessageTextPartFromNickFilter("bot_nick")
        event = _new_message(parts=[_forward_part("text1", nick="other")])
        assert f(event) is False

    def test_all_mode_all_match(self):
        f = MessageTextPartFromNickFilter("bot_nick", all_text_parts_from_nick=True)
        event = _new_message(parts=[
            _forward_part("text1", nick="bot_nick"),
            _reply_part("text2", nick="bot_nick"),
        ])
        assert f(event) is True

    def test_all_mode_partial_match(self):
        f = MessageTextPartFromNickFilter("bot_nick", all_text_parts_from_nick=True)
        event = _new_message(parts=[
            _forward_part("text1", nick="bot_nick"),
            _forward_part("text2", nick="other"),
        ])
        assert f(event) is False

    def test_no_parts(self):
        f = MessageTextPartFromNickFilter("bot_nick")
        event = _new_message(parts=None)
        assert f(event) is False

    def test_no_relevant_parts(self):
        f = MessageTextPartFromNickFilter("bot_nick")
        event = _new_message(parts=[_file_part()])
        assert f(event) is False

    def test_wrong_event_type(self):
        f = MessageTextPartFromNickFilter("bot_nick")
        assert f(_callback_query()) is False


# -- StateFilter --


class TestStateFilter:
    class MyStates(StatesGroup):
        waiting = State()
        done = State()

    @pytest.mark.asyncio
    async def test_matching_state(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "MyStates:waiting")

        f = StateFilter(self.MyStates.waiting, storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check(event) is True

    @pytest.mark.asyncio
    async def test_non_matching_state(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "MyStates:done")

        f = StateFilter(self.MyStates.waiting, storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check(event) is False

    @pytest.mark.asyncio
    async def test_no_state_set(self):
        storage = MemoryStorage()
        f = StateFilter(self.MyStates.waiting, storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check(event) is False

    @pytest.mark.asyncio
    async def test_with_callback_query(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "MyStates:waiting")

        f = StateFilter(self.MyStates.waiting, storage)
        event = _callback_query(chat_id="chat1", user_id="user1")
        assert await f.check(event) is True

    @pytest.mark.asyncio
    async def test_with_string_state(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "custom_state")

        f = StateFilter("custom_state", storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check(event) is True

    def test_sync_call_raises(self):
        storage = MemoryStorage()
        f = StateFilter(self.MyStates.waiting, storage)
        with pytest.raises(NotImplementedError):
            f(_new_message())

    @pytest.mark.asyncio
    async def test_event_without_user(self):
        storage = MemoryStorage()
        f = StateFilter(self.MyStates.waiting, storage)
        event = _deleted_message()
        assert await f.check(event) is False

    @pytest.mark.asyncio
    async def test_with_edited_message(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "MyStates:waiting")

        f = StateFilter(self.MyStates.waiting, storage)
        event = _edited_message(chat_id="chat1", user_id="user1")
        assert await f.check(event) is True


class TestStateFilterInsideCompositeFilters:
    class MyStates(StatesGroup):
        waiting = State()

    @pytest.mark.asyncio
    async def test_state_filter_inside_and_filter(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "MyStates:waiting")

        f = MessageFilter() & StateFilter(self.MyStates.waiting, storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check_async(event) is True

    @pytest.mark.asyncio
    async def test_state_filter_inside_or_filter(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "MyStates:waiting")

        f = RegexpFilter(r"^nomatch$") | StateFilter(self.MyStates.waiting, storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check_async(event) is True

    @pytest.mark.asyncio
    async def test_state_filter_inside_not_filter(self):
        storage = MemoryStorage()

        f = ~StateFilter(self.MyStates.waiting, storage)
        event = _new_message(chat_id="chat1", user_id="user1")
        assert await f.check_async(event) is True
