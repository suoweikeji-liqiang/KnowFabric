# Internal Workbench UI Style Guide

**Status:** Rebuild Design Guide  
**Last Updated:** 2026-03-21

This document defines the visual style, interaction constraints, and page-level
rules for the first internal KnowFabric workbench.

It does **not** define a customer-facing product shell. It defines the
operator-facing workspace used for:

- document intake
- chunk and evidence inspection
- candidate review and knowledge calibration
- readiness and apply workflow control
- ontology and coverage visibility

The goal is a tool that is calm, efficient, and trustworthy under daily use.

---

## Product Position

The internal workbench is:

- an operator console for knowledge engineering
- evidence-first and review-first
- optimized for long sessions and high-density inspection work

The internal workbench is **not**:

- a marketing demo site
- a chatbot-first interface
- a dashboard made of decorative cards with shallow actions
- a generic CRUD admin template

The workbench must help a human answer these questions quickly:

1. What document or chunk am I looking at?
2. What ontology class and knowledge object does it map to?
3. What evidence supports it?
4. Is it pending, review-ready, approved, or applied?
5. What should I do next?

---

## Visual Direction

### Target Feel

Use a calm desktop-app feel closer to:

- Apple pro apps
- Linear/Codex-style focused tooling
- evidence and text workbenches rather than BI dashboards

The interface should feel:

- quiet
- precise
- spatially ordered
- confident without being flashy

### Style Keywords

- frosted but restrained
- dense but breathable
- editorial typography
- low-chroma surfaces
- sharp evidence contrast
- minimal ornament

### Explicit Non-Goals

Avoid:

- loud gradients as the main visual identity
- oversized hero banners
- consumer SaaS “metric card farm” layouts
- purple neon / dark cyberpunk defaults
- rounded toy-like controls

---

## Core Design Principles

### 1. Evidence Is The Primary UI Object

Document, page, chunk, and evidence text should be first-class panels, not
secondary metadata hidden behind tabs.

### 2. Review Actions Must Be Local

The user should be able to inspect, compare, edit, accept, reject, and apply
without page-hopping.

### 3. Density Beats Decoration

This is a working tool. Prefer compact clarity over empty whitespace.

### 4. One Primary Action Per Surface

Every page or panel should make the next recommended action obvious:

- import
- review
- mark ready
- apply
- inspect evidence

### 5. Layout Must Preserve Context

When the operator edits a candidate, the evidence and chunk context should stay
visible beside or near the form.

---

## Tone And Interaction Model

The UI language should be:

- operational
- plain
- specific

Prefer labels like:

- `Review Ready`
- `Apply Approved Packs`
- `Open Evidence`
- `Ontology Class`
- `Chunk Candidate`

Avoid vague labels like:

- `Insights`
- `Magic`
- `Smart Results`
- `Optimize`

Interactions should feel:

- immediate
- reversible
- stateful

Use confirmations only for:

- apply actions
- destructive resets
- bulk state transitions

---

## Layout System

### App Shell

The workbench should use a three-zone shell on desktop:

1. Left navigation rail
2. Main working canvas
3. Context or inspector panel

This shell is preferred over full-page route replacement because the user needs
persistent context.

### Recommended Desktop Structure

- Left rail width: `232-256px`
- Main canvas max width: fluid
- Right inspector width: `360-420px`

### Mobile / Narrow Rules

On narrow screens:

- collapse right inspector into a bottom sheet or drawer
- preserve list/detail flow
- never hide evidence entirely

This is still an internal desktop-first tool, but it must remain usable on a
laptop-sized viewport.

---

## Typography

### Font Direction

Prefer:

- `SF Pro Text` / `SF Pro Display` where available
- `PingFang SC` for Chinese
- `Avenir Next` or `Inter Tight` only as fallback, not as brand identity
- `SF Mono` / `Menlo` for ids, evidence excerpts, and structured payloads

### Hierarchy

- Page titles: compact, semibold, 24-30px
- Section titles: 16-18px semibold
- Body: 13-15px
- Dense table/list text: 12-13px
- Metadata labels: 11-12px uppercase or semibold muted

### Text Rules

- Use tabular numerals where counts matter
- Keep line length short in evidence panes
- Use monospace for ids, page numbers, chunk ids, trust levels, and statuses when scanning benefits

---

## Color System

Use a restrained neutral palette with one warm accent and one cool state color.

### Recommended Tokens

- `--bg-root`: soft warm gray
- `--bg-panel`: translucent white or very light neutral
- `--bg-panel-strong`: solid elevated panel
- `--ink-primary`: deep slate
- `--ink-secondary`: muted blue-gray
- `--line-subtle`: low-contrast border
- `--accent-primary`: burnt orange or copper
- `--accent-cool`: deep teal
- `--success`: muted green
- `--warning`: amber
- `--danger`: restrained red

