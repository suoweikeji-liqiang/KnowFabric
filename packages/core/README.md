# Core Package

Domain models, interfaces, and types used across all packages.

## Responsibility

- Define domain entities (Document, Page, Chunk, Fact)
- Define interfaces for repositories and services
- Define shared types and enums

## Constraints

- ❌ MUST NOT depend on any other package
- ❌ MUST NOT contain business logic
- ✅ Pure data models and interfaces only
