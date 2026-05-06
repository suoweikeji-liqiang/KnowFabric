"""Tests for the ASHRAE Guideline 36 full-book runner helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import OpenAICompatibleBackend
from packages.db.models import ContentChunk
from scripts.run_ashrae_g36_full_book import (
    Guideline36BatchJudgeItem,
    apply_batch_verdicts,
    assemble_full_book_text,
    backend_with_overrides,
    build_batch_judge_messages,
    build_full_book_extract_messages,
    filter_weak_evidence_candidates,
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
    assert "architecture: single-call full-book extraction" in messages[1]["content"]


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
