"""Event dispatcher with middleware chain, handler routing, and decorator shortcuts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Sequence

from .filters.base import FilterBase
from .filters.state import StateFilter
from .fsm.context import FSMContext
from .fsm.storage.base import BaseStorage
from .handlers.base import BaseHandler
from .handlers.callback_query import CallbackQueryHandler
from .handlers.chat_member import LeftChatMembersHandler, NewChatMembersHandler
from .handlers.command import CommandHandler
from .handlers.deleted_message import DeletedMessageHandler
from .handlers.edited_message import EditedMessageHandler
from .handlers.message import MessageHandler
from .handlers.pinned_message import PinnedMessageHandler, UnpinnedMessageHandler
from .middleware.base import BaseMiddleware
from .middleware.manager import MiddlewareManager
from .types.event import (
    BaseEvent,
    CallbackQueryEvent,
    EditedMessageEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    RawUnknownEvent,
)

if TYPE_CHECKING:
    from .bot import Bot

logger = logging.getLogger(__name__)


def _extract_chat_user(event: BaseEvent | RawUnknownEvent) -> tuple[str, str] | None:
    """Extract (chat_id, user_id) from an event for FSM context."""
    if isinstance(event, (NewMessageEvent, EditedMessageEvent, PinnedMessageEvent)):
        return event.chat.chat_id, event.from_.user_id
    if isinstance(event, CallbackQueryEvent):
        return event.chat.chat_id, event.from_.user_id
    return None


class Dispatcher:
    """Routes events through middleware chain to matching handlers.

    Supports decorator shortcuts for registering handlers::

        dp = Dispatcher()

        @dp.message(CommandFilter("/start"))
        async def on_start(event, bot):
            await bot.send_text(event.chat.chat_id, "Hello!")

        @dp.callback_query()
        async def on_button(event, bot):
            await bot.answer_callback_query(event.query_id)
    """

    def __init__(
        self,
        storage: BaseStorage | None = None,
    ) -> None:
        self.handlers: list[BaseHandler] = []
        self.middleware = MiddlewareManager()
        self._storage = storage

    def add_middleware(self, mw: BaseMiddleware) -> None:
        """Register a middleware instance."""
        self.middleware.add(mw)

    def add_handler(self, handler: BaseHandler) -> None:
        """Register a handler instance."""
        self.handlers.append(handler)

    # -- Decorator shortcuts ---------------------------------------------------

    def message(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``MessageHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = MessageHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def edited_message(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``EditedMessageHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = EditedMessageHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def deleted_message(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``DeletedMessageHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = DeletedMessageHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def pinned_message(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``PinnedMessageHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = PinnedMessageHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def unpinned_message(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``UnpinnedMessageHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = UnpinnedMessageHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def new_chat_members(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``NewChatMembersHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = NewChatMembersHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def left_chat_members(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``LeftChatMembersHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = LeftChatMembersHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    def callback_query(
        self,
        *filters: FilterBase,
    ) -> Callable:
        """Decorator shortcut for ``CallbackQueryHandler``."""

        def decorator(callback: Callable) -> Callable:
            handler = CallbackQueryHandler(
                callback=callback,
                filters=filters if filters else None,
            )
            self.add_handler(handler)
            return callback

        return decorator

    # -- Event processing ------------------------------------------------------

    async def feed_event(self, event: BaseEvent | RawUnknownEvent, bot: Bot) -> None:
        """Process a single event through the middleware chain and handlers.

        This is the main entry point called by Bot.start_polling().
        """
        if isinstance(event, RawUnknownEvent):
            logger.warning("Skipping unknown event type: %s", event.type)
            return

        data: dict[str, Any] = {
            "bot": bot,
            "dispatcher": self,
        }

        # Inject FSMContext if storage is configured
        if self._storage is not None:
            key = _extract_chat_user(event)
            if key is not None:
                data["fsm_context"] = FSMContext(
                    storage=self._storage, key=key
                )

        # Build the handler chain wrapped by middlewares
        wrapped = self.middleware.wrap(self._dispatch_to_handler)
        await wrapped(event, data)

    async def _dispatch_to_handler(
        self,
        event: BaseEvent | RawUnknownEvent,
        data: dict[str, Any],
    ) -> None:
        """Find the first matching handler and execute it."""
        bot = data["bot"]

        for handler in self.handlers:
            # Use async check if handler has async filters (e.g. StateFilter)
            if handler.has_async_filters():
                # Inject storage into StateFilter if needed
                if self._storage is not None:
                    self._inject_storage(handler)
                if not await handler.check_async(event):
                    continue
            else:
                if not handler.check(event):
                    continue

            # Inject FSMContext into handler kwargs if the callback wants it
            fsm_context = data.get("fsm_context")
            if fsm_context is not None:
                bot._fsm_context = fsm_context

            await handler.handle(event, bot)
            return

    def _inject_storage(self, handler: BaseHandler) -> None:
        """Ensure StateFilter instances have a reference to the storage."""
        if not handler.filters:
            return

        filters: Sequence[FilterBase]
        if isinstance(handler.filters, FilterBase):
            filters = [handler.filters]
        else:
            filters = handler.filters

        for f in filters:
            if isinstance(f, StateFilter) and f._storage is None:
                f._storage = self._storage
