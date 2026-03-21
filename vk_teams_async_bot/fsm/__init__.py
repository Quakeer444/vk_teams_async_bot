"""Finite State Machine (FSM) for managing conversational state."""

from .context import FSMContext
from .state import State, StatesGroup
from .storage import BaseStorage, MemoryStorage, StorageKey

__all__ = [
    "BaseStorage",
    "FSMContext",
    "MemoryStorage",
    "State",
    "StatesGroup",
    "StorageKey",
]

try:
    from .storage import RedisStorage

    __all__ = [*__all__, "RedisStorage"]
except ImportError:
    pass
