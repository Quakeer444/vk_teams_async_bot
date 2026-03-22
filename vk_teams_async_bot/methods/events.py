"""Event polling API methods."""

from __future__ import annotations

import logging

from vk_teams_async_bot.types.event import BaseEvent, RawUnknownEvent, parse_event

from .base import BaseMethods

logger = logging.getLogger(__name__)


class EventMethods(BaseMethods):
    """Mixin providing /events/* API methods."""

    async def get_events(
        self,
        last_event_id: int,
        poll_time: int,
    ) -> list[BaseEvent | RawUnknownEvent]:
        """Long-poll for events.

        Returns a list of parsed event objects.  Unknown event types
        are wrapped in ``RawUnknownEvent``.  Malformed events are logged
        and skipped so the batch is never lost entirely.

        Endpoint: GET /events/get
        """
        raw = await self._session.get(
            "/events/get",
            lastEventId=last_event_id,
            pollTime=poll_time,
        )
        raw_events: list[dict] = raw.get("events", [])
        results: list[BaseEvent | RawUnknownEvent] = []
        for ev in raw_events:
            logger.debug("Raw event: %s", ev)
            try:
                results.append(parse_event(ev))
            except Exception as exc:
                event_id = ev.get("eventId", 0)
                logger.error(
                    "Failed to parse event (eventId=%s, type=%s): %s",
                    event_id,
                    ev.get("type"),
                    exc,
                )
                results.append(
                    RawUnknownEvent(
                        eventId=event_id,
                        type=ev.get("type", ""),
                        payload=ev.get("payload", {}),
                    )
                )
        logger.debug("Parsed %d/%d events", len(results), len(raw_events))
        return results
