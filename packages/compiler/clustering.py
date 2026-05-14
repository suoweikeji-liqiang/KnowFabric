"""Cosine-similarity clustering via union-find.

Calibrated for BGE-M3 4-bit on chiller domain parameter names.
Threshold 0.78: same-concept sim ≥0.80, different-concept sim ≤0.66, gap 0.14.
"""

from __future__ import annotations

import math

DEFAULT_THRESHOLD = 0.78


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.parent[ri] = rj


def _member_indices(uf: _UnionFind, n: int, root: int) -> list[int]:
    return [idx for idx in range(n) if uf.find(idx) == root]


def _can_complete_link(
    uf: _UnionFind,
    embeddings: list[list[float]],
    *,
    i: int,
    j: int,
    threshold: float,
) -> bool:
    n = len(embeddings)
    left = _member_indices(uf, n, uf.find(i))
    right = _member_indices(uf, n, uf.find(j))
    merged = list(dict.fromkeys(left + right))
    for a_idx, a in enumerate(merged):
        for b in merged[a_idx + 1:]:
            if cosine(embeddings[a], embeddings[b]) < threshold:
                return False
    return True


def cluster_by_cosine(
    names: list[str],
    embeddings: list[list[float]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    linkage: str = "complete",
) -> list[list[str]]:
    """Greedy clustering by cosine similarity.

    ``single`` merges when any pair crosses the threshold. ``complete`` only
    merges clusters when every pair in the merged cluster remains above it.
    """
    n = len(names)
    if n != len(embeddings):
        raise ValueError(f"names ({n}) and embeddings ({len(embeddings)}) length mismatch")
    if linkage not in {"single", "complete"}:
        raise ValueError("linkage must be 'single' or 'complete'")
    if n == 0:
        return []

    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if cosine(embeddings[i], embeddings[j]) < threshold:
                continue
            if linkage == "complete" and not _can_complete_link(
                uf,
                embeddings,
                i=i,
                j=j,
                threshold=threshold,
            ):
                continue
            if uf.find(i) != uf.find(j):
                uf.union(i, j)

    clusters: dict[int, list[str]] = {}
    for i in range(n):
        clusters.setdefault(uf.find(i), []).append(names[i])
    return list(clusters.values())
