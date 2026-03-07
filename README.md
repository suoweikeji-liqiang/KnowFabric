# KnowFabric

**Industrial Knowledge Injection Platform**

## What KnowFabric Is

KnowFabric is an industrial knowledge injection platform that transforms raw technical documentation into structured, traceable knowledge assets through a mandatory six-layer data pipeline.

**Core Identity:**
- Knowledge engineering platform for industrial/energy domains
- Domain-agnostic foundation with pluggable domain packages
- Six-layer data architecture with mandatory traceability
- Service-oriented platform providing retrieval and query APIs

## What KnowFabric Is NOT

- ❌ NOT a chatbot or conversational AI shell
- ❌ NOT a document management system
- ❌ NOT an automatic knowledge graph inference engine
- ❌ NOT a device control system
- ❌ NOT a multi-tenant SaaS platform

## Current Priority: Governance and Main Chain

**This repository is currently in governance hardening phase.**

Priority is establishing:
1. Hard boundaries between modules
2. Mandatory data pipeline contracts
3. Runnable quality gates
4. Phase 1 implementation contract

**Not prioritizing:** Feature volume, UI shells, or advanced capabilities.

## Mandatory Data Pipeline

**The Only Valid Path:**
```
Raw Document → Page → Chunk → Fact → Retrieval/Export
```

Every knowledge output MUST trace through this pipeline. No shortcuts permitted.

## Phase 1 Scope

**Phase 1 ONLY builds:**
- Document ingestion with deduplication
- Page generation with traceability
- Chunk generation with semantic typing
- Basic retrieval (full-text + vector)
- Minimal job tracking and logging
- Two domain packages: hvac, drive

**Phase 1 explicitly does NOT build:**
- Heavy fact extraction engine
- Full review workflow platform
- Graph reasoning capabilities
- Fine-tuning factory
- Rich admin web interface

## Local Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/suoweikeji-liqiang/KnowFabric.git
cd KnowFabric
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Initialize database:
```bash
# Create database (PostgreSQL must be installed and running)
createdb knowfabric

# Run migrations
alembic upgrade head
```

### Running Services

**API Service:**
```bash
cd apps/api
python main.py
```

API will be available at http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

**Worker Service:**
```bash
cd apps/worker
python main.py
```

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

## Quality Gates

Run quality gates to validate repository standards:

```bash
# Individual gates
scripts/check-docs              # Documentation completeness
scripts/check-boundaries        # Module boundary compliance
scripts/check-forbidden-deps    # Forbidden dependency patterns

# All gates
scripts/check-all              # Run all quality checks
```

**All gates must pass before merge. No exceptions.**

## Standards and Governance

All development must follow the governance documents in `docs/`:

**Core Governance (Read First):**
- **[00_repo-charter.md](docs/00_repo-charter.md)** - Repository constitution with hard constraints
- **[01_system-boundaries.md](docs/01_system-boundaries.md)** - Module boundaries and forbidden dependencies
- **[02_data-layer-contract.md](docs/02_data-layer-contract.md)** - Six-layer data architecture with forbidden shortcuts

**Implementation Contracts:**
- **[05_phase-plan.md](docs/05_phase-plan.md)** - Phase delivery contracts with acceptance criteria
- **[06_quality-gates.md](docs/06_quality-gates.md)** - Quality gate specifications
- **[07_phase1-implementation-contract.md](docs/07_phase1-implementation-contract.md)** - Phase 1 hard boundaries

**Additional Standards:**
- **[03_domain-package-spec.md](docs/03_domain-package-spec.md)** - Domain package structure
- **[04_engineering-standards.md](docs/04_engineering-standards.md)** - Coding conventions

**These documents are binding contracts, not aspirational guidelines.**

## Getting Started

**New developers should:**
1. Read [docs/00_repo-charter.md](docs/00_repo-charter.md) - Understand what KnowFabric is and is NOT
2. Read [docs/01_system-boundaries.md](docs/01_system-boundaries.md) - Understand module boundaries
3. Read [docs/02_data-layer-contract.md](docs/02_data-layer-contract.md) - Understand the data pipeline
4. Read [docs/07_phase1-implementation-contract.md](docs/07_phase1-implementation-contract.md) - Understand Phase 1 scope
5. Run `scripts/check-all` to validate repository state

See [docs/README.md](docs/README.md) for complete documentation navigation.

## License

[To be determined]
