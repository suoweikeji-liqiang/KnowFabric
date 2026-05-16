# Regroup Failure Trace Notes

## 1) Requested restore point mismatch

Requested file:

- `/tmp/h3_pre_rerun_20260511T.sql`

Actual SQL after restore:

```sql
SELECT COUNT(*)
FROM knowledge_object
WHERE ontology_class_id='centrifugal_chiller'
  AND knowledge_object_type='parameter_spec';
```

Result:

```text
6
```

So this file is not the operator-described 56-KO H3 baseline on this machine.

## 2) Rich pre-regroup probe that still fails

Temp DB restored from:

- `/tmp/m1_pre_regroup_20260511T.sql`

Pre-regroup:

- chiller `parameter_spec` KOs: `114`
- Carrier 19XR KOs: `60`

After regroup:

- total KOs: `4`
- cross-publisher KOs: `1`
- super-KO: `hvac:centrifugal_chiller:parameter:chilled_water_entering_temperature_maximum`
- layers: `111`
- publishers: `{Carrier,McQuay,Trane}`

## 3) Diagnostic artifacts

- latest merger input:
  - `/Users/asteroida/work/KnowFabric/output/diagnostic/20260511T161057Z/merger_input.jsonl`
- prior LLM mega-cluster trace:
  - `/Users/asteroida/work/KnowFabric/output/diagnostic/20260511T142653Z/n3_llm_refinement_trace.jsonl`

## 4) Why this still fails

The original P0 plumbing bug is fixed: source-specific names now survive `existing KO -> merge_with_existing`.

But on the rich persisted backup, regroup still forms an oversized cross-brand cluster before final KO materialization, causing a second failure mode:

- cross-publisher count too low
- total KO count collapses too far
- a 111-layer super-KO appears

This is no longer the same bug as the original oracle failure; it is a separate persisted-regroup over-grouping failure.
