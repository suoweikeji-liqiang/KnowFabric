# ASHRAE Guideline 36 Review Decision Draft

- Source run: 20260506T101446Z_ashrae_guideline_36_2021_high_performance_sequences_ashrae_g36
- Standard: ASHRAE Guideline 36-2021
- Sections: 5.1.14, 5.20, 5.21
- Verified candidates: 22
- Type breakdown: {'application_guidance': 1, 'operational_sequence': 15, 'commissioning_procedure': 1, 'fault_diagnostic_rule': 4, 'parameter_spec': 1}

## How to review

For each item, mark `Decision` as `accepted` or `rejected`. Recommended review criteria: operational usefulness, correct KO type, accurate section citation, and suitability for sw_base_model.

## 1. [application_guidance] T&R Logic Application for VAV Static Pressure Control

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.1.14.4
- Pages: [46]
- Trust: L3
- Summary: Example sequence: Td=5 min, T=2 min, I=2, SPtrim=-10 Pa, SPres=15 Pa, SPres-max=37 Pa. Setpoint trims down when requests ≤ 2, responds up when requests > 2, capped at 37 Pa per step.
- Trigger: Fan status ON, after 5 min delay.
- Required behavior: Every 2 min: if R≤2, decrease setpoint by 10 Pa; if R>2, increase setpoint by (R-2)*15 Pa but max 37 Pa.
- Configurable values: SP0 = 120 Pa; SPmin = 37 Pa; SPmax = 370 Pa; Td = 5 min; T = 2 min; I = 2; SPtrim = -10 Pa; SPres = 15 Pa; SPres-max = 37 Pa
- Evidence quote: `See Section 5.1.14.4  for an example of T&R implementation.`
- Judge: Directly captures a control sequence example with configurable parameters from Section 5.1.14.4 of Guideline 36.

## 2. [operational_sequence] Trim & Respond Set-Point Reset Logic

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.1.14
- Pages: [46]
- Trust: L3
- Summary: T&R logic resets a setpoint at a fixed rate until a downstream zone is no longer satisfied and generates a request. When sufficient requests are present, the setpoint is increased. When requests subside, the setpoint resumes decreasing.
- Trigger: Associated device is proven ON, starting Td after initial device start command.
- Required behavior: Every time step T, if R ≤ I, trim setpoint by SPtrim. If R > I, respond by changing setpoint by (R – I)*SPres but no larger than SPres-max.
- Configurable values: SP0 (initial setpoint); SPmin (minimum setpoint); SPmax (maximum setpoint); Td (delay timer); T (time step); I (number of ignored requests); SPtrim (trim amount); SPres (respond amount, opposite sign to SPtrim); SPres-max (maximum response per time interval)
- Evidence quote: `5.1.14.  Trim & Respond Set -Point Reset Logic`
- Judge: The item describes a real control sequence (Trim & Respond logic) from section 5.1.14, which is operational knowledge per Guideline 36.

## 3. [commissioning_procedure] Request-Hours Accumulator Reset

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.1.14.2
- Pages: [47]
- Trust: L3
- Summary: Request-Hours Accumulator and System Run-Hours Total are reset to zero automatically when System Run-Hours Total exceeds 400 hours, or manually by a global operator command.
- Trigger: System Run-Hours Total exceeds 400 hours, or manual command.
- Required behavior: Reset Request-Hours Accumulator and System Run-Hours Total to zero.
- Configurable values: Automatic reset threshold (400 hours)
- Evidence quote: `The Request-Hours Accumulator and System Run-Hours Total are reset to zero as follows: i. Reset automatically for an individual zone/system when the System Run-Hours Total exceeds 400 hours. ii. Reset manually by a global operator command.`
- Judge: Captures a specific, operational commissioning procedure regarding automatic and manual reset of request-hour accumulators based on system run-hours, which is a configurable control parameter from the guideline.

## 4. [fault_diagnostic_rule] Rogue Zone Detection via Cumulative% Request-Hours

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.1.14.2
- Pages: [47]
- Trust: L3
- Summary: A Level 4 alarm is generated if zone Importance-Multiplier > 0, Cumulative% Request-Hours > 70%, and total zone/system run hours > 40.
- Trigger: Importance-Multiplier > 0, Cumulative% Request-Hours > 70%, and total run hours > 40.
- Required behavior: Generate a Level 4 alarm.
- Configurable values: Importance-Multiplier (default = 1); Cumulative% Request-Hours threshold (70%); Run hours threshold (40 hours)
- Fault condition: Rogue zone driving reset logic
- Evidence quote: `A Level 4 alarm is generated if the zone Importance-Multiplier is greater than zero, the zone/system Cumulative% Request Hours exceeds 70%, and the total number of zone/system run hours exceeds 40.`
- Judge: The item captures a real fault diagnostic rule from ASHRAE Guideline 36, specifying clear operational conditions for generating a Level 4 alarm, which is grounded in the provided evidence.

