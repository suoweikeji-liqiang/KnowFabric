#!/usr/bin/env python3
"""Prepare a full chunk-backfill review bundle in one command."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.bootstrap_review_packs_batch import bootstrap_review_pack_directory
from scripts.check_review_pack_readiness import check_review_pack_directory
from scripts.export_review_pipeline_artifacts import export_review_pipeline_artifacts
from scripts.print_review_pipeline_summary import build_review_pipeline_summary_text
from scripts.summarize_review_pipeline_stats import summarize_review_pipeline_stats


def prepare_review_pipeline_bundle(
    domain_id: str,
    output_dir: str | Path,
    *,
    doc_id: str | None = None,
    chunk_id: str | None = None,
    equipment_class_id: str | None = None,
    limit: int = 100,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Export, bootstrap, validate, and summarize one review bundle."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    export_manifest = export_review_pipeline_artifacts(
        domain_id,
        destination,
        doc_id=doc_id,
        chunk_id=chunk_id,
        equipment_class_id=equipment_class_id,
        limit=limit,
        default_trust_level=default_trust_level,
    )

    review_pack_dir = Path(export_manifest["paths"]["review_pack_dir"])
    bootstrap_report = bootstrap_review_pack_directory(
        review_pack_dir,
        default_trust_level=default_trust_level,
    )
    bootstrapped_dir = Path(bootstrap_report["output_dir"])
    readiness_report = check_review_pack_directory(bootstrapped_dir)
    stats = summarize_review_pipeline_stats(
        candidate_path=export_manifest["paths"]["candidates"],
        pack_dir=bootstrapped_dir,
        readiness_report_path=readiness_report["report_path"],
    )

    bootstrapped_stats_path = destination / "bootstrapped_review_pipeline_stats.json"
    bootstrapped_stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_text = build_review_pipeline_summary_text(stats)
    summary_path = destination / "review_pipeline_summary.txt"
    summary_path.write_text(summary_text + "\n", encoding="utf-8")

    manifest = {
        "prepare_mode": "chunk_backfill_review_pipeline_prepare",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain_id": domain_id,
        "filters_applied": {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "equipment_class_id": equipment_class_id,
            "limit": limit,
        },
        "paths": {
            "bundle_dir": str(destination),
            "candidates": export_manifest["paths"]["candidates"],
            "review_pack_dir": export_manifest["paths"]["review_pack_dir"],
            "review_pack_manifest": export_manifest["paths"]["review_pack_manifest"],
            "initial_stats": export_manifest["paths"]["stats"],
            "bootstrapped_review_pack_dir": str(bootstrapped_dir),
            "bootstrap_report": bootstrap_report["report_path"],
            "readiness_report": readiness_report["report_path"],
            "bootstrapped_stats": str(bootstrapped_stats_path),
            "summary_text": str(summary_path),
        },
        "counts": {
            "candidate_entries": export_manifest["counts"]["candidate_entries"],
            "review_packs": export_manifest["counts"]["review_packs"],
            "bootstrapped_packs": bootstrap_report["summary"]["bootstrapped"],
            "ready_packs": readiness_report["summary"]["ready"],
        },
    }
    manifest_path = destination / "prepare_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["paths"]["prepare_manifest"] = str(manifest_path)
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain_id", help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("output_dir", help="Directory where the prepared bundle should be written")
    parser.add_argument("--doc-id", dest="doc_id", help="Optional document filter")
    parser.add_argument("--chunk-id", dest="chunk_id", help="Optional chunk filter")
    parser.add_argument(
        "--equipment-class-id",
        dest="equipment_class_id",
        help="Optional known equipment class to constrain candidate generation",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of candidate entries to export")
    parser.add_argument(
        "--default-trust-level",
        default="L3",
        help="Default trust level to prefill in generated review packs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    manifest = prepare_review_pipeline_bundle(
        args.domain_id,
        args.output_dir,
        doc_id=args.doc_id,
        chunk_id=args.chunk_id,
        equipment_class_id=args.equipment_class_id,
        limit=args.limit,
        default_trust_level=args.default_trust_level,
    )
    print(
        f"Prepared review bundle with {manifest['counts']['candidate_entries']} candidates, "
        f"{manifest['counts']['review_packs']} pack(s), "
        f"{manifest['counts']['ready_packs']} ready pack(s). "
        f"Manifest: {manifest['paths']['prepare_manifest']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review bundle preparation failed: {exc}")
        raise SystemExit(1)
