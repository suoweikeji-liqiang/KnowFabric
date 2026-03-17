# Database Package

Database layer for KnowFabric providing session management and models.

## Responsibility

- Database connection and session management
- SQLAlchemy models for all entities
- Migration management via Alembic

## Phase 1 P0 Components

- `session.py` - Database session factory and management
- `models.py` - Active baseline tables for document/page/chunk processing
- `models_v2.py` - Draft rebuild-track storage contract for ontology-first tables

## Rebuild Note

`models_v2.py` is intentionally a draft contract only. It is not imported by
`init_db` and does not activate new tables until a dedicated migration lands.

## Module Boundaries

**May Depend On:**
- core (domain models)

**Must NOT Depend On:**
- domain-kit, processing modules

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
