#!/usr/bin/env python3
"""Run remaining ASHRAE Guideline 36 extraction/import batches end to end."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DOC_ID = "doc_4bbd3703c4f84be4"
DEFAULT_EXTRACT_BACKEND = "deepseek-parameter-spec"
DEFAULT_JUDGE_BACKEND = "deepseek-v4-pro-judge"


@dataclass(frozen=True)
class Batch:
    name: str
    sections: tuple[str, ...]
    description: str


DEFAULT_BATCHES = (
    Batch(
        "remaining_high_value",
        ("5.2", "5.3", "5.17", "5.18", "5.19", "5.22"),
        "All remaining high-value G36 sections in one DeepSeek 1M-context extraction call.",
    ),
)

GENERAL_BATCH = Batch(
    "general_controls",
    ("5.1",),
    "General control philosophy and cross-cutting alarm/control-loop rules. May duplicate the prior 5.1.14 run.",
)


def parse_batches(value: str | None, *, include_general: bool = False) -> list[Batch]:
    if not value:
        batches = list(DEFAULT_BATCHES)
        if include_general:
            batches.append(GENERAL_BATCH)
        return batches
    result = []
    for item in value.split(";"):
        if not item.strip():
            continue
        name, sep, sections = item.partition("=")
        if not sep:
            raise ValueError("Custom batch format must be name=section,section;name2=section")
        section_tuple = tuple(section.strip() for section in sections.split(",") if section.strip())
        if not section_tuple:
            raise ValueError(f"Batch {name!r} has no sections")
        result.append(Batch(slugify(name), section_tuple, "custom batch"))
    return result


def slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_") or "batch"


def run_batch(args: argparse.Namespace, batch: Batch, root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    workspace = root / batch.name
    extract_cmd = [
        sys.executable,
        "scripts/run_standard_import_pipeline.py",
        "--workspace-dir",
        str(workspace),
        "--extract",
        "--doc-id",
        args.doc_id,
        "--sections",
        ",".join(batch.sections),
        "--extract-backend",
        args.extract_backend,
        "--judge-backend",
        args.judge_backend,
        "--extract-output-dir",
        args.extract_output_dir,
        "--budget-rmb",
        str(args.budget_rmb_per_batch),
        "--max-candidates-per-section",
        str(args.max_candidates_per_section),
        "--extract-mode",
        args.extract_mode,
    ]
    run_command(extract_cmd, dry_run=dry_run)
    if dry_run:
        return {"batch": batch.name, "sections": list(batch.sections), "workspace_dir": str(workspace), "dry_run": True}

    pipeline_summary_path = workspace / "standard_import_pipeline_summary.json"
    pipeline_summary = load_json(pipeline_summary_path)
    source_run_dir = Path(pipeline_summary["source_run_dir"])

    review_cmd = [
        sys.executable,
        "scripts/apply_model_review_to_standard_packs.py",
        "--pack-dir",
        str(workspace / "review_packs"),
        "--judge-rejected-jsonl",
        str(source_run_dir / "candidates_llm_judge_rejected.jsonl"),
    ]
    run_command(review_cmd)

    apply_cmd = [
        sys.executable,
        "scripts/run_standard_import_pipeline.py",
        "--workspace-dir",
        str(workspace),
        "--candidate-file",
        str(workspace / "candidates_input.json"),
        "--review-pack-dir",
        str(workspace / "review_packs"),
        "--skip-review-pack-build",
        "--apply",
        "--smoke",
        "--min-trust-level",
        args.min_trust_level,
    ]
    run_command(apply_cmd)
    return build_batch_result(batch, workspace, source_run_dir)


def run_command(cmd: list[str], *, dry_run: bool = False) -> None:
    print("+ " + " ".join(cmd), flush=True)
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_batch_result(batch: Batch, workspace: Path, source_run_dir: Path) -> dict[str, Any]:
    extraction_summary = load_json(source_run_dir / "summary.json")
    pipeline_summary = load_json(workspace / "standard_import_pipeline_summary.json")
    smoke_path = workspace / "review_packs" / "api_smoke_report.json"
    smoke_report = load_json(smoke_path) if smoke_path.exists() else {}
    return {
        "batch": batch.name,
        "sections": list(batch.sections),
        "description": batch.description,
        "workspace_dir": str(workspace),
        "source_run_dir": str(source_run_dir),
        "report_path": str(source_run_dir / "REPORT.md"),
        "raw_candidates": extraction_summary.get("raw_candidates"),
        "judge_accepted": extraction_summary.get("judge_accepted"),
        "judge_rejected": extraction_summary.get("judge_rejected"),
        "final_by_type": extraction_summary.get("final_by_type", {}),
        "l4_final": extraction_summary.get("l4_final"),
        "l3_final": extraction_summary.get("l3_final"),
        "gates": {key: value.get("status") for key, value in extraction_summary.get("gates", {}).items()},
        "apply_summary": pipeline_summary.get("apply_summary"),
        "api_smoke_summary": smoke_report.get("summary") or pipeline_summary.get("api_smoke_summary"),
    }


def write_summary(root: Path, results: list[dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    summary = {
        "pipeline_mode": "ashrae_g36_remaining_batches",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "batch_count": len(results),
        "results": results,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "batch_pipeline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "BATCH_PIPELINE_SUMMARY.md").write_text(render_summary(summary) + "\n", encoding="utf-8")
    return summary


def render_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# ASHRAE G36 Remaining Batch Pipeline Summary",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Dry run: `{summary['dry_run']}`",
        f"- Batches: {summary['batch_count']}",
        "",
        "| Batch | Sections | Accepted | Rejected | L4/L3 | API smoke | Report |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for result in summary["results"]:
        smoke = result.get("api_smoke_summary") or {}
        smoke_text = "dry-run" if result.get("dry_run") else f"{smoke.get('passed', 0)}/{smoke.get('targets', 0)}"
        report = result.get("report_path") or "-"
        lines.append(
            f"| `{result['batch']}` | {', '.join(result['sections'])} | "
            f"{result.get('judge_accepted', '-')} | {result.get('judge_rejected', '-')} | "
            f"{result.get('l4_final', '-')}/{result.get('l3_final', '-')} | {smoke_text} | `{report}` |"
        )
    lines.extend(["", "## Notes", "", "- `5.22` and terminal/exhaust-fan sections are temporarily imported into the existing `ahu` class until dedicated HVAC ontology classes are added."])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", default=DEFAULT_DOC_ID)
    parser.add_argument("--extract-backend", default=DEFAULT_EXTRACT_BACKEND)
    parser.add_argument("--judge-backend", default=DEFAULT_JUDGE_BACKEND)
    parser.add_argument("--extract-output-dir", default="output/ashrae_guideline36_vertical")
    parser.add_argument("--workspace-root", default="workspace/ashrae_g36_remaining_batch_pipeline")
    parser.add_argument("--budget-rmb-per-batch", type=float, default=30.0)
    parser.add_argument("--max-candidates-per-section", type=int, default=24)
    parser.add_argument("--min-trust-level", default="L3")
    parser.add_argument("--extract-mode", choices=["bundle", "section"], default="bundle")
    parser.add_argument("--batches", help="Custom batches: name=5.2,5.3;name2=5.17,5.18")
    parser.add_argument("--include-general", action="store_true", help="Also run §5.1. This may duplicate prior §5.1.14 candidates.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.workspace_root) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batches = parse_batches(args.batches, include_general=args.include_general)
    results = [run_batch(args, batch, root, dry_run=args.dry_run) for batch in batches]
    summary = write_summary(root, results, dry_run=args.dry_run)
    print(f"batch_count={summary['batch_count']} summary={root / 'BATCH_PIPELINE_SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"ASHRAE G36 batch pipeline failed: {exc}")
        raise SystemExit(1)
