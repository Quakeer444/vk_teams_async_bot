"""User-related filters: sender matching."""

from __future__ import annotations

from ..types.event import BaseEvent
from .base import FilterBase


class FromUserFilter(FilterBase):
    """Match events by sender user_id.

    Works on any event that has a ``from_`` field.
    Uses frozenset internally for O(1) lookup.
    """

    def __init__(self, user_ids: str | list[str]) -> None:
        if isinstance(user_ids, str):
            self._user_ids = frozenset([user_ids])
        else:
            self._user_ids = frozenset(user_ids)

    def __call__(self, event: BaseEvent) -> bool:
        from_ = getattr(event, "from_", None)
        if from_ is None:
            return False
        return from_.user_id in self._user_ids

    def __repr__(self) -> str:
        return f"FromUserFilter(user_ids={sorted(self._user_ids)!r})"
