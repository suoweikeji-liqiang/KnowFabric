# ASHRAE G36 Evidence Quality Audit

- Generated: `2026-05-07T08:13:51.595751+00:00`
- Rows audited: 699
- Weak rows: 21 (3.0%)
- By reason: weak evidence_quote: lacks rule/action signal: 6, weak evidence_quote: section heading without supporting rule: 15
- By type: commissioning_step: 6, fault_diagnostic_rule: 5, operational_sequence: 10
- By equipment: ahu: 21

## Findings

### 1. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_10_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.10.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p94: 5.10.7.  Testing/Commissioning Overrides . Provide software switches that interlock to a system level point to

### 2. Dual-Duct VAV Terminal Unit Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_12_7:dual_duct_vav_terminal_unit_testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.12.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p102: 5.12.7.  Testing/Commissioning Overrides . Provide software switches that interlock to a system level point to

### 3. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_13_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.13.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p106: 5.13.7.  Testing/Commissioning Overrides.  Provide software switches that interlock to a system level point to

### 4. Dual-Duct VAV Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_14_7:dual_duct_vav_testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.14.7 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p109: 5.14.7.  Testing/Commissioning Overrides .

### 5. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_7_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.7.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p82: 5.7.7.  Testing/Commissioning Overrides . Provide software switches that interlock to a system level point to

### 6. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_8_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.8.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p86: 5.8.7.  Testing/Commissioning Overrides . Provide software switches that interlock to a system level point to

### 7. AFDD Fault Condition FC#6: OA Fraction Error

- Key: `ashrae:g36:fault_diagnostic_rule:5_16_14_8:afdd_fault_condition_fc_6_oa_fraction_error`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.16.14.8 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p137: nevertheless occur if so determined by the fault condition tests in Section 5.16.14.8 .

### 8. AFDD Fault Condition FC#7: SAT Too Low in Full Heating

- Key: `ashrae:g36:fault_diagnostic_rule:5_16_14_8:afdd_fault_condition_fc_7_sat_too_low_in_full_heating`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.16.14.8 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p137: nevertheless occur if so determined by the fault condition tests in Section 5.16.14.8 .

### 9. Single-Zone VAV AHU AFDD Fault Conditions

- Key: `ashrae:g36:fault_diagnostic_rule:5_18_13:single_zone_vav_ahu_afdd_fault_conditions`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.18.13 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p149: AFDD routines for cooling ducts are listed in Sections 5.16.14  and 5.18.13 .

### 10. SZVAV AHU AFDD Fault Conditions

- Key: `ashrae:g36:fault_diagnostic_rule:5_18_13_6:szvav_ahu_afdd_fault_conditions`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.18.13.6 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p162: if so determined by the fault condition tests in Section 5.18.13.6 .

### 11. Fan Coil Unit AFDD Fault Conditions

- Key: `ashrae:g36:fault_diagnostic_rule:5_22_6:fan_coil_unit_afdd_fault_conditions`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.22.6 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p264: 5.22.6.  Automatic Fault Detection and Diagnostics

### 12. Dual-Duct VAV Zone Endpoints as Function of Zone Group Mode

- Key: `ashrae:g36:operational_sequence:5_14_4:dual_duct_vav_zone_endpoints_as_function_of_zone_group_mode`
- Scope: `ahu` / `operational_sequence` / §5.14.4 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p108: Table 5.14.4 Endpoints as a Function of Zone Group Mode

### 13. Supply Air Temperature Setpoint for Cooldown, Warmup, Setback

- Key: `ashrae:g36:operational_sequence:5_16_2_2:supply_air_temperature_setpoint_for_cooldown_warmup_setback`
- Scope: `ahu` / `operational_sequence` / §5.16.2.2 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p112: 5.16.2.2. Supply Air Temperature Setpoint

### 14. Single-Zone VAV AHU Supply Fan Speed and SAT Setpoint Reset

- Key: `ashrae:g36:operational_sequence:5_18_4:single_zone_vav_ahu_supply_fan_speed_and_sat_setpoint_reset`
- Scope: `ahu` / `operational_sequence` / §5.18.4 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p152: 5.18.4. Supply Fan Speed Control and  Supply Air Temperature Set -Point Reset

### 15. Single-Zone VAV AHU Supply Air Temperature Control

- Key: `ashrae:g36:operational_sequence:5_18_5:single_zone_vav_ahu_supply_air_temperature_control`
- Scope: `ahu` / `operational_sequence` / §5.18.5 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p156: 154 ASHRAE Guideline 36 -2021  5.18.5.  Supply Air Temperature Control

### 16. Zone Minimum Outdoor Air and Minimum Airflow Setpoints (ASHRAE 62.1)

- Key: `ashrae:g36:operational_sequence:5_2_1_3:zone_minimum_outdoor_air_and_minimum_airflow_setpoints_ashrae_62_1`
- Scope: `ahu` / `operational_sequence` / §5.2.1.3 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p54: condition per Sections 5.20.4.13  and 5.21.3.8 .

### 17. Time-Averaged Ventilation (TAV) for Zones

- Key: `ashrae:g36:operational_sequence:5_2_2:time_averaged_ventilation_tav_for_zones`
- Scope: `ahu` / `operational_sequence` / §5.2.2 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p66: 64 ASHRAE Guideline 36 -2021  5.2.2.  Time -Averaged Ventilation

### 18. Zone State Heating - Discharge Temperature Reset

- Key: `ashrae:g36:operational_sequence:5_7_5_3:zone_state_heating_discharge_temperature_reset`
- Scope: `ahu` / `operational_sequence` / §5.7.5.3 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p81: 5.7.5.3.  When Zone State  Is Heating

### 19. Fan Control Logic for Parallel Fan-Powered Terminal Unit

- Key: `ashrae:g36:operational_sequence:5_7_5_5:fan_control_logic_for_parallel_fan_powered_terminal_unit`
- Scope: `ahu` / `operational_sequence` / §5.7.5.5 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p81: 5.7.5.5.  Fan Control

### 20. Heating Mode Sequence for Parallel Fan-Powered Terminal Unit

- Key: `ashrae:g36:operational_sequence:5_8_5_3:heating_mode_sequence_for_parallel_fan_powered_terminal_unit`
- Scope: `ahu` / `operational_sequence` / §5.8.5.3 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p85: 5.8.5.3.  When Zone State  is Heating

### 21. Cooling SAT Reset Requests

- Key: `ashrae:g36:operational_sequence:5_8_8_1:cooling_sat_reset_requests`
- Scope: `ahu` / `operational_sequence` / §5.8.8.1 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p87: 5.8.8.1.  Cooling SAT Reset Requests

