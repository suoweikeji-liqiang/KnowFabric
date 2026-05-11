#!/usr/bin/env python3
"""Backfill v0.2 authority fields on existing knowledge objects.

Reads every KnowledgeObjectV2 row without authority_summary_json and populates:
- authority_summary_json (single-layer, inferred from linked evidence + document)
- consensus_state (always "single_source" for backfill)
- highest_authority_level (inferred from document.authority_level)

Safe to re-run — skips rows that already have authority_summary_json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from packages.db.session import SessionLocal


def _infer_authority_level(doc_row) -> str:
    if doc_row is None:
        return "unspecified"
    level = getattr(doc_row, "authority_level", None)
    return level if level else "unspecified"


def _build_single_source_summary(ko_row, evidence_rows, doc_cache: dict) -> dict:
    doc_row = doc_cache.get(ko_row.primary_chunk_id)
    authority_level = "unspecified"
    publisher = None
    citation = None

    if evidence_rows:
        first_ev = evidence_rows[0]
        doc = doc_cache.get(first_ev.doc_id) if hasattr(first_ev, "doc_id") else None
        if doc:
            authority_level = _infer_authority_level(doc)
            publisher = getattr(doc, "publisher", None) or None
            citation = f"{getattr(doc, 'file_name', 'unknown')} p.{first_ev.page_no}" if hasattr(first_ev, "page_no") else None

    payload = getattr(ko_row, "structured_payload_json", None)
    value_summary = None
    if isinstance(payload, dict):
        value_summary = payload.get("value") or payload.get("default_value") or payload.get("range")

    return {
        "layers": [
            {
                "authority_level": authority_level,
                "publisher": publisher,
                "citation": citation,
                "evidence_role": "primary",
                "value_summary": value_summary,
            }
        ]
    }


def backfill(session=None) -> dict:
    close_session = session is None
    if session is None:
        session = SessionLocal()

    try:
        # Find KOs missing authority_summary_json
        ko_rows = session.execute(
            text("SELECT * FROM knowledge_object WHERE authority_summary_json IS NULL")
        ).fetchall()

        if not ko_rows:
            return {"backfilled": 0, "skipped": 0, "message": "No KOs need backfill"}

        # Pre-load document cache
        doc_ids = set()
        for ko in ko_rows:
            doc_ids.update(
                session.execute(
                    text("SELECT doc_id FROM knowledge_object_evidence WHERE knowledge_object_id = :kid"),
                    {"kid": ko.knowledge_object_id},
                )
                .scalars()
                .all()
            )
        doc_rows = session.execute(
            text(f"SELECT * FROM document WHERE doc_id IN ({','.join(f':d{i}' for i in range(len(doc_ids)))})"),
            {f"d{i}": did for i, did in enumerate(doc_ids)},
        ).fetchall() if doc_ids else []
        doc_cache = {d.doc_id: d for d in doc_rows}

        updated = 0
        for ko in ko_rows:
            ev_rows = session.execute(
                text("SELECT * FROM knowledge_object_evidence WHERE knowledge_object_id = :kid"),
                {"kid": ko.knowledge_object_id},
            ).fetchall()

            summary = _build_single_source_summary(ko, ev_rows, doc_cache)
            highest = summary["layers"][0]["authority_level"] if summary["layers"] else "unspecified"

            session.execute(
                text(
                    """UPDATE knowledge_object
                       SET authority_summary_json = CAST(:summary AS json),
                           consensus_state = 'single_source',
                           highest_authority_level = :highest
                       WHERE knowledge_object_id = :kid"""
                ),
                {
                    "summary": json.dumps(summary, ensure_ascii=False),
                    "highest": highest,
                    "kid": ko.knowledge_object_id,
                },
            )
            updated += 1

        session.commit()
        return {"backfilled": updated, "skipped": 0, "message": f"Backfilled {updated} KOs"}
    except Exception:
        session.rollback()
        raise
    finally:
        if close_session:
            session.close()


def main() -> int:
    result = backfill()
    print(result["message"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Backfill failed: {exc}")
        raise SystemExit(1)
