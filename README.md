# KnowFabric

KnowFabric is rebuilding into an ontology-first domain knowledge authority and
publishing engine for industrial equipment knowledge.

Current repository reality:

- ontology/storage/API/MCP semantic retrieval is wired end to end
- HVAC and drive demo query sets are runnable
- `scripts/bootstrap_v1_demo.py` can migrate, sync, seed, run semantic checks,
  run MCP smoke, and build a handoff brief
- API and MCP smoke paths are available for external evaluation

Rebuild entry points:

- [ADR-0003](docs/adr/0003-promote-knowfabric-to-domain-knowledge-authority.md)
- [Ontology Authority Architecture](docs/09_ontology-authority-architecture.md)
- [Rebuild Plan](docs/10_rebuild-plan.md)
- [Semantic API and MCP Contract](docs/14_semantic-api-mcp-contract.md)
- [External Evaluation Guide](docs/22_external-evaluation-guide.md)

## Product Boundary

KnowFabric owns:

- canonical industrial ontology packages
- evidence-grounded knowledge objects
- semantic delivery through REST and MCP
- curated domain knowledge packs

KnowFabric does not own:

- project-instance or site runtime models
- control logic or live telemetry behavior
- UI-first product shells

The six-layer evidence discipline remains mandatory. Chunks stay the truth
source, and every semantic response must remain evidence-backed.

## Fastest Evaluation Path

From the repository root:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
createdb knowfabric
python3 scripts/run_live_demo_evaluation.py --output-dir output/demo
```

That one command now performs:

- preflight checks
- demo bootstrap
- temporary API startup
- live API smoke for HVAC and drive
- final brief rebuild
- evaluation manifest emission

Primary artifacts:

- `output/demo/EVALUATOR_NOTE.md`
- `output/demo/v1_demo_brief.md`
- `output/demo/live_demo_evaluation_manifest.json`
- `output/demo/api_service.log`

See [docs/22_external-evaluation-guide.md](docs/22_external-evaluation-guide.md)
for the full operator-facing flow and the manual fallback path.

## Service Entry Points

- `apps/api/` exposes the REST surface, including `/api/v1/chunks/search` and
  rebuild-track semantic routes under `/api/v2/`
- `apps/mcp/` exposes the read-only MCP tool surface for semantic retrieval
- `apps/worker/` is not required for the current read-only demo evaluation path
- `apps/admin-web/` is not part of the current productization path

## Repository Guide

- `docs/README.md` is the main document index
- `scripts/README.md` lists operator, demo, and curation scripts
- `domain_packages/hvac/v2/examples/example_queries.yaml` is the fixed HVAC demo query set
- `domain_packages/drive/v2/examples/example_queries.yaml` is the fixed drive demo query set

## Local Development

Minimal local setup:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
createdb knowfabric
alembic upgrade head
```

Service commands:

```bash
cd apps/api && python main.py
cd apps/mcp && python main.py
cd apps/worker && python main.py
```

Docker packaging is not currently checked into this workspace. For external
evaluation today, use the local bootstrap path above instead of a compose
workflow.

## Quality Gates

All work must pass:

```bash
bash scripts/check-docs
bash scripts/check-boundaries
bash scripts/check-forbidden-deps
bash scripts/check-all
```

These are binding gates, not optional hygiene checks.

## Python Version Note

Use Python 3.11 for the current pinned dependency set. Newer interpreter
versions may require dependency upgrades before the same setup path will work.
