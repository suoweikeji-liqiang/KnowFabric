# KnowFabric vNext Direction Note
## From semantic publishing to compile-check-publish

## Purpose

This note clarifies one possible vNext direction for KnowFabric after the current rebuild track.

It does **not** replace the current boundary, architecture, or rebuild plan.
Its purpose is narrower:

1. preserve the current ontology-first direction,
2. identify the most meaningful next capability layer,
3. avoid drifting into a generic RAG tool or a runtime industrial application.

The current repository already defines KnowFabric as an ontology-first domain knowledge authority and publishing engine for industrial equipment knowledge. It owns canonical industrial ontology packages, evidence-grounded knowledge objects, and semantic delivery through REST and MCP, while explicitly not owning project-instance runtime models, control logic, or UI-first product shells. The six-layer evidence discipline remains mandatory, with chunks as the truth source and every semantic response remaining evidence-backed.

This direction note keeps that boundary unchanged.

---

## Current Position

KnowFabric is already on a strong path.

Its core direction is not “document search,” and not “chat over manuals.”
The durable value is stated more precisely in the repository:

- canonical industrial ontology,
- curated equipment knowledge,
- evidence traceability,
- domain-specific delivery contracts.

This is an important distinction.
Document ingestion, chunking, indexing, and extraction are necessary, but they are not the moat.

The current architecture already expresses this clearly:

- KnowFabric owns canonical equipment class identifiers, external mappings, domain relation vocabularies, aliases and terminology normalization, evidence-grounded knowledge objects, and semantic query/publishing interfaces.
- The mandatory evidence pipeline is: `Raw Document -> Page -> Chunk -> Knowledge Object -> Delivery Surface`.
- Knowledge is organized into typed knowledge objects such as `fault_code`, `parameter_spec`, `symptom`, `diagnostic_step`, `maintenance_procedure`, `commissioning_step`, `selection_criterion`, and `performance_spec`.
- Each knowledge object is expected to carry a stable identifier, ontology anchor, source evidence references, trust metadata, and optional brand/model applicability.
- The semantic delivery surface already exposes `/api/v2/` routes for equipment class explanation, fault knowledge, parameter profiles, maintenance guidance, application guidance, and operational guidance, with matching MCP semantics.

This means the project already has meaningful foundations in place.
The question is not whether the current path is wrong.
The question is what capability most naturally comes next.

---

## External Prompt For Reflection

A recent idea discussed by Andrej Karpathy around “LLM Knowledge Bases” is useful here.
The valuable part is not the wiki UI itself.
The deeper idea is that LLM systems can be used to continuously transform raw materials into structured knowledge assets, and then run health checks over the resulting knowledge base to find gaps, inconsistencies, weak links, and missing concepts.

For KnowFabric, the main takeaway is not “build a wiki product.”
The main takeaway is this:

**semantic publishing is not yet the full loop.**

A more complete loop is:

`Raw Sources -> Compile -> Check -> Publish`

KnowFabric already has part of `Compile`, and it already has meaningful `Publish`.
The largest missing piece is making `Compile` and `Check` into first-class product capabilities.

---

## vNext Thesis

KnowFabric vNext should be understood as:

**an ontology-first industrial knowledge compiler, checker, and publisher**

not merely as:

- a semantic API layer,
- a domain-flavored RAG stack,
- a generic document processing system,
- or a runtime industrial copilot.

This is not a major repositioning.
It is a completion of the current direction.

The repository already defines KnowFabric as a knowledge authority and publishing engine.
The next step is to make it equally strong as a **knowledge compilation** and **knowledge health** system.

---

## What "Compile" Means In KnowFabric

“Compile” should mean more than extracting facts from chunks.

In the KnowFabric context, compile should mean transforming raw industrial sources into stable, typed, ontology-anchored knowledge assets that are suitable for long-term semantic delivery.

Raw sources may include:

- manufacturer manuals,
- commissioning guides,
- maintenance procedures,
- fault code references,
- parameter tables,
- standard documents,
- internal engineering notes,
- curated domain references.

Compilation should produce knowledge objects that are not just extracted fragments, but reviewable semantic units attached to canonical ontology anchors.

Examples:

- equipment-class explanations,
- parameter profiles,
- fault-code knowledge bundles,
- symptom-to-diagnostic mappings,
- maintenance procedures,
- selection criteria,
- applicability-scoped recommendations,
- cross-standard mappings.

In practical terms, this moves KnowFabric one step beyond “retrieve knowledge objects” toward “produce high-quality knowledge objects intentionally.”

---

## What "Check" Means In KnowFabric

The strongest missing concept in the current direction is explicit knowledge health.

Evidence-grounded delivery is necessary, but not sufficient.
A system may still be evidence-backed while remaining incomplete, inconsistent, weakly supported, or poorly scoped.

