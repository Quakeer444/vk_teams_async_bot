"""Shared helpers for API method modules."""
from __future__ import annotations


def bool_str(value: bool | None) -> str | None:
    """Convert bool to 'true'/'false' string; None passes through."""
    if value is None:
        return None
    return "true" if value else "false"
