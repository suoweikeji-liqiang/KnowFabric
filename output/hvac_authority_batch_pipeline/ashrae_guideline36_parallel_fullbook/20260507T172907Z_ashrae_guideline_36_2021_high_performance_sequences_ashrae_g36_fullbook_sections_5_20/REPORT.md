# ASHRAE Guideline 36 Extraction Run Report

**Run ID:** 20260507T172907Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36_fullbook_sections_5_20
**Standard:** ASHRAE Guideline 36-2021
**Document:** ashrae_guideline_36_2021_high_performance_sequences.pdf
**Architecture:** chapter-level section_context extraction + single-call batch judge + verbatim chunk anchoring
**Focus sections:** 5.20
**Extract backend:** deepseek-v4-pro / deepseek-v4-pro
**Judge backend:** deepseek-v4-pro-judge / deepseek-v4-pro

## Token / Cost

| Metric | Value |
|--------|-------|
| Manual chunks | 923 |
| Manual tokens estimated | 73298 |
| Extract calls | 1 |
| Extract input tokens | 74550 |
| Extract output tokens | 32029 |
| Judge calls | 1 |
| Judge total tokens | 9257 |
| Total cost | ¥0.4559 / ¥10.00 |
| Extract wallclock | 897.34s |
| Total wallclock | 1013.71s |

## Extraction Numbers

| Metric | Value |
|--------|-------|
| Raw candidates | 40 |
| Anchor passed | 33 |
| Anchor rejected | 7 |
| Weak evidence rejected before judge | 3 |
| Judge input | 30 |
| Judge accepted | 30 |
| Judge rejected | 0 |
| Judge rejection breakdown | none |
| Final by type | operational_sequence: 23, parameter_spec: 4, fault_diagnostic_rule: 3 |
| L4 / L3 | 6 / 24 |

## Samples

### Accepted
- p172, §5.20.2.2, operational_sequence: Chiller Plant Enable Conditions
- p172, §5.20.2.3, operational_sequence: Chiller Plant Disable Conditions
- p172, §5.20.2.1, parameter_spec: Chiller Plant Enabling Schedule Default
- p175, §5.20.3.1, operational_sequence: Waterside Economizer Enable Conditions
- p176, §5.20.3.2, operational_sequence: Waterside Economizer Disable Conditions
- p176, §5.20.3.5, operational_sequence: WSE In-line CHW Return Valve Modulation
- p176, §5.20.3.9, parameter_spec: WSE HX Pump Speed Reset Trim & Respond Parameters
- p177, §5.20.3.11, operational_sequence: Economizer-Only CHW Bypass Valve Operation
- p181, §5.20.4.15.a, operational_sequence: Minimum Stage Runtime
- p182, §5.20.4.15.g.2, operational_sequence: Stage Up Efficiency Condition for Primary-Only Plants
- p182, §5.20.4.15.g.3.i, operational_sequence: Failsafe Stage Up DP Condition for Parallel Chillers
- p182, §5.20.4.15.g.3.ii, operational_sequence: Failsafe Stage Up CHWST Condition
- p182, §5.20.4.15.h, operational_sequence: Stage Down Condition for Primary-Only Plants
- p183, §5.20.4.15.l, operational_sequence: Stage Down to WSE Only Mode
- p185, §5.20.4.15.n.3.i, operational_sequence: Failsafe Stage Up for Primary-Secondary Based on Secondary Recirculation

### Anchor Rejected
- §5.20.4.14.a.3: SPLR UP for Variable Speed Centrifugal Chillers | evidence_quote not verbatim in any chunk
- §5.20.4.14.b.3: SPLR DN for Variable Speed Centrifugal Chillers | evidence_quote not verbatim in any chunk
- §5.20.4.15.j: Stage Up from WSE Only Mode | evidence_quote not verbatim in any chunk
- §5.20.6.7.a: Primary CHW Pump Staging Based on Flow Ratio | evidence_quote not verbatim in any chunk
- §5.20.7.3.a.1: Secondary CHW Pump Staging Based on Flow Ratio | evidence_quote not verbatim in any chunk
- §5.20.12.2.a.4: Cooling Tower Fan Speed Limit Based on OPLR | evidence_quote not verbatim in any chunk
- §5.20.12.3.a: Cooling Tower Bypass Valve Freeze Protection | evidence_quote not verbatim in any chunk
- §5.20.4.1: Chiller Stage Definition | weak evidence_quote: lacks rule/action signal
- §5.20.15.1: Freeze Protection for Tower Basin Heaters | weak evidence_quote: too short to support structured summary
- §5.20.16.2: Total Plant Power Calculation for Performance Monitoring | weak evidence_quote: lacks rule/action signal

### Judge Rejected
None

## Stability Gates

- G1 anchor_match_rate >= 80%: PASS (82.5%)
- G2 judge_acceptance_rate >= 50%: PASS (100.0%)
- G3 focused section run produced at least one verified candidate: PASS (30)
- G4 extract wallclock <= configured limit: PASS (897.34s / 1200s)

## Operator Review

Review accepted candidates for operational usefulness, section citation accuracy, and sw_base_model mapping readiness.
