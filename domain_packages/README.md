# Domain Packages

Domain-specific configurations for KnowFabric.

## Structure

Legacy Phase 1 packages still use:
- `manifest.yaml` - Domain metadata and configuration
- `label_schema.yaml` - Label taxonomy
- `entity_schema.yaml` - Entity type definitions
- `relation_schema.yaml` - Relation type definitions
- `retrieval_profile.yaml` - Retrieval configuration
- `extraction_templates/` - Extraction templates

Rebuild-track packages may also add a parallel `v2/` directory with:
- `package.yaml` - Ontology-first package metadata
- `ontology/classes.yaml` - Canonical class identifiers and anchors
- `ontology/relations.yaml` - Canonical relation vocabulary
- `delivery/` - Semantic query and response placeholders
- `coverage/` - Brand/document coverage and exclusions

## Phase 1 Domains

- **hvac/** - HVAC systems domain
- **drive/** - Frequency converters and drives domain

## Future Domains

- energy_storage/ - Energy storage systems
- photovoltaics/ - Photovoltaic systems

See [Domain Package Spec](../docs/03_domain-package-spec.md) for the legacy
baseline and [Rebuild Plan](../docs/10_rebuild-plan.md) for the ontology-first
track.
