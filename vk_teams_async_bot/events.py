from enum import Enum, unique
from types import MappingProxyType
from typing import Dict, List, Optional


@unique
class EventType(Enum):
    __slots__ = ()

    NEW_MESSAGE = "newMessage"
    EDITED_MESSAGE = "editedMessage"
    DELETED_MESSAGE = "deletedMessage"
    PINNED_MESSAGE = "pinnedMessage"
    UNPINNED_MESSAGE = "unpinnedMessage"
    NEW_CHAT_MEMBERS = "newChatMembers"
    LEFT_CHAT_MEMBERS = "leftChatMembers"
    CHANGED_CHAT_INFO = "changedChatInfo"
    CALLBACK_QUERY = "callbackQuery"


class ChatInfo(object):
    __slots__ = ("chatId", "type", "title")

    def __init__(self, chatId: str, type: str, title: Optional[str] = None):
        self.chatId: str = chatId
        self.type: str = type
        self.title = title

    def __repr__(self):
        return "{self.get_title}({self.chatId})".format(self=self)


class UserInfo(object):
    __slots__ = ("userId", "firstName", "lastName", "nick")

    def __init__(
        self,
        userId: str,
        firstName: Optional[str] = None,
        lastName: Optional[str] = None,
        nick: Optional[str] = None,
    ):
        self.userId = userId
        self.firstName = firstName
        self.lastName = lastName
        self.nick = nick

    def __repr__(self):
        return "{self.firstName} {self.lastName}({self.userId})".format(self=self)


class Event(object):
    bot = None

    def __init__(self, type_: EventType, data: dict):
        self.type = type_
        self.data = MappingProxyType(data)
        self.text: str | None = data.get("text")
        self.middleware_data: dict = {}

        if type_ != EventType.CALLBACK_QUERY:
            self.chat: ChatInfo = ChatInfo(**data["chat"])

        if type_ == EventType.CALLBACK_QUERY:
            self.chat: ChatInfo = ChatInfo(**data["message"]["chat"])

        if type_ in [
            EventType.NEW_MESSAGE,
            EventType.EDITED_MESSAGE,
            EventType.PINNED_MESSAGE,
        ]:
            if data.get("from"):
                self.from_: UserInfo = UserInfo(**data["from"])

            self._format: Dict[str, List[Dict[str, int]]] = data.get("format")
            self.timestamp: int = data.get("timestamp")
            self.msgId: str = data.get("msgId")

        elif type_ in [EventType.DELETED_MESSAGE, EventType.UNPINNED_MESSAGE]:
            self.timestamp: int = data.get("timestamp")
            self.msgId: str = data.get("msgId")

        elif type_ in [EventType.NEW_CHAT_MEMBERS, EventType.LEFT_CHAT_MEMBERS]:
            self.newMembers = [UserInfo(**user) for user in data.get("newMembers", [])]
            if data.get("addedBy"):
                self.addedBy = UserInfo(**data["addedBy"])

        else:
            self.queryId = data["queryId"]
            self.from_ = UserInfo(**data["from"])
            self.cb_message = Event(EventType.NEW_MESSAGE, data["message"])
            self.callbackData = data["callbackData"]

    def __repr__(self):
        return (
            "Event(type='{self.type}', data='{self.data}', "
            "middleware_data='{self.middleware_data}')"
        ).format(self=self)
