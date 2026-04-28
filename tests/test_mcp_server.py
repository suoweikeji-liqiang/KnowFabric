"""Tests for the minimal MCP server."""

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

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


def _seed_semantic_data(session_factory) -> None:
    bundle = load_domain_package_v2(HVAC_V2_ROOT)
    db = session_factory()
    try:
        db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
        db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
        mapping_rows = build_ontology_mapping_rows(bundle)
        if mapping_rows:
            db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_mcp_001",
                    "file_hash": "hash_mcp_001",
                    "storage_path": "/tmp/doc_mcp_001.pdf",
                    "file_name": "Carrier 19XR Combined Manual",
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
                    "page_id": "page_mcp_001",
                    "doc_id": "doc_mcp_001",
                    "page_no": 10,
                    "raw_text": "Carrier combined semantic data",
                    "cleaned_text": "Carrier combined semantic data",
                    "page_type": "technical_manual",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_mcp_001",
                    "doc_id": "doc_mcp_001",
                    "page_id": "page_mcp_001",
                    "page_no": 10,
                    "chunk_index": 0,
                    "raw_text": "Semantic combined evidence",
                    "cleaned_text": "Semantic combined evidence",
                    "text_excerpt": "Semantic combined evidence",
                    "chunk_type": "paragraph",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_mcp_001",
                    "chunk_id": "chunk_mcp_001",
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
                    "knowledge_object_id": "ko_mcp_param",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:centrifugal_chiller",
                    "ontology_class_id": "centrifugal_chiller",
                    "knowledge_object_type": "parameter_spec",
                    "canonical_key": "chw_leaving_temp_setpoint",
                    "title": "Chilled Water Leaving Temperature Setpoint",
                    "summary": "Default setpoint.",
                    "structured_payload_json": {
                        "parameter_name": "chw_leaving_temp_setpoint",
                        "parameter_category": "temperature",
                        "default_value": "7 C",
                    },
                    "applicability_json": {"brand": "Carrier"},
                    "confidence_score": 0.9,
                    "trust_level": "L2",
                    "review_status": "pending",
                    "primary_chunk_id": "chunk_mcp_001",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                }
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_mcp_param",
                    "knowledge_object_id": "ko_mcp_param",
                    "chunk_id": "chunk_mcp_001",
                    "doc_id": "doc_mcp_001",
                    "page_id": "page_mcp_001",
                    "page_no": 10,
                    "evidence_text": "Chilled water leaving temperature setpoint: 7 C",
                    "evidence_role": "primary",
                    "confidence_score": 0.9,
                }
            ],
        )
        db.commit()
    finally:
        db.close()


def test_tools_list_includes_semantic_tools() -> None:
    server = KnowFabricMcpServer()
    response = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tool_names = {tool["name"] for tool in response["result"]["tools"]}

    assert "search_knowledge" in tool_names
    assert "get_fault_knowledge" in tool_names
    assert "get_parameter_profile" in tool_names
    assert "get_maintenance_guidance" in tool_names
    assert "explain_equipment_class" in tool_names


def test_tools_call_parameter_profile_uses_semantic_service() -> None:
    session_factory = _build_session_factory()
    _seed_semantic_data(session_factory)
    server = KnowFabricMcpServer()
    server._with_session = lambda fn: fn(session_factory())  # type: ignore[method-assign]

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_parameter_profile",
                "arguments": {
                    "domain_id": "hvac",
                    "equipment_class_id": "centrifugal_chiller",
                    "brand": "Carrier",
                },
            },
        }
    )
    text_payload = response["result"]["content"][0]["text"]
    parsed = json.loads(text_payload)

    assert parsed["items"][0]["canonical_key"] == "chw_leaving_temp_setpoint"


if __name__ == "__main__":
    test_tools_list_includes_semantic_tools()
    test_tools_call_parameter_profile_uses_semantic_service()
    print("MCP server checks passed")
