# Database Package

Database layer for KnowFabric providing session management and models.

## Responsibility

- Database connection and session management
- SQLAlchemy models for all entities
- Migration management via Alembic

## Phase 1 P0 Components

- `session.py` - Database session factory and management

## Module Boundaries

**May Depend On:**
- core (domain models)

**Must NOT Depend On:**
- domain-kit, processing modules

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
