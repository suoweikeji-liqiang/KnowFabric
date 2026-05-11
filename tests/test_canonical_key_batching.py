"""E2: group_and_normalize batching + sanity check tests (docs/38 §5)."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.canonical_key import (
    BATCH_SIZE,
    MAX_GROUP_SIZE,
    _sanity_check_groups,
    _save_registry,
    group_and_normalize,
    HASH_CACHE,
)


def _clear():
    _save_registry({"canonical_keys": {}})
    HASH_CACHE.clear()


def test_sanity_check_rejects_oversized_group():
    """E2: 280-member group → split into 280 individual groups."""
    groups = [{
        "canonical_key": "super_merged",
        "normalized_name": "everything",
        "member_names": [f"param_{i}" for i in range(280)],
        "rationale": "LLM greedy merge",
    }]
    result = _sanity_check_groups(groups)
    assert len(result) == 280, f"Expected 280 groups, got {len(result)}"
    for g in result:
        assert len(g["member_names"]) == 1, f"Each group should have 1 member"


def test_sanity_check_rejects_degenerate_key():
    """E2: canonical_key='1' → replaced with mechanical slug."""
    groups = [{
        "canonical_key": "1",
        "normalized_name": "1",
        "member_names": ["Chilled Water Setpoint", "Current Limit"],
        "rationale": "test",
    }]
    result = _sanity_check_groups(groups)
    assert len(result) == 2
    for g in result:
        assert g["canonical_key"] not in ("1", "")


def test_sanity_check_passes_normal_group():
    """E2: 3-member group with valid key → passes through."""
    groups = [{
        "canonical_key": "chilled_water_setpoint",
        "normalized_name": "chw_setpoint",
        "member_names": ["CHWS", "Chilled Water Setpoint", "冷冻水设定"],
        "rationale": "valid",
    }]
    result = _sanity_check_groups(groups)
    assert len(result) == 1
    assert result[0]["canonical_key"] == "chilled_water_setpoint"


def test_group_and_normalize_with_mock_oversized():
    """E2 integration: mock LLM returns 280-member group → sanity splits it."""
    _clear()
    names = [f"param_{i}" for i in range(50)]
    mock_groups = [{
        "canonical_key": "bad_merge",
        "normalized_name": "bad",
        "member_names": names,
        "rationale": "mock pathological",
    }]

    with patch("packages.compiler.canonical_key._llm_group_and_normalize",
               return_value=mock_groups):
        mapping = group_and_normalize(
            names, domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    # No single key should have > MAX_GROUP_SIZE names
    from collections import Counter
    counts = Counter(mapping.values())
    for ck, count in counts.most_common(5):
        assert count <= MAX_GROUP_SIZE, f"Key '{ck}' has {count} names, max allowed {MAX_GROUP_SIZE}"
    assert len(mapping) == 50


def test_batch_split(monkeypatch):
    """E2: 100 names → at least 4 batches (100/30 = 4). Forces old LLM path."""
    _clear()
    monkeypatch.setenv("KNOWFABRIC_USE_EMBEDDING_FIRST", "0")
    import importlib
    import packages.compiler.canonical_key as ck
    importlib.reload(ck)

    names = [f"test_param_{i}" for i in range(100)]

    call_count = 0
    def mock_llm(batch, **kw):
        nonlocal call_count
        call_count += 1
        return [{"canonical_key": f"key_{n}", "normalized_name": n, "member_names": [n], "rationale": "test"} for n in batch]

    with patch.object(ck, "_llm_group_and_normalize", side_effect=mock_llm):
        ck.group_and_normalize(names, domain_id="hvac",
                               equipment_class_id="centrifugal_chiller",
                               knowledge_object_type="parameter_spec")

    expected_batches = (len(names) + BATCH_SIZE - 1) // BATCH_SIZE
    assert call_count == expected_batches, f"Expected {expected_batches} batches, got {call_count}"
