from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Configuration for retry behaviour with exponential backoff.

    All fields are immutable after creation.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: bool = True


async def exponential_backoff_with_jitter(
    policy: RetryPolicy,
    attempt: int,
) -> float:
    """Sleep with exponential backoff and optional jitter.

    Args:
        policy: Retry configuration controlling delays and jitter.
        attempt: Zero-based attempt index (0 = first retry).

    Returns:
        The actual delay (in seconds) that was applied.
    """
    delay = min(policy.base_delay * (2**attempt), policy.max_delay)

    if policy.jitter:
        delay = random.uniform(0, delay)  # noqa: S311

    await asyncio.sleep(delay)
    return delay
