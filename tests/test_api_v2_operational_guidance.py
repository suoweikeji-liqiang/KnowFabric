"""API tests for drive operational guidance delivery."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"


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


def _seed_operational_guidance(session_factory: sessionmaker) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_drive_ops_001",
                    "file_hash": "hash_drive_ops_001",
                    "storage_path": "/tmp/doc_drive_ops_001.pdf",
                    "file_name": "Drive Operational Guidance.pdf",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1,
                    "source_domain": "drive",
                    "parse_status": "complete",
                    "is_active": True,
                }
            ],
        )
        db.execute(
            DocumentPage.__table__.insert(),
            [
                {
                    "page_id": "page_drive_ops_001",
                    "doc_id": "doc_drive_ops_001",
                    "page_no": 12,
                    "raw_text": "combined drive guide knowledge",
                    "cleaned_text": "combined drive guide knowledge",
                    "page_type": "commissioning_guide",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_drive_ops_001",
                    "doc_id": "doc_drive_ops_001",
                    "page_id": "page_drive_ops_001",
                    "page_no": 12,
                    "chunk_index": 0,
                    "raw_text": "combined drive guide knowledge",
                    "cleaned_text": "combined drive guide knowledge",
                    "text_excerpt": "combined drive guide knowledge",
                    "chunk_type": "guidance_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_drive_ops_001",
                    "chunk_id": "chunk_drive_ops_001",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "domain_id": "drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                }
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_ops_commission",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "commissioning_step",
                    "canonical_key": "backup_drive_settings_after_commissioning",
                    "title": "Backup Drive Settings",
                    "summary": "Back up settings after commissioning.",
                    "structured_payload_json": {"step": "Back up settings", "commissioning_phase": "startup"},
                    "applicability_json": {"brand": "Siemens", "model_family": "G120XA"},
                    "confidence_score": 0.85,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_drive_ops_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_ops_wiring",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "wiring_guidance",
                    "canonical_key": "shield_grounding_control_cable_shield_360",
                    "title": "Control Cable Shield Grounding",
                    "summary": "Ground control cable shield 360 degrees.",
                    "structured_payload_json": {"wiring_topic": "shield_grounding", "guidance": "Ground shield 360 degrees"},
                    "applicability_json": {"brand": "ABB", "model_family": "ACH531"},
                    "confidence_score": 0.86,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_drive_ops_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_ops_application",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "application_guidance",
                    "canonical_key": "pump_fan_application_control",
                    "title": "Pump and Fan Application Control",
                    "summary": "Use the drive for pump and fan control applications.",
                    "structured_payload_json": {"application_type": "pump_fan", "guidance": "Use drive for pump and fan control"},
                    "applicability_json": {"brand": "Danfoss", "model_family": "FC111"},
                    "confidence_score": 0.87,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_drive_ops_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_ops_commission",
                    "knowledge_object_id": "ko_ops_commission",
                    "chunk_id": "chunk_drive_ops_001",
                    "doc_id": "doc_drive_ops_001",
                    "page_id": "page_drive_ops_001",
                    "page_no": 12,
                    "evidence_text": "Back up settings after commissioning",
                    "evidence_role": "primary",
                    "confidence_score": 0.85,
                },
                {
                    "knowledge_evidence_id": "koev_ops_wiring",
                    "knowledge_object_id": "ko_ops_wiring",
                    "chunk_id": "chunk_drive_ops_001",
                    "doc_id": "doc_drive_ops_001",
                    "page_id": "page_drive_ops_001",
                    "page_no": 12,
                    "evidence_text": "Ground shield 360 degrees",
                    "evidence_role": "primary",
                    "confidence_score": 0.86,
                },
                {
                    "knowledge_evidence_id": "koev_ops_application",
                    "knowledge_object_id": "ko_ops_application",
                    "chunk_id": "chunk_drive_ops_001",
                    "doc_id": "doc_drive_ops_001",
                    "page_id": "page_drive_ops_001",
                    "page_no": 12,
                    "evidence_text": "Use drive for pump and fan control",
                    "evidence_role": "primary",
                    "confidence_score": 0.87,
                },
            ],
        )
        db.commit()
    finally:
        db.close()


def test_operational_guidance_route_returns_drive_guide_types() -> None:
    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_operational_guidance(session_factory)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/operational-guidance"
        )
        payload = response.json()

        assert response.status_code == 200
        assert {item["knowledge_object_type"] for item in payload["data"]["items"]} == {
            "commissioning_step",
            "wiring_guidance",
            "application_guidance",
        }
    finally:
        app.dependency_overrides.clear()


def test_operational_guidance_route_can_filter_by_type() -> None:
    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_operational_guidance(session_factory)
        response = client.get(
            "/api/v2/domains/drive/equipment-classes/variable_frequency_drive/operational-guidance"
            "?guidance_type=wiring_guidance&brand=ABB"
        )
        payload = response.json()

        assert response.status_code == 200
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["knowledge_object_type"] == "wiring_guidance"
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_operational_guidance_route_returns_drive_guide_types()
    test_operational_guidance_route_can_filter_by_type()
    print("Operational guidance API checks passed")
