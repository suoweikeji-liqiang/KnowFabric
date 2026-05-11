#!/usr/bin/env python3
"""Analyze standard page-subset extraction results and emit structured validation findings."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def analyze_task(task: dict[str, Any]) -> dict[str, Any]:
    backend = (task.get("backend_results") or [{}])[0]
    accepted = int(backend.get("judge_accepted") or 0)
    rejected = int(backend.get("judge_rejected") or 0)
    rate = float(backend.get("judge_acceptance_rate") or 0.0)
    equipment = str(task.get("equipment_class_id") or "")
    findings = []

    if accepted == 0:
        findings.append(
            {
                "code": "no_publishable_knowledge",
                "severity": "high",
                "message": "No candidates survived judge review for this selected page subset.",
            }
        )
    if rate < 20.0:
        findings.append(
            {
                "code": "low_judge_acceptance",
                "severity": "high",
                "message": "Judge acceptance rate is very low; selected pages likely contain weak evidence or wrong page type.",
            }
        )
    elif rate < 50.0:
        findings.append(
            {
                "code": "medium_judge_acceptance",
                "severity": "medium",
                "message": "Judge acceptance rate is moderate; selected subset may still contain noisy or weak-evidence pages.",
            }
        )

    if equipment in {"controller", "valve", "pump", "cooling_tower"}:
        findings.append(
            {
                "code": "equipment_anchor_suspect",
                "severity": "medium",
                "message": "Automatic equipment anchor may not reflect the standard document's real semantic scope.",
            }
        )

    breakdown = backend.get("judge_rejection_breakdown") or {}
    if int(breakdown.get("weak_evidence") or 0) > 0:
        findings.append(
            {
                "code": "weak_evidence_present",
                "severity": "medium",
                "message": "Some candidates were rejected for weak evidence; page selection rules may still need refinement.",
            }
        )

    status = "pass"
    if any(item["severity"] == "high" for item in findings):
        status = "fail"
    elif findings:
        status = "flag"

    return {
        "doc_id": task.get("doc_id"),
        "file_name": task.get("file_name"),
        "equipment_class_id": equipment,
        "accepted": accepted,
        "rejected": rejected,
        "judge_acceptance_rate": rate,
        "knowledge_types": backend.get("by_type") or {},
        "status": status,
        "findings": findings,
        "task_dir": task.get("task_dir"),
    }


def analyze_pipeline(pipeline_summary_path: Path) -> dict[str, Any]:
    pipeline = json.loads(pipeline_summary_path.read_text(encoding="utf-8"))
    results = []
    for row in pipeline.get("results", []):
        extract_dir = Path(row["extract_dir"])
        task_files = sorted(extract_dir.glob("*/0001_*/task_summary.json"))
        if not task_files:
            continue
        task = json.loads(task_files[0].read_text(encoding="utf-8"))
        analyzed = analyze_task(task)
        analyzed["suggested_equipment_class_id"] = row.get("suggested_equipment_class_id")
        analyzed["suggested_equipment_class_reason"] = row.get("suggested_equipment_class_reason")
        results.append(analyzed)

    counts = Counter(item["status"] for item in results)
    code_counts = Counter(
        finding["code"]
        for item in results
        for finding in item["findings"]
    )
    return {
        "analysis_mode": "standard_subset_validation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_pipeline_summary": str(pipeline_summary_path),
        "summary": {
            "documents": len(results),
            "pass": counts.get("pass", 0),
            "flag": counts.get("flag", 0),
            "fail": counts.get("fail", 0),
            "finding_codes": dict(code_counts),
        },
        "results": results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Standard Subset Validation Report",
        "",
        f"- Documents: `{report['summary']['documents']}`",
        f"- Pass: `{report['summary']['pass']}`",
        f"- Flag: `{report['summary']['flag']}`",
        f"- Fail: `{report['summary']['fail']}`",
        "",
        "| Document | Status | Accepted | Judge Rate | Equipment Anchor | Suggested Anchor | Findings |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for item in report["results"]:
        finding_codes = ", ".join(f["code"] for f in item["findings"]) or "-"
        lines.append(
            f"| {item['file_name']} | {item['status']} | {item['accepted']} | "
            f"{item['judge_acceptance_rate']:.1f} | {item['equipment_class_id']} | "
            f"{item.get('suggested_equipment_class_id') or '-'} | {finding_codes} |"
        )
    return "\n".join(lines) + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = analyze_pipeline(args.pipeline_summary)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "standard_subset_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "STANDARD_SUBSET_VALIDATION.md").write_text(render_markdown(report), encoding="utf-8")
    print(args.output_dir / "STANDARD_SUBSET_VALIDATION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
