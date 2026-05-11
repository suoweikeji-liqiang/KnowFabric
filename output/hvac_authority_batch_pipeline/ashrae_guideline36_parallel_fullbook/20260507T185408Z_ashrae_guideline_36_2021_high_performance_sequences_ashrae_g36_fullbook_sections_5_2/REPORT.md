# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T185408Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_2
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.2
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 32783 |
| Extract calls | 1 |
| Extract input tokens | 34130 |
| Extract output tokens | 22304 |
| Judge calls | 1 |
| Judge total tokens | 9095 |
| Total cost | ¥0.2765 / ¥10.00 |
| Extract wallclock | 523.20s |
| Total wallclock | 646.10s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 30 |
| Anchor passed | 30 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 2 |
| Judge input | 28 |
| Judge accepted | 27 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | operational_sequence: 25, fault_diagnostic_rule: 2 |
| L4 / L3 | 4 / 23 |

## Samples

### Accepted
- p59, §5.2.1.3, operational_sequence: Automatic Zone Minimum Airflow Vmin Calculation (62.1)
- p59, §5.2.1.3, operational_sequence: Normal Breathing Zone Outdoor Airflow Components
- p59, §5.2.1.3, operational_sequence: Zone Air Distribution Effectiveness Based on DAT
- p60, §5.2.1.3, operational_sequence: CO2 DCV Reset for Standard VAV and Dual-Duct Terminals (62.1)
- p60, §5.2.1.3, operational_sequence: Occupied Minimum Airflow Initialization
- p60, §5.2.1.3, operational_sequence: P-Only CO2 Control Loop (62.1)
- p60, §5.2.1.3, operational_sequence: Ventilation Reduction: Unpopulated without Occupied-Standby
- p60, §5.2.1.3, operational_sequence: Ventilation Zero Override: Unoccupied or Window Open
- p60, §5.2.1.3, operational_sequence: Ventilation Zero Override: Unpopulated with Occupied-Standby Permitted
- p60, §5.2.1.3, operational_sequence: Zone Outdoor Airflow Voz Calculation
- p62, §5.2.1.3, operational_sequence: CO2 DCV Reset for SZVAV AHUs (62.1)
- p63, §5.2.1.4, operational_sequence: Automatic Zone Minimum Airflow Vmin Calculation (Title 24)
- p63, §5.2.1.4, operational_sequence: Occupied Minimum Airflow Initialization (Title 24)
- p63, §5.2.1.4, operational_sequence: Vmin* Zero Override: Unpopulated with Occupied-Standby (Title 24)
- p63, §5.2.1.4, operational_sequence: Vmin* Zero Override: Window Open (Title 24)

### Anchor Rejected
- §5.2.1.4: Zone Absolute Minimum Outdoor Air Reset Priorities (Title 24) | weak evidence_quote: section heading without supporting rule
- §5.2.1.4: CO2 DCV Reset for Parallel Fan-Powered Terminals (Title 24) | weak evidence_quote: section heading without supporting rule

### Judge Rejected
- §5.2.1.3: CO2 DCV Reset for Parallel Fan-Powered Terminals (62.1) | unsupported: Evidence quote is generic and does not support the summarized operational sequence for parallel fan-powered terminals.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (96.4%)
- G3 focused section run produced at least one verified candidate: PASS (27)
- G4 extract wallclock <= configured limit: PASS (523.20s / 1800s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
