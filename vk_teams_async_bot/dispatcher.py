from typing import TYPE_CHECKING

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
            event = await middleware.handle(event, self.bot)

        for handler in self.handlers:
            if handler.check(event):
                await handler.handle(event, self.bot)
                break

    def add_handler(self, handler):
        self.handlers.append(handler)
