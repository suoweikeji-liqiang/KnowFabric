# Semantic Retrieval Direction

**Status:** Direction Note - Rebuild Track
**Last Updated:** 2026-05-07

This note captures the intended retrieval model for KnowFabric during the
ontology-first rebuild.

It exists to prevent the project from drifting into a generic "vector search
plus prompt" architecture that loses product identity, traceability, and
semantic control.

---

## Short Answer

KnowFabric should not behave like a generic RAG system whose main retrieval
primitive is:

`query -> embedding similarity -> nearest chunks`

That approach is acceptable as a fallback recall mechanism, but it is not the
target retrieval architecture for this product.

KnowFabric should move toward:

`query -> semantic parse -> ontology / knowledge-object candidate retrieval -> evidence trace-back`

In that model, text similarity remains useful, but it is not the main control
surface.

---

## Why Generic RAG Is Not Enough

Generic RAG is optimized for:

- broad unstructured corpora
- "find similar text" behavior
- answer synthesis from chunk recall

KnowFabric has a different product requirement:

- evidence-grounded industrial knowledge
- stable ontology identifiers
- typed knowledge objects
- explicit applicability and trust metadata
- delivery through semantic APIs and MCP tools

If KnowFabric relies mainly on chunk similarity, the downstream consumer still
has to reconstruct meaning from text fragments. That is exactly the product gap
the rebuild is trying to close.

---

## Target Retrieval Principle

The retrieval target is not "the most similar chunk".

The retrieval target is:

- the right ontology anchor
- the right knowledge-object type
- the right applicability scope
- the right evidence chain

That means retrieval should be organized around semantic objects first, with
chunk-level search acting as a supporting layer.

---

## Recommended Retrieval Stack

### 1. Semantic Query Parsing

Incoming queries should be interpreted into structured constraints where
possible.

Examples:

- equipment class: `centrifugal_chiller`
- knowledge type: `fault_code`, `parameter_spec`, `maintenance_procedure`
- brand or OEM applicability
- code or parameter key
- task or symptom category

This is the first major difference from a plain RAG system.

The system should not start by asking "which chunks look similar?".
It should start by asking "what semantic object is the user actually asking
for?".

### 2. Ontology / Knowledge-Object Candidate Retrieval

Once the query is constrained, the system should retrieve from semantic storage
first:

- ontology classes
- aliases and mappings
- knowledge objects
- applicability metadata
- trust and review state

This is the primary retrieval layer for the rebuild track.

### 3. Evidence Trace-Back

Every semantic result must trace back to:

- source document
- source page
- source chunk
- evidence text

This keeps the six-layer evidence pipeline intact:

`Raw Document -> Page -> Chunk -> Knowledge Object -> Delivery Surface`

Semantic delivery does not replace evidence. It organizes access to evidence.

### 4. Similarity Retrieval as Recall / Fallback

Chunk retrieval remains useful when:

- no suitable knowledge object exists yet
- the query is vague or broad
- recall and coverage-gap discovery matter more than precision
- an operator needs corpus exploration rather than semantic delivery

In those cases, BM25, vector search, or hybrid search are appropriate.

But they should be treated as recall helpers, not the product's main semantic
contract.

---

## Suggested Ranking Logic

The long-term ranking model should combine multiple signals, not just one
similarity score.

Conceptually:

```text
score =
  semantic_match
  + ontology_match
  + knowledge_type_match
  + applicability_match
  + trust_score
  + evidence_quality
  + text_similarity(optional)
```

The exact formula can change, but the architectural intent is stable:

- semantic constraints are primary
- evidence quality matters
- text similarity is supportive, not dominant

---

## Knowledge-Graph-Style Model Without Graph Storage

KnowFabric does not need a graph database in order to use a knowledge-graph-like
data model.

The model can still be implemented in PostgreSQL as long as it preserves these
core entities:

- `ontology_class`
- `ontology_alias`
- `ontology_mapping`
- `content_chunk`
- `chunk_anchor`
- `knowledge_object`
- `knowledge_object_evidence`
- `knowledge_relation`

The critical point is not the storage engine.
The critical point is that retrieval is driven by semantic entities and their
relations rather than by chunk similarity alone.

---

## Current State vs Target State

### Current State

The repository is currently in an intermediate state:

- evidence pipeline is real and mandatory
- chunk-level retrieval and traceability are present
- structured extraction and equipment matching exist in partial form
- rebuild contracts define ontology-first semantic delivery as the target

But the project does not yet have a fully unified semantic retrieval layer whose
primary retrieval unit is the knowledge object.

### Target State

The rebuild should move the system toward:

- ontology-anchored chunk indexing
- typed knowledge-object persistence
- semantic query parsing
- semantic result ranking
- evidence-backed semantic APIs and MCP tools

At that point, similarity search becomes a supporting subsystem rather than the
product definition.

---

## Design Rules

1. Do not treat vector similarity as the main product contract.
2. Do not treat graph-shaped semantics as a reason to skip the evidence chain.
3. Do not return semantic answers that cannot trace back to chunk-level evidence.
4. Prefer semantic object retrieval over raw chunk retrieval where the required
   structure already exists.
5. Use similarity search to expand recall, discover gaps, and support fallback
   search, not to define semantic truth.

---

## Practical Implication for Implementation

Near-term implementation should prioritize:

1. ontology identifiers
2. alias and mapping normalization
3. chunk anchors
4. typed knowledge-object storage
5. semantic API and MCP query contracts

Only after those become stable should the team worry about whether a dedicated
graph store would materially improve query performance or relation traversal.

For now, the key risk is not "missing graph storage".
The key risk is staying trapped in chunk-first retrieval and never graduating to
semantic knowledge delivery.
