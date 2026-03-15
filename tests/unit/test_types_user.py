import pytest
from pydantic import ValidationError

from vk_teams_async_bot.types.user import BotInfo, PhotoUrl, User, UserAdmin


class TestUser:
    def test_from_dict_with_alias(self):
        data = {"userId": "123", "firstName": "John", "lastName": "Doe", "nick": "jdoe"}
        user = User(**data)
        assert user.user_id == "123"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.nick == "jdoe"

    def test_minimal(self):
        user = User(userId="123")
        assert user.user_id == "123"
        assert user.first_name is None

    def test_round_trip(self):
        data = {"userId": "123", "firstName": "John"}
        user = User(**data)
        dumped = user.model_dump(by_alias=True, exclude_none=True)
        assert dumped == data

    def test_extra_fields_allowed(self):
        data = {"userId": "123", "unknown_field": "value"}
        user = User(**data)
        assert user.user_id == "123"


class TestBotInfo:
    def test_full(self):
        data = {
            "userId": "bot123",
            "nick": "mybot",
            "firstName": "Bot",
            "about": "A test bot",
            "photo": [{"url": "https://example.com/photo.jpg"}],
        }
        bot = BotInfo(**data)
        assert bot.user_id == "bot123"
        assert bot.nick == "mybot"
        assert bot.photo[0].url == "https://example.com/photo.jpg"

    def test_minimal(self):
        bot = BotInfo(userId="bot123")
        assert bot.user_id == "bot123"
        assert bot.photo is None

    def test_extra_fields_ignored(self):
        bot = BotInfo(userId="bot123", unknown="nope")
        assert bot.user_id == "bot123"


class TestUserAdmin:
    def test_creator(self):
        ua = UserAdmin(userId="123", creator=True)
        assert ua.user_id == "123"
        assert ua.creator is True
        assert ua.admin is None

    def test_admin(self):
        ua = UserAdmin(userId="456", admin=True)
        assert ua.admin is True
        assert ua.creator is None

    def test_plain_member(self):
        ua = UserAdmin(userId="789")
        assert ua.creator is None
        assert ua.admin is None


class TestPhotoUrl:
    def test_url(self):
        p = PhotoUrl(url="https://example.com/img.png")
        assert p.url == "https://example.com/img.png"
