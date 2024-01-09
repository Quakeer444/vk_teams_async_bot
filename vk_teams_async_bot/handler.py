import inspect

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
            is_annotated = value.annotation.__dict__.get("__metadata__")
            value = value.annotation.__dict__.get("__metadata__")[0] if is_annotated else value.annotation

            depend = [
                depend for depend in bot.depends if depend == value
            ]
            if depend:
                result = value
                depends.update({key: result})
        return depends

    async def handle(self, event, bot):
        handle_kwargs = await self.check_signature(bot)

        objects = {}
        for item_name, item_func in handle_kwargs.items():
            if inspect.isasyncgenfunction(item_func):
                item = item_func()
                objects[item_name] = await anext(item)
                continue
            if inspect.iscoroutinefunction(item_func):
                objects[item_name] = await item_func()
                continue
            if inspect.isfunction(item_func):
                objects[item_name] = item_func()
        await self.callback(event, bot, **objects)


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