For KnowFabric, “Check” should become a first-class capability that evaluates the health of the curated knowledge layer itself.

### Example health dimensions

#### 1. Conflict detection
Detect when parameter ranges, definitions, or recommended procedures conflict across sources for the same ontology anchor.

#### 2. Coverage gaps
Detect when an equipment class has some knowledge object types but lacks others that should normally exist.
For example, a class may have `fault_code` objects but no linked `diagnostic_step` or `maintenance_procedure`.

#### 3. Weak evidence
Detect knowledge objects that are technically extractable but rely on thin, low-trust, or single-source evidence.

#### 4. Applicability ambiguity
Detect objects whose brand/model applicability is missing, underspecified, or inconsistent with source evidence.

#### 5. Terminology drift
Detect mismatches in aliases, multilingual labels, standard mappings, and normalized domain vocabulary.

#### 6. Anchor quality
Detect objects whose ontology anchor is uncertain, probabilistic, or unstable after review.

These checks fit the existing architecture well because the current design already requires ontology anchors, source evidence references, trust metadata, and optional brand/model applicability.

---

## What "Publish" Continues To Mean

Publish remains essential, but its role becomes clearer in the larger loop.

KnowFabric should continue to publish through semantics-first delivery surfaces such as REST and MCP.
The difference is that these surfaces should increasingly expose knowledge that has been:

1. compiled intentionally,
2. checked for health,
3. and then delivered with preserved traceability.

This makes the publishing layer stronger without changing its core contract.

The existing `/api/v2/` direction remains correct:

- equipment class explanation,
- fault knowledge,
- parameter profiles,
- maintenance guidance,
- application guidance,
- operational guidance.

But over time, consumers should not receive only “matching knowledge.”
They should also be able to receive knowledge state signals such as:

- evidence strength,
- applicability clarity,
- coverage completeness,
- conflict warnings,
- or review status.

This does not require abandoning the current semantic API strategy.
It suggests enriching it carefully.

---

## Boundary Clarification

This vNext direction should **not** expand KnowFabric into downstream runtime ownership.

KnowFabric should still not own:

- site-specific instance models,
- project topology,
- point binding,
- runtime control logic,
- live telemetry reasoning,
- optimization execution,
- operator workflow shells.

Its role remains upstream of runtime systems.

A useful way to describe the boundary is:

**KnowFabric governs industrial knowledge authority, not industrial runtime behavior.**

That distinction should remain strict.

---

## Strategic Value

If this direction is adopted, KnowFabric becomes easier to explain as a product.

Instead of being described mainly as:

- industrial semantic retrieval,
- ontology-backed knowledge API,
- or domain package infrastructure,

it can be described more completely as:

**the system that compiles raw industrial knowledge into canonical, evidence-grounded, health-checked knowledge assets for AI and software consumption.**

That description is stronger for three reasons.

### First
It better matches the existing moat statement in ADR-0003.
The value is not generic ingestion; it is curated ontology, curated knowledge, traceability, and domain-specific delivery.

### Second
It gives KnowFabric a durable upstream role across many downstream products.
Copilots, service tools, training systems, design assistants, maintenance tools, and future industrial agents can all consume the same authority layer.

### Third
It resists the common failure mode of becoming “just another RAG system.”
Compile-check-publish is a harder and more defensible posture than retrieval alone.

---

## Proposed vNext Statement

A concise vNext statement could be:

> KnowFabric is an ontology-first industrial knowledge authority that compiles raw domain sources into evidence-grounded knowledge objects, checks their health and consistency, and publishes them through semantics-first interfaces for AI and software systems.

A shorter internal version could be:

> KnowFabric vNext = Compile / Check / Publish for industrial knowledge.

---

## Recommended Near-Term Implications

This note does not define a full roadmap, but it suggests a clear priority order.

### Priority 1: strengthen compilation
Move from extraction-oriented pipelines toward knowledge-compilation pipelines that explicitly produce stable, typed, ontology-anchored assets.

### Priority 2: introduce knowledge health
Add first-class checks for conflict, coverage, weak evidence, applicability ambiguity, terminology drift, and anchor quality.

### Priority 3: enrich publishing carefully
Keep the current REST/MCP direction, but allow future delivery surfaces to expose health and review signals in addition to semantic knowledge payloads.

---

## Additional Absorption From The "LLM Knowledge Bases" Pattern

The current vNext direction already captures the core external pattern:

`Raw Sources -> Compile -> Check -> Publish`

For KnowFabric, the useful absorption is limited and specific:

- continuous compilation of authority assets from raw sources,
- repeatable health checks over those assets,
- AI-assisted maintenance proposals with human authority review.

This should be treated as an authority-layer enhancement, not as a wiki, portal, collaboration product, or broad knowledge-operations platform.

---

