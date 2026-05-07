# ASHRAE G36 Consumer Validation Report

- Generated: `2026-05-07T08:07:10.523930+00:00`
- Min trust level: `L3`
- Service limit: 500
- Passed/failed: 10/0

| Scenario | Equipment | Service | Status | Matches | Expected Sections |
|---|---|---|---|---:|---|
| `ahu_low_airflow_alarm` | `ahu` | `fault_knowledge` | pass | 32 / 3 | `5.5.6.1, 5.6.6.1, 5.7.6.1, 5.8.6.1, 5.10.6.1, 5.12.6.1, 5.13.6.1, 5.14.6.1` |
| `ahu_sat_reset` | `ahu` | `operational_guidance` | pass | 23 / 3 | `5.6.8.1, 5.8.8.1, 5.10.8.1, 5.12.8.1, 5.14.8.1` |
| `ahu_static_pressure_reset` | `ahu` | `operational_guidance` | pass | 25 / 3 | `5.6.8.2, 5.8.8.2, 5.10.8.2, 5.12.8.2, 5.14.8.2, 5.16.1.2, 5.17.1.2` |
| `ahu_afdd` | `ahu` | `fault_knowledge` | pass | 29 / 3 | `5.16.14, 5.17.4, 5.18.13, 5.22.6` |
| `chiller_plant_enable_disable` | `chiller` | `operational_guidance` | pass | 4 / 2 | `5.20.2.2, 5.20.2.3` |
| `chiller_stage_up_down` | `chiller` | `operational_guidance` | pass | 10 / 3 | `5.20.4.15` |
| `chiller_afdd` | `chiller` | `fault_knowledge` | pass | 9 / 3 | `5.20.18.6` |
| `hot_water_plant_enable_disable` | `hot_water_plant` | `operational_guidance` | pass | 6 / 2 | `5.21.2.2, 5.21.2.3` |
| `hot_water_boiler_staging` | `hot_water_plant` | `operational_guidance` | pass | 17 / 3 | `5.21.3.9` |
| `hot_water_fault_diagnostics` | `hot_water_plant` | `fault_knowledge` | pass | 11 / 3 | `5.21.11.6` |

## Samples

### ahu_low_airflow_alarm (pass)

Question: For an AHU or VAV terminal, what does G36 say about low airflow alarms?

- §5.5.6.1.c / L3 / p74: Low Airflow Alarm Suppression for Zero Importance Multiplier Zones
  Evidence: If a zone has an importance multiplier of 0 (see Section 5.1.14.2.a.1) for its static pressure reset T&R control loop, low airflow alarms shall be suppressed for that zone.
- §5.10.6.1 / L4 / p74, 77, 81, 86, 89: Low Primary Airflow Alarm
  Evidence: If the measured airflow is less than 70% of setpoint for 10 minutes while setpoint is greater than zero, generate a Level 4 alarm.
- §5.10.6.1 / L4 / p74, 77, 81, 86, 89: Low Primary Airflow Alarm - Level 3
  Evidence: b. If the measured airflow is less than 50% of setpoint for 10 minutes while setpoint is greater than zero, generate a Level 3 alarm.
- §5.10.6.1 / L4 / p77, 81, 86, 89, 93: Low Primary Airflow Alarm - Level 4
  Evidence: a. If the measured airflow is less than 70% of setpoint for 10 minutes while setpoint is greater than zero, generate a Level 4 alarm.
- §5.12.6.1 / L4 / p74, 77, 81, 86, 89: Dual-Duct VAV Terminal Unit Low Airflow Alarm
  Evidence: If the measured airflow is less than 70% of setpoint for 10 minutes while setpoint is greater than zero, generate a Level 4 alarm.

### ahu_sat_reset (pass)

Question: How are AHU SAT reset requests generated?

- §5.8.8.1 / L3 / p87: Cooling SAT Reset Requests
  Evidence: 5.8.8.1.  Cooling SAT Reset Requests
- §5.10.8.1 / L4 / p75, 78, 83, 87, 90: Cooling SAT Reset Requests
  Evidence: If the zone temperature exceeds the zone’s cooling setpoint by 3°C (5°F) for 2 minutes and after suppression period due to setpoint change per Section 5.1.20, send 3 requests.
