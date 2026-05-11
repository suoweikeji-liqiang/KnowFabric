# E4 R3/R4 Verification Report
- Run: `20260511T104337Z`

## Results
- **F1_empty_agree**: {'new_merged': 1, 'updated_existing': 0, 'material_conflicts': 0}
- **F2_temp_convert**: {'error': '(psycopg2.errors.NotNullViolation) null value in column "primary_chunk_id" of relation "knowledge_ob'}
- **F3_pressure_convert**: {'error': '(psycopg2.errors.NotNullViolation) null value in column "primary_chunk_id" of relation "knowledge_ob'}
- **F4_real_conflict**: {'error': '(psycopg2.errors.NotNullViolation) null value in column "primary_chunk_id" of relation "knowledge_ob'}
- **F5_multi_facet**: {'error': '(psycopg2.errors.NotNullViolation) null value in column "primary_chunk_id" of relation "knowledge_ob'}
- **F6_same_value**: {'error': '(psycopg2.errors.NotNullViolation) null value in column "primary_chunk_id" of relation "knowledge_ob'}

## Consensus Distribution
- agreed: 1

## Fixture Expectations vs Actual
| Fixture | Expected | Got | Pass |
|---------|----------|-----|------|
| chilled_water_setpoint | — | agreed | — |

## Summary
- 1 consensus states (need ≥3 incl agreed)
- 1 total KOs
