# Standard Knowledge Dedupe Report

- Standard: `ASHRAE Guideline 36-2021`
- Approved rows scanned: 246
- Duplicate groups: 21
- Recommended duplicate rows: 30
- Estimated unique after dedupe: 216
- Similarity threshold: 0.78

## Duplicate Groups

### Group 1

Keep: `ko_b766d84d16cfc10a` ahu / fault_diagnostic_rule / §5.16.14.8 / L3 / evidence=1
- VAV AHU – FC#7: SAT Too Low in Full Heating

Duplicates:
- `ko_9e3547fa20b709a7` L3 evidence=1 - AFDD Fault Condition FC#7: SAT Too Low in Full Heating
- `ko_b3dc4f8b1af762ac` L3 evidence=1 - VAV AHU – FC#13: SAT Too High in Full Cooling

### Group 2

Keep: `ko_6d02ce616fcfa72f` ahu / fault_diagnostic_rule / §5.6.6.2 / L4 / evidence=5
- Low-Discharge Air Temperature Alarm

Duplicates:
- `ko_a46de9bfbeed88c5` L4 evidence=4 - VAV Reheat Zone – Low Discharge Air Temperature Alarm

### Group 3

Keep: `ko_1a6dc67ec54044dc` ahu / fault_diagnostic_rule / §5.6.6.3 / L4 / evidence=6
- Airflow Sensor Calibration Alarm

Duplicates:
- `ko_b4e606430d007373` L4 evidence=5 - VAV Reheat Zone – Airflow Sensor Calibration Alarm

### Group 4

Keep: `ko_299d7274bf02aa45` ahu / fault_diagnostic_rule / §5.6.6.5 / L4 / evidence=2
- VAV Reheat Zone – Leaking Valve Alarm

Duplicates:
- `ko_7374603b46d475d5` L4 evidence=2 - Leaking Valve Alarm

### Group 5

Keep: `ko_86bbc0a34ec16597` ahu / operational_sequence / §5.16.2.2 / L3 / evidence=1
- Supply Air Temperature Setpoint Reset

Duplicates:
- `ko_4436778f785f5638` L3 evidence=1 - Multiple-Zone VAV AHU – Supply Air Temperature Setpoint Reset (Occupied/Setup)
- `ko_d8e1162b7ada1c07` L3 evidence=1 - Supply Air Temperature Setpoint Reset (Occupied/Setup)

### Group 6

Keep: `ko_b5e5eee2717ff3e4` ahu / operational_sequence / §5.16.2.2 / L3 / evidence=1
- Multiple-Zone VAV AHU – SAT Setpoint in Warmup/Setback Mode

Duplicates:
- `ko_7b725cdb75c142da` L3 evidence=1 - Multiple-Zone VAV AHU – SAT Setpoint in Cooldown Mode

### Group 7

Keep: `ko_93d230d5b4e82055` ahu / operational_sequence / §5.16.4.4 / L4 / evidence=2
- Minimum Outdoor Air Control Enable/Disable (Separate Damper, DP, Return Fan)

Duplicates:
- `ko_925c5d4df42a9333` L4 evidence=2 - Minimum Outdoor Air Control Enable/Disable (Separate Damper, DP Control, Return Fan)

### Group 8

Keep: `ko_da1929f3739b18e6` ahu / operational_sequence / §5.18.4 / L3 / evidence=1
- Single-Zone VAV AHU Supply Fan Speed and SAT Setpoint Reset

Duplicates:
- `ko_03f1a70f702efbb0` L3 evidence=1 - Single-Zone VAV AHU – Supply Fan Speed and SAT Control
- `ko_9948b1b650718ae0` L3 evidence=1 - SZVAV AHU Supply Fan Speed and SAT Setpoint Reset

### Group 9

Keep: `ko_05ad27d8db52c268` ahu / operational_sequence / §5.18.6.2 / L3 / evidence=1
- Single-Zone VAV AHU Minimum Outdoor Air Control (Without AFMS)

Duplicates:
- `ko_dc309853b5ce2124` L3 evidence=1 - SZVAV AHU Minimum Outdoor Air Control without AFMS

### Group 10

Keep: `ko_eb5573fe04421c86` ahu / operational_sequence / §5.8.5.1.d / L3 / evidence=1
- Parallel Fan Start/Stop for Ventilation (Title 24)

Duplicates:
- `ko_24a60d10a580cf49` L3 evidence=1 - Parallel Fan Start/Stop for Ventilation (ASHRAE 62.1)

