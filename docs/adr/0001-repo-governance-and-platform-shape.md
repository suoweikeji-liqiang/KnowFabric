# ADR-0001: Repository Governance and Platform Shape

**Status:** Accepted

**Date:** 2026-03-07

## Context

KnowFabric is being built as an industrial and energy domain knowledge injection platform. We need to establish foundational architectural decisions that will guide all subsequent development.

Key challenges:
1. Risk of building a generic chatbot shell instead of a knowledge engineering platform
2. Risk of hardcoding domain-specific logic into core foundation
3. Risk of skipping intermediate data layers for quick results
4. Risk of losing traceability from results to original evidence
5. Risk of building features without clear boundaries and contracts

## Decision

We adopt a **standards-first, boundaries-first, data-chain-first** approach:

### 1. Platform Shape

**Decision:** Build domain-agnostic foundation + pluggable domain packages

**Rationale:**
- Enables expansion from HVAC/drives to energy storage/PV without rewriting core
- Keeps domain logic isolated and maintainable
- Prevents domain-specific assumptions from polluting foundation

**Consequences:**
- More upfront design work
- Clearer separation of concerns
- Easier to add new domains later

### 2. Data Architecture

**Decision:** Enforce six-layer data model with mandatory intermediate layers

**Layers:**
1. Raw Document (truth source)
2. Page (traceability anchor)
3. Chunk (retrieval unit)
4. Fact (structured knowledge)
5. Index (query acceleration)
6. Derived Assets (exports)

**Rationale:**
- Ensures full traceability from any result back to original evidence
- Prevents shortcuts that sacrifice evidence quality
- Enables rebuilding derived data from source layers

**Consequences:**
- More storage required
- More processing stages
- Better traceability and evidence quality
- Ability to rebuild indexes and exports

### 3. First Phase Scope

**Decision:** Focus on HVAC and drive domains only in Phase 1

**Rationale:**
- HVAC and drives are well-understood domains with existing documentation
- Drives (frequency converters) are used in HVAC systems, providing natural integration test
- Limiting scope allows focus on platform quality over feature breadth
- Two domains sufficient to validate domain package mechanism

**Consequences:**
- Energy storage and PV deferred to later phases
- Can establish patterns with manageable scope
- Risk of over-fitting to HVAC/drive needs (mitigated by domain package abstraction)

### 4. Development Approach

**Decision:** Standards and boundaries before implementation

**Rationale:**
- Prevents architectural drift and technical debt
- Makes code reviews objective (does it follow standards?)
- Enables parallel development with clear contracts
- Reduces rework from boundary violations

**Consequences:**
- Slower initial progress
- More documentation upfront
- Clearer expectations for all developers
- Less rework and refactoring later

### 5. Truth Source Hierarchy

**Decision:** Original documents and intermediate layers are truth sources; indexes and exports are not

**Rationale:**
- Indexes can be corrupted, out of sync, or lost
- Original evidence must always be accessible
- Derived data must be regenerable

**Consequences:**
- Cannot delete original documents casually
- Must maintain page and chunk layers even if not directly queried
- Indexes must be rebuildable from chunks

### 6. Traceability Requirements

**Decision:** All outputs must include traceability to source document, page, and evidence text

**Rationale:**
- Users must be able to verify knowledge sources
- Enables debugging and quality improvement
- Builds trust in system outputs
- Required for regulatory compliance in industrial domains

**Consequences:**
- Larger response payloads
- More complex data models
- Higher quality and verifiability

### 7. Domain Package Mechanism

**Decision:** Domain logic expressed through configuration (YAML/JSON), not code

**Rationale:**
- Non-developers can maintain domain packages
- Domain changes don't require code deployment
- Clear separation between platform and domain logic
- Easier to version and audit domain changes

**Consequences:**
- Need robust configuration validation
- Limited expressiveness compared to code
- Clearer domain boundaries

## Alternatives Considered

### Alternative 1: Build HVAC-specific system first, generalize later

**Rejected because:**
- Generalizing after the fact is much harder
- Would likely result in HVAC assumptions baked into core
- Rework cost would be high

### Alternative 2: Skip page layer, go directly from document to chunks

**Rejected because:**
- Loses page-level traceability
- Makes visual evidence (page images) harder to link
- Complicates multimodal processing

### Alternative 3: Use vector index as primary truth source

**Rejected because:**
- Vectors are lossy representations
- Cannot regenerate original text from vectors
- Index corruption would lose knowledge
- No evidence text for verification

### Alternative 4: Build all domains simultaneously

**Rejected because:**
- Too much scope for Phase 1
- Would delay validation of core platform
- Higher risk of over-engineering

## Consequences

### Positive

- Clear architectural boundaries from day one
- Traceability built in, not bolted on
- Domain expansion path is clear
- Quality gates can be automated
- Code reviews have objective standards

### Negative

- More upfront design and documentation work
- Slower initial feature delivery
- More storage required for intermediate layers
- More complex data models

### Neutral

- Need to maintain documentation discipline
- Need to enforce boundaries through tooling
- Need to validate domain packages

## Compliance

All development must comply with:
- [Repository Charter](../00_repo-charter.md)
- [System Boundaries](../01_system-boundaries.md)
- [Data Layer Contract](../02_data-layer-contract.md)
- [Domain Package Spec](../03_domain-package-spec.md)
- [Engineering Standards](../04_engineering-standards.md)
- [Quality Gates](../06_quality-gates.md)

## Review

This ADR should be reviewed after Phase 1 completion to validate assumptions and adjust if needed.
