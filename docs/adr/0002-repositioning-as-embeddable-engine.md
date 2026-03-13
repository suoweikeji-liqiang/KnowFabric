# ADR-0002: Repositioning as Embeddable Knowledge Engineering Engine

**Status:** Accepted
**Date:** 2026-03-13
**Deciders:** Project leadership

## Context

KnowFabric was originally positioned as an "industrial knowledge injection platform" — a service-oriented system focused on internal data processing. This positioning had several problems:

1. **External APIs deferred to Phase 3**: Integration capabilities were scheduled late, preventing early validation by real consumers.
2. **No AI Agent support**: AI agents (the fastest-growing consumer class) had no way to access KnowFabric knowledge. No MCP tools, no structured context delivery.
3. **Weak differentiation**: The "platform" positioning was indistinguishable from generic RAG solutions. The unique value (industrial domain depth, traceability, structured knowledge) was not surfaced in the architecture.
4. **Unclear consumption model**: It was unclear who would use KnowFabric and how. The system was built inward (data processing) without outward interfaces (APIs, tools, SDK).

## Decision

Reposition KnowFabric from "industrial knowledge injection platform" to **"embeddable knowledge engineering engine for industrial domains"** with three changes:

### 1. Identity Shift: Platform → Engine

An "engine" is embedded into other systems; a "platform" stands alone. KnowFabric is not an end-user application — it powers applications. This shift clarifies the integration-first nature of the product.

### 2. AI Agents as First-Class Consumer

Define three consumer classes (AI Agents, Developers, Upstream Applications) with AI agents as the primary target. This means:
- MCP Server baseline in Phase 1 (not Phase 3)
- Context block format designed for LLM context windows
- Token budget control protocol (Phase 2)
- AI prompt templates per domain (Phase 3)

### 3. Integration APIs in Phase 1

Move external APIs and MCP Server from Phase 3 to Phase 1. The rationale:
- An engine without integration points cannot be validated
- Early API exposure forces good interface design
- MCP tools enable immediate AI agent testing
- Docker deployment enables quick evaluation by partners

## Phase Plan Changes

| Capability | Before (Phase) | After (Phase) |
|-----------|----------------|---------------|
| Integration REST API | Phase 3 | **Phase 1** |
| MCP Server | Not planned | **Phase 1** |
| Docker deployment | Not planned | **Phase 1** |
| Context assembly (token budget) | Not planned | **Phase 2** |
| Python SDK | Not planned | **Phase 3** |
| AI prompt templates | Not planned | **Phase 3** |
| Terminology mapping | Not planned | **Phase 3** |
| Domain package distribution | Not planned | **Phase 3** |
| Cross-domain knowledge linking | Not planned | **Phase 4** |

## Consequences

### Positive

- **Early validation**: External consumers can test KnowFabric from Phase 1, providing feedback before deep investment
- **Clear differentiation**: "Embeddable engine with industrial traceability" is distinct from "another RAG solution"
- **AI-ready**: MCP support positions KnowFabric for the AI agent ecosystem immediately
- **Faster integration**: Partners and developers can evaluate and integrate without waiting for Phase 3

### Negative

- **Phase 1 scope increase**: Adding API, MCP, and Docker increases Phase 1 work
- **Documentation effort**: New governance document (08_ai-consumer-contract.md) and updates to 6 existing documents
- **API stability pressure**: Exposing APIs early means committing to interface stability sooner

### Mitigations

- Phase 1 API is minimal (4 endpoints, 3 MCP tools) — not a full API surface
- MCP tools reuse existing retrieval/db packages — no new data path
- Docker deployment uses standard compose — minimal new infrastructure
- API version stability promise (v1 no breaking changes) is standard practice

## Documents Modified

1. `docs/00_repo-charter.md` — Identity, Phase 1 scope, evolution principles
2. `docs/05_phase-plan.md` — All four phases restructured
3. `docs/07_phase1-implementation-contract.md` — New deliverables and DoD criteria
4. `docs/08_ai-consumer-contract.md` — New document
5. `docs/04_engineering-standards.md` — Async API, AI consumer standards, version stability
6. `docs/03_domain-package-spec.md` — AI prompt templates, terminology, distribution
7. `README.md` — Public-facing identity and integration examples
8. `CLAUDE.md` — Synchronized positioning and commands
9. `docs/README.md` — Reading order updated

## Documents NOT Modified

- `docs/01_system-boundaries.md` — Module boundaries unchanged (API/MCP layers sit on top)
- `docs/02_data-layer-contract.md` — Six-layer data architecture unchanged
- `docs/06_quality-gates.md` — Quality gate mechanisms unchanged
