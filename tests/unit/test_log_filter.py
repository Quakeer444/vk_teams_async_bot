import logging

from vk_teams_async_bot.client.log_filter import TokenSanitizingFilter


class TestTokenSanitizingFilter:
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
