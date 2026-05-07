"""Tests for ASHRAE G36 evidence quality audit helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.audit_ashrae_g36_evidence_quality import audit_row, build_report, is_g36_row


def test_is_g36_row_accepts_standard_id_or_canonical_key() -> None:
    assert is_g36_row(row(applicability_json={"standard_id": "ASHRAE Guideline 36-2021"}))
    assert is_g36_row(row(canonical_key="ashrae:g36:operational_sequence:key"))
    assert not is_g36_row(row(canonical_key="vendor:key", applicability_json={}))


def test_audit_row_flags_heading_only_evidence_when_no_strong_evidence() -> None:
    finding = audit_row(
        row(),
        [evidence("5.8.8.1. Cooling SAT Reset Requests")],
    )

    assert finding is not None
    assert "weak evidence_quote: section heading without supporting rule" in finding["reasons"]


def test_audit_row_passes_when_any_evidence_is_strong() -> None:
    finding = audit_row(
        row(),
        [
            evidence("5.8.8.1. Cooling SAT Reset Requests"),
            evidence("If the Cooling Loop is greater than 95%, send 1 request until the Cooling Loop is less than 85%."),
        ],
    )

    assert finding is None


def test_build_report_counts_weak_rows() -> None:
    rows = [row(knowledge_object_id="ko_weak")]
    report = build_report(rows, {"ko_weak": [evidence("5.8.8.1. Cooling SAT Reset Requests")]})

    assert report["row_count"] == 1
    assert report["weak_row_count"] == 1
    assert report["by_type"] == {"operational_sequence": 1}


def row(**overrides):
    values = {
        "knowledge_object_id": "ko_1",
        "canonical_key": "ashrae:g36:operational_sequence:5_8_8_1:cooling_sat_reset_requests",
        "domain_id": "hvac",
        "ontology_class_id": "ahu",
        "knowledge_object_type": "operational_sequence",
        "title": "Cooling SAT Reset Requests",
        "structured_payload_json": {"section_id": "5.8.8.1", "title": "Cooling SAT Reset Requests"},
        "applicability_json": {"standard_id": "ASHRAE Guideline 36-2021"},
        "trust_level": "L3",
        "confidence_score": 0.9,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def evidence(text: str):
    return SimpleNamespace(page_no=87, chunk_id="chunk_1", evidence_text=text)
