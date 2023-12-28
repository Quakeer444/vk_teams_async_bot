import inspect

from .events import Event, EventType
from .filter import Filter


class BaseHandler(object):
    def __init__(self, callback, filters=None):
        self.callback = callback
        self.filters = filters

    def check(self, event: Event):
        return bool(not self.filters or self.filters(event))

    def check_signature(self, bot):
        signature = inspect.signature(self.callback)
        depends = {}
        for key, value in signature.parameters.items():
            depend = [
                depend for depend in bot.depends if isinstance(depend, value.annotation)
            ]
            if depend:
                depends.update({key: depend[0]})
        return depends

    async def handle(self, event, bot):
        handle_kwargs = self.check_signature(bot)
        await self.callback(event, bot, **handle_kwargs)


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
