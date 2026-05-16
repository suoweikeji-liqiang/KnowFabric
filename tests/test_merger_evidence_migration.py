"""Regression tests for merger upsert evidence migration ordering."""

import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler import cross_source_merger
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import KnowledgeObjectEvidenceV2, KnowledgeObjectV2
from packages.db.session import Base


def _session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(
        engine,
        tables=[
            Document.__table__,
            DocumentPage.__table__,
            ContentChunk.__table__,
            KnowledgeObjectV2.__table__,
            KnowledgeObjectEvidenceV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_trace_rows(session):
    doc = Document(
        doc_id="doc_existing",
        file_hash="hash_existing",
        storage_path="/tmp/manual.pdf",
        file_name="manual.pdf",
        source_domain="hvac",
    )
    page = DocumentPage(
        page_id="page_existing",
        doc_id=doc.doc_id,
        page_no=1,
        raw_text="Oil temperature",
        cleaned_text="Oil temperature",
    )
    chunk = ContentChunk(
        chunk_id="chunk_existing",
        doc_id=doc.doc_id,
        page_id=page.page_id,
        page_no=1,
        chunk_index=0,
        raw_text="Oil temperature",
        cleaned_text="Oil temperature",
        chunk_type="paragraph",
    )
    session.add(doc)
    session.flush()
    session.add(page)
    session.flush()
    session.add(chunk)
    session.flush()


def _seed_existing_ko(session):
    existing = KnowledgeObjectV2(
        knowledge_object_id="ko_existing",
        domain_id="hvac",
        ontology_class_key="hvac:centrifugal_chiller",
        ontology_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
        canonical_key="hvac:centrifugal_chiller:parameter:supply_oil_temperature",
        title="Supply Oil Temperature",
        summary="Existing KO",
        structured_payload_json={"parameter_name": "Supply Oil Temperature"},
        confidence_score=0.9,
        trust_level="L4",
        review_status="published",
        primary_chunk_id="chunk_existing",
        authority_summary_json={"layers": []},
        consensus_state="single_source",
        package_version="2.0.0-alpha",
        ontology_version="2.0.0-alpha",
    )
    evidence = KnowledgeObjectEvidenceV2(
        knowledge_evidence_id="ev_existing",
        knowledge_object_id=existing.knowledge_object_id,
        chunk_id="chunk_existing",
        doc_id="doc_existing",
        page_id="page_existing",
        page_no=1,
        evidence_text="Oil temperature",
        evidence_role="primary",
    )
    session.add(existing)
    session.flush()
    session.add(evidence)


def test_ck_conflict_reuses_existing_target_before_evidence_migration(monkeypatch):
    """A new merged KO with an existing canonical key must not migrate into a missing target."""

    factory = _session_factory()
    session = factory()
    _seed_trace_rows(session)
    _seed_existing_ko(session)
    session.commit()

    def fake_merge_candidates(*_args, **_kwargs):
        return [{
            "knowledge_object_id": "ko_missing_target",
            "domain_id": "hvac",
            "ontology_class_key": "hvac:centrifugal_chiller",
            "ontology_class_id": "centrifugal_chiller",
            "knowledge_object_type": "parameter_spec",
            "canonical_key": "hvac:centrifugal_chiller:parameter:supply_oil_temperature",
            "title": "供油温度范围",
            "summary": "Merged KO",
            "structured_payload_json": {"parameter_name": "供油温度范围"},
            "confidence_score": 0.95,
            "trust_level": "L4",
            "review_status": "published",
            "primary_chunk_id": "chunk_existing",
            "authority_summary_json": {"layers": []},
            "consensus_state": "single_source",
            "conflict_summary": None,
            "highest_authority_level": "oem_manual",
            "deviation_justification_json": {},
            "package_version": "2.0.0-alpha",
            "ontology_version": "2.0.0-alpha",
            "_source_names": ["供油温度范围"],
            "evidence_rows": [],
        }]

    monkeypatch.setattr(cross_source_merger, "merge_candidates", fake_merge_candidates)

    stats = cross_source_merger.merge_with_existing(
        session,
        [{
            "title": "供油温度范围",
            "structured_payload": {"parameter_name": "供油温度范围"},
            "evidence": [{
                "chunk_id": "chunk_existing",
                "doc_id": "doc_existing",
                "page_id": "page_existing",
                "page_no": 1,
                "evidence_text": "Oil temperature",
                "evidence_role": "primary",
            }],
        }],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        ontology_class_key="hvac:centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )

    assert stats["new_merged"] == 1
    assert session.query(KnowledgeObjectV2).count() == 1
    assert session.query(KnowledgeObjectV2).first().knowledge_object_id == "ko_existing"
    assert session.query(KnowledgeObjectV2).filter_by(knowledge_object_id="ko_missing_target").count() == 0
