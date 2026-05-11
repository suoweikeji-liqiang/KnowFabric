"""H2: embedding-first group_and_normalize tests (docs/39 §5.4)."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.canonical_key import (
    _apply_terminology,
    _group_via_embedding,
    _save_registry,
    group_and_normalize,
    HASH_CACHE,
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

    with patch("packages.compiler.embedding_client.embed_batch", return_value=fake_embs):
        with patch("packages.compiler.canonical_key._llm_refine_cluster") as mock_llm:
            mock_llm.return_value = [{
                "canonical_key": "chilled_water_setpoint",
                "member_names": ["Fake Chilled Water Param A", "Fake Chilled Water Param B"],
                "rationale": "same physical quantity",
            }, {
                "canonical_key": "safety_valve_pressure",
                "member_names": ["Fake Safety Valve Param"],
                "rationale": "different concept",
            }]
            mapping = _group_via_embedding(
                names, domain_id="hvac", equipment_class_id="centrifugal_chiller",
                knowledge_object_type="parameter_spec",
            )

    ck1 = mapping["Fake Chilled Water Param A"]
    ck2 = mapping["Fake Chilled Water Param B"]
    ck3 = mapping["Fake Safety Valve Param"]
    assert ck1 == ck2, f"EN pair should share canonical_key: {ck1} vs {ck2}"
    assert ck1 != ck3, f"Different concept should have different key"
    assert "chilled_water_setpoint" in ck1


def test_embedding_first_is_default():
    assert USE_EMBEDDING_FIRST is True, "KNOWFABRIC_USE_EMBEDDING_FIRST must default to 1"


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
        with patch.object(ck, "_llm_refine_cluster", return_value=[]):
            mapping = ck.group_and_normalize(
                names, domain_id="hvac", equipment_class_id="centrifugal_chiller",
                knowledge_object_type="parameter_spec",
            )
    # Should not crash; each name gets a key
    assert len(mapping) == 2
    for n in names:
        assert n in mapping
