# KnowFabric

**Embeddable Knowledge Engineering Engine for Industrial Domains**

KnowFabric is entering a rebuild track to become an ontology-first domain knowledge authority and publishing engine for industrial equipment knowledge.

Rebuild entry points:

- [ADR-0003](docs/adr/0003-promote-knowfabric-to-domain-knowledge-authority.md)
- [Ontology Authority Architecture](docs/09_ontology-authority-architecture.md)
- [Rebuild Plan](docs/10_rebuild-plan.md)

## What KnowFabric Is

KnowFabric is an embeddable knowledge engineering engine that transforms raw technical documentation into structured, traceable knowledge assets through a mandatory six-layer data pipeline, and delivers them via integration APIs to AI agents, developers, and applications.

**Core Identity:**
- Embeddable knowledge engineering engine (not a standalone application)
- Domain-agnostic foundation with pluggable domain packages
- Six-layer data architecture with mandatory traceability
- Integration-first: REST API, MCP Server, and SDK as primary interfaces
- AI agents are first-class consumers

## What KnowFabric Is NOT

- ❌ NOT a chatbot or conversational AI shell
- ❌ NOT a document management system
- ❌ NOT an automatic knowledge graph inference engine
- ❌ NOT a device control system
- ❌ NOT a multi-tenant SaaS platform
- ❌ NOT an end-user application (it powers applications)
- ❌ NOT a chat frontend or UI-first product

## Integration Examples

### REST API

```bash
# Upload a document (async)
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@manual.pdf" -F "domain=hvac"
# → 202 Accepted {"data": {"job_id": "job_abc123", "poll_url": "/api/v1/jobs/job_abc123"}}

# Search knowledge with traceability
curl -X POST http://localhost:8000/api/v1/chunks/search \
  -H "Content-Type: application/json" \
  -d '{"query": "chiller fault E01", "domain": "hvac"}'
# → Results with doc_id, page_no, chunk_id, evidence_text
```

### MCP Server (for AI Agents)

```json
// AI agent calls search_knowledge via MCP
{
  "tool": "search_knowledge",
  "arguments": {
    "query": "ACS880 overcurrent fault diagnosis",
    "domain": "drive",
    "limit": 5
  }
}
// → Structured results with citations and traceability
```

### Python SDK (Phase 3)

```python
from knowfabric import KnowFabric

kf = KnowFabric(base_url="http://localhost:8000")
results = kf.search("chiller fault codes", domain="hvac", limit=10)
for r in results:
    print(f"{r.content} [Source: {r.citation.doc_name} p.{r.citation.page_no}]")
```

## Mandatory Data Pipeline

**The Only Valid Path:**
```
Raw Document → Page → Chunk → Fact → Retrieval/Export
```

Every knowledge output MUST trace through this pipeline. No shortcuts permitted.

## Phase 1 Scope

**Phase 1 builds:**
- Document ingestion with deduplication
- Page generation with traceability
- Chunk generation with semantic typing
- Basic retrieval (full-text + vector)
- Minimal job tracking and logging
- Two domain packages: hvac, drive
- Integration API baseline (document upload, status, trace, search)
- MCP Server baseline (search_knowledge, trace_evidence, list_domains)
- Docker deployment baseline

**Phase 1 explicitly does NOT build:**
- Heavy fact extraction engine
- Full review workflow platform
- Graph reasoning capabilities
- Fine-tuning factory
- Rich admin web interface
- AI-optimized knowledge delivery (Phase 2)
- Python SDK (Phase 3)

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

**MCP Server:**
```bash
cd apps/mcp
python main.py
```

**Docker (Full Stack):**
```bash
docker-compose up
```

## Monorepo Structure

```
KnowFabric/
├── apps/                    # Application entry points
│   ├── api/                # REST API service
│   ├── worker/             # Background processing workers
│   ├── mcp/               # MCP Server for AI agent integration
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
├── final_docs/            # Original requirement documents
└── docker-compose.yml     # Docker deployment configuration
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
- **[08_ai-consumer-contract.md](docs/08_ai-consumer-contract.md)** - AI consumer interface contract

**These documents are binding contracts, not aspirational guidelines.**

## Getting Started

**New developers should:**
1. Read [docs/00_repo-charter.md](docs/00_repo-charter.md) - Understand what KnowFabric is and is NOT
2. Read [docs/01_system-boundaries.md](docs/01_system-boundaries.md) - Understand module boundaries
3. Read [docs/02_data-layer-contract.md](docs/02_data-layer-contract.md) - Understand the data pipeline
4. Read [docs/07_phase1-implementation-contract.md](docs/07_phase1-implementation-contract.md) - Understand Phase 1 scope
5. Read [docs/08_ai-consumer-contract.md](docs/08_ai-consumer-contract.md) - Understand AI consumer interfaces
6. Run `scripts/check-all` to validate repository state

See [docs/README.md](docs/README.md) for complete documentation navigation.

## License

[To be determined]
