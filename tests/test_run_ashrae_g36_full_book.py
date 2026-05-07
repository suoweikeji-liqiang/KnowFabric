"""Tests for the ASHRAE Guideline 36 full-book runner helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import OpenAICompatibleBackend
from packages.db.models import ContentChunk
from scripts.run_ashrae_g36_full_book import (
    Guideline36BatchJudgeItem,
    architecture_instruction,
    apply_batch_verdicts,
    assemble_full_book_text,
    backend_with_overrides,
    build_batch_judge_messages,
    build_context_sections,
    build_full_book_extract_messages,
    build_g3_gate,
    candidate_in_focus,
    filter_weak_evidence_candidates,
    focus_text_block,
    input_manifest,
    make_focused_run_id,
    parse_focus_sections,
    source_text_label,
)


def test_assemble_full_book_text_uses_chunk_anchors() -> None:
    chunk = ContentChunk(
        chunk_id="chunk_1",
        doc_id="doc_g36",
        page_id="page_10",
        page_no=10,
        chunk_index=2,
        cleaned_text="5.1.14. Trim & Respond logic.",
        text_excerpt="Trim & Respond",
        chunk_type="paragraph",
    )

    text = assemble_full_book_text([chunk])

    assert "[[page=10 chunk_id=chunk_1 chunk_index=2]]" in text
    assert "5.1.14. Trim & Respond logic." in text


def test_full_book_prompt_requires_whole_book_context_and_verbatim_quotes() -> None:
    class Doc:
        file_name = "ashrae_guideline_36.pdf"

    messages = build_full_book_extract_messages(Doc(), "5.1 text")

    assert "entire standard in one pass" in messages[0]["content"]
    assert "whole-book context" in messages[0]["content"]
    assert "evidence_quote MUST be a verbatim contiguous substring" in messages[0]["content"]
    assert "section heading alone" in messages[0]["content"]
    assert "architecture: full_book" in messages[1]["content"]


def test_full_book_prompt_can_focus_on_sections_with_full_book_context() -> None:
    class Doc:
        file_name = "ashrae_guideline_36.pdf"

    messages = build_full_book_extract_messages(Doc(), "5.20 text", focus_sections=["5.20"], focus_text="5.20 focused text")

    assert "Extract ONLY knowledge whose primary section_id equals one of these sections" in messages[0]["content"]
    assert "Use the rest of the manual only as context" in messages[0]["content"]
    assert "focus_sections: 5.20" in messages[1]["content"]
    assert "FOCUS SECTION TEXT" in messages[1]["content"]
    assert "5.20 focused text" in messages[1]["content"]


def test_section_context_prompt_uses_context_pack_and_focus_text() -> None:
    class Doc:
        file_name = "ashrae_guideline_36.pdf"

    messages = build_full_book_extract_messages(
        Doc(),
        "3 definitions\n5.1 common rules",
        focus_sections=["5.22"],
        focus_text="5.22 focused text",
        input_mode="section_context",
    )

    assert "focused chapter/section" in messages[0]["content"]
    assert "context pack is CONTEXT ONLY" in messages[0]["content"]
    assert "evidence_quote must be copied from FOCUS SECTION TEXT" in messages[0]["content"]
    assert "architecture: section_context" in messages[1]["content"]
    assert "CONTEXT ONLY STANDARD PACK" in messages[1]["content"]
    assert "5.22 focused text" in messages[1]["content"]


def test_section_context_helpers_exclude_focus_from_context() -> None:
    assert architecture_instruction("section_context").startswith("You are a senior HVAC controls engineer")
    assert source_text_label("section_context") == "CONTEXT ONLY STANDARD PACK with chunk/page anchors"
    assert build_context_sections(["5.1"], "3,5.1") == ["3"]
    assert build_context_sections(["5.1.14"], "3,5.1") == ["3"]
    assert build_context_sections(["5.22"], "3,5.1") == ["3", "5.1"]


def test_input_manifest_tracks_context_and_focus_text_separately() -> None:
    manifest = input_manifest("section_context", "context text", "focus text")

    assert manifest["input_mode"] == "section_context"
    assert manifest["source_text_chars"] == len("context text")
    assert manifest["focus_text_chars"] == len("focus text")
    assert manifest["total_tokens_estimated"] == manifest["source_tokens_estimated"] + manifest["focus_tokens_estimated"]


def test_focus_section_helpers_filter_subsections() -> None:
    assert parse_focus_sections("5.20, 5.21") == ["5.20", "5.21"]
    assert candidate_in_focus(candidate_model("5.20.2.2"), ["5.20"])
    assert not candidate_in_focus(candidate_model("5.21.2.2"), ["5.20"])


def test_make_focused_run_id_adds_section_suffix(monkeypatch) -> None:
    monkeypatch.setattr("scripts.run_ashrae_g36_full_book.make_run_id", lambda file_name: "stamp_manual_ashrae_g36")

    assert make_focused_run_id("manual.pdf", ["5.20"]) == "stamp_manual_ashrae_g36_fullbook_sections_5_20"


def test_focus_text_block_is_omitted_when_empty() -> None:
    assert focus_text_block("") == ""
    assert "FOCUS SECTION TEXT" in focus_text_block("5.1 text")


def test_focused_g3_gate_requires_verified_not_l4() -> None:
    gate = build_g3_gate([{"trust_level": "L3"}], 0, ["5.1"])

    assert gate["status"] == "PASS"
    assert gate["requirement"] == "focused section run produced at least one verified candidate"


def test_batch_judge_prompt_contains_all_candidate_ids() -> None:
    messages = build_batch_judge_messages([candidate("cand_1"), candidate("cand_2")])

    assert "Return exactly one verdict per candidate_id" in messages[0]["content"]
    assert '"candidate_id": "cand_1"' in messages[1]["content"]
    assert '"candidate_id": "cand_2"' in messages[1]["content"]


def test_apply_batch_verdicts_accepts_and_rejects_missing_verdicts() -> None:
    candidates = [candidate("cand_accept"), candidate("cand_missing")]
    verdicts = [
        Guideline36BatchJudgeItem(
            candidate_id="cand_accept",
            is_valid_guideline36_knowledge=True,
            reason="grounded operational sequence",
        )
    ]

    accepted, rejected = apply_batch_verdicts(candidates, verdicts)

    assert accepted[0]["candidate_id"] == "cand_accept"
    assert accepted[0]["judge_verdict"] == "accepted"
    assert rejected[0]["candidate_id"] == "cand_missing"
    assert rejected[0]["judge_category"] == "missing_verdict"


def test_backend_with_overrides_sets_large_max_tokens() -> None:
    backend = OpenAICompatibleBackend(
        name="deepseek-v4-pro-judge",
        api_base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        request_options={"temperature": 1.0, "max_tokens": 1200},
    )

    updated = backend_with_overrides(backend, max_tokens=80_000, timeout_seconds=900)

    assert updated.request_options["max_tokens"] == 80_000
    assert updated.request_options["temperature"] == 1.0
    assert updated.timeout_seconds == 900


def test_filter_weak_evidence_rejects_heading_only_candidate() -> None:
    row = candidate("cand_heading")
    row["evidence_quote"] = "5.20.2.2 Chiller Plant Enable Logic"
    row["structured_payload_candidate"]["title"] = "Chiller Plant Enable Logic"

    passed, rejected = filter_weak_evidence_candidates([row])

    assert passed == []
    assert rejected[0]["rejection_reason"] == "weak evidence_quote: section heading without supporting rule"


def test_filter_weak_evidence_accepts_complete_rule_candidate() -> None:
    row = candidate("cand_rule")
    row["evidence_quote"] = (
        "The chiller plant shall be enabled when the chilled water plant enable command is true."
    )

    passed, rejected = filter_weak_evidence_candidates([row])

    assert rejected == []
    assert passed[0]["candidate_id"] == "cand_rule"


def test_filter_weak_evidence_rejects_introductory_fragment() -> None:
    row = candidate("cand_intro")
    row["evidence_quote"] = "5.20.10.5. For each chiller, when the WSE is disabled, map loop output as follows:"

    passed, rejected = filter_weak_evidence_candidates([row])

    assert passed == []
    assert rejected[0]["rejection_reason"] == "weak evidence_quote: introductory fragment without complete rule"


def test_filter_weak_evidence_rejects_fault_without_specific_fc() -> None:
    row = candidate("cand_fault")
    row["knowledge_object_type"] = "fault_diagnostic_rule"
    row["structured_payload_candidate"]["title"] = "CHW Plant AFDD - FC#18: Too many OS changes"
    row["evidence_quote"] = "5.20.18.6. The following are potential Fault Conditions that can be evaluated."

    passed, rejected = filter_weak_evidence_candidates([row])

    assert passed == []
    assert rejected[0]["rejection_reason"] == "weak evidence_quote: fault evidence lacks the specific FC item"


def candidate(candidate_id: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "knowledge_object_type": "operational_sequence",
        "structured_payload_candidate": {
            "title": "Trim and Respond",
            "section_id": "5.1.14",
            "summary": "Reset setpoint using Trim and Respond logic.",
        },
        "evidence_quote": "Trim & Respond logic shall reset the setpoint.",
        "source_page_nos": [46],
    }


def candidate_model(section_id: str):
    from scripts.run_ashrae_guideline36_vertical import Guideline36Candidate

    return Guideline36Candidate(
        knowledge_type="operational_sequence",
        title="Rule",
        section_id=section_id,
        summary="Rule summary",
        evidence_quote="The system shall enable when the command is true.",
        confidence=0.9,
    )
