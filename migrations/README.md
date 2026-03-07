# Database Migrations

This directory contains Alembic database migrations for KnowFabric.

## Running Migrations

### Initialize Database

First, ensure PostgreSQL is running and the database exists:

```bash
# Create database (if not exists)
createdb knowfabric
```

### Apply Migrations

```bash
# Run all pending migrations
alembic upgrade head
```

### Check Migration Status

```bash
# Show current migration version
alembic current

# Show migration history
alembic history
```

## Migration Files

- `001_create_baseline_tables.py` - Initial schema with document/page/chunk/job tables

## Creating New Migrations

```bash
# Create a new migration
alembic revision -m "description"
```

See [Engineering Standards](../docs/04_engineering-standards.md) for migration conventions.