- §5.10.8.1 / L4 / p75, 78, 83, 87, 90: Cooling SAT Reset Requests - 0 Requests (Cooling Loop < 95%)
  Evidence: d. Else if the Cooling Loop is less than 95%, send 0 requests.
- §5.10.8.1 / L4 / p75, 78, 83, 87, 90: Cooling SAT Reset Requests - 1 Request (Cooling Loop > 95%)
  Evidence: c. Else if the Cooling Loop is greater than 95%, send 1 request until the Cooling Loop is less than 85%.
- §5.10.8.1 / L4 / p75, 78, 83, 87, 90: Cooling SAT Reset Requests - 2 Requests
  Evidence: b. Else if the zone temperature exceeds the zone’s cooling setpoint by 2°C (3°F) for 2 minutes and after suppression period due to setpoint change per Section 5.1.20, send 2 requests.

### ahu_static_pressure_reset (pass)

Question: How are duct static pressure reset requests generated?

- §5.16.1.2 / L3 / p111: Multiple-Zone VAV AHU – Static Pressure Setpoint Reset (T&R)
  Evidence: Static pressure setpoint. Setpoint shall be reset using T&R logic (see Section 5.1.14) using the parameters shown in Table 5.16.1.2.
- §5.16.1.2 / L3 / p111: Static Pressure Setpoint Reset using T&R Logic
  Evidence: Static pressure setpoint. Setpoint shall be reset using T&R logic (see Section 5.1.14) using the parameters shown in Table 5.16.1.2.
- §5.16.1.2 / L3 / p111: Static Pressure Setpoint Reset using Trim & Respond
  Evidence: Static pressure setpoint. Setpoint shall be reset using T&R logic (see Section 5.1.14) using the parameters shown in Table 5.16.1.2.
- §5.17.1.2 / L3 / p146: Dual-Fan Dual-Duct Heating VAV AHU Static Pressure Setpoint Reset
  Evidence: Static pressure setpoint. Setpoint shall be reset using T&R logic (see Section 5.1.14) using the parameters in Table 5.17.1.2.
- §5.17.1.2 / L3 / p146: Static Pressure Setpoint Reset using T&R Logic
  Evidence: Static pressure setpoint. Setpoint shall be reset using T&R logic (see Section 5.1.14) using the parameters in Table 5.17.1.2.

### ahu_afdd (pass)

Question: What AFDD rules and fault conditions are available for AHUs?

- §5.18.13.6 / L3 / p168: AFDD Fault Condition FC#13
  Evidence: FC #13 Equation: SAT AVG > SAT SP-C + Ɛ SAT and CC ≥ 99% Applies to OS #3, #4 Description: SAT too high in full cooling Possible Diagnosis: SAT sensor error, Cooling coil valve stuck closed or actuator failure, Fouled or undersized cooling 
- §5.18.13.6 / L3 / p166: AFDD Fault Condition FC#3
  Evidence: FC #3 (omit if no MAT sensor) Equation: MAT AVG - ƐMAT > min[(RAT AVG + Ɛ RAT), (OAT AVG + Ɛ OAT)] Applies to OS #1 – #5 Description: MAT too high; should be between OAT and RAT Possible Diagnosis: RAT sensor error, MAT sensor error, OAT se
- §5.18.13.6 / L3 / p166: AFDD Fault Condition FC#7
  Evidence: FC #7 (omit if no heating coil) Equation: SAT AVG < SATSP - ƐSAT and HC ≥ 99% Applies to OS #1 Description: SAT too low in full heating Possible Diagnosis: SAT sensor error, Cooling coil valve leaking or stuck open, Heating coil valve stuck
- §5.16.14.8 / L3 / p140: AFDD Fault Condition FC#1: Duct Static Pressure Too Low
  Evidence: FC#1 Equation: DSP AVG < DSPSP - ƐDSP and VFDSPD ≥ 99% - ƐVFDSPD. Applies to OS #1 – #5. Description: Duct static pressure is too low with fan at full speed.
- §5.16.14.8 / L3 / p137: AFDD Fault Condition FC#6: OA Fraction Error
  Evidence: nevertheless occur if so determined by the fault condition tests in Section 5.16.14.8 .

### chiller_plant_enable_disable (pass)

Question: How should the chilled water plant be enabled and disabled?

- §5.20.2.2 / L3 / p172: Chiller Plant Enable Logic
  Evidence: 5.20.2.2.  Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and:
