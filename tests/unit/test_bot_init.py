from unittest.mock import AsyncMock, patch

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


class TestBotContextManager:
    @pytest.mark.asyncio
    async def test_aenter_opens_session_and_returns_bot(self):
        bot = Bot(bot_token="test-token")
        with patch.object(
            bot._session, "__aenter__", new_callable=AsyncMock
        ) as mock_enter:
            result = await bot.__aenter__()
        assert result is bot
        mock_enter.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_aexit_calls_close(self):
        bot = Bot(bot_token="test-token")
        with patch.object(bot, "close", new_callable=AsyncMock) as mock_close:
            await bot.__aexit__(None, None, None)
        mock_close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_with_enters_and_exits_session(self):
        bot = Bot(bot_token="test-token")
        with patch.object(bot._session, "__aenter__", new_callable=AsyncMock):
            with patch.object(bot, "_drain_tasks", new_callable=AsyncMock):
                with patch.object(
                    bot._session, "close", new_callable=AsyncMock
                ) as mock_close:
                    async with bot as b:
                        assert b is bot
                    mock_close.assert_awaited_once()


class TestBotClose:
    @pytest.mark.asyncio
    async def test_close_drains_then_closes_session(self):
        bot = Bot(bot_token="test-token")
        call_order = []

        async def mock_drain():
            call_order.append("drain")

        async def mock_close():
            call_order.append("close")

        with patch.object(bot, "_drain_tasks", side_effect=mock_drain):
            with patch.object(bot._session, "close", side_effect=mock_close):
                await bot.close()

        assert call_order == ["drain", "close"]
