import pytest
from pydantic import ValidationError

from vk_teams_async_bot.types.base import (
    VKTeamsFlexModel,
    VKTeamsModel,
    VKTeamsResponseModel,
)


class StrictModel(VKTeamsModel):
    name: str
    value: int


class FlexModel(VKTeamsFlexModel):
    name: str
    value: int


class TestVKTeamsModel:
    def test_valid_data(self):
        m = StrictModel(name="test", value=42)
        assert m.name == "test"
        assert m.value == 42

    def test_frozen(self):
        m = StrictModel(name="test", value=42)
        with pytest.raises(ValidationError):
            m.name = "changed"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            StrictModel(name="test", value=42, extra_field="nope")

    def test_round_trip(self):
        data = {"name": "test", "value": 42}
        m = StrictModel(**data)
        assert m.model_dump() == data


class ResponseModel(VKTeamsResponseModel):
    name: str
    value: int


class TestVKTeamsResponseModel:
    def test_valid_data(self):
        m = ResponseModel(name="test", value=42)
        assert m.name == "test"
        assert m.value == 42

    def test_frozen(self):
        m = ResponseModel(name="test", value=42)
        with pytest.raises(ValidationError):
            m.name = "changed"

    def test_extra_fields_ignored(self):
        m = ResponseModel(name="test", value=42, extra_field="nope")
        assert m.name == "test"
        assert not hasattr(m, "extra_field")

    def test_round_trip(self):
        data = {"name": "test", "value": 42}
        m = ResponseModel(**data)
        assert m.model_dump() == data


class TestVKTeamsFlexModel:
    def test_valid_data(self):
        m = FlexModel(name="test", value=42)
        assert m.name == "test"
        assert m.value == 42

    def test_extra_fields_allowed(self):
        m = FlexModel(name="test", value=42, extra_field="ok")
        assert m.name == "test"

    def test_frozen(self):
        m = FlexModel(name="test", value=42)
        with pytest.raises(ValidationError):
            m.name = "changed"
