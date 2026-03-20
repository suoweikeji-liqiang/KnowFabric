"""Tests for language-aware semantic display selection."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyClassV2,
)
from packages.db.session import Base
from packages.retrieval.semantic_service import SemanticRetrievalService


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            Document.__table__,
            DocumentPage.__table__,
            ContentChunk.__table__,
            OntologyClassV2.__table__,
            KnowledgeObjectV2.__table__,
            KnowledgeObjectEvidenceV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_localized_fault(session_factory) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_drive_cn",
                    "file_hash": "hash_drive_cn",
                    "storage_path": "/tmp/drive_cn.pdf",
                    "file_name": "Drive CN Manual.pdf",
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
                    "page_id": "page_drive_cn_1",
                    "doc_id": "doc_drive_cn",
                    "page_no": 1,
                    "raw_text": "A7C1 现场总线通讯",
                    "cleaned_text": "A7C1 现场总线通讯",
                    "page_type": "fault_code_reference",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_drive_cn_1",
                    "doc_id": "doc_drive_cn",
                    "page_id": "page_drive_cn_1",
                    "page_no": 1,
                    "chunk_index": 0,
                    "raw_text": "A7C1 现场总线通讯",
                    "cleaned_text": "A7C1 现场总线通讯",
                    "text_excerpt": "A7C1 现场总线通讯",
                    "chunk_type": "fault_code_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.execute(
            OntologyClassV2.__table__.insert(),
            [
                {
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "domain_id": "drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                    "parent_class_key": None,
                    "class_kind": "equipment",
                    "primary_label": "Variable Frequency Drive",
                    "labels_json": {"en": "Variable Frequency Drive", "zh": "变频驱动器"},
                    "knowledge_anchors_json": ["fault_code"],
                    "is_active": True,
                }
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_drive_a7c1",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "fault_code",
                    "canonical_key": "A7C1",
                    "title": "ABB A7C1 Fieldbus Communication Warning",
                    "summary": "Drive and fieldbus cyclic communication is lost.",
                    "structured_payload_json": {
                        "fault_code": "A7C1",
                        "fault_name": "Fieldbus Communication",
                        "recommended_actions": ["Check fieldbus status"],
                        "_localized_display": {
                            "zh": {
                                "title": "ABB A7C1 现场总线通讯警告",
                                "summary": "传动与现场总线之间的循环通讯已丢失。",
                                "structured_payload": {
                                    "fault_name": "现场总线通讯",
                                    "recommended_actions": ["检查现场总线状态"]
                                }
                            }
                        },
                    },
                    "applicability_json": {"brand": "ABB"},
                    "confidence_score": 0.93,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_drive_cn_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                }
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_drive_a7c1",
                    "knowledge_object_id": "ko_drive_a7c1",
                    "chunk_id": "chunk_drive_cn_1",
                    "doc_id": "doc_drive_cn",
                    "page_id": "page_drive_cn_1",
                    "page_no": 1,
                    "evidence_text": "A7C1 现场总线适配器A通讯信号丢失。",
                    "evidence_role": "primary",
                    "confidence_score": 0.93,
                }
            ],
        )
        db.commit()
    finally:
        db.close()


def test_semantic_service_returns_localized_display_and_preserves_evidence() -> None:
    session_factory = _build_session_factory()
    _seed_localized_fault(session_factory)
    db = session_factory()
    try:
        service = SemanticRetrievalService()
        payload = service.get_fault_knowledge(
            db=db,
            domain_id="drive",
            equipment_class_id="variable_frequency_drive",
            fault_code="A7C1",
            language="zh",
        )
    finally:
        db.close()

    assert payload is not None
    item = payload["items"][0]
    assert payload["equipment_class"]["label"] == "变频驱动器"
    assert item["title"] == "ABB A7C1 现场总线通讯警告"
    assert item["summary"] == "传动与现场总线之间的循环通讯已丢失。"
    assert item["structured_payload"]["fault_name"] == "现场总线通讯"
    assert item["structured_payload"]["recommended_actions"] == ["检查现场总线状态"]
    assert item["display_language"] == "zh"
    assert item["evidence"][0]["evidence_text"] == "A7C1 现场总线适配器A通讯信号丢失。"


def test_semantic_service_falls_back_to_english_when_language_is_missing() -> None:
    session_factory = _build_session_factory()
    _seed_localized_fault(session_factory)
    db = session_factory()
    try:
        service = SemanticRetrievalService()
        payload = service.get_fault_knowledge(
            db=db,
            domain_id="drive",
            equipment_class_id="variable_frequency_drive",
            fault_code="A7C1",
            language="ja",
        )
    finally:
        db.close()

    assert payload is not None
    item = payload["items"][0]
    assert item["title"] == "ABB A7C1 Fieldbus Communication Warning"
    assert item["display_language"] == "en"
