#!/usr/bin/env python3
"""Build per-document review packs from chunk backfill candidate JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_review_scaffold_from_candidates import build_review_scaffold_from_candidate_file


def _slugify(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip()).strip("_").lower()
    return value or "pack"


def _pack_filename(domain_id: str, doc_id: str, equipment_class_id: str) -> str:
    return f"{_slugify(domain_id)}__{_slugify(doc_id)}__{_slugify(equipment_class_id)}.json"


def _group_entries(scaffold: dict[str, Any]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in scaffold["candidate_entries"]:
        grouped[
            (
                entry["domain_id"],
                entry["doc_id"],
                entry["equipment_class_candidate"]["equipment_class_id"],
            )
        ].append(entry)
    return grouped


def build_review_packs_from_scaffold(scaffold: dict[str, Any]) -> list[dict[str, Any]]:
    """Split one scaffold payload into smaller doc/equipment review packs."""

    packs = []
    for (_, _, _), entries in sorted(_group_entries(scaffold).items()):
        first = entries[0]
        pack = {
            "review_mode": "chunk_backfill_review_pack",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_generation_mode": scaffold.get("source_generation_mode"),
            "source_review_mode": scaffold.get("review_mode"),
            "domain_id": first["domain_id"],
            "doc_id": first["doc_id"],
            "doc_name": first["doc_name"],
            "equipment_class": {
                "equipment_class_id": first["equipment_class_candidate"]["equipment_class_id"],
                "equipment_class_key": first["equipment_class_candidate"]["equipment_class_key"],
                "label": first["equipment_class_candidate"]["label"],
                "supported_knowledge_anchors": first["equipment_class_candidate"].get("supported_knowledge_anchors", []),
            },
            "filters_applied": scaffold.get("filters_applied", {}),
            "review_metadata": {
                "default_trust_level": scaffold.get("review_metadata", {}).get("default_trust_level"),
                "candidate_count": len(entries),
                "workflow": scaffold.get("review_metadata", {}).get("workflow", []),
            },
            "candidate_entries": entries,
        }
        packs.append(pack)
    return packs


def write_review_packs_from_candidate_file(
    candidate_path: str | Path,
    output_dir: str | Path,
    *,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Build and write doc/equipment review packs plus a manifest."""

    scaffold = build_review_scaffold_from_candidate_file(
        candidate_path,
        default_trust_level=default_trust_level,
    )
    packs = build_review_packs_from_scaffold(scaffold)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    manifest_entries = []
    for pack in packs:
        file_name = _pack_filename(
            pack["domain_id"],
            pack["doc_id"],
            pack["equipment_class"]["equipment_class_id"],
        )
        (destination / file_name).write_text(
            json.dumps(pack, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_entries.append(
            {
                "file_name": file_name,
                "doc_id": pack["doc_id"],
                "doc_name": pack["doc_name"],
                "equipment_class_id": pack["equipment_class"]["equipment_class_id"],
                "equipment_class_key": pack["equipment_class"]["equipment_class_key"],
                "candidate_count": len(pack["candidate_entries"]),
            }
        )

    manifest = {
        "review_mode": "chunk_backfill_review_pack_manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_generation_mode": scaffold.get("source_generation_mode"),
        "source_review_mode": scaffold.get("review_mode"),
        "domain_id": scaffold.get("domain_id"),
        "filters_applied": scaffold.get("filters_applied", {}),
        "total_packs": len(manifest_entries),
        "packs": manifest_entries,
    }
    (destination / "review_pack_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_path", help="Path to generated candidate JSON")
    parser.add_argument("output_dir", help="Directory where review packs should be written")
    parser.add_argument(
        "--default-trust-level",
        default="L3",
        help="Default trust level to prefill in each generated pack",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    manifest = write_review_packs_from_candidate_file(
        args.candidate_path,
        args.output_dir,
        default_trust_level=args.default_trust_level,
    )
    print(
        f"Wrote {manifest['total_packs']} review packs to {args.output_dir} "
        f"(manifest=review_pack_manifest.json)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Review pack build failed: {exc}")
        raise SystemExit(1)
