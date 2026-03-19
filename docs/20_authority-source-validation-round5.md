# Authority Source Validation Round 5

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-18

This note captures the next rebuild validation step after Round 4, focused on
drive-side guide material and whether the rebuild can now carry more
authority-like application knowledge instead of only troubleshooting and
settings.

---

## Goal

Check whether the current semi-automated review and bundle flow now supports a
drive-side knowledge type that looks more like handbook or guide content:

- `application_guidance`

This matters because authority-style HVAC references often express knowledge as:

- use-case guidance
- application notes
- scenario-specific operating advice
- design and selection implications

rather than only as parameter rows or fault tables.

---

## Real Source Focus For This Round

### Drive corpus used to steer the implementation

Primary local corpus:

- `/Volumes/TSD302/pan/vfd`

The most relevant source families for this round were:

- HVAC-oriented drive firmware manuals
- flow-drive design guides
- communication and getting-started guides

Representative source files reviewed:

- `/Volumes/TSD302/pan/vfd/丹佛斯/VLT_Flow_Drive_FC_111_DG_M0029202_AJ363928382091zh-000101.pdf`
- `/Volumes/TSD302/pan/vfd/ABB/ABB_ACH531 HVAC控制程序固件手册_CN_revD.pdf`
- `/Volumes/TSD302/pan/vfd/西门子/G120XA.pdf`
- `/Volumes/TSD302/pan/vfd/施耐德/ATV 610变频器Modbus通信手册_CN.pdf`

### Why these matter

These manuals contain not only:

- fault codes
- parameters
- wiring
- commissioning

but also direct application language around:

- pump control
- fan control
- flow behavior
- pressure behavior
- HVAC-oriented usage scenarios

That is the right local signal for validating `application_guidance`.

---

## What This Round Confirms

### 1. `application_guidance` is justified by real drive material

The local flow-drive and HVAC-drive materials repeatedly use guidance-shaped
phrasing that fits:

- canonical application notes
- pump/fan use-case guidance
- flow and pressure behavior guidance

This confirms that `application_guidance` should remain inside KnowFabric’s
authority scope for the drive domain.

### 2. The semi-automated bundle workflow now reaches eight knowledge object types

With this round, the active chunk-backed review flow now supports:

- `fault_code`
- `parameter_spec`
- `performance_spec`
- `maintenance_procedure`
- `diagnostic_step`
- `commissioning_step`
- `wiring_guidance`
- `application_guidance`

This is now materially broader than a vendor fault-code or settings workflow.

### 3. The rebuild now exposes a first read-only semantic surface for application guidance

An additive route is now valid for:

- drive-side application guidance by canonical equipment class

This keeps the rebuild aligned with the existing semantics-first direction
without altering legacy compatibility routes.

---

## What Still Remains Open

### 1. Authority-reference material still needs stronger concept anchoring

The local standards and handbook corpus contains broader guidance such as:

- design heuristics
- energy audit logic
- thermal comfort interpretation
- system-level best practices

Those materials still need a stronger concept-anchoring strategy before they
become first-class curated sources in the same way as the currently
equipment-attached objects.

### 2. Drive-side `application_guidance` is still equipment-attached first

This round keeps the guidance attached to:

- `variable_frequency_drive`

That is the safest reversible step. It does not yet attempt to introduce a more
abstract application ontology such as a separate canonical pump-system or
fan-system knowledge carrier.

---

## Immediate Implications

### Best next authority-like target after this round

The next most promising target is no longer another vendor-style troubleshooting
type. It is likely one of:

- broader system performance guidance
- selection or design criteria tied to existing equipment or concept anchors
- authority-reference summaries grounded in handbook or standard text

### Best next drive-side target after this round

The next drive-side expansion should likely focus on:

- richer `application_guidance`
- or a first pass at `commissioning_step -> wiring_guidance -> application_guidance`
  sequence curation across one vendor family

depending on which local manuals give the cleanest repeatable chunks.
