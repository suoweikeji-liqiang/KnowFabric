"""Tests for cross-source knowledge object merger."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import (
    _coerce_numeric,
    _compute_consensus_state,
    _values_agree,
    merge_candidates,
)


def _make_candidate(
    title: str,
    value: str | None = None,
    default_value: str | None = None,
    authority_level: str = "oem_manual",
    publisher: str = "Trane",
    citation: str = "Trane Manual p.29",
    doc_id: str = "doc_001",
    chunk_id: str = "chunk_001",
    confidence: float = 0.9,
    trust_level: str = "L4",
    evidence_text: str = "Test evidence text",
) -> dict:
    return {
        "title": title,
        "summary": f"Summary for {title}",
        "structured_payload": {
            "value": value,
            "default_value": default_value,
        },
        "confidence_score": confidence,
        "trust_level": trust_level,
        "review_status": "published",
        "authority_level": authority_level,
        "publisher": publisher,
        "citation": citation,
        "doc_id": doc_id,
        "evidence": [
            {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "page_id": "page_001",
                "page_no": 29,
                "evidence_text": evidence_text,
                "evidence_role": "primary",
            }
        ],
    }


def test_single_candidate_returns_single_source():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", default_value="44F"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert len(result) == 1
    assert result[0]["consensus_state"] == "single_source"
    assert result[0]["highest_authority_level"] == "oem_manual"
    assert result[0]["conflict_summary"] is None
    assert len(result[0]["authority_summary_json"]["layers"]) == 1


def test_two_candidates_same_value_returns_agreed():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_trane", chunk_id="chunk_trane",
                         authority_level="oem_manual", publisher="Trane",
                         citation="Trane Manual p.29"),
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_york", chunk_id="chunk_york",
                         authority_level="oem_manual", publisher="York",
                         citation="York YK Manual p.43"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert len(result) == 1
    assert result[0]["consensus_state"] == "agreed"
    assert len(result[0]["authority_summary_json"]["layers"]) == 2
    assert len(result[0]["evidence_rows"]) == 2


def test_different_values_produces_conflict():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_trane", chunk_id="chunk_trane",
                         authority_level="oem_manual", publisher="Trane"),
        _make_candidate("CHWS Setpoint", value="50F", doc_id="doc_york", chunk_id="chunk_york",
                         authority_level="oem_manual", publisher="York"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert len(result) == 1
    assert result[0]["consensus_state"] == "material_conflict"
    assert result[0]["conflict_summary"] is not None


def test_similar_numeric_values_within_tolerance():
    candidates = [
        _make_candidate("Setpoint", value="44.0", doc_id="doc_a", chunk_id="chunk_a"),
        _make_candidate("Setpoint", value="44.2", doc_id="doc_b", chunk_id="chunk_b"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert result[0]["consensus_state"] == "agreed"


def test_numeric_values_outside_tolerance():
    candidates = [
        _make_candidate("Setpoint", value="44.0", doc_id="doc_a", chunk_id="chunk_a"),
        _make_candidate("Setpoint", value="50.0", doc_id="doc_b", chunk_id="chunk_b"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert result[0]["consensus_state"] == "material_conflict"


def test_authority_rank_assignment():
    candidates = [
        _make_candidate("Setpoint", value="44F", doc_id="doc_ashrae", chunk_id="chunk_a",
                         authority_level="industry_standard", publisher="ASHRAE",
                         citation="ASHRAE 90.1-2022 §6.5.3.2"),
        _make_candidate("Setpoint", value="44F", doc_id="doc_trane", chunk_id="chunk_b",
                         authority_level="oem_manual", publisher="Trane"),
    ]
    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert result[0]["highest_authority_level"] == "industry_standard"
    assert result[0]["consensus_state"] == "agreed"


def test_material_conflict_includes_authority_arbitration_result():
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_ashrae", chunk_id="chunk_ashrae",
                         authority_level="industry_standard", publisher="ASHRAE",
                         citation="ASHRAE G36 §5.22"),
        _make_candidate("CHWS Setpoint", value="50F", doc_id="doc_trane", chunk_id="chunk_trane",
                         authority_level="oem_manual", publisher="Trane",
                         citation="Trane Manual p.29"),
    ]

    result = merge_candidates(
        candidates,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    arbitration = result[0]["deviation_justification_json"]["authority_arbitration"]
    assert result[0]["consensus_state"] == "material_conflict"
    assert arbitration["recommended_value"] == "44F"
    assert arbitration["recommended_authority_level"] == "industry_standard"
    assert arbitration["arbitration_rule_applied"] == "rule_3_standard_over_oem"


def test_value_agree_helpers():
    assert _values_agree("44F", "44F") is True
    assert _values_agree("44.0F", "44F") is True   # numeric: both 44.0
    assert _values_agree(44.0, 44.2) is True      # within 5%
    assert _values_agree(44.0, 48.0) is False     # outside 5%
    assert _values_agree(None, None) is True
    assert _values_agree("44F", None) is True   # R3: empty value treated as agree (no data to compare)

def test_temperature_unit_conversion():
    """R4: °F ↔ °C unit normalization."""
    assert _values_agree("95°F", "35°C") is True    # 95F = 35C, exact
    assert _values_agree("95°F", "32°C") is True    # 95F = 35C, diff from 32C is 8.6% within 10%
    assert _values_agree("100°F", "50°C") is False  # 100F = 37.8C, diff from 50C is 24% outside 10%
    assert _values_agree("32°F", "0°C") is True     # 32F = 0C, exact

def test_pressure_unit_conversion():
    """R4: pressure unit normalization."""
    assert _values_agree("120psi", "8.27bar") is True   # 120 psi ≈ 8.27 bar
    assert _values_agree("1MPa", "10bar") is True       # 1 MPa = 10 bar
    assert _values_agree("100kPa", "1bar") is True      # 100 kPa = 1 bar
    assert _values_agree("100psi", "10bar") is False    # 100 psi ≈ 6.89 bar, diff is 31%

def test_empty_value_short_circuit():
    """R3: empty/missing values treated as agree."""
    assert _values_agree("", "") is True
    assert _values_agree("44F", "") is True
    assert _values_agree(None, "some value") is True
    assert _values_agree("none", "N/A") is True


def test_multi_facet_detection():
    """E3: same concept different facets → multi_facet, not conflict."""
    from packages.compiler.cross_source_merger import _compute_consensus_state
    layers = [
        {"value_summary": "Setpoint: 44F", "citation": "Trane CVGF p.29"},
        {"value_summary": "Limit: 38F (cutout)", "citation": "Carrier 19XR p.37"},
    ]
    state, summary = _compute_consensus_state(layers)
    assert state == "multi_facet", f"Expected multi_facet, got {state}"
    assert "setpoint" in (summary or "").lower()


def test_merger_sanity_pathological_split(monkeypatch):
    """E3: defensive sanity forces split of oversized groups (LLM path only)."""
    monkeypatch.setenv("KNOWFABRIC_USE_EMBEDDING_FIRST", "0")
    import importlib, packages.compiler.cross_source_merger as ckmod
    importlib.reload(ckmod)
    from packages.compiler.cross_source_merger import merge_candidates, MERGER_MAX_GROUP_CANDIDATES
    from unittest.mock import patch

    candidates = []
    for i in range(MERGER_MAX_GROUP_CANDIDATES + 2):  # 7 candidates
        candidates.append({
            "title": f"unrelated_param_{i}",
            "structured_payload": {"parameter_name": f"unrelated_param_{i}"},
            "confidence_score": 0.85, "trust_level": "L3",
            "authority_level": "oem_manual", "publisher": "Test",
            "evidence": [{"chunk_id": "c1", "doc_id": "d1", "page_no": 1,
                "evidence_text": "test", "evidence_role": "primary"}],
        })

    # Mock group_and_normalize to return all-in-one bad key
    bad_key = "bad_merge_key"
    name_map = {c["title"]: bad_key for c in candidates}
    with patch.object(ckmod, "group_and_normalize", return_value=name_map):
        merged_result = ckmod.merge_candidates(
            candidates, domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            ontology_class_key="hvac:centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    # Sanity check should split them into multiple KOs
    unique_keys = {ko["canonical_key"] for ko in merged_result}
    assert len(unique_keys) >= MERGER_MAX_GROUP_CANDIDATES, \
        f"Expected ≥{MERGER_MAX_GROUP_CANDIDATES} unique keys after split, got {len(unique_keys)}"
    assert _values_agree(0, 0) is True


def test_consensus_state_scoring():
    layers_single = [{"value_summary": "44F"}]
    state, summary = _compute_consensus_state(layers_single)
    assert state == "single_source"
    assert summary is None

    layers_agreed = [{"value_summary": "44F"}, {"value_summary": "44F"}]
    state, summary = _compute_consensus_state(layers_agreed)
    assert state == "agreed"

    layers_conflict = [{"value_summary": "44F"}, {"value_summary": "50F"}]
    state, summary = _compute_consensus_state(layers_conflict)
    assert state == "material_conflict"


if __name__ == "__main__":
    test_single_candidate_returns_single_source()
    test_two_candidates_same_value_returns_agreed()
    test_different_values_produces_conflict()
    test_similar_numeric_values_within_tolerance()
    test_numeric_values_outside_tolerance()
    test_authority_rank_assignment()
    test_value_agree_helpers()
    test_consensus_state_scoring()
    print("Cross-source merger tests passed")
