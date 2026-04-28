# parameter_spec Vertical Run Report

**Run ID:** 20260428T151542Z_trane_cvgf_parameter_spec
**Date:** 2026-04-28
**Manual:** trane_cvgf_400_1000_chiller_manual.pdf (64 pages, 84 chunks)
**Source PDF:** /Volumes/TSD302/pan/a00238/05、特灵中央空调/特灵/【特灵】CVGF 400-1000离心机操作维护手册（64页）-制冷百家网.pdf
**Equipment class:** brick:centrifugal_chiller
**LLM backend:** deepseek-parameter-spec / deepseek-v4-flash
**ontology_version:** 0.2.0

## Token / Cost

| Metric | Value |
|--------|-------|
| Total prompt tokens | 15082 |
| Total completion tokens | 5687 |
| Total tokens | 20769 |
| Estimated cost | ¥0.0270 |
| Budget cap | ¥50.00 |
| Status | within |

## LLM-side numbers

| Metric | Value |
|--------|-------|
| Chunks scanned | 84 |
| LLM calls made | 8 |
| Candidates generated (raw) | 12 |
| Passed verbatim verification | 9 (75.0%) |
| L4 / L3 / L2 / L1 breakdown | 0 / 7 / 2 / 0 |

## Rule-baseline numbers

| Metric | Value |
|--------|-------|
| Candidates generated | 0 |

## Overlap

| Set | Count |
|-----|-------|
| LLM ∩ Rule (same parameter_name) | 0 |
| LLM only (not found by rule) | 9 |
| Rule only (not found by LLM) | 0 |

## Sample LLM-only finds (top 10)

- p18, chunk_65ed7e9e29664680: parameter_name=数据采集速度; value=每秒三次; unit=次/秒; description=智能传感器每秒可以采集三次数据，是上代产品数据采集速度的55倍。
- p18, chunk_65ed7e9e29664680: parameter_name=比较间隔; value=每五秒钟; unit=秒; description=每五秒钟，多对象算法都会对每个参数和它的设定极限值进行一次比较。
- p25, chunk_b65fbe91567446ea: parameter_name=Active Chilled Water Setpoint; value=44.0F; unit=F
- p25, chunk_b65fbe91567446ea: parameter_name=Active Current Limit Setpoint; value=100%; unit=% RLA
- p25, chunk_b65fbe91567446ea: parameter_name=Chilled Water Reset; value=Return/Constant Return/Outdoor/None
- p34, chunk_5aff234add1441d6: parameter_name=Time Setpoint Adjustment Method; value=arrows; description=User selects hour and minute, then uses up/down arrows to adjust. When adjusting hour, am/pm can also be adjusted.
- p45, chunk_e4668bc89eb04c2e: parameter_name=External Chilled Water Setpoint (ECWS); description=外部冷冻水设定可对冷冻水的设定在远程进行修改。建立在1A16 J2-2至J2-6(接地)的输入基础上。2-10 VDC和4-20 mA对应于34至65°F (-36.7 to 18.3°C)的CWS范围。缺省的34°F至65°F可通过维护工具调节。
- p45, chunk_e4668bc89eb04c2e: parameter_name=External Current Limit Setpoint; description=外部电流限制选项运行远程调整电流限制设定值。位于1A16 J2-5到J2-6(接地)，2-10V直流电压和4-20 mA电流对应于40-120% RLA。CH530限制最大ECLS为100%。
- p45, chunk_8313dd032701485a: parameter_name=External Current Limit Setpoint; description=External current limit option allows remote adjustment of current limit setpoint. Input at 1A16 J2-5 to J2-6 (ground), 2-10 VDC and 4-20 mA correspond to 40-120% RLA. CH530 limits maximum ECLS to 100%.

## Sample Rule-only finds (top 10)

None

## Sample LLM rejections with reason (top 5)

- p18, chunk_65ed7e9e29664680: no evidence_text or structured field is verbatim in source chunk | hvac:centrifugal_chiller:tracer_ch530:parameter_evaporator_water_flow_adjustment
- p34, chunk_5aff234add1441d6: no evidence_text or structured field is verbatim in source chunk | hvac:centrifugal_chiller:ucp:time_setpoint_screen_format
- p45, chunk_8313dd032701485a: no evidence_text or structured field is verbatim in source chunk | hvac:centrifugal_chiller:parameter:external_chilled_water_setpoint

## Operator-facing accuracy assessment

Pending operator review — sample 20 random L3+ candidates and mark accurate / inaccurate.

## Notes

- Ground truth file: none.
- Raw LLM responses are stored in `raw_llm_responses.jsonl` with provider `usage` payloads when returned.
- Cost uses `prompt_price_rmb_per_1k=0.001022` and `completion_price_rmb_per_1k=0.002044` from `scripts/llm_backends.json`.
