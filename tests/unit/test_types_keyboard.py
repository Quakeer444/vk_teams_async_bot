import json

import pytest
from pydantic import ValidationError

from vk_teams_async_bot.types.keyboard import InlineKeyboardMarkup, KeyboardButton


class TestKeyboardButton:
    def test_with_callback_data(self):
        btn = KeyboardButton(text="Click", callbackData="cb_1")
        assert btn.text == "Click"
        assert btn.callback_data == "cb_1"
        assert btn.url is None

    def test_with_url(self):
        btn = KeyboardButton(text="Open", url="https://example.com")
        assert btn.url == "https://example.com"
        assert btn.callback_data is None

    def test_url_xor_callback_both_present(self):
        with pytest.raises(ValidationError, match="mutually exclusive"):
            KeyboardButton(text="Bad", url="https://x.com", callbackData="cb")

    def test_url_xor_callback_neither_present(self):
        with pytest.raises(ValidationError, match="one of url or callbackData"):
            KeyboardButton(text="Bad")

    def test_default_style(self):
        btn = KeyboardButton(text="Click", callbackData="cb")
        assert btn.style == "base"

    def test_custom_style(self):
        btn = KeyboardButton(text="Click", callbackData="cb", style="primary")
        assert btn.style == "primary"

    def test_to_dict(self):
        btn = KeyboardButton(text="Go", callbackData="cb_go", style="attention")
        d = btn.to_dict()
        assert d == {
            "text": "Go",
            "callbackData": "cb_go",
            "style": "attention",
        }

    def test_to_dict_with_url(self):
        btn = KeyboardButton(text="Link", url="https://example.com")
        d = btn.to_dict()
        assert d == {
            "text": "Link",
            "url": "https://example.com",
            "style": "base",
        }
        assert "callbackData" not in d

    def test_frozen(self):
        btn = KeyboardButton(text="Click", callbackData="cb")
        with pytest.raises(ValidationError):
            btn.text = "Changed"


class TestInlineKeyboardMarkup:
    def test_add_buttons_respects_row_limit(self):
        kb = InlineKeyboardMarkup(buttons_in_row=2)
        b1 = KeyboardButton(text="A", callbackData="a")
        b2 = KeyboardButton(text="B", callbackData="b")
        b3 = KeyboardButton(text="C", callbackData="c")
        kb.add(b1, b2, b3)
        assert len(kb.keyboard) == 2
        assert len(kb.keyboard[0]) == 2
        assert len(kb.keyboard[1]) == 1

    def test_row_adds_all_in_one(self):
        kb = InlineKeyboardMarkup()
        b1 = KeyboardButton(text="A", callbackData="a")
        b2 = KeyboardButton(text="B", callbackData="b")
        b3 = KeyboardButton(text="C", callbackData="c")
        kb.row(b1, b2, b3)
        assert len(kb.keyboard) == 1
        assert len(kb.keyboard[0]) == 3

    def test_to_json(self):
        kb = InlineKeyboardMarkup()
        kb.row(KeyboardButton(text="OK", callbackData="ok"))
        result = json.loads(kb.to_json())
        assert len(result) == 1
        assert result[0][0]["text"] == "OK"
        assert result[0][0]["callbackData"] == "ok"

    def test_str(self):
        kb = InlineKeyboardMarkup()
        kb.row(KeyboardButton(text="X", callbackData="x"))
        assert str(kb) == kb.to_json()

    def test_add_operator_with_markup(self):
        kb1 = InlineKeyboardMarkup()
        kb1.row(KeyboardButton(text="A", callbackData="a"))
        kb2 = InlineKeyboardMarkup()
        kb2.row(KeyboardButton(text="B", callbackData="b"))
        combined = kb1 + kb2
        assert len(combined.keyboard) == 2
        assert len(kb1.keyboard) == 1  # original not mutated

    def test_add_operator_with_button(self):
        kb = InlineKeyboardMarkup()
        kb.row(KeyboardButton(text="A", callbackData="a"))
        btn = KeyboardButton(text="B", callbackData="b")
        combined = kb + btn
        assert len(combined.keyboard) == 2

    def test_add_operator_type_error(self):
        kb = InlineKeyboardMarkup()
        with pytest.raises(TypeError):
            kb + "invalid"
