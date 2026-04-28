"""API tests for rebuild-track parameter profile delivery."""

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


def _seed_ontology(session_factory: sessionmaker) -> None:
    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    db = session_factory()
    try:
        db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
        mapping_rows = build_ontology_mapping_rows(bundle)
        if mapping_rows:
            db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()


def _seed_parameter_profile(session_factory: sessionmaker) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_param_001",
                    "file_hash": "hash_param_001",
                    "storage_path": "/tmp/doc_param_001.pdf",
                    "file_name": "Carrier 19XR Parameter Guide",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 2048,
                    "source_domain": "hvac",
                    "parse_status": "complete",
                    "is_active": True,
                }
            ],
        )
        db.execute(
            DocumentPage.__table__.insert(),
            [
                {
                    "page_id": "page_param_001",
                    "doc_id": "doc_param_001",
                    "page_no": 18,
                    "raw_text": "P01 Chilled water setpoint",
                    "cleaned_text": "P01 Chilled water setpoint",
                    "page_type": "parameter_manual",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_param_001",
                    "doc_id": "doc_param_001",
                    "page_id": "page_param_001",
                    "page_no": 18,
                    "chunk_index": 0,
                    "raw_text": "Chilled water leaving temperature setpoint: 7 C",
                    "cleaned_text": "Chilled water leaving temperature setpoint: 7 C",
                    "text_excerpt": "Chilled water leaving temperature setpoint: 7 C",
                    "chunk_type": "parameter_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_param_001",
                    "chunk_id": "chunk_param_001",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "domain_id": "hvac",
                    "ontology_class_id": "centrifugal_chiller",
                    "match_method": "seed",
                    "confidence_score": 0.94,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                }
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_param_001",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "parameter_spec",
                    "canonical_key": "chw_leaving_temp_setpoint",
                    "title": "Chilled Water Leaving Temperature Setpoint",
                    "summary": "Default chilled water leaving temperature setpoint.",
                    "structured_payload_json": {
                        "parameter_name": "chw_leaving_temp_setpoint",
                        "parameter_category": "temperature",
                        "default_value": "7 C",
                    },
                    "applicability_json": {"brand": "Carrier", "model_family": "19XR"},
                    "confidence_score": 0.9,
                    "trust_level": "L2",
                    "review_status": "pending",
                    "primary_chunk_id": "chunk_param_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_perf_001",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "performance_spec",
                    "canonical_key": "cooling_capacity_rating",
                    "title": "Cooling Capacity Rating",
                    "summary": "Nominal cooling capacity.",
                    "structured_payload_json": {
                        "parameter_name": "cooling_capacity_rating",
                        "parameter_category": "capacity",
                        "rated_value": "1000 RT",
                    },
                    "applicability_json": {"brand": "Carrier", "model_family": "19XR"},
                    "confidence_score": 0.88,
                    "trust_level": "L2",
                    "review_status": "pending",
                    "primary_chunk_id": "chunk_param_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_param_001",
                    "knowledge_object_id": "ko_param_001",
                    "chunk_id": "chunk_param_001",
                    "doc_id": "doc_param_001",
                    "page_id": "page_param_001",
                    "page_no": 18,
                    "evidence_text": "Chilled water leaving temperature setpoint: 7 C",
                    "evidence_role": "primary",
                    "confidence_score": 0.9,
                },
                {
                    "knowledge_evidence_id": "koev_perf_001",
                    "knowledge_object_id": "ko_perf_001",
                    "chunk_id": "chunk_param_001",
                    "doc_id": "doc_param_001",
                    "page_id": "page_param_001",
                    "page_no": 18,
                    "evidence_text": "Rated cooling capacity: 1000 RT",
                    "evidence_role": "primary",
                    "confidence_score": 0.88,
                },
            ],
        )
        db.commit()
    finally:
        db.close()


def test_parameter_profiles_route_returns_parameter_and_performance_items() -> None:
    """Parameter profiles route should return matching semantic items."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_parameter_profile(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?brand=Carrier"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["metadata"]["query_type"] == "parameter_profile"
        assert len(payload["data"]["items"]) == 2
        assert {item["knowledge_object_type"] for item in payload["data"]["items"]} == {
            "parameter_spec",
            "performance_spec",
        }
    finally:
        app.dependency_overrides.clear()


def test_parameter_profiles_route_filters_by_category_and_name() -> None:
    """Parameter profile filters should narrow the result set."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_parameter_profile(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?parameter_category=temperature&parameter_name=chw_leaving_temp_setpoint&brand=Carrier"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["canonical_key"] == "chw_leaving_temp_setpoint"
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_parameter_profiles_route_returns_parameter_and_performance_items()
    test_parameter_profiles_route_filters_by_category_and_name()
    print("API v2 parameter profile route checks passed")
