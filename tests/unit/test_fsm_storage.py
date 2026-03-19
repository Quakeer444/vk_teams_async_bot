"""Tests for FSM storage backends."""

import asyncio

import pytest

from vk_teams_async_bot.fsm.storage.base import StorageKey
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage

KEY_A: StorageKey = ("chat_1", "user_1")
KEY_B: StorageKey = ("chat_2", "user_1")  # same user, different chat
KEY_C: StorageKey = ("chat_1", "user_2")  # different user, same chat


@pytest.fixture
def storage() -> MemoryStorage:
    return MemoryStorage()


class TestMemoryStorageState:
    @pytest.mark.asyncio
    async def test_get_state_unknown_key_returns_none(
        self, storage: MemoryStorage
    ) -> None:
        result = await storage.get_state(KEY_A)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_state(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "SomeGroup:step_one")
        result = await storage.get_state(KEY_A)
        assert result == "SomeGroup:step_one"

    @pytest.mark.asyncio
    async def test_set_state_to_none(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "SomeGroup:step_one")
        await storage.set_state(KEY_A, None)
        result = await storage.get_state(KEY_A)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_state_overwrites(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "step_one")
        await storage.set_state(KEY_A, "step_two")
        assert await storage.get_state(KEY_A) == "step_two"


class TestMemoryStorageData:
    @pytest.mark.asyncio
    async def test_get_data_unknown_key_returns_empty_dict(
        self, storage: MemoryStorage
    ) -> None:
        result = await storage.get_data(KEY_A)
        assert result == {}

    @pytest.mark.asyncio
    async def test_set_and_get_data(self, storage: MemoryStorage) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        result = await storage.get_data(KEY_A)
        assert result == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_get_data_returns_copy(self, storage: MemoryStorage) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        data = await storage.get_data(KEY_A)
        data["name"] = "Bob"
        # Original must be unchanged
        assert (await storage.get_data(KEY_A))["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_set_data_stores_copy(self, storage: MemoryStorage) -> None:
        original = {"key": "value"}
        await storage.set_data(KEY_A, original)
        original["key"] = "mutated"
        assert (await storage.get_data(KEY_A))["key"] == "value"


class TestMemoryStorageUpdateData:
    @pytest.mark.asyncio
    async def test_update_data_on_empty(self, storage: MemoryStorage) -> None:
        result = await storage.update_data(KEY_A, data={"name": "Alice"})
        assert result == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_update_data_merges(self, storage: MemoryStorage) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        result = await storage.update_data(KEY_A, data={"phone": "123"})
        assert result == {"name": "Alice", "phone": "123"}

    @pytest.mark.asyncio
    async def test_update_data_overwrites_key(self, storage: MemoryStorage) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        result = await storage.update_data(KEY_A, data={"name": "Bob"})
        assert result == {"name": "Bob"}

    @pytest.mark.asyncio
    async def test_update_data_returns_copy(self, storage: MemoryStorage) -> None:
        result = await storage.update_data(KEY_A, data={"x": 1})
        result["x"] = 999
        assert (await storage.get_data(KEY_A))["x"] == 1


class TestMemoryStorageClear:
    @pytest.mark.asyncio
    async def test_clear_removes_state_and_data(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "active")
        await storage.set_data(KEY_A, {"foo": "bar"})
        await storage.clear(KEY_A)
        assert await storage.get_state(KEY_A) is None
        assert await storage.get_data(KEY_A) == {}

    @pytest.mark.asyncio
    async def test_clear_unknown_key_is_noop(self, storage: MemoryStorage) -> None:
        # Should not raise
        await storage.clear(("nonexistent", "key"))


class TestMemoryStorageIsolation:
    """Same user in different chats must have independent state."""

    @pytest.mark.asyncio
    async def test_same_user_different_chats(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "state_in_chat_1")
        await storage.set_state(KEY_B, "state_in_chat_2")
        await storage.set_data(KEY_A, {"from": "chat_1"})
        await storage.set_data(KEY_B, {"from": "chat_2"})

        assert await storage.get_state(KEY_A) == "state_in_chat_1"
        assert await storage.get_state(KEY_B) == "state_in_chat_2"
        assert (await storage.get_data(KEY_A))["from"] == "chat_1"
        assert (await storage.get_data(KEY_B))["from"] == "chat_2"

    @pytest.mark.asyncio
    async def test_clear_one_chat_does_not_affect_another(
        self, storage: MemoryStorage
    ) -> None:
        await storage.set_state(KEY_A, "active")
        await storage.set_state(KEY_B, "active")
        await storage.clear(KEY_A)
        assert await storage.get_state(KEY_A) is None
        assert await storage.get_state(KEY_B) == "active"

    @pytest.mark.asyncio
    async def test_different_users_same_chat(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "user1_state")
        await storage.set_state(KEY_C, "user2_state")
        assert await storage.get_state(KEY_A) == "user1_state"
        assert await storage.get_state(KEY_C) == "user2_state"


class TestMemoryStorageConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_updates_different_keys(
        self, storage: MemoryStorage
    ) -> None:
        async def update_key(key: StorageKey, value: str) -> None:
            await storage.set_state(key, value)
            await storage.set_data(key, {"value": value})

        await asyncio.gather(
            update_key(KEY_A, "val_a"),
            update_key(KEY_B, "val_b"),
            update_key(KEY_C, "val_c"),
        )

        assert await storage.get_state(KEY_A) == "val_a"
        assert await storage.get_state(KEY_B) == "val_b"
        assert await storage.get_state(KEY_C) == "val_c"
        assert (await storage.get_data(KEY_A))["value"] == "val_a"
        assert (await storage.get_data(KEY_B))["value"] == "val_b"
        assert (await storage.get_data(KEY_C))["value"] == "val_c"


class TestMemoryStorageClose:
    @pytest.mark.asyncio
    async def test_close_clears_everything(self, storage: MemoryStorage) -> None:
        await storage.set_state(KEY_A, "active")
        await storage.set_data(KEY_A, {"x": 1})
        await storage.close()
        assert await storage.get_state(KEY_A) is None
        assert await storage.get_data(KEY_A) == {}
