"""Tests for parameter_spec vertical runner prompt helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, DocumentPage
from scripts.run_parameter_spec_vertical import anchor_to_chunks, build_judge_messages


def test_build_judge_messages_accepts_mode_and_active_setpoints_but_rejects_io_labels() -> None:
    candidate = {
        "structured_payload_candidate": {
            "parameter_name": "Chilled Water Reset",
            "value": None,
            "unit": None,
        },
        "evidence_quote": "Chilled Water Reset Return/Constant Return/Outdoor/None",
        "source_page_nos": [25, 29],
    }

    messages = build_judge_messages(candidate)
    user_prompt = messages[1]["content"]
    assert "Mode selections count even without a numeric value" in user_prompt
    assert "active/arbitrated setpoint shown on a control panel table" in user_prompt
    assert "External Chilled Water Setpoint" in user_prompt
    assert "Do not reject a real external setpoint merely because it is implemented through an analog input" in user_prompt
    assert "Relay Output Status" in user_prompt
    assert "1A17 Analog Input/Output Module" in user_prompt
    assert "Display Units" in user_prompt
    assert "Keypad and Display Lockout" in user_prompt


def test_anchor_to_chunks_repairs_quote_with_verbatim_parameter_label() -> None:
    chunk = ContentChunk(
        chunk_id="chunk_25",
        doc_id="doc_trane",
        page_id="page_25",
        page_no=25,
        chunk_index=0,
        cleaned_text="Active Current Limit Setpoint Arbitration\nFront Panel 100% Active/Blank",
        text_excerpt="Active Current Limit Setpoint Arbitration",
        chunk_type="table",
    )
    page = DocumentPage(
        page_id="page_25",
        doc_id="doc_trane",
        page_no=25,
        cleaned_text=chunk.cleaned_text,
        page_type="control_panel",
    )
    candidate = {
        "evidence_quote": "Active Current Limit Setpoint 100%",
        "structured_payload_candidate": {"parameter_name": "Active Current Limit Setpoint"},
    }

    anchored, rejected = anchor_to_chunks([candidate], [(chunk, page, object())])

    assert rejected == []
    assert anchored[0]["evidence_quote"] == "Active Current Limit Setpoint"
    assert anchored[0]["source_chunk_ids"] == ["chunk_25"]
    assert anchored[0]["anchor_repair_reason"] == "evidence_quote replaced with verbatim parameter_name label"
