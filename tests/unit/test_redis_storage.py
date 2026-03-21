"""Tests for RedisStorage backend."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import fakeredis.aioredis
import pytest

from vk_teams_async_bot.fsm.storage.base import StorageKey
from vk_teams_async_bot.fsm.storage.redis import RedisStorage

KEY_A: StorageKey = ("chat_1", "user_1")
KEY_B: StorageKey = ("chat_2", "user_1")  # same user, different chat
KEY_C: StorageKey = ("chat_1", "user_2")  # different user, same chat


@pytest.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    r = fakeredis.aioredis.FakeRedis()
    yield r
    await r.aclose()


@pytest.fixture
async def storage(
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> AsyncIterator[RedisStorage]:
    s = RedisStorage(redis=fake_redis, state_ttl=600)
    yield s


@pytest.fixture
async def storage_no_ttl(
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> AsyncIterator[RedisStorage]:
    s = RedisStorage(redis=fake_redis)
    yield s


class TestRedisStorageState:
    @pytest.mark.asyncio
    async def test_get_state_unknown_key_returns_none(
        self, storage: RedisStorage
    ) -> None:
        result = await storage.get_state(KEY_A)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_state(self, storage: RedisStorage) -> None:
        await storage.set_state(KEY_A, "SomeGroup:step_one")
        result = await storage.get_state(KEY_A)
        assert result == "SomeGroup:step_one"

    @pytest.mark.asyncio
    async def test_set_state_to_none(self, storage: RedisStorage) -> None:
        await storage.set_state(KEY_A, "SomeGroup:step_one")
        await storage.set_state(KEY_A, None)
        result = await storage.get_state(KEY_A)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_state_overwrites(self, storage: RedisStorage) -> None:
        await storage.set_state(KEY_A, "step_one")
        await storage.set_state(KEY_A, "step_two")
        assert await storage.get_state(KEY_A) == "step_two"


class TestRedisStorageData:
    @pytest.mark.asyncio
    async def test_get_data_unknown_key_returns_empty_dict(
        self, storage: RedisStorage
    ) -> None:
        result = await storage.get_data(KEY_A)
        assert result == {}

    @pytest.mark.asyncio
    async def test_set_and_get_data(self, storage: RedisStorage) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        result = await storage.get_data(KEY_A)
        assert result == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_get_data_returns_independent_copy(
        self, storage: RedisStorage
    ) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        data = await storage.get_data(KEY_A)
        data["name"] = "Bob"
        assert (await storage.get_data(KEY_A))["name"] == "Alice"


class TestRedisStorageUpdateData:
    @pytest.mark.asyncio
    async def test_update_data_on_empty(self, storage: RedisStorage) -> None:
        result = await storage.update_data(KEY_A, data={"name": "Alice"})
        assert result == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_update_data_merges(self, storage: RedisStorage) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        result = await storage.update_data(KEY_A, data={"phone": "123"})
        assert result == {"name": "Alice", "phone": "123"}

    @pytest.mark.asyncio
    async def test_update_data_overwrites_key(
        self, storage: RedisStorage
    ) -> None:
        await storage.set_data(KEY_A, {"name": "Alice"})
        result = await storage.update_data(KEY_A, data={"name": "Bob"})
        assert result == {"name": "Bob"}

    @pytest.mark.asyncio
    async def test_update_data_returns_independent_copy(
        self, storage: RedisStorage
    ) -> None:
        result = await storage.update_data(KEY_A, data={"x": 1})
        result["x"] = 999
        assert (await storage.get_data(KEY_A))["x"] == 1


class TestRedisStorageClear:
    @pytest.mark.asyncio
    async def test_clear_removes_state_and_data(
        self, storage: RedisStorage
    ) -> None:
        await storage.set_state(KEY_A, "active")
        await storage.set_data(KEY_A, {"foo": "bar"})
        await storage.clear(KEY_A)
        assert await storage.get_state(KEY_A) is None
        assert await storage.get_data(KEY_A) == {}

    @pytest.mark.asyncio
    async def test_clear_unknown_key_is_noop(
        self, storage: RedisStorage
    ) -> None:
        await storage.clear(("nonexistent", "key"))


class TestRedisStorageIsolation:
    """Same user in different chats must have independent state."""

    @pytest.mark.asyncio
    async def test_same_user_different_chats(
        self, storage: RedisStorage
    ) -> None:
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
        self, storage: RedisStorage
    ) -> None:
        await storage.set_state(KEY_A, "active")
        await storage.set_state(KEY_B, "active")
        await storage.clear(KEY_A)
        assert await storage.get_state(KEY_A) is None
        assert await storage.get_state(KEY_B) == "active"

    @pytest.mark.asyncio
    async def test_different_users_same_chat(
        self, storage: RedisStorage
    ) -> None:
        await storage.set_state(KEY_A, "user1_state")
        await storage.set_state(KEY_C, "user2_state")
        assert await storage.get_state(KEY_A) == "user1_state"
        assert await storage.get_state(KEY_C) == "user2_state"


class TestRedisStorageTTL:
    @pytest.mark.asyncio
    async def test_ttl_set_on_write(
        self,
        storage: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage.set_state(KEY_A, "active")
        rk = storage._make_key(KEY_A)
        ttl = await fake_redis.ttl(rk)
        assert 0 < ttl <= 600

    @pytest.mark.asyncio
    async def test_ttl_refreshed_on_read(
        self,
        storage: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage.set_state(KEY_A, "active")
        rk = storage._make_key(KEY_A)
        # Artificially reduce TTL
        await fake_redis.expire(rk, 100)
        assert await fake_redis.ttl(rk) <= 100
        # Read should refresh TTL back to 600
        await storage.get_state(KEY_A)
        ttl = await fake_redis.ttl(rk)
        assert ttl > 100

    @pytest.mark.asyncio
    async def test_ttl_refreshed_on_get_data(
        self,
        storage: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage.set_data(KEY_A, {"x": 1})
        rk = storage._make_key(KEY_A)
        await fake_redis.expire(rk, 50)
        await storage.get_data(KEY_A)
        ttl = await fake_redis.ttl(rk)
        assert ttl > 50

    @pytest.mark.asyncio
    async def test_no_ttl_when_disabled(
        self,
        storage_no_ttl: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage_no_ttl.set_state(KEY_A, "active")
        rk = storage_no_ttl._make_key(KEY_A)
        ttl = await fake_redis.ttl(rk)
        assert ttl == -1  # -1 means no TTL set

    @pytest.mark.asyncio
    async def test_ttl_set_on_set_data(
        self,
        storage: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage.set_data(KEY_A, {"name": "test"})
        rk = storage._make_key(KEY_A)
        ttl = await fake_redis.ttl(rk)
        assert 0 < ttl <= 600

    @pytest.mark.asyncio
    async def test_ttl_set_on_update_data(
        self,
        storage: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage.update_data(KEY_A, data={"x": 1})
        rk = storage._make_key(KEY_A)
        ttl = await fake_redis.ttl(rk)
        assert 0 < ttl <= 600


class TestRedisStorageConnection:
    def test_requires_redis_or_url(self) -> None:
        with pytest.raises(ValueError, match="either"):
            RedisStorage()

    def test_rejects_both_redis_and_url(self) -> None:
        r = fakeredis.aioredis.FakeRedis()
        with pytest.raises(ValueError, match="not both"):
            RedisStorage(redis=r, redis_url="redis://localhost")

    @pytest.mark.asyncio
    async def test_close_does_not_close_external_redis(
        self,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        s = RedisStorage(redis=fake_redis)
        await s.close()
        # External redis should still be usable
        await fake_redis.ping()

    @pytest.mark.asyncio
    async def test_owns_connection_from_url(self) -> None:
        s = RedisStorage(redis_url="redis://localhost")
        assert s._owns_connection is True
        # Clean up without actually connecting
        s._redis = fakeredis.aioredis.FakeRedis()
        await s.close()

    @pytest.mark.asyncio
    async def test_does_not_own_external_connection(
        self,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        s = RedisStorage(redis=fake_redis)
        assert s._owns_connection is False


class TestRedisStorageKeyPrefix:
    @pytest.mark.asyncio
    async def test_default_prefix(
        self,
        storage: RedisStorage,
        fake_redis: fakeredis.aioredis.FakeRedis,
    ) -> None:
        await storage.set_state(KEY_A, "active")
        keys = [k.decode() for k in await fake_redis.keys("*")]
        assert keys == ["vkbot:chat_1:user_1"]

    @pytest.mark.asyncio
    async def test_custom_prefix(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        s = RedisStorage(redis=fake_redis, key_prefix="mybot")
        await s.set_state(KEY_A, "active")
        keys = [k.decode() for k in await fake_redis.keys("*")]
        assert keys == ["mybot:chat_1:user_1"]


class TestRedisStorageSerialization:
    @pytest.mark.asyncio
    async def test_nested_dict_survives_roundtrip(
        self, storage: RedisStorage
    ) -> None:
        data = {"user": {"name": "Alice", "settings": {"theme": "dark"}}}
        await storage.set_data(KEY_A, data)
        result = await storage.get_data(KEY_A)
        assert result == data

    @pytest.mark.asyncio
    async def test_list_values_survive_roundtrip(
        self, storage: RedisStorage
    ) -> None:
        data = {"tags": ["python", "bot", "async"]}
        await storage.set_data(KEY_A, data)
        result = await storage.get_data(KEY_A)
        assert result == data

    @pytest.mark.asyncio
    async def test_unicode_survives_roundtrip(
        self, storage: RedisStorage
    ) -> None:
        data = {"name": "Tester McTestface"}
        await storage.set_data(KEY_A, data)
        result = await storage.get_data(KEY_A)
        assert result == data

    @pytest.mark.asyncio
    async def test_numeric_values_survive_roundtrip(
        self, storage: RedisStorage
    ) -> None:
        data = {"count": 42, "ratio": 3.14, "flag": True, "empty": None}
        await storage.set_data(KEY_A, data)
        result = await storage.get_data(KEY_A)
        assert result == data


class TestRedisStorageConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_updates_different_keys(
        self, storage: RedisStorage
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