### Group 11

Keep: `ko_3b924e63065c9d64` chiller / fault_diagnostic_rule / §5.20.18.6 / L3 / evidence=1
- CHW Plant – FC#6: Chilled Water Supply Temperature Too High

Duplicates:
- `ko_80b887a27bf38854` L3 evidence=1 - AFDD – Chilled Water Supply Temperature Too High

### Group 12

Keep: `ko_fb78f73ab2472072` chiller / fault_diagnostic_rule / §5.20.18.6 / L3 / evidence=1
- CHW Plant – FC#8: Condenser Approach Too High

Duplicates:
- `ko_ed34327dd6c6c391` L3 evidence=1 - AFDD – Evaporator Approach Too High
- `ko_f576867d97db0da9` L3 evidence=1 - AFDD – Condenser Approach Too High

### Group 13

Keep: `ko_05f5732fd2bb2b08` chiller / operational_sequence / §5.20.2.2 / L3 / evidence=2
- Chilled Water Plant Enable Logic

Duplicates:
- `ko_aaf4be54f82b2100` L3 evidence=1 - Chiller Plant Enable Logic

### Group 14

Keep: `ko_8cb0a403097c0189` chiller / operational_sequence / §5.20.2.3 / L3 / evidence=1
- Chiller Plant Disable Logic

Duplicates:
- `ko_e0511a7fcbdbd6bd` L3 evidence=1 - Chilled Water Plant Disable Logic

### Group 15

Keep: `ko_197d9d04fccd1dba` chiller / operational_sequence / §5.20.4.15 / L4 / evidence=4
- Chiller Stage Up – Availability Condition

Duplicates:
- `ko_1716f9779bdb98ae` L4 evidence=3 - Chiller Stage Down – Efficiency Condition
- `ko_6207ca3927455605` L4 evidence=4 - Chiller Staging – Stage Up Efficiency Condition
- `ko_f66dce37fefd74bf` L4 evidence=4 - Chiller Stage Up – Efficiency Condition
- `ko_f9622e405a6dd1bb` L4 evidence=3 - Chiller Staging – Stage Down Condition

### Group 16

Keep: `ko_525cb177e9a3237f` chiller / operational_sequence / §5.20.5.2 / L3 / evidence=1
- Chilled Water Supply Temperature Reset (DP Controlled Loops)

Duplicates:
- `ko_cef31b83a98c1e22` L3 evidence=1 - Chilled Water Supply Temperature Reset – Differential Pressure Controlled Loops

### Group 17

Keep: `ko_aa719e9412cf1ccf` hot_water_plant / fault_diagnostic_rule / §5.21.11.6 / L3 / evidence=1
- HW Plant – FC#8: Return Temperature Too High for Condensing

Duplicates:
- `ko_38f5562445088806` L3 evidence=1 - HW Plant – FC#9: Return Temperature Too Low (Condensing Risk)

### Group 18

Keep: `ko_cd318fe602e8a59f` hot_water_plant / operational_sequence / §5.21.2.2 / L3 / evidence=2
- Hot Water Plant Enable Logic

Duplicates:
- `ko_7d1d86608cf4abb7` L3 evidence=1 - Boiler Plant Enable Logic

### Group 19

Keep: `ko_4787dcde08ab167f` hot_water_plant / operational_sequence / §5.21.2.3 / L3 / evidence=1
- Boiler Plant Disable Logic

Duplicates:
- `ko_0eb3b69e0dc25363` L3 evidence=1 - Hot Water Plant Disable Logic

### Group 20

Keep: `ko_479e3f64bd68fe16` hot_water_plant / operational_sequence / §5.21.3.9 / L4 / evidence=2
- Boiler Stage Up – Efficiency Condition (Non-Condensing)

Duplicates:
- `ko_0037e3539cb25e49` L3 evidence=1 - Boiler Stage Down – Efficiency Condition (Condensing)
- `ko_aa76266f1d189904` L3 evidence=1 - Boiler Stage Up – Efficiency Condition (Condensing)
- `ko_e7fdd9316692857f` L3 evidence=1 - Boiler Stage Down – Efficiency Condition (Non-Condensing)

### Group 21

Keep: `ko_384a0b5c8ff7e2ea` hot_water_plant / operational_sequence / §5.21.3.9.g / L3 / evidence=1
- Primary Only Condensing Boiler Staging Down

Duplicates:
- `ko_1f43deb051fcb35a` L3 evidence=1 - Non-Condensing Boiler Staging Down

