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
    Датакласс для инициализации состояний пользователей,
    контроля переходов и передачей данных пользователя между обработчиками

    Attributes:
        user (str): ID пользователя VK Teams (login@@company.ru)
        state (str): Установить состояние пользователя в определенном обработчике
        data (Mapping | None): Словарь с данными, необходимые для установки или передаче в др. обработчик
        expire_session (Seconds): Через какое время удалится словарь с данными,
                                  если пользователь не произвел никаких действий
        additional (Mapping | None): Резервный ключ для добавления в него любых логических флагов и т.п.

    После инициализации состояния через DictUserState.set(StateData()),
    можно вызывать повторно для добавления данных.
    Предыдущие данные, хранимые в ключах не удаляются.
    """

    user: str
    state: str | None = None
    data: Mapping | None = None
    expire_session: Seconds = 300
    additional: Mapping | None = None


class UserState(Protocol):
    """
    Абстрактный класс для создания цепочек состояний пользователей

    Attributes:
        message_timeout_to_users: Флаг отправки сообщения пользователю или в
                                  группу о завершение сессии его состояний

        session_timeout_seconds: Через какое время происходит проверка состояний пользователя
        session_timeout_debug: Вывод logger состояния пользователей
        keyboard_session_end: При установленном message_timeout_to_users,
                              отправляется сообщение с клавиатурой
                              (например переход в главное меню)

    """

    message_timeout_to_users = False
    session_timeout_seconds = 60
    session_timeout_debug = False
    keyboard_session_end = lambda a: '[[{"text": "empty", "callbackData": "empty"}]]'

    async def set(self, state_data: StateData):
        raise NotImplementedError

    async def delete_user(self, user: str):
        raise NotImplementedError


class DictUserState(UserState):
    """
    Состояние пользователя и его данные хранятся в памяти
    """

    _instance = None
    users_states: dict[str, dict[str, Any]] = dict()

    def __init__(self, bot_send_text: Callable):
        self.bot_send_text = bot_send_text

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_user_all_data(self, user: str) -> dict:
        return self.users_states.get(user)

    def get_user_data(self, user: str) -> dict:
        return self.users_states.get(user, {}).get("data")

    def update_user_data(self, user: str, data: dict) -> None:
        try:
            for key, value in data.items():
                self.users_states[user]["data"][key] = value
            self.set_new_expire_session(user)
        except KeyError as err:
            logger.error(err, exc_info=True)

    def get_user_state(self, user: str) -> str:
        return self.users_states.get(user, {}).get("state")

    def update_user_state(self, user: str, state: str) -> None:
        try:
            self.users_states.get(user)["state"] = state
            self.set_new_expire_session(user)
        except KeyError as err:
            logger.error(err, exc_info=True)

    def get_user_additional(self, user: str) -> dict:
        return self.users_states.get(user).get("additional")

    def update_user_additional(self, user: str, additional: dict) -> None:
        try:
            self.users_states.get(user)["additional"] = additional
            self.set_new_expire_session(user)
        except KeyError as err:
            logger.error(err, exc_info=True)

    def set_new_expire_session(self, user: str, expire_session: Seconds = 15) -> None:
        try:
            self.users_states.get(user)["expire_session"] = datetime.now() + timedelta(
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
