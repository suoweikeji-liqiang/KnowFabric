from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts.run_ashrae_g36_remaining_batches import (
    Batch,
    parse_batches,
    render_summary,
    run_batch,
)


def test_parse_default_batches_excludes_general_by_default() -> None:
    batches = parse_batches(None)
    assert [batch.name for batch in batches] == ["remaining_high_value"]
    assert batches[0].sections == ("5.2", "5.3", "5.17", "5.18", "5.19", "5.22")


def test_parse_custom_batches() -> None:
    batches = parse_batches("zones=5.2,5.3;fcu=5.22")
    assert [batch.name for batch in batches] == ["zones", "fcu"]
    assert batches[1].sections == ("5.22",)


def test_run_batch_dry_run_builds_extract_command(tmp_path, monkeypatch) -> None:
    commands = []

    def fake_run_command(cmd, *, dry_run=False):
        commands.append((cmd, dry_run))

    monkeypatch.setattr("scripts.run_ashrae_g36_remaining_batches.run_command", fake_run_command)
    args = Namespace(
        doc_id="doc_g36",
        extract_backend="extract",
        judge_backend="judge",
        extract_output_dir="output/g36",
        budget_rmb_per_batch=12.0,
        max_candidates_per_section=9,
        min_trust_level="L3",
        extract_mode="bundle",
    )

    result = run_batch(args, Batch("zones", ("5.2", "5.3"), "test"), tmp_path, dry_run=True)

    assert result["dry_run"] is True
    assert result["sections"] == ["5.2", "5.3"]
    command = commands[0][0]
    assert "scripts/run_standard_import_pipeline.py" in command
    assert "--extract" in command
    assert "5.2,5.3" in command
    assert "--extract-mode" in command
    assert "bundle" in command


def test_run_batch_orchestrates_extract_review_apply(tmp_path, monkeypatch) -> None:
    commands = []
    root = tmp_path / "root"
    workspace = root / "zones"
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (workspace).mkdir(parents=True)
    (workspace / "review_packs").mkdir()
    (workspace / "standard_import_pipeline_summary.json").write_text(
        json.dumps({"source_run_dir": str(run_dir), "apply_summary": {"applied": 1}}),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps({"judge_accepted": 1, "judge_rejected": 0, "final_by_type": {"operational_sequence": 1}, "gates": {"G1": {"status": "PASS"}}}),
        encoding="utf-8",
    )
    (workspace / "review_packs" / "api_smoke_report.json").write_text(
        json.dumps({"summary": {"targets": 1, "passed": 1, "failed": 0}}),
        encoding="utf-8",
    )

    def fake_run_command(cmd, *, dry_run=False):
        commands.append(cmd)

    monkeypatch.setattr("scripts.run_ashrae_g36_remaining_batches.run_command", fake_run_command)
    args = Namespace(
        doc_id="doc_g36",
        extract_backend="extract",
        judge_backend="judge",
        extract_output_dir="output/g36",
        budget_rmb_per_batch=12.0,
        max_candidates_per_section=9,
        min_trust_level="L3",
        extract_mode="bundle",
    )

    result = run_batch(args, Batch("zones", ("5.2",), "test"), root)

    assert len(commands) == 3
    assert "scripts/apply_model_review_to_standard_packs.py" in commands[1]
    assert "--apply" in commands[2]
    assert result["judge_accepted"] == 1
    assert result["api_smoke_summary"]["passed"] == 1


def test_render_summary_includes_smoke_counts() -> None:
    rendered = render_summary(
        {
            "generated_at": "2026-05-06T00:00:00+00:00",
            "dry_run": False,
            "batch_count": 1,
            "results": [
                {
                    "batch": "zones",
                    "sections": ["5.2"],
                    "judge_accepted": 3,
                    "judge_rejected": 1,
                    "l4_final": 2,
                    "l3_final": 1,
                    "api_smoke_summary": {"targets": 1, "passed": 1},
                    "report_path": "output/run/REPORT.md",
                }
            ],
        }
    )
    assert "| `zones` | 5.2 | 3 | 1 | 2/1 | 1/1 | `output/run/REPORT.md` |" in rendered
