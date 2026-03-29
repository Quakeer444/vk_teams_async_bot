"""Logging filter that masks bot tokens in log output."""

from __future__ import annotations

import logging
import traceback


class TokenSanitizingFilter(logging.Filter):
    """Replace occurrences of a bot token in log records with a masked version."""

    def __init__(self, token: str) -> None:
        super().__init__()
        self._token = token
        self._masked = token[:4] + "***" if len(token) > 4 else "***"

    def _sanitize(self, value: object) -> str:
        """Convert value to string and replace token if present."""
        text = str(value)
        if self._token in text:
            return text.replace(self._token, self._masked)
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        if self._token in str(record.msg):
            record.msg = str(record.msg).replace(self._token, self._masked)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize(a) if self._token in str(a) else a
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: (self._sanitize(v) if self._token in str(v) else v)
                    for k, v in record.args.items()
                }
        if record.exc_info and record.exc_info[1] is not None:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            record.exc_text = exc_text.replace(self._token, self._masked)
            record.exc_info = None
        elif record.exc_text and self._token in record.exc_text:
            record.exc_text = record.exc_text.replace(self._token, self._masked)
        return True
