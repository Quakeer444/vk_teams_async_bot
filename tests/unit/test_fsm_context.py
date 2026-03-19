"""Tests for FSMContext -- per-user facade over storage."""

import pytest

from vk_teams_async_bot.fsm.context import FSMContext
from vk_teams_async_bot.fsm.state import State, StatesGroup
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage


class OrderForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


KEY = ("chat_1", "user_1")


@pytest.fixture
def storage() -> MemoryStorage:
    return MemoryStorage()


@pytest.fixture
def ctx(storage: MemoryStorage) -> FSMContext:
    return FSMContext(storage=storage, key=KEY)


class TestFSMContextSetState:
    @pytest.mark.asyncio
    async def test_set_state_with_state_object(self, ctx: FSMContext) -> None:
        await ctx.set_state(OrderForm.waiting_for_name)
        result = await ctx.get_state()
        assert result == "OrderForm:waiting_for_name"

    @pytest.mark.asyncio
    async def test_set_state_with_string(self, ctx: FSMContext) -> None:
        await ctx.set_state("custom:state")
        result = await ctx.get_state()
        assert result == "custom:state"

    @pytest.mark.asyncio
    async def test_set_state_with_none_clears(self, ctx: FSMContext) -> None:
        await ctx.set_state(OrderForm.waiting_for_name)
        await ctx.set_state(None)
        result = await ctx.get_state()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_state_initially_none(self, ctx: FSMContext) -> None:
        assert await ctx.get_state() is None


class TestFSMContextData:
    @pytest.mark.asyncio
    async def test_set_and_get_data(self, ctx: FSMContext) -> None:
        await ctx.set_data({"name": "Alice"})
        result = await ctx.get_data()
        assert result == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_get_data_returns_copy(self, ctx: FSMContext) -> None:
        await ctx.set_data({"name": "Alice"})
        data = await ctx.get_data()
        data["name"] = "Bob"
        assert (await ctx.get_data())["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_update_data_merges(self, ctx: FSMContext) -> None:
        await ctx.set_data({"name": "Alice"})
        result = await ctx.update_data(phone="123", age=30)
        assert result == {"name": "Alice", "phone": "123", "age": 30}

    @pytest.mark.asyncio
    async def test_update_data_on_empty(self, ctx: FSMContext) -> None:
        result = await ctx.update_data(key="value")
        assert result == {"key": "value"}


class TestFSMContextClear:
    @pytest.mark.asyncio
    async def test_clear_resets_state_and_data(self, ctx: FSMContext) -> None:
        await ctx.set_state(OrderForm.waiting_for_phone)
        await ctx.set_data({"phone": "555"})
        await ctx.clear()
        assert await ctx.get_state() is None
        assert await ctx.get_data() == {}

    @pytest.mark.asyncio
    async def test_clear_on_fresh_context(self, ctx: FSMContext) -> None:
        # Should not raise
        await ctx.clear()
        assert await ctx.get_state() is None
        assert await ctx.get_data() == {}


class TestFSMContextIsolation:
    """Two FSMContext instances on the same storage but different keys."""

    @pytest.mark.asyncio
    async def test_independent_contexts(self, storage: MemoryStorage) -> None:
        ctx_a = FSMContext(storage=storage, key=("chat_1", "user_1"))
        ctx_b = FSMContext(storage=storage, key=("chat_2", "user_1"))

        await ctx_a.set_state(OrderForm.waiting_for_name)
        await ctx_b.set_state(OrderForm.waiting_for_phone)

        assert await ctx_a.get_state() == "OrderForm:waiting_for_name"
        assert await ctx_b.get_state() == "OrderForm:waiting_for_phone"
