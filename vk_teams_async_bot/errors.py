from __future__ import annotations

import builtins


class VKTeamsError(Exception):
    pass


class APIError(VKTeamsError):
    def __init__(self, status_code: int, description: str) -> None:
        self.status_code = status_code
        self.description = description
        super().__init__(f"API error {status_code}: {description}")


class ServerError(APIError):
    pass


class NetworkError(VKTeamsError):
    pass


class TimeoutError(VKTeamsError, builtins.TimeoutError):
    pass


class RateLimitError(APIError):
    pass


class SessionError(VKTeamsError):
    pass


class PollingError(VKTeamsError):
    pass


class EventParsingError(VKTeamsError):
    def __init__(self, message: str, raw_data: dict | None = None) -> None:
        self.raw_data = raw_data
        super().__init__(message)


# Legacy alias for existing code until migration is complete
ResponseStatus500orHigherError = ServerError
