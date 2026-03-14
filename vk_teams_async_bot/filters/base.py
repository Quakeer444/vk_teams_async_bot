"""Base filter classes with composition support (AND, OR, NOT)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types.event import BaseEvent


class FilterBase(ABC):
    """Abstract base for all filters.

    Filters are synchronous predicates that accept a typed event model
    and return True/False. Composition is supported via &, |, ~ operators.
    """

    @abstractmethod
    def __call__(self, event: BaseEvent) -> bool:
        ...

    def __and__(self, other: FilterBase) -> AndFilter:
        return AndFilter(self, other)

    def __or__(self, other: FilterBase) -> OrFilter:
        return OrFilter(self, other)

    def __invert__(self) -> NotFilter:
        return NotFilter(self)


class AndFilter(FilterBase):
    """Logical AND of two filters."""

    def __init__(self, filter_1: FilterBase, filter_2: FilterBase) -> None:
        self.filter_1 = filter_1
        self.filter_2 = filter_2

    def __call__(self, event: BaseEvent) -> bool:
        return self.filter_1(event) and self.filter_2(event)

    def __repr__(self) -> str:
        return f"AndFilter({self.filter_1!r}, {self.filter_2!r})"


class OrFilter(FilterBase):
    """Logical OR of two filters."""

    def __init__(self, filter_1: FilterBase, filter_2: FilterBase) -> None:
        self.filter_1 = filter_1
        self.filter_2 = filter_2

    def __call__(self, event: BaseEvent) -> bool:
        return self.filter_1(event) or self.filter_2(event)

    def __repr__(self) -> str:
        return f"OrFilter({self.filter_1!r}, {self.filter_2!r})"


class NotFilter(FilterBase):
    """Logical NOT of a filter."""

    def __init__(self, filter_: FilterBase) -> None:
        self.filter_ = filter_

    def __call__(self, event: BaseEvent) -> bool:
        return not self.filter_(event)

    def __repr__(self) -> str:
        return f"NotFilter({self.filter_!r})"
