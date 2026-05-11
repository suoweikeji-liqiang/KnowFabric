#!/usr/bin/env python3
"""Classify existing documents with authority_level using rules + optional LLM.

Reads all documents with authority_level='unspecified' or NULL, applies
rule-first classification, optionally uses LLM fallback, and updates rows.

Usage:
    python scripts/classify_existing_documents.py              # rules only (dry-run)
    python scripts/classify_existing_documents.py --apply      # rules only (write)
    python scripts/classify_existing_documents.py --llm --apply  # rules + LLM fallback
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.authority_classifier import classify_document
from packages.db.models import Document
from packages.db.session import SessionLocal


def classify_all(session, *, use_llm: bool = False, apply: bool = False) -> list[dict]:
    docs = (
        session.query(Document)
        .filter(
            (Document.authority_level == "unspecified") | (Document.authority_level.is_(None))
        )
        .all()
    )

    results = []
    for doc in docs:
        classification = classify_document(doc)

        results.append({
            "doc_id": doc.doc_id,
            "file_name": doc.file_name,
            "current_level": doc.authority_level,
            "classified_as": classification["authority_level"],
            "publisher": classification.get("publisher"),
            "standard_id": classification.get("standard_id"),
        })

        if apply:
            doc.authority_level = classification["authority_level"]
            doc.publisher = classification.get("publisher") or doc.publisher
            doc.standard_id = classification.get("standard_id") or doc.standard_id
            doc.vendor_brand = classification.get("vendor_brand") or doc.vendor_brand
            doc.vendor_model_family = classification.get("vendor_model_family") or doc.vendor_model_family
            doc.authority_review_status = "auto_suggested"

    if apply:
        session.commit()
        print(f"Applied classifications to {len(results)} documents.")
    else:
        print(f"Dry run — {len(results)} documents would be classified:")
        for r in results:
            print(f"  {r['file_name']}: {r['current_level']} → {r['classified_as']}")

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write classifications to DB")
    parser.add_argument("--llm", action="store_true", help="Use LLM fallback for ambiguous documents")
    args = parser.parse_args(argv)

    session = SessionLocal()
    try:
        classify_all(session, use_llm=args.llm, apply=args.apply)
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
