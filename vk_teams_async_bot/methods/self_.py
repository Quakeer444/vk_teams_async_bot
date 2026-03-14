"""Bot self-info method."""

from __future__ import annotations

from vk_teams_async_bot.types.user import BotInfo

from .base import BaseMethods


class SelfMethods(BaseMethods):
    """Mixin providing /self/* API methods."""

    async def get_self(self) -> BotInfo:
        """Get bot info.

        Endpoint: GET /self/get
        """
        raw = await self._session.get("/self/get")
        # The API wraps the response with an "ok" field that BotInfo
        # (strict model) does not declare.  Strip it before validation.
        data = {k: v for k, v in raw.items() if k != "ok"}
        return BotInfo.model_validate(data)
