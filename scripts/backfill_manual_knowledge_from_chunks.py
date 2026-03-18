#!/usr/bin/env python3
"""Backfill semantic rows from existing chunk evidence and manual fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyClassV2,
)
from packages.db.session import SessionLocal
from packages.domain_kit_v2.manual_fixture import (
    build_manual_semantic_rows,
    discover_manual_fixture_paths,
    load_manual_fixture,
)


def _merge_rows(session, model, rows: list[dict]) -> None:
    for row in rows:
        session.merge(model(**row))


def _load_ontology_class(session, equipment_class_key: str) -> OntologyClassV2:
    ontology_class = (
        session.query(OntologyClassV2)
        .filter(OntologyClassV2.ontology_class_key == equipment_class_key)
        .one_or_none()
    )
    if ontology_class is None:
        raise ValueError(
            "Missing ontology class for fixture. Run scripts/sync_ontology_package_v2.py first: "
            f"{equipment_class_key}"
        )
    return ontology_class


def _load_chunk_contexts(session, chunk_ids: list[str]) -> dict[str, dict[str, int | str]]:
    rows = (
        session.query(ContentChunk.chunk_id, ContentChunk.doc_id, ContentChunk.page_id, ContentChunk.page_no)
        .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
        .join(Document, ContentChunk.doc_id == Document.doc_id)
        .filter(ContentChunk.chunk_id.in_(chunk_ids))
        .all()
    )
    chunk_contexts = {
        row.chunk_id: {"doc_id": row.doc_id, "page_id": row.page_id, "page_no": row.page_no}
        for row in rows
    }
    missing = sorted(set(chunk_ids) - set(chunk_contexts))
    if missing:
        raise ValueError(f"Missing chunk rows for manual backfill: {', '.join(missing)}")
    return chunk_contexts


def backfill_manual_fixture_from_chunks(path: str | Path) -> tuple[str, int]:
    """Backfill anchors, knowledge objects, and evidence from existing chunks."""

    fixture = load_manual_fixture(path)
    chunk_ids = [entry["chunk"]["chunk_id"] for entry in fixture["manual_entries"]]
    session = SessionLocal()
    try:
        ontology_class = _load_ontology_class(session, fixture["equipment_class_key"])
        rows = build_manual_semantic_rows(
            fixture,
            package_version=ontology_class.package_version,
            ontology_version=ontology_class.ontology_version,
            chunk_contexts=_load_chunk_contexts(session, chunk_ids),
            match_method="manual_backfill",
        )
        _merge_rows(session, ChunkOntologyAnchorV2, rows["anchors"])
        _merge_rows(session, KnowledgeObjectV2, rows["knowledge_objects"])
        _merge_rows(session, KnowledgeObjectEvidenceV2, rows["evidence"])
        session.commit()
        return fixture["equipment_class_key"], len(rows["knowledge_objects"])
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> int:
    if len(sys.argv) > 1:
        fixture_paths = [Path(arg) for arg in sys.argv[1:]]
    else:
        fixture_paths = discover_manual_fixture_paths("tests/fixtures/manual_validation")

    if not fixture_paths:
        print("No manual validation fixtures found.")
        return 0

    for fixture_path in fixture_paths:
        equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(fixture_path)
        print(f"Backfilled {fixture_path.name} -> {equipment_class_key} ({knowledge_count} knowledge objects)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Manual chunk backfill failed: {exc}")
        raise SystemExit(1)
