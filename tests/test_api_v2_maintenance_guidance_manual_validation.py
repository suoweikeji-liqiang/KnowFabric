"""Manual-backed validation for the semantic maintenance guidance route."""

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
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_MANUAL_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_maintenance_guidance.json"
DRIVE_MANUAL_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_maintenance_guidance.json"
DRIVE_SOFT_STARTER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_soft_starter_baseline.json"


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


def _seed_domain_ontology(session_factory: sessionmaker, root: Path) -> None:
    bundle = load_domain_package_v2(root)
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


def _seed_manual_maintenance_entries(session_factory: sessionmaker, fixture_path: Path) -> None:
    original_session_local = seed_script.SessionLocal
    try:
        seed_script.SessionLocal = session_factory
        seed_script.seed_manual_fixture(fixture_path)
    finally:
        seed_script.SessionLocal = original_session_local


def test_manual_validation_maintenance_route_for_guoxiang_cleaning() -> None:
    """Manual-backed HVAC maintenance entries should resolve via maintenance-guidance."""

    client, session_factory = _build_client()
    try:
        _seed_domain_ontology(session_factory, HVAC_V2_ROOT)
        _seed_manual_maintenance_entries(session_factory, HVAC_MANUAL_FIXTURE)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/air_cooled_modular_heat_pump/maintenance-guidance"
            "?task_type=cleaning&brand=Guoxiang"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 2
        assert {item["knowledge_object_type"] for item in payload["data"]["items"]} == {
            "maintenance_procedure",
            "diagnostic_step",
        }
    finally:
        app.dependency_overrides.clear()


def test_manual_validation_maintenance_route_for_siemens_drive() -> None:
    """Manual-backed drive maintenance entries should resolve via maintenance-guidance."""

    client, session_factory = _build_client()
    try:
        _seed_domain_ontology(session_factory, DRIVE_V2_ROOT)
        _seed_manual_maintenance_entries(session_factory, DRIVE_MANUAL_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/maintenance-guidance"
            "?brand=Siemens&model_family=G120XA"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 2
        assert {item["knowledge_object_type"] for item in payload["data"]["items"]} == {
            "maintenance_procedure",
            "diagnostic_step",
        }
    finally:
        app.dependency_overrides.clear()


def test_manual_validation_maintenance_route_for_schneider_soft_starter() -> None:
    """Soft starter maintenance entries should resolve via maintenance-guidance."""

    client, session_factory = _build_client()
    try:
        _seed_domain_ontology(session_factory, DRIVE_V2_ROOT)
        _seed_manual_maintenance_entries(session_factory, DRIVE_SOFT_STARTER_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/soft_starter/maintenance-guidance"
            "?task_type=inspection&brand=Schneider"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["knowledge_object_type"] == "maintenance_procedure"
        assert payload["data"]["items"][0]["canonical_key"] == "inspect_terminals_and_ventilation_path"
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_manual_validation_maintenance_route_for_guoxiang_cleaning()
    test_manual_validation_maintenance_route_for_siemens_drive()
    test_manual_validation_maintenance_route_for_schneider_soft_starter()
    print("Manual-backed maintenance guidance validation checks passed")
