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


def test_value_agree_helpers():
    assert _values_agree("44F", "44F") is True
    assert _values_agree("44.0F", "44F") is True   # numeric: both 44.0
    assert _values_agree(44.0, 44.2) is True      # within 5%
    assert _values_agree(44.0, 48.0) is False     # outside 5%
    assert _values_agree(None, None) is True
    assert _values_agree("44F", None) is False
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
