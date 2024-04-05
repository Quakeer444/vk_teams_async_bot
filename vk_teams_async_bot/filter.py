import re
from abc import abstractmethod

from .constants import Parts
from .events import Event, EventType


class FilterBase(object):
    def __init__(self):
        super(FilterBase, self).__init__()

    def __call__(self, event: Event):
        return self.filter(event)

    @abstractmethod
    def filter(self, event: Event):
        pass


class CompositeFilter(FilterBase):
    def __init__(self, filter_1, filter_2):
        super(CompositeFilter, self).__init__()
        self.filter_1 = filter_1
        self.filter_2 = filter_2


class AndFilter(CompositeFilter):
    def filter(self, event):
        return self.filter_1(event) and self.filter_2(event)


class MessageFilter(FilterBase):
    def filter(self, event: Event):
        return bool(event.type == EventType.NEW_MESSAGE)


class FileFilter(MessageFilter):
    def filter(self, event):
        return (
            super(FileFilter, self).filter(event)
            and "parts" in event.data
            and any(p["type"] == Parts.FILE.value for p in event.data["parts"])
        )


class CallbackDataFilter(FilterBase):
    def __init__(self, callback_data):
        super(CallbackDataFilter, self).__init__()
        self.callback_data = callback_data

    def filter(self, event: Event):
        return (
            EventType.CALLBACK_QUERY is event.type
            and event.callbackData == self.callback_data
        )


class CallbackDataRegexpFilter(FilterBase):
    def __init__(self, pattern):
        super(CallbackDataRegexpFilter, self).__init__()

        self.pattern = re.compile(pattern)

    def filter(self, event):
        return EventType.CALLBACK_QUERY is event.type and self.pattern.search(
            event.callbackData
        )


class CommandFilter(MessageFilter):
    COMMAND_PREFIXES = "/"

    def __init__(self, command):
        super(CommandFilter, self).__init__()
        self.command = command

    def filter(self, event):
        return (
            super(CommandFilter, self).filter(event)
            and any(
                event.data.get("text", "").strip().startswith(p)
                for p in CommandFilter.COMMAND_PREFIXES
            )
            and event.text == self.command
        )


class StateUserFilter(MessageFilter):
    def __init__(self, user_state, now_user_state):
        super(StateUserFilter, self).__init__()
        self.user_state = user_state
        self.now_user_state = now_user_state

    def filter(self, event):
        return super().filter(event) and self.user_state == self.now_user_state.get(
            event.data["chat"]["chatId"], {}
        ).get("state", None)


class StateUserRegexFilter(MessageFilter):
    def __init__(self, user_state, now_user_state):
        super(StateUserRegexFilter, self).__init__()
        self.user_state = user_state
        self.now_user_state = now_user_state

    def filter(self, event):
        return super().filter(event) and self.user_state in self.now_user_state.get(
            event.data["message"]["chat"]["chatId"], {}
        ).get("state", {})


class ReplyFilter(MessageFilter):
    def filter(self, event):
        return (
            super(ReplyFilter, self).filter(event)
            and "parts" in event.data
            and any(p["type"] == Parts.REPLY.value for p in event.data["parts"])
        )


class RegexpFilter(MessageFilter):
    def __init__(self, pattern):
        super(RegexpFilter, self).__init__()

        self.pattern = re.compile(pattern)

    def filter(self, event):
        return super(RegexpFilter, self).filter(event) and self.pattern.search(
            event.data.get("text", "").strip()
        )


class ForwardFilter(MessageFilter):
    def filter(self, event):
        return (
            'parts' in event.data and
            any(p['type'] == Parts.FORWARD.value for p in event.data['parts'])
        )


class TagFilter(MessageFilter):
    def __init__(self, tags: list):
        super(MessageFilter, self).__init__()
        self.tags = tags

    def filter(self, event):
        return super(TagFilter, self).filter(event) and event.text in self.tags


class Filter(object):
    messagetext = MessageFilter
    regexp = RegexpFilter
    callback_data = CallbackDataFilter
    callback_data_regexp = CallbackDataRegexpFilter
    file = FileFilter()
    command = CommandFilter
    state = StateUserFilter
    state_regex = StateUserRegexFilter
    reply = ReplyFilter()
    tag = TagFilter
