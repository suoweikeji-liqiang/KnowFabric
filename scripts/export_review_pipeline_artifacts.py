#!/usr/bin/env python3
"""Export chunk-backfill review pipeline artifacts for one scope."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_review_packs_from_candidates import write_review_packs_from_candidate_file
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates
from scripts.summarize_review_pipeline_stats import summarize_review_pipeline_stats


def export_review_pipeline_artifacts(
    domain_id: str,
    output_dir: str | Path,
    *,
    doc_id: str | None = None,
    chunk_id: str | None = None,
    equipment_class_id: str | None = None,
    limit: int = 100,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Generate candidate, review-pack, and stats artifacts into one directory."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    candidate_path = destination / "candidates.json"
    review_pack_dir = destination / "review_packs"
    stats_path = destination / "review_pipeline_stats.json"
    manifest_path = destination / "artifact_manifest.json"

    candidates = generate_chunk_backfill_candidates(
        domain_id,
        doc_id=doc_id,
        chunk_id=chunk_id,
        equipment_class_id=equipment_class_id,
        limit=limit,
    )
    candidate_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review_pack_manifest = write_review_packs_from_candidate_file(
        candidate_path,
        review_pack_dir,
        default_trust_level=default_trust_level,
    )
    stats = summarize_review_pipeline_stats(
        candidate_path=candidate_path,
        pack_dir=review_pack_dir,
    )
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "artifact_mode": "chunk_backfill_review_pipeline_export",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain_id": domain_id,
        "filters_applied": {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "equipment_class_id": equipment_class_id,
            "limit": limit,
        },
        "paths": {
            "candidates": str(candidate_path),
            "review_pack_dir": str(review_pack_dir),
            "review_pack_manifest": str(review_pack_dir / "review_pack_manifest.json"),
            "stats": str(stats_path),
        },
        "counts": {
            "candidate_entries": candidates["metadata"]["total_candidates"],
            "review_packs": review_pack_manifest["total_packs"],
            "documents": len(stats["documents"]),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["paths"]["artifact_manifest"] = str(manifest_path)
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain_id", help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("output_dir", help="Directory where exported artifacts should be written")
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
        help="Default trust level to prefill in exported review packs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    manifest = export_review_pipeline_artifacts(
        args.domain_id,
        args.output_dir,
        doc_id=args.doc_id,
        chunk_id=args.chunk_id,
        equipment_class_id=args.equipment_class_id,
        limit=args.limit,
        default_trust_level=args.default_trust_level,
    )
    print(
        f"Exported {manifest['counts']['candidate_entries']} candidates and "
        f"{manifest['counts']['review_packs']} review pack(s) to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pipeline artifact export failed: {exc}")
        raise SystemExit(1)
