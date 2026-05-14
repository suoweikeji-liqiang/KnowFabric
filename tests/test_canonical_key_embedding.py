"""H2: embedding-first group_and_normalize tests (docs/39 §5.4)."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.canonical_key import (
    _apply_terminology,
    _group_via_embedding,
    _save_registry,
    _tighten_oversize_embedding_clusters,
    group_and_normalize,
    HASH_CACHE,
    MAX_GROUP_SIZE,
    USE_EMBEDDING_FIRST,
)


def _clear():
    _save_registry({"canonical_keys": {}})
    HASH_CACHE.clear()


def test_apply_terminology_resolves_and_returns_remaining():
    terms = {
        "chw_setpoint": ["Chilled Water Setpoint", "CHWS"],
        "current_limit": ["Current Limit"],
    }
    resolved, remaining = _apply_terminology(
        ["Chilled Water Setpoint", "Unknown Param", "CHWS"],
        terms,
    )
    assert resolved == {"Chilled Water Setpoint": "chw_setpoint", "CHWS": "chw_setpoint"}
    assert remaining == ["Unknown Param"]


def test_group_via_embedding_merges_cross_lingual():
    """Mock embedding makes EN+ZH pair similar → clustered → 1 group."""
    _clear()
    names = ["Fake Chilled Water Param A", "Fake Chilled Water Param B",
             "Fake Safety Valve Param"]

    fake_embs = [
        [1.0, 0.0, 0.0],     # EN chw
        [0.95, 0.1, 0.0],    # EN chw (similar → cosine 0.99)
        [-1.0, 0.0, 0.0],    # different (cosine -1.0)
    ]

    # N3: embedding clusters directly → same cluster = same canonical_key
    # First 2 names sim 0.99 → same cluster → same key. Third name far → separate.
    with patch("packages.compiler.embedding_client.embed_batch", return_value=fake_embs):
        mapping = _group_via_embedding(
            names, domain_id="hvac", equipment_class_id="centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    ck1 = mapping["Fake Chilled Water Param A"]
    ck2 = mapping["Fake Chilled Water Param B"]
    ck3 = mapping["Fake Safety Valve Param"]
    assert ck1 == ck2, f"Embedding cluster should share key: {ck1} vs {ck2}"
    assert ck1 != ck3, f"Different cluster should have different key"


def test_embedding_cluster_splits_by_unit_facet():
    """High-similarity names with incompatible unit facets must split."""

    _clear()
    names = ["油压差范围（运行）", "供油温度范围"]
    fake_embs = [
        [1.0, 0.0, 0.0],
        [0.95, 0.1, 0.0],
    ]
    facet_hints = {
        "油压差范围（运行）": "pressure_differential",
        "供油温度范围": "temperature",
    }

    with patch("packages.compiler.embedding_client.embed_batch", return_value=fake_embs):
        mapping = _group_via_embedding(
            names,
            domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            knowledge_object_type="parameter_spec",
            facet_hints=facet_hints,
        )

    assert mapping["油压差范围（运行）"] != mapping["供油温度范围"]


def test_embedding_cluster_splits_by_brick_reference_subtype():
    """Same physical unit family but different reference points must split."""

    _clear()
    names = ["油温控制设定值", "Cooling Water Inlet Temperature"]
    fake_embs = [
        [1.0, 0.0, 0.0],
        [0.95, 0.1, 0.0],
    ]
    facet_hints = {
        "油温控制设定值": ("temperature", "oil_temperature"),
        "Cooling Water Inlet Temperature": (
            "temperature",
            "cooling_water_inlet_temperature",
        ),
    }

    with patch("packages.compiler.embedding_client.embed_batch", return_value=fake_embs):
        mapping = _group_via_embedding(
            names,
            domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            knowledge_object_type="parameter_spec",
            facet_hints=facet_hints,
        )

    assert mapping["油温控制设定值"] != mapping["Cooling Water Inlet Temperature"]


def test_embedding_first_is_default():
    assert USE_EMBEDDING_FIRST is True, "KNOWFABRIC_USE_EMBEDDING_FIRST must default to 1"


def test_oversize_embedding_cluster_is_tightened(monkeypatch):
    names = [f"param_{i}" for i in range(MAX_GROUP_SIZE + 1)]
    embeddings = [[1.0, 0.0] for _ in names]
    calls = {}

    def fake_recursive(sub_names, sub_embs, *, threshold, max_size):
        calls["threshold"] = threshold
        calls["max_size"] = max_size
        return [sub_names[:6], sub_names[6:]]

    monkeypatch.setattr(
        "packages.compiler.canonical_key._cluster_recursive",
        fake_recursive,
    )
    refined = _tighten_oversize_embedding_clusters(
        names,
        embeddings,
        [names],
        threshold=0.78,
    )

    assert round(calls["threshold"], 2) == 0.83
    assert calls["max_size"] == 8
    assert [len(cluster) for cluster in refined] == [6, 5]


def test_group_and_normalize_dispatches_to_embedding(monkeypatch):
    """Verify the dispatcher routes to embedding path by default."""
    _clear()
    monkeypatch.setenv("KNOWFABRIC_USE_EMBEDDING_FIRST", "1")
    # Force reimport
    import importlib
    import packages.compiler.canonical_key as ck
    importlib.reload(ck)

    names = ["test_param_a", "test_param_b"]
    fake_embs = [[1.0, 0.0], [0.5, 0.87]]

    with patch("packages.compiler.embedding_client.embed_batch", return_value=fake_embs):
        mapping = ck.group_and_normalize(
            names, domain_id="hvac", equipment_class_id="centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )
    # Should not crash; each name gets a key (N3: embedding clusters directly)
    assert len(mapping) == 2
    for n in names:
        assert n in mapping
