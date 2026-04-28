#!/usr/bin/env python3
"""Seed semantic knowledge tables from manual validation fixtures."""

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
from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient
from packages.domain_kit_v2.manual_fixture import (
    DEFAULT_PACKAGE_VERSION,
    build_manual_fixture_rows,
    discover_manual_fixture_paths,
    load_manual_fixture,
)


def _merge_rows(session, model, rows: list[dict]) -> None:
    for row in rows:
        session.merge(model(**row))


def seed_manual_fixture(path: str | Path) -> tuple[str, int]:
    """Seed one manual validation fixture into semantic tables."""

    fixture = load_manual_fixture(path)
    session = SessionLocal()
    client = SwBaseModelOntologyClient()
    try:
        if client.get_equipment_class(fixture["equipment_class_key"]) is None:
            raise ValueError(f'Missing sw_base_model equipment class for fixture: {fixture["equipment_class_key"]}')
        rows = build_manual_fixture_rows(
            fixture,
            package_version=DEFAULT_PACKAGE_VERSION,
            ontology_version=client.ontology_version(),
        )

        _merge_rows(session, Document, rows["documents"])
        session.flush()
        _merge_rows(session, DocumentPage, rows["pages"])
        session.flush()
        _merge_rows(session, ContentChunk, rows["chunks"])
        session.flush()
        _merge_rows(session, ChunkOntologyAnchorV2, rows["anchors"])
        session.flush()
        _merge_rows(session, KnowledgeObjectV2, rows["knowledge_objects"])
        session.flush()
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
        equipment_class_key, knowledge_count = seed_manual_fixture(fixture_path)
        print(f"Seeded {fixture_path.name} -> {equipment_class_key} ({knowledge_count} knowledge objects)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Manual validation fixture seed failed: {exc}")
        raise SystemExit(1)
