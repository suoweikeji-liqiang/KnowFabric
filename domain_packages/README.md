# Domain Packages

Domain-specific configurations for KnowFabric.

## Structure

Each domain package contains:
- `manifest.yaml` - Domain metadata and configuration
- `label_schema.yaml` - Label taxonomy
- `entity_schema.yaml` - Entity type definitions
- `relation_schema.yaml` - Relation type definitions
- `retrieval_profile.yaml` - Retrieval configuration
- `extraction_templates/` - Extraction templates

## Phase 1 Domains

- **hvac/** - HVAC systems domain
- **drive/** - Frequency converters and drives domain

## Future Domains

- energy_storage/ - Energy storage systems
- photovoltaics/ - Photovoltaic systems

See [Domain Package Spec](../docs/03_domain-package-spec.md) for details.
