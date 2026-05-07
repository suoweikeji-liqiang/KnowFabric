"""Tests for ASHRAE G36 parallel section merge helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.merge_ashrae_g36_parallel_sections import (
    build_candidate_input,
    exact_dedup_candidates,
    section_stats,
    verified_paths_from_summary,
)


def test_verified_paths_from_summary_uses_report_parent() -> None:
    summary = {"results": [{"summary": {"report": "output/run_a/REPORT.md"}}]}

    assert verified_paths_from_summary(summary) == [Path("output/run_a/candidates_llm_verified.jsonl")]


def test_exact_dedup_merges_chunks_and_promotes_l4() -> None:
    left = candidate("cand_a", ["chunk_1"], [10], confidence=0.8)
    right = candidate("cand_b", ["chunk_2"], [11], confidence=0.9)

    deduped, duplicates = exact_dedup_candidates([left, right])

    assert len(deduped) == 1
    assert deduped[0]["candidate_id"] == "cand_b"
    assert deduped[0]["source_chunk_ids"] == ["chunk_1", "chunk_2"]
    assert deduped[0]["source_page_nos"] == [10, 11]
    assert deduped[0]["trust_level"] == "L4"
    assert deduped[0]["global_dedupe"]["exact_group_size"] == 2
    assert [row["candidate_id"] for row in duplicates] == ["cand_a"]


def test_section_stats_extracts_counts_from_parallel_summary() -> None:
    summary = {
        "results": [
            {
                "section": "5.15",
                "elapsed_seconds": 12.5,
                "summary": {"raw": 62, "anchor_passed": 1, "verified": 1, "L4": 0, "report": "r.md"},
            }
        ]
    }

    assert section_stats(summary)[0] == {
        "section": "5.15",
        "verified": 1,
        "l4": 0,
        "raw": 62,
        "anchor_passed": 1,
        "elapsed_seconds": 12.5,
        "report": "r.md",
    }


def test_build_candidate_input_normalizes_equipment_class_for_review_packs() -> None:
    row = candidate("cand_ahu", ["chunk_1"], [10], confidence=0.9)
    row["structured_payload_candidate"]["section_id"] = "5.22.6.1"
    report = {
        "source_summary_path": "workspace/summary.json",
        "raw_candidate_count": 1,
        "exact_duplicate_count": 0,
        "fuzzy_duplicate_group_count": 0,
        "trust_breakdown": {"L4": 1, "L3": 0},
    }

    payload = build_candidate_input(report, [row])

    assert payload["metadata"]["total_candidates"] == 1
    assert payload["candidate_entries"][0]["equipment_class_candidate"]["equipment_class_id"] == "ahu"


def candidate(candidate_id: str, chunks: list[str], pages: list[int], *, confidence: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "canonical_key_candidate": "ashrae:g36:operational_sequence:5_20_2_2:plant_enable",
        "knowledge_object_type": "operational_sequence",
        "confidence_score": confidence,
        "trust_level": "L3",
        "source_chunk_ids": chunks,
        "source_page_nos": pages,
        "structured_payload_candidate": {
            "knowledge_type": "operational_sequence",
            "section_id": "5.20.2.2",
            "title": "Plant Enable",
            "summary": "Enable the plant.",
        },
    }
