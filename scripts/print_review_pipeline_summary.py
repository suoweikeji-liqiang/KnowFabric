#!/usr/bin/env python3
"""Render a terminal-friendly summary for chunk-backfill review pipeline stats."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.summarize_review_pipeline_stats import summarize_review_pipeline_stats


def _load_stats_payload(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _format_ratio(matched: int, scanned: int) -> str:
    return f"{matched}/{scanned}" if scanned else "0/0"


def build_review_pipeline_summary_text(stats: dict[str, Any]) -> str:
    """Render one review pipeline stats payload as readable terminal text."""

    overall = stats.get("overall", {})
    lines = [
        "Review Pipeline Summary",
        f"Candidates: {overall.get('candidate_entries', 0)} entries from "
        f"{_format_ratio(overall.get('matched_chunks', 0), overall.get('scanned_chunks', 0))} matched chunks "
        f"(hit rate {overall.get('candidate_hit_rate', 0.0):.3f})",
        f"Packs: {overall.get('review_packs_total', 0)} total, "
        f"{overall.get('review_packs_ready_to_apply', 0)} ready, "
        f"{overall.get('review_packs_pending', 0)} pending, "
        f"{overall.get('review_packs_rejected_only', 0)} rejected-only",
        f"Readiness: {overall.get('readiness_status_counts', {}).get('ready', 0)} ready, "
        f"{overall.get('readiness_status_counts', {}).get('blocked_pending', 0)} blocked-pending, "
        f"{overall.get('readiness_status_counts', {}).get('blocked_no_accepted', 0)} blocked-no-accepted, "
        f"{overall.get('readiness_status_counts', {}).get('blocked_invalid', 0)} blocked-invalid",
        f"Apply: {overall.get('apply_status_counts', {}).get('applied', 0)} applied, "
        f"{overall.get('apply_status_counts', {}).get('skipped_pending', 0)} skipped-pending, "
        f"{overall.get('apply_status_counts', {}).get('skipped_no_accepted', 0)} skipped-no-accepted, "
        f"{overall.get('apply_status_counts', {}).get('failed', 0)} failed",
    ]

    documents = stats.get("documents", [])
    if documents:
        lines.append("")
        lines.append("Documents")
        for document in documents:
            lines.append(
                f"- {document['doc_id']}: "
                f"{_format_ratio(document['matched_chunks'], document['scanned_chunks'])} matched chunks, "
                f"{document['candidate_entries']} candidates, "
                f"review a/r/p={document['review_decisions']['accepted']}/"
                f"{document['review_decisions']['rejected']}/"
                f"{document['review_decisions']['pending']}, "
                f"packs {document['packs_ready_to_apply']}/{document['packs_total']} ready, "
                f"readiness {document['readiness_status_counts']['ready']}/"
                f"{document['readiness_status_counts']['blocked_pending']}/"
                f"{document['readiness_status_counts']['blocked_no_accepted']}/"
                f"{document['readiness_status_counts']['blocked_invalid']}"
            )

    packs_needing_review = [
        item
        for item in stats.get("review_packs", [])
        if item.get("pending_count", 0) > 0
    ]
    if packs_needing_review:
        lines.append("")
        lines.append("Packs Needing Review")
        for pack in packs_needing_review:
            lines.append(
                f"- {pack['pack_file']}: doc={pack['doc_id']}, "
                f"accepted={pack['accepted_count']}, rejected={pack['rejected_count']}, pending={pack['pending_count']}"
            )

    failed_packs = [
        item
        for item in stats.get("review_packs", [])
        if item.get("apply_status") == "failed"
    ]
    if failed_packs:
        lines.append("")
        lines.append("Failed Packs")
        for pack in failed_packs:
            lines.append(
                f"- {pack['pack_file']}: doc={pack['doc_id']}, equipment={pack['equipment_class_id']}"
            )

    blocked_invalid_packs = [
        item
        for item in stats.get("review_packs", [])
        if item.get("readiness_status") == "blocked_invalid"
    ]
    if blocked_invalid_packs:
        lines.append("")
        lines.append("Invalid Packs")
        for pack in blocked_invalid_packs:
            lines.append(
                f"- {pack['pack_file']}: doc={pack['doc_id']}, blocker={pack['readiness_blocker']}"
            )

    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats-file", help="Existing review_pipeline_stats.json file")
    parser.add_argument("--candidate-file", dest="candidate_path", help="Candidate JSON file to summarize")
    parser.add_argument("--pack-dir", help="Directory containing review packs")
    parser.add_argument("--readiness-report", dest="readiness_report_path", help="Optional readiness report JSON path")
    parser.add_argument("--apply-report", dest="apply_report_path", help="Optional batch apply report JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.stats_file:
        stats = _load_stats_payload(args.stats_file)
    else:
        if not args.candidate_path and not args.pack_dir and not args.readiness_report_path and not args.apply_report_path:
            raise ValueError("Provide --stats-file or at least one of --candidate-file, --pack-dir, --readiness-report, or --apply-report")
        stats = summarize_review_pipeline_stats(
            candidate_path=args.candidate_path,
            pack_dir=args.pack_dir,
            readiness_report_path=args.readiness_report_path,
            apply_report_path=args.apply_report_path,
        )
    print(build_review_pipeline_summary_text(stats))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pipeline summary failed: {exc}")
        raise SystemExit(1)
