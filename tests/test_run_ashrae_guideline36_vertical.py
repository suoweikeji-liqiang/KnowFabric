"""Tests for the ASHRAE Guideline 36 vertical runner helpers."""

from __future__ import annotations

import http.client
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_ashrae_guideline36_vertical import (
    Guideline36ExtractionResponse,
    SectionUnit,
    anchor_candidates,
    build_summary,
    build_extract_messages,
    canonical_key,
    request_json_completion_with_retry,
    trim_to_section_start,
)
from packages.db.models import ContentChunk


def test_trim_to_section_start_drops_previous_section_tail() -> None:
    text = "5.20.18.8. Previous tail\n\n5.21.1. See Section 3.1.8\n5.21.2. Plant Enable/Disable"

    trimmed = trim_to_section_start(text, "5.21")

    assert trimmed.startswith("5.21.1.")
    assert "Previous tail" not in trimmed


def test_extract_prompt_scopes_to_official_guideline36_section() -> None:
    unit = SectionUnit(
        requested_section="5.1.14",
        section_id="5.1.14",
        section_title="5.1.14. Trim & Respond Set-Point Reset Logic",
        start_page=46,
        end_page=49,
        text="5.1.14. Trim & Respond logic resets a setpoint.",
        chunk_ids=["chunk_1"],
    )

    messages = build_extract_messages(unit)
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]

    assert "official ASHRAE Guideline 36 knowledge" in system_prompt
    assert "operational_sequence" in system_prompt
    assert "fault_diagnostic_rule" in system_prompt
    assert "commissioning_step" in system_prompt
    assert "evidence_quote MUST be a SHORT verbatim contiguous substring" in system_prompt
    assert "Do not use ellipses" in system_prompt
    assert "standard_id: ASHRAE Guideline 36-2021" in user_prompt
    assert "requested_section: 5.1.14" in user_prompt


def test_canonical_key_includes_section_and_type() -> None:
    key = canonical_key(
        {
            "knowledge_type": "operational_sequence",
            "section_id": "5.20.2.2",
            "title": "Enable Chiller Plant",
        }
    )

    assert key == "ashrae:g36:operational_sequence:5_20_2_2:enable_chiller_plant"


def test_extraction_response_accepts_null_configurable_values() -> None:
    """Model JSON sometimes returns null for optional list fields; normalize it."""

    response = Guideline36ExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "knowledge_type": "operational_sequence",
                    "title": "AHU System Modes",
                    "section_id": "5.15",
                    "summary": "AHU modes follow the served Zone Group mode.",
                    "configurable_values": None,
                    "evidence_quote": "AHU system modes are the same as the mode of the Zone Group served by the system.",
                    "confidence": 0.9,
                }
            ]
        }
    )

    assert response.candidates[0].configurable_values == []


def test_extraction_response_uses_contract_commissioning_step_type() -> None:
    response = Guideline36ExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "knowledge_type": "commissioning_step",
                    "title": "Testing Overrides",
                    "section_id": "5.16.15",
                    "summary": "Provide testing override points.",
                    "evidence_quote": "Provide software switches for testing and commissioning.",
                    "confidence": 0.9,
                }
            ]
        }
    )

    assert response.candidates[0].knowledge_type == "commissioning_step"


