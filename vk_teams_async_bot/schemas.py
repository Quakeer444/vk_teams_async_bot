from dataclasses import dataclass

from pydantic import BaseModel


@dataclass(slots=True, frozen=True)
class VKTeamsEventsResponse:
    events: list[dict]
    ok: bool


class Event(BaseModel):
    eventId: int
    payload: dict
    type_: str
