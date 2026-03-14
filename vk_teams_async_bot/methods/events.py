"""Event polling API methods."""

from __future__ import annotations

from vk_teams_async_bot.types.event import (
    BaseEvent,
    RawUnknownEvent,
    parse_event,
)

from .base import BaseMethods


class EventMethods(BaseMethods):
    """Mixin providing /events/* API methods."""

    async def get_events(
        self,
        last_event_id: int,
        poll_time: int,
    ) -> list[BaseEvent | RawUnknownEvent]:
        """Long-poll for events.

        Returns a list of parsed event objects.  Unknown event types
        are wrapped in ``RawUnknownEvent``.

        Endpoint: GET /events/get
        """
        raw = await self._session.get(
            "/events/get",
            lastEventId=last_event_id,
            pollTime=poll_time,
        )
        raw_events: list[dict] = raw.get("events", [])
        return [parse_event(ev) for ev in raw_events]
