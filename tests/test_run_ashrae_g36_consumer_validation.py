"""Tests for ASHRAE G36 consumer validation helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_ashrae_g36_consumer_validation import (
    ConsumerScenario,
    evaluate_scenario,
    keyword_matches,
    matching_items,
    section_matches,
)


def test_section_matches_supports_subsections() -> None:
    assert section_matches("5.20.4.15.a", ("5.20.4.15",))
    assert not section_matches("5.21.4.15", ("5.20.4.15",))


def test_keyword_matches_requires_one_keyword_from_each_group() -> None:
    assert keyword_matches("Cooling SAT reset request", (("sat", "supply air temperature"), ("reset",)))
    assert not keyword_matches("Cooling SAT request", (("sat",), ("reset",)))


def test_evaluate_scenario_passes_with_evidence_backed_section_and_keywords() -> None:
    scenario = ConsumerScenario(
        "test",
        "question",
        "chiller",
        "operational_guidance",
        "operational_sequence",
        ("5.20.2.2",),
        (("plant",), ("enable",)),
    )
    payload = {"items": [item("5.20.2.2", "Chiller Plant Enable Logic", "The plant shall enable.")]}

    result = evaluate_scenario(payload, scenario)

    assert result["status"] == "pass"
    assert result["matched_with_evidence_count"] == 1
    assert result["sample_matches"][0]["section_id"] == "5.20.2.2"


def test_matching_items_ignores_items_without_expected_ko_type() -> None:
    scenario = ConsumerScenario(
        "test",
        "question",
        "ahu",
        "fault_knowledge",
        "fault_diagnostic_rule",
        ("5.6.6.1",),
        (("low", "airflow"),),
    )

    assert matching_items([item("5.6.6.1", "Low Airflow Alarm", "Evidence", ko_type="operational_sequence")], scenario) == []


def item(section_id: str, title: str, evidence: str, *, ko_type: str = "operational_sequence") -> dict:
    return {
        "knowledge_object_type": ko_type,
        "canonical_key": "key",
        "title": title,
        "summary": title,
        "structured_payload": {"section_id": section_id, "title": title},
        "trust_level": "L3",
        "evidence": [{"page_no": 1, "evidence_text": evidence}],
    }
