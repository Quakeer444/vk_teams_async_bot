"""Base mixin for API method groups."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vk_teams_async_bot.client.session import VKTeamsSession


class BaseMethods:
    """Base mixin that holds a reference to the HTTP session.

    Every method mixin inherits from this class.  The ``_session``
    attribute is injected by ``Bot.__init__`` and provides
    ``get`` / ``post`` helpers that return raw dicts.
    """

    _session: VKTeamsSession