### State Mapping

- `candidate`: amber tint
- `pending`: warm neutral
- `approved`: green tint
- `applied`: teal tint
- `rejected`: muted red tint

Never rely on color alone; every state needs text and icon support.

---

## Surface Rules

### Panel Design

Panels should be:

- lightly elevated
- border-defined
- softly rounded
- visually stackable

Recommended radius:

- shell containers: `20-24px`
- cards/panels: `16-20px`
- controls: `10-14px`

### Shadows

Use soft large-radius shadows with low opacity.

Do not stack heavy shadows on every card.

### Blur And Glass

Glass effects are allowed, but only as a subtle layer treatment.

Rules:

- blur is secondary to contrast
- text contrast must stay high
- blur should never reduce legibility of tables or evidence text

---

## Component Constraints

### Navigation

Left rail should group work by workflow, not by technical subsystem.

Recommended primary nav:

- `Inbox`
- `Documents`
- `Review`
- `Apply`
- `Coverage`
- `Ontology`

### Tables And Lists

Use dense lists for:

- document queues
- candidate packs
- coverage rows

Every row should expose:

- name/title
- equipment class
- knowledge object type
- status
- evidence count or page ref
- next action

### Evidence Pane

Evidence pane must show:

- source doc name
- page number
- chunk id
- excerpt
- evidence text

And should support:

- copy citation
- open source location
- compare chunk vs curated payload

### Review Editor

The review form should show editable fields beside evidence, not below it.

Minimum editable fields:

- title
- summary
- canonical key
- structured payload
- applicability
- trust level
- review decision

### Status Indicators

Statuses should be compact pills, not giant banners.

Every status component must be legible in dense tables.

---

## Workflow Constraints

### Page 1: Document Intake

Must support:

- import one document or batch
- assign domain
- assign equipment class if known
- inspect parse and chunk state

Should emphasize:

- queue health
- import errors
- next processing step

### Page 2: Candidate Review

This is the highest-priority page.

Must support:

- candidate list
- list filters by domain, class, type, status
- evidence and chunk side-by-side
- edit curation fields
- accept / reject / leave pending

Recommended layout:

- center: candidate list + edit form
- right: evidence inspector

### Page 3: Apply And Coverage

Must support:

- readiness summary
- packs ready to apply
- applied history
- coverage inventory by equipment class and knowledge type

This page should answer:

- what is blocked
- what is ready
- where coverage is thin

---

## Information Architecture Rules

Organize by workflow state first:

- intake
- review
- apply

Organize by domain or ontology class second.

Do **not** make the first navigation level purely technical:

- avoid leading with `tables`, `jobs`, `models`, `artifacts`

Operators think in work items, not storage layers.

---

## Good Defaults

### Filters

Persist the user’s last-used filters locally in the session for:

- domain
- equipment class
- review state
- knowledge type

### Sorting

Default sort should favor actionable work:

- review pages: pending first
- apply pages: ready first
- coverage pages: uncovered or thin coverage first

### Empty States

Empty states should always tell the user what to do next.

Good example:

- `No review-ready packs. Open Candidate Review or run bundle preparation.`

Bad example:

- `No data available.`

---

## Accessibility And Usability Constraints

- Minimum interactive target: `36px`
- Keyboard navigation must work for all review actions
- Focus ring must be clearly visible
- Contrast must meet practical desktop accessibility standards
- Do not hide critical actions behind hover-only controls
- Do not require drag-and-drop as the only import mechanism

---

## Performance Constraints

The workbench should feel immediate with medium-size internal datasets.

Rules:

- prefer server-driven pagination for long lists
- virtualize very long candidate lists when needed
- avoid re-rendering large evidence panes unnecessarily
- keep action latency visible with subtle inline progress, not blocking modals

---

## Page-Building Constraints

Before building any page:

1. Define the primary user task.
2. Define the single next action the page should promote.
3. Keep evidence visible if the page edits knowledge.
4. Reuse the same state language across pages.

When in doubt, choose:

- fewer panels
- stronger hierarchy
- better evidence visibility

Instead of:

- more metrics
- more decoration
- more route depth

---

## Initial Implementation Scope

The first implementation should include only:

1. app shell and navigation
2. document intake list/detail
3. candidate review workspace
4. apply and coverage status workspace

Do not start with:

- settings center
- user management
- analytics dashboard
- customer-facing showcase layer

---

## Decision Summary

The internal KnowFabric workbench should be:

- Apple-software calm
- Codex-like focused
- evidence-dense
- operator-oriented
- workflow-first

It should look polished, but its real standard is this:

Can a knowledge engineer import documents, review chunk candidates, calibrate
knowledge objects, and apply reviewed packs without falling back to shell
scripts for the common path?
