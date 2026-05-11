# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T021632Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_2
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.2
**Extract backend:** deepseek-parameter-spec / deepseek-v4-flash
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 32783 |
| Extract calls | 1 |
| Extract input tokens | 34094 |
| Extract output tokens | 7066 |
| Judge calls | 1 |
| Judge total tokens | 5476 |
| Total cost | ¥0.0761 / ¥10.00 |
| Extract wallclock | 88.70s |
| Total wallclock | 175.09s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 18 |
| Anchor passed | 18 |
| Anchor rejected | 0 |
| Weak evidence rejected before judge | 7 |
| Judge input | 11 |
| Judge accepted | 10 |
| Judge rejected | 1 |
| Judge rejection breakdown | unsupported: 1 |
| Final by type | operational_sequence: 8, fault_diagnostic_rule: 2 |
| L4 / L3 | 2 / 8 |

## Samples

### Accepted
- p60, §5.2.1.3, operational_sequence: CO2 P-Only Loop Disable When Not in Occupied Mode
- p60, §5.2.1.4, operational_sequence: CO2 P-Only Loop Disable When Not in Occupied Mode (Title 24)
- p62, §5.2.1.3, operational_sequence: CO2 DCV for Standard 62.1 - SZVAV AHUs
- p63, §5.2.1.4, operational_sequence: Zone-Des-OA-min Calculation for Title 24
- p64, §5.2.1.4, operational_sequence: CO2 DCV for Title 24 - Cooling-Only, Reheat, Series Fan-Powered, Dual-Duct Terminal Units
- p65, §5.2.1.4, operational_sequence: CO2 DCV for Title 24 - SZVAV AHUs
- p66, §5.2.2.3, fault_diagnostic_rule: CO2 High Concentration Alarm (TAV)
- p66, §5.2.2.3, fault_diagnostic_rule: CO2 Sensor Out of Calibration Alarm (TAV)
- p66, §5.2.2.1, operational_sequence: TAV Mode Initial Open Period with Randomization
- p66, §5.2.2.2, operational_sequence: TAV Mode Override of Active Airflow Setpoint

### Anchor Rejected
- §5.2.1.3: Zone Minimum Outdoor Air Calculation for Standard 62.1 | weak evidence_quote: lacks rule/action signal
- §5.2.1.3: Zone Minimum Airflow Setpoint Vmin Determination for Standard 62.1 | weak evidence_quote: lacks rule/action signal
- §5.2.1.3: CO2 DCV for Standard 62.1 - Cooling-Only, Reheat, Series Fan-Powered, Dual-Duct Terminal Units | weak evidence_quote: lacks rule/action signal
- §5.2.1.3: CO2 DCV for Standard 62.1 - Parallel Fan-Powered Terminal Units | weak evidence_quote: lacks rule/action signal
- §5.2.1.4: Zone Minimum Outdoor Air Calculation for California Title 24 | weak evidence_quote: section heading without supporting rule
- §5.2.1.4: CO2 DCV for Title 24 - Parallel Fan-Powered Terminal Units | weak evidence_quote: section heading without supporting rule
- §5.2.1.3: Zone Air Distribution Effectiveness Determination for Standard 62.1 | weak evidence_quote: lacks rule/action signal

### Judge Rejected
- §5.2.2.1: Time-Averaged Ventilation (TAV) Pulse Width Modulation | unsupported: Summary details (15 min cycle, 1.5 min open period) not in evidence quote; truncated evidence.

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (100.0%)
- G2 judge_acceptance_rate >= 50%: PASS (90.9%)
- G3 focused section run produced at least one verified candidate: PASS (10)
- G4 extract wallclock <= configured limit: PASS (88.70s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
