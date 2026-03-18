#!/usr/bin/env python3
"""Apply only ready review packs from a prepared review bundle."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_packs_batch import apply_review_pack_paths
from scripts.print_review_pipeline_summary import build_review_pipeline_summary_text
from scripts.summarize_review_pipeline_stats import summarize_review_pipeline_stats


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _ready_pack_paths(readiness_report: dict[str, Any]) -> list[Path]:
    pack_dir = Path(readiness_report["pack_dir"])
    return [
        pack_dir / item["pack_file"]
        for item in readiness_report.get("results", [])
        if item.get("status") == "ready"
    ]


def apply_ready_review_bundle(
    bundle_dir: str | Path,
    *,
    prepare_manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Apply all ready packs from a prepared bundle and refresh bundle outputs."""

    bundle_root = Path(bundle_dir)
    manifest_path = Path(prepare_manifest_path) if prepare_manifest_path else bundle_root / "prepare_manifest.json"
    manifest = _load_json(manifest_path)

    candidate_path = Path(manifest["paths"]["candidates"])
    bootstrapped_dir = Path(manifest["paths"]["bootstrapped_review_pack_dir"])
    readiness_report_path = Path(manifest["paths"]["readiness_report"])
    readiness_report = _load_json(readiness_report_path)
    ready_pack_paths = _ready_pack_paths(readiness_report)

    apply_report_path = bootstrapped_dir / "review_pack_apply_report.json"
    fixtures_output_dir = bootstrapped_dir / "applied_fixtures"
    apply_report = apply_review_pack_paths(
        ready_pack_paths,
        source_label=str(bootstrapped_dir),
        fixtures_output_dir=fixtures_output_dir,
        report_path=apply_report_path,
    )

    stats = summarize_review_pipeline_stats(
        candidate_path=candidate_path,
        pack_dir=bootstrapped_dir,
        readiness_report_path=readiness_report_path,
        apply_report_path=apply_report["report_path"],
    )
    stats_path = bundle_root / "bootstrapped_review_pipeline_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_text = build_review_pipeline_summary_text(stats)
    summary_path = bundle_root / "review_pipeline_summary.txt"
    summary_path.write_text(summary_text + "\n", encoding="utf-8")

    result = {
        "apply_ready_mode": "chunk_backfill_review_bundle_ready_apply",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bundle_dir": str(bundle_root),
        "ready_pack_count": len(ready_pack_paths),
        "paths": {
            "prepare_manifest": str(manifest_path),
            "bootstrapped_review_pack_dir": str(bootstrapped_dir),
            "readiness_report": str(readiness_report_path),
            "apply_report": str(apply_report["report_path"]),
            "stats": str(stats_path),
            "summary_text": str(summary_path),
        },
        "summary": {
            "applied": apply_report["summary"]["applied"],
            "failed": apply_report["summary"]["failed"],
        },
    }
    result_path = bundle_root / "apply_ready_manifest.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["paths"]["apply_ready_manifest"] = str(result_path)
    return result


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", help="Prepared review bundle directory")
    parser.add_argument("--prepare-manifest", dest="prepare_manifest_path", help="Optional prepare manifest path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = apply_ready_review_bundle(
        args.bundle_dir,
        prepare_manifest_path=args.prepare_manifest_path,
    )
    print(
        f"Applied {result['summary']['applied']} ready pack(s), "
        f"failed {result['summary']['failed']}. "
        f"Manifest: {result['paths']['apply_ready_manifest']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Apply-ready bundle step failed: {exc}")
        raise SystemExit(1)
