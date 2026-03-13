from __future__ import annotations

import json
from typing import Self

from pydantic import Field, model_validator

from .base import VKTeamsModel
from .enums import StyleKeyboard


class KeyboardButton(VKTeamsModel):
    text: str
    callback_data: str | None = Field(default=None, alias="callbackData")
    style: StyleKeyboard = StyleKeyboard.BASE
    url: str | None = None

    @model_validator(mode="after")
    def _validate_url_xor_callback(self) -> Self:
        if self.url and self.callback_data:
            raise ValueError(
                "KeyboardButton: url and callbackData are mutually exclusive"
            )
        if not self.url and not self.callback_data:
            raise ValueError(
                "KeyboardButton: one of url or callbackData is required"
            )
        return self

    def to_dict(self) -> dict[str, str]:
        result: dict[str, str] = {"text": self.text}
        if self.url is not None:
            result["url"] = self.url
        if self.callback_data is not None:
            result["callbackData"] = self.callback_data
        result["style"] = self.style.value
        return result


class InlineKeyboardMarkup:
    __slots__ = ("buttons_in_row", "keyboard")

    def __init__(self, buttons_in_row: int = 2) -> None:
        self.buttons_in_row = buttons_in_row
        self.keyboard: list[list[KeyboardButton]] = []

    def add(self, *buttons: KeyboardButton) -> None:
        row: list[KeyboardButton] = []
        for button in buttons:
            row.append(button)
            if len(row) >= self.buttons_in_row:
                self.keyboard.append(row)
                row = []
        if row:
            self.keyboard.append(row)

    def row(self, *buttons: KeyboardButton) -> None:
        self.keyboard.append(list(buttons))

    def to_json(self) -> str:
        return json.dumps(
            [[btn.to_dict() for btn in row] for row in self.keyboard]
        )

    def __str__(self) -> str:
        return self.to_json()

    def __add__(self, other: InlineKeyboardMarkup | KeyboardButton) -> InlineKeyboardMarkup:
        new_markup = InlineKeyboardMarkup(buttons_in_row=self.buttons_in_row)
        new_markup.keyboard = [row[:] for row in self.keyboard]
        if isinstance(other, InlineKeyboardMarkup):
            new_markup.keyboard.extend(row[:] for row in other.keyboard)
        elif isinstance(other, KeyboardButton):
            new_markup.keyboard.append([other])
        else:
            raise TypeError(
                f"unsupported operand type for +: "
                f"'InlineKeyboardMarkup' and '{type(other).__name__}'"
            )
        return new_markup
