"""API method mixins for VK Teams Bot.

Each mixin groups related endpoints.  The ``Bot`` class inherits from
all of them to expose a complete API surface.
"""

from .base import BaseMethods
from .chats import ChatMethods
from .events import EventMethods
from .files import FileMethods
from .messages import MessageMethods
from .self_ import SelfMethods

__all__ = [
    "BaseMethods",
    "ChatMethods",
    "EventMethods",
    "FileMethods",
    "MessageMethods",
    "SelfMethods",
]
