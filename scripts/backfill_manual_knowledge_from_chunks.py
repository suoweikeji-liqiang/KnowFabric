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
)
from packages.db.session import SessionLocal
from packages.domain_kit_v2.manual_fixture import (
    DEFAULT_PACKAGE_VERSION,
    build_manual_semantic_rows,
    discover_manual_fixture_paths,
    load_manual_fixture,
)
from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient


def _merge_rows(session, model, rows: list[dict]) -> None:
    for row in rows:
        session.merge(model(**row))


def _dedupe_new_anchor_rows(session, rows: list[dict]) -> list[dict]:
    """Keep one anchor per chunk/class pair and skip anchors already in storage."""

    unique_rows: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["chunk_id"], row["ontology_class_key"])
        unique_rows.setdefault(key, row)

    existing_keys = set()
    for chunk_id, ontology_class_key in unique_rows:
        existing = (
            session.query(ChunkOntologyAnchorV2.chunk_anchor_id)
            .filter(
                ChunkOntologyAnchorV2.chunk_id == chunk_id,
                ChunkOntologyAnchorV2.ontology_class_key == ontology_class_key,
            )
            .one_or_none()
        )
        if existing is not None:
            existing_keys.add((chunk_id, ontology_class_key))

    return [
        row
        for key, row in unique_rows.items()
        if key not in existing_keys
    ]


def _dedupe_new_evidence_rows(session, rows: list[dict]) -> list[dict]:
    """Skip evidence rows already attached to the same KO/chunk/role."""

    unique_rows: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        key = (row["knowledge_object_id"], row["chunk_id"], row["evidence_role"])
        unique_rows.setdefault(key, row)

    existing_keys = set()
    for knowledge_object_id, chunk_id, evidence_role in unique_rows:
        existing = (
            session.query(KnowledgeObjectEvidenceV2.knowledge_evidence_id)
            .filter(
                KnowledgeObjectEvidenceV2.knowledge_object_id == knowledge_object_id,
                KnowledgeObjectEvidenceV2.chunk_id == chunk_id,
                KnowledgeObjectEvidenceV2.evidence_role == evidence_role,
            )
            .one_or_none()
        )
        if existing is not None:
            existing_keys.add((knowledge_object_id, chunk_id, evidence_role))

    return [
        row
        for key, row in unique_rows.items()
        if key not in existing_keys
    ]


def _dedupe_new_knowledge_rows(session, rows: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Skip existing canonical KOs and map new IDs to stored IDs for evidence."""

    unique_rows: dict[tuple[str, str, str, str], dict] = {}
    id_map: dict[str, str] = {}
    for row in rows:
        key = (
            row["domain_id"],
            row["ontology_class_id"],
            row["knowledge_object_type"],
            row["canonical_key"],
        )
        existing = unique_rows.get(key)
        if existing is None:
            unique_rows[key] = row
        else:
            id_map[row["knowledge_object_id"]] = existing["knowledge_object_id"]

    existing_rows = (
        session.query(
            KnowledgeObjectV2.knowledge_object_id,
            KnowledgeObjectV2.domain_id,
            KnowledgeObjectV2.ontology_class_id,
            KnowledgeObjectV2.knowledge_object_type,
            KnowledgeObjectV2.canonical_key,
        )
        .filter(
            KnowledgeObjectV2.canonical_key.in_(
                [row["canonical_key"] for row in unique_rows.values()]
            )
        )
        .all()
    )
    existing_by_key = {
        (row.domain_id, row.ontology_class_id, row.knowledge_object_type, row.canonical_key): row.knowledge_object_id
        for row in existing_rows
    }
    for key, row in unique_rows.items():
        if key in existing_by_key:
            id_map[row["knowledge_object_id"]] = existing_by_key[key]
    return [row for key, row in unique_rows.items() if key not in existing_by_key], id_map


def _remap_evidence_knowledge_ids(rows: list[dict], id_map: dict[str, str]) -> list[dict]:
    return [
        {**row, "knowledge_object_id": id_map.get(row["knowledge_object_id"], row["knowledge_object_id"])}
        for row in rows
    ]


def _load_equipment_class(client: SwBaseModelOntologyClient, equipment_class_key: str) -> dict:
    equipment_class = client.get_equipment_class(equipment_class_key)
    if equipment_class is None:
        raise ValueError(f"Missing sw_base_model equipment class for fixture: {equipment_class_key}")
    return equipment_class


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


def _fixture_chunk_ids(fixture: dict) -> list[str]:
    chunk_ids = []
    for entry in fixture["manual_entries"]:
        chunk_ids.append(entry["chunk"]["chunk_id"])
        chunk_ids.extend(
            evidence["chunk"]["chunk_id"]
            for evidence in entry.get("additional_evidence", [])
            if isinstance(evidence, dict)
        )
    return list(dict.fromkeys(chunk_ids))


def backfill_manual_fixture_from_chunks(path: str | Path) -> tuple[str, int]:
    """Backfill anchors, knowledge objects, and evidence from existing chunks."""

    fixture = load_manual_fixture(path)
    chunk_ids = _fixture_chunk_ids(fixture)
    session = SessionLocal()
    client = SwBaseModelOntologyClient()
    try:
        _load_equipment_class(client, fixture["equipment_class_key"])
        rows = build_manual_semantic_rows(
            fixture,
            package_version=DEFAULT_PACKAGE_VERSION,
            ontology_version=client.ontology_version(),
            chunk_contexts=_load_chunk_contexts(session, chunk_ids),
            match_method="manual_backfill",
        )
        knowledge_count = len(rows["knowledge_objects"])
        rows["anchors"] = _dedupe_new_anchor_rows(session, rows["anchors"])
        rows["knowledge_objects"], id_map = _dedupe_new_knowledge_rows(session, rows["knowledge_objects"])
        rows["evidence"] = _dedupe_new_evidence_rows(
            session,
            _remap_evidence_knowledge_ids(rows["evidence"], id_map),
        )
        _merge_rows(session, ChunkOntologyAnchorV2, rows["anchors"])
        session.flush()
        _merge_rows(session, KnowledgeObjectV2, rows["knowledge_objects"])
        session.flush()
        _merge_rows(session, KnowledgeObjectEvidenceV2, rows["evidence"])
        session.commit()
        return fixture["equipment_class_key"], knowledge_count
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
