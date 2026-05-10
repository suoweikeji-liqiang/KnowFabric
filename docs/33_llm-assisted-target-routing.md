# LLM-Assisted Target Routing for Standard References

## Why this exists

The current standard-reference pipeline already improved from page-first to section-first, but the remaining failures show a deeper issue:

- we can heuristically guess **knowledge types**
- but we still often misroute **document mission** and **section topic/object**
- once that happens, extraction and judge both operate under the wrong objective

Two recent failures make this clear:

- `ASHRAE 211` selected the right sections, but the knowledge target was wrong: it is an audit/methodology source, not a chiller-equipment source.
- `ASHRAE绿色建筑指南` selected sections about dynamic glazing and desiccant systems, but the route forced them into `chiller`, so the judge correctly rejected everything.

This means heuristic routing has reached its ceiling. We need more LLM participation **before extraction**, not only during extraction and judge.

---

## Core principle

Routing should become:

`Document -> LLM document mission routing -> LLM section topic/object routing -> allowed knowledge targets -> extraction -> judge`

Instead of:

`Document -> heuristic keyword match -> default equipment anchor -> extraction`

The LLM is not replacing evidence anchoring or judge. It is deciding:

1. **What kind of document this is**
2. **What each section is actually about**
3. **Which knowledge targets are allowed for that section**
4. **Whether the section should enter the current extraction lane at all**

---

## Routing layers

### 1. Document-level route

The document-level route answers:

- What family of source is this?
- Should it enter an equipment-operational pipeline?
- What default anchor policy should be used?

Recommended labels:

- `equipment_manual`
- `design_handbook`
- `standard_reference`
- `methodology_guide`
- `system_topic_guide`
- `cross_domain_sustainability_guide`

And one higher-level lane decision:

- `equipment_operational`
- `system_design`
- `audit_methodology`
- `sustainability_topic`
- `mixed`

Example:

- `ASHRAE 211` -> `methodology_guide` + `audit_methodology`
- `ASHRAE绿色建筑指南` -> `cross_domain_sustainability_guide` + `mixed`
- `ASHRAE手册2024` -> `design_handbook` + `system_design`

### 2. Section-level route

For each section, the LLM should decide:

- section topic/object
- whether the section belongs to the current lane
- what equipment anchor is valid, if any
- what knowledge types are allowed

Recommended section topic labels:

- `chiller`
- `ahu`
- `cooling_tower`
- `pump`
- `boiler`
- `valve_control`
- `desiccant_system`
- `dynamic_glazing`
- `air_distribution`
- `general_hvac_design`
- `audit_process`
- `reporting_requirement`
- `sustainability_general`
- `unknown`

### 3. Allowed knowledge targets per route

The section route should output an allowlist, not just a topic guess.

Examples:

#### If topic = `chiller`
Allowed:
- `parameter_spec`
- `operational_sequence`
- `maintenance_procedure`
- `performance_spec`
- `application_guidance`

#### If topic = `audit_process`
Allowed:
- `application_guidance`
- `workflow_step` (future)
- `assessment_requirement` (future)
- `deliverable_requirement` (future)

#### If topic = `dynamic_glazing`
Allowed:
- currently **not** in the chiller-equipment lane
- should be skipped or routed to a future envelope/sustainability lane

---

## What the LLM should decide versus what rules should still do

### LLM should decide

- document mission/family
- section topic/object
- whether a section belongs to the active extraction lane
- which knowledge targets are semantically appropriate
- whether the default equipment anchor is wrong

### Rules should still do

- page/chunk traceability
- evidence anchoring
- canonical key normalization
- duplicate checks
- output schema validation
- safety filters on malformed or empty outputs

This preserves the six-layer evidence discipline while letting the LLM handle the ambiguous semantic routing step.

---

## Operational design

### Input to the router

The router should consume the section matrix, not raw pages directly.

For each document:

- file name
- doc name
- a compact section list
  - title
  - page range
  - chunk count
  - sample text
  - heuristic candidate types

### Output from the router

Augment the section matrix with fields such as:

- `llm_document_family`
- `llm_document_lane`
- `llm_default_equipment_anchor`
- `llm_section_topic`
- `llm_knowledge_goal`
- `llm_allowed_knowledge_types`
- `llm_should_extract`
- `llm_equipment_anchor`
- `llm_route_reason`
- `llm_route_confidence`

The section selector should treat these fields as first-class signals.

---

## Immediate changes recommended

### 1. Add a routing step before subset selection

`section_target_matrix -> llm_route_standard_sections -> routed_matrix -> subset_selection`

### 2. Stop forcing all standard references into `chiller`

The current `suggested_standard_equipment_anchor()` default is too aggressive for broad ASHRAE references.

### 3. Treat `ASHRAE 211` as a methodology track source

Do not keep retrying it in the chiller-operational lane.

### 4. Treat `ASHRAE绿色建筑指南` as mixed-topic

Require section-level topic routing before extraction.

---

## Success criteria

This routing upgrade is successful when:

- methodology guides are no longer judged as failed equipment manuals
- mixed-topic handbooks stop leaking unrelated sections into the wrong equipment lane
- fewer extracted candidates are rejected for `other` or `wrong object` reasons
- more of the extraction budget is spent on semantically valid sections
- routing decisions are inspectable and replayable as structured artifacts

---

## Non-goal

This is **not** generic free-form agent reasoning over the corpus.

The routing LLM is a bounded classifier/planner inside the evidence-first pipeline. It decides the target lane; it does not replace extraction, evidence, or validation.
