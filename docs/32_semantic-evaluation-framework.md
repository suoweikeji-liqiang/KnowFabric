# Semantic Evaluation Framework

**Status:** Direction Note - Rebuild Track
**Last Updated:** 2026-05-07

This note describes how KnowFabric should be evaluated as it moves from
chunk-first retrieval toward ontology-first semantic delivery.

It exists to prevent the project from using a generic "answer looks right"
evaluation loop that is too weak for an evidence-grounded industrial knowledge
authority.

---

## Core Principle

KnowFabric should not be evaluated like a generic chatbot or a plain RAG
system.

The key question is not:

- "Did the final answer look plausible?"

The key questions are:

- Was the query interpreted into the correct semantic target?
- Were the correct knowledge objects retrieved?
- Did the result carry the right evidence?
- Could a downstream consumer use the result safely?

That means the evaluation stack must be layered.

---

## Recommended Evaluation Layers

### 1. Query Parse Evaluation

Purpose:
Measure whether the system can turn user questions into the right structured
semantic intent.

Examples of target fields:

- `domain_id`
- `equipment_class_id`
- `knowledge_type`
- `brand`
- `model_family`
- `fault_code`
- `parameter_category`
- `task_type`

Example gold record:

```json
{
  "query": "约克风冷螺杆机常见报警代码",
  "domain_id": "hvac",
  "equipment_class_id": "air_cooled_screw_chiller",
  "knowledge_type": "fault_code",
  "brand": "York/JCI"
}
```

Suggested metrics:

- equipment-class accuracy
- knowledge-type accuracy
- brand/model extraction accuracy
- code/category extraction accuracy
- Chinese vs English query accuracy
- mixed-language query accuracy

This layer evaluates semantic parsing, not retrieval.

---

### 2. Retrieval Evaluation

Purpose:
Measure whether the system retrieves the right semantic knowledge objects once
the intent is known.

Gold targets can be:

- exact `knowledge_object_id`
- exact `canonical_key`
- accepted gold result sets for one query

Suggested metrics:

- Recall@K
- Precision@K
- MRR
- nDCG

Important failure buckets:

- wrong equipment class
- wrong knowledge-object type
- wrong brand applicability
- near-neighbor semantic confusion

Examples of confusion cases:

- `modular_chiller` vs `centrifugal_chiller`
- `fault_code` vs `maintenance_procedure`
- one OEM family retrieved for another OEM family

For KnowFabric, this layer is more important than answer fluency.

---

### 3. Evidence Evaluation

Purpose:
Measure whether retrieved semantic outputs are truly grounded in the source
corpus.

Every semantic result should be checked for:

- evidence presence
- evidence completeness
- evidence correctness
- evidence support quality

Required evidence fields:

- `doc_id`
- `page_no`
- `chunk_id`
- `evidence_text`

Suggested metrics:

- evidence completeness rate
- evidence correctness rate
- wrong-citation rate
- unsupported-claim rate
- evidence-to-summary support rate

This is the most important difference between KnowFabric and a generic RAG
evaluation setup.

If the answer looks right but the evidence is wrong, the result should fail.

---

### 4. End-to-End Consumer Evaluation

Purpose:
Measure whether a downstream software system or AI agent can actually use the
response safely and effectively.

Representative task families:

- fault lookup
- parameter lookup
- maintenance guidance retrieval
- application guidance retrieval
- authority reference retrieval

The result should be evaluated as a structured delivery artifact, not only as a
free-text answer.

Things to verify:

- correct ontology anchor
- correct knowledge-object type
- trust level present
- evidence present
- applicability filters respected
- uncertainty handled honestly

Suggested metrics:

- task success rate
- evidence-backed answer rate
- hallucination rate
- safe abstention rate

KnowFabric should be rewarded for refusing unsupported claims instead of
guessing.

---

## Recommended Evaluation Datasets

### 1. Semantic Query Set

Purpose:
Measure parse quality plus semantic retrieval quality.

Contents:

- real operator and engineer queries
- gold semantic parse targets
- gold knowledge-object targets

This should include:

- Chinese queries
- English queries
- mixed Chinese/English queries
- short keyword queries
- full natural-language queries

### 2. Authority Validation Set

Purpose:
Measure evidence-grounded semantic delivery against manually validated or
high-confidence authority material.

Contents:

- manually reviewed standard-derived KOs
- manually reviewed OEM-derived KOs
- expected evidence anchors
- trust expectations where appropriate

This dataset should be used heavily for evidence evaluation.

### 3. Confusion Set

Purpose:
Stress-test semantic precision.

Contents:

- near-neighbor equipment classes
- similar OEM product families
- similar document types
- Chinese synonyms and colloquial terms
- cross-brand fault-code confusion cases

This set is critical because many weak retrieval systems look good on easy
queries and collapse on confusion-heavy queries.

---

## Score Composition

The evaluation stack should use a weighted score rather than a single answer
accuracy number.

One reasonable composition is:

```text
Total Score =
  0.25 * Parse Score
  + 0.30 * Retrieval Score
  + 0.30 * Evidence Score
  + 0.15 * End-to-End Task Score
```

The exact weights can change, but the design intent should remain:

- semantic correctness matters
- evidence correctness matters
- final answer style matters less

---

## Role Of LLM-Based Judges

LLM judges can help, but they should not be the primary evaluator.

### Good Uses For LLM Judges

- whether a summary is supported by the cited evidence
- whether a task response is materially useful
- whether an abstention is reasonable

### Bad Uses For LLM Judges

- replacing exact field matching
- replacing KO id matching
- replacing evidence completeness checks
- replacing deterministic filter validation

Recommended policy:

- deterministic checks first
- LLM judges only for semantic support or task-utility gaps
- high-risk cases should still be reviewable by humans

In short:

- the main evaluator should be deterministic
- LLM-as-judge should be a supplement, not the foundation

---

## Current Gap

The repository already has:

- chunk-level traceability
- rebuild-track semantic contracts
- typed knowledge-object direction
- semantic route and MCP surface prototypes

But it does not yet have a full evaluation framework that scores the whole
semantic pipeline in layers.

That gap matters because a system can look strong on chunk recall while still
failing semantic precision, applicability control, or evidence discipline.

---

## Implementation Priority

If an evaluation framework is built, the recommended order is:

1. semantic query gold set
2. deterministic parse and retrieval scoring
3. evidence validation scoring
4. end-to-end task scoring
5. optional LLM-judge augmentation

Do not start with answer-only grading.

The highest-value signal for KnowFabric is not whether the final prose sounds
good. It is whether the system returns the correct semantic object with correct
evidence and safe delivery behavior.
