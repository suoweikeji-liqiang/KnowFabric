# AI Consumer Contract

**Status:** Governance Document - Binding Contract
**Last Updated:** 2026-03-13

This document defines the contract for AI agents and AI-powered applications consuming KnowFabric knowledge. It specifies data formats, interaction protocols, and quality guarantees.

---

## Consumer Classes

KnowFabric serves three classes of consumers with different access patterns:

### 1. AI Agents (First-Class Consumer)

**Access Pattern:** MCP tools and structured API endpoints
**Use Cases:** Autonomous knowledge retrieval, evidence-grounded reasoning, fact verification
**Key Requirement:** Structured responses with confidence scores and token counts for context window management

### 2. Developers

**Access Pattern:** REST API and Python SDK
**Use Cases:** Building applications that embed industrial knowledge (chatbots, dashboards, copilots)
**Key Requirement:** Well-documented API with stable contracts, OpenAPI spec, SDK with type hints

### 3. Upstream Applications

**Access Pattern:** REST API (typically server-to-server)
**Use Cases:** Knowledge backend for enterprise systems, ERP integration, maintenance platforms
**Key Requirement:** Reliable API with pagination, filtering, and standard response envelopes

---

## Context Block Standard Format

All knowledge delivery endpoints return **context blocks** — the standard unit of knowledge consumed by AI agents.

### Context Block Schema

```json
{
  "block_id": "ctx_abc123",
  "content": "The ACS880 drive fault code F0001 indicates...",
  "citation": {
    "doc_id": "doc_xyz789",
    "doc_name": "ABB ACS880 Technical Manual",
    "page_no": 42,
    "chunk_id": "chunk_def456",
    "evidence_text": "F0001: Overcurrent fault detected during acceleration"
  },
  "confidence": 0.92,
  "trust_level": "L2",
  "token_count": 87,
  "domain": "drive",
  "chunk_type": "fault_code_block"
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_id` | string | Yes | Unique context block identifier |
| `content` | string | Yes | Knowledge content text |
| `citation` | object | Yes | Full traceability citation |
| `citation.doc_id` | string | Yes | Source document ID |
| `citation.doc_name` | string | Yes | Source document name |
| `citation.page_no` | integer | Yes | Source page number |
| `citation.chunk_id` | string | Yes | Source chunk ID |
| `citation.evidence_text` | string | Yes | Original evidence text from source |
| `confidence` | float | Yes | Confidence score (0.0-1.0) |
| `trust_level` | string | Yes | Trust level (L1-L4) |
| `token_count` | integer | Yes | Token count of content field |
| `domain` | string | Yes | Source domain |
| `chunk_type` | string | No | Chunk type classification |

### Invariant

Every context block MUST include a citation that traces back to the original document. Context blocks without citations are forbidden.

---

## Token Budget Control Protocol

When AI agents request knowledge, they can specify a token budget to control context window usage.

### Request Parameters

```json
{
  "query": "ACS880 fault codes",
  "domain": "drive",
  "max_tokens": 2000,
  "strategy": "greedy"
}
```

### Assembly Strategies

| Strategy | Behavior | Best For |
|----------|----------|----------|
| `greedy` | Fill budget with highest-relevance blocks first | Single focused question |
| `diverse` | Spread budget across different topics/sources | Broad exploration |
| `deep` | Fill budget with blocks from single most relevant topic | Deep-dive on one subject |

### Budget Enforcement

- Response MUST NOT exceed `max_tokens` (5% margin allowed for metadata overhead)
- If no blocks fit within budget, return empty result with explanation
- Token counts are computed server-side using a consistent tokenizer
- Response metadata includes: `total_tokens_used`, `total_blocks`, `budget_remaining`

### Response Envelope

```json
{
  "success": true,
  "data": {
    "blocks": [ ... ],
    "query_metadata": {
      "strategy": "greedy",
      "total_tokens_used": 1847,
      "total_blocks": 4,
      "budget_remaining": 153,
      "max_tokens": 2000
    }
  }
}
```

**Phase:** Token budget control is a Phase 2 deliverable. Phase 1 returns blocks without budget enforcement.

---

## Trust Level Semantics

Trust levels indicate the reliability of knowledge and influence how AI agents should use it.

### Level Definitions

| Level | Name | Meaning | AI Decision Guidance |
|-------|------|---------|---------------------|
| L1 | Verified | Human-reviewed and approved fact | Safe to state as fact. Cite source. |
| L2 | Extracted | Machine-extracted with high confidence (≥0.85) | Safe to use with "according to [source]" framing. |
| L3 | Inferred | Machine-extracted with moderate confidence (0.5-0.85) | Use with hedging language ("may", "possibly"). Flag uncertainty. |
| L4 | Raw | Unprocessed chunk content, no extraction | Treat as reference material. Do not present as structured fact. |

### Trust Level Rules

1. AI agents SHOULD prefer higher trust levels when multiple sources answer the same question
2. AI agents MUST NOT present L3/L4 content as verified facts
3. Trust level MUST be included in every context block — no knowledge without trust annotation
4. Trust levels are assigned by the extraction and review pipelines, not by the consumer

**Phase:** Trust levels L1-L2 require fact extraction and review (Phase 2). Phase 1 returns all content as L4 (raw chunk content).

