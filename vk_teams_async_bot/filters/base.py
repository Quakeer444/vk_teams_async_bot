"""Base filter classes with composition support (AND, OR, NOT)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..types.event import BaseEvent


class FilterBase(ABC):
    """Abstract base for all filters.

    Filters are synchronous predicates that accept a typed event model
    and return True/False. Composition is supported via &, |, ~ operators.
    """

    @abstractmethod
    def __call__(self, event: BaseEvent) -> bool:
        ...

    async def check_async(self, event: BaseEvent) -> bool:
        """Async check. Default delegates to synchronous __call__."""
        return self(event)

    def iter_filters(self) -> Iterator[FilterBase]:
        """Yield all leaf filters (recurses into composite filters)."""
        yield self

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

    async def check_async(self, event: BaseEvent) -> bool:
        return await self.filter_1.check_async(
            event
        ) and await self.filter_2.check_async(event)

    def iter_filters(self) -> Iterator[FilterBase]:
        yield from self.filter_1.iter_filters()
        yield from self.filter_2.iter_filters()

    def __repr__(self) -> str:
        return f"AndFilter({self.filter_1!r}, {self.filter_2!r})"


class OrFilter(FilterBase):
    """Logical OR of two filters."""

    def __init__(self, filter_1: FilterBase, filter_2: FilterBase) -> None:
        self.filter_1 = filter_1
        self.filter_2 = filter_2

    def __call__(self, event: BaseEvent) -> bool:
        return self.filter_1(event) or self.filter_2(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return await self.filter_1.check_async(
            event
        ) or await self.filter_2.check_async(event)

    def iter_filters(self) -> Iterator[FilterBase]:
        yield from self.filter_1.iter_filters()
        yield from self.filter_2.iter_filters()

    def __repr__(self) -> str:
        return f"OrFilter({self.filter_1!r}, {self.filter_2!r})"


class NotFilter(FilterBase):
    """Logical NOT of a filter."""

    def __init__(self, filter_: FilterBase) -> None:
        self.filter_ = filter_

    def __call__(self, event: BaseEvent) -> bool:
        return not self.filter_(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return not await self.filter_.check_async(event)

    def iter_filters(self) -> Iterator[FilterBase]:
        yield from self.filter_.iter_filters()

    def __repr__(self) -> str:
        return f"NotFilter({self.filter_!r})"
