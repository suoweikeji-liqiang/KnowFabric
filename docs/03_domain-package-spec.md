# Domain Package Specification

## Purpose

Domain packages isolate domain-specific logic from the core platform, enabling KnowFabric to expand from HVAC and drives to energy storage, photovoltaics, and other domains without rewriting the foundation.

## Domain Package Structure

Each domain package is a directory under `domain_packages/` containing:

```
domain_packages/{domain_name}/
├── manifest.yaml              # Domain metadata and configuration
├── label_schema.yaml          # Label taxonomy
├── entity_schema.yaml         # Entity type definitions
├── relation_schema.yaml       # Relation type definitions
├── retrieval_profile.yaml     # Retrieval configuration
├── extraction_templates/      # Extraction templates
│   ├── README.md
│   ├── fault_extraction.yaml
│   ├── parameter_extraction.yaml
│   └── control_extraction.yaml
├── export_profiles/           # Export configurations
│   ├── finetune_profile.yaml
│   └── graph_profile.yaml
├── ai_prompt_templates.yaml   # AI prompt templates (Phase 3)
└── terminology.yaml           # Terminology mapping (Phase 3)
```

## Manifest Schema

**File:** `manifest.yaml`

```yaml
domain_id: hvac                    # Unique domain identifier
domain_name: HVAC Systems          # Human-readable name
version: "1.0.0"                   # Domain package version
description: |
  HVAC domain package covering chillers, pumps, cooling towers,
  AHU, VRF systems, valves, sensors, and control strategies.

maintainers:
  - name: Knowledge Engineering Team
    email: knowledge@example.com

coverage:
  equipment_types:
    - chiller
    - pump
    - cooling_tower
    - ahu
    - vrf_system
    - valve
    - sensor

  knowledge_types:
    - fault_diagnosis
    - control_strategy
    - parameter_setting
    - maintenance_procedure

priority_brands:
  - Carrier
  - Trane
  - York
  - Daikin

supported_languages:
  - en
  - zh

dependencies:
  - domain_id: drive
    reason: HVAC systems use frequency converters for pump/fan control
```

## Label Schema

**File:** `label_schema.yaml`

```yaml
# Label taxonomy for domain-specific tagging
labels:
  equipment_type:
    - chiller
    - pump
    - cooling_tower
    - ahu
    - vrf_system
    - valve
    - sensor
    - controller

  document_type:
    - technical_manual
    - maintenance_guide
    - fault_code_reference
    - parameter_manual
    - installation_guide
    - training_material

  knowledge_type:
    - fault_diagnosis
    - control_strategy
    - parameter_setting
    - maintenance_procedure
    - troubleshooting

  brand:
    - Carrier
    - Trane
    - York
    - Daikin
    - McQuay
    - Midea
```

## Entity Schema

**File:** `entity_schema.yaml`

```yaml
# Entity type definitions for structured extraction
entities:
  equipment:
    description: Physical equipment or system
    attributes:
      - name
      - model
      - brand
      - capacity
      - power_rating
    examples:
      - "Carrier 30XA chiller"
      - "Grundfos CR pump"

  component:
    description: Equipment component or subsystem
    attributes:
      - name
      - parent_equipment
      - function
    examples:
      - "compressor"
      - "evaporator"
      - "expansion valve"

  fault_code:
    description: Equipment fault or alarm code
    attributes:
      - code
      - equipment_type
      - severity
    examples:
      - "E01"
      - "ALM-003"

  parameter:
    description: Configurable parameter
    attributes:
      - parameter_name
      - parameter_group
      - default_value
      - valid_range
    examples:
      - "P01 - Acceleration time"
      - "Setpoint temperature"

  symptom:
    description: Observable fault symptom
    attributes:
      - description
      - severity
    examples:
      - "High discharge pressure"
      - "Low cooling capacity"

  control_strategy:
    description: Control algorithm or strategy
    attributes:
      - name
      - target_variable
      - applicable_scenario
    examples:
      - "Chilled water temperature reset"
      - "VFD pump staging control"
```

## Relation Schema

**File:** `relation_schema.yaml`

```yaml
# Relation type definitions for fact extraction
relations:
  # Equipment relations
  has_component:
    domain: equipment
    range: component
    description: Equipment contains component
    examples:
      - "Chiller has_component compressor"

  monitors:
    domain: sensor
    range: parameter
    description: Sensor monitors parameter
    examples:
      - "Temperature sensor monitors chilled water temperature"

  controls:
    domain: controller
    range: equipment
    description: Controller controls equipment
    examples:
      - "DDC controller controls AHU"

  # Fault relations
  indicates:
    domain: fault_code
    range: symptom
    description: Fault code indicates symptom
    examples:
      - "E01 indicates high pressure"

  causes:
    domain: symptom
    range: fault
    description: Symptom causes fault
    examples:
      - "Low refrigerant causes low cooling capacity"

  may_cause:
    domain: symptom
    range: fault
    description: Symptom may cause fault (probabilistic)
    examples:
      - "Dirty filter may_cause high pressure drop"

  requires:
    domain: fault
    range: repair_action
    description: Fault requires repair action
    examples:
      - "Compressor failure requires replacement"

  # Control relations
  applies_to:
    domain: control_strategy
    range: equipment
    description: Strategy applies to equipment type
    examples:
      - "Temperature reset applies_to chiller"

  manipulates:
    domain: control_strategy
    range: parameter
    description: Strategy manipulates parameter
    examples:
      - "VFD control manipulates pump speed"

  # Parameter relations
  belongs_to:
    domain: parameter
    range: parameter_group
    description: Parameter belongs to group
    examples:
      - "P01 belongs_to acceleration_parameters"

  affects:
    domain: parameter
    range: behavior
    description: Parameter affects system behavior
    examples:
      - "Acceleration time affects motor startup"
```

