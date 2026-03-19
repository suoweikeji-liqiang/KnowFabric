# API Service

REST API service providing external access to KnowFabric knowledge assets.

## Phase 1 P0 Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with service info
- `GET /api/v1/chunks/search` - Legacy chunk search compatibility endpoint

## Rebuild Note

Semantic ontology-first delivery is currently documented as a draft contract in
[`docs/14_semantic-api-mcp-contract.md`](../../docs/14_semantic-api-mcp-contract.md).
The first minimal read-only route is wired in `main.py`:

- `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}`
- `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/fault-knowledge`
- `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/parameter-profiles`
- `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/maintenance-guidance`
- `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/application-guidance`
- `GET /api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/operational-guidance`

Additional semantic routes remain draft-only until semantic persistence is populated.

## Demo Query Set

Once semantic knowledge has been populated, run the fixed HVAC authority demo
queries from the repository root:

```bash
python3 scripts/run_semantic_demo_queries.py domain_packages/hvac/v2/examples/example_queries.yaml
```

The current demo query set expects HVAC authority-backed objects to be present
at trust level `L3`, so the bundled examples apply `min_trust_level=L3`.

A matching drive-domain demo query set is also available:

```bash
python3 scripts/run_semantic_demo_queries.py domain_packages/drive/v2/examples/example_queries.yaml --output-dir output/demo
```

## Service Smoke Path

After bootstrapping the demo knowledge, start the API service and verify the
same demo queries through real HTTP routes:

```bash
cd apps/api
python main.py
```

From another terminal at the repository root:

```bash
python3 scripts/run_api_demo_smoke.py domain_packages/hvac/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo
python3 scripts/run_api_demo_smoke.py domain_packages/drive/v2/examples/example_queries.yaml --base-url http://127.0.0.1:8000 --output-dir output/demo
```

## Running Locally

```bash
# From repository root
cd apps/api
python main.py
```

API will be available at http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## Configuration

Configuration is loaded from environment variables or `.env` file:

```
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql://user:pass@localhost:5432/knowfabric
LOG_LEVEL=INFO
```

See [Engineering Standards](../../docs/04_engineering-standards.md) for API conventions.
