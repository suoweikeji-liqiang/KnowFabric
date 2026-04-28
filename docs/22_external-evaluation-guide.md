# External Evaluation Guide

> **Status note (2026-04-27):** With the v0.1 integration contract in place,
> KnowFabric's primary consumer is sw_base_model. The external evaluation
> flow described below remains functional and is preserved as an optional
> standalone demo, but it is not the main delivery path. New work should
> target sw_base_model consumption first.

**Status:** Operator Guide - Productization
**Last Updated:** 2026-03-19

This guide is the shortest path for setting up KnowFabric in a fresh environment,
bootstrapping the read-only demo bundle, and handing the result to an external
evaluator.

It is intentionally scoped to the current productization surface:

- ontology-backed semantic retrieval
- fixed HVAC and drive demo query sets
- REST API and MCP read surfaces
- operator-facing bootstrap, smoke, and brief artifacts

It does not introduce a UI-first shell, project-instance modeling, runtime
control logic, or any shortcut around the six-layer evidence discipline.

This guide assumes a local Python + PostgreSQL setup. Docker packaging is not
currently checked into this workspace, so local bootstrap is the supported
evaluation path.

---

## What This Path Produces

The current evaluation path gives you:

- a migrated database
- synced HVAC and drive ontology metadata
- seeded demo knowledge fixtures
- semantic demo reports written under `output/demo/`
- MCP smoke reports written under `output/demo/`
- a Markdown handoff brief at `output/demo/v1_demo_brief.md`

Live API smoke is run after the API service is up, then folded back into the
same brief.

---

## 1. Prepare The Environment

From the repository root:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
createdb knowfabric
```

Update `.env` so `DATABASE_URL` points at the local PostgreSQL database you want
to use for the demo.

Use Python 3.11 for this flow. The current pinned dependency set is validated
against that interpreter line.

---

## 2. Bootstrap The Read-Only Demo Bundle

From the repository root:

```bash
python3 scripts/run_live_demo_evaluation.py --output-dir output/demo
```

This is the recommended one-shot path. It performs:

- environment preflight
- demo bootstrap
- temporary API startup
- live HVAC and drive API smoke
- brief rebuild
- manifest emission

Primary artifacts:

- `output/demo/EVALUATOR_NOTE.md`
- `output/demo/v1_demo_brief.md`
- `output/demo/live_demo_evaluation_manifest.json`
- `output/demo/demo_environment_preflight.json`
- `output/demo/api_service.log`

---

## 3. Manual Fallback Path

Use the manual path below when you want to inspect or rerun each phase separately.

```bash
python3 scripts/check_demo_environment.py --output-dir output/demo

python3 scripts/bootstrap_v1_demo.py \
  --output-dir output/demo \
  --brief-output output/demo/v1_demo_brief.md
```

The preflight step checks:

- Python interpreter compatibility
- config presence
- required demo files
- database connectivity
- output directory writability
- optional API health when a base URL is provided

Then bootstrap performs:

1. `alembic upgrade head`
2. ontology sync for `hvac` and `drive`
3. demo fixture seeding
4. semantic demo query execution
5. MCP smoke execution
6. brief generation

Primary bundle artifacts:

- `output/demo/hvac__example_queries__semantic_demo_report.json`
- `output/demo/drive__example_queries__semantic_demo_report.json`
- `output/demo/hvac__example_queries__mcp_smoke_report.json`
- `output/demo/drive__example_queries__mcp_smoke_report.json`
- `output/demo/v1_demo_brief.md`

---

## 4. Start The API And Run Live HTTP Smoke

In one terminal:

```bash
cd apps/api
python main.py
```

In another terminal from the repository root:

```bash
python3 scripts/run_api_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml \
  --base-url http://127.0.0.1:8000 \
  --output-dir output/demo

python3 scripts/run_api_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml \
  --base-url http://127.0.0.1:8000 \
  --output-dir output/demo
```

Then refresh the handoff brief so the live API results are folded into the same
artifact:

```bash
python3 scripts/build_v1_demo_brief.py \
  --report-dir output/demo \
  --output output/demo/v1_demo_brief.md
```

If the API is already running before bootstrap, you can also include live HTTP
smoke during bootstrap:

```bash
python3 scripts/bootstrap_v1_demo.py \
  --output-dir output/demo \
  --brief-output output/demo/v1_demo_brief.md \
  --api-base-url http://127.0.0.1:8000
```

---

## 5. Optional Standalone MCP Refresh

Bootstrap already runs MCP smoke. Use the standalone runner only when you want
to refresh MCP results without redoing the full bootstrap:

```bash
python3 scripts/run_mcp_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --output-dir output/demo
python3 scripts/run_mcp_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --output-dir output/demo
python3 scripts/build_v1_demo_brief.py --report-dir output/demo --output output/demo/v1_demo_brief.md
```

---

## 6. Handoff Checklist

Before handing the environment to an evaluator, confirm:

1. `output/demo/v1_demo_brief.md` reflects the latest bootstrap and smoke run.
2. HVAC and drive semantic demo reports both show zero failures.
3. HVAC and drive MCP smoke reports both show zero failures.
4. API smoke is either green or clearly marked pending in the brief.
5. The handoff artifact bundle stays read-only and evidence-backed.
6. No UI-first shell, project-instance logic, or runtime control logic was added.

---

## 7. Related Docs

- [README.md](../README.md) for the repo-level quickstart
- [docs/14_semantic-api-mcp-contract.md](14_semantic-api-mcp-contract.md) for the semantic delivery contract
- [apps/api/README.md](../apps/api/README.md) for API entry point notes
- [apps/mcp/README.md](../apps/mcp/README.md) for MCP entry point notes
