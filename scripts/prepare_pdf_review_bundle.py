#!/usr/bin/env python3
"""Bootstrap selected PDF page groups and prepare a review bundle."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.bootstrap_pdf_pages_to_chunks import seed_pdf_pages_as_chunks
from scripts.prepare_review_pipeline_bundle import prepare_review_pipeline_bundle

DEFAULT_CHUNK_TYPE = "text"


@dataclass(frozen=True)
class PageGroupSpec:
    page_numbers: tuple[int, ...]
    page_type: str
    chunk_type: str = DEFAULT_CHUNK_TYPE


def _unique_pages(page_numbers: list[int]) -> tuple[int, ...]:
    deduped = []
    seen = set()
    for page_no in page_numbers:
        if page_no not in seen:
            seen.add(page_no)
            deduped.append(page_no)
    return tuple(deduped)


def _parse_page_numbers(raw: str) -> tuple[int, ...]:
    page_numbers: list[int] = []
    for token in (part.strip() for part in raw.split(",") if part.strip()):
        if "-" not in token:
            page_numbers.append(int(token))
            continue
        start_text, end_text = token.split("-", 1)
        start = int(start_text)
        end = int(end_text)
        if end < start:
            raise ValueError(f"Invalid page range: {token}")
        page_numbers.extend(range(start, end + 1))
    if not page_numbers:
        raise ValueError("Each page group must include at least one page")
    if any(page_no < 1 for page_no in page_numbers):
        raise ValueError("Page numbers must be 1-based positive integers")
    return _unique_pages(page_numbers)


def parse_page_group_spec(raw: str) -> PageGroupSpec:
    """Parse one CLI page-group spec: pages:page_type[:chunk_type]."""

    parts = [part.strip() for part in raw.split(":")]
    if len(parts) not in {2, 3} or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid page group spec: {raw}")
    page_numbers = _parse_page_numbers(parts[0])
    chunk_type = parts[2] if len(parts) == 3 and parts[2] else DEFAULT_CHUNK_TYPE
    return PageGroupSpec(
        page_numbers=page_numbers,
        page_type=parts[1],
        chunk_type=chunk_type,
    )


def _validate_page_groups(page_groups: list[PageGroupSpec]) -> None:
    seen: dict[int, str] = {}
    for group in page_groups:
        for page_no in group.page_numbers:
            owner = seen.get(page_no)
            if owner is not None:
                raise ValueError(f"Page {page_no} is assigned more than once: {owner} and {group.page_type}")
            seen[page_no] = group.page_type


def _group_pages(page_groups: list[PageGroupSpec]) -> list[PageGroupSpec]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for group in page_groups:
        grouped[(group.page_type, group.chunk_type)].extend(group.page_numbers)
    return [
        PageGroupSpec(page_numbers=_unique_pages(page_numbers), page_type=page_type, chunk_type=chunk_type)
        for (page_type, chunk_type), page_numbers in sorted(grouped.items())
    ]


def prepare_pdf_review_bundle(
    pdf_path: str | Path,
    domain_id: str,
    output_dir: str | Path,
    *,
    page_groups: list[PageGroupSpec],
    equipment_class_id: str | None = None,
    doc_id: str | None = None,
    limit: int = 100,
    default_trust_level: str = "L3",
) -> dict[str, Any]:
    """Seed selected PDF pages and prepare one ready-to-review bundle."""

    if not page_groups:
        raise ValueError("At least one page group is required")
    _validate_page_groups(page_groups)
    grouped_specs = _group_pages(page_groups)

    resolved_doc_id = doc_id
    seeded_groups = []
    seeded_pages = 0
    for spec in grouped_specs:
        resolved_doc_id, seeded = seed_pdf_pages_as_chunks(
            pdf_path,
            domain_id=domain_id,
            page_numbers=list(spec.page_numbers),
            page_type=spec.page_type,
            chunk_type=spec.chunk_type,
            doc_id=resolved_doc_id,
        )
        seeded_groups.append(
            {
                "page_type": spec.page_type,
                "chunk_type": spec.chunk_type,
                "page_numbers": list(spec.page_numbers),
                "seeded_pages": seeded,
            }
        )
        seeded_pages += seeded

    prepare_manifest = prepare_review_pipeline_bundle(
        domain_id,
        output_dir,
        doc_id=resolved_doc_id,
        equipment_class_id=equipment_class_id,
        limit=limit,
        default_trust_level=default_trust_level,
    )

    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "bundle_mode": "pdf_page_group_review_bundle_prepare",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain_id": domain_id,
        "pdf_path": str(Path(pdf_path)),
        "doc_id": resolved_doc_id,
        "equipment_class_id": equipment_class_id,
        "seeded_pages": seeded_pages,
        "page_groups": seeded_groups,
        "paths": {
            "bundle_dir": str(bundle_dir),
            "prepare_manifest": prepare_manifest["paths"]["prepare_manifest"],
            "candidates": prepare_manifest["paths"]["candidates"],
            "review_pack_dir": prepare_manifest["paths"]["review_pack_dir"],
            "bootstrapped_review_pack_dir": prepare_manifest["paths"]["bootstrapped_review_pack_dir"],
            "summary_text": prepare_manifest["paths"]["summary_text"],
        },
        "counts": prepare_manifest["counts"],
    }
    manifest_path = bundle_dir / "pdf_review_bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["paths"]["pdf_review_bundle_manifest"] = str(manifest_path)
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", help="Path to a PDF file")
    parser.add_argument("domain_id", help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("output_dir", help="Directory where the review bundle should be written")
    parser.add_argument(
        "--page-group",
        dest="page_groups",
        action="append",
        required=True,
        help="Page selection in the form pages:page_type[:chunk_type], for example 67-72:application_guide",
    )
    parser.add_argument("--equipment-class-id", help="Optional known equipment class to constrain candidates")
    parser.add_argument("--doc-id", help="Optional explicit doc_id")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of candidate entries to export")
    parser.add_argument(
        "--default-trust-level",
        default="L3",
        help="Default trust level to prefill in generated review packs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    manifest = prepare_pdf_review_bundle(
        args.pdf_path,
        args.domain_id,
        args.output_dir,
        page_groups=[parse_page_group_spec(value) for value in args.page_groups],
        equipment_class_id=args.equipment_class_id,
        doc_id=args.doc_id,
        limit=args.limit,
        default_trust_level=args.default_trust_level,
    )
    print(
        f"Prepared PDF review bundle for {manifest['doc_id']} with "
        f"{manifest['seeded_pages']} seeded page(s), "
        f"{manifest['counts']['candidate_entries']} candidates, and "
        f"{manifest['counts']['review_packs']} review pack(s). "
        f"Manifest: {manifest['paths']['pdf_review_bundle_manifest']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"PDF review bundle preparation failed: {exc}")
        raise SystemExit(1)
