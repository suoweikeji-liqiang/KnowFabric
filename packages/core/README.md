# Core Package

Core domain models, interfaces, and shared utilities for KnowFabric.

## Responsibility

- Define domain models and interfaces
- Provide type definitions for all entities
- Define contracts between modules
- Configuration management
- Logging setup

## Phase 1 P0 Components

- `config.py` - Application configuration
- `logging.py` - Structured logging setup
- `models.py` - Legacy chunk-search response models
- `semantic_contract_v2.py` - Draft rebuild-track semantic API and MCP contracts

## Module Boundaries

**May Depend On:**
- Standard library only

**Must NOT Depend On:**
- ANY other package in this repository

See [System Boundaries](../../docs/01_system-boundaries.md) for details.