## 5. [parameter_spec] T&R Variables and Defaults

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.1.14.3
- Pages: [47]
- Trust: L3
- Summary: Define variables: Device, SP0, SPmin, SPmax, Td, T, I, SPtrim, SPres, SPres-max. Initial values defined in system/plant sequences. Values for trim, respond, time step, etc. shall be tuned to provide stable control.
- Configurable values: Device (associated device e.g., fan, pump); SP0 (initial setpoint); SPmin (minimum setpoint); SPmax (maximum setpoint); Td (delay timer); T (time step); I (number of ignored requests); SPtrim (trim amount); SPres (respond amount, must be opposite in sign to SPtrim); SPres-max (maximum response per time interval, same sign as SPres)
- Evidence quote: `For each upstream system or plant setpoint being controlled by a T&R loop, define the following variables. Initial values are defined in system/plant sequences below. Values for trim, respond, time step, etc. shall be tuned to provide stable control. See Table 5.1.14.3.`
- Judge: Captures configurable control parameters for T&R loops with tuning guidance, grounded in operational control sequences from Guideline 36.

## 6. [operational_sequence] Plant Enable Logic

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.2.2
- Pages: [172]
- Trust: L3
- Summary: Enable plant when disabled for ≥15 min, number of Chiller Plant Requests > I (default 0), OAT > CH-LOT, and schedule active.
- Trigger: Plant disabled for ≥15 min AND Number of Chiller Plant Requests > I (default 0) AND OAT > CH-LOT AND schedule active.
- Required behavior: Enable plant in lowest stage.
- Configurable values: I (default 0); CH-LOT
- Evidence quote: `5.20.2.2.  Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and:`
- Judge: Captures real plant enable control sequence with specific conditions from Guideline 36 section 5.20.2.2.

## 7. [operational_sequence] Plant Disable Logic

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.2.3
- Pages: [172]
- Trust: L3
- Summary: Disable plant when enabled for ≥15 min and either requests ≤ I for 3 min, OAT < CH-LOT – 1°F, or schedule inactive.
- Trigger: Plant enabled for ≥15 min AND (Number of Chiller Plant Requests ≤ I for 3 min OR OAT < CH-LOT – 1°F OR schedule inactive).
- Required behavior: Disable plant.
- Configurable values: I (default 0); CH-LOT
- Evidence quote: `Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Chiller Plant Requests ≤ I for 3 minutes, or b. OAT<CH-LOT – 1°F, or c. The chiller plant enable schedule is inactive.`
- Judge: Captures a real control sequence for plant disable logic from section 5.20.2.3.

## 8. [operational_sequence] Waterside Economizer Enable Logic

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.3.1
- Pages: [175]
- Trust: L3
- Summary: Enable WSE if disabled for ≥20 min and CHWRT upstream of HX > PHXLWT + 2°F. PHXLWT calculated from wetbulb, design approaches, and part load ratio.
- Trigger: WSE disabled for ≥20 min AND CHWRT upstream of HX > PHXLWT + 2°F.
- Required behavior: Enable waterside economizer.
- Configurable values: DA HX; DA CT; DT WB; m (tunable)
- Evidence quote: `Enable waterside economizer (WSE) if it has been disabled for at least 20 minutes and CHWRT upstream of HX is greater than the predicted heat exchanger leaving water temperature (PHXLWT) plus 2°F.`
- Judge: Captures a specific waterside economizer enable control sequence with configurable parameters (timing, temperature differential) from ASHRAE Guideline 36.

## 9. [operational_sequence] Waterside Economizer Disable Logic

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.3.2
- Pages: [176]
- Trust: L3
- Summary: Disable WSE when it has run for ≥20 min and CHW temp downstream of HX > CHWRT upstream of HX less 1°F for 2 min.
- Trigger: WSE enabled for ≥20 min AND CHW temp downstream of HX > CHWRT upstream of HX – 1°F for 2 min.
- Required behavior: Disable waterside economizer.
- Evidence quote: `Disable WSE when it has run for at least 20 minutes and CHW temp downstream of HX is greater than CHWRT upstream of HX less 1ºF for 2 minutes`
- Judge: Captures a real control sequence for disabling waterside economizer based on runtime and temperature conditions.

