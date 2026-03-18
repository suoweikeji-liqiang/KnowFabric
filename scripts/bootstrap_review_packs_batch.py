#!/usr/bin/env python3
"""Bootstrap editable curation drafts for all review packs in one directory."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_packs_batch import discover_review_pack_paths
from scripts.bootstrap_review_pack_curation import bootstrap_review_pack_file

BOOTSTRAP_REPORT_FILE = "review_pack_bootstrap_report.json"


def _output_pack_path(output_dir: Path, source_path: Path) -> Path:
    return output_dir / source_path.name


def bootstrap_review_pack_directory(
    pack_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    report_path: str | Path | None = None,
    target_decisions: set[str] | None = None,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Bootstrap all review packs in one directory and write a report."""

    pack_root = Path(pack_dir)
    output_root = Path(output_dir) if output_dir else pack_root / "bootstrapped_review_packs"
    output_root.mkdir(parents=True, exist_ok=True)
    pack_paths = discover_review_pack_paths(pack_root)

    results = []
    summary = Counter()
    total_entries_updated = 0
    for pack_path in pack_paths:
        result = {
            "pack_file": pack_path.name,
            "source_path": str(pack_path),
        }
        try:
            payload = bootstrap_review_pack_file(
                pack_path,
                target_decisions=target_decisions,
                default_trust_level=default_trust_level,
            )
            output_path = _output_pack_path(output_root, pack_path)
            output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            entries_updated = payload.get("bootstrap_metadata", {}).get("entries_updated", 0)
            result["status"] = "bootstrapped" if entries_updated else "unchanged"
            result["entries_updated"] = entries_updated
            result["output_path"] = str(output_path)
            total_entries_updated += entries_updated
        except Exception as exc:
            result["status"] = "failed"
            result["error"] = str(exc)
        summary[result["status"]] += 1
        results.append(result)

    report = {
        "bootstrap_mode": "chunk_backfill_review_pack_batch_bootstrap",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_dir": str(pack_root),
        "output_dir": str(output_root),
        "total_pack_files": len(pack_paths),
        "total_entries_updated": total_entries_updated,
        "target_decisions": sorted(target_decisions) if target_decisions else None,
        "summary": {
            "bootstrapped": summary.get("bootstrapped", 0),
            "unchanged": summary.get("unchanged", 0),
            "failed": summary.get("failed", 0),
        },
        "results": results,
    }
    target = Path(report_path) if report_path else output_root / BOOTSTRAP_REPORT_FILE
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(target)
    return report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir", help="Directory containing review pack JSON files")
    parser.add_argument(
        "--output-dir",
        help="Optional output directory for bootstrapped review pack JSON files",
    )
    parser.add_argument("--report-path", help="Optional output path for the bootstrap report JSON")
    parser.add_argument(
        "--default-trust-level",
        default="L3",
        help="Fallback trust level for empty curation blocks",
    )
    parser.add_argument(
        "--target-decisions",
        nargs="+",
        default=["accepted", "pending"],
        help="Only bootstrap entries whose review_decision is in this set",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = bootstrap_review_pack_directory(
        args.pack_dir,
        output_dir=args.output_dir,
        report_path=args.report_path,
        target_decisions=set(args.target_decisions),
        default_trust_level=args.default_trust_level,
    )
    print(
        f"Bootstrapped {report['summary']['bootstrapped']} pack(s), "
        f"left {report['summary']['unchanged']} unchanged, "
        f"failed {report['summary']['failed']}. "
        f"Report: {report['report_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pack batch bootstrap failed: {exc}")
        raise SystemExit(1)
