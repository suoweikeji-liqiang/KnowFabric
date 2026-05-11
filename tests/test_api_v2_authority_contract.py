"""Contract tests for v0.2 authority envelope and redistribution gating."""

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
    DocumentPageImageV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyMappingV2,
    VisualEvidenceAnchorV2,
)
from packages.db.session import Base, get_db
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_mapping_rows,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"


def _build_tables() -> list:
    return [
        Document.__table__,
        DocumentPage.__table__,
        ContentChunk.__table__,
        OntologyAliasV2.__table__,
        OntologyMappingV2.__table__,
        ChunkOntologyAnchorV2.__table__,
        KnowledgeObjectV2.__table__,
        KnowledgeObjectEvidenceV2.__table__,
        DocumentPageImageV2.__table__,
        VisualEvidenceAnchorV2.__table__,
    ]


def _build_client(tables: list | None = None) -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=tables or _build_tables())
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


def _seed_authority_fixture(session_factory: sessionmaker) -> None:
    """Seed a restricted document + OEM document with authority-typed KOs."""
    db = session_factory()
    try:
        long_evidence = (
            "6.5.3.2 Chilled Water Setpoint. The leaving chilled water temperature setpoint "
            "shall be 44F (6.7C) for comfort cooling applications. For process cooling "
            "applications requiring lower temperatures, the setpoint may be adjusted downward "
            "to a minimum of 40F (4.4C) provided that the chiller is equipped with low-temperature "
            "controls and the cooling coil is selected for the lower temperature. The setpoint "
            "shall be adjustable in 0.5F (0.3C) increments. The default value upon factory "
            "shipment shall be 44F (6.7C). Field adjustment requires level-2 access credentials "
            "and shall be recorded in the commissioning report per section 8.2.1."
        )
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_ashrae_restricted",
                    "file_hash": "hash_ashrae_001",
                    "storage_path": "/tmp/ashrae_901.pdf",
                    "file_name": "ASHRAE 90.1-2022",
                    "file_ext": "pdf",
                    "source_domain": "hvac",
                    "parse_status": "complete",
                    "is_active": True,
                    "authority_level": "industry_standard",
                    "publisher": "ASHRAE",
                    "standard_id": "ASHRAE 90.1-2022",
                    "language": "en",
                    "is_redistributable": False,
                    "authority_review_status": "human_confirmed",
                },
                {
                    "doc_id": "doc_trane_oem",
                    "file_hash": "hash_trane_001",
                    "storage_path": "/tmp/trane_cvgf.pdf",
                    "file_name": "Trane CVGF Operation Manual",
                    "file_ext": "pdf",
                    "source_domain": "hvac",
                    "parse_status": "complete",
                    "is_active": True,
                    "authority_level": "oem_manual",
                    "publisher": "Trane",
                    "standard_id": None,
                    "language": "en",
                    "vendor_brand": "Trane",
                    "vendor_model_family": "CVGF",
                    "is_redistributable": True,
                    "authority_review_status": "human_confirmed",
                },
            ],
        )
        for doc_id, page_id, page_no in [
            ("doc_ashrae_restricted", "page_ashrae_001", 42),
            ("doc_trane_oem", "page_trane_001", 29),
        ]:
            db.execute(
                DocumentPage.__table__.insert(),
                [
                    {
                        "page_id": page_id,
                        "doc_id": doc_id,
                        "page_no": page_no,
                        "cleaned_text": "Chilled water setpoint data",
                    }
                ],
            )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_ashrae_001",
                    "doc_id": "doc_ashrae_restricted",
                    "page_id": "page_ashrae_001",
                    "page_no": 42,
                    "chunk_index": 0,
                    "cleaned_text": long_evidence,
                    "text_excerpt": long_evidence[:200],
                    "chunk_type": "standard_clause",
                    "standard_clause": "6.5.3.2",
                    "clause_path": None,
                    "raw_text": None,
                    "evidence_anchor": None,
                },
                {
                    "chunk_id": "chunk_trane_001",
                    "doc_id": "doc_trane_oem",
                    "page_id": "page_trane_001",
                    "page_no": 29,
                    "chunk_index": 0,
                    "cleaned_text": "CHWS setpoint: 44F at ARI standard conditions",
                    "text_excerpt": "CHWS setpoint: 44F",
                    "chunk_type": "parameter_block",
                    "standard_clause": None,
                    "clause_path": None,
                    "raw_text": None,
                    "evidence_anchor": None,
                },
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_ashrae_001",
                    "chunk_id": "chunk_ashrae_001",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "domain_id": "hvac",
                    "ontology_class_id": "centrifugal_chiller",
                    "match_method": "seed",
                    "confidence_score": 0.95,
                    "is_primary": True,
                },
                {
                    "chunk_anchor_id": "anchor_trane_001",
                    "chunk_id": "chunk_trane_001",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "domain_id": "hvac",
                    "ontology_class_id": "centrifugal_chiller",
                    "match_method": "seed",
                    "confidence_score": 0.95,
                    "is_primary": True,
                },
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_ashrae_setpoint",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "parameter_spec",
                    "canonical_key": "chw_leaving_temp_setpoint",
                    "title": "Chilled Water Leaving Temperature Setpoint",
                    "summary": "ASHRAE 90.1 required CHWS setpoint",
                    "structured_payload_json": {"default_value": "44F", "parameter_category": "temperature"},
                    "confidence_score": 0.95,
                    "trust_level": "L4",
                    "review_status": "published",
                    "primary_chunk_id": "chunk_ashrae_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                    "authority_summary_json": {
                        "layers": [{
                            "authority_level": "industry_standard",
                            "publisher": "ASHRAE",
                            "citation": "ASHRAE 90.1-2022 §6.5.3.2",
                            "evidence_role": "primary",
                            "value_summary": "44F",
                        }]
                    },
                    "consensus_state": "single_source",
                    "highest_authority_level": "industry_standard",
                },
                {
                    "knowledge_object_id": "ko_trane_setpoint",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "parameter_spec",
                    "canonical_key": "chw_leaving_temp_setpoint_trane",
                    "title": "CHWS Setpoint",
                    "summary": "Trane CVGF CHWS setpoint",
                    "structured_payload_json": {"default_value": "44F", "parameter_category": "temperature"},
                    "confidence_score": 0.92,
                    "trust_level": "L4",
                    "review_status": "published",
                    "primary_chunk_id": "chunk_trane_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                    "authority_summary_json": {
                        "layers": [{
                            "authority_level": "oem_manual",
                            "publisher": "Trane",
                            "citation": "Trane CVGF Operation Manual p.29",
                            "evidence_role": "primary",
                            "value_summary": "44F",
                        }]
                    },
                    "consensus_state": "single_source",
                    "highest_authority_level": "oem_manual",
                },
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_ashrae_001",
                    "knowledge_object_id": "ko_ashrae_setpoint",
                    "chunk_id": "chunk_ashrae_001",
                    "doc_id": "doc_ashrae_restricted",
                    "page_id": "page_ashrae_001",
                    "page_no": 42,
                    "evidence_text": long_evidence,
                    "evidence_role": "primary",
                    "authority_role": "primary_standard",
                    "evidence_citation": "ASHRAE 90.1-2022 §6.5.3.2",
                },
                {
                    "knowledge_evidence_id": "koev_trane_001",
                    "knowledge_object_id": "ko_trane_setpoint",
                    "chunk_id": "chunk_trane_001",
                    "doc_id": "doc_trane_oem",
                    "page_id": "page_trane_001",
                    "page_no": 29,
                    "evidence_text": "CHWS setpoint: 44F at ARI standard conditions",
                    "evidence_role": "primary",
                    "authority_role": "primary_oem",
                    "evidence_citation": "Trane CVGF Operation Manual p.29",
                },
            ],
        )
        db.commit()
    finally:
        db.close()


