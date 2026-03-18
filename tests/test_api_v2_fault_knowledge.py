"""API tests for rebuild-track fault knowledge delivery."""

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


def _seed_document_chain(session_factory: sessionmaker) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_001",
                    "file_hash": "hash_001",
                    "storage_path": "/tmp/doc_001.pdf",
                    "file_name": "Carrier 19XR Service Manual",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024,
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
                    "page_id": "page_001",
                    "doc_id": "doc_001",
                    "page_no": 12,
                    "raw_text": "E01 overcurrent alarm",
                    "cleaned_text": "E01 overcurrent alarm",
                    "page_type": "fault_code_reference",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_001",
                    "doc_id": "doc_001",
                    "page_id": "page_001",
                    "page_no": 12,
                    "chunk_index": 0,
                    "raw_text": "E01: Overcurrent during acceleration",
                    "cleaned_text": "E01: Overcurrent during acceleration",
                    "text_excerpt": "E01: Overcurrent during acceleration",
                    "chunk_type": "fault_code_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.commit()
    finally:
        db.close()


def _seed_fault_knowledge_rows(session_factory: sessionmaker) -> None:
    db = session_factory()
    try:
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_001",
                    "chunk_id": "chunk_001",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "domain_id": "hvac",
                    "ontology_class_id": "centrifugal_chiller",
                    "match_method": "seed",
                    "confidence_score": 0.95,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                }
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_001",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "fault_code",
                    "canonical_key": "E01",
                    "title": "Fault Code E01",
                    "summary": "Overcurrent during acceleration.",
                    "structured_payload_json": {
                        "fault_code": "E01",
                        "severity": "high",
                        "recommended_actions": [
                            "Inspect compressor current",
                            "Check startup ramp",
                        ],
                    },
                    "applicability_json": {"brand": "Carrier", "model_family": "19XR"},
                    "confidence_score": 0.91,
                    "trust_level": "L2",
                    "review_status": "pending",
                    "primary_chunk_id": "chunk_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                }
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_001",
                    "knowledge_object_id": "ko_001",
                    "chunk_id": "chunk_001",
                    "doc_id": "doc_001",
                    "page_id": "page_001",
                    "page_no": 12,
                    "evidence_text": "E01: Overcurrent during acceleration",
                    "evidence_role": "primary",
                    "confidence_score": 0.91,
                }
            ],
        )
        db.commit()
    finally:
        db.close()


def _seed_fault_knowledge(session_factory: sessionmaker) -> None:
    _seed_ontology(session_factory)
    _seed_document_chain(session_factory)
    _seed_fault_knowledge_rows(session_factory)


def test_fault_knowledge_route_returns_evidence_grounded_items() -> None:
    """Fault route should return semantic knowledge with evidence."""

    client, session_factory = _build_client()
    try:
        _seed_fault_knowledge(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/fault-knowledge"
            "?fault_code=E01&brand=Carrier"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["metadata"]["query_type"] == "fault_knowledge"
        assert payload["data"]["equipment_class"]["equipment_class_id"] == "centrifugal_chiller"
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["knowledge_object_type"] == "fault_code"
        assert payload["data"]["items"][0]["confidence"] == 0.91
        assert payload["data"]["items"][0]["evidence"][0]["chunk_id"] == "chunk_001"
    finally:
        app.dependency_overrides.clear()


def test_fault_knowledge_route_filters_out_mismatched_brand() -> None:
    """Brand mismatch should yield an empty result set, not a 404."""

    client, session_factory = _build_client()
    try:
        _seed_fault_knowledge(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/fault-knowledge"
            "?fault_code=E01&brand=Trane"
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["data"]["items"] == []
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_fault_knowledge_route_returns_evidence_grounded_items()
    test_fault_knowledge_route_filters_out_mismatched_brand()
    print("API v2 fault knowledge route checks passed")
