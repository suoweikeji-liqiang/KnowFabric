# Authority Source Validation Round 4

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-18

This note captures the next validation step after Round 3, focused on whether
the current semi-automated bundle workflow now covers a wider set of
authority-like knowledge object types from real local source corpora.

---

## Goal

Check whether the rebuild has moved beyond:

- fault-code extraction
- parameter row extraction

and now supports more handbook-like and guide-like knowledge shapes that are
common in vendor manuals, operating guides, and authority references.

---

## Source Sets Revisited

### 1. Chiller and HVAC manuals

Reviewed against:

- `/Volumes/TSD302/pan/a00238`

Representative source types confirmed in this round:

- screw chiller operating manuals
- technical specification books
- maintenance guides
- controller manuals

Examples:

- `/Volumes/TSD302/pan/a00238/13、天加中央空调/【天加】水冷螺杆式冷水机组操作使用说明书.3.pdf`
- `/Volumes/TSD302/pan/a00238/21、国祥/【国祥】KMS模块机操作用户手册-20RT30RT40RT（56页）.pdf`

### 2. Drive and VFD manuals

Reviewed against:

- `/Volumes/TSD302/pan/vfd`

Representative source types confirmed in this round:

- firmware manuals
- Modbus communication manuals
- getting-started and programming guides
- HVAC or flow-drive application guides

Examples:

- `/Volumes/TSD302/pan/vfd/ABB/ABB_ACH531 HVAC控制程序固件手册_CN_revD.pdf`
- `/Volumes/TSD302/pan/vfd/西门子/G120XA.pdf`
- `/Volumes/TSD302/pan/vfd/施耐德/ATV 610变频器Modbus通信手册_CN.pdf`
- `/Volumes/TSD302/pan/vfd/丹佛斯/VLT_Flow_Drive_FC_111_DG_M0029202_AJ363928382091zh-000101.pdf`

### 3. Authority and handbook corpus

Reviewed against:

- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准`

Representative source types confirmed in this round:

- ASHRAE handbooks
- HVAC best-practice guides
- HVAC energy audit references
- HVAC operations and efficiency guides
- design and system-analysis references

Examples:

- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE手册2024.pdf`
- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/ASHRAE 211能源审计最佳实践.pdf`
- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/HVAC系统高性能运行序列指南.pdf`
- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/HVAC系统效率和维护最佳实践.pdf`

---

## What Changed Since Round 3

Round 3 established that the rebuild direction was not drifting into a
fault-code-only system.

Round 4 confirms that the active semi-automated bundle workflow now covers
five object types end to end:

- `fault_code`
- `parameter_spec`
- `performance_spec`
- `maintenance_procedure`
- `diagnostic_step`

and also reaches two additional drive-side guide types in the same bundle flow:

- `commissioning_step`
- `wiring_guidance`

This means the rebuild is now directionally capable of handling:

- vendor troubleshooting material
- parameter and communication setup material
- rated performance statements
- maintenance procedures
- diagnostic actions
- commissioning and wiring guidance

without changing the core evidence path.

---

## What This Round Confirms

### 1. `performance_spec` is now a practical bridge object, not only a planned concept

The current bundle workflow now handles rated-value material such as:

- rated cooling capacity
- nominal COP or similar efficiency ratings

This matters because such knowledge is common both in vendor technical manuals
and in authority references such as handbooks, guidebooks, and standard-facing
performance discussions.

### 2. Guide-shaped knowledge now fits the same chunk-backed workflow

The drive corpus contains abundant material shaped like:

- startup and commissioning sequences
- parameter backup or initialization steps
- communication and terminal wiring guidance

The current flow now supports semi-automated handling of:

- `commissioning_step`
- `wiring_guidance`

at the storage and bundle level, even though these types are not yet exposed by
their own dedicated public semantic route.

### 3. Document profile constraints are now more important than raw keyword matching

Real local materials include overlapping language such as:

- performance terms inside maintenance context
- setup or communication language inside programming manuals
- checklist-style language inside different source types

This round confirms that the bundle workflow should continue using
`coverage/document_profiles.yaml` to narrow likely knowledge object types by
page or document profile before it trusts raw keyword detection.

That keeps the rebuild moving toward authority-grade curation rather than noisy
generic text mining.

---

## What Still Remains Open

### 1. `application_guidance` is justified by the drive corpus but not yet on the semi-automated path

The Danfoss and ABB HVAC/flow-drive materials clearly contain application notes
for pump and fan scenarios.

`application_guidance` remains a strong next candidate for the drive side, but
it is not yet on the same semi-automated bundle path as the seven object types
listed above.

### 2. Authority references still need concept-heavy anchoring work

The authority corpus includes knowledge that does not naturally attach to one
equipment class, for example:

- building energy audit procedure
- general design principles
- thermal comfort model interpretation
- broader building performance guidance

The rebuild still needs a careful concept-anchoring strategy before these
materials can become first-class curated sources in the same way as the current
equipment-attached objects.

### 3. Public semantic delivery still lags behind storage for some guide objects

`commissioning_step` and `wiring_guidance` now fit the bundle and persistence
flow, but the current public REST baseline does not yet expose dedicated routes
for these types.

This is acceptable for now because the rebuild charter prioritizes stronger
knowledge shaping and traceability before broader delivery expansion.

---

## Immediate Implications

### Best next drive-side target

The next most natural drive-side target is:

- `application_guidance`

because:

- the local corpus clearly supports it
- it aligns with the `drive/v2` package contract
- it would extend the rebuild further beyond fault/parameter material

### Best next authority-reference target

The next safest authority-reference-like target remains:

- performance guidance
- maintenance best practices
- operations and audit guidance that can still be attached to known system or
  equipment anchors

### Bigger architecture question after this slice

After the current seven-object slice is stable, the next major question is not
whether KnowFabric can ingest authority references.

It can.

The next question is:

- how to anchor handbook and standard content that is authoritative but not
  naturally bound to a single equipment class, without collapsing into a generic
  document repository

That should stay a later step, after the current equipment-attached semi-automated
flow is fully stable.
