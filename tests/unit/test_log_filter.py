import io
import logging

from aiohttp.client_exceptions import ClientResponseError
from yarl import URL

from vk_teams_async_bot.bot import Bot
from vk_teams_async_bot.client.log_filter import TokenSanitizingFilter


class TestTokenSanitizingFilter:
    @staticmethod
    def _bot_logger_error_output(*tokens: str) -> str:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s\n%(exc_text)s"))

        bot_logger = logging.getLogger("vk_teams_async_bot.bot")
        session_logger = logging.getLogger("vk_teams_async_bot.client.session")
        old_handlers = bot_logger.handlers[:]
        old_level = bot_logger.level
        old_propagate = bot_logger.propagate
        old_bot_filters = bot_logger.filters[:]
        old_session_filters = session_logger.filters[:]

        bot_logger.handlers = [handler]
        bot_logger.setLevel(logging.ERROR)
        bot_logger.propagate = False
        bot_logger.filters[:] = []
        session_logger.filters[:] = []

        try:
            for token in tokens:
                Bot(bot_token=token, url="https://api.example.com")

            for token in tokens:
                request_info = type(
                    "Req",
                    (),
                    {
                        "real_url": URL(
                            f"https://api.example.com/bot/v1/events/get?token={token}"
                        )
                    },
                )()
                cause = ClientResponseError(
                    request_info=request_info,
                    history=(),
                    status=500,
                    message="boom",
                )

                try:
                    raise RuntimeError("wrapped failure") from cause
                except RuntimeError as exc:
                    bot_logger.error("Polling error: %s", exc, exc_info=True)

            handler.flush()
            return stream.getvalue()
        finally:
            bot_logger.handlers = old_handlers
            bot_logger.setLevel(old_level)
            bot_logger.propagate = old_propagate
            bot_logger.filters[:] = old_bot_filters
            session_logger.filters[:] = old_session_filters

    def test_masks_token_in_message(self):
        f = TokenSanitizingFilter("secret.token.value")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="URL: https://api.example.com?token=secret.token.value",
            args=(),
            exc_info=None,
        )
        f.filter(record)
        assert "secret.token.value" not in record.msg
        assert "secr***" in record.msg

    def test_masks_token_in_format_args(self):
        f = TokenSanitizingFilter("secret.token.value")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Got %s",
            args=("secret.token.value",),
            exc_info=None,
        )
        f.filter(record)
        assert "secret.token.value" not in str(record.args)

    def test_preserves_non_token_messages(self):
        f = TokenSanitizingFilter("secret.token.value")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Normal log message",
            args=(),
            exc_info=None,
        )
        f.filter(record)
        assert record.msg == "Normal log message"

    def test_masks_token_in_dict_args(self):
        f = TokenSanitizingFilter("secret.token.value")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="%(url)s",
            args=None,
            exc_info=None,
        )
        record.args = {"url": "https://api.example.com?token=secret.token.value"}
        f.filter(record)
        assert "secret.token.value" not in str(record.args)

    def test_masks_token_in_exception_arg(self):
        f = TokenSanitizingFilter("secret.token.value")
        exc = Exception("url=https://api.example.com?token=secret.token.value")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error: %s",
            args=(exc,),
            exc_info=None,
        )
        f.filter(record)
        assert "secret.token.value" not in str(record.args)

    def test_masks_token_in_exc_info(self):
        f = TokenSanitizingFilter("secret.token.value")
        try:
            raise RuntimeError("url=https://api.example.com?token=secret.token.value")
        except RuntimeError:
            import sys

            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Something failed",
            args=(),
            exc_info=exc_info,
        )
        f.filter(record)
        assert record.exc_info is None
        assert record.exc_text is not None
        assert "secret.token.value" not in record.exc_text
        assert "secr***" in record.exc_text

    def test_masks_token_in_exc_text(self):
        f = TokenSanitizingFilter("secret.token.value")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Something failed",
            args=(),
            exc_info=None,
        )
        record.exc_text = (
            "Traceback: url=https://api.example.com?token=secret.token.value"
        )
        f.filter(record)
        assert "secret.token.value" not in record.exc_text
        assert "secr***" in record.exc_text

    def test_short_token_fully_masked(self):
        f = TokenSanitizingFilter("abc")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="token=abc",
            args=(),
            exc_info=None,
        )
        f.filter(record)
        assert "abc" not in record.msg

    def test_bot_logger_error_output_masks_token_from_exception_chain(self):
        output = self._bot_logger_error_output("secret.token.value")
        assert "secret.token.value" not in output
        assert "secr***" in output

    def test_bot_logger_masks_tokens_for_multiple_bots(self):
        output = self._bot_logger_error_output("token.A.secret", "token.B.secret")
        assert "token.A.secret" not in output
        assert "token.B.secret" not in output
        assert "toke***" in output
