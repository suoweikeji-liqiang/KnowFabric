# API Service

REST API service providing external access to KnowFabric knowledge assets.

## Phase 1 P0 Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with service info

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
