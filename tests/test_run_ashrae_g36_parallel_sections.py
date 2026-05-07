"""Tests for ASHRAE G36 parallel focus-section runner helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_ashrae_g36_parallel_sections import (
    build_command,
    build_summary,
    parse_sections,
    parse_summary_line,
    section_sort_key,
)


def test_parse_sections_supports_all_and_commas() -> None:
    assert parse_sections("5.20, 5.21") == ["5.20", "5.21"]
    assert parse_sections("all")[0] == "5.1"
    assert parse_sections("all")[-1] == "5.22"


def test_build_command_uses_focus_section_and_fullbook_runner() -> None:
    args = args_fixture()

    command = build_command(args, "5.20", Path("workspace/run"))

    assert command[1] == "scripts/run_ashrae_g36_full_book.py"
    assert "--focus-sections" in command
    assert command[command.index("--focus-sections") + 1] == "5.20"
    assert command[command.index("--input-mode") + 1] == "section_context"
    assert command[command.index("--context-sections") + 1] == "3,5.1"


def test_parse_summary_line_extracts_counts_and_report() -> None:
    parsed = parse_summary_line("summary raw=130 anchor_passed=130 verified=75 L4=18 cost=¥0.4544 report=out/REPORT.md")

    assert parsed["raw"] == 130
    assert parsed["verified"] == 75
    assert parsed["L4"] == 18
    assert parsed["cost"] == 0.4544
    assert parsed["report"] == "out/REPORT.md"


def test_build_summary_totals_passed_jobs() -> None:
    args = args_fixture()
    results = [
        {"section": "5.1", "status": "pass", "summary": {"verified": 3, "L4": 1}},
        {"section": "5.2", "status": "fail", "summary": {"verified": 9, "L4": 9}},
    ]

    summary = build_summary(args, results)

    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["total_verified"] == 3
    assert summary["total_l4"] == 1


def test_section_sort_key_sorts_numerically() -> None:
    assert sorted(["5.10", "5.2"], key=section_sort_key) == ["5.2", "5.10"]


def args_fixture() -> argparse.Namespace:
    return argparse.Namespace(
        doc_id="doc_g36",
        extract_backend="extract",
        judge_backend="judge",
        extract_output_dir="output",
        budget_rmb_per_section=10.0,
        extract_max_tokens=80_000,
        judge_max_tokens=50_000,
        extract_timeout_seconds=1200,
        judge_timeout_seconds=1200,
        max_extract_seconds=1200,
        target_candidates_per_section=40,
        max_raw_candidates_per_section=80,
        workers=2,
        input_mode="section_context",
        context_sections="3,5.1",
        dry_run=False,
    )
