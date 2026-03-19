from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from vk_teams_async_bot.client.retry import RetryPolicy, exponential_backoff_with_jitter

_SLEEP_TARGET = "vk_teams_async_bot.client.retry.asyncio.sleep"


class TestRetryPolicyDefaults:
    def test_default_values(self) -> None:
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 30.0
        assert policy.jitter is True

    def test_custom_values(self) -> None:
        policy = RetryPolicy(
            max_retries=5, base_delay=0.5, max_delay=60.0, jitter=False
        )
        assert policy.max_retries == 5
        assert policy.base_delay == 0.5
        assert policy.max_delay == 60.0
        assert policy.jitter is False

    def test_frozen(self) -> None:
        policy = RetryPolicy()
        with pytest.raises(AttributeError):
            policy.max_retries = 10  # type: ignore[misc]


class TestExponentialBackoffWithJitter:
    @pytest.mark.asyncio
    async def test_basic_delay_no_jitter(self) -> None:
        """Without jitter the delay equals base_delay * 2^attempt."""
        policy = RetryPolicy(base_delay=1.0, max_delay=30.0, jitter=False)
        with patch(_SLEEP_TARGET, new=AsyncMock()):
            delay_0 = await exponential_backoff_with_jitter(policy, 0)
            delay_1 = await exponential_backoff_with_jitter(policy, 1)
            delay_2 = await exponential_backoff_with_jitter(policy, 2)

        assert delay_0 == pytest.approx(1.0)
        assert delay_1 == pytest.approx(2.0)
        assert delay_2 == pytest.approx(4.0)

    @pytest.mark.asyncio
    async def test_delay_capped_at_max(self) -> None:
        """Delay must never exceed max_delay regardless of attempt number."""
        policy = RetryPolicy(base_delay=1.0, max_delay=5.0, jitter=False)
        with patch(_SLEEP_TARGET, new=AsyncMock()):
            delay = await exponential_backoff_with_jitter(policy, 10)

        assert delay == pytest.approx(5.0)

    @pytest.mark.asyncio
    async def test_jitter_adds_randomness(self) -> None:
        """With jitter enabled the delay should vary between runs."""
        policy = RetryPolicy(base_delay=2.0, max_delay=30.0, jitter=True)
        delays: list[float] = []

        with patch(_SLEEP_TARGET, new=AsyncMock()):
            for _ in range(20):
                d = await exponential_backoff_with_jitter(policy, 2)
                delays.append(d)

        # The theoretical max is base_delay * 2^2 = 8.0
        assert all(0 <= d <= 8.0 for d in delays)
        # With 20 samples, not all should be identical (extremely unlikely)
        assert len(set(delays)) > 1

    @pytest.mark.asyncio
    async def test_jitter_bounded_by_max_delay(self) -> None:
        """Jittered delay must also respect max_delay."""
        policy = RetryPolicy(base_delay=1.0, max_delay=3.0, jitter=True)

        with patch(_SLEEP_TARGET, new=AsyncMock()):
            for _ in range(30):
                d = await exponential_backoff_with_jitter(policy, 10)
                assert d <= 3.0

    @pytest.mark.asyncio
    async def test_sleep_is_called(self) -> None:
        """Verify that asyncio.sleep is actually invoked with the computed delay."""
        policy = RetryPolicy(base_delay=0.5, max_delay=10.0, jitter=False)
        mock_sleep = AsyncMock()

        with patch(_SLEEP_TARGET, new=mock_sleep):
            await exponential_backoff_with_jitter(policy, 0)

        mock_sleep.assert_awaited_once_with(pytest.approx(0.5))
