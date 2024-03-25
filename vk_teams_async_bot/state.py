import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Mapping, Protocol, TypeAlias

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

Seconds: TypeAlias = int


@dataclass(slots=True, frozen=True)
class StateData:
    """
    Dataclass for initializing user states,
         control of transitions and transfer of user data between handlers

        Attributes:
            user (str): User id VK Teams (login@@company.ru)
            state (str): Set user state in a specific handler
            data (Mapping | None): A dictionary with data necessary for
            installation or transfer to another handler
            expire_session (Seconds): After what time will the dictionary with data be deleted?
                                       if the user has not performed any action
            additional (Mapping | None): Reserve key for adding any logical flags, etc. to it.

        After initializing the state via DictUserState.set(StateData()),
         can be called repeatedly to add data.
         Previous data stored in keys is not deleted.
    """

    user: str
    state: str | None = None
    data: Mapping | None = None
    expire_session: Seconds = 300
    additional: Mapping | None = None


class UserState(Protocol):
    """
    Abstract class for creating user state chains

    Attributes:
         message_timeout_to_users: Flag to send a message to a user or to
                                   group about the end of the session of its states

         session_timeout_seconds: After what time the user states are checked
         session_timeout_debug: User state logger output
         keyboard_session_end: When message_timeout_to_users is set,
                               a message is sent with the keyboard
                               (for example, going to the main menu)
    """

    message_timeout_to_users: bool = False
    session_timeout_seconds: int = 60
    session_timeout_debug: bool = False
    keyboard_session_end: Callable = lambda a: '[[{"text": "empty", "callbackData": "empty"}]]'

    async def set(self, state_data: StateData):
        raise NotImplementedError

    async def delete_user(self, user: str):
        raise NotImplementedError


class DictUserState(UserState):
    """
    The user's state and data are stored in memory
    """

    _instance = None
    users_states: dict[str, dict[str, Any]] = dict()

    def __init__(self, bot_send_text: Callable):
        self.bot_send_text = bot_send_text

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_user_all_data(self, user: str) -> dict | None:
        return self.users_states.get(user)

    def get_user_data(self, user: str) -> dict | None:
        return self.users_states.get(user, {}).get("data")

    def update_user_data(self, user: str, data: dict) -> None:
        try:
            for key, value in data.items():
                self.users_states[user]["data"][key] = value
            self.set_new_expire_session(user)
        except KeyError as err:
            logger.error(err, exc_info=True)

    def get_user_state(self, user: str) -> str | None:
        return self.users_states.get(user, {}).get("state")

    def update_user_state(self, user: str, state: str) -> None:
        try:
            if self.users_states.get(user):
                self.users_states[user]["state"] = state
                self.set_new_expire_session(user)
        except KeyError as err:
            logger.error(err, exc_info=True)

    def get_user_additional(self, user: str) -> dict | None:
        if self.users_states.get(user):
            return self.users_states["user"].get("additional")
        return None

    def update_user_additional(self, user: str, additional: dict) -> None:
        try:
            if self.users_states.get(user):
                self.users_states["user"]["additional"] = additional
                self.set_new_expire_session(user)
        except KeyError as err:
            logger.error(err, exc_info=True)

    def set_new_expire_session(self, user: str, expire_session: Seconds = 15) -> None:
        try:
            if self.users_states.get(user):
                self.users_states["user"]["expire_session"] = datetime.now() + timedelta(
                    seconds=expire_session
                )
        except KeyError as err:
            logger.error(err, exc_info=True)

    async def set(self, state_data: StateData) -> None:
        if state_data.user not in self.users_states:
            self.users_states[state_data.user] = {
                "expire_session": None,
                "state": None,
                "data": {},
                "additional": {},
            }

        self.users_states[state_data.user][
            "expire_session"
        ] = datetime.now() + timedelta(seconds=state_data.expire_session)

        self.users_states[state_data.user]["state"] = state_data.state

        if state_data.data:
            for key, value in state_data.data.items():
                self.users_states[state_data.user]["data"][key] = value

        if state_data.additional:
            for key, value in state_data.additional.items():
                self.users_states[state_data.user]["additional"][key] = value
        logger.debug(f"set user state - {self.users_states}")

    async def delete_user(self, user: str) -> None:
        if self.users_states.get(user):
            logger.debug(
                f"удаление пользователя {user} - {self.users_states.get(user)} из сессии"
            )
            del self.users_states[user]

    async def session_timeout_handler(self) -> None:
        while True:
            await asyncio.sleep(self.session_timeout_seconds)
            if self.session_timeout_debug:
                logger.debug(f"user_states - {self.users_states}")
            await self._session_timeout_handler()

    async def _session_timeout_handler(self) -> None:
        users: list = list(self.users_states.keys())

        for user in users:
            if datetime.now() > self.users_states[user]["expire_session"]:
                logger.info(f"user session timeout - {user}")
                del self.users_states[user]
                if self.message_timeout_to_users:
                    await self.bot_send_text(
                        chat_id=user,
                        text="the session has expired, you have been transferred to the main menu",
                        inline_keyboard_markup=self.keyboard_session_end(),
                    )
