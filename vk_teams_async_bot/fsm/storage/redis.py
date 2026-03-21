"""Redis storage backend for FSM."""

from __future__ import annotations

import json
from typing import Any

try:
    from redis.asyncio import Redis
except ImportError as exc:
    raise ImportError(
        "RedisStorage requires the 'redis' package. "
        "Install it with: pip install vk-teams-async-bot[redis]"
    ) from exc

from .base import BaseStorage, StorageKey


class RedisStorage(BaseStorage):
    """Redis-backed storage implementation.

    Stores FSM state and data in Redis hashes keyed by
    ``{key_prefix}:{chat_id}:{user_id}``.  Supports optional TTL
    with sliding-window refresh on every operation.

    Suitable for production and multi-process deployments.
    """

    def __init__(
        self,
        redis: Redis | None = None,  # type: ignore[type-arg]
        redis_url: str | None = None,
        key_prefix: str = "vkbot",
        state_ttl: int | None = None,
    ) -> None:
        if redis is not None and redis_url is not None:
            raise ValueError("Provide either 'redis' or 'redis_url', not both.")
        if redis is None and redis_url is None:
            raise ValueError("Provide either 'redis' instance or 'redis_url'.")

        if redis_url is not None:
            self._redis: Redis = Redis.from_url(redis_url)  # type: ignore[type-arg]
            self._owns_connection = True
        else:
            self._redis = redis  # type: ignore[assignment]
            self._owns_connection = False

        self._key_prefix = key_prefix
        self._state_ttl = state_ttl

    def _make_key(self, key: StorageKey) -> str:
        chat_id, user_id = key
        return f"{self._key_prefix}:{chat_id}:{user_id}"

    async def _refresh_ttl(self, pipe: Any, redis_key: str) -> None:
        if self._state_ttl is not None:
            pipe.expire(redis_key, self._state_ttl)

    async def get_state(self, key: StorageKey) -> str | None:
        rk = self._make_key(key)
        pipe = self._redis.pipeline()
        pipe.hget(rk, "state")
        await self._refresh_ttl(pipe, rk)
        results = await pipe.execute()
        raw = results[0]
        if raw is None:
            return None
        return raw.decode() if isinstance(raw, bytes) else str(raw)

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        rk = self._make_key(key)
        if state is None:
            await self._redis.hdel(rk, "state")  # type: ignore[misc]
        else:
            pipe = self._redis.pipeline()
            pipe.hset(rk, "state", state)
            await self._refresh_ttl(pipe, rk)
            await pipe.execute()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        rk = self._make_key(key)
        pipe = self._redis.pipeline()
        pipe.hget(rk, "data")
        await self._refresh_ttl(pipe, rk)
        results = await pipe.execute()
        raw = results[0]
        if raw is None:
            return {}
        raw_str = raw.decode() if isinstance(raw, bytes) else str(raw)
        return json.loads(raw_str)  # type: ignore[no-any-return]

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        rk = self._make_key(key)
        pipe = self._redis.pipeline()
        pipe.hset(rk, "data", json.dumps(data, ensure_ascii=False))
        await self._refresh_ttl(pipe, rk)
        await pipe.execute()

    async def update_data(
        self, key: StorageKey, data: dict[str, Any]
    ) -> dict[str, Any]:
        rk = self._make_key(key)
        raw = await self._redis.hget(rk, "data")  # type: ignore[misc]
        if raw is None:
            current: dict[str, Any] = {}
        else:
            raw_str = raw.decode() if isinstance(raw, bytes) else str(raw)
            current = json.loads(raw_str)
        updated = {**current, **data}
        pipe = self._redis.pipeline()
        pipe.hset(rk, "data", json.dumps(updated, ensure_ascii=False))
        await self._refresh_ttl(pipe, rk)
        await pipe.execute()
        return updated

    async def clear(self, key: StorageKey) -> None:
        rk = self._make_key(key)
        await self._redis.delete(rk)

    async def close(self) -> None:
        if self._owns_connection:
            await self._redis.aclose()
