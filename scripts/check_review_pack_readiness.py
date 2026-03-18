#!/usr/bin/env python3
"""Check whether review packs are ready for batch apply."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_packs_batch import APPLY_REPORT_FILE, PACK_MANIFEST_FILE, discover_review_pack_paths, inspect_review_pack
from scripts.build_manual_fixture_from_review_candidates import build_manual_fixture_from_review_candidate_file

READINESS_REPORT_FILE = "review_pack_readiness_report.json"
BOOTSTRAP_REPORT_FILE = "review_pack_bootstrap_report.json"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def assess_review_pack_readiness(path: str | Path) -> dict[str, Any]:
    """Assess whether one review pack can safely enter the apply step."""

    pack_path = Path(path)
    payload = _load_json(pack_path)
    equipment = payload.get("equipment_class", {})
    result = {
        "pack_file": pack_path.name,
        "pack_path": str(pack_path),
        "doc_id": payload.get("doc_id"),
        "doc_name": payload.get("doc_name"),
        "equipment_class_id": equipment.get("equipment_class_id"),
        "equipment_class_key": equipment.get("equipment_class_key"),
    }
    inspection = inspect_review_pack(payload)
    result.update(inspection)
    if inspection["pending_count"] > 0:
        result["status"] = "blocked_pending"
        result["blocker"] = "pending_review_decisions"
        return result
    if inspection["accepted_count"] == 0:
        result["status"] = "blocked_no_accepted"
        result["blocker"] = "no_accepted_entries"
        return result
    try:
        fixture = build_manual_fixture_from_review_candidate_file(pack_path)
    except Exception as exc:
        result["status"] = "blocked_invalid"
        result["blocker"] = str(exc)
        return result
    result["status"] = "ready"
    result["blocker"] = None
    result["ready_manual_entries"] = len(fixture["manual_entries"])
    result["fixture_equipment_class_key"] = fixture["equipment_class_key"]
    return result


def check_review_pack_directory(
    pack_dir: str | Path,
    *,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Check all review packs in one directory and write a readiness report."""

    pack_root = Path(pack_dir)
    pack_paths = discover_review_pack_paths(pack_root)
    results = [assess_review_pack_readiness(path) for path in pack_paths]
    summary_counts = Counter(item["status"] for item in results)
    report = {
        "readiness_mode": "chunk_backfill_review_pack_readiness",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_dir": str(pack_root),
        "ignored_files": [
            PACK_MANIFEST_FILE,
            APPLY_REPORT_FILE,
            READINESS_REPORT_FILE,
            BOOTSTRAP_REPORT_FILE,
        ],
        "total_pack_files": len(pack_paths),
        "summary": {
            "ready": summary_counts.get("ready", 0),
            "blocked_pending": summary_counts.get("blocked_pending", 0),
            "blocked_no_accepted": summary_counts.get("blocked_no_accepted", 0),
            "blocked_invalid": summary_counts.get("blocked_invalid", 0),
        },
        "results": results,
    }
    target = Path(report_path) if report_path else pack_root / READINESS_REPORT_FILE
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(target)
    return report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", help="Directory containing review packs")
    parser.add_argument("--report-path", help="Optional output path for the readiness report JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = check_review_pack_directory(
        args.pack_dir,
        report_path=args.report_path,
    )
    print(
        f"Ready {report['summary']['ready']}, "
        f"blocked_pending {report['summary']['blocked_pending']}, "
        f"blocked_no_accepted {report['summary']['blocked_no_accepted']}, "
        f"blocked_invalid {report['summary']['blocked_invalid']}. "
        f"Report: {report['report_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pack readiness check failed: {exc}")
        raise SystemExit(1)
