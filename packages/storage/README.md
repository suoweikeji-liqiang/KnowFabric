# Storage Package

File and object storage abstraction.

## Responsibility

- Store and retrieve raw documents
- Store and retrieve page assets
- Store and retrieve export files
- Handle file hashing and deduplication

## Constraints

- ❌ MUST NOT parse file contents
- ✅ Storage operations only
