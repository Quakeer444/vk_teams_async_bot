"""Declarative state definitions for FSM (finite state machine).

Inspired by aiogram's state management pattern. States are defined
declaratively as class attributes on a StatesGroup subclass.
"""

from __future__ import annotations


class State:
    """A single state in a states group.

    Can be used standalone with an explicit name, or as a descriptor
    on a StatesGroup subclass where the name is inferred automatically.

    Examples:
        Standalone usage::

            my_state = State("custom_name")

        As a descriptor on a group::

            class OrderForm(StatesGroup):
                waiting_for_name = State()  # state == "OrderForm:waiting_for_name"
    """

    def __init__(self, state: str | None = None) -> None:
        self._state = state
        self._group_name: str | None = None

    @property
    def state(self) -> str | None:
        """Return the fully qualified state name (GroupName:state_name)."""
        if self._group_name and self._state:
            return f"{self._group_name}:{self._state}"
        return self._state

    def __set_name__(self, owner: type, name: str) -> None:
        """Descriptor protocol: auto-set state name from attribute name."""
        if self._state is None:
            self._state = name
        self._group_name = owner.__name__

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.state)

    def __repr__(self) -> str:
        return f"State({self.state!r})"


class StatesGroup:
    """Base class for declarative state groups.

    Usage::

        class OrderForm(StatesGroup):
            waiting_for_name = State()
            waiting_for_phone = State()
            waiting_for_confirm = State()

        # OrderForm.waiting_for_name.state == "OrderForm:waiting_for_name"
        # OrderForm.all_states() returns list of all State instances
    """

    @classmethod
    def all_states(cls) -> list[State]:
        """Return all State instances defined on this group."""
        return [
            value
            for value in cls.__dict__.values()
            if isinstance(value, State)
        ]

    @classmethod
    def all_state_names(cls) -> list[str]:
        """Return all fully qualified state name strings."""
        return [s.state for s in cls.all_states() if s.state is not None]
