"""Event dispatcher with middleware chain, handler routing, and decorator shortcuts."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable, Sequence

from .filters.base import FilterBase
from .filters.message import CommandFilter
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
from .types.event import BaseEvent, RawUnknownEvent
from .utils import extract_chat_user

if TYPE_CHECKING:
    from .bot import Bot

logger = logging.getLogger(__name__)


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
        self._user_locks: dict[tuple[str, str], asyncio.Lock] = {}

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

    def command(
        self,
        cmd: str,
        *filters: FilterBase,
    ) -> Callable:
        """Convenience decorator for command handlers.

        Equivalent to ``@dp.message(CommandFilter(cmd), *filters)``::

            @dp.command("start")
            async def on_start(event, bot):
                await bot.send_text(event.chat.chat_id, "Hello!")
        """
        return self.message(CommandFilter(cmd), *filters)

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
        user_key = None
        if self._storage is not None:
            user_key = extract_chat_user(event)
            if user_key is not None:
                data["fsm_context"] = FSMContext(storage=self._storage, key=user_key)

        # Build the handler chain wrapped by middlewares
        wrapped = self.middleware.wrap(self._dispatch_to_handler)
        if user_key is not None:
            lock = self._user_locks.setdefault(user_key, asyncio.Lock())
            async with lock:
                await wrapped(event, data)
        else:
            await wrapped(event, data)

    async def _dispatch_to_handler(
        self,
        event: BaseEvent | RawUnknownEvent,
        data: dict[str, Any],
    ) -> None:
        """Find the first matching handler and execute it."""
        if not isinstance(event, BaseEvent):
            logger.debug(
                "Skipping non-BaseEvent in dispatch: %s", type(event).__name__
            )
            return
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

            await handler.handle(event, bot, extra_kwargs=data)
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
            for leaf in f.iter_filters():
                if isinstance(leaf, StateFilter) and leaf._storage is None:
                    leaf._storage = self._storage