- §5.20.2.2 / L3 / p172, 172: Chilled Water Plant Enable Logic
  Evidence: 5.20.2.2. Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and: a. Number of Chiller Plant Requests > I (I = Ignores shall default to 0, adjustable), and b. OAT>CH -LOT, and c. The chiller plant 
- §5.20.2.3 / L3 / p172: Chiller Plant Disable Logic
  Evidence: Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Chiller Plant Requests ≤ I for 3 minutes, or b. OAT<CH-LOT – 1°F, or c. The chiller plant enable schedule is inactive.
- §5.20.2.3 / L3 / p172: Chilled Water Plant Disable Logic
  Evidence: Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Chiller Plant Requests ≤ I for 3 minutes, or b. OAT<CH-LOT – 1°F, or c. The chiller plant enable schedule is inactive.

### chiller_stage_up_down (pass)

Question: What does G36 say about chiller stage up and stage down logic?

- §5.20.4.15 / L3 / p185: Stage Up Failsafe Condition (Primary-Secondary without WSE)
  Evidence: Failsafe Condition: i. Secondary CHW supply temperature > primary CHW supply temperature + 2°F for 10 minutes and the enabled primary pumps are at maximum speed; or ii. Primary CHW supply temperature is 2°F > setpoint for 15 minutes.
- §5.20.4.15 / L4 / p183, 184, 185, 238: Chiller Stage Up – Availability Condition
  Evidence: Availability Condition: The equipment necessary to operate the current stage are unavailable. The availability condition is not subject to the minimum stage runtime requirement.
- §5.20.4.15 / L4 / p182, 183, 184: Chiller Staging – Stage Down Condition
  Evidence: Stage down if both of the following are true: 1. Next available lower stage OPLR < SPLR DN for 15 minutes and next lower stage OPLR is not increasing at a rate greater than 2.5% per minute averaged over 5 minutes; and 2. The failsafe stage 
- §5.20.4.15 / L4 / p182, 183, 184, 185: Chiller Staging – Stage Up Efficiency Condition
  Evidence: Efficiency Condition : Current stage OPLR > SPLR UP for 15 minutes and current stage OPLR is not decreasing at a rate greater than 2.5% per minute averaged over 5 minutes
- §5.20.4.15 / L4 / p182, 183, 184: Stage Down Condition (Primary-Only without WSE)
  Evidence: Stage down if both of the following are true: 1. Next available lower stage OPLR < SPLR DN for 15 minutes and next lower stage OPLR is not increasing at a rate greater than 2.5% per minute averaged over 5 minutes; and 2. The failsafe stage 

### chiller_afdd (pass)

Question: What AFDD fault diagnostics are available for the chilled water plant?

- §5.20.18.6 / L3 / p230: AFDD – Chilled Water Supply Temperature Too High
  Evidence: FC#6 Equation CHWST AVG - ƐCHWT ≥ CHWSTSP Applies to OS #2 – #5 Description Chilled water supply temperature is too high
- §5.20.18.6 / L3 / p230: AFDD – Condenser Approach Too High
  Evidence: FC#8 Equation Approach COND ≥ RefrigCondTemp CH-x, AVG - CWRT CH-x, AVG Applies to OS #2, #3, #5 Description Condenser approach is too high
- §5.20.18.6 / L3 / p230: AFDD – Evaporator Approach Too High
  Evidence: FC#9 Equation Approach EVAP ≥ CHWST CH-x, AVG - RefrigEvapTemp CH-x, AVG Applies to OS #2, #3, #5 Description Evaporator approach is too high
- §5.20.18.6 / L3 / p232: AFDD FC#14: CWST Too High with Towers at Full Speed
  Evidence: FC#14 Equation CWST AVG - ƐCWT ≥ DesCWSTdes and SpeedCT ≥ 99% - ƐVFDSPD Applies to OS #2, #3 Description Condenser water supply temperature is too high with cooling tower(s) at full speed.
- §5.20.18.6 / L3 / p229: AFDD FC#1: DP Too High with Pumps Off
  Evidence: FC#1 Equation DP AVG > Ɛ DSP and Status CHWP = Off Applies to OS #1 Description Differential pressure is too high with the chilled water pumps off Possible Diagnosis DP sensor error

### hot_water_plant_enable_disable (pass)

Question: How should the hot water plant or boiler plant be enabled and disabled?

