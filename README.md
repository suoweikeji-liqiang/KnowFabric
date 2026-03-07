# KnowFabric

## What KnowFabric Is

KnowFabric is an **industrial and energy domain knowledge injection platform** that transforms scattered industry documentation into structured, traceable, and serviceable knowledge assets.

It is NOT a general chatbot or document management tool. It is a knowledge engineering platform with:

- **Domain-agnostic foundation** + **domain package mechanism**
- **Multi-layer data architecture** (document → page → chunk → fact → index → derived assets)
- **Full traceability chain** from any result back to original evidence
- **Incremental processing** with stage-level recovery
- **Service-oriented output** (retrieval API, structured query, knowledge export)

## What KnowFabric Is NOT

- ❌ Not a general-purpose chatbot shell
- ❌ Not a one-time document converter
- ❌ Not an automatic knowledge graph inference engine (first phase)
- ❌ Not a direct device control system
- ❌ Not a multi-tenant commercial SaaS (first phase)

## First Phase Scope

**Target Domains (Phase 1):**
- `hvac` - HVAC equipment, faults, control strategies
- `drive` - Frequency converters (ABB focus), parameters, fault codes

**Reserved for Future:**
- `energy_storage` - Energy storage systems
- `photovoltaics` - Photovoltaic systems
- `integrated_energy` - Integrated energy solutions

**Core Capabilities (Phase 1):**
- Raw document ingestion and archival
- Page-level parsing and asset generation
- Chunk-level knowledge unit creation
- Structured fact extraction
- Retrieval knowledge base construction
- Document/page/chunk/fact traceability chain
- Basic human review workflow
- Basic external query interfaces
- Domain package mechanism foundation

## Core Data Chain

All processing follows this mandatory chain:

```
Raw Document → Page → Chunk → Fact → Index/Export
```

**Truth Source Hierarchy:**
1. **Raw Document Layer** - Ultimate truth source
2. **Page Layer** - Traceability and multimodal processing anchor
3. **Chunk Layer** - Retrieval and extraction primary unit
4. **Fact Layer** - Structured knowledge truth source
5. **Index Layer** - Query acceleration only (NOT truth source)
6. **Derived Assets Layer** - Exportable products (NOT truth source)

**Forbidden:**
- ❌ Skipping page/chunk layers to build direct Q&A
- ❌ Treating index as primary truth source
- ❌ Hardcoding domain-specific logic into global foundation

## Monorepo Structure

```
KnowFabric/
├── apps/                    # Application entry points
│   ├── api/                # REST API service
│   ├── worker/             # Background processing workers
│   └── admin-web/          # Admin dashboard
├── packages/               # Shared packages
│   ├── core/              # Core domain models
│   ├── db/                # Database layer
│   ├── storage/           # File/object storage
│   ├── domain-kit/        # Domain package toolkit
│   ├── ingest/            # Document ingestion
│   ├── parser/            # Document parsing
│   ├── chunking/          # Chunk generation
│   ├── extraction/        # Fact extraction
│   ├── retrieval/         # Search and retrieval
│   ├── review/            # Review workflow
│   └── exporter/          # Knowledge export
├── domain_packages/        # Domain-specific configurations
│   ├── hvac/              # HVAC domain package
│   └── drive/             # Drive/converter domain package
├── pipelines/             # Processing pipelines
├── scripts/               # Utility scripts and quality gates
├── tests/                 # Test suites
├── docs/                  # Documentation and standards
└── final_docs/            # Original requirement documents
```

## Local Commands

```bash
# Quality gates
npm run check:docs              # Verify documentation completeness
npm run check:boundaries        # Verify module boundaries
npm run check:forbidden-deps    # Check for forbidden dependencies
npm run check:all              # Run all quality checks

# Development
npm run dev                    # Start development environment
npm run build                  # Build all packages
npm run test                   # Run test suites

# Database
npm run db:migrate            # Run database migrations
npm run db:seed               # Seed initial data
```

## Standards Entry

All development must follow the standards defined in `docs/`:

- **[Repo Charter](docs/00_repo-charter.md)** - Project positioning and principles
- **[System Boundaries](docs/01_system-boundaries.md)** - Module responsibilities and constraints
- **[Data Layer Contract](docs/02_data-layer-contract.md)** - Six-layer data model specification
- **[Domain Package Spec](docs/03_domain-package-spec.md)** - Domain package structure and rules
- **[Engineering Standards](docs/04_engineering-standards.md)** - Coding and naming conventions
- **[Phase Plan](docs/05_phase-plan.md)** - Delivery phases and acceptance criteria
- **[Quality Gates](docs/06_quality-gates.md)** - Repository-level quality requirements

## Phase Delivery Principle

**Standards First, Features Second:**
1. Establish boundaries and contracts before implementation
2. Build data layers before intelligence layers
3. Ensure traceability before optimization
4. Validate with minimal scope before scaling

**Phase Progression:**
- Phase 1: Document/Page/Chunk/Retrieval foundation
- Phase 2: Fact extraction, review, structured query
- Phase 3: Domain package strengthening, external API
- Phase 4: Advanced capabilities (graph, fine-tuning samples)

Each phase must deliver:
- ✅ Runnable code
- ✅ Complete documentation
- ✅ Test coverage
- ✅ Acceptance validation

## Getting Started

See [docs/README.md](docs/README.md) for complete documentation navigation.

## License

[To be determined]