# --- Test 1: redistribution gating without include_restricted_evidence ---

def test_redistribution_gating_paraphrases_restricted_evidence() -> None:
    """When is_redistributable=false and include_restricted_evidence is not set,
    evidence_text should be truncated and redistribution_restricted=true."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_authority_fixture(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?min_trust_level=L2"
        )
        payload = response.json()
        assert response.status_code == 200

        ashrae_item = next(
            (i for i in payload["data"]["items"] if i["knowledge_object_id"] == "ko_ashrae_setpoint"),
            None,
        )
        assert ashrae_item is not None, "ASHRAE KO should be in results"
        assert ashrae_item["consensus_state"] == "single_source"
        assert ashrae_item["highest_authority_level"] == "industry_standard"
        assert ashrae_item["redistribution_restricted"] is True

        ashrae_evidence = ashrae_item["evidence"][0]
        assert ashrae_evidence["redistribution_restricted"] is True
        assert len(ashrae_evidence["evidence_text"]) <= 203  # 200 + "..."
        assert ashrae_evidence["authority_role"] == "primary_standard"
        assert ashrae_evidence["evidence_citation"] == "ASHRAE 90.1-2022 §6.5.3.2"

        trane_item = next(
            (i for i in payload["data"]["items"] if i["knowledge_object_id"] == "ko_trane_setpoint"),
            None,
        )
        assert trane_item is not None, "Trane KO should be in results"
        assert trane_item["redistribution_restricted"] is False
        trane_evidence = trane_item["evidence"][0]
        assert "CHWS setpoint: 44F" in trane_evidence["evidence_text"]
    finally:
        app.dependency_overrides.clear()


# --- Test 2: include_restricted_evidence=true returns verbatim ---

def test_include_restricted_evidence_returns_verbatim() -> None:
    """When include_restricted_evidence=true, verbatim evidence_text is returned
    even for non-redistributable documents."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_authority_fixture(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?min_trust_level=L2&include_restricted_evidence=true"
        )
        payload = response.json()
        assert response.status_code == 200

        ashrae_item = next(
            (i for i in payload["data"]["items"] if i["knowledge_object_id"] == "ko_ashrae_setpoint"),
            None,
        )
        assert ashrae_item is not None
        assert ashrae_item["redistribution_restricted"] is False

        ashrae_evidence = ashrae_item["evidence"][0]
        assert ashrae_evidence["redistribution_restricted"] is False
        assert "6.5.3.2 Chilled Water Setpoint" in ashrae_evidence["evidence_text"]
        assert "low-temperature controls" in ashrae_evidence["evidence_text"]
    finally:
        app.dependency_overrides.clear()


