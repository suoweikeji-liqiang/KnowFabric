"""Concurrency and rate-limit behavior for LLM call wrappers."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from packages.compiler import canonical_key as ck
from packages.compiler.rate_limited_client import AsyncRateLimiter, MaxRetriesExceeded, RateLimit429, RateLimitedClient
from scripts import run_hvac_doclevel_extraction_batch as batch


def test_arbiter_concurrent_matches_serial(monkeypatch) -> None:
    clusters = [[f"name-{idx}-a", f"name-{idx}-b"] for idx in range(5)]
    publisher_hints = {name: f"pub-{idx % 2}" for idx, cluster in enumerate(clusters) for name in cluster}

    def adjudicate(cluster, **_kwargs):
        return [list(cluster)]

    monkeypatch.setattr(ck, "_llm_adjudicate_cluster", adjudicate)
    monkeypatch.setenv("LLM_MAX_CONCURRENT", "1")
    serial = ck._apply_llm_arbiter(
        clusters,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints=publisher_hints,
    )
    monkeypatch.setenv("LLM_MAX_CONCURRENT", "8")
    concurrent = ck._apply_llm_arbiter(
        clusters,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        publisher_hints=publisher_hints,
    )

    assert _digest(serial) == _digest(concurrent)


def test_extraction_concurrent_matches_serial(tmp_path, monkeypatch) -> None:
    items = [_item(idx) for idx in range(1, 6)]
    args = _args(tmp_path)
    calls: list[int] = []

    monkeypatch.setattr(batch, "load_manifest", lambda _path: [])
    monkeypatch.setattr(batch, "select_items", lambda _rows, groups, limit: items)
    monkeypatch.setattr(batch, "load_existing_task_summaries", lambda _batch_dir: [])
    monkeypatch.setattr(batch, "write_batch_summary", lambda _batch_dir, _summary: None)

    def fake_run_item(_args, item, _batch_dir):
        calls.append(item.row_index)
        return {"row_index": item.row_index, "status": "completed", "backend_results": [{"backend": "mock", "status": "ok"}]}

    monkeypatch.setattr(batch, "run_item", fake_run_item)
    run_ids = iter(["serial", "concurrent"])
    monkeypatch.setattr(batch, "make_run_id", lambda: next(run_ids))
    monkeypatch.setenv("EXTRACTION_DOC_CONCURRENCY", "1")
    serial = batch.run(args)["tasks"]
    calls.clear()
    monkeypatch.setenv("EXTRACTION_DOC_CONCURRENCY", "8")
    concurrent = batch.run(args)["tasks"]

    assert _digest(serial) == _digest(concurrent)
    assert calls == [1, 2, 3, 4, 5]


def test_rate_limit_handler_429() -> None:
    asyncio.run(_rate_limit_handler_429())


async def _rate_limit_handler_429() -> None:
    attempts = 0
    client = RateLimitedClient(max_concurrent=2, max_rpm=6000, max_retries=5, sleeper=lambda _seconds: asyncio.sleep(0))

    async def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RateLimit429("retry")
        return "ok"

    assert await client.call(operation) == "ok"
    assert attempts == 3


def test_semaphore_caps_concurrency() -> None:
    asyncio.run(_semaphore_caps_concurrency())


async def _semaphore_caps_concurrency() -> None:
    active = 0
    max_active = 0
    client = RateLimitedClient(max_concurrent=8, max_rpm=6000, max_retries=1)

    async def operation(idx: int) -> int:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return idx

    results = await asyncio.gather(*(client.call(operation, idx) for idx in range(10)))

    assert sorted(results) == list(range(10))
    assert max_active <= 8


def test_rpm_limiter_throttles() -> None:
    asyncio.run(_rpm_limiter_throttles())


async def _rpm_limiter_throttles() -> None:
    fake = _FakeClock()
    limiter = AsyncRateLimiter(max_rpm=60, time_fn=fake.monotonic, sleeper=fake.sleep)

    for _ in range(100):
        await limiter.acquire()

    assert fake.elapsed >= 99.0


def test_max_retries_exhausted() -> None:
    asyncio.run(_max_retries_exhausted())


async def _max_retries_exhausted() -> None:
    client = RateLimitedClient(max_concurrent=2, max_rpm=6000, max_retries=5, sleeper=lambda _seconds: asyncio.sleep(0))

    async def operation():
        raise RateLimit429("retry")

    with pytest.raises(MaxRetriesExceeded):
        await client.call(operation)


def _digest(value) -> str:
    return hashlib.sha1(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _item(idx: int):
    return type(
        "Item",
        (),
        {
            "row_index": idx,
            "path": Path(f"/tmp/doc-{idx}.pdf"),
            "authority_level": "oem_manual",
            "brand": "Brand",
            "batch_group": "group",
            "priority": "P1",
            "document_kind": "manual",
            "equipment_scope": "chiller",
            "text_quality": "text",
            "recommended_mode": "text",
        },
    )()


def _args(tmp_path: Path):
    return Namespace(
        manifest="manifest.csv",
        groups={"group"},
        limit=5,
        resume_dir=None,
        output_dir=str(tmp_path),
        force=False,
        backends=["mock"],
        judge_backend="",
        knowledge_types=["parameter_spec"],
        target_candidates=10,
        section_aware=False,
        section_max_tokens=30000,
        section_target_candidates=20,
        execute=False,
        ignore_triage=True,
    )


class _FakeClock:
    def __init__(self) -> None:
        self.elapsed = 0.0

    def monotonic(self) -> float:
        return self.elapsed

    async def sleep(self, seconds: float) -> None:
        self.elapsed += seconds
