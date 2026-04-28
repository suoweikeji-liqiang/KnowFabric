"""Manual-backed validation for the semantic parameter profile route."""

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
VFD_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_parameter_profiles.json"
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
        db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
        mapping_rows = build_ontology_mapping_rows(bundle)
        if mapping_rows:
            db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()


def _seed_manual_parameter_entries(session_factory: sessionmaker, fixture_path: Path) -> None:
    original_session_local = seed_script.SessionLocal
    try:
        seed_script.SessionLocal = session_factory
        seed_script.seed_manual_fixture(fixture_path)
    finally:
        seed_script.SessionLocal = original_session_local


def test_manual_validation_parameter_route_for_siemens_temperature_thresholds() -> None:
    """Manual-backed Siemens parameter entries should resolve via parameter-profiles."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_manual_parameter_entries(session_factory, VFD_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/parameter-profiles"
            "?parameter_category=temperature_protection&brand=Siemens"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 2
        assert {item["canonical_key"] for item in payload["data"]["items"]} == {
            "p0604_motor_temperature_alarm_threshold",
            "p0605_motor_temperature_fault_threshold",
        }
    finally:
        app.dependency_overrides.clear()


def test_manual_validation_parameter_route_for_schneider_soft_starter() -> None:
    """Soft starter parameter entries should resolve via parameter-profiles."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_manual_parameter_entries(session_factory, SOFT_STARTER_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/soft_starter/parameter-profiles"
            "?parameter_category=startup_control&brand=Schneider"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["canonical_key"] == "acc_acceleration_ramp_time"
    finally:
        app.dependency_overrides.clear()


def test_manual_validation_parameter_route_for_danfoss_frequency_converter() -> None:
    """Frequency converter parameter entries should resolve via parameter-profiles."""

    client, session_factory = _build_client()
    try:
        _seed_drive_ontology(session_factory)
        _seed_manual_parameter_entries(session_factory, FREQUENCY_CONVERTER_FIXTURE)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/frequency_converter/parameter-profiles"
            "?parameter_category=speed_reference&brand=Danfoss"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["canonical_key"] == "003_local_reference_max_frequency"
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_manual_validation_parameter_route_for_siemens_temperature_thresholds()
    test_manual_validation_parameter_route_for_schneider_soft_starter()
    test_manual_validation_parameter_route_for_danfoss_frequency_converter()
    print("Manual-backed parameter profile validation checks passed")
