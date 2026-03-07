# KnowFabric Documentation

**Status:** Governance Documents - Binding Contracts
**Last Updated:** 2026-03-07

This directory contains the governance and standards documentation for KnowFabric. These are binding contracts, not aspirational guidelines.

---

## Reading Order for New Developers

**Start here (in order):**

1. **[00_repo-charter.md](00_repo-charter.md)** - Repository constitution
   - What KnowFabric is and is NOT
   - Hard constraints (non-negotiable)
   - Phase 1 success criteria

2. **[01_system-boundaries.md](01_system-boundaries.md)** - Module boundary contract
   - Module responsibilities
   - Dependency matrix
   - Forbidden behaviors

3. **[02_data-layer-contract.md](02_data-layer-contract.md)** - Data pipeline contract
   - Six-layer architecture
   - Forbidden shortcuts
   - Traceability requirements

4. **[07_phase1-implementation-contract.md](07_phase1-implementation-contract.md)** - Phase 1 delivery contract
   - What Phase 1 must deliver
   - What Phase 1 must NOT deliver
   - Definition of done

**Then read:**

5. **[05_phase-plan.md](05_phase-plan.md)** - Phase delivery contracts
6. **[06_quality-gates.md](06_quality-gates.md)** - Quality gate specifications
7. **[03_domain-package-spec.md](03_domain-package-spec.md)** - Domain package structure
8. **[04_engineering-standards.md](04_engineering-standards.md)** - Coding conventions

---

## Document Purpose and Authority

### Governance Documents (Binding)

These documents define hard boundaries and are enforced by CI:

- **00_repo-charter.md** - Defines what can and cannot be built
- **01_system-boundaries.md** - Enforced by `scripts/check-boundaries`
- **02_data-layer-contract.md** - Enforced by code review and architecture review
- **06_quality-gates.md** - Enforced by `scripts/check-all`
- **07_phase1-implementation-contract.md** - Enforced by acceptance testing

### Implementation Contracts

These documents define delivery expectations:

- **05_phase-plan.md** - Phase acceptance criteria
- **07_phase1-implementation-contract.md** - Phase 1 boundaries

### Standards Documents

These documents define conventions:

- **03_domain-package-spec.md** - Domain package structure
- **04_engineering-standards.md** - Coding style and naming

---

## How These Documents Are Used

### During Planning
- Read charter to understand scope boundaries
- Read system boundaries to understand module constraints
- Read data contract to understand pipeline requirements

### During Implementation
- Reference boundaries to avoid forbidden dependencies
- Reference data contract to avoid shortcuts
- Run quality gates before committing

### During Code Review
- Verify compliance with boundaries
- Verify compliance with data contract
- Verify traceability requirements met

### During Phase Acceptance
- Verify all acceptance criteria met
- Verify quality gates passing
- Verify no boundary violations

---

## Architecture Decision Records

- **[adr/](adr/)** - Architectural decisions and rationale

---

## For AI Assistants

When working on KnowFabric:

1. These documents are BINDING CONTRACTS, not suggestions
2. Prioritize governance over feature velocity
3. Never skip data layers (Document → Page → Chunk)
4. Always include traceability fields
5. Run `scripts/check-all` before claiming work is complete
