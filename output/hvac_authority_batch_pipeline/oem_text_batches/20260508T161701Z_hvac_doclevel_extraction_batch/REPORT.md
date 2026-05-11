# HVAC Doc-Level Extraction Batch Report

- Run ID: `20260508T161701Z_hvac_doclevel_extraction_batch`
- Output dir: `/Users/asteroida/work/KnowFabric/output/hvac_authority_batch_pipeline/oem_text_batches/20260508T161701Z_hvac_doclevel_extraction_batch`

## 【美的】风冷热泵模块机组技术手册 （C、G、H系列）148页-制冷百家网.pdf

- doc_id: `doc_92fe1e6200fe4f4d`
- equipment: `centrifugal_chiller`

| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| deepseek-v4-pro | failed | - | - | - | - | - | - | - | ¥0.0000 |

## 【格力】风管机技术服务手册（160页）.pdf

- doc_id: `doc_d4d32488171c4acd`
- equipment: `centrifugal_chiller`

| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| deepseek-v4-pro | ok | 40 | 40 | 14 | 100.0 | 35.0 | fault_code:12, parameter_spec:2 | 164.367 | ¥0.1917 |

## 【麦克维尔】螺杆冷水机组维修保养手册-制冷百家网.pdf

- doc_id: `doc_0c7b3998a63c499c`
- equipment: `screw_chiller`

| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| deepseek-v4-pro | ok | 41 | 41 | 19 | 100.0 | 46.3 | parameter_spec:6, performance_spec:5, maintenance_procedure:1, operational_sequence:3, fault_diagnostic_rule:4 | 196.527 | ¥0.0630 |

