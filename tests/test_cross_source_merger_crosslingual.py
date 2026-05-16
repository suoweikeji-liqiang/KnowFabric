"""T1 cross-lingual merger plumbing test (docs/35 §T1.4)."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import merge_candidates


def _make_candidate(title, value, authority_level="oem_manual", publisher="Trane",
                    citation="Manual p.1", doc_id="doc_001", chunk_id="chunk_001"):
    return {
        "title": title,
        "summary": f"Summary for {title}",
        "structured_payload": {"parameter_name": title, "value": value},
        "confidence_score": 0.9,
        "trust_level": "L4",
        "review_status": "published",
        "authority_level": authority_level,
        "publisher": publisher,
        "citation": citation,
        "doc_id": doc_id,
        "evidence": [{
            "chunk_id": chunk_id, "doc_id": doc_id, "page_id": "p1",
            "page_no": 1, "evidence_text": f"{value} setpoint",
            "evidence_role": "primary",
        }],
    }


def test_crosslingual_merger_with_llm_grouping():
    """T1: Two candidates with different-language names → merged into 1 KO with 2 layers."""
    candidates = [
        _make_candidate("Active Chilled Water Setpoint", value="44F",
                        authority_level="oem_manual", publisher="Trane",
                        citation="Trane CVGF p.29", doc_id="doc_trane", chunk_id="ch_trane"),
        _make_candidate("动态冷冻水设定", value="44F",
                        authority_level="oem_manual", publisher="McQuay",
                        citation="McQuay Manual p.12", doc_id="doc_mcquay", chunk_id="ch_mcquay"),
    ]

    mock_groups = [{
        "canonical_key": "hvac:centrifugal_chiller:parameter:chw_supply_temp_setpoint",
        "normalized_name": "chw_supply_temp_setpoint",
        "member_names": ["Active Chilled Water Setpoint", "动态冷冻水设定"],
        "rationale": "Same physical quantity in EN and ZH",
    }]

    with patch("packages.compiler.cross_source_merger.group_and_normalize", return_value={
        "Active Chilled Water Setpoint": mock_groups[0]["canonical_key"],
        "动态冷冻水设定": mock_groups[0]["canonical_key"],
    }):
        merged = merge_candidates(
            candidates,
            domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            ontology_class_key="hvac:centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    assert len(merged) == 1, f"Expected 1 merged KO, got {len(merged)}"
    ko = merged[0]
    layers = ko["authority_summary_json"]["layers"]
    assert len(layers) == 2, f"Expected 2 authority layers, got {len(layers)}"
    assert ko["consensus_state"] == "agreed", f"Expected agreed, got {ko['consensus_state']}"
    publishers = {l["publisher"] for l in layers}
    assert publishers == {"Trane", "McQuay"}, f"Expected Trane+McQuay, got {publishers}"


def test_crosslingual_fallback_to_mechanical_when_llm_fails():
    """T1: LLM grouping fails → mechanical fallback still works (no crash)."""
    candidates = [
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_a", chunk_id="c_a"),
        _make_candidate("CHWS Setpoint", value="44F", doc_id="doc_b", chunk_id="c_b"),
    ]

    with patch("packages.compiler.cross_source_merger.group_and_normalize",
               side_effect=RuntimeError("LLM unavailable")):
        merged = merge_candidates(
            candidates,
            domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            ontology_class_key="hvac:centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    # Mechanical fallback: same name → same slug → 1 merged KO
    assert len(merged) == 1
    assert merged[0]["consensus_state"] == "agreed"
    assert len(merged[0]["authority_summary_json"]["layers"]) == 2


def test_crosslingual_different_values_produces_conflict():
    """T1: Cross-lingual merge with different values → correct conflict state."""
    candidates = [
        _make_candidate("Chilled Water Setpoint", value="44F", publisher="Trane",
                        doc_id="doc_trane", chunk_id="c_t"),
        _make_candidate("冷冻水设定温度", value="50F", publisher="Daikin",
                        doc_id="doc_daikin", chunk_id="c_d"),
    ]

    mock_groups = [{
        "canonical_key": "hvac:centrifugal_chiller:parameter:chw_setpoint",
        "member_names": ["Chilled Water Setpoint", "冷冻水设定温度"],
    }]

    with patch("packages.compiler.cross_source_merger.group_and_normalize", return_value={
        "Chilled Water Setpoint": mock_groups[0]["canonical_key"],
        "冷冻水设定温度": mock_groups[0]["canonical_key"],
    }):
        merged = merge_candidates(
            candidates,
            domain_id="hvac",
            equipment_class_id="centrifugal_chiller",
            ontology_class_key="hvac:centrifugal_chiller",
            knowledge_object_type="parameter_spec",
        )

    assert len(merged) == 1
    assert merged[0]["consensus_state"] == "value_disagreement"
    assert len(merged[0]["authority_summary_json"]["layers"]) == 2
