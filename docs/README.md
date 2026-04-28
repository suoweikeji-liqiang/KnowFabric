# KnowFabric Documentation

**Status:** Governance Documents - Binding Contracts
**Last Updated:** 2026-04-10

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

**If you are working on the rebuild track, read next:**

5. **[adr/0003-promote-knowfabric-to-domain-knowledge-authority.md](adr/0003-promote-knowfabric-to-domain-knowledge-authority.md)** - Why KnowFabric is being rebuilt as an ontology-first product
6. **[09_ontology-authority-architecture.md](09_ontology-authority-architecture.md)** - Target architecture and ownership boundaries
7. **[10_rebuild-plan.md](10_rebuild-plan.md)** - Execution plan and workstream sequencing

**Then read:**

8. **[05_phase-plan.md](05_phase-plan.md)** - Legacy phase delivery contracts
9. **[06_quality-gates.md](06_quality-gates.md)** - Quality gate specifications
10. **[03_domain-package-spec.md](03_domain-package-spec.md)** - Legacy domain package structure
11. **[04_engineering-standards.md](04_engineering-standards.md)** - Coding conventions
12. **[08_ai-consumer-contract.md](08_ai-consumer-contract.md)** - AI consumer interface contract
13. **[11_rebuild-session-kickoff.md](11_rebuild-session-kickoff.md)** - Recommended prompt and startup checklist for new rebuild sessions
14. **[12_domain-package-v2-migration-checklist.md](12_domain-package-v2-migration-checklist.md)** - Legacy-to-v2 package migration checklist
15. **[13_rebuild-storage-contract.md](13_rebuild-storage-contract.md)** - Draft storage contract for ontology anchors and knowledge objects
16. **[14_semantic-api-mcp-contract.md](14_semantic-api-mcp-contract.md)** - Draft semantic REST and MCP delivery contracts
17. **[15_manual-validation-round1.md](15_manual-validation-round1.md)** - First manual-driven validation note for module-unit HVAC manuals
18. **[16_manual-validation-drive-round1.md](16_manual-validation-drive-round1.md)** - First manual-driven validation note for VFD manuals
19. **[17_manual-validation-round2.md](17_manual-validation-round2.md)** - Second manual-driven validation note for parameter and maintenance material
20. **[18_authority-source-validation-round3.md](18_authority-source-validation-round3.md)** - Real-corpus validation note across chillers, VFDs, and authority reference material
21. **[19_authority-source-validation-round4.md](19_authority-source-validation-round4.md)** - Validation note for performance specs plus drive commissioning and wiring guidance
22. **[20_authority-source-validation-round5.md](20_authority-source-validation-round5.md)** - Validation note for drive-side application guidance and broader guide knowledge
23. **[21_authority-source-validation-round6.md](21_authority-source-validation-round6.md)** - Validation note for HVAC-side authority application guidance from ASHRAE guide material
24. **[22_external-evaluation-guide.md](22_external-evaluation-guide.md)** - Operator-facing quickstart for bootstrap, smoke, and handoff artifacts
25. **[23_vnext-compile-check-publish-direction.md](23_vnext-compile-check-publish-direction.md)** - Direction note proposing the next capability loop: compile -> check -> publish
26. **[24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md)** - **BINDING CONTRACT** with sw_base_model: ownership boundary, ID conventions, data flow, MCP registration, ontology_version sync, feedback channels. Mirrored verbatim in `sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`.
27. **[25_knowfabric-side-contract-implementation-plan.md](25_knowfabric-side-contract-implementation-plan.md)** - Codex-executable plan for KnowFabric side of the contract migration (8 tasks; OntologyClassV2 export, drop, feedback API, CI checks, charter rewrite).
28. **[26_ai-assisted-compilation-pilot-milestone.md](26_ai-assisted-compilation-pilot-milestone.md)** - AI-assisted compilation pilot milestone — defines the operationally-usable bar for Compile/Check/Review/Publish loop

---

## Document Purpose and Authority

### Governance Documents (Binding)

These documents define hard boundaries and are enforced by CI:

- **00_repo-charter.md** - Defines what can and cannot be built
- **01_system-boundaries.md** - Enforced by `scripts/check-boundaries`
- **02_data-layer-contract.md** - Enforced by code review and architecture review
- **06_quality-gates.md** - Enforced by `scripts/check-all`
- **07_phase1-implementation-contract.md** - Enforced by acceptance testing
- **08_ai-consumer-contract.md** - Defines AI consumer interface standards
- **24_knowfabric-sw-base-model-contract.md** - Cross-repo integration contract; enforced by `scripts/check-contract-mirror` (paired SHA with `sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`)

### Implementation Contracts

These documents define delivery expectations:

- **05_phase-plan.md** - Phase acceptance criteria
- **07_phase1-implementation-contract.md** - Phase 1 boundaries
- **10_rebuild-plan.md** - Rebuild-track execution plan

### Rebuild Architecture

These documents govern the ontology-first rebuild track:

- **adr/0003-promote-knowfabric-to-domain-knowledge-authority.md** - Rebuild decision and product boundary
- **09_ontology-authority-architecture.md** - Target architecture for ontology-first KnowFabric
- **10_rebuild-plan.md** - Workstream-based execution plan
- **11_rebuild-session-kickoff.md** - Session startup guide and reusable kickoff prompt
- **12_domain-package-v2-migration-checklist.md** - File-by-file migration checklist for legacy packages
- **13_rebuild-storage-contract.md** - Proposed additive storage model for ontology-first persistence
- **14_semantic-api-mcp-contract.md** - Proposed read-only semantic REST and MCP contract set
- **15_manual-validation-round1.md** - Findings from the first real-manual validation round
- **16_manual-validation-drive-round1.md** - Findings from the first real VFD manual validation round
- **17_manual-validation-round2.md** - Findings from the second manual-backed semantic validation round
- **18_authority-source-validation-round3.md** - Findings from source-level validation against local chiller, VFD, and authority-reference corpora
- **19_authority-source-validation-round4.md** - Findings from expanding the semi-automated flow to performance, commissioning, and wiring guidance
- **20_authority-source-validation-round5.md** - Findings from adding drive-side application guidance to the semi-automated flow
- **21_authority-source-validation-round6.md** - Findings from adding HVAC-side authority application guidance to the semi-automated flow
- **22_external-evaluation-guide.md** - Productization-facing operator flow for external evaluation and handoff
- **23_vnext-compile-check-publish-direction.md** - Direction note on elevating compilation and knowledge-health checks as first-class capabilities
- **24_knowfabric-sw-base-model-contract.md** - Binding sw_base_model integration contract and ownership boundary
- **25_knowfabric-side-contract-implementation-plan.md** - KnowFabric-side execution plan for the contract migration
- **26_ai-assisted-compilation-pilot-milestone.md** - AI-assisted compilation pilot milestone — defines the operationally-usable bar for Compile/Check/Review/Publish loop

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
