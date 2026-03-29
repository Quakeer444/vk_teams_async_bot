"""Logging filter that masks bot tokens in log output."""

from __future__ import annotations

import logging
import re
import traceback


class TokenSanitizingFilter(logging.Filter):
    """Replace occurrences of a bot token in log records with a masked version."""

    def __init__(self, token: str) -> None:
        super().__init__()
        self._tokens = {token}

    @staticmethod
    def _mask(token: str) -> str:
        return token[:4] + "***" if len(token) > 4 else "***"

    def add_token(self, token: str) -> None:
        self._tokens.add(token)

    def _contains_token(self, text: str) -> bool:
        return any(token in text for token in self._tokens)

    def _sanitize_text(self, text: str) -> str:
        for token in sorted(self._tokens, key=len, reverse=True):
            pattern = re.compile(
                rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])"
            )
            text = pattern.sub(self._mask(token), text)
        return text

    def _sanitize(self, value: object) -> str:
        """Convert value to string and replace token if present."""
        return self._sanitize_text(str(value))

    def filter(self, record: logging.LogRecord) -> bool:
        if self._contains_token(str(record.msg)):
            record.msg = self._sanitize(record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize(a) if self._contains_token(str(a)) else a
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: (self._sanitize(v) if self._contains_token(str(v)) else v)
                    for k, v in record.args.items()
                }
        if record.exc_info and record.exc_info[1] is not None:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            record.exc_text = self._sanitize_text(exc_text)
            record.exc_info = None
        elif record.exc_text and self._contains_token(record.exc_text):
            record.exc_text = self._sanitize_text(record.exc_text)
        return True


def ensure_token_sanitizing_filter(target_logger: logging.Logger, token: str) -> None:
    """Attach a shared token sanitizer to a logger and register *token*."""
    for filter_ in target_logger.filters:
        if isinstance(filter_, TokenSanitizingFilter):
            filter_.add_token(token)
            return
    target_logger.addFilter(TokenSanitizingFilter(token))
