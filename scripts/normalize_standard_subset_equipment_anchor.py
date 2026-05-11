#!/usr/bin/env python3
"""Normalize equipment anchors for standard page-subset extraction artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def suggest_equipment_anchor(file_name: str, knowledge_types: dict[str, int]) -> tuple[str, str]:
    name = file_name.lower()
    if "2019" in name or "2024" in name or "hvac系统和设备篇" in file_name or "design" in name or "设计" in file_name:
        if knowledge_types.get("performance_spec", 0) or knowledge_types.get("parameter_spec", 0):
            return "chiller", "standard_general_hvac_handbook_with_hvac_design_content"
    if "绿色建筑指南" in file_name or "211" in file_name:
        return "chiller", "standard_guidance_default_for_general_hvac_reference"
    return "chiller", "fallback_general_hvac_standard"


def normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    backend = (task.get("backend_results") or [{}])[0]
    original = str(task.get("equipment_class_id") or "")
    suggested, reason = suggest_equipment_anchor(str(task.get("file_name") or ""), backend.get("by_type") or {})
    return {
        "file_name": task.get("file_name"),
        "doc_id": task.get("doc_id"),
        "original_equipment_class_id": original,
        "suggested_equipment_class_id": suggested,
        "accepted": backend.get("judge_accepted"),
        "judge_acceptance_rate": backend.get("judge_acceptance_rate"),
        "knowledge_types": backend.get("by_type") or {},
        "reason": reason,
        "needs_override": original != suggested,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    pipeline = json.loads(args.pipeline_summary.read_text(encoding="utf-8"))
    rows = []
    for item in pipeline.get("results", []):
        extract_dir = Path(item["extract_dir"])
        task_files = sorted(extract_dir.glob("*/0001_*/task_summary.json"))
        if not task_files:
            continue
        task = json.loads(task_files[0].read_text(encoding="utf-8"))
        rows.append(normalize_task(task))

    report = {
        "report_mode": "standard_subset_equipment_anchor_override",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_pipeline_summary": str(args.pipeline_summary),
        "rows": rows,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "standard_subset_equipment_anchor_override.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Standard Subset Equipment Anchor Override",
        "",
        "| Document | Original Anchor | Suggested Anchor | Accepted | Judge Rate | Needs Override | Reason |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['file_name']} | {row['original_equipment_class_id']} | {row['suggested_equipment_class_id']} | "
            f"{row['accepted']} | {float(row['judge_acceptance_rate'] or 0.0):.1f} | {row['needs_override']} | {row['reason']} |"
        )
    (args.output_dir / "STANDARD_SUBSET_EQUIPMENT_ANCHOR_OVERRIDE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output_dir / "STANDARD_SUBSET_EQUIPMENT_ANCHOR_OVERRIDE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
