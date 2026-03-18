#!/usr/bin/env python3
"""Apply reviewed chunk backfill packs in batch and emit a report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.backfill_manual_knowledge_from_chunks import backfill_manual_fixture_from_chunks
from scripts.build_manual_fixture_from_review_candidates import build_manual_fixture_from_review_candidate_file

PACK_MANIFEST_FILE = "review_pack_manifest.json"
APPLY_REPORT_FILE = "review_pack_apply_report.json"
READINESS_REPORT_FILE = "review_pack_readiness_report.json"
BOOTSTRAP_REPORT_FILE = "review_pack_bootstrap_report.json"
VALID_DECISIONS = {"accepted", "rejected", "pending"}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def discover_review_pack_paths(pack_dir: str | Path) -> list[Path]:
    """Discover review pack JSON files in one directory."""

    root = Path(pack_dir)
    ignored = {
        PACK_MANIFEST_FILE,
        APPLY_REPORT_FILE,
        READINESS_REPORT_FILE,
        BOOTSTRAP_REPORT_FILE,
    }
    return sorted(
        path
        for path in root.glob("*.json")
        if path.is_file() and path.name not in ignored
    )


def inspect_review_pack(payload: dict[str, Any]) -> dict[str, Any]:
    """Return review pack status metadata without applying it."""

    if payload.get("review_mode") != "chunk_backfill_review_pack":
        raise ValueError("JSON file is not a review pack")
    entries = payload.get("candidate_entries")
    if not isinstance(entries, list):
        raise ValueError("review pack must contain candidate_entries")
    decisions = [entry.get("review_decision", "pending") for entry in entries]
    invalid = sorted({decision for decision in decisions if decision not in VALID_DECISIONS})
    if invalid:
        raise ValueError(f"review pack contains invalid decisions: {', '.join(invalid)}")
    counts = Counter(decisions)
    return {
        "candidate_count": len(entries),
        "accepted_count": counts.get("accepted", 0),
        "rejected_count": counts.get("rejected", 0),
        "pending_count": counts.get("pending", 0),
    }


def _fixture_path(fixtures_output_dir: Path, pack_path: Path) -> Path:
    return fixtures_output_dir / f"{pack_path.stem}__fixture.json"


def _apply_one_pack(pack_path: Path, fixture_root: Path) -> dict[str, Any]:
    result = {
        "pack_file": pack_path.name,
        "pack_path": str(pack_path),
    }
    try:
        payload = _load_json(pack_path)
        inspection = inspect_review_pack(payload)
        result.update(inspection)
        if inspection["pending_count"] > 0:
            result["status"] = "skipped_pending"
        elif inspection["accepted_count"] == 0:
            result["status"] = "skipped_no_accepted"
        else:
            fixture = build_manual_fixture_from_review_candidate_file(pack_path)
            fixture_path = _fixture_path(fixture_root, pack_path)
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(fixture_path)
            result["status"] = "applied"
            result["equipment_class_key"] = equipment_class_key
            result["knowledge_object_count"] = knowledge_count
            result["fixture_path"] = str(fixture_path)
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
    return result


def apply_review_pack_paths(
    pack_paths: list[Path],
    *,
    source_label: str,
    fixtures_output_dir: str | Path,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Apply a selected list of review pack paths and write a report."""

    fixture_root = Path(fixtures_output_dir)
    fixture_root.mkdir(parents=True, exist_ok=True)

    results = []
    summary = Counter()
    for pack_path in pack_paths:
        result = _apply_one_pack(pack_path, fixture_root)
        summary[result["status"]] += 1
        results.append(result)

    report = {
        "apply_mode": "chunk_backfill_review_pack_batch",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_dir": source_label,
        "fixtures_output_dir": str(fixture_root),
        "total_pack_files": len(pack_paths),
        "summary": {
            "applied": summary.get("applied", 0),
            "skipped_pending": summary.get("skipped_pending", 0),
            "skipped_no_accepted": summary.get("skipped_no_accepted", 0),
            "failed": summary.get("failed", 0),
        },
        "results": results,
    }
    report_target = Path(report_path) if report_path else fixture_root.parent / APPLY_REPORT_FILE
    report_target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_target)
    return report


def apply_review_packs_in_directory(
    pack_dir: str | Path,
    *,
    fixtures_output_dir: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Apply all fully reviewed packs in one directory and write a report."""

    pack_root = Path(pack_dir)
    fixture_root = Path(fixtures_output_dir) if fixtures_output_dir else pack_root / "applied_fixtures"
    pack_paths = discover_review_pack_paths(pack_root)
    return apply_review_pack_paths(
        pack_paths,
        source_label=str(pack_root),
        fixtures_output_dir=fixture_root,
        report_path=report_path,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", help="Directory containing review packs")
    parser.add_argument(
        "--fixtures-output-dir",
        help="Optional directory for generated fixture JSON files",
    )
    parser.add_argument("--report-path", help="Optional output path for the apply report JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = apply_review_packs_in_directory(
        args.pack_dir,
        fixtures_output_dir=args.fixtures_output_dir,
        report_path=args.report_path,
    )
    print(
        f"Applied {report['summary']['applied']} pack(s), "
        f"skipped {report['summary']['skipped_pending'] + report['summary']['skipped_no_accepted']} pack(s), "
        f"failed {report['summary']['failed']} pack(s). "
        f"Report: {report['report_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pack batch apply failed: {exc}")
        raise SystemExit(1)