# --- Test 3: min_authority_level filtering ---

def test_min_authority_level_filters_kos() -> None:
    """min_authority_level=oem_manual should exclude KOs with
    highest_authority_level=unspecified or lower-ranked levels."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_authority_fixture(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?min_trust_level=L2&min_authority_level=oem_manual"
        )
        payload = response.json()
        assert response.status_code == 200

        item_ids = {i["knowledge_object_id"] for i in payload["data"]["items"]}
        assert "ko_trane_setpoint" in item_ids
        assert "ko_ashrae_setpoint" in item_ids  # industry_standard > oem_manual
        assert payload["metadata"]["total_count"] == 2

        limited = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?min_trust_level=L2&min_authority_level=industry_standard"
        )
        limited_payload = limited.json()
        limited_ids = {i["knowledge_object_id"] for i in limited_payload["data"]["items"]}
        assert "ko_ashrae_setpoint" in limited_ids
        assert "ko_trane_setpoint" not in limited_ids
    finally:
        app.dependency_overrides.clear()


# --- Test 4: consensus_filter ---

def test_consensus_filter() -> None:
    """consensus_filter=single_source should only return KOs with that state."""

    client, session_factory = _build_client()
    try:
        _seed_ontology(session_factory)
        _seed_authority_fixture(session_factory)
        response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?min_trust_level=L2&consensus_filter=single_source"
        )
        payload = response.json()
        assert response.status_code == 200
        assert payload["metadata"]["total_count"] == 2

        none_response = client.get(
            "/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-profiles"
            "?min_trust_level=L2&consensus_filter=material_conflict"
        )
        none_payload = none_response.json()
        assert none_payload["metadata"]["total_count"] == 0
    finally:
        app.dependency_overrides.clear()