## 10. [operational_sequence] Chiller Staging – Stage Down Condition

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.4.15
- Pages: [182, 183, 184]
- Trust: L4
- Summary: Stage down if next lower stage OPLR < SPLR_DN for 15 min and not increasing >2.5%/min, and failsafe stage up condition not true.
- Trigger: Next available lower stage OPLR < SPLR_DN for 15 minutes AND next lower stage OPLR is not increasing at a rate greater than 2.5% per minute averaged over 5 minutes AND failsafe stage up condition is not true.
- Required behavior: Initiate stage down.
- Configurable values: SPLR_DN (calculated per chiller type and lift)
- Evidence quote: `Stage down if both of the following are true: 1. Next available lower stage OPLR < SPLR DN for 15 minutes and next lower stage OPLR is not increasing at a rate greater than 2.5% per minute averaged over 5 minutes; and 2. The failsafe stage up condition is not true.`
- Judge: This is a real control sequence from the chiller staging section of Guideline 36, capturing a specific stage down condition with configurable parameters and timing.

## 11. [operational_sequence] Chiller Staging – Stage Up Efficiency Condition

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.4.15
- Pages: [182, 183, 184, 185]
- Trust: L4
- Summary: Stage up if current stage OPLR > SPLR_UP for 15 min and OPLR not decreasing >2.5%/min averaged over 5 min.
- Trigger: Current stage OPLR > SPLR_UP for 15 minutes AND current stage OPLR is not decreasing at a rate greater than 2.5% per minute averaged over 5 minutes.
- Required behavior: Initiate stage up.
- Configurable values: SPLR_UP (calculated per chiller type and lift)
- Evidence quote: `Efficiency Condition : Current stage OPLR > SPLR UP for 15 minutes and current stage OPLR is not decreasing at a rate greater than 2.5% per minute averaged over 5 minutes`
- Judge: Captures a specific chiller staging control rule from the guideline.

## 12. [operational_sequence] Chilled Water Supply Temperature Reset (DP Controlled Loops)

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.5.2
- Pages: [199]
- Trust: L3
- Summary: Reset DP setpoint from CHW-DPmin to CHW-DPmax from 0-50% loop output, then reset CHWST setpoint from CHWSTmax to CHWSTmin from 50-100% loop output. Trim & Respond with parameters.
- Trigger: Plant enabled.
- Required behavior: Reset CHW Plant Reset variable using Trim & Respond logic with given parameters.
- Configurable values: CHW-DPmin; CHW-DPmax; CHWSTmin; CHWSTmax; Td=15 min; T=5 min; I=2; SPtrim=-2%; SPres=+3%; SPres-max=+7%
- Evidence quote: `5.20.5.2. Differential Pressure Controlled Loops: Chilled water supply t emperature setpoint CHWSTsp and`
- Judge: Captures a real operational control sequence for chilled water supply temperature reset with DP control from Section 5.20.5.2.

## 13. [operational_sequence] Primary CHW Pump Speed Control (Variable Primary-Variable Secondary with Decoupler Flow Meter)

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.6.17
- Pages: [204]
- Trust: L3
- Summary: Reset primary pump speed by reverse acting PID maintaining decoupler flow at 5% of PCHWFdesign. Map loop output from CH-MinPriPumpSpdStage to 100% speed.
- Trigger: Plant enabled and primary pumps proven on.
- Required behavior: Maintain decoupler flow at 5% of PCHWFdesign via PID loop.
- Configurable values: CH-MinPriPumpSpdStage; PCHWFdesign
- Evidence quote: `Primary pump speed shall be reset by a reverse acting PID loop maintaining flow through the decoupler flow meter at 5% of PCHWFdesign`
- Judge: Extracted control sequence for primary pump speed reset using reverse acting PID to maintain decoupler flow, directly from section 5.20.6.17.

## 14. [fault_diagnostic_rule] AFDD – Chilled Water Supply Temperature Too High

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.18.6
- Pages: [230]
- Trust: L3
- Summary: Fault condition FC#6: CHWST_AVG - ƐCHWT ≥ CHWSTSP. Applies to OS #2-#5.
- Trigger: CHWST_AVG - ƐCHWT ≥ CHWSTSP
- Required behavior: Report alarm with possible diagnosis: mechanical problem with chillers or primary flow too high.
- Configurable values: ƐCHWT (default 2°F)
- Fault condition: Chilled water supply temperature too high
- Evidence quote: `FC#6 Equation CHWST AVG - ƐCHWT ≥ CHWSTSP Applies to OS #2 – #5 Description Chilled water supply temperature is too high`
- Judge: Valid fault diagnostic rule with equation and applicable operating states