## Retrieval Profile

**File:** `retrieval_profile.yaml`

```yaml
# Domain-specific retrieval configuration
retrieval:
  # Boost factors for different chunk types
  chunk_type_boost:
    fault_code_block: 1.5
    parameter_block: 1.3
    procedure_block: 1.2
    table_block: 1.1

  # Boost factors for document types
  document_type_boost:
    fault_code_reference: 1.4
    parameter_manual: 1.3
    technical_manual: 1.2

  # Boost factors for brands
  brand_boost:
    Carrier: 1.2
    Trane: 1.2
    York: 1.1

  # Minimum confidence threshold
  min_confidence: 0.3

  # Default result limit
  default_limit: 20

  # Filters
  default_filters:
    review_status: ["approved", "pending"]
    trust_level: ["L1", "L2", "L3"]
```

## Extraction Templates

**File:** `extraction_templates/fault_extraction.yaml`

```yaml
# Fault knowledge extraction template
template_id: hvac_fault_extraction
template_version: "1.0.0"
description: Extract fault-related knowledge from HVAC documents

target_chunk_types:
  - fault_code_block
  - procedure_block
  - paragraph

extraction_patterns:
  fault_code_definition:
    pattern: |
      Extract fault code, description, and severity
    output_schema:
      - fault_code: string
      - description: string
      - severity: enum[critical, high, medium, low]
      - equipment_type: string

  symptom_cause:
    pattern: |
      Extract symptom and possible causes
    output_schema:
      - symptom: string
      - causes: list[string]
      - probability: enum[certain, likely, possible]

  repair_action:
    pattern: |
      Extract repair actions for faults
    output_schema:
      - fault: string
      - actions: list[string]
      - required_tools: list[string]
      - estimated_time: string

confidence_rules:
  - condition: "Explicit fault code table"
    confidence: 0.95
  - condition: "Manufacturer manual"
    confidence: 0.90
  - condition: "Training material"
    confidence: 0.75
  - condition: "Inferred from context"
    confidence: 0.50
```

## Export Profiles

**File:** `export_profiles/finetune_profile.yaml`

```yaml
# Fine-tuning sample export configuration
profile_id: hvac_finetune_export
profile_version: "1.0.0"
description: Export HVAC knowledge as fine-tuning samples

sample_types:
  fault_diagnosis:
    input_template: |
      Equipment: {equipment_type}
      Symptom: {symptom}
      Question: What could be the cause and recommended action?

    output_template: |
      Possible cause: {cause}
      Recommended action: {repair_action}
      Source: {source_doc_name}, page {source_page_no}

    filters:
      trust_level: ["L1", "L2"]
      review_status: ["approved"]

  parameter_explanation:
    input_template: |
      Parameter: {parameter_name}
      Question: What does this parameter control?

    output_template: |
      {parameter_description}
      Default: {default_value}
      Range: {valid_range}
      Effect: {setting_effect}
      Source: {source_doc_name}, page {source_page_no}

    filters:
      trust_level: ["L1", "L2"]
      review_status: ["approved"]

output_format: jsonl
include_metadata: true
max_samples_per_type: 10000
```

## AI Prompt Templates (Phase 3)

**File:** `ai_prompt_templates.yaml`

AI prompt templates help AI agents formulate domain-appropriate queries and structure responses using domain knowledge.

### Schema

```yaml
templates:
  {template_id}:
    description: string           # What this template is for
    system_context: string        # System prompt context for the AI
    query_template: string        # Query template with {variables}
    response_guidance: string     # How to structure the response
    required_knowledge_types:     # Which knowledge types to retrieve
      - string
    variables:                    # Template variable definitions
      - name: string
        description: string
        required: boolean
```

### Example (HVAC)

