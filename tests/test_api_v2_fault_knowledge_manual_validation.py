"""Manual-backed validation for the semantic fault knowledge route."""

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
MANUAL_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"


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


def _seed_ontology(session_factory: sessionmaker) -> None:
    bundle = load_domain_package_v2(HVAC_V2_ROOT)
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

def _seed_manual_fault_entries(session_factory: sessionmaker) -> None:
    original_session_local = seed_script.SessionLocal
    try:
        seed_script.SessionLocal = session_factory
        seed_script.seed_manual_fixture(MANUAL_FIXTURE)
    finally:
        seed_script.SessionLocal = original_session_local


def test_manual_validation_fault_route_for_aux_module_faults() -> None:
    """AUX module faults from the manual should resolve through the semantic route."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_manual_fault_entries(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/air_cooled_modular_heat_pump/fault-knowledge"
            "?fault_code=E22&brand=AUX"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["equipment_class"]["equipment_class_id"] == "air_cooled_modular_heat_pump"
        assert payload["data"]["items"][0]["canonical_key"] == "E22"
        assert payload["data"]["items"][0]["structured_payload"]["fault_name"] == "High Pressure Switch Protection"
        assert payload["data"]["items"][0]["evidence"][0]["page_no"] == 4
    finally:
        app.dependency_overrides.clear()


def test_manual_validation_fault_route_for_guoxiang_module_faults() -> None:
    """Guoxiang module faults from the manual should resolve through the same class id."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_manual_fault_entries(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/air_cooled_modular_heat_pump/fault-knowledge"
            "?fault_code=49&brand=Guoxiang"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["items"][0]["canonical_key"] == "49"
        assert payload["data"]["items"][0]["structured_payload"]["fault_name"] == "1#/3# Compressor High Pressure"
        assert payload["data"]["items"][0]["evidence"][0]["page_no"] == 48
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_manual_validation_fault_route_for_aux_module_faults()
    test_manual_validation_fault_route_for_guoxiang_module_faults()
    print("Manual-backed fault knowledge validation checks passed")
