#!/usr/bin/env python3
"""Backfill Document inventory metadata from source_inventory.csv."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import Document
from packages.db.session import SessionLocal


REPORT_FIELDS = ["doc_id", "file_name", "matched", "matched_by", "fields_filled"]


@dataclass(frozen=True)
class DocumentMatch:
    document: Document | None
    matched_by: str


def latest_inventory_csv(root: Path) -> Path:
    candidates = sorted(path / "source_inventory.csv" for path in root.iterdir() if path.is_dir())
    for candidate in reversed(candidates):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No source_inventory.csv found under {root}")


def load_inventory_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [{str(key): str(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def fields_from_inventory_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "text_quality": _clean_text(row.get("text_quality")),
        "page_count": _int_or_none(row.get("page_count")),
        "sample_text_chars_first_3_pages": _int_or_none(row.get("sample_text_chars_first_3_pages")),
        "inventory_source_path": _clean_text(row.get("path")),
    }


def apply_inventory_metadata(document: Any, row: dict[str, str]) -> list[str]:
    filled = []
    for field, value in fields_from_inventory_row(row).items():
        if value is None:
            continue
        setattr(document, field, value)
        filled.append(field)
    return filled


def build_document_indexes(documents: list[Document]) -> dict[str, dict[str, list[Document]]]:
    indexes: dict[str, dict[str, list[Document]]] = {
        "file_name": defaultdict(list),
        "path": defaultdict(list),
        "hash": defaultdict(list),
        "size_mb": defaultdict(list),
    }
    for doc in documents:
        indexes["file_name"][str(doc.file_name)].append(doc)
        indexes["path"][str(doc.storage_path)].append(doc)
        if doc.inventory_source_path:
            indexes["path"][str(doc.inventory_source_path)].append(doc)
        meta = doc.authority_metadata_json if isinstance(doc.authority_metadata_json, dict) else {}
        if meta.get("source_path"):
            indexes["path"][str(meta["source_path"])].append(doc)
        for digest in {doc.file_sha256, doc.file_hash}:
            if digest:
                indexes["hash"][str(digest)].append(doc)
        if doc.file_size is not None:
            indexes["size_mb"][_size_mb_key(doc.file_size)].append(doc)
    return indexes


def match_document(
    row: dict[str, str],
    indexes: dict[str, dict[str, list[Document]]],
    *,
    allow_hash: bool = True,
) -> DocumentMatch:
    file_name = row.get("file_name") or Path(row.get("path") or "").name
    match = _unique(indexes["file_name"].get(file_name or "", []))
    if match:
        return DocumentMatch(match, "file_name")

    source_path = row.get("path") or ""
    match = _unique(indexes["path"].get(source_path, []))
    if match:
        return DocumentMatch(match, "path")

    if allow_hash:
        if not indexes["size_mb"].get(_clean_text(row.get("size_mb")) or ""):
            return DocumentMatch(None, "")
        digest = row_sha256(row)
        match = _unique(indexes["hash"].get(digest or "", []))
        if match:
            return DocumentMatch(match, "sha256")

    return DocumentMatch(None, "")


def row_sha256(row: dict[str, str]) -> str | None:
    path = Path(row.get("path") or "")
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def backfill(
    inventory_csv: Path,
    report_path: Path,
    *,
    source_domain: str | None = "hvac",
    dry_run: bool = False,
) -> dict[str, int]:
    rows = load_inventory_rows(inventory_csv)
    report_rows = []
    matched_doc_ids: set[str] = set()
    db = SessionLocal()
    try:
        query = db.query(Document)
        if source_domain:
            query = query.filter(Document.source_domain == source_domain)
        documents = query.all()
        indexes = build_document_indexes(documents)
        matched = 0
        for row in rows:
            doc_match = match_document(row, indexes)
            doc = doc_match.document
            if doc is None or str(doc.doc_id) in matched_doc_ids:
                report_rows.append(report_row(row, None, "", []))
                continue
            filled = apply_inventory_metadata(doc, row)
            matched_doc_ids.add(str(doc.doc_id))
            matched += 1
            report_rows.append(report_row(row, doc, doc_match.matched_by, filled))
        write_report(report_rows, report_path)
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return {"inventory_rows": len(rows), "matched_documents": matched}
    finally:
        db.close()


def report_row(row: dict[str, str], document: Document | None, matched_by: str, fields_filled: list[str]) -> dict[str, str]:
    return {
        "doc_id": str(getattr(document, "doc_id", "") or ""),
        "file_name": str(row.get("file_name") or Path(row.get("path") or "").name),
        "matched": "yes" if document is not None else "no",
        "matched_by": matched_by,
        "fields_filled": ",".join(fields_filled),
    }


def write_report(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _unique(documents: list[Document]) -> Document | None:
    unique = {str(doc.doc_id): doc for doc in documents}
    return next(iter(unique.values())) if len(unique) == 1 else None


def _clean_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _size_mb_key(byte_count: int) -> str:
    return f"{byte_count / 1024 / 1024:.2f}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    default_inventory = latest_inventory_csv(Path("workspace/hvac_source_inventory"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=str(default_inventory))
    parser.add_argument("--report", help="Output CSV report path")
    parser.add_argument("--source-domain", default="hvac")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inventory_csv = Path(args.inventory)
    report_path = Path(args.report) if args.report else inventory_csv.parent / "document_metadata_backfill_report.csv"
    stats = backfill(inventory_csv, report_path, source_domain=args.source_domain, dry_run=args.dry_run)
    print(f"inventory_rows={stats['inventory_rows']} matched_documents={stats['matched_documents']} report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
