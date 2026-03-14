"""Handler classes for VK Teams bot events with DI support."""

from .base import BaseHandler
from .callback_query import CallbackQueryHandler
from .chat_member import LeftChatMembersHandler, NewChatMembersHandler
from .command import CommandHandler
from .deleted_message import DeletedMessageHandler
from .edited_message import EditedMessageHandler
from .message import MessageHandler
from .pinned_message import PinnedMessageHandler, UnpinnedMessageHandler

__all__ = [
    "BaseHandler",
    "MessageHandler",
    "CommandHandler",
    "CallbackQueryHandler",
    "NewChatMembersHandler",
    "LeftChatMembersHandler",
    "EditedMessageHandler",
    "DeletedMessageHandler",
    "PinnedMessageHandler",
    "UnpinnedMessageHandler",
]
