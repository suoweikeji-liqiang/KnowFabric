"""Tests for rebuild-track semantic API and MCP contracts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.core.semantic_contract_v2 import (
    FaultKnowledgeQuery,
    MCP_TOOL_GET_FAULT_KNOWLEDGE,
    SEMANTIC_MCP_TOOLS_V2,
    SemanticApiEnvelope,
)


def test_fault_query_defaults() -> None:
    """Fault query contract should apply stable defaults."""

    query = FaultKnowledgeQuery(domain_id="hvac", equipment_class_id="centrifugal_chiller")
    assert query.limit == 20
    assert query.min_trust_level == "L4"
    assert query.include_related_symptoms is True
    assert query.language == "en"


def test_mcp_tool_names_present() -> None:
    """Semantic MCP tool set should expose the minimum rebuild query set."""

    tool_names = {tool["name"] for tool in SEMANTIC_MCP_TOOLS_V2}
    assert MCP_TOOL_GET_FAULT_KNOWLEDGE["name"] in tool_names
    assert "get_parameter_profile" in tool_names
    assert "get_maintenance_guidance" in tool_names
    assert "language" in MCP_TOOL_GET_FAULT_KNOWLEDGE["inputSchema"]["properties"]


def test_semantic_envelope_shape() -> None:
    """Semantic API envelope should preserve evidence and ontology ids."""

    payload = SemanticApiEnvelope.model_validate(
        {
            "success": True,
            "data": {
                "equipment_class": {
                    "equipment_class_id": "centrifugal_chiller",
                    "label": "Centrifugal Chiller",
                    "domain_id": "hvac",
                },
                "items": [
                    {
                        "knowledge_object_id": "ko_001",
                        "knowledge_object_type": "fault_code",
                        "canonical_key": "E01",
                        "equipment_class": {
                            "equipment_class_id": "centrifugal_chiller",
                            "label": "Centrifugal Chiller",
                            "domain_id": "hvac",
                        },
                        "summary": "Overcurrent during acceleration.",
                        "display_language": "en",
                        "structured_payload": {"fault_code": "E01"},
                        "trust_level": "L2",
                        "review_status": "pending",
                        "evidence": [
                            {
                                "doc_id": "doc_001",
                                "page_no": 12,
                                "chunk_id": "chunk_001",
                                "evidence_text": "E01: Overcurrent during acceleration",
                                "evidence_role": "primary",
                            }
                        ],
                    }
                ],
            },
            "metadata": {
                "query_type": "fault_knowledge",
                "filters_applied": {"domain_id": "hvac", "equipment_class_id": "centrifugal_chiller"},
                "total": 1,
                "limit": 20,
                "requested_language": "en",
                "display_fallback_used": False,
            },
        }
    )
    assert payload.data.items[0].equipment_class.equipment_class_id == "centrifugal_chiller"
    assert payload.data.items[0].evidence[0].chunk_id == "chunk_001"
    assert payload.data.items[0].display_language == "en"


if __name__ == "__main__":
    test_fault_query_defaults()
    test_mcp_tool_names_present()
    test_semantic_envelope_shape()
    print("Semantic contract v2 checks passed")
