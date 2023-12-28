from enum import Enum, StrEnum, unique


class StyleKeyboard(Enum):
    BASE = "base"
    PRIMARY = "primary"
    ATTENTION = "attention"


@unique
class ParseMode(StrEnum):
    MARKDOWNV2 = "MarkdownV2"
    HTML = "HTML"


@unique
class Parts(Enum):
    FILE = "file"
    STICKER = "sticker"
    MENTION = "mention"
    VOICE = "voice"
    FORWARD = "forward"
    REPLY = "reply"


@unique
class ChatType(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


@unique
class StyleType(Enum):
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    LINK = "link"
    MENTION = "mention"
    INLINE_CODE = "inline_code"
    PRE = "pre"
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    QUOTE = "quote"
