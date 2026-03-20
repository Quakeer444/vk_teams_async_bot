"""Logging filter that masks bot tokens in log output."""

from __future__ import annotations

import logging


class TokenSanitizingFilter(logging.Filter):
    """Replace occurrences of a bot token in log records with a masked version."""

    def __init__(self, token: str) -> None:
        super().__init__()
        self._token = token
        self._masked = token[:4] + "***" if len(token) > 4 else "***"

    def filter(self, record: logging.LogRecord) -> bool:
        if self._token in str(record.msg):
            record.msg = str(record.msg).replace(self._token, self._masked)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    str(a).replace(self._token, self._masked)
                    if isinstance(a, str) and self._token in a
                    else a
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: str(v).replace(self._token, self._masked)
                    if isinstance(v, str) and self._token in v
                    else v
                    for k, v in record.args.items()
                }
        return True
