import pytest

from vk_teams_async_bot.errors import (
    APIError,
    EventParsingError,
    NetworkError,
    PollingError,
    RateLimitError,
    ServerError,
    SessionError,
    TimeoutError,
    VKTeamsError,
)


class TestErrorHierarchy:
    def test_api_error_is_vk_teams_error(self):
        err = APIError(400, "Bad request")
        assert isinstance(err, VKTeamsError)

    def test_server_error_is_api_error(self):
        err = ServerError(500, "Internal")
        assert isinstance(err, APIError)
        assert isinstance(err, VKTeamsError)

    def test_rate_limit_error_is_api_error(self):
        err = RateLimitError(429, "Too many requests")
        assert isinstance(err, APIError)

    def test_network_error_is_vk_teams_error(self):
        assert isinstance(NetworkError(), VKTeamsError)

    def test_timeout_error_is_vk_teams_error(self):
        assert isinstance(TimeoutError(), VKTeamsError)

    def test_timeout_error_is_builtin_timeout(self):
        import builtins

        assert isinstance(TimeoutError(), builtins.TimeoutError)

    def test_session_error_is_vk_teams_error(self):
        assert isinstance(SessionError(), VKTeamsError)

    def test_polling_error_is_vk_teams_error(self):
        assert isinstance(PollingError(), VKTeamsError)


class TestAPIError:
    def test_attributes(self):
        err = APIError(404, "Not found")
        assert err.status_code == 404
        assert err.description == "Not found"

    def test_str(self):
        err = APIError(400, "Bad request")
        assert "400" in str(err)
        assert "Bad request" in str(err)


class TestEventParsingError:
    def test_with_raw_data(self):
        raw = {"type": "unknown", "payload": {}}
        err = EventParsingError("Failed to parse", raw_data=raw)
        assert err.raw_data == raw
        assert "Failed to parse" in str(err)

    def test_without_raw_data(self):
        err = EventParsingError("No data")
        assert err.raw_data is None
