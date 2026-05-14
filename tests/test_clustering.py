"""H1: clustering tests (docs/39 §4.3)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.clustering import cluster_by_cosine, cosine, DEFAULT_THRESHOLD


def _fake_emb(values: list[list[float]]) -> list[list[float]]:
    return values


def test_cosine_identical():
    v = [1.0, 2.0, 3.0]
    assert abs(cosine(v, v) - 1.0) < 1e-9


def test_cosine_orthogonal():
    assert abs(cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_single_name_single_cluster():
    clusters = cluster_by_cosine(["a"], _fake_emb([[1.0, 0.0]]))
    assert len(clusters) == 1
    assert clusters[0] == ["a"]


def test_similar_names_one_cluster():
    # sim ≈ 0.87 > 0.78 → merged
    clusters = cluster_by_cosine(
        ["a", "b", "c"],
        _fake_emb([[1.0, 0.2], [1.0, 0.3], [1.0, 0.25]]),
    )
    assert len(clusters) == 1
    assert sorted(clusters[0]) == ["a", "b", "c"]


def test_one_pair_above_threshold_one_isolated():
    # a,b sim ≈ 0.98 > 0.78; c isolated from both
    clusters = cluster_by_cosine(
        ["a", "b", "c"],
        _fake_emb([[1.0, 0.0], [1.0, 0.03], [-1.0, 0.0]]),
    )
    assert len(clusters) == 2
    lens = sorted(len(c) for c in clusters)
    assert lens == [1, 2]


def test_complete_linkage_blocks_semantic_chain_merge():
    """A-B and B-C edges must not force A/B/C into one complete-linkage cluster."""

    # Pairwise cosine: A-B = 0.85, B-C = 0.85, A-C = 0.60.
    embeddings = _fake_emb([
        [1.0, 0.0, 0.0],
        [0.85, 0.526782687642637, 0.0],
        [0.60, 0.6454274643132343, 0.4727439401643625],
    ])

    single_clusters = cluster_by_cosine(
        ["a", "b", "c"],
        embeddings,
        threshold=DEFAULT_THRESHOLD,
        linkage="single",
    )
    complete_clusters = cluster_by_cosine(
        ["a", "b", "c"],
        embeddings,
        threshold=DEFAULT_THRESHOLD,
    )

    assert [sorted(cluster) for cluster in single_clusters] == [["a", "b", "c"]]
    assert sorted(sorted(cluster) for cluster in complete_clusters) == [["a", "b"], ["c"]]


def test_large_input_no_crash():
    import random
    random.seed(42)
    names = [f"p{i}" for i in range(100)]
    embs = [[random.random() for _ in range(100)] for _ in range(100)]
    clusters = cluster_by_cosine(names, embs)
    assert len(clusters) > 0


def test_mismatched_lengths_raises():
    try:
        cluster_by_cosine(["a", "b"], [[1.0]])
        assert False, "should have raised"
    except ValueError:
        pass