## Compiled Knowledge Asset Forms (Authority Scope)

Compilation should not stop at extraction and normalization. It should produce stable authority assets that improve semantic consistency and traceability.

For KnowFabric, compiled outputs may include four constrained forms:

### 1. Typed knowledge objects
These remain the core semantic units already aligned with the current architecture, for example:

- `fault_code`
- `parameter_spec`
- `symptom`
- `diagnostic_step`
- `maintenance_procedure`
- `commissioning_step`
- `selection_criterion`
- `performance_spec`

These objects remain ontology-anchored, evidence-backed, and suitable for semantic delivery.

### 2. Concept briefs
Canonical concept summaries around one ontology anchor to support curation and review.

Examples:

- equipment class concepts,
- parameter meaning and interpretation,
- common fault families,
- maintenance intent,
- commissioning concepts,
- standard term normalization,
- applicability boundaries.

These are authority artifacts, not end-user wiki pages.

### 3. Relation views
Structured representations that make key domain relations explicit and reviewable.

Examples:

- symptom -> possible fault code -> diagnostic step
- equipment class -> parameter set -> expected operating interpretation
- maintenance procedure -> prerequisite condition -> applicability scope
- canonical term -> aliases -> external standard mappings

These should be machine-readable first, with optional review rendering.

### 4. Knowledge governance artifacts
Artifacts used to govern quality and maintenance, not direct user-facing product surfaces.

Examples:

- coverage reports,
- conflict reports,
- terminology drift reports,
- weak-evidence reports,
- missing-object reports,
- candidate curation tasks,
- candidate cross-link suggestions.

---

## Health Checks As A Maintenance Mechanism

Health checks are not only validation gates. They should also produce structured maintenance work for the authority layer.

For KnowFabric, this means:

### 1. Checks should detect
- conflicting parameter ranges or definitions,
- incomplete knowledge-object coverage,
- uncertain ontology anchors,
- missing applicability scope,
- terminology drift,
- weak or thin evidence.

### 2. Checks should propose
- candidate missing knowledge objects,
- candidate cross-links between existing objects,
- candidate concept briefs that should exist,
- candidate applicability refinements,
- candidate source gaps requiring additional evidence,
- candidate human review tasks.

### 3. Checks should feed authority maintenance
The output of a health check should include both findings and a prioritized maintenance queue.

A practical loop is:

`Compiled Assets -> Health Checks -> Suggested Repairs / Missing Pieces / New Links -> Human Review -> Updated Authority State`

---

## Operating Model (AI-Assisted, Human-Governed)

For KnowFabric, the operating model should be explicit:

**AI performs primary compilation and maintenance assistance; humans perform authority review and final acceptance.**

This avoids two failure modes:

- manual-only maintenance drift (slow and expensive),
- ungoverned auto-truth (low trust and unstable authority).

The intended path is:

- AI drafts or updates authority assets,
- AI proposes links, repairs, and missing pieces,
- AI runs health checks and surfaces issues,
- humans review, accept, reject, revise, or promote authority state.

---

## Practical Interpretation For KnowFabric

KnowFabric should not only compile industrial documents into evidence-grounded knowledge objects for semantic publishing. It should also produce constrained authority assets, run health checks that generate maintenance work, and maintain an explicit AI-assisted, human-governed authority loop.

A more complete shorthand is:

`Raw Sources -> Compile Assets -> Check Health -> Maintain Authority -> Publish`

This is a deepening of the authority layer, not an expansion into downstream knowledge usage products.

---

## Concise Internal Restatement

A concise internal restatement could be:

> KnowFabric is an ontology-first industrial knowledge authority that compiles raw sources into evidence-grounded authority assets, checks their health, maintains them through AI-assisted and human-governed review, and publishes them through semantics-first interfaces.

An even shorter internal shorthand could be:

> Compile assets. Check health. Maintain authority. Publish semantics.

---

## What This Note Is Not Saying

This note is **not** saying that KnowFabric should become:

- a wiki product,
- a UI-first knowledge portal,
- a runtime control engine,
- a site digital twin platform,
- or a generic autonomous agent framework.

It is also **not** saying that the current rebuild direction is incomplete or misguided.

The narrower claim is:

**the current direction is sound, but it becomes substantially stronger when compilation and knowledge health are elevated to first-class concerns.**

---

## Final Position

The current rebuild has already established a meaningful foundation:

- ontology-first authority,
- evidence-grounded knowledge objects,
- semantic API and MCP delivery,
- clear boundary against runtime ownership.

The most rational next step is not to widen the boundary.
It is to deepen the authority layer.

That deepening can be summarized as:

`Compile -> Check -> Publish`

If KnowFabric succeeds here, it will not merely expose industrial knowledge.
It will become a system that is trusted to shape, verify, and deliver industrial knowledge in a durable way.
