# KnowFabric Documentation

This directory contains the complete governance and standards documentation for KnowFabric.

## Documentation Structure

### Core Standards (Read in Order)

1. **[00_repo-charter.md](00_repo-charter.md)** - Project positioning, scope, and principles
2. **[01_system-boundaries.md](01_system-boundaries.md)** - Module boundaries and responsibilities
3. **[02_data-layer-contract.md](02_data-layer-contract.md)** - Six-layer data model specification
4. **[03_domain-package-spec.md](03_domain-package-spec.md)** - Domain package structure and rules
5. **[04_engineering-standards.md](04_engineering-standards.md)** - Coding, naming, and workflow standards
6. **[05_phase-plan.md](05_phase-plan.md)** - Delivery phases and acceptance criteria
7. **[06_quality-gates.md](06_quality-gates.md)** - Repository-level quality requirements

### Architecture Decision Records

- **[adr/](adr/)** - Architectural decisions and rationale

## Purpose

These documents serve as the **evaluation standard** for all development work. They define:

- What KnowFabric is and is not
- Module boundaries and forbidden dependencies
- Data layer contracts and truth sources
- Traceability requirements
- Domain package mechanisms
- Quality gates and acceptance criteria

## For Developers

Before implementing any feature:

1. Read the relevant standards documents
2. Verify your design complies with boundaries and contracts
3. Ensure traceability requirements are met
4. Run quality gates before committing

## For AI Assistants

When working on KnowFabric:

1. Read and strictly follow these standards
2. Prioritize establishing contracts over rapid feature delivery
3. Never skip intermediate data layers (page/chunk)
4. Always maintain traceability chains
5. Keep domain logic in domain packages, not in core foundation
