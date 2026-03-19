# Authority Source Validation Round 6

**Status:** Rebuild Validation Note
**Last Updated:** 2026-03-18

This note captures the next validation step after Round 5, focused on whether
the rebuild can now carry a first HVAC-side authority-guide knowledge object
through the same semi-automated flow.

---

## Goal

Check whether authority-style HVAC sequence and application guidance from a real
ASHRAE guide can now move through:

- chunk-backed candidate generation
- review bundle preparation
- ready-only apply
- semantic read delivery

without introducing a second data path.

---

## Real Authority Source Used

Primary reference used in this round:

- `/Volumes/TSD302/19.暖通论文/英文文献/手册与标准/HVAC系统高性能运行序列指南.pdf`

This file corresponds to:

- ASHRAE Guideline 36
- high-performance sequences of operation for HVAC systems

The specific content used to validate the current step was the AHU mode
hierarchy material around the air-handling-unit sequence section.

Representative extracted content:

- when zone groups served by an AHU are in different modes, the AHU follows a
  defined priority hierarchy such as Occupied, Cooldown, Setup, Warmup, Setback,
  and Unoccupied

---

## What This Round Confirms

### 1. HVAC-side `application_guidance` is now justified and active

The rebuild previously proved drive-side application guidance through flow-drive
and pump/fan material.

This round confirms that HVAC-side authority guides also contain guidance that is
best represented as:

- `application_guidance`

rather than being forced into:

- `maintenance_procedure`
- `diagnostic_step`
- `performance_spec`

### 2. The semi-automated flow now spans vendor and authority application guidance

The current bundle and apply-ready workflow now supports:

- drive-side `application_guidance`
- HVAC-side `application_guidance`

That matters because it is the clearest signal so far that the rebuild is
moving toward a true authority-layer product instead of remaining a vendor
manual post-processor.

### 3. HVAC package v2 can be extended additively without breaking the rebuild path

This round required only additive HVAC package updates:

- `application_guidance` added to supported knowledge objects
- HVAC `application_guide` document profile added
- selected HVAC equipment anchors updated to support `application_guidance`

No legacy compatibility surface had to be removed or rewritten.

---

## What Still Remains Open

### 1. General system and building guidance is still under-anchored

The local authority corpus also contains guidance that is broader than one AHU
or one equipment family, for example:

- energy audit procedure
- building performance analysis
- broader design and operating principles

Those items still need a stronger concept-anchoring approach before they can
enter the same curated path safely.

### 2. Public semantic delivery is still selective

At this stage, the public semantics-first read surfaces now cover:

- fault knowledge
- parameter profiles
- maintenance guidance
- application guidance

but not every stored knowledge object type yet.

This is still acceptable because the rebuild is adding delivery surfaces only
when a type is proven against real material and can be kept additive.

---

## Immediate Implications

### Best next authority-like expansion target

The next most natural authority-side expansion target is likely one of:

- HVAC operating best practices
- energy-audit or efficiency guidance that can still be attached to an HVAC
  class
- design or sequence guidance attached to an existing equipment class

### Best next architecture question

The next architecture question is no longer whether authority guides fit the
current rebuild.

They do.

The next question is:

- how far the current equipment-attached model can stretch before more explicit
  concept-level authority anchors become necessary

That should remain a later step, after a few more authority-backed examples are
stable in the current reversible path.
