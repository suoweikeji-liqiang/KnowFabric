"""API tests for rebuild-track ontology class explanation."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2, OntologyMappingV2
from packages.db.session import Base, get_db
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"


def _build_client() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            OntologyClassV2.__table__,
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
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


def _seed_hvac(session_factory: sessionmaker) -> None:
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


def test_explain_equipment_class_route() -> None:
    """Route should return ontology metadata for a synced class."""

    client, session_factory = _build_client()
    try:
        _seed_hvac(session_factory)
        response = client.get("/api/v2/domains/hvac/equipment-classes/centrifugal_chiller")
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["equipment_class"]["equipment_class_id"] == "centrifugal_chiller"
        assert payload["data"]["equipment_class"]["domain_id"] == "hvac"
        assert payload["data"]["parent_class_id"] == "chiller"
        assert payload["metadata"]["query_type"] == "explain_equipment_class"
    finally:
        app.dependency_overrides.clear()


def test_explain_equipment_class_route_not_found() -> None:
    """Unknown classes should return 404."""

    client, _ = _build_client()
    try:
        response = client.get("/api/v2/domains/hvac/equipment-classes/does_not_exist")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_explain_equipment_class_route()
    test_explain_equipment_class_route_not_found()
    print("API v2 equipment class route checks passed")
