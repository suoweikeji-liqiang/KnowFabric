# Manual Validation Round 1

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-17

This note captures the first manual-driven validation pass against the
ontology-first rebuild.

---

## Goal

Check whether the current ontology and semantic fault delivery contract can
represent real HVAC manuals without drifting into project-instance modeling.

---

## Manuals Reviewed

### Primary sources used for structured validation

1. `/Users/asteroida/a00238/11、奥克斯/【奥克斯】中央空调故障代码(模块机、多联机).pdf`
2. `/Users/asteroida/a00238/21、国祥/【国祥】KMS模块机操作用户手册-20RT30RT40RT（56页）.pdf`
3. `/Users/asteroida/a00238/13、天加中央空调/【天加】水冷螺杆式冷水机组操作使用说明书.3.pdf`

### Secondary source reviewed for signal only

4. `/Users/asteroida/a00238/20、欧科/【欧科】模块化风冷冷水热泵机组报警代码和维修步骤.pdf`

The Ouke manual appears relevant, but text extraction quality is too poor for
reliable structured validation in this round.

---

## What The Manuals Tell Us

### 1. HVAC ontology was missing a real equipment family

The current `hvac/v2` package originally lacked a canonical class for
module-based air-cooled chilled/hot water units.

Real manuals repeatedly use terms such as:

- 模块机
- 模块式风冷冷热水机组
- 风冷模块机
- 模块化风冷冷水热泵机组

That gap is now addressed by adding:

- `modular_chiller`
- `air_cooled_modular_heat_pump`

to the HVAC ontology package.

### 2. `fault_code` is still the right first knowledge object type

The AUX and Guoxiang manuals both organize fault delivery around code-oriented
entries that map cleanly to:

- code
- trigger/condition
- protection behavior
- recommended checks or reset actions

This fits the current `fault_code` knowledge object type and does not yet
require a new type.

### 3. `diagnostic_step` remains useful but should often stay nested for now

The manuals often include troubleshooting actions together with the fault entry.
For the first runtime slice, storing those actions inside
`structured_payload.recommended_actions` is acceptable.

We should not split every manual row into multiple independent knowledge objects
until we have more evidence from additional brands.

### 4. `screw_chiller` looks directionally correct

The TICA water-cooled screw chiller manual supports the current ontology around:

- `screw_chiller`
- `parameter_spec`
- `maintenance_procedure`
- `diagnostic_step`

The bigger gap today is not screw chillers. It is module-unit coverage.

---

## Manual-Derived Validation Entries

The first structured batch is stored in:

- `/Users/asteroida/work/KnowFabric/tests/fixtures/manual_validation/hvac_module_faults.json`

This batch includes:

- AUX `E01` water flow switch protection
- AUX `E22` high pressure switch protection
- AUX `E23` low pressure switch protection
- Guoxiang `49` 1#/3# compressor high pressure
- Guoxiang `50` 1#/3# compressor overload

These entries are used for route-level validation of the current semantic fault
contract.

---

## Validation Outcome

### Confirmed

- The rebuild can represent real module-unit fault rows without violating the
  evidence chain.
- `fault-knowledge` query shape is still viable.
- Brand and model-family applicability filters are useful on real manuals.
- Domain-scoped equipment identity is necessary and still correct.

### Not Yet Proven

- Automatic extraction from raw manuals into chunk anchors and knowledge objects
- `parameter_profile` and `maintenance_guidance` on real manuals
- `drive/v2` ontology against real VFD manuals

### Immediate Implication

The next validation rounds should focus on:

1. manual-backed write paths for chunk anchors and fault knowledge
2. a real drive/VFD manual
3. parameter and maintenance validation for screw chillers or module units