def test_json_completion_retry_handles_empty_content_once(monkeypatch) -> None:
    """Transient empty LLM content should not abort a long standards run."""

    calls = {"count": 0}

    def fake_request(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("LLM compile returned empty content")
        return {"candidates": []}

    monkeypatch.setattr("scripts.run_ashrae_guideline36_vertical._request_json_completion", fake_request)

    result = request_json_completion_with_retry(
        [{"role": "user", "content": "x"}],
        object(),
        response_format={"type": "json_object"},
        recorder=lambda payload: None,
    )

    assert result == {"candidates": []}
    assert calls["count"] == 2


def test_json_completion_retry_handles_incomplete_read_once(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_request(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise http.client.IncompleteRead(b"")
        return {"candidates": []}

    monkeypatch.setattr("scripts.run_ashrae_guideline36_vertical._request_json_completion", fake_request)

    result = request_json_completion_with_retry(
        [{"role": "user", "content": "x"}],
        object(),
        response_format={"type": "json_object"},
        recorder=lambda payload: None,
    )

    assert result == {"candidates": []}
    assert calls["count"] == 2


def test_wallclock_gate_scales_with_llm_call_count() -> None:
    class Args:
        sections = "5.7,5.8"

    class Doc:
        file_name = "ashrae_guideline_36.pdf"
        doc_id = "doc_g36"

    candidate = {
        "structured_payload_candidate": {"section_id": "5.7.5", "title": "Control"},
        "knowledge_object_type": "operational_sequence",
        "canonical_key_candidate": "key",
    }
    raw_judge = [{"usage": {}} for _ in range(80)]

    summary = build_summary(
        Args(),
        Doc(),
        [],
        {"total_seconds": 1400},
        ([candidate], [candidate], [candidate], [], [], [], raw_judge),
        ((type("Backend", (), {"name": "extract", "model": "model"})()), (type("Backend", (), {"name": "judge", "model": "model"})())),
        ({}, {}),
    )

    assert summary["gates"]["G4"]["status"] == "PASS"
    assert summary["gates"]["G4"]["limit_seconds"] == 1600


def test_anchor_candidates_repairs_to_section_heading_line() -> None:
    chunk = ContentChunk(
        chunk_id="chunk_g36",
        doc_id="doc_g36",
        page_id="page_46",
        page_no=46,
        chunk_index=0,
        cleaned_text="5.1.14.4. Trim & Respond logic shall reset the setpoint within the range SPmin to SPmax.",
        text_excerpt="5.1.14.4. Trim & Respond logic",
        chunk_type="paragraph",
    )
    candidate = {
        "candidate_id": "cand_1",
        "evidence_quote": "Trim & Respond logic resets the setpoint ...",
        "structured_payload_candidate": {"section_id": "5.1.14.4", "title": "T&R reset"},
        "knowledge_object_type": "operational_sequence",
        "canonical_key_candidate": "ashrae:g36:operational_sequence:5_1_14_4:t_r_reset",
    }

    anchored, rejected = anchor_candidates([candidate], [chunk])

    assert rejected == []
    assert anchored[0]["evidence_quote"].startswith("5.1.14.4.")
    assert anchored[0]["anchor_repair_reason"] == "evidence_quote replaced with verbatim section heading line"


def test_anchor_candidates_repairs_weak_section_only_quote() -> None:
    chunk = ContentChunk(
        chunk_id="chunk_g36",
        doc_id="doc_g36",
        page_id="page_199",
        page_no=199,
        chunk_index=0,
        cleaned_text="5.20.5.2.\nCHWST setpoint shall be reset using Trim & Respond logic.",
        text_excerpt="5.20.5.2.",
        chunk_type="paragraph",
    )
    candidate = {
        "candidate_id": "cand_1",
        "evidence_quote": "5.20.5.2.",
        "structured_payload_candidate": {"section_id": "5.20.5.2", "title": "CHWST reset"},
        "knowledge_object_type": "operational_sequence",
        "canonical_key_candidate": "ashrae:g36:operational_sequence:5_20_5_2:chwst_reset",
    }

    anchored, rejected = anchor_candidates([candidate], [chunk])

    assert rejected == []
    assert "CHWST setpoint shall be reset" in anchored[0]["evidence_quote"]


def test_anchor_candidates_repairs_weak_quote_from_next_chunk_line() -> None:
    first = ContentChunk(
        chunk_id="chunk_heading",
        doc_id="doc_g36",
        page_id="page_199",
        page_no=199,
        chunk_index=0,
        cleaned_text="5.20.5.2.",
        text_excerpt="5.20.5.2.",
        chunk_type="paragraph",
    )
    second = ContentChunk(
        chunk_id="chunk_body",
        doc_id="doc_g36",
        page_id="page_199",
        page_no=199,
        chunk_index=1,
        cleaned_text="Differential Pressure Controlled Loops: Chilled water supply temperature setpoint CHWSTsp",
        text_excerpt="Differential Pressure Controlled Loops",
        chunk_type="paragraph",
    )
    candidate = {
        "candidate_id": "cand_1",
        "evidence_quote": "5.20.5.2.",
        "structured_payload_candidate": {"section_id": "5.20.5.2", "title": "CHWST reset"},
        "knowledge_object_type": "operational_sequence",
        "canonical_key_candidate": "ashrae:g36:operational_sequence:5_20_5_2:chwst_reset",
    }

    anchored, rejected = anchor_candidates([candidate], [first, second])

    assert rejected == []
    assert "Differential Pressure Controlled Loops" in anchored[0]["evidence_quote"]
