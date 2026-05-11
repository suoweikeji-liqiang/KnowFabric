#!/usr/bin/env python3
"""Seed a small gold-set draft from successful standard subset extraction results."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def collect_rows(pipeline_summary: Path) -> list[dict]:
    pipeline = json.loads(pipeline_summary.read_text(encoding="utf-8"))
    rows = []
    for item in pipeline.get("results", []):
        extract_dir = Path(item["extract_dir"])
        task_files = sorted(extract_dir.glob("*/0001_*/task_summary.json"))
        if not task_files:
            continue
        task = json.loads(task_files[0].read_text(encoding="utf-8"))
        backend = (task.get("backend_results") or [{}])[0]
        if int(backend.get("judge_accepted") or 0) <= 0:
            continue
        candidate_path = Path(task["task_dir"]) / backend["backend"] / "candidates.json"
        if not candidate_path.exists():
            continue
        payload = json.loads(candidate_path.read_text(encoding="utf-8"))
        entries = payload.get("candidate_entries", [])[:2]
        for entry in entries:
            rows.append(
                {
                    "doc_id": task["doc_id"],
                    "doc_name": task["file_name"],
                    "expected_equipment_class_id": item.get("suggested_equipment_class_id") or task.get("equipment_class_id"),
                    "knowledge_object_type": entry.get("knowledge_object_type"),
                    "canonical_key_candidate": entry.get("canonical_key_candidate"),
                    "evidence_text": entry.get("evidence_text"),
                    "chunk_id": entry.get("chunk_id"),
                    "page_no": entry.get("page_no"),
                }
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = collect_rows(args.pipeline_summary)
    payload = {
        "gold_set_mode": "standard_subset_seed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_pipeline_summary": str(args.pipeline_summary),
        "entries": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
