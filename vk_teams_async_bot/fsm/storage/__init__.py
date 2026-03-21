"""FSM storage backends."""

from .base import BaseStorage, StorageKey
from .memory import MemoryStorage

__all__ = [
    "BaseStorage",
    "MemoryStorage",
    "StorageKey",
]

try:
    from .redis import RedisStorage

    __all__ = [*__all__, "RedisStorage"]
except ImportError:
    pass
