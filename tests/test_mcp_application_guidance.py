"""Tests for application guidance MCP exposure."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.mcp.main import KnowFabricMcpServer
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyClassV2,
    OntologyMappingV2,
)
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"


def _build_session_factory():
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
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_ontology(session_factory) -> None:
    db = session_factory()
    try:
        for root in (HVAC_V2_ROOT, DRIVE_V2_ROOT):
            bundle = load_domain_package_v2(root)
            db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
            db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
            mapping_rows = build_ontology_mapping_rows(bundle)
            if mapping_rows:
                db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()


def _seed_application_guidance(session_factory) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_danfoss_fc111_manual",
                    "file_hash": "hash_doc_danfoss_fc111_manual",
                    "storage_path": "/tmp/doc_danfoss_fc111_manual.pdf",
                    "file_name": "Danfoss FC111 Flow Drive Design Guide.pdf",
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
                    "page_id": "page_danfoss_fc111_14",
                    "doc_id": "doc_danfoss_fc111_manual",
                    "page_no": 14,
                    "raw_text": "pump and fan control flow and pressure behavior",
                    "cleaned_text": "pump and fan control flow and pressure behavior",
                    "page_type": "application_guide",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_danfoss_pump_fan_control",
                    "doc_id": "doc_danfoss_fc111_manual",
                    "page_id": "page_danfoss_fc111_14",
                    "page_no": 14,
                    "chunk_index": 0,
                    "raw_text": "pump and fan control flow and pressure behavior",
                    "cleaned_text": "pump and fan control flow and pressure behavior",
                    "text_excerpt": "pump and fan control applications",
                    "chunk_type": "guidance_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_drive_app_001",
                    "chunk_id": "chunk_danfoss_pump_fan_control",
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
                    "knowledge_object_id": "ko_drive_app_001",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "application_guidance",
                    "canonical_key": "pump_fan_application_control",
                    "title": "Pump and Fan Application Control",
                    "summary": "Flow drive guidance for pump and fan control.",
                    "structured_payload_json": {
                        "application_type": "pump_fan",
                        "guidance": "Use the drive application functions for pump and fan control.",
                    },
                    "applicability_json": {"brand": "Danfoss", "model_family": "FC111"},
                    "confidence_score": 0.86,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_danfoss_pump_fan_control",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                }
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_drive_app_001",
                    "knowledge_object_id": "ko_drive_app_001",
                    "chunk_id": "chunk_danfoss_pump_fan_control",
                    "doc_id": "doc_danfoss_fc111_manual",
                    "page_id": "page_danfoss_fc111_14",
                    "page_no": 14,
                    "evidence_text": "pump and fan control flow and pressure behavior",
                    "evidence_role": "primary",
                    "confidence_score": 0.86,
                }
            ],
        )
        db.commit()
    finally:
        db.close()


def test_tools_list_includes_application_guidance() -> None:
    server = KnowFabricMcpServer()
    names = {item["name"] for item in server._tools_list()["tools"]}
    assert "get_application_guidance" in names


def test_tools_call_application_guidance_uses_semantic_service(monkeypatch) -> None:
    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_application_guidance(session_factory)
    monkeypatch.setattr("apps.mcp.main.SessionLocal", session_factory)

    server = KnowFabricMcpServer()
    response = server._tools_call(
        {
            "name": "get_application_guidance",
            "arguments": {
                "domain_id": "drive",
                "equipment_class_id": "variable_frequency_drive",
                "application_type": "pump_fan",
                "brand": "Danfoss",
            },
        }
    )

    assert "application_guidance" in response["content"][0]["text"]


if __name__ == "__main__":
    class _MonkeyPatch:
        def __init__(self) -> None:
            self._patches = []

        def setattr(self, target: str, value) -> None:
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            original = getattr(module, attr_name)
            setattr(module, attr_name, value)
            self._patches.append((module, attr_name, original))

        def undo(self) -> None:
            while self._patches:
                module, attr_name, original = self._patches.pop()
                setattr(module, attr_name, original)

    monkeypatch = _MonkeyPatch()
    test_tools_list_includes_application_guidance()
    test_tools_call_application_guidance_uses_semantic_service(monkeypatch)
    monkeypatch.undo()
    print("Application guidance MCP checks passed")
