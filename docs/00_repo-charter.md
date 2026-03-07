# Repository Charter

## Project Positioning

**KnowFabric** is an industrial and energy domain knowledge injection platform that transforms scattered industry documentation into structured, traceable, and serviceable knowledge assets.

### What It Is

- A **knowledge engineering platform** for industrial and energy domains
- A **domain-agnostic foundation** with pluggable domain packages
- A **multi-layer data architecture** ensuring full traceability
- A **service-oriented platform** providing retrieval, query, and export APIs

### What It Is NOT

- ❌ A general-purpose chatbot or conversational AI shell
- ❌ A simple document management or file storage system
- ❌ An automatic knowledge graph inference engine (not in Phase 1)
- ❌ A direct device control or real-time automation system
- ❌ A multi-tenant commercial SaaS platform (not in Phase 1)
- ❌ A one-size-fits-all solution covering all domains simultaneously

## Target Users and Scenarios

### Primary Users

1. **Knowledge Engineers**
   - Ingest raw industry documents
   - Configure domain packages and extraction rules
   - Maintain indexes and knowledge assets

2. **Domain Experts**
   - Review extracted facts and relationships
   - Validate fault codes, parameters, and control strategies
   - Approve high-value knowledge for export

3. **Algorithm/Platform Engineers**
   - Maintain domain package configurations
   - Optimize extraction strategies
   - Export fine-tuning samples and knowledge packages

4. **External Business Systems**
   - Query knowledge via retrieval APIs
   - Access structured facts via query APIs
   - Import domain-specific knowledge packages

### Key Scenarios (Phase 1)

1. Import HVAC and ABB drive documentation into unified knowledge base
2. Query fault codes with evidence traceability to original manuals
3. Retrieve control strategies and parameter settings with source citations
4. Extract structured knowledge entries from technical documents
5. Export knowledge samples for model fine-tuning or downstream systems
6. Provide retrieval and structured query APIs to external systems

## First Phase Scope

### Included Domains

**Phase 1 focuses on TWO domain packages:**

1. **hvac** - HVAC Domain Package
   - Chillers, pumps, cooling towers
   - AHU, VRF systems, valves, sensors
   - HVAC fault diagnosis and control optimization

2. **drive** - Drive/Converter Domain Package
   - ABB frequency converters (primary focus)
   - Parameter settings and fault codes
   - Commissioning, wiring, and control interfaces
   - HVAC-specific applications (fan/pump control)

### Included Capabilities

Phase 1 delivers:

- ✅ Raw document ingestion and archival
- ✅ Page-level parsing and asset generation
- ✅ Chunk-level knowledge unit creation
- ✅ Retrieval knowledge base construction
- ✅ Structured fact extraction
- ✅ Document/page/chunk/fact traceability chain
- ✅ Basic human review workflow
- ✅ Basic external query interfaces
- ✅ Domain package mechanism foundation

### Explicitly Excluded (Phase 1)

Phase 1 does NOT include:

- ❌ Automatic high-precision knowledge graph reasoning
- ❌ Automatic fine-tuning training platform
- ❌ Direct control of field devices with closed-loop execution
- ❌ Commercial multi-tenant SaaS features
- ❌ One-time coverage of all domains (HVAC, storage, PV, etc.)
- ❌ Full-scale deep multimodal reprocessing of all documents

### Reserved for Future Phases

- Energy storage domain package
- Photovoltaics domain package
- Integrated energy domain package
- Advanced graph reasoning and rule capabilities
- Higher-level diagnostic and control advisory services
- Fine-tuning sample factory with evaluation capabilities

## Success Criteria (Phase 1)

Phase 1 is considered successful when:

1. ✅ Can import a batch of raw documents successfully
2. ✅ Can stably generate document/page/chunk/fact data chain
3. ✅ Chunks are retrievable and traceable back to original pages
4. ✅ Facts are generated with evidence text
5. ✅ Supports hvac and drive domain packages
6. ✅ Supports incremental import and partial re-processing
7. ✅ Supports basic review and revision workflow
8. ✅ External API responses include traceability fields
9. ✅ Can export at least one type of knowledge asset package

## Evolution Principles

### 1. Standards Before Scale

Establish boundaries, contracts, and quality gates before pursuing feature volume.

### 2. Assets Before Intelligence

Transform raw documents into stable knowledge assets before adding advanced reasoning capabilities.

### 3. Traceability Before Optimization

Ensure every result can trace back to original evidence before optimizing for speed or accuracy.

### 4. Foundation Before Domain

Build domain-agnostic foundation capabilities before embedding domain-specific logic.

### 5. Incremental Before Complete

Support incremental processing and partial re-runs before attempting full-scale batch processing.

### 6. Evidence Before Answers

Prioritize original evidence over answer quality - users must be able to verify sources.

### 7. Contracts Before Implementation

Define module boundaries and data contracts before writing implementation code.

## Non-Goals

To maintain focus, the following are explicitly NOT goals for this platform:

1. **Not a general AI platform** - Focus on industrial/energy knowledge, not general Q&A
2. **Not a training platform** - Export samples for training, but don't manage training itself
3. **Not a device controller** - Provide knowledge for control decisions, not direct control
4. **Not a data lake** - Structured knowledge assets, not raw data storage
5. **Not a BI platform** - Knowledge retrieval and query, not analytics dashboards
6. **Not a CMS** - Document processing for knowledge extraction, not content management

## Governance Principles

### Migration-First

All data schema changes must go through migration scripts. No ad-hoc schema modifications.

### Boundaries Before Implementation

Define module responsibilities and forbidden dependencies before writing code.

### Quality Gates Before Merge

All code must pass documentation, boundary, dependency, lint, type, and test checks.

### Monorepo Layout Clear and Intentional

Directory structure reflects architectural boundaries. No "utils" or "common" dumping grounds.
