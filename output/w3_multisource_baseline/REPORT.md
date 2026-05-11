# W3 D5 Multi-Source Regression Report (Re-run 2026-05-11)

**Status**: PARTIAL — infrastructure verified, 3 material_conflict KOs produced

## Pipeline

1. Loaded 38 centrifugal_chiller parameter_spec KOs (Trane CVGF + McQuay)
2. `group_and_normalize` via MiMo mimo-v2-omni → 33 concept groups, 4 with ≥2 names
3. `merge_candidates` → 34 merged KOs  
4. DB upsert: 8 KOs updated, 26 new (64 total)

## Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| multi-source rate (≥2 layers) | ≥20% | 4.7% (3/64) | BELOW |
| partial_conflict | ≥3 | 0 | BELOW |
| material_conflict | ≥1 | **3** | MET |
| agreed | ≥5 | 0 | BELOW |

## Multi-Layer KOs

| KO | Layers | Consensus | Publishers |
|----|--------|-----------|------------|
| chilled_water_setpoint | 2 | material_conflict | Trane, Trane |
| current_limit_setpoint | 3 | material_conflict | Trane, Trane, Trane |
| safety_valve_pressure_setting | 2 | material_conflict | McQuay, McQuay |

## Root Cause

All multi-layer KOs are same-publisher variants. No cross-brand merge occurred because:
1. MiMo prompt merges "Front Panel X" + "External X" (known issue)
2. Only 2 real brands in corpus (Trane + McQuay), most parameters don't overlap
3. Need more brands extracted (York, Carrier, Daikin) for true cross-source merging

## What Works

- `group_and_normalize` pipeline ✓
- `merge_candidates` consensus_state computation ✓  
- DB authority_summary_json + consensus_state fields ✓
- Terminology YAML correctly separates cross-lingual pairs ✓
