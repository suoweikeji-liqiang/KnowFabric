# AI-Assisted Compilation Pilot Milestone

**Status:** Milestone Definition and Current Completion Snapshot
**Last Updated:** 2026-04-10

This milestone defines the minimum bar for treating AI-assisted compilation as
an operationally usable enhancement inside KnowFabric, without changing the
product boundary into a wiki, chat product, or generic knowledge base shell.

It is intentionally narrower than full vNext. The goal is to make the
`Compile -> Check -> Review -> Publish` loop usable for targeted knowledge
types under explicit guardrails.

---

## Milestone Name

**AI-Assisted Compilation Pilot: Operationally Usable**

---

## Problem

KnowFabric already has:

- ontology-first package structure
- chunk-backed evidence discipline
- review/apply workflow
- semantic REST and MCP delivery

What it lacked before this milestone was an operationally usable way to:

1. run LLM-assisted compilation on top of the existing review pipeline,
2. compare remote and local OpenAI-compatible backends,
3. surface compiler provenance and health findings to reviewers,
4. keep higher-risk knowledge types gated instead of allowing unconstrained LLM over-generation.

---

## Scope

This milestone is specifically about improving the authority-layer compilation
workflow for a constrained set of knowledge types.

### In scope

- OpenAI-compatible compiler backend support
- backend comparison between remote and local models
- LLM-assisted candidate generation for:
  - `maintenance_procedure`
  - `application_guidance`
- compiler provenance on candidates and published semantic objects
- lightweight health findings in prepared review bundles
- admin/workbench support for selecting compiler backend in review-bundle preparation
- reviewer visibility into compile metadata and health findings

### Out of scope

- markdown/wiki pages as source of truth
- autonomous publishing without review
- replacing rule extraction for:
  - `fault_code`
  - `parameter_spec`
  - `performance_spec`
- full vNext knowledge-health coverage
- runtime/site modeling
- downstream operator/copilot UX

---

## Product Boundary

This milestone does **not** change the product boundary.

KnowFabric remains:

- ontology-first
- evidence-grounded
- review-governed
- semantics-first in delivery

LLM output remains:

- candidate-only before review
- subject to traceability constraints
- subject to type/context gating
- non-authoritative until accepted and backfilled

---

## Acceptance Criteria

The milestone is considered reached when all of the following are true.

### 1. Compiler integration

- `prepare_review_pipeline_bundle.py` can run with a named OpenAI-compatible backend
- the rule baseline still works when LLM is disabled
- LLM compilation can be restricted to named knowledge types

### 2. Provenance

- generated candidates include compiler provenance
- accepted reviewed entries preserve provenance into semantic objects
- semantic read surfaces can expose:
  - `compilation_method`
  - `compiler_version`
  - `health_flags`

### 3. Health visibility

- prepared review bundles emit a machine-readable health report
- candidate-level or bundle-level health findings can be surfaced to reviewers

### 4. Operational visibility

- the admin/workbench prepare flow can forward compiler backend options
- review-center candidate details can show compiler metadata and health findings

### 5. Pilot quality bar

- `maintenance_procedure` shows real LLM uplift over the rule baseline on a
  real sample
- `application_guidance` is usable only after tighter context gating prevents
  obvious over-generation from spec-like chunks
- at least one remote backend and one local backend can be compared on the same
  scope

---

## Current Snapshot

At the time of this document update, the milestone is effectively reached in
pilot form.

Implemented:

- compiler package extraction from the monolithic candidate script
- optional OpenAI-compatible LLM compiler path
- backend comparison workflow for remote vs local models
- provenance and health metadata propagation
- admin prepare flow support for backend/type selection
- review-center visibility for compiler metadata and health findings
- compare-summary Markdown generation

Observed pilot outcomes:

- `maintenance_procedure` shows consistent uplift from LLM-assisted compilation
- `application_guidance` initially over-generated, then became usable after
  tighter context gating
- remote DeepSeek remains the stronger primary compiler backend
- upgraded local Gemma is viable as a local comparison backend

---

## Recommended Default Operating Mode

For the current pilot:

- use `DeepSeek` as the primary LLM compiler backend
- use local `Gemma` as a comparison or fallback exploration backend
- enable LLM compilation by default only for:
  - `maintenance_procedure`
  - `application_guidance`
- keep rule-first handling for:
  - `fault_code`
  - `parameter_spec`
  - `performance_spec`

---

## Exit Condition For The Next Milestone

The next milestone should begin only after this pilot is treated as stable
enough for repeated operator use.

That next milestone should focus on one of:

1. stronger UI operationalization of compiler selection and review diagnostics
2. broader health-check coverage and maintenance-queue generation
3. broader type expansion beyond the two pilot knowledge types

The current milestone should not be widened into “AI compiles everything” until
the type boundaries remain controllable under review.
