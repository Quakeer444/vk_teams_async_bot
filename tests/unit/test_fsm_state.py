"""Tests for FSM state definitions (State and StatesGroup)."""

import pytest

from vk_teams_async_bot.fsm.state import State, StatesGroup


class SampleForm(StatesGroup):
    step_one = State()
    step_two = State()
    step_three = State()


class AnotherForm(StatesGroup):
    waiting = State()
    done = State("custom_done")


class TestStateDescriptorProtocol:
    """State gets its name via __set_name__ when used as a class attribute."""

    def test_state_name_from_descriptor(self) -> None:
        assert SampleForm.step_one._state == "step_one"
        assert SampleForm.step_two._state == "step_two"

    def test_state_group_name_set(self) -> None:
        assert SampleForm.step_one._group_name == "SampleForm"

    def test_fully_qualified_name(self) -> None:
        assert SampleForm.step_one.state == "SampleForm:step_one"
        assert SampleForm.step_two.state == "SampleForm:step_two"
        assert SampleForm.step_three.state == "SampleForm:step_three"


class TestStateExplicitName:
    """State with an explicit name keeps it, ignoring the attribute name."""

    def test_explicit_name_preserved(self) -> None:
        assert AnotherForm.done._state == "custom_done"
        assert AnotherForm.done.state == "AnotherForm:custom_done"

    def test_implicit_name_still_works(self) -> None:
        assert AnotherForm.waiting.state == "AnotherForm:waiting"


class TestStateStandalone:
    """State used outside of a StatesGroup."""

    def test_standalone_with_name(self) -> None:
        s = State("my_state")
        assert s.state == "my_state"

    def test_standalone_without_name(self) -> None:
        s = State()
        assert s.state is None


class TestStateEquality:
    def test_equal_states(self) -> None:
        assert SampleForm.step_one == SampleForm.step_one

    def test_not_equal_states(self) -> None:
        assert SampleForm.step_one != SampleForm.step_two

    def test_equal_to_string(self) -> None:
        assert SampleForm.step_one == "SampleForm:step_one"

    def test_not_equal_to_string(self) -> None:
        assert SampleForm.step_one != "SampleForm:step_two"

    def test_not_equal_to_unrelated_type(self) -> None:
        assert SampleForm.step_one != 42

    def test_hash_consistency(self) -> None:
        assert hash(SampleForm.step_one) == hash(SampleForm.step_one)

    def test_hash_usable_in_set(self) -> None:
        s = {SampleForm.step_one, SampleForm.step_two, SampleForm.step_one}
        assert len(s) == 2


class TestStateRepr:
    def test_repr_format(self) -> None:
        r = repr(SampleForm.step_one)
        assert r == "State('SampleForm:step_one')"

    def test_repr_standalone(self) -> None:
        s = State("solo")
        assert repr(s) == "State('solo')"


class TestStatesGroup:
    def test_all_states_returns_state_instances(self) -> None:
        states = SampleForm.all_states()
        assert len(states) == 3
        assert all(isinstance(s, State) for s in states)

    def test_all_state_names(self) -> None:
        names = SampleForm.all_state_names()
        assert len(names) == 3
        assert "SampleForm:step_one" in names
        assert "SampleForm:step_two" in names
        assert "SampleForm:step_three" in names

    def test_different_groups_are_independent(self) -> None:
        sample_names = set(SampleForm.all_state_names())
        another_names = set(AnotherForm.all_state_names())
        assert sample_names.isdisjoint(another_names)

    def test_all_states_with_explicit_name(self) -> None:
        names = AnotherForm.all_state_names()
        assert "AnotherForm:custom_done" in names