---

## MCP Tool Definitions

### Phase 1 Tools

#### `search_knowledge`

Search the knowledge base and return structured results.

```json
{
  "name": "search_knowledge",
  "description": "Search industrial knowledge base for relevant information. Returns structured results with full source traceability.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language search query"
      },
      "domain": {
        "type": "string",
        "description": "Domain filter (e.g., 'hvac', 'drive')",
        "enum": ["hvac", "drive"]
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of results (default: 10)",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

#### `trace_evidence`

Retrieve the full evidence chain for a specific chunk.

```json
{
  "name": "trace_evidence",
  "description": "Retrieve full evidence chain for a knowledge chunk: chunk → page → document. Use this to verify sources.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "chunk_id": {
        "type": "string",
        "description": "The chunk ID to trace"
      }
    },
    "required": ["chunk_id"]
  }
}
```

#### `list_domains`

List available knowledge domains.

```json
{
  "name": "list_domains",
  "description": "List available knowledge domains and their coverage (equipment types, document counts).",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

### Phase 2 Tools

#### `query_knowledge`

Token-budget-aware knowledge query (extends search_knowledge).

```json
{
  "name": "query_knowledge",
  "description": "Query knowledge with token budget control. Returns context blocks optimized for AI consumption.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "domain": { "type": "string" },
      "max_tokens": { "type": "integer", "default": 2000 },
      "strategy": { "type": "string", "enum": ["greedy", "diverse", "deep"], "default": "greedy" },
      "min_confidence": { "type": "number", "default": 0.3 },
      "min_trust_level": { "type": "string", "enum": ["L1", "L2", "L3", "L4"], "default": "L4" }
    },
    "required": ["query"]
  }
}
```

#### `get_facts`

Query structured facts with evidence.

```json
{
  "name": "get_facts",
  "description": "Query structured facts (subject-relation-object) with full evidence traceability.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "entity": { "type": "string", "description": "Entity to query facts about" },
      "relation": { "type": "string", "description": "Relation type filter" },
      "domain": { "type": "string" },
      "min_trust_level": { "type": "string", "enum": ["L1", "L2", "L3", "L4"] },
      "limit": { "type": "integer", "default": 20 }
    },
    "required": ["entity"]
  }
}
```

---

## Domain Knowledge Delivery (Phase 3)

### AI Prompt Templates

Domain packages will include prompt templates that help AI agents formulate domain-appropriate queries and responses.

**File:** `domain_packages/{domain}/ai_prompt_templates.yaml`

```yaml
templates:
  fault_diagnosis:
    description: Guide AI to diagnose equipment faults
    system_context: |
      You are an industrial HVAC expert. Use the provided knowledge
      to diagnose equipment faults. Always cite your sources.
    query_template: |
      Equipment: {equipment_type}
      Symptom: {symptom}
      Find relevant fault codes and recommended actions.
    response_guidance: |
      Structure your response as:
      1. Most likely fault code and cause
      2. Recommended diagnostic steps
      3. Repair actions
      Always include source citations.
```

### Terminology Mapping

Domain packages will include terminology mappings for consistent AI interpretation.

**File:** `domain_packages/{domain}/terminology.yaml`

```yaml
terms:
  - canonical: "variable_frequency_drive"
    aliases: ["VFD", "frequency converter", "inverter", "变频器"]
    domain: drive
    description: "Device that controls motor speed by varying frequency"

  - canonical: "chilled_water_supply_temperature"
    aliases: ["CHWST", "supply temp", "冷冻水供水温度"]
    domain: hvac
    description: "Temperature of water leaving the chiller"
```

---

## Constraints

### Traceability Rules (Unchanged)

The core traceability contract is NOT modified by this document:
- Every knowledge output MUST trace through: Document → Page → Chunk → (Fact) → Output
- Every context block MUST include citation with doc_id, page_no, chunk_id, evidence_text
- No knowledge may be delivered without a traceable source

### Read-Only Interface

AI consumers access knowledge through read-only interfaces:
- MCP tools are read-only (except review_fact in Phase 2, which is a controlled write)
- API endpoints for AI consumption are read-only
- Document ingestion and processing are separate from consumption

### MCP Implementation Constraint

MCP tools MUST reuse existing packages (retrieval, db, etc.):
- `search_knowledge` calls the existing retrieval package
- `trace_evidence` calls existing db queries
- `list_domains` reads existing domain package manifests
- No separate data path or duplicate logic for MCP

### No Knowledge Without Confidence

Starting from Phase 2, all knowledge delivered to AI consumers MUST include confidence scores. Phase 1 may omit confidence (content is L4/raw), but the field must be present in the response schema with a null or default value.

---

## Phase Alignment Summary

| Capability | Phase |
|-----------|-------|
| MCP Server (3 tools: search, trace, list_domains) | Phase 1 |
| Integration API (upload, status, trace, search) | Phase 1 |
| Context block format in API responses | Phase 1 (without confidence) |
| Token budget control | Phase 2 |
| Confidence/trust level semantics | Phase 2 |
| Enhanced MCP tools (query_knowledge, get_facts) | Phase 2 |
| AI prompt templates | Phase 3 |
| Terminology mappings | Phase 3 |
| Python SDK | Phase 3 |
| Domain package distribution | Phase 3 |
