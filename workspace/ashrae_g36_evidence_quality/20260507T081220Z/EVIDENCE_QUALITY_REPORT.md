# ASHRAE G36 Evidence Quality Audit

- Generated: `2026-05-07T08:12:20.340661+00:00`
- Rows audited: 699
- Weak rows: 28 (4.01%)
- By reason: weak evidence_quote: commissioning evidence lacks procedure/check action: 5, weak evidence_quote: lacks rule/action signal: 8, weak evidence_quote: section heading without supporting rule: 15
- By type: commissioning_step: 11, fault_diagnostic_rule: 7, operational_sequence: 10
- By equipment: ahu: 26, chiller: 2

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

- Key: `ashrae:g36:commissioning_step:5_16_15:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.16.15 / L3
- Reasons: weak evidence_quote: commissioning evidence lacks procedure/check action
- Sample p145: Provide software switches that interlock to a CHW and hot-water plant level to a. force HW valve full open if there is a hot-water coil, b. force HW valve full closed if there is a hot-water coil, c. force CHW valve full open, and d. force CHW valve full closed.

### 6. Zone Group Testing/Commissioning Override Switches

- Key: `ashrae:g36:commissioning_step:5_4_5:zone_group_testing_commissioning_override_switches`
- Scope: `ahu` / `commissioning_step` / §5.4.5 / L3
- Reasons: weak evidence_quote: commissioning evidence lacks procedure/check action
- Sample p71: When the value of a Zone Group’s override switch is changed, the corresponding override switch for every zone in the Zone Group shall change to the same value. Subsequently, the zone-level override switch may be changed to a different value.

### 7. Testing/Commissioning Overrides for Cooling-Only VAV

- Key: `ashrae:g36:commissioning_step:5_5_7:testing_commissioning_overrides_for_cooling_only_vav`
- Scope: `ahu` / `commissioning_step` / §5.5.7 / L3
- Reasons: weak evidence_quote: commissioning evidence lacks procedure/check action
- Sample p74: Provide software switches that interlock to a system-level point to a. force zone airflow setpoint to zero, b. force zone airflow setpoint to Vcool-max, c. force zone airflow setpoint to Vmin, d. force damper full closed/open, and e. reset request-hours accumulator point to zero.

### 8. Testing/Commissioning Overrides for VAV Zone

- Key: `ashrae:g36:commissioning_step:5_6_7:testing_commissioning_overrides_for_vav_zone`
- Scope: `ahu` / `commissioning_step` / §5.6.7 / L3
- Reasons: weak evidence_quote: commissioning evidence lacks procedure/check action
- Sample p78: Provide software switches that interlock to a system level point to a. force zone airflow setpoint to zero, b. force zone airflow setpoint to Vcool-max, c. force zone airflow setpoint to Vmin, d. force zone airflow setpoint to Vheat-max, e. force damper full closed/open, f. force heating to OFF/closed, and g. reset request-hours accumulator point to zero

### 9. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_7_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.7.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p82: 5.7.7.  Testing/Commissioning Overrides . Provide software switches that interlock to a system level point to

### 10. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_8_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.8.7 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p86: 5.8.7.  Testing/Commissioning Overrides . Provide software switches that interlock to a system level point to

### 11. Testing/Commissioning Overrides

- Key: `ashrae:g36:commissioning_step:5_9_7:testing_commissioning_overrides`
- Scope: `ahu` / `commissioning_step` / §5.9.7 / L3
- Reasons: weak evidence_quote: commissioning evidence lacks procedure/check action
- Sample p90: Provide software switches that interlock to a system level point to a. force zone airflow setpoint to zero, b. force zone airflow setpoint to Vcool-max, c. force zone airflow setpoint to Vmin, d. force damper full closed/open, e. force heating to ON/closed, f. turn fan ON/OFF, and g. reset request-hours accumulator point to zero.

### 12. AFDD Fault Condition FC#6: OA Fraction Error

- Key: `ashrae:g36:fault_diagnostic_rule:5_16_14_8:afdd_fault_condition_fc_6_oa_fraction_error`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.16.14.8 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p137: nevertheless occur if so determined by the fault condition tests in Section 5.16.14.8 .

### 13. AFDD Fault Condition FC#7: SAT Too Low in Full Heating

- Key: `ashrae:g36:fault_diagnostic_rule:5_16_14_8:afdd_fault_condition_fc_7_sat_too_low_in_full_heating`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.16.14.8 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p137: nevertheless occur if so determined by the fault condition tests in Section 5.16.14.8 .

### 14. Single-Zone VAV AHU AFDD Fault Conditions

- Key: `ashrae:g36:fault_diagnostic_rule:5_18_13:single_zone_vav_ahu_afdd_fault_conditions`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.18.13 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p149: AFDD routines for cooling ducts are listed in Sections 5.16.14  and 5.18.13 .

### 15. SZVAV AHU AFDD Fault Conditions

- Key: `ashrae:g36:fault_diagnostic_rule:5_18_13_6:szvav_ahu_afdd_fault_conditions`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.18.13.6 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p162: if so determined by the fault condition tests in Section 5.18.13.6 .

### 16. Fan Coil Unit AFDD Fault Conditions

- Key: `ashrae:g36:fault_diagnostic_rule:5_22_6:fan_coil_unit_afdd_fault_conditions`
- Scope: `ahu` / `fault_diagnostic_rule` / §5.22.6 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p264: 5.22.6.  Automatic Fault Detection and Diagnostics

### 17. Dual-Duct VAV Zone Endpoints as Function of Zone Group Mode

- Key: `ashrae:g36:operational_sequence:5_14_4:dual_duct_vav_zone_endpoints_as_function_of_zone_group_mode`
- Scope: `ahu` / `operational_sequence` / §5.14.4 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p108: Table 5.14.4 Endpoints as a Function of Zone Group Mode

### 18. Supply Air Temperature Setpoint for Cooldown, Warmup, Setback

- Key: `ashrae:g36:operational_sequence:5_16_2_2:supply_air_temperature_setpoint_for_cooldown_warmup_setback`
- Scope: `ahu` / `operational_sequence` / §5.16.2.2 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p112: 5.16.2.2. Supply Air Temperature Setpoint

### 19. Single-Zone VAV AHU Supply Fan Speed and SAT Setpoint Reset

- Key: `ashrae:g36:operational_sequence:5_18_4:single_zone_vav_ahu_supply_fan_speed_and_sat_setpoint_reset`
- Scope: `ahu` / `operational_sequence` / §5.18.4 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p152: 5.18.4. Supply Fan Speed Control and  Supply Air Temperature Set -Point Reset

### 20. Single-Zone VAV AHU Supply Air Temperature Control

- Key: `ashrae:g36:operational_sequence:5_18_5:single_zone_vav_ahu_supply_air_temperature_control`
- Scope: `ahu` / `operational_sequence` / §5.18.5 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p156: 154 ASHRAE Guideline 36 -2021  5.18.5.  Supply Air Temperature Control

### 21. Zone Minimum Outdoor Air and Minimum Airflow Setpoints (ASHRAE 62.1)

- Key: `ashrae:g36:operational_sequence:5_2_1_3:zone_minimum_outdoor_air_and_minimum_airflow_setpoints_ashrae_62_1`
- Scope: `ahu` / `operational_sequence` / §5.2.1.3 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p54: condition per Sections 5.20.4.13  and 5.21.3.8 .

### 22. Time-Averaged Ventilation (TAV) for Zones

- Key: `ashrae:g36:operational_sequence:5_2_2:time_averaged_ventilation_tav_for_zones`
- Scope: `ahu` / `operational_sequence` / §5.2.2 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p66: 64 ASHRAE Guideline 36 -2021  5.2.2.  Time -Averaged Ventilation

### 23. Zone State Heating - Discharge Temperature Reset

- Key: `ashrae:g36:operational_sequence:5_7_5_3:zone_state_heating_discharge_temperature_reset`
- Scope: `ahu` / `operational_sequence` / §5.7.5.3 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p81: 5.7.5.3.  When Zone State  Is Heating

### 24. Fan Control Logic for Parallel Fan-Powered Terminal Unit

- Key: `ashrae:g36:operational_sequence:5_7_5_5:fan_control_logic_for_parallel_fan_powered_terminal_unit`
- Scope: `ahu` / `operational_sequence` / §5.7.5.5 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p81: 5.7.5.5.  Fan Control

### 25. Heating Mode Sequence for Parallel Fan-Powered Terminal Unit

- Key: `ashrae:g36:operational_sequence:5_8_5_3:heating_mode_sequence_for_parallel_fan_powered_terminal_unit`
- Scope: `ahu` / `operational_sequence` / §5.8.5.3 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p85: 5.8.5.3.  When Zone State  is Heating

### 26. Cooling SAT Reset Requests

- Key: `ashrae:g36:operational_sequence:5_8_8_1:cooling_sat_reset_requests`
- Scope: `ahu` / `operational_sequence` / §5.8.8.1 / L3
- Reasons: weak evidence_quote: section heading without supporting rule
- Sample p87: 5.8.8.1.  Cooling SAT Reset Requests

### 27. AFDD – Condenser Approach Too High

- Key: `ashrae:g36:fault_diagnostic_rule:5_20_18_6:afdd_condenser_approach_too_high`
- Scope: `chiller` / `fault_diagnostic_rule` / §5.20.18.6 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p230: FC#8 Equation Approach COND ≥ RefrigCondTemp CH-x, AVG - CWRT CH-x, AVG Applies to OS #2, #3, #5 Description Condenser approach is too high

### 28. AFDD – Evaporator Approach Too High

- Key: `ashrae:g36:fault_diagnostic_rule:5_20_18_6:afdd_evaporator_approach_too_high`
- Scope: `chiller` / `fault_diagnostic_rule` / §5.20.18.6 / L3
- Reasons: weak evidence_quote: lacks rule/action signal
- Sample p230: FC#9 Equation Approach EVAP ≥ CHWST CH-x, AVG - RefrigEvapTemp CH-x, AVG Applies to OS #2, #3, #5 Description Evaporator approach is too high

