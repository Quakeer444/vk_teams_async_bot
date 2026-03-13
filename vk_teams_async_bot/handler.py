import inspect
import typing

from .events import Event, EventType
from .filter import Filter


class BaseHandler(object):
    def __init__(self, callback, filters=None):
        self.callback = callback
        self.filters = filters

    def check(self, event: Event):
        return bool(not self.filters or self.filters(event))

    async def check_signature(self, bot):
        signature = inspect.signature(self.callback)
        depends = {}

        for key, value in signature.parameters.items():
            if typing.get_origin(value.annotation) is typing.Annotated:
                value = typing.get_args(value.annotation)[1]
            else:
                value = value.annotation

            depend = [depend for depend in bot.depends if depend == value]
            if depend:
                result = value
                depends.update({key: result})
        return depends

    async def handle(self, event, bot):
        handle_kwargs = await self.check_signature(bot)

        objects = {}
        async_generators = []
        try:
            for item_name, item_func in handle_kwargs.items():
                if inspect.isasyncgenfunction(item_func):
                    item = item_func()
                    async_generators.append(item)
                    objects[item_name] = await anext(item)
                    continue
                if inspect.iscoroutinefunction(item_func):
                    objects[item_name] = await item_func()
                    continue
                if inspect.isfunction(item_func):
                    objects[item_name] = item_func()
            await self.callback(event, bot, **objects)
        finally:
            for gen in async_generators:
                await gen.aclose()


class MessageHandler(BaseHandler):
    def check(self, event: Event):
        return (
            super(MessageHandler, self).check(event=event)
            and event.type == EventType.NEW_MESSAGE
        )


class CommandHandler(MessageHandler):
    def __init__(self, command=None, filters=None, callback=None):
        super(CommandHandler, self).__init__(
            filters=Filter.command if filters is None else filters, callback=callback
        )

        self.command = command


class BotButtonCommandHandler(BaseHandler):
    def check(self, event: Event):
        return (
            super(BotButtonCommandHandler, self).check(event=event)
            and event.type == EventType.CALLBACK_QUERY
        )
