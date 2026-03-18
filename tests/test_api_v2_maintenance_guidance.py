"""API tests for rebuild-track maintenance guidance delivery."""

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
        db.execute(OntologyMappingV2.__table__.insert(), build_ontology_mapping_rows(bundle))
        db.commit()
    finally:
        db.close()


def _seed_maintenance_guidance(session_factory: sessionmaker) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_maint_001",
                    "file_hash": "hash_maint_001",
                    "storage_path": "/tmp/doc_maint_001.pdf",
                    "file_name": "Carrier 19XR Maintenance Manual",
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
                    "page_id": "page_maint_001",
                    "doc_id": "doc_maint_001",
                    "page_no": 25,
                    "raw_text": "Inspect condenser tubes and clean fouling",
                    "cleaned_text": "Inspect condenser tubes and clean fouling",
                    "page_type": "maintenance_guide",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_maint_001",
                    "doc_id": "doc_maint_001",
                    "page_id": "page_maint_001",
                    "page_no": 25,
                    "chunk_index": 0,
                    "raw_text": "Monthly condenser cleaning and verification.",
                    "cleaned_text": "Monthly condenser cleaning and verification.",
                    "text_excerpt": "Monthly condenser cleaning and verification.",
                    "chunk_type": "procedure_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_maint_001",
                    "chunk_id": "chunk_maint_001",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "domain_id": "hvac",
                    "ontology_class_id": "centrifugal_chiller",
                    "match_method": "seed",
                    "confidence_score": 0.93,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                }
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_maint_001",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "maintenance_procedure",
                    "canonical_key": "monthly_condenser_cleaning",
                    "title": "Monthly Condenser Cleaning",
                    "summary": "Clean condenser tubes every month.",
                    "structured_payload_json": {
                        "maintenance_task": "cleaning",
                        "task_type": "cleaning",
                        "steps": ["Inspect condenser tubes", "Remove fouling"],
                    },
                    "applicability_json": {"brand": "Carrier", "model_family": "19XR"},
                    "confidence_score": 0.89,
                    "trust_level": "L2",
                    "review_status": "pending",
                    "primary_chunk_id": "chunk_maint_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_diag_001",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "diagnostic_step",
                    "canonical_key": "verify_condensing_pressure",
                    "title": "Verify Condensing Pressure",
                    "summary": "Verify condensing pressure after cleaning.",
                    "structured_payload_json": {
                        "task_type": "cleaning",
                        "step": "Verify condensing pressure after cleaning",
                    },
                    "applicability_json": {"brand": "Carrier", "model_family": "19XR"},
                    "confidence_score": 0.86,
                    "trust_level": "L2",
                    "review_status": "pending",
                    "primary_chunk_id": "chunk_maint_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_maint_001",
                    "knowledge_object_id": "ko_maint_001",
                    "chunk_id": "chunk_maint_001",
                    "doc_id": "doc_maint_001",
                    "page_id": "page_maint_001",
                    "page_no": 25,
                    "evidence_text": "Inspect condenser tubes and clean fouling",
                    "evidence_role": "primary",
                    "confidence_score": 0.89,
                },
                {
                    "knowledge_evidence_id": "koev_diag_001",
                    "knowledge_object_id": "ko_diag_001",
                    "chunk_id": "chunk_maint_001",
                    "doc_id": "doc_maint_001",
                    "page_id": "page_maint_001",
                    "page_no": 25,
                    "evidence_text": "Verify condensing pressure after cleaning",
                    "evidence_role": "primary",
                    "confidence_score": 0.86,
                },
            ],
        )
        db.commit()
    finally:
        db.close()


def test_maintenance_guidance_route_returns_maintenance_and_diagnostic_items() -> None:
    """Maintenance route should return procedure and linked diagnostic items."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_maintenance_guidance(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/maintenance-guidance"
            "?brand=Carrier"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["metadata"]["query_type"] == "maintenance_guidance"
        assert len(payload["data"]["items"]) == 2
        assert {item["knowledge_object_type"] for item in payload["data"]["items"]} == {
            "maintenance_procedure",
            "diagnostic_step",
        }
    finally:
        app.dependency_overrides.clear()


def test_maintenance_guidance_route_can_exclude_diagnostic_steps() -> None:
    """Maintenance route should support excluding linked diagnostic steps."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_maintenance_guidance(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/maintenance-guidance"
            "?task_type=cleaning&brand=Carrier&include_diagnostic_steps=false"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["knowledge_object_type"] == "maintenance_procedure"
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_maintenance_guidance_route_returns_maintenance_and_diagnostic_items()
    test_maintenance_guidance_route_can_exclude_diagnostic_steps()
    print("API v2 maintenance guidance route checks passed")
