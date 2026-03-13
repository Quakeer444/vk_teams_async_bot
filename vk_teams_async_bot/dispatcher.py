import logging

from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .bot import Bot
    from .events import Event


class Dispatcher(object):
    def __init__(self, bot: "Bot", middlewares=None):
        self.bot = bot
        self.handlers: list = []
        self.middlewares = middlewares or []

    async def processed_event(self, event: "Event"):
        for middleware in self.middlewares:
            try:
                event = await middleware.handle(event, self.bot)
            except PermissionError:
                return
            except Exception as err:
                logger.error(f"Middleware error: {err}", exc_info=True)
                continue

        for handler in self.handlers:
            if handler.check(event):
                await handler.handle(event, self.bot)
                break

    def add_handler(self, handler):
        self.handlers.append(handler)
