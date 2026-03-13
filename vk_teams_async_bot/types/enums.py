from enum import StrEnum, unique


@unique
class ParseMode(StrEnum):
    MARKDOWNV2 = "MarkdownV2"
    HTML = "HTML"


@unique
class ChatType(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


@unique
class StyleKeyboard(StrEnum):
    BASE = "base"
    PRIMARY = "primary"
    ATTENTION = "attention"


@unique
class Parts(StrEnum):
    FILE = "file"
    STICKER = "sticker"
    MENTION = "mention"
    VOICE = "voice"
    FORWARD = "forward"
    REPLY = "reply"


@unique
class StyleType(StrEnum):
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


@unique
class ChatAction(StrEnum):
    TYPING = "typing"
    LOOKING = "looking"


@unique
class EventType(StrEnum):
    NEW_MESSAGE = "newMessage"
    EDITED_MESSAGE = "editedMessage"
    DELETED_MESSAGE = "deletedMessage"
    PINNED_MESSAGE = "pinnedMessage"
    UNPINNED_MESSAGE = "unpinnedMessage"
    NEW_CHAT_MEMBERS = "newChatMembers"
    LEFT_CHAT_MEMBERS = "leftChatMembers"
    CALLBACK_QUERY = "callbackQuery"