```yaml
templates:
  fault_diagnosis:
    description: Guide AI to diagnose equipment faults using HVAC knowledge
    system_context: |
      You are an industrial HVAC expert. Use the provided knowledge
      to diagnose equipment faults. Always cite your sources with
      document name and page number.
    query_template: |
      Equipment: {equipment_type}
      Brand: {brand}
      Symptom: {symptom}
      Find relevant fault codes and recommended actions.
    response_guidance: |
      Structure your response as:
      1. Most likely fault code and cause
      2. Recommended diagnostic steps
      3. Repair actions with estimated time
      Always include source citations.
    required_knowledge_types:
      - fault_diagnosis
      - troubleshooting
    variables:
      - name: equipment_type
        description: Type of HVAC equipment (chiller, pump, AHU, etc.)
        required: true
      - name: brand
        description: Equipment brand/manufacturer
        required: false
      - name: symptom
        description: Observed symptom or fault description
        required: true

  parameter_lookup:
    description: Guide AI to find and explain equipment parameters
    system_context: |
      You are an industrial HVAC commissioning expert.
      Help users understand equipment parameters and their settings.
    query_template: |
      Equipment: {equipment_type}
      Parameter: {parameter_name}
      Explain this parameter and its recommended settings.
    response_guidance: |
      Include: parameter description, default value, valid range,
      effect of changing, and common use cases.
    required_knowledge_types:
      - parameter_setting
    variables:
      - name: equipment_type
        description: Type of equipment
        required: true
      - name: parameter_name
        description: Parameter name or code
        required: true
```

### Constraints

- Templates are pure YAML configuration (no executable code)
- Template variables use `{variable_name}` syntax
- Templates reference knowledge_types defined in the domain's label_schema
- Templates are consumed by AI agents, not executed by KnowFabric directly

## Terminology Mapping (Phase 3)

**File:** `terminology.yaml`

Terminology mappings provide consistent vocabulary normalization for AI agents working across languages and synonym variations.

### Schema

```yaml
terms:
  - canonical: string             # Canonical term (snake_case)
    aliases: [string]             # All known aliases and translations
    domain: string                # Which domain this term belongs to
    description: string           # Definition of the term
    category: string              # Term category (equipment, parameter, etc.)
```

### Example (HVAC)

```yaml
terms:
  - canonical: "variable_frequency_drive"
    aliases: ["VFD", "frequency converter", "inverter", "变频器", "变频驱动"]
    domain: hvac
    description: "Device that controls motor speed by varying electrical frequency"
    category: equipment

  - canonical: "chilled_water_supply_temperature"
    aliases: ["CHWST", "supply temp", "冷冻水供水温度", "供水温度"]
    domain: hvac
    description: "Temperature of chilled water leaving the chiller evaporator"
    category: parameter

  - canonical: "coefficient_of_performance"
    aliases: ["COP", "性能系数", "能效比"]
    domain: hvac
    description: "Ratio of cooling/heating output to energy input"
    category: metric
```

### Constraints

- Terminology files are pure YAML configuration
- Canonical terms use snake_case
- Aliases include Chinese equivalents where applicable
- Terms reference categories consistent with label_schema

## Distribution Mechanism (Phase 3)

Domain packages will support independent versioning and distribution:

### Planned Capabilities

- **Versioning:** Each domain package has a `version` field in manifest.yaml (semver)
- **Packaging:** Domain packages can be packaged as tarballs for distribution
- **Registry:** Local or remote registry for publishing/discovering domain packages
- **Installation:** CLI tool to install/update domain packages into a KnowFabric instance

### Constraints

- Distribution mechanism must not change the domain package directory structure
- Installed packages must pass the same validation as locally authored packages
- Version conflicts between dependent domains must be detected and reported

**Note:** Detailed distribution specification will be defined when Phase 3 implementation begins.

## Phase 1 Domain Packages

### HVAC Domain Package

**Location:** `domain_packages/hvac/`

**Coverage:**
- Chillers, pumps, cooling towers, AHU, VRF, valves, sensors
- Fault diagnosis and troubleshooting
- Control strategies and optimization
- Parameter configuration

**Priority Brands:** Carrier, Trane, York, Daikin

### Drive Domain Package

**Location:** `domain_packages/drive/`

**Coverage:**
- Frequency converters (ABB primary focus)
- Parameter settings and fault codes
- Commissioning and wiring
- HVAC-specific applications (pump/fan control)

**Priority Brands:** ABB, Siemens, Schneider

## Domain Package Constraints

### Isolation Rules

1. ✅ Domain packages contain ONLY configuration (no code)
2. ✅ Domain-specific logic implemented via templates and schemas
3. ✅ AI prompt templates and terminology files are also pure configuration
4. ❌ Domain packages MUST NOT import core modules
5. ❌ Domain packages MUST NOT contain hardcoded business logic
6. ❌ Domain packages MUST NOT directly access database
7. ❌ AI prompt templates MUST NOT contain executable logic

### Cross-Domain References

When one domain references another (e.g., HVAC references drive for VFD control):

```yaml
# In hvac/manifest.yaml
dependencies:
  - domain_id: drive
    reason: HVAC systems use frequency converters
    shared_entities:
      - vfd_controller
      - motor_parameter
```

### Validation Requirements

All domain packages must pass:
- Schema validation (YAML structure)
- Entity/relation consistency checks
- Template syntax validation
- No circular dependencies between domains
