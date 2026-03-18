#!/usr/bin/env python3
"""Summarize chunk-backfill review pipeline stats."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_packs_batch import (
    APPLY_REPORT_FILE,
    discover_review_pack_paths,
    inspect_review_pack,
)
from scripts.check_review_pack_readiness import READINESS_REPORT_FILE


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _doc_record(base: dict[str, Any] | None = None) -> dict[str, Any]:
    record = {
        "doc_id": None,
        "doc_name": None,
        "scanned_chunks": 0,
        "matched_chunks": 0,
        "candidate_entries": 0,
        "candidate_hit_rate": 0.0,
        "review_decisions": {"accepted": 0, "rejected": 0, "pending": 0},
        "packs_total": 0,
        "packs_ready_to_apply": 0,
        "readiness_status_counts": {
            "ready": 0,
            "blocked_pending": 0,
            "blocked_no_accepted": 0,
            "blocked_invalid": 0,
        },
        "apply_status_counts": {
            "applied": 0,
            "skipped_pending": 0,
            "skipped_no_accepted": 0,
            "failed": 0,
        },
    }
    if base:
        record.update(base)
    return record


def summarize_review_pipeline_stats(
    *,
    candidate_path: str | Path | None = None,
    pack_dir: str | Path | None = None,
    readiness_report_path: str | Path | None = None,
    apply_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a summary across candidate generation, review packs, and apply results."""

    documents: dict[str, dict[str, Any]] = {}
    candidate_payload = _load_json(candidate_path) if candidate_path else None
    if candidate_payload:
        for summary in candidate_payload.get("metadata", {}).get("doc_summaries", []):
            documents[summary["doc_id"]] = _doc_record(summary)

    pack_root = Path(pack_dir) if pack_dir else None
    if readiness_report_path is None and pack_root and (pack_root / READINESS_REPORT_FILE).exists():
        readiness_report_path = pack_root / READINESS_REPORT_FILE
    if apply_report_path is None and pack_root and (pack_root / APPLY_REPORT_FILE).exists():
        apply_report_path = pack_root / APPLY_REPORT_FILE
    readiness_report = _load_json(readiness_report_path) if readiness_report_path else None
    apply_report = _load_json(apply_report_path) if apply_report_path else None
    readiness_result_by_file = {
        item["pack_file"]: item
        for item in readiness_report.get("results", [])
    } if readiness_report else {}
    apply_result_by_file = {
        item["pack_file"]: item
        for item in apply_report.get("results", [])
    } if apply_report else {}

    pack_summaries = []
    if pack_root:
        for pack_path in discover_review_pack_paths(pack_root):
            payload = _load_json(pack_path)
            inspection = inspect_review_pack(payload)
            equipment = payload.get("equipment_class", {})
            summary = {
                "pack_file": pack_path.name,
                "doc_id": payload.get("doc_id"),
                "doc_name": payload.get("doc_name"),
                "equipment_class_id": equipment.get("equipment_class_id"),
                "equipment_class_key": equipment.get("equipment_class_key"),
                "candidate_count": inspection["candidate_count"],
                "accepted_count": inspection["accepted_count"],
                "rejected_count": inspection["rejected_count"],
                "pending_count": inspection["pending_count"],
                "ready_to_apply": inspection["pending_count"] == 0 and inspection["accepted_count"] > 0,
                "readiness_status": readiness_result_by_file.get(pack_path.name, {}).get("status"),
                "readiness_blocker": readiness_result_by_file.get(pack_path.name, {}).get("blocker"),
                "apply_status": apply_result_by_file.get(pack_path.name, {}).get("status"),
            }
            pack_summaries.append(summary)

            doc_id = summary["doc_id"]
            doc_record = documents.setdefault(
                doc_id,
                _doc_record({"doc_id": doc_id, "doc_name": summary["doc_name"]}),
            )
            doc_record["doc_name"] = doc_record["doc_name"] or summary["doc_name"]
            doc_record["review_decisions"]["accepted"] += summary["accepted_count"]
            doc_record["review_decisions"]["rejected"] += summary["rejected_count"]
            doc_record["review_decisions"]["pending"] += summary["pending_count"]
            doc_record["packs_total"] += 1
            if summary["ready_to_apply"]:
                doc_record["packs_ready_to_apply"] += 1
            if summary["readiness_status"] in doc_record["readiness_status_counts"]:
                doc_record["readiness_status_counts"][summary["readiness_status"]] += 1
            if summary["apply_status"] in doc_record["apply_status_counts"]:
                doc_record["apply_status_counts"][summary["apply_status"]] += 1

    overall_readiness_counts = readiness_report.get("summary", {}) if readiness_report else {}
    overall_apply_counts = apply_report.get("summary", {}) if apply_report else {}
    overall = {
        "scanned_chunks": candidate_payload.get("metadata", {}).get("scanned_chunks", 0) if candidate_payload else 0,
        "matched_chunks": candidate_payload.get("metadata", {}).get("matched_chunks", 0) if candidate_payload else 0,
        "candidate_entries": candidate_payload.get("metadata", {}).get("total_candidates", 0) if candidate_payload else 0,
        "candidate_hit_rate": candidate_payload.get("metadata", {}).get("candidate_hit_rate", 0.0) if candidate_payload else 0.0,
        "review_packs_total": len(pack_summaries),
        "review_packs_ready_to_apply": sum(1 for item in pack_summaries if item["ready_to_apply"]),
        "review_packs_pending": sum(1 for item in pack_summaries if item["pending_count"] > 0),
        "review_packs_rejected_only": sum(
            1
            for item in pack_summaries
            if item["pending_count"] == 0 and item["accepted_count"] == 0
        ),
        "readiness_status_counts": {
            "ready": overall_readiness_counts.get("ready", 0),
            "blocked_pending": overall_readiness_counts.get("blocked_pending", 0),
            "blocked_no_accepted": overall_readiness_counts.get("blocked_no_accepted", 0),
            "blocked_invalid": overall_readiness_counts.get("blocked_invalid", 0),
        },
        "apply_status_counts": {
            "applied": overall_apply_counts.get("applied", 0),
            "skipped_pending": overall_apply_counts.get("skipped_pending", 0),
            "skipped_no_accepted": overall_apply_counts.get("skipped_no_accepted", 0),
            "failed": overall_apply_counts.get("failed", 0),
        },
    }
    return {
        "stats_mode": "chunk_backfill_review_pipeline_stats",
        "candidate_source": str(candidate_path) if candidate_path else None,
        "pack_dir": str(pack_root) if pack_root else None,
        "readiness_report_path": str(readiness_report_path) if readiness_report_path else None,
        "apply_report_path": str(apply_report_path) if apply_report_path else None,
        "overall": overall,
        "documents": [documents[key] for key in sorted(documents)],
        "review_packs": sorted(
            pack_summaries,
            key=lambda item: (
                item["doc_id"] or "",
                item["equipment_class_id"] or "",
                item["pack_file"],
            ),
        ),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-file", dest="candidate_path", help="Candidate JSON file to summarize")
    parser.add_argument("--pack-dir", help="Directory containing review packs")
    parser.add_argument("--readiness-report", dest="readiness_report_path", help="Optional readiness report JSON path")
    parser.add_argument("--apply-report", dest="apply_report_path", help="Optional apply report JSON path")
    parser.add_argument("--output", help="Optional output path for the stats report JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not args.candidate_path and not args.pack_dir and not args.readiness_report_path and not args.apply_report_path:
        raise ValueError("Provide at least one of --candidate-file, --pack-dir, --readiness-report, or --apply-report")
    payload = summarize_review_pipeline_stats(
        candidate_path=args.candidate_path,
        pack_dir=args.pack_dir,
        readiness_report_path=args.readiness_report_path,
        apply_report_path=args.apply_report_path,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote review pipeline stats to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pipeline stats failed: {exc}")
        raise SystemExit(1)
