"""Tests for vk_teams_async_bot.types.message models."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter

from vk_teams_async_bot.types.message import (
    FilePart,
    ForwardPart,
    MentionPart,
    MessagePart,
    NestedMessage,
    ReplyPart,
    StickerPart,
    VoicePart,
    parse_parts,
)

# -- Fixtures: reusable raw dicts --


def _user_raw(user_id: str = "user1") -> dict:
    return {"userId": user_id, "firstName": "Alice", "lastName": "Smith"}


def _nested_message_raw(**overrides) -> dict:
    base = {
        "from": _user_raw(),
        "msgId": "msg-100",
        "text": "hello",
        "timestamp": 1700000000,
    }
    return {**base, **overrides}


# -- NestedMessage --


class TestNestedMessage:
    def test_all_fields(self) -> None:
        raw = _nested_message_raw(format={"bold": [[0, 5]]})
        msg = NestedMessage.model_validate(raw)
        assert msg.from_.user_id == "user1"
        assert msg.msg_id == "msg-100"
        assert msg.text == "hello"
        assert msg.format_ == {"bold": [[0, 5]]}
        assert msg.timestamp == 1700000000

    def test_flatten_preserves_top_level_keys(self) -> None:
        data = {
            "from": {"userId": "outer_user"},
            "msgId": "outer_id",
            "payload": {
                "from": {"userId": "inner_user"},
                "msgId": "inner_id",
                "text": "hello",
            },
        }
        msg = NestedMessage.model_validate(data)
        assert msg.from_.user_id == "outer_user"  # Top-level should win
        assert msg.msg_id == "outer_id"

    def test_minimal_fields(self) -> None:
        raw = {"from": _user_raw(), "msgId": "msg-200"}
        msg = NestedMessage.model_validate(raw)
        assert msg.msg_id == "msg-200"
        assert msg.text is None
        assert msg.format_ is None
        assert msg.timestamp is None


# -- Individual part types --


class TestFilePart:
    def test_basic(self) -> None:
        raw = {
            "type": "file",
            "payload": {"fileId": "f1", "type": "image"},
        }
        part = FilePart.model_validate(raw)
        assert part.payload.file_id == "f1"
        assert part.payload.type == "image"
        assert part.payload.caption is None

    def test_with_caption_and_format(self) -> None:
        raw = {
            "type": "file",
            "payload": {
                "fileId": "f2",
                "caption": "My photo",
                "format": {"bold": [[0, 2]]},
            },
        }
        part = FilePart.model_validate(raw)
        assert part.payload.caption == "My photo"
        assert part.payload.format_ == {"bold": [[0, 2]]}


class TestStickerPart:
    def test_basic(self) -> None:
        raw = {"type": "sticker", "payload": {"fileId": "stk1"}}
        part = StickerPart.model_validate(raw)
        assert part.payload.file_id == "stk1"


class TestMentionPart:
    def test_basic(self) -> None:
        raw = {"type": "mention", "payload": _user_raw("mentioned_user")}
        part = MentionPart.model_validate(raw)
        assert part.payload.user_id == "mentioned_user"
        assert part.payload.first_name == "Alice"


class TestVoicePart:
    def test_basic(self) -> None:
        raw = {"type": "voice", "payload": {"fileId": "v1"}}
        part = VoicePart.model_validate(raw)
        assert part.payload.file_id == "v1"


class TestForwardPart:
    def test_contains_nested_message(self) -> None:
        raw = {
            "type": "forward",
            "payload": {"message": _nested_message_raw()},
        }
        part = ForwardPart.model_validate(raw)
        assert isinstance(part.payload.message, NestedMessage)
        assert part.payload.message.msg_id == "msg-100"
        assert part.payload.message.from_.user_id == "user1"


class TestReplyPart:
    def test_contains_nested_message(self) -> None:
        raw = {
            "type": "reply",
            "payload": {"message": _nested_message_raw(text="original")},
        }
        part = ReplyPart.model_validate(raw)
        assert isinstance(part.payload.message, NestedMessage)
        assert part.payload.message.text == "original"


# -- Discriminated union --


class TestMessagePartUnion:
    def test_discriminator_resolves_all_types(self) -> None:
        adapter = TypeAdapter(MessagePart)
        cases = [
            ({"type": "file", "payload": {"fileId": "x"}}, FilePart),
            ({"type": "sticker", "payload": {"fileId": "x"}}, StickerPart),
            ({"type": "mention", "payload": _user_raw()}, MentionPart),
            ({"type": "voice", "payload": {"fileId": "x"}}, VoicePart),
            (
                {"type": "forward", "payload": {"message": _nested_message_raw()}},
                ForwardPart,
            ),
            (
                {"type": "reply", "payload": {"message": _nested_message_raw()}},
                ReplyPart,
            ),
        ]
        for raw, expected_type in cases:
            parsed = adapter.validate_python(raw)
            assert isinstance(
                parsed, expected_type
            ), f"Expected {expected_type}, got {type(parsed)}"


# -- parse_parts --


class TestParseParts:
    def test_all_valid(self) -> None:
        raw_list = [
            {"type": "file", "payload": {"fileId": "f1"}},
            {"type": "sticker", "payload": {"fileId": "s1"}},
        ]
        result = parse_parts(raw_list)
        assert len(result) == 2
        assert isinstance(result[0], FilePart)
        assert isinstance(result[1], StickerPart)

    def test_unknown_type_skipped(self) -> None:
        raw_list = [
            {"type": "file", "payload": {"fileId": "f1"}},
            {"type": "unknownWidget", "payload": {"data": 42}},
            {"type": "sticker", "payload": {"fileId": "s1"}},
        ]
        result = parse_parts(raw_list)
        assert len(result) == 2
        assert isinstance(result[0], FilePart)
        assert isinstance(result[1], StickerPart)

    def test_empty_list(self) -> None:
        assert parse_parts([]) == []

    def test_malformed_part_skipped(self) -> None:
        raw_list = [
            {"type": "file"},  # missing payload
            {"type": "sticker", "payload": {"fileId": "s1"}},
        ]
        result = parse_parts(raw_list)
        assert len(result) == 1
        assert isinstance(result[0], StickerPart)
