"""Scale checks for complete-linkage cosine clustering."""

from __future__ import annotations

import random
import signal
import time
from contextlib import contextmanager

from packages.compiler.clustering import DEFAULT_THRESHOLD, cluster_by_cosine, cosine


@contextmanager
def _time_limit(seconds: int):
    def _handle_timeout(signum, frame):
        raise TimeoutError(f"operation exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def _random_embeddings(count: int, dim: int) -> list[list[float]]:
    rng = random.Random(42)
    return [[rng.random() for _ in range(dim)] for _ in range(count)]


def _slow_complete_linkage_reference(
    names: list[str],
    embeddings: list[list[float]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[list[str]]:
    parent = list(range(len(names)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def members(root: int) -> list[int]:
        return [idx for idx in range(len(names)) if find(idx) == root]

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if cosine(embeddings[i], embeddings[j]) < threshold:
                continue
            merged = list(dict.fromkeys(members(find(i)) + members(find(j))))
            if all(
                cosine(embeddings[a], embeddings[b]) >= threshold
                for idx, a in enumerate(merged)
                for b in merged[idx + 1 :]
            ):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    clusters: dict[int, list[str]] = {}
    for i, name in enumerate(names):
        clusters.setdefault(find(i), []).append(name)
    return list(clusters.values())


def _canonical(clusters: list[list[str]]) -> list[list[str]]:
    return sorted(sorted(cluster) for cluster in clusters)


def test_complete_linkage_matches_reference_on_small_input():
    names = [f"p{i}" for i in range(6)]
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.91, 0.414608, 0.0],
        [0.82, 0.572364, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.91, 0.414608],
        [0.0, 0.82, 0.572364],
    ]

    assert _canonical(cluster_by_cosine(names, embeddings)) == _canonical(
        _slow_complete_linkage_reference(names, embeddings)
    )


def test_complete_linkage_clusters_100_random_embeddings_under_one_second():
    names = [f"p{i}" for i in range(100)]
    embeddings = _random_embeddings(100, 64)

    started = time.perf_counter()
    clusters = cluster_by_cosine(names, embeddings)
    elapsed = time.perf_counter() - started

    assert len(clusters) > 0
    assert elapsed < 1.0


def test_complete_linkage_clusters_700_dense_embeddings_under_five_seconds():
    names = [f"p{i}" for i in range(700)]
    embeddings = [[1.0] + [0.0] * 63 for _ in names]

    with _time_limit(6):
        started = time.perf_counter()
        clusters = cluster_by_cosine(names, embeddings)
        elapsed = time.perf_counter() - started

    assert clusters == [names]
    assert elapsed < 5.0