## 15. [fault_diagnostic_rule] AFDD – Condenser Approach Too High

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.18.6
- Pages: [230]
- Trust: L3
- Summary: Fault condition FC#8: Approach_COND ≥ RefrigCondTemp_CH-x,AVG - CWRT_CH-x,AVG. Applies to OS #2, #3, #5.
- Trigger: Approach_COND ≥ RefrigCondTemp_CH-x,AVG - CWRT_CH-x,AVG
- Required behavior: Report alarm with possible diagnosis: condenser fouling, low CW temperature or flow.
- Configurable values: Approach_COND (default 4°F)
- Fault condition: Condenser approach too high
- Evidence quote: `FC#8 Equation Approach COND ≥ RefrigCondTemp CH-x, AVG - CWRT CH-x, AVG Applies to OS #2, #3, #5 Description Condenser approach is too high`
- Judge: It is a specific fault diagnostic rule from Guideline 36 with an equation and applicability.

## 16. [fault_diagnostic_rule] AFDD – Evaporator Approach Too High

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.20.18.6
- Pages: [230]
- Trust: L3
- Summary: Fault condition FC#9: Approach_EVAP ≥ CHWST_CH-x,AVG - RefrigEvapTemp_CH-x,AVG. Applies to OS #2, #3, #5.
- Trigger: Approach_EVAP ≥ CHWST_CH-x,AVG - RefrigEvapTemp_CH-x,AVG
- Required behavior: Report alarm with possible diagnosis: evaporator fouling, low refrigerant charge, or contaminated charge.
- Configurable values: Approach_EVAP (default 3°F)
- Fault condition: Evaporator approach too high
- Evidence quote: `FC#9 Equation Approach EVAP ≥ CHWST CH-x, AVG - RefrigEvapTemp CH-x, AVG Applies to OS #2, #3, #5 Description Evaporator approach is too high`
- Judge: The extraction captures a specific fault diagnostic rule (FC#9) with a condition equation and applicability, which is operational knowledge from the guideline.

## 17. [operational_sequence] Plant Enable/Disable

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.21.2.2
- Pages: [235]
- Trust: L3
- Summary: Enable plant when disabled for ≥15 min, number of Heating Hot-Water Plant Requests > I (default 0), OAT < HW-LOT, and schedule active.
- Trigger: Plant disabled for ≥15 min AND Number of Heating Hot-Water Plant Requests > I (adjustable, default 0) AND OAT < HW-LOT AND Boiler plant enable schedule active.
- Required behavior: Enable plant in lowest stage.
- Configurable values: I (ignore count, default 0); HW-LOT (lockout temperature)
- Evidence quote: `5.21.2.2.  Enable the plant in the lowest stage when the plant has been disabled for at least 15 minutes and:`
- Judge: Operational sequence for enabling heating hot-water plant with configurable parameters, grounded in Guideline 36 section 5.21.2.2.

## 18. [operational_sequence] Plant Disable Logic

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.21.2.3
- Pages: [235]
- Trust: L3
- Summary: Disable plant when enabled for ≥15 min and either number of requests ≤ I for 3 min, OAT > HW-LOT+1°F, or schedule inactive.
- Trigger: Plant enabled for ≥15 min AND (Number of Heating Hot-Water Plant Requests ≤ I for 3 minutes OR OAT > HW-LOT + 1°F OR Boiler plant enable schedule inactive).
- Required behavior: Disable the plant.
- Configurable values: I (ignore count); HW-LOT
- Evidence quote: `Disable the plant when it has been enabled for at least 15 minutes and: a. Number of Heating Hot-Water Plant Requests ≤ I for 3 minutes, or b. OAT>HW-LOT + 1°F, or c. The Boiler plant enable schedule is inactive.`
- Judge: Extracted item captures a specific control sequence for plant disable logic with configurable parameters, grounded in ASHRAE Guideline 36 operational knowledge.

## 19. [operational_sequence] Primary Only Condensing Boiler Staging Down

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.21.3.9.g
- Pages: [238]
- Trust: L3
- Summary: Stage down if Qrequired < 110% of B-STAGE MIN of current stage for 5 min or bypass valve >0% for 5 min, failsafe not true, and Qrequired < 80% of design capacity of next lower stage for 5 min.
- Trigger: All of: 1) (Qrequired < 110% of B-STAGE MIN of current stage for 5 minutes OR minimum flow bypass valve >0% open for 5 minutes); 2) failsafe stage up condition not true; 3) Qrequired < 80% of design capacity of boilers in next lower stage for 5 minutes.
- Required behavior: Stage down to next available lower stage.
- Configurable values: B-STAGE MIN; QbX (design capacity)
- Evidence quote: `Stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. The minimum flow bypass valve, if provided, is greater than 0% open for 5 minutes. 2. The fail safe stage up condition is not true. 3. Qrequired is less than 80% of the design capacity, QbX, of the boilers in the next available lower stage for 5 minutes.`
- Judge: Extraction captures a real control sequence with specific parameters and timers from G36 section 5.21.3.9.g.

