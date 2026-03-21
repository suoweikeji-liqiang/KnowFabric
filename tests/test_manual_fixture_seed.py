"""Tests for seeding manual validation fixtures."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

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
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.seed_manual_validation_fixtures import seed_manual_fixture

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"
DRIVE_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_vfd_faults.json"
DRIVE_MAINTENANCE_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_maintenance_guidance.json"
DRIVE_SYMPTOM_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_symptoms.json"
DRIVE_SOFT_STARTER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_soft_starter_baseline.json"
DRIVE_FREQUENCY_CONVERTER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_frequency_converter_baseline.json"


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


def test_seed_manual_fixture_populates_hvac_rows(monkeypatch) -> None:
    """HVAC manual fixture should seed documents, chunks, anchors, and knowledge rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.seed_manual_validation_fixtures.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = seed_manual_fixture(HVAC_FIXTURE)
    db = session_factory()
    try:
        assert equipment_class_key == "hvac:air_cooled_modular_heat_pump"
        assert knowledge_count == 5
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "hvac").count() == 5
        assert db.query(ChunkOntologyAnchorV2).filter(ChunkOntologyAnchorV2.domain_id == "hvac").count() == 5
    finally:
        db.close()


def test_seed_manual_fixture_populates_drive_rows(monkeypatch) -> None:
    """Drive manual fixture should seed VFD semantic rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.seed_manual_validation_fixtures.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = seed_manual_fixture(DRIVE_FIXTURE)
    db = session_factory()
    try:
        assert equipment_class_key == "drive:variable_frequency_drive"
        assert knowledge_count == 4
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "drive").count() == 4
        assert db.query(KnowledgeObjectEvidenceV2).filter(KnowledgeObjectEvidenceV2.doc_id == "doc_abb_ach531_fw_manual").count() == 2
    finally:
        db.close()


def test_seed_manual_fixture_populates_drive_maintenance_rows(monkeypatch) -> None:
    """Drive maintenance fixture should seed maintenance guidance rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.seed_manual_validation_fixtures.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = seed_manual_fixture(DRIVE_MAINTENANCE_FIXTURE)
    db = session_factory()
    try:
        assert equipment_class_key == "drive:variable_frequency_drive"
        assert knowledge_count == 2
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "drive").count() == 2
        assert db.query(KnowledgeObjectEvidenceV2).filter(KnowledgeObjectEvidenceV2.doc_id == "doc_siemens_g120xa_manual").count() == 2
    finally:
        db.close()


def test_seed_manual_fixture_populates_drive_symptom_rows(monkeypatch) -> None:
    """Drive symptom fixture should seed symptom knowledge rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.seed_manual_validation_fixtures.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = seed_manual_fixture(DRIVE_SYMPTOM_FIXTURE)
    db = session_factory()
    try:
        assert equipment_class_key == "drive:variable_frequency_drive"
        assert knowledge_count == 2
        assert db.query(KnowledgeObjectV2).filter(
            KnowledgeObjectV2.domain_id == "drive",
            KnowledgeObjectV2.knowledge_object_type == "symptom",
        ).count() == 2
    finally:
        db.close()


def test_seed_manual_fixture_populates_soft_starter_rows(monkeypatch) -> None:
    """Soft starter baseline fixture should seed fault, parameter, and maintenance rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.seed_manual_validation_fixtures.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = seed_manual_fixture(DRIVE_SOFT_STARTER_FIXTURE)
    db = session_factory()
    try:
        assert equipment_class_key == "drive:soft_starter"
        assert knowledge_count == 3
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.ontology_class_id == "soft_starter").count() == 3
    finally:
        db.close()


def test_seed_manual_fixture_populates_frequency_converter_rows(monkeypatch) -> None:
    """Frequency converter baseline fixture should seed fault, parameter, and commissioning rows."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    monkeypatch.setattr("scripts.seed_manual_validation_fixtures.SessionLocal", session_factory)

    equipment_class_key, knowledge_count = seed_manual_fixture(DRIVE_FREQUENCY_CONVERTER_FIXTURE)
    db = session_factory()
    try:
        assert equipment_class_key == "drive:frequency_converter"
        assert knowledge_count == 3
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.ontology_class_id == "frequency_converter").count() == 3
    finally:
        db.close()


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
    test_seed_manual_fixture_populates_hvac_rows(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_seed_manual_fixture_populates_drive_rows(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_seed_manual_fixture_populates_drive_maintenance_rows(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_seed_manual_fixture_populates_drive_symptom_rows(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_seed_manual_fixture_populates_soft_starter_rows(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_seed_manual_fixture_populates_frequency_converter_rows(monkeypatch)
    monkeypatch.undo()
    print("Manual fixture seed checks passed")
