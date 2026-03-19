"""Tests for chunk-backed manual semantic backfill."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyClassV2,
    OntologyMappingV2,
)
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.manual_fixture import build_manual_fixture_rows, load_manual_fixture
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.backfill_manual_knowledge_from_chunks import backfill_manual_fixture_from_chunks

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"
DRIVE_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_vfd_faults.json"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            Document.__table__,
            DocumentPage.__table__,
            ContentChunk.__table__,
            OntologyClassV2.__table__,
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
            ChunkOntologyAnchorV2.__table__,
            KnowledgeObjectV2.__table__,
            KnowledgeObjectEvidenceV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_ontology(session_factory) -> None:
    db = session_factory()
    try:
        for root in (HVAC_V2_ROOT, DRIVE_V2_ROOT):
            bundle = load_domain_package_v2(root)
            db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
            db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
            db.execute(OntologyMappingV2.__table__.insert(), build_ontology_mapping_rows(bundle))
        db.commit()
    finally:
        db.close()


def _seed_chunk_layers(session_factory, fixture_path: Path) -> None:
    fixture = load_manual_fixture(fixture_path)
    rows = build_manual_fixture_rows(fixture)
    db = session_factory()
    try:
        db.execute(Document.__table__.insert(), rows["documents"])
        db.execute(DocumentPage.__table__.insert(), rows["pages"])
        db.execute(ContentChunk.__table__.insert(), rows["chunks"])
        db.commit()
    finally:
        db.close()


def test_backfill_manual_fixture_from_chunks_for_hvac(monkeypatch) -> None:
    """HVAC manual entries should backfill semantic rows from pre-existing chunks."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_chunk_layers(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(HVAC_FIXTURE)
    db = session_factory()
    try:
        evidence = (
            db.query(KnowledgeObjectEvidenceV2)
            .filter(KnowledgeObjectEvidenceV2.knowledge_object_id == "ko_aux_e01")
            .one()
        )
        anchor = (
            db.query(ChunkOntologyAnchorV2)
            .filter(ChunkOntologyAnchorV2.chunk_id == "chunk_aux_module_faults_e01")
            .one()
        )
        assert equipment_class_key == "hvac:air_cooled_modular_heat_pump"
        assert knowledge_count == 5
        assert db.query(Document).count() == 2
        assert db.query(ContentChunk).count() == 5
        assert anchor.match_method == "manual_backfill"
        assert anchor.match_metadata_json["source_manual_page_no"] == 3
        assert evidence.doc_id == "doc_aux_module_faults"
        assert evidence.page_id == "page_aux_module_faults_3"
        assert evidence.page_no == 3
    finally:
        db.close()


def test_backfill_manual_fixture_from_chunks_for_drive(monkeypatch) -> None:
    """Drive manual entries should backfill knowledge objects using ontology versions."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_chunk_layers(session_factory, DRIVE_FIXTURE)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(DRIVE_FIXTURE)
    db = session_factory()
    try:
        ontology_class = (
            db.query(OntologyClassV2)
            .filter(OntologyClassV2.ontology_class_key == "drive:variable_frequency_drive")
            .one()
        )
        knowledge_object = (
            db.query(KnowledgeObjectV2)
            .filter(KnowledgeObjectV2.knowledge_object_id == "ko_abb_a7c1")
            .one()
        )
        assert equipment_class_key == "drive:variable_frequency_drive"
        assert knowledge_count == 4
        assert knowledge_object.package_version == ontology_class.package_version
        assert knowledge_object.ontology_version == ontology_class.ontology_version
    finally:
        db.close()


def test_backfill_manual_fixture_from_chunks_requires_existing_chunk_rows(monkeypatch) -> None:
    """Backfill should fail instead of inventing missing chunk/page/document rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    try:
        backfill_manual_fixture_from_chunks(HVAC_FIXTURE)
    except ValueError as exc:
        assert "Missing chunk rows for manual backfill" in str(exc)
    else:
        raise AssertionError("Expected missing chunk rows error")


if __name__ == "__main__":
    class _MonkeyPatch:
        def __init__(self) -> None:
            self._patches = []

        def setattr(self, target: str, value) -> None:
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            original = getattr(module, attr_name)
            setattr(module, attr_name, value)
            self._patches.append((module, attr_name, original))

        def undo(self) -> None:
            while self._patches:
                module, attr_name, original = self._patches.pop()
                setattr(module, attr_name, original)

    monkeypatch = _MonkeyPatch()
    test_backfill_manual_fixture_from_chunks_for_hvac(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_backfill_manual_fixture_from_chunks_for_drive(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_backfill_manual_fixture_from_chunks_requires_existing_chunk_rows(monkeypatch)
    monkeypatch.undo()
    print("Manual chunk backfill checks passed")
