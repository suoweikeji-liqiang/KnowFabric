"""Cosine-similarity hierarchical clustering via union-find.

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


def cluster_by_cosine(
    names: list[str],
    embeddings: list[list[float]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[list[str]]:
    """Greedy single-linkage clustering: any pair with sim ≥ threshold gets merged."""
    n = len(names)
    if n != len(embeddings):
        raise ValueError(f"names ({n}) and embeddings ({len(embeddings)}) length mismatch")
    if n == 0:
        return []

    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if cosine(embeddings[i], embeddings[j]) >= threshold:
                uf.union(i, j)

    clusters: dict[int, list[str]] = {}
    for i in range(n):
        clusters.setdefault(uf.find(i), []).append(names[i])
    return list(clusters.values())
