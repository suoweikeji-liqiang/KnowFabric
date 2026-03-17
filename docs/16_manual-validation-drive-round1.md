# Drive Manual Validation Round 1

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-17

This note captures the first manual-driven validation pass for the `drive/v2`
 ontology package.

---

## Goal

Check whether the current `drive/v2` ontology and semantic fault delivery
contract can represent real variable-frequency-drive manuals used in HVAC and
 pump/fan scenarios.

---

## Manuals Reviewed

### Primary sources used for structured validation

1. `/Volumes/TSD302/pan/vfd/ABB/ABB_ACH531 HVAC控制程序固件手册_CN_revD.pdf`
2. `/Volumes/TSD302/pan/vfd/西门子/G120XA.pdf`

### Supporting source reviewed for application signal

3. `/Volumes/TSD302/pan/vfd/丹佛斯/VLT_Flow_Drive_FC_111_DG_M0029202_AJ363928382091zh-000101.pdf`

---

## What The Manuals Tell Us

### 1. `variable_frequency_drive` is the right top-level equipment class

The ABB and Siemens manuals are still clearly about variable-frequency drives,
not about a fundamentally different equipment ontology.

The manuals support keeping:

- `variable_frequency_drive`
- `frequency_converter`

as the canonical equipment classes.

At this stage, we do **not** need a separate `hvac_drive` canonical class.

### 2. HVAC and flow-drive language should be captured as aliases, not new classes

Real manuals use language such as:

- HVAC drive
- flow drive
- 风机
- 泵

These terms describe application positioning, firmware specialization, or load
type more often than they describe a separate equipment class.

The ontology therefore benefits from additional aliases on
`variable_frequency_drive`, but not from a new equipment class yet.

### 3. `parameter_spec` remains the right home for communication settings

The ABB ACH531 manual and Danfoss FC111 manual both include large sections on:

- parameter groups
- Modbus RTU
- BACnet MS/TP
- control words and communication setup

This supports keeping communication settings under `parameter_spec` for now,
rather than introducing a separate `communication_parameter` type too early.

### 4. `application_guidance` is justified by real manuals

The Danfoss FC111 manual contains direct pump/fan/flow application guidance:

- fan and pump control
- flow and pressure behavior
- energy-saving context

That means `application_guidance` is not speculative. It is supported by real
source material.

### 5. `fault_code` still works for drive warnings and faults

The ABB and Siemens manuals include warning/fault entries such as:

- `A7C1` fieldbus adapter communication
- `D50C` maximum flow protection
- `F07011` motor overtemperature fault
- `A01098` RTC date/time required

These still fit the current `fault_code` object type.

---

## Manual-Derived Validation Entries

The first structured batch is stored in:

- `/Users/asteroida/work/KnowFabric/tests/fixtures/manual_validation/drive_vfd_faults.json`

This batch includes:

- ABB `A7C1` fieldbus adapter communication warning
- ABB `D50C` maximum flow protection
- Siemens `F07011` motor overtemperature fault
- Siemens `A01098` RTC date/time required

These are used for route-level validation of the current semantic fault
contract against real VFD manuals.

---

## Validation Outcome

### Confirmed

- `drive/v2` is directionally correct.
- `variable_frequency_drive` is a viable canonical anchor for real manuals.
- `fault_code`, `parameter_spec`, and `application_guidance` are all justified.
- Brand and model-family applicability are required in real drive manuals too.

### Not Yet Proven

- automatic extraction from raw VFD manuals into chunk anchors and knowledge objects
- whether communication-heavy parameters need a dedicated knowledge object type later
- whether soft starters should remain in the same package without separate validation

### Immediate Implication

The next drive-focused steps should be:

1. manual-backed parameter-profile validation for Modbus/BACnet settings
2. one write path from raw manual evidence into drive fault knowledge objects
3. a second vendor beyond ABB/Siemens for broader fault vocabulary coverage