- §5.21.2.2 / L3 / p235: Boiler Plant Enable Logic
  Evidence: 5.21.2.2.  Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and:
- §5.21.2.2 / L3 / p235, 235: Hot Water Plant Enable Logic
  Evidence: 5.21.2.2. Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and: a. Number of Heating Hot -Water Plant Requests > I (I = Ignores shall default to 0, ad justable), and b. OAT<HW -LOT, and c. The Bo
- §5.21.2.2 / L3 / p235: Plant Enable/Disable - Enable Logic
  Evidence: 5.21.2.2.  Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and:
- §5.21.2.3 / L3 / p235: Boiler Plant Disable Logic
  Evidence: Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Heating Hot-Water Plant Requests ≤ I for 3 minutes, or b. OAT>HW-LOT + 1°F, or c. The Boiler plant enable schedule is inactive.
- §5.21.2.3 / L3 / p235: Hot Water Plant Disable Logic
  Evidence: Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Heating Hot-Water Plant Requests ≤ I for 3 minutes, or b. OAT>HW-LOT + 1°F, or c. The Boiler plant enable schedule is inactive.

### hot_water_boiler_staging (pass)

Question: What does G36 say about boiler stage up and stage down logic?

- §5.21.3.9 / L3 / p237: Boiler Minimum Stage Runtime
  Evidence: Each stage shall have a minimum runtime of 10 minutes.
- §5.21.3.9.g / L3 / p238: Boiler Staging - Primary Only Condensing: Stage Down
  Evidence: Stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. The minimum flow bypass valve, if provided, is greater than 0% open for 5 minutes. 2. The fail s
- §5.21.3.9.h / L3 / p240: Boiler Staging - Variable Primary/Variable Secondary Condensing: Stage Up
  Evidence: Stage up if any of the following is true: 1. Availability Condition: The equipment necessary to operate the current stage is unavailable. The availability condition is not subject to the minimum stage runtime requirement. Or 2. Efficiency C
- §5.21.3.9.k / L3 / p240: Boiler Staging - Non-Condensing: Stage Down
  Evidence: Stage down if both of the following are true: 1. Qrequired is less than 80% of the design capacity of the next lower available stage for 10 minutes; and 2. The failsafe stage up condition is not true.
- §5.21.3.9.l / L3 / p240: Boiler Staging - Hybrid: Stage Up to Condensing Stage
  Evidence: If all boilers enabled in the next higher stage are condensing, stage up if any of the following is true: 1. Availability Condition: The equipment necessary to operate the current stage is unavailable. The availability condition is not subj

### hot_water_fault_diagnostics (pass)

Question: What hot water plant AFDD fault conditions are available?

- §5.21.11.6 / L3 / p260: AFDD - FC#10: Supply Temperature Sensor Deviation
  Evidence: FC#10 Equation | (∑(HW-Flow B-X * HWST B-X) / ∑HW-Flow B-X) - HWST AVG | > ƐHWT Applies to OS #2 Description Deviation between the active boiler hot water supply temperature and the common hot water supply temperature is too high.
- §5.21.11.6 / L3 / p261: AFDD - FC#11: Return Temperature Sensor Deviation
  Evidence: FC#11 Equation | (∑(HW-Flow B-X * HWRT B-X) / ∑HW-Flow B-X) - HWRT AVG | > ƐHWT Applies to OS #2 Description Deviation between the active boiler hot water return temperature and the common boiler entering water temperature is too high.
- §5.21.11.6 / L3 / p258: AFDD - FC#1: DP Too High with Pumps Off
  Evidence: FC#1 Equation DP AVG > Ɛ DSP and Status HWP = Off Applies to OS #1 Description Differential pressure is too high with the hot water pumps off Possible Diagnosis DP sensor error
- §5.21.11.6 / L3 / p259: AFDD - FC#2: Primary Flow Too High with Pumps Off
  Evidence: FC#2 Equation FLOW P, AVG > Ɛ FM and Status PHWP = Off Applies to OS #1 Description Primary hot water flow is too high with the hot water pumps off Possible Diagnosis Flow meter error
- §5.21.11.6 / L3 / p259: AFDD - FC#3: Secondary Flow Too High with Pumps Off
  Evidence: FC#3 Equation FLOW S, AVG > Ɛ FM and Status SHWP = Off Applies to OS #1 Description Secondary hot water flow is too high with the associated hot water pumps off Possible Diagnosis Flow meter error

