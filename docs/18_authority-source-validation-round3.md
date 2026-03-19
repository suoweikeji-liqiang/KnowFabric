# Authority Source Validation Round 3

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-18

This note captures a source-level validation pass across the local chiller,
drive, and authority-reference corpora used to guide the ontology-first rebuild.

It does not approve new schema by itself. It records which real source types now
fit the current chunk-backed review and backfill flow, and which source types
should be next.

---

## Goal

Check whether the current rebuild is still moving toward a domain knowledge
authority, not drifting into a narrow vendor fault-code tool.

The validation question for this round was:

- can the current semi-automated flow support knowledge objects that also appear
  in standards, handbooks, and reference material
- which real local sources are the best fit for the next expansion step

---

## Source Sets Reviewed

### 1. Chiller and HVAC equipment manuals

Primary local corpus:

- `/Volumes/TSD302/pan/a00238`

Representative source types found in this corpus:

- fault code books
- technical manuals
- operation manuals
- maintenance guides
- controller manuals
- product specification books

Examples used to steer this round:

- `/Volumes/TSD302/pan/a00238/13、天加中央空调/【天加】水冷螺杆式冷水机组操作使用说明书.3.pdf`
- `/Volumes/TSD302/pan/a00238/21、国祥/【国祥】KMS模块机操作用户手册-20RT30RT40RT（56页）.pdf`
- `/Volumes/TSD302/pan/a00238/20、欧科/【欧科】EKAS系列-螺杆式风冷冷水(热泵)(含热回收)机组样本(1012版).pdf`

### 2. Drive and VFD manuals

Primary local corpus:

- `/Volumes/TSD302/pan/vfd`

Representative source types found in this corpus:

- firmware manuals
- communication parameter guides
- Modbus register references
- getting-started guides
- programming manuals
- HVAC and flow-drive application manuals

Examples used to steer this round:

- `/Volumes/TSD302/pan/vfd/ABB/ABB_ACH531 HVAC控制程序固件手册_CN_revD.pdf`
- `/Volumes/TSD302/pan/vfd/西门子/G120XA.pdf`
- `/Volumes/TSD302/pan/vfd/丹佛斯/VLT_Flow_Drive_FC_111_DG_M0029202_AJ363928382091zh-000101.pdf`

### 3. Authority and reference corpus

Primary local corpus:

- `/Volumes/TSD302/19.暖通论文`

The most relevant subfolder for rebuild planning in this round was:

- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准`

Representative source types found in this corpus:

- ASHRAE handbooks
- ASHRAE best-practice and green-building guides
- HVAC energy audit and operations references
- HVAC control and design references
- building performance and simulation references

Examples used to steer this round:

- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE手册2024.pdf`
- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE 211能源审计最佳实践.pdf`
- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/HVAC系统高性能运行序列指南.pdf`
- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/HVAC系统效率和维护最佳实践.pdf`

---

## What This Round Confirms

### 1. The rebuild is not drifting into a fault-code-only product

The current chunk-backed review flow now fits at least these knowledge object
types against real local source material:

- `fault_code`
- `parameter_spec`
- `performance_spec`
- `maintenance_procedure`
- `diagnostic_step`

This matters because `performance_spec`, `maintenance_procedure`, and
`diagnostic_step` are common in technical manuals and authority references, not
only in vendor-specific troubleshooting tables.

### 2. `performance_spec` is the right bridge from vendor manuals to authority references

Real chiller manuals and reference books repeatedly express knowledge in forms
such as:

- rated cooling capacity
- nominal COP or EER
- flow or temperature performance values
- design or rated output conditions

That makes `performance_spec` the best current knowledge object for the next
step beyond parameter rows and fault codes.

### 3. `maintenance_procedure` and `diagnostic_step` also generalize well beyond vendor manuals

The local corpora contain not only equipment-specific service guidance, but also
best-practice and operations documents whose content fits the same object
shapes:

- cleaning and inspection procedures
- corrective checks
- maintenance best practices
- troubleshooting steps

This supports using the same chunk-backed review flow for both vendor manuals
and broader operational guidance, as long as the knowledge remains evidence
grounded and does not become project-instance runtime logic.

### 4. The current delivery surface still fits the safest next expansion

Existing semantic routes already support:

- fault knowledge
- parameter profiles
- maintenance guidance

Because `parameter_profiles` already includes `performance_spec`, and
`maintenance_guidance` already includes `diagnostic_step`, the rebuild can keep
advancing without opening a new public API surface first.

---

## What This Round Does Not Yet Prove

### 1. Authority references are not yet first-class reviewed sources in the repo

This round validates source fit and direction, but it does not yet establish a
curated reviewed fixture from an ASHRAE or handbook source inside the repo.

### 2. Concept-heavy standards content is still under-modeled

The local authority corpus contains content that is less naturally attached to a
single equipment class, for example:

- thermal comfort guidance
- building energy audit procedure
- generic design principles
- fan efficiency grade interpretation

Those items likely require stronger concept anchoring and possibly new semantic
delivery shapes later. They should not be forced prematurely into a vendor-style
equipment-only workflow.

### 3. Drive-side authority guidance beyond parameters is not yet semi-automated

Drive manuals clearly support future work on:

- `commissioning_step`
- `wiring_guidance`
- `application_guidance`

but those object types are not yet on the same semi-automated bundle path as
the five currently-supported object types above.

---

## Immediate Implications

### Best current expansion target

The safest next expansion target after this round is still:

- authority-like `performance_spec`
- authority-like `maintenance_procedure`
- authority-like `diagnostic_step`

because those fit both the current ontology anchors and the current semantic
read contracts.

### Best next drive-side targets

After the current five-object slice is stable, the next strongest drive-side
targets should be:

- `commissioning_step`
- `wiring_guidance`
- `application_guidance`

These are strongly represented in the local VFD corpus and align with the
existing `drive/v2` package contract.

### Best future authority-source design question

The next architecture question is no longer whether authority references belong
in KnowFabric. They do.

The next question is:

- how to anchor concept-heavy handbook and standards material without collapsing
  back into a generic document repository or leaking into downstream runtime
  modeling

That should be solved after the current evidence-grounded semi-automated flow is
stable across a few more knowledge object types.
