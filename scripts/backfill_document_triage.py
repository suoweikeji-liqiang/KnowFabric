#!/usr/bin/env python3
"""Backfill document processing_decision fields with deterministic triage."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import Document
from packages.db.session import SessionLocal
from packages.ingest.document_triage import apply_triage_to_document


def backfill(*, source_domain: str | None = None, dry_run: bool = False) -> Counter:
    db = SessionLocal()
    counts: Counter[str] = Counter()
    try:
        query = db.query(Document)
        if source_domain:
            query = query.filter(Document.source_domain == source_domain)
        for doc in query.all():
            if not getattr(doc, "file_sha256", None):
                doc.file_sha256 = doc.file_hash
            result = apply_triage_to_document(doc)
            counts[result.decision.value] += 1
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return counts
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-domain", help="Limit backfill to one source_domain")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    counts = backfill(source_domain=args.source_domain, dry_run=args.dry_run)
    for decision, count in sorted(counts.items()):
        print(f"{decision}\t{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
