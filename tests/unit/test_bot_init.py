import pytest

from vk_teams_async_bot import Bot


class TestBotTokenValidation:
    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="bot_token"):
            Bot(bot_token="")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="bot_token"):
            Bot(bot_token="   ")

    def test_valid_token_accepted(self):
        bot = Bot(bot_token="valid.token.123")
        assert bot is not None


class TestBotSignalHandler:
    def test_first_signal_sets_running_false(self):
        bot = Bot(bot_token="test.token")
        bot._running = True
        bot._handle_signal()
        assert bot._running is False

    def test_second_signal_raises_system_exit(self):
        bot = Bot(bot_token="test.token")
        bot._running = False
        with pytest.raises(SystemExit):
            bot._handle_signal()
