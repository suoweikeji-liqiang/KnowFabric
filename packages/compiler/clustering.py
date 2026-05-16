"""Cosine-similarity clustering via union-find.

Calibrated for BGE-M3 4-bit on chiller domain parameter names.
Threshold 0.78: same-concept sim ≥0.80, different-concept sim ≤0.66, gap 0.14.
"""

from __future__ import annotations

import math

import numpy as np

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
    sim_matrix: np.ndarray,
    *,
    left: list[int],
    right: list[int],
    threshold: float,
) -> bool:
    return bool(np.all(sim_matrix[np.ix_(left, right)] >= threshold))


def _cosine_similarity_matrix(embeddings: list[list[float]]) -> np.ndarray:
    matrix = np.asarray(embeddings, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("embeddings must be a 2D list of vectors")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    normalized = np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms != 0)
    return normalized @ normalized.T


def _row_masks(eligible: np.ndarray) -> list[int]:
    """Return bit masks of threshold-eligible neighbors for each row."""

    return [
        sum(1 << int(idx) for idx in np.flatnonzero(row))
        for row in eligible
    ]


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

    sim_matrix = _cosine_similarity_matrix(embeddings)
    eligible = sim_matrix >= threshold
    uf = _UnionFind(n)
    cluster_masks = {idx: 1 << idx for idx in range(n)}
    common_masks = {idx: mask for idx, mask in enumerate(_row_masks(eligible))}
    for i in range(n):
        for j in range(i + 1, n):
            if not eligible[i, j]:
                continue
            ri, rj = uf.find(i), uf.find(j)
            if ri == rj:
                continue
            if linkage == "complete":
                if cluster_masks[rj] & ~common_masks[ri]:
                    continue
                if cluster_masks[ri] & ~common_masks[rj]:
                    continue
            merged_mask = cluster_masks[ri] | cluster_masks[rj]
            merged_common = common_masks[ri] & common_masks[rj]
            uf.union(ri, rj)
            new_root = uf.find(rj)
            cluster_masks.pop(ri, None)
            cluster_masks.pop(rj, None)
            common_masks.pop(ri, None)
            common_masks.pop(rj, None)
            cluster_masks[new_root] = merged_mask
            common_masks[new_root] = merged_common

    clusters: dict[int, list[str]] = {}
    for i in range(n):
        clusters.setdefault(uf.find(i), []).append(names[i])
    return list(clusters.values())
