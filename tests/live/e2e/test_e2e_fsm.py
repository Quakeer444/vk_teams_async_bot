"""E2E FSM tests: multi-step state transitions with real Bot API calls."""

from __future__ import annotations

import pytest

from tests.helpers import make_new_message_event
from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.filters.state import StateFilter, StatesGroupFilter
from vk_teams_async_bot.fsm import FSMContext, MemoryStorage, State, StatesGroup

pytestmark = pytest.mark.live


async def test_fsm_state_transitions(bot, test_user_id):
    """Multi-step FSM flow: each state transition triggers a real API call."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    steps: list[str] = []

    class Form(StatesGroup):
        name = State()
        confirm = State()

    @dp.message(StateFilter(None, storage=storage))
    async def start_form(event, b, fsm_context):
        await fsm_context.set_state(Form.name)
        await b.send_text(chat_id=test_user_id, text="E2E FSM: enter name")
        steps.append("started")

    @dp.message(StateFilter(Form.name, storage=storage))
    async def got_name(event, b, fsm_context):
        await fsm_context.update_data(name=event.text)
        await fsm_context.set_state(Form.confirm)
        await b.send_text(chat_id=test_user_id, text=f"E2E FSM: confirm {event.text}?")
        steps.append("got_name")

    e1 = make_new_message_event(text="hello", chat_id=test_user_id, user_id="user1")
    await dp.feed_event(e1, bot)

    e2 = make_new_message_event(
        text="Alice", event_id=2, chat_id=test_user_id, user_id="user1"
    )
    await dp.feed_event(e2, bot)

    assert steps == ["started", "got_name"]
    ctx = FSMContext(storage=storage, key=(test_user_id, "user1"))
    assert await ctx.get_state() == Form.confirm.state
    assert (await ctx.get_data())["name"] == "Alice"


async def test_fsm_data_persistence(bot, test_user_id):
    """update_data in handler persists and can be read back."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    class Steps(StatesGroup):
        collecting = State()

    @dp.message(StateFilter(None, storage=storage))
    async def init(event, b, fsm_context):
        await fsm_context.set_state(Steps.collecting)
        await fsm_context.update_data(count=0)

    @dp.message(StateFilter(Steps.collecting, storage=storage))
    async def collect(event, b, fsm_context):
        data = await fsm_context.get_data()
        await fsm_context.update_data(count=data.get("count", 0) + 1)

    user_key = (test_user_id, "user_persist")

    e1 = make_new_message_event(
        text="init", chat_id=test_user_id, user_id="user_persist"
    )
    await dp.feed_event(e1, bot)

    e2 = make_new_message_event(
        text="item1", event_id=2, chat_id=test_user_id, user_id="user_persist"
    )
    await dp.feed_event(e2, bot)

    e3 = make_new_message_event(
        text="item2", event_id=3, chat_id=test_user_id, user_id="user_persist"
    )
    await dp.feed_event(e3, bot)

    ctx = FSMContext(storage=storage, key=user_key)
    data = await ctx.get_data()
    assert data["count"] == 2


async def test_fsm_clear_resets(bot, test_user_id):
    """clear() via handler resets state to None and data to {}."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    class Flow(StatesGroup):
        active = State()

    @dp.message(StateFilter(None, storage=storage))
    async def start(event, b, fsm_context):
        await fsm_context.set_state(Flow.active)
        await fsm_context.update_data(value="test")

    @dp.message(StateFilter(Flow.active, storage=storage))
    async def reset(event, b, fsm_context):
        await fsm_context.clear()

    user_key = (test_user_id, "user_clear")

    e1 = make_new_message_event(
        text="start", chat_id=test_user_id, user_id="user_clear"
    )
    await dp.feed_event(e1, bot)

    ctx = FSMContext(storage=storage, key=user_key)
    assert await ctx.get_state() == Flow.active.state

    e2 = make_new_message_event(
        text="reset", event_id=2, chat_id=test_user_id, user_id="user_clear"
    )
    await dp.feed_event(e2, bot)

    assert await ctx.get_state() is None
    assert await ctx.get_data() == {}


async def test_state_filter_routing(bot, test_user_id):
    """StateFilter routes to the correct handler based on current FSM state."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    routed: list[str] = []

    class States(StatesGroup):
        waiting = State()

    @dp.message(StateFilter(None, storage=storage))
    async def no_state_handler(event, b, fsm_context):
        await fsm_context.set_state(States.waiting)
        routed.append("no_state")

    @dp.message(StateFilter(States.waiting, storage=storage))
    async def waiting_handler(event, b, fsm_context):
        routed.append("waiting")

    user_id = "user_routing"

    e1 = make_new_message_event(text="first", chat_id=test_user_id, user_id=user_id)
    await dp.feed_event(e1, bot)

    e2 = make_new_message_event(
        text="second", event_id=2, chat_id=test_user_id, user_id=user_id
    )
    await dp.feed_event(e2, bot)

    assert routed == ["no_state", "waiting"]


async def test_states_group_filter(bot, test_user_id):
    """StatesGroupFilter catches any state within the group."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    caught: list[str] = []

    class Wizard(StatesGroup):
        step1 = State()
        step2 = State()
        step3 = State()

    @dp.message(StateFilter(None, storage=storage))
    async def init(event, b, fsm_context):
        await fsm_context.set_state(Wizard.step1)

    @dp.message(StatesGroupFilter(Wizard, storage=storage))
    async def any_wizard_step(event, b, fsm_context):
        caught.append(event.text)
        data = await fsm_context.get_data()
        step_num = data.get("step", 1)
        states = [Wizard.step1, Wizard.step2, Wizard.step3]
        next_idx = step_num
        if next_idx < len(states):
            await fsm_context.set_state(states[next_idx])
            await fsm_context.update_data(step=step_num + 1)

    user_id = "user_group_filter"

    e0 = make_new_message_event(text="init", chat_id=test_user_id, user_id=user_id)
    await dp.feed_event(e0, bot)

    for i, text in enumerate(["a", "b", "c"], start=1):
        ev = make_new_message_event(
            text=text, event_id=i + 1, chat_id=test_user_id, user_id=user_id
        )
        await dp.feed_event(ev, bot)

    assert caught == ["a", "b", "c"]
