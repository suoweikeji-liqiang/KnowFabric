# HVAC Doc-Level Extraction Batch Report

- Run ID: `20260507T200220Z_hvac_doclevel_extraction_batch`
- Output dir: `output/hvac_authority_batch_pipeline/20260507T200220Z_hvac_authority_batch_pipeline/hvac_doclevel_extraction_batch/20260507T200220Z_hvac_doclevel_extraction_batch`

## 【三菱重工】线控器用户使用说明手册（20页）.pdf

- doc_id: `doc_c3b1d28767304e3a`
- equipment: `controller`

| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| deepseek-v4-pro | ok | 10 | 10 | 6 | 100.0 | 60.0 | parameter_spec:1, operational_sequence:4, maintenance_procedure:1 | 36.26 | ¥0.1102 |

## 【天加 】风冷净化空调机组安装操作手册.pdf

- doc_id: `doc_a8258f8764a54269`
- equipment: `chilled_water_pump`

| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| deepseek-v4-pro | ok | 10 | 10 | 10 | 100.0 | 100.0 | parameter_spec:8, fault_code:2 | 63.437 | ¥0.0869 |

## 【约克】风冷冷水机组YCAC，YMAC，YSAC通用控制器使用手册3.0.pdf

- doc_id: `doc_1f7a392bdd7b4e4c`
- equipment: `valve`

| Backend | Status | Raw | Anchored | Final | Anchor rate | Judge rate | Types | Seconds | Cost |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|
| deepseek-v4-pro | ok | 10 | 9 | 9 | 90.0 | 100.0 | fault_code:6, parameter_spec:2, maintenance_procedure:1 | 35.805 | ¥0.0512 |

