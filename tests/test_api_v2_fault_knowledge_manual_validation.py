"""Manual-backed validation for the semantic fault knowledge route."""

import json
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


def _load_fixture() -> dict:
    return json.loads(MANUAL_FIXTURE.read_text(encoding="utf-8"))


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


def _seed_manual_fault_entries(session_factory: sessionmaker) -> None:
    fixture = _load_fixture()
    db = session_factory()
    seen_docs: set[str] = set()
    seen_pages: set[str] = set()
    seen_chunks: set[str] = set()
    try:
        for entry in fixture["manual_entries"]:
            if entry["doc"]["doc_id"] not in seen_docs:
                db.merge(
                    Document(
                        doc_id=entry["doc"]["doc_id"],
                        file_hash=f"hash_{entry['doc']['doc_id']}",
                        storage_path=entry["source_manual"]["path"],
                        file_name=entry["doc"]["file_name"],
                        file_ext="pdf",
                        mime_type="application/pdf",
                        file_size=1,
                        source_domain=entry["doc"]["source_domain"],
                        parse_status="complete",
                        is_active=True,
                    )
                )
                seen_docs.add(entry["doc"]["doc_id"])
            if entry["page"]["page_id"] not in seen_pages:
                db.merge(
                    DocumentPage(
                        page_id=entry["page"]["page_id"],
                        doc_id=entry["doc"]["doc_id"],
                        page_no=entry["page"]["page_no"],
                        raw_text=entry["evidence"]["evidence_text"],
                        cleaned_text=entry["evidence"]["evidence_text"],
                        page_type=entry["page"]["page_type"],
                    )
                )
                seen_pages.add(entry["page"]["page_id"])
            if entry["chunk"]["chunk_id"] not in seen_chunks:
                db.merge(
                    ContentChunk(
                        chunk_id=entry["chunk"]["chunk_id"],
                        doc_id=entry["doc"]["doc_id"],
                        page_id=entry["page"]["page_id"],
                        page_no=entry["page"]["page_no"],
                        chunk_index=entry["chunk"]["chunk_index"],
                        raw_text=entry["chunk"]["cleaned_text"],
                        cleaned_text=entry["chunk"]["cleaned_text"],
                        text_excerpt=entry["chunk"]["text_excerpt"],
                        chunk_type=entry["chunk"]["chunk_type"],
                        evidence_anchor=f'{{"manual_page": {entry["source_manual"]["page_no"]}}}',
                    )
                )
                seen_chunks.add(entry["chunk"]["chunk_id"])
            db.merge(
                ChunkOntologyAnchorV2(
                    chunk_anchor_id=f'anchor_{entry["knowledge_object_id"]}',
                    chunk_id=entry["chunk"]["chunk_id"],
                    ontology_class_key=fixture["equipment_class_key"],
                    domain_id=fixture["domain_id"],
                    ontology_class_id=fixture["equipment_class_id"],
                    match_method="manual_validation",
                    confidence_score=entry["confidence_score"],
                    is_primary=True,
                    match_metadata_json={"source_manual": entry["source_manual"]["path"]},
                )
            )
            db.merge(
                KnowledgeObjectV2(
                    knowledge_object_id=entry["knowledge_object_id"],
                    domain_id=fixture["domain_id"],
                    ontology_class_key=fixture["equipment_class_key"],
                    ontology_class_id=fixture["equipment_class_id"],
                    knowledge_object_type="fault_code",
                    canonical_key=entry["canonical_key"],
                    title=entry["title"],
                    summary=entry["summary"],
                    structured_payload_json=entry["structured_payload"],
                    applicability_json=entry["applicability"],
                    confidence_score=entry["confidence_score"],
                    trust_level=entry["trust_level"],
                    review_status=entry["review_status"],
                    primary_chunk_id=entry["chunk"]["chunk_id"],
                    package_version="2.0.0-alpha",
                    ontology_version="2.0.0-alpha",
                )
            )
            db.merge(
                KnowledgeObjectEvidenceV2(
                    knowledge_evidence_id=entry["evidence"]["knowledge_evidence_id"],
                    knowledge_object_id=entry["knowledge_object_id"],
                    chunk_id=entry["chunk"]["chunk_id"],
                    doc_id=entry["doc"]["doc_id"],
                    page_id=entry["page"]["page_id"],
                    page_no=entry["page"]["page_no"],
                    evidence_text=entry["evidence"]["evidence_text"],
                    evidence_role=entry["evidence"]["evidence_role"],
                    confidence_score=entry["confidence_score"],
                )
            )
        db.commit()
    finally:
        db.close()


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
