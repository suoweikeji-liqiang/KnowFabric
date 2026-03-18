"""Draft semantic API and MCP contracts for the ontology-first rebuild track."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


TrustLevel = Literal["L1", "L2", "L3", "L4"]
QueryStrategy = Literal["greedy", "diverse", "deep"]
KnowledgeObjectType = Literal[
    "fault_code",
    "parameter_spec",
    "commissioning_step",
    "wiring_guidance",
    "maintenance_procedure",
    "application_guidance",
    "performance_spec",
    "symptom",
    "diagnostic_step",
]


class SemanticBaseModel(BaseModel):
    """Base model for rebuild-track semantic contracts."""

    model_config = ConfigDict(protected_namespaces=())


class EquipmentClassRef(SemanticBaseModel):
    """Canonical equipment class reference returned by semantic endpoints."""

    equipment_class_id: str = Field(..., description="Canonical ontology class id")
    label: str = Field(..., description="Primary display label for the equipment class")
    domain_id: str = Field(..., description="Owning domain package identifier")


class EvidenceCitation(SemanticBaseModel):
    """Traceability citation for a semantic knowledge response."""

    doc_id: str
    doc_name: str | None = None
    page_no: int
    chunk_id: str
    evidence_text: str
    evidence_role: Literal["primary", "supporting"] = "supporting"


class SemanticKnowledgeObject(SemanticBaseModel):
    """Structured semantic knowledge object attached to an ontology anchor."""

    knowledge_object_id: str
    knowledge_object_type: KnowledgeObjectType
    canonical_key: str
    equipment_class: EquipmentClassRef
    title: str | None = None
    summary: str | None = None
    structured_payload: dict[str, Any]
    applicability: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    trust_level: TrustLevel
    review_status: str
    evidence: list[EvidenceCitation] = Field(min_length=1)


class SemanticQueryMetadata(SemanticBaseModel):
    """Metadata returned with semantic API or MCP responses."""

    contract_version: str = "2026-03-17"
    query_type: str
    filters_applied: dict[str, Any]
    total: int
    limit: int
    compatibility_surfaces: list[str] = Field(
        default_factory=lambda: ["/api/v1/chunks/search", "trace_evidence", "search_knowledge"]
    )


class SemanticKnowledgeResponse(SemanticBaseModel):
    """Envelope body for semantic collection responses."""

    equipment_class: EquipmentClassRef
    items: list[SemanticKnowledgeObject]


class ExternalMappingRef(SemanticBaseModel):
    """External interoperability mapping for an ontology class."""

    mapping_system: str
    external_id: str
    is_primary: bool = False
    mapping_metadata: dict[str, Any] = Field(default_factory=dict)


class EquipmentClassExplanationData(SemanticBaseModel):
    """Expanded ontology metadata for a canonical equipment class."""

    equipment_class: EquipmentClassRef
    class_kind: str
    parent_class_id: str | None = None
    labels: dict[str, str]
    aliases: dict[str, list[str]] = Field(default_factory=dict)
    external_mappings: list[ExternalMappingRef] = Field(default_factory=list)
    supported_knowledge_anchors: list[str] = Field(default_factory=list)


class SemanticApiEnvelope(SemanticBaseModel):
    """Standard API success envelope for semantic read endpoints."""

    success: bool = True
    data: SemanticKnowledgeResponse
    metadata: SemanticQueryMetadata


class EquipmentClassExplainEnvelope(SemanticBaseModel):
    """Standard API success envelope for class explanation responses."""

    success: bool = True
    data: EquipmentClassExplanationData
    metadata: SemanticQueryMetadata


class FaultKnowledgeQuery(SemanticBaseModel):
    """Request contract for fault knowledge retrieval."""

    domain_id: str
    equipment_class_id: str
    fault_code: str | None = None
    brand: str | None = None
    model_family: str | None = None
    include_related_symptoms: bool = True
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    min_trust_level: TrustLevel = "L4"
    limit: int = Field(default=20, ge=1, le=100)


class ParameterProfileQuery(SemanticBaseModel):
    """Request contract for parameter profile retrieval."""

    domain_id: str
    equipment_class_id: str
    parameter_category: str | None = None
    parameter_name: str | None = None
    brand: str | None = None
    model_family: str | None = None
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    min_trust_level: TrustLevel = "L4"
    limit: int = Field(default=20, ge=1, le=100)


class MaintenanceGuidanceQuery(SemanticBaseModel):
    """Request contract for maintenance guidance retrieval."""

    domain_id: str
    equipment_class_id: str
    task_type: str | None = None
    brand: str | None = None
    model_family: str | None = None
    include_diagnostic_steps: bool = True
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    min_trust_level: TrustLevel = "L4"
    limit: int = Field(default=20, ge=1, le=100)


class ExplainEquipmentClassQuery(SemanticBaseModel):
    """Request contract for ontology class explanation."""

    domain_id: str
    equipment_class_id: str
    language: str = "en"


MCP_TOOL_GET_FAULT_KNOWLEDGE: dict[str, Any] = {
    "name": "get_fault_knowledge",
    "description": (
        "Retrieve evidence-grounded fault knowledge objects by canonical "
        "equipment class id and optional fault filters."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "equipment_class_id": {
                "type": "string",
                "description": "Canonical ontology class id such as 'centrifugal_chiller'.",
            },
            "domain_id": {
                "type": "string",
                "description": "Domain package scope such as 'hvac' or 'drive'.",
            },
            "fault_code": {
                "type": "string",
                "description": "Optional vendor or canonical fault code filter.",
            },
            "brand": {
                "type": "string",
                "description": "Optional brand filter for applicability.",
            },
            "model_family": {
                "type": "string",
                "description": "Optional model family filter for applicability.",
            },
            "include_related_symptoms": {
                "type": "boolean",
                "default": True,
            },
            "min_confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "min_trust_level": {
                "type": "string",
                "enum": ["L1", "L2", "L3", "L4"],
                "default": "L4",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
            },
        },
        "required": ["domain_id", "equipment_class_id"],
    },
}


MCP_TOOL_GET_PARAMETER_PROFILE: dict[str, Any] = {
    "name": "get_parameter_profile",
    "description": (
        "Retrieve parameter specification knowledge objects by canonical "
        "equipment class id and optional category filters."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "equipment_class_id": {
                "type": "string",
                "description": "Canonical ontology class id such as 'chilled_water_pump'.",
            },
            "domain_id": {
                "type": "string",
                "description": "Domain package scope such as 'hvac' or 'drive'.",
            },
            "parameter_category": {
                "type": "string",
                "description": "Optional parameter category filter.",
            },
            "parameter_name": {
                "type": "string",
                "description": "Optional normalized parameter name filter.",
            },
            "brand": {
                "type": "string",
                "description": "Optional brand filter for applicability.",
            },
            "model_family": {
                "type": "string",
                "description": "Optional model family filter for applicability.",
            },
            "min_confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "min_trust_level": {
                "type": "string",
                "enum": ["L1", "L2", "L3", "L4"],
                "default": "L4",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
            },
        },
        "required": ["domain_id", "equipment_class_id"],
    },
}


MCP_TOOL_GET_MAINTENANCE_GUIDANCE: dict[str, Any] = {
    "name": "get_maintenance_guidance",
    "description": (
        "Retrieve maintenance guidance knowledge objects by canonical "
        "equipment class id and optional task filters."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "equipment_class_id": {
                "type": "string",
                "description": "Canonical ontology class id such as 'cooling_tower'.",
            },
            "domain_id": {
                "type": "string",
                "description": "Domain package scope such as 'hvac' or 'drive'.",
            },
            "task_type": {
                "type": "string",
                "description": "Optional maintenance task filter.",
            },
            "brand": {
                "type": "string",
                "description": "Optional brand filter for applicability.",
            },
            "model_family": {
                "type": "string",
                "description": "Optional model family filter for applicability.",
            },
            "include_diagnostic_steps": {
                "type": "boolean",
                "default": True,
            },
            "min_confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "min_trust_level": {
                "type": "string",
                "enum": ["L1", "L2", "L3", "L4"],
                "default": "L4",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
            },
        },
        "required": ["domain_id", "equipment_class_id"],
    },
}


MCP_TOOL_EXPLAIN_EQUIPMENT_CLASS: dict[str, Any] = {
    "name": "explain_equipment_class",
    "description": "Explain a canonical equipment class, its aliases, mappings, and supported knowledge anchors.",
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "equipment_class_id": {
                "type": "string",
                "description": "Canonical ontology class id to explain.",
            },
            "domain_id": {
                "type": "string",
                "description": "Domain package scope such as 'hvac' or 'drive'.",
            },
            "language": {
                "type": "string",
                "default": "en",
                "description": "Preferred response language for labels.",
            },
        },
        "required": ["domain_id", "equipment_class_id"],
    },
}


SEMANTIC_MCP_TOOLS_V2: list[dict[str, Any]] = [
    MCP_TOOL_GET_FAULT_KNOWLEDGE,
    MCP_TOOL_GET_PARAMETER_PROFILE,
    MCP_TOOL_GET_MAINTENANCE_GUIDANCE,
    MCP_TOOL_EXPLAIN_EQUIPMENT_CLASS,
]
