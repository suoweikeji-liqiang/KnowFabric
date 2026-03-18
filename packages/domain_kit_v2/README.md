# Domain Kit V2 Package

Ontology-first domain package helpers for the rebuild track.

## Responsibility

- define the minimal executable contract for `domain_packages/*/v2`
- load and validate `package.yaml` and `ontology/classes.yaml`
- keep rebuild-track package validation separate from legacy package files

## Current Scope

This package intentionally covers only the first rebuild backlog items:

- package metadata schema
- ontology class schema
- filesystem loading helpers for v2 package roots
- pure projection helpers for syncing ontology metadata into additive tables

Storage migrations, semantic API contracts, and MCP delivery schemas stay out of
scope until ontology identifiers are stable.
