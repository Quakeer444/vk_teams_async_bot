from __future__ import annotations

import json

from .enums import StyleType


class Style:
    __slots__ = ("ranges",)

    def __init__(self) -> None:
        self.ranges: list[dict[str, int | str]] = []

    def add(
        self,
        offset: int,
        length: int,
        **kwargs: str,
    ) -> None:
        entry: dict[str, int | str] = {"offset": offset, "length": length}
        entry.update(kwargs)
        self.ranges.append(entry)

    def to_list(self) -> list[dict[str, int | str]]:
        return self.ranges

    def to_json(self) -> str:
        return json.dumps(self.ranges)


class Format:
    __slots__ = ("styles",)

    def __init__(self) -> None:
        self.styles: dict[StyleType, Style] = {}

    def add(
        self,
        style: StyleType,
        offset: int,
        length: int,
        **kwargs: str,
    ) -> Format:
        if style not in self.styles:
            self.styles[style] = Style()
        self.styles[style].add(offset, length, **kwargs)
        return self

    def to_dict(self) -> dict[str, list[dict[str, int | str]]]:
        return {
            style_type.value: style.to_list()
            for style_type, style in self.styles.items()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
