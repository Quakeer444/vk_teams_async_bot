import asyncio
import functools
import json
import logging
from typing import Dict, List, Mapping, Protocol, Union

import aiofiles
import aiohttp

from .constants import StyleKeyboard, StyleType
from .errors import ResponseStatus500orHigherError

logger = logging.getLogger(__name__)


class JsonSerializeAble(Protocol):
    def to_json(self):
        raise NotImplementedError


class DictionaryAble(Protocol):
    def to_dic(self):
        raise NotImplementedError


class KeyboardButton(DictionaryAble, JsonSerializeAble):
    __slots__ = ("text", "callbackData", "style", "url")

    def __init__(
        self,
        text: str,
        style: StyleKeyboard = StyleKeyboard.BASE,
        callback_data: str | None = None,
        url: str | None = None,
    ):
        self.text = text
        self.callbackData = callback_data
        self.style = style.value
        self.url = url

    def to_json(self) -> str:
        return json.dumps(self.to_dic(), ensure_ascii=False)

    def to_dic(self) -> Mapping:
        data = {"text": self.text}
        if self.callbackData:
            data["callbackData"] = self.callbackData
        if self.style:
            data["style"] = self.style
        if self.url:
            data["url"] = self.url
        return data


class InlineKeyboardMarkup(JsonSerializeAble):
    __slots__ = ("buttons_in_row", "keyboard")

    def __init__(self, buttons_in_row: int = 2):
        self.buttons_in_row = buttons_in_row
        self.keyboard: list = []

    def add(self, *buttons: KeyboardButton) -> None:
        number_button = 1
        row = []
        for button in buttons:
            row.append(button.to_dic())
            if number_button % self.buttons_in_row == 0:
                self.keyboard.append(row)
                row = []
            number_button += 1
        self.keyboard.append(row) if len(row) > 0 else None

    def row(self, *buttons: KeyboardButton):
        buttons_in_row = []
        for button in buttons:
            buttons_in_row.append(button.to_dic())
        self.keyboard.append(buttons_in_row)

    def to_json(self) -> str:
        return json.dumps(self.keyboard, ensure_ascii=False)

    def __str__(self) -> str:
        return self.to_json()


class Style(DictionaryAble, JsonSerializeAble):
    __slots__ = "ranges"

    def __init__(self):
        self.ranges = []

    def add(self, offset, length, args=None):
        range_ = {"offset": offset, "length": length}
        if args is not None:
            self.ranges.append({**range_, **args})
        else:
            self.ranges.append(range_)

    def to_dic(self):
        return self.ranges

    def to_json(self):
        return json.dumps(self.ranges)


class Format(DictionaryAble, JsonSerializeAble):
    __slots__ = "styles"

    def __init__(self):
        self.styles = {}

    def add(self, style, offset, length, args=None):
        StyleType(style)
        if style in self.styles.keys():
            self.styles[style].add(offset, length, args)
        else:
            newStyle = Style()
            newStyle.add(offset, length, args)
            self.styles[style] = newStyle

    def to_dic(self):
        return self.styles

    def to_json(self):
        result = {}
        for key in self.styles.keys():
            result[key] = self.styles[key].to_dic()
        return json.dumps(result)


def format_to_json(format_):
    if isinstance(format_, Format):
        return format_.to_json()
    elif isinstance(format_, list):
        return json.dumps(format_)
    elif isinstance(format_, str):
        return format_
    elif format_ is None:
        return format_
    else:
        raise ValueError(f"Unsupported type: format_ ({type(format_)})")


def keyboard_to_json(
    keyboard_markup: Union[List[List[Dict]], InlineKeyboardMarkup, str, None]
) -> Union[str, None]:
    if isinstance(keyboard_markup, InlineKeyboardMarkup):
        return keyboard_markup.to_json()
    elif isinstance(keyboard_markup, list):
        return json.dumps(keyboard_markup)
    elif isinstance(keyboard_markup, str):
        return keyboard_markup
    else:
        raise ValueError(f"Unsupported type: keyboard_markup ({type(keyboard_markup)})")


async def async_read_file(file_path: str) -> bytes:
    async with aiofiles.open(file_path, "rb") as file:
        content = await file.read()
    return content


async def download_file(file_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            if response.status == 200:
                return await response.read()


def retry_on_500_or_higher_response(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        delay_between_retries = kwargs.get("delay_between_retries", None)
        established_retries = kwargs.get("_count_request_retries", 2)
        current_retries = established_retries

        while current_retries > 0:
            try:
                if current_retries < established_retries:
                    delay = delay_between_retries
                    if delay:
                        await asyncio.sleep(delay)
                    logger.warning(
                        f"{func.__name__=} attempt "
                        f"{(established_retries + 1) - current_retries} "
                        f"of {established_retries}- {kwargs}"
                    )

                return await func(self, *args, **kwargs)

            except ResponseStatus500orHigherError as err:
                logger.warning(f"{err=} {kwargs=}")
                current_retries -= 1
                if current_retries == 0:
                    logger.error(
                        f" {func.__name__=} ran out of attempts. "
                        f"The request will not be processed {kwargs}"
                    )
                    raise

    return wrapper
