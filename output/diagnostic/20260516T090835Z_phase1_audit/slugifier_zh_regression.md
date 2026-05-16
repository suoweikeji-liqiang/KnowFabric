# Slugifier Chinese Regression

Scope: read-only function check using `packages.compiler.llm_compiler._slugify_part`; fallback condition inferred from current `_safe_slug_for_name`: empty slug, `len(slug) <= 2`, or all-numeric slug triggers `_hashed_slug`.

| input | current KO example | _slugify_part output | intermediate_len | fallback_triggered | trigger_condition | fallback_slug | current canonical_key sample |
|---|---|---:|---:|---|---|---|---|
| 启动电流 | ko_ffb7cc1b38ae8467 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_9fc1319bb1` | `hvac:centrifugal_chiller:performance_spec:key_9fc1319bb1_key_9fc1319bb1_12` |
| 制冷剂 | ko_40e8b515811dcc91 / screw_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_b45c97cb55` | `hvac:screw_chiller:parameter:key_b45c97cb55` |
| 油加热器预热时间 | ko_57d50f6bff6caef9 / chiller | `` | 0 | yes | empty_after_ascii_regex | `key_d4a11fbe9e` | `hvac:screw_chiller:maintenance:key_d4a11fbe9e` |
| 排气压力 | ko_13be08b257cfe5ef / screw_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_6428129801` | `hvac:screw_chiller:performance_spec:key_6428129801` |
| 重启抑制时间设定值 | ko_007c216c7e472be1 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_42f5d7a8ec` | `hvac:centrifugal_chiller:parameter:key_42f5d7a8ec` |
| 全自动启动顺序 | ko_3e1ce17681480ad5 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_deeba31c9b` | `hvac:centrifugal_chiller:operational_sequence:key_deeba31c9b` |
| 排水管接口尺寸 | ko_3fde94ba89d7abd8 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_c001032cf6` | `hvac:centrifugal_chiller:performance_spec:key_c001032cf6` |
| 能量调节范围 | ko_6ba078de2eed310a / screw_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_2b0d5b413b` | `hvac:centrifugal_chiller:parameter:key_2b0d5b413b` |
| 性能系数 | ko_1f9b372a3dbd1077 / screw_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_47246f135c` | `hvac:centrifugal_chiller:performance_spec:key_47246f135c` |
| 油压差报警/保护 | ko_04dc5b2658675b79 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_9594a80439` | `hvac:centrifugal_chiller:fault_code:key_9594a80439` |
| 推力轴承—油温传感器 | ko_02e2749573080a28 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_90cab05c63` | `hvac:centrifugal_chiller:fault_code:key_90cab05c63` |
| 节能评价值 | ko_f7701189ae98bcf8 / chiller | `` | 0 | yes | empty_after_ascii_regex | `key_9800764812` | `hvac:chiller:parameter:key_9800764812` |
| 冷却水流量允许偏差 | ko_3ad19ef39ff1a796 / chiller | `` | 0 | yes | empty_after_ascii_regex | `key_f7391e3d9e` | `hvac:chiller:parameter:key_f7391e3d9e` |
| 制冷排气过热度 | ko_c8e9839f653924f2 / water_source_heat_pump | `` | 0 | yes | empty_after_ascii_regex | `key_15c949229f` | `hvac:water_source_heat_pump:parameter:key_15c949229f` |
| 制冷时排气温度 | ko_68c45a855ceee05f / water_source_heat_pump | `` | 0 | yes | empty_after_ascii_regex | `key_8624deaec0` | `hvac:water_source_heat_pump:parameter:key_8624deaec0` |
| 总硬度 | ko_142b8b8d0123ddfc / water_source_heat_pump | `` | 0 | yes | empty_after_ascii_regex | `key_853301449b` | `hvac:water_source_heat_pump:parameter:key_853301449b` |
| 最大运行电流 | ko_aba917f97a8d4514 / water_source_heat_pump | `` | 0 | yes | empty_after_ascii_regex | `key_ba368123f9` | `hvac:water_source_heat_pump:parameter:key_ba368123f9` |
| 水质全硬度 | ko_236411e7a56b9555 / water_source_heat_pump | `` | 0 | yes | empty_after_ascii_regex | `key_470f4cbe06` | `hvac:water_source_heat_pump:parameter:key_470f4cbe06` |
| 盘管进出水管径 | ko_fa397b4dbdd7507b / ahu | `` | 0 | yes | empty_after_ascii_regex | `key_6ea83846e7` | `hvac:ahu:parameter:key_6ea83846e7` |
| 断电恢复后油泵接通周期 | ko_4578fd43574d9b18 / centrifugal_chiller | `` | 0 | yes | empty_after_ascii_regex | `key_eaa7ec3e34` | `hvac:centrifugal_chiller:parameter:key_eaa7ec3e34` |

## Summary

- Cases tested: 20
- Fallback-triggered: 20/20 (100%)
- Verdict: needs_fix

## Conclusion

The current `_slugify_part` keeps only `[a-zA-Z0-9]`; pure Chinese names collapse to an empty string and then hash. This is systematic, not a corner case. It preserves uniqueness but destroys human-readable canonical key semantics for Chinese technical concepts.