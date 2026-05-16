#!/usr/bin/env python3
"""Ingest new HVAC authority source files and apply document triage."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.core.config import settings
from packages.db.models import Document
from packages.db.session import SessionLocal
from packages.ingest.document_triage import apply_triage_to_document
from packages.ingest.service import IngestService
from packages.storage.manager import StorageManager
from scripts.dedup_source_inventory import SUPPORTED_SUFFIXES, canonical_score
from scripts.generate_triage_review import generate as generate_triage_review


def make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def authority_level_for(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    if "standards" in parts:
        return "industry_standard"
    if "oem" in parts:
        return "oem_manual"
    return "unspecified"


def publisher_for(path: Path) -> str:
    stem = path.stem.lower()
    for key, publisher in {
        "ahri": "AHRI",
        "ashrae": "ASHRAE",
        "gb": "GB",
        "gbt": "GB",
        "trane": "Trane",
        "carrier": "Carrier",
        "mcquay": "McQuay",
        "gree": "Gree",
    }.items():
        if key in stem:
            return publisher
    return "unknown"


def metadata_for(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "source_path": str(path),
        "source_root": "storage/authority_sources",
        "authority_level": authority_level_for(path),
        "publisher": publisher_for(path),
        "document_kind": "standard" if "standards" in {p.lower() for p in path.parts} else "manual",
        "text_quality": "unknown",
        "page_count": "",
        "file_size_mb": round(stat.st_size / 1024 / 1024, 3),
        "file_ext": path.suffix.lower().lstrip("."),
    }


def scan_sources(root: Path) -> list[Path]:
    return sorted(
        [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES],
        key=canonical_score,
    )


def ingest_file(db, ingest: IngestService, storage: StorageManager, path: Path, run_id: str, seen: set[str]) -> dict[str, Any]:
    digest = storage.calculate_file_hash(path)
    row = {"path": str(path), "sha256": digest, "status": "", "doc_id": "", "processing_decision": "", "reason": ""}
    if digest in seen:
        row.update(status="skipped_duplicate_in_run", reason="same sha256 already ingested or skipped in this run")
        return row
    seen.add(digest)

    existing = db.query(Document).filter(Document.file_sha256 == digest).first()
    if existing is None:
        existing = db.query(Document).filter(Document.file_hash == digest).first()
    if existing:
        row.update(status="skipped_existing_sha256", doc_id=existing.doc_id, reason="document.file_sha256 already exists")
        return row

    doc_id = ingest.import_document(db, str(path), source_domain="hvac", batch_id=run_id)
    if not doc_id:
        existing = db.query(Document).filter(Document.file_hash == digest).first()
        row.update(status="skipped_existing_file_hash", doc_id=getattr(existing, "doc_id", ""), reason="IngestService duplicate")
        return row

    doc = db.query(Document).filter(Document.doc_id == doc_id).one()
    meta = metadata_for(path)
    doc.file_sha256 = digest
    doc.authority_level = meta["authority_level"]
    doc.publisher = meta["publisher"]
    doc.authority_metadata_json = {**(doc.authority_metadata_json or {}), **meta}
    result = apply_triage_to_document(doc)
    db.commit()
    row.update(status="imported", doc_id=doc_id, processing_decision=result.decision.value, reason=result.reason)
    return row


def write_report(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["path", "sha256", "status", "doc_id", "processing_decision", "reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", default="storage/authority_sources/hvac")
    parser.add_argument("--output-root", default="workspace/hvac_source_inventory")
    args = parser.parse_args(argv)
    run_id = make_run_id()
    out_dir = Path(args.output_root) / run_id
    storage = StorageManager(settings.storage_root)
    ingest = IngestService(storage)
    rows = []
    seen: set[str] = set()
    db = SessionLocal()
    try:
        for path in scan_sources(Path(args.source_root)):
            rows.append(ingest_file(db, ingest, storage, path, run_id, seen))
    finally:
        db.close()
    report_path = out_dir / "new_files_ingest_report.csv"
    write_report(rows, report_path)
    review_path = generate_triage_review(
        Path("workspace/triage_review"),
        source_domain="hvac",
        source_batch_id=run_id,
        run_id=run_id,
    )
    print(f"report={report_path}")
    print(f"manual_review={review_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
