# KnowFabric

KnowFabric is the domain knowledge compilation and authority engine for the
intelligent O&M platform at `sw_base_model`. It ingests raw industrial documents
(OEM manuals, service guides, parameter tables) and compiles them into
evidence-grounded knowledge objects (fault codes, parameter specs, diagnostic
chains, etc.) that sw_base_model consumes via REST and MCP.

KnowFabric does not own structural ontology (equipment classes, point classes,
relation types). Those live in sw_base_model. KnowFabric owns the content
layer: the knowledge objects, evidence chains, trust scoring, and health checks.

For the integration contract between the two repos, see
[docs/24_knowfabric-sw-base-model-contract.md](docs/24_knowfabric-sw-base-model-contract.md).

Current repository reality:

- ontology/storage/API/MCP semantic retrieval is wired end to end
- HVAC and drive demo query sets are runnable
- `scripts/bootstrap_v1_demo.py` can migrate, sync, seed, run semantic checks,
  run MCP smoke, and build a handoff brief
- API and MCP smoke paths remain available as optional standalone demos

Rebuild entry points:

- [ADR-0003](docs/adr/0003-promote-knowfabric-to-domain-knowledge-authority.md)
- [Ontology Authority Architecture](docs/09_ontology-authority-architecture.md)
- [Rebuild Plan](docs/10_rebuild-plan.md)
- [Semantic API and MCP Contract](docs/14_semantic-api-mcp-contract.md)
- [KnowFabric x sw_base_model Contract](docs/24_knowfabric-sw-base-model-contract.md)
- [External Evaluation Guide](docs/22_external-evaluation-guide.md) (historical standalone demo path)

## Product Boundary

KnowFabric owns:

- evidence-grounded knowledge objects
- semantic delivery through REST and MCP
- curated domain knowledge packs
- feedback and health signals for sw_base_model consumption

KnowFabric does not own:

- structural ontology definitions owned by sw_base_model
- project-instance or site runtime models
- control logic or live telemetry behavior
- UI-first product shells

The six-layer evidence discipline remains mandatory. Chunks stay the truth
source, and every semantic response must remain evidence-backed.

## Optional Standalone Evaluation Path

The primary delivery path is sw_base_model consumption through the v0.1
integration contract. The standalone evaluation flow below remains available for
operator demos and regression checks.

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
- `apps/admin-web/` now provides an optional read-only Chinese evaluation shell over `output/demo/`

To launch the Chinese demo shell in one command:

```bash
python3 scripts/run_chinese_demo_shell.py --output-dir output/demo
```

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
