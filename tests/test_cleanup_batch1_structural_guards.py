"""Structural guard tests for cleanup batch 1."""

from __future__ import annotations

import pytest

from packages.compiler.cross_source_merger import assert_valid_ko_identity, _normalize_canonical_key_for_anchor
from scripts.retag_consensus_state import retag_consensus_states


def test_merger_rejects_empty_equipment_class():
    with pytest.raises(ValueError, match="equipment_class_id"):
        _normalize_canonical_key_for_anchor(
            "hvac::performance_spec:制冷量",
            domain_id="hvac",
            equipment_class_id="",
            knowledge_object_type="performance_spec",
            fallback_name="制冷量",
        )


def test_merger_rejects_double_colon_canonical_key_after_normalization():
    with pytest.raises(ValueError, match="canonical_key"):
        assert_valid_ko_identity(
            {
                "ontology_class_id": "ahu",
                "canonical_key": "hvac::performance_spec:制冷量",
            }
        )


def test_retag_rejects_structurally_invalid_ko_identity():
    rows = [
        {
            "knowledge_object_id": "ko_bad",
            "ontology_class_id": "",
            "canonical_key": "hvac::performance_spec:制冷量",
            "consensus_state": "material_conflict",
            "authority_summary_json": {"layers": []},
        }
    ]

    with pytest.raises(ValueError, match="ontology_class_id"):
        retag_consensus_states(rows, apply=False)
