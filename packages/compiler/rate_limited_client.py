"""Shared async/sync rate limiting for OpenAI-compatible LLM calls."""

from __future__ import annotations

import asyncio
import inspect
import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


class RateLimit429(RuntimeError):
    """Raised when a provider returns HTTP 429."""


class ServerError5xx(RuntimeError):
    """Raised when a provider returns a retryable HTTP 5xx."""


class MaxRetriesExceeded(RuntimeError):
    """Raised when a rate-limited call exhausts retry attempts."""


class AsyncRateLimiter:
    """Simple interval-based async RPM limiter."""

    def __init__(
        self,
        max_rpm: int,
        *,
        time_fn: Callable[[], float] | None = None,
        sleeper: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.max_rpm = max(1, int(max_rpm))
        self._interval = 60.0 / float(self.max_rpm)
        self._time_fn = time_fn or time.monotonic
        self._sleeper = sleeper or asyncio.sleep
        self._lock = asyncio.Lock()
        self._last_at: float | None = None

    async def acquire(self) -> None:
        async with self._lock:
            now = self._time_fn()
            if self._last_at is not None:
                wait = self._interval - (now - self._last_at)
                if wait > 0:
                    await self._sleeper(wait)
                    now = self._time_fn()
            self._last_at = now


class _SyncRateLimiter:
    def __init__(self, max_rpm: int) -> None:
        self._interval = 60.0 / float(max(1, int(max_rpm)))
        self._lock = threading.Lock()
        self._last_at: float | None = None

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            if self._last_at is not None:
                wait = self._interval - (now - self._last_at)
                if wait > 0:
                    time.sleep(wait)
                    now = time.monotonic()
            self._last_at = now


@dataclass
class RateLimitedClient:
    """Limit concurrent LLM calls and retry transient provider failures."""

    max_concurrent: int = 8
    max_rpm: int = 60
    max_retries: int = 5
    sleeper: Callable[[float], Awaitable[None]] | None = None
    semaphore: asyncio.Semaphore = field(init=False)
    rpm_limiter: AsyncRateLimiter = field(init=False)
    _sync_semaphore: threading.Semaphore = field(init=False)
    _sync_limiter: _SyncRateLimiter = field(init=False)

    def __post_init__(self) -> None:
        self.max_concurrent = max(1, int(self.max_concurrent))
        self.max_rpm = max(1, int(self.max_rpm))
        self.max_retries = max(1, int(self.max_retries))
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.rpm_limiter = AsyncRateLimiter(self.max_rpm, sleeper=self.sleeper)
        self._sync_semaphore = threading.Semaphore(self.max_concurrent)
        self._sync_limiter = _SyncRateLimiter(self.max_rpm)

    async def call(self, operation: Callable[..., T | Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        last_error: BaseException | None = None
        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:
                    await self.rpm_limiter.acquire()
                    return await _call_operation(operation, *args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - normalized below
                if not _is_retryable(exc):
                    raise
                last_error = exc
                if attempt >= self.max_retries - 1:
                    break
                await (self.sleeper or asyncio.sleep)(_backoff_seconds(attempt))
        raise MaxRetriesExceeded(f"LLM request failed after {self.max_retries} attempts") from last_error

    def call_sync(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        last_error: BaseException | None = None
        for attempt in range(self.max_retries):
            try:
                with self._sync_semaphore:
                    self._sync_limiter.acquire()
                    return operation(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - normalized below
                if not _is_retryable(exc):
                    raise
                last_error = exc
                if attempt >= self.max_retries - 1:
                    break
                time.sleep(_backoff_seconds(attempt))
        raise MaxRetriesExceeded(f"LLM request failed after {self.max_retries} attempts") from last_error

    @classmethod
    def from_env(cls) -> "RateLimitedClient":
        return cls(
            max_concurrent=_env_int("LLM_MAX_CONCURRENT", 8),
            max_rpm=_env_int("LLM_MAX_RPM", 60),
            max_retries=_env_int("LLM_MAX_RETRIES", 5),
        )


async def _call_operation(operation: Callable[..., T | Awaitable[T]], *args: Any, **kwargs: Any) -> T:
    if inspect.iscoroutinefunction(operation):
        return await operation(*args, **kwargs)  # type: ignore[return-value]
    return await asyncio.to_thread(operation, *args, **kwargs)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (RateLimit429, ServerError5xx)):
        return True
    code = getattr(exc, "code", None)
    if code == 429:
        return True
    return isinstance(code, int) and 500 <= code <= 599


def _backoff_seconds(attempt: int) -> float:
    return min(60.0, (2.0 ** attempt) + random.random())


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


_GLOBAL_CLIENT: RateLimitedClient | None = None
_GLOBAL_LOCK = threading.Lock()


def global_rate_limited_client() -> RateLimitedClient:
    global _GLOBAL_CLIENT
    with _GLOBAL_LOCK:
        if _GLOBAL_CLIENT is None:
            _GLOBAL_CLIENT = RateLimitedClient.from_env()
        return _GLOBAL_CLIENT


def reset_global_rate_limited_client() -> None:
    global _GLOBAL_CLIENT
    with _GLOBAL_LOCK:
        _GLOBAL_CLIENT = None
