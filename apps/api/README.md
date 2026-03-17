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

Additional semantic routes remain draft-only until semantic persistence is populated.

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
