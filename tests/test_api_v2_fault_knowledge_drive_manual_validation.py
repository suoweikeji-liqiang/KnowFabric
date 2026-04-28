"""Manual-backed validation for drive fault knowledge delivery."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyClassV2,
    OntologyMappingV2,
)
from packages.db.session import Base, get_db
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts import seed_manual_validation_fixtures as seed_script

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
FAULT_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_vfd_faults.json"
SYMPTOM_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_symptoms.json"
SOFT_STARTER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_soft_starter_baseline.json"
FREQUENCY_CONVERTER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_frequency_converter_baseline.json"


def _build_client() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session


def _seed_drive_ontology(session_factory: sessionmaker) -> None:
    bundle = load_domain_package_v2(DRIVE_V2_ROOT)
    db = session_factory()
    try:
        db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
        db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
        mapping_rows = build_ontology_mapping_rows(bundle)
        if mapping_rows:
            db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()

def _seed_drive_manual_fault_entries(session_factory: sessionmaker, *fixture_paths: Path) -> None:
    original_session_local = seed_script.SessionLocal
    try:
        seed_script.SessionLocal = session_factory
        for fixture_path in fixture_paths:
            seed_script.seed_manual_fixture(fixture_path)
    finally:
        seed_script.SessionLocal = original_session_local


def test_drive_manual_validation_route_for_abb_fault() -> None:
    """ABB ACH531 fieldbus fault should resolve via the semantic route."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_drive_manual_fault_entries(session_factory, FAULT_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/fault-knowledge"
            "?fault_code=A7C1&brand=ABB"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["equipment_class"]["equipment_class_id"] == "variable_frequency_drive"
        assert payload["data"]["items"][0]["canonical_key"] == "A7C1"
        assert payload["data"]["items"][0]["structured_payload"]["fault_name"] == "Fieldbus Adapter A Communication"
        assert payload["data"]["items"][0]["evidence"][0]["page_no"] == 133
    finally:
        app.dependency_overrides.clear()


def test_drive_manual_validation_route_for_siemens_fault() -> None:
    """Siemens G120XA motor overtemperature fault should resolve via the same class id."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_drive_manual_fault_entries(session_factory, FAULT_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/fault-knowledge"
            "?fault_code=F07011&brand=Siemens"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["items"][0]["canonical_key"] == "F07011"
        assert payload["data"]["items"][0]["structured_payload"]["fault_name"] == "Motor Overtemperature Fault"
        assert payload["data"]["items"][0]["evidence"][0]["page_no"] == 400
    finally:
        app.dependency_overrides.clear()


def test_drive_manual_validation_route_can_include_related_symptom() -> None:
    """Fault knowledge route should return reviewed symptom entries when enabled."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_drive_manual_fault_entries(session_factory, FAULT_FIXTURE, SYMPTOM_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/fault-knowledge"
            "?fault_code=F07011&brand=Siemens&include_related_symptoms=true"
        )
        payload = response.json()

        assert response.status_code == 200
        assert {item["knowledge_object_type"] for item in payload["data"]["items"]} == {
            "fault_code",
            "symptom",
        }
    finally:
        app.dependency_overrides.clear()


def test_drive_manual_validation_route_can_exclude_related_symptom() -> None:
    """Fault knowledge route should suppress symptom entries when requested."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_drive_manual_fault_entries(session_factory, FAULT_FIXTURE, SYMPTOM_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/fault-knowledge"
            "?fault_code=F07011&brand=Siemens&include_related_symptoms=false"
        )
        payload = response.json()

        assert response.status_code == 200
        assert [item["knowledge_object_type"] for item in payload["data"]["items"]] == ["fault_code"]
    finally:
        app.dependency_overrides.clear()


def test_soft_starter_manual_validation_route_for_schneider_fault() -> None:
    """Soft starter fault entries should resolve through the semantic fault route."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_drive_manual_fault_entries(session_factory, SOFT_STARTER_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/soft_starter/fault-knowledge"
            "?fault_code=OCF&brand=Schneider"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["equipment_class"]["equipment_class_id"] == "soft_starter"
        assert payload["data"]["items"][0]["canonical_key"] == "OCF"
        assert payload["data"]["items"][0]["structured_payload"]["fault_name"] == "Overcurrent Fault"
    finally:
        app.dependency_overrides.clear()


def test_frequency_converter_manual_validation_route_for_danfoss_fault() -> None:
    """Frequency converter fault entries should resolve through the semantic fault route."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_drive_manual_fault_entries(session_factory, FREQUENCY_CONVERTER_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/frequency_converter/fault-knowledge"
            "?fault_code=16&brand=Danfoss"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["equipment_class"]["equipment_class_id"] == "frequency_converter"
        assert payload["data"]["items"][0]["canonical_key"] == "16"
        assert payload["data"]["items"][0]["structured_payload"]["fault_name"] == "Short Circuit Fault"
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_drive_manual_validation_route_for_abb_fault()
    test_drive_manual_validation_route_for_siemens_fault()
    test_drive_manual_validation_route_can_include_related_symptom()
    test_drive_manual_validation_route_can_exclude_related_symptom()
    test_soft_starter_manual_validation_route_for_schneider_fault()
    test_frequency_converter_manual_validation_route_for_danfoss_fault()
    print("Drive manual-backed fault knowledge validation checks passed")