## 20. [operational_sequence] Variable Primary/Variable Secondary Condensing Boiler Staging Down

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.21.3.9.i
- Pages: [239, 240]
- Trust: L4
- Summary: Stage down if Qrequired < 110% of B-STAGE MIN of current stage for 5 min or (primary pumps at min speed and primary HWRT > secondary HWRT by 3°F for 5 min), failsafe not true, and Qrequired < 80% of design capacity of next lower stage for 5 min.
- Trigger: All of: 1) (Qrequired < 110% of B-STAGE MIN of current stage for 5 minutes OR Primary HW pumps at B-MinPriPumpSpdStage and primary HWRT > secondary HWRT by 3°F for 5 minutes); 2) failsafe stage up condition not true; 3) Qrequired < 80% of design capacity of boilers in next lower stage for 5 minutes.
- Required behavior: Stage down to next available lower stage.
- Configurable values: B-STAGE MIN; B-MinPriPumpSpdStage; QbX
- Evidence quote: `Stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. For 5 minutes, Primary HW pumps are at B-MinPriPumpSpdStage and primary HWRT exceeds secondary HWRT by 3°F. 2. The failsafe stage up condition is not true. 3. Qrequired is less than 80% of the design capacity, QbX, of the boilers in the next available lower stage for 5 minutes.`
- Judge: Captures a real staging down control sequence with specific parameters and timing from the guideline.

## 21. [operational_sequence] Non-Condensing Boiler Staging Down

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.21.3.9.k
- Pages: [240]
- Trust: L3
- Summary: Stage down if Qrequired < 80% of design capacity of next lower stage for 10 min and failsafe not true.
- Trigger: Both: 1) Qrequired < 80% of design capacity of next lower available stage for 10 minutes; 2) failsafe stage up condition not true.
- Required behavior: Stage down to next available lower stage.
- Configurable values: QbX
- Evidence quote: `Stage down if both of the following are true: 1. Qrequired is less than 80% of the design capacity of the next lower available stage for 10 minutes; and 2. The failsafe stage up condition is not true.`
- Judge: Captures a real staging down control sequence from ASHRAE Guideline 36, section 5.21.3.9.k.

## 22. [operational_sequence] Hybrid Boiler Staging Down (Condensing Current Stage)

- Decision: pending
- Notes:
- Citation: ASHRAE Guideline 36-2021 §5.21.3.9.m
- Pages: [240]
- Trust: L3
- Summary: If all boilers in current stage are condensing, stage down using same conditions as variable primary/variable secondary condensing: Qrequired < 110% of B-STAGE MIN for 5 min or (primary pumps at min speed and primary HWRT > secondary HWRT by 3°F for 5 min), failsafe not true, and Qrequired < 80% of design capacity of next lower stage for 5 min.
- Trigger: Same as 5.21.3.9.i.
- Required behavior: Stage down to next available lower stage.
- Configurable values: B-STAGE MIN; B-MinPriPumpSpdStage; QbX
- Evidence quote: `If all boilers enabled in the current stage are condensing, stage down if all of the following are true: 1. Either: i. Qrequired falls below 110% of B-STAGE MIN of the current stage for 5 minutes; or ii. For 5 minutes, Primary HW pumps are at B-MinPriPumpSpdStage and primary HWRT exceeds secondary HWRT by 3°F. 2. The failsafe stage up condition is not true. 3. Qrequired is less than 80% of the design capacity, QbX, of the boilers in the next available lower stage for 5 minutes.`
- Judge: Extraction captures a real control sequence with configurable parameters and timing conditions from Section 5.21.3.9.m, providing actionable operational knowledge.

