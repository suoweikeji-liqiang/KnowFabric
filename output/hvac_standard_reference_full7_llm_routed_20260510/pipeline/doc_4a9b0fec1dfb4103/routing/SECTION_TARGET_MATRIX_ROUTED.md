# LLM Routed Section Matrix

- Document: `ASHRAE手册2024.pdf`
- Doc ID: `doc_4a9b0fec1dfb4103`
- Backend: `deepseek-parameter-spec`
- Document family: `design_handbook`
- Document lane: `system_design`
- Default equipment anchor: `general_hvac`
- Equipment pipeline: `True`

| Section | Pages | Topic | Goal | Extract | Anchor | Allowed Types | Reason |
|---|---:|---|---|---|---|---|---|
| Heating, Ventilating, | 1-1 | - | - | None | - | - |  |
| DEDICATED TO THE ADV ANCEMENT OF | 2-2 | - | - | None | - | - |  |
| ASHRAE TECHNICAL COMMITTEES, TASK GROUPS, AND | 3-5 | unknown | system_topic_reference | False | general_hvac | application_guidance | List of technical committees, no actionable content. |
| CONTENTS | 6-6 | - | - | None | - | - |  |
| HEATING EQUIPMENT AND COMPONENTS | 7-7 | - | - | None | - | - |  |
| HV AC SYSTEM ANALYSIS AND SELECTION | 8-8 | general_hvac_design | system_design | True | general_hvac | application_guidance | Chapter on HVAC system analysis and selection, providing design guidance. |
| ®, ENERGYSTAR®, etc.) | 9-9 | - | - | None | - | - |  |
| HVAC System Analysis and Selection | 10-12 | - | - | None | - | - |  |
| Primary Equipment | 13-13 | - | - | None | - | - |  |
| HVAC System Analysis and Selection | 14-17 | general_hvac_design | system_design | True | general_hvac | application_guidance | Continuation of system analysis and selection, including equipment room location. |
| DECENTRALIZED COOLING AND HEATING | 18-28 | - | - | None | - | - |  |
| BIBLIOGRAPHY | 29-29 | - | - | None | - | - |  |
| CENTRAL COOLING AND HEATING PLANTS | 30-36 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Chapter on central cooling and heating plants, covers system design and equipment. |
| 5. SOUND, VIBRATION, SEISMIC, AND WIND | 37-37 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section on sound, vibration, seismic, and wind considerations in central plant design. |
| Central Cooling and Heating Plants | 38-41 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section covers central plant design, including equipment room layout and code compliance. |
| AIR HANDLING AND DISTRIBUTION | 42-48 | - | - | None | - | - |  |
| Pa. High-efficiency, low-pressure louvers that effectively limit | 49-49 | - | - | None | - | - |  |
| Air Handling and Distribution | 50-52 | air_distribution | system_design | True | ahu | application_guidance, parameter_spec | Section on air handling and distribution, includes filter requirements and mixing. |
| 2. AIR-HANDLING SYSTEMS | 53-53 | air_distribution | system_design | True | ahu | application_guidance, operational_sequence | Section on air-handling systems, describes single-duct constant volume systems. |
| Air Handling and Distribution | 54-60 | - | - | None | - | - |  |
| BUILDING SYSTEM COMMISSIONING | 61-61 | general_hvac_design | system_design | True | general_hvac | application_guidance, maintenance_procedure | Section on building system commissioning, includes service space requirements. |
| IN-ROOM TERMINAL SYSTEMS | 62-66 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Chapter on in-room terminal systems, covers system characteristics and components. |
| Two-Pipe Nonchangeover with Full Electric Strip Heat. This | 67-67 | general_hvac_design | system_design | True | general_hvac | application_guidance | Subsection on two-pipe nonchangeover with electric strip heat, discusses energy conservati |
| In-Room Terminal Systems | 68-68 | - | - | None | - | - |  |
| 6. VARIABLE-REFRIGERANT-FLOW (VRF) | 69-69 | - | - | None | - | - |  |
| In-Room Terminal Systems | 70-70 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Subsection on in-room terminal systems, covers chilled beam selection and wiring. |
| Types and Location | 71-71 | - | - | None | - | - |  |
| In-Room Terminal Systems | 72-74 | - | - | None | - | - |  |
| Changeover Temperature Considerations | 75-75 | general_hvac_design | system_design | True | general_hvac | parameter_spec, operational_sequence | Subsection on changeover temperature considerations, includes parameter specifications. |
| In-Room Terminal Systems | 76-77 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Subsection on zoning for two-pipe systems, provides application guidance. |
| RADIANT HEATING AND COOLING | 78-78 | - | - | None | - | - |  |
| HEAT TRANSFER | 79-79 | - | - | None | - | - |  |
| Radiant Heating and Cooling | 80-96 | - | - | None | - | - |  |
| Sensible Cooling Controls | 97-97 | - | - | None | - | - |  |
| Radiant Heating and Cooling | 98-98 | - | - | None | - | - |  |
| COMBINED HEAT AND POWER SYSTEMS | 99-101 | - | - | None | - | - |  |
| LOAD PROFILING AND PRIME | 102-102 | - | - | None | - | - |  |
| Combined Heat and Power Systems | 103-107 | general_hvac_design | system_design | True | general_hvac | application_guidance | Combined heat and power systems design guidance. |
| RECIPROCATING ENGINES | 108-108 | - | - | None | - | - |  |
| Combined Heat and Power Systems | 109-117 | - | - | None | - | - |  |
| PERFORMANCE CHARACTERISTICS | 118-118 | - | - | None | - | - |  |
| Combined Heat and Power Systems | 119-119 | - | - | None | - | - |  |
| Noise and Vibration | 120-120 | general_hvac_design | system_design | True | general_hvac | application_guidance, maintenance_procedure | Subsection on noise and vibration, includes maintenance and application guidance. |
| Combined Heat and Power Systems | 121-121 | - | - | None | - | - |  |
| 5. THERMAL-TO-POWER | 122-122 | general_hvac_design | system_design | True | general_hvac | application_guidance, parameter_spec | Subsection on thermal-to-power components, includes parameter specifications. |
| Combined Heat and Power Systems | 123-129 | - | - | None | - | - |  |
| Performance Characteristics | 130-130 | general_hvac_design | system_design | True | general_hvac | parameter_spec, operational_sequence | Subsection on performance characteristics of Stirling engines, includes parameters. |
| Combined Heat and Power Systems | 131-131 | - | - | None | - | - |  |
| HEAT RECOVERY | 132-132 | general_hvac_design | system_design | True | general_hvac | application_guidance, maintenance_procedure | Subsection on heat recovery from reciprocating engines, includes maintenance guidance. |
| Combined Heat and Power Systems | 133-139 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Section on combined heat and power systems, covers design and operational guidance. |
| Thermal Loads | 140-140 | general_hvac_design | system_design | True | general_hvac | application_guidance | Thermal loads discussion for heat recovery design. |
| Combined Heat and Power Systems | 141-151 | - | - | None | - | - |  |
| Analysis by Simulations | 152-152 | - | - | None | - | - |  |
| Combined Heat and Power Systems | 153-154 | - | - | None | - | - |  |
| COMBUSTION TURBINE INLET COOLING | 155-164 | - | - | None | - | - |  |
| APPLIED HEAT PUMP AND HEAT RECOVERY SYSTEMS | 165-169 | - | - | None | - | - |  |
| Heat Source | 170-170 | - | - | None | - | - |  |
| Applied Heat Pump and Heat Recovery Systems | 171-190 | - | - | None | - | - |  |
| SMALL FORCED-AIR HEATING AND COOLING SYSTEMS | 191-191 | - | - | None | - | - |  |
| Heating and Cooling Units | 192-192 | - | - | None | - | - |  |
| Small Forced-Air Heating and Cooling Systems | 193-204 | - | - | None | - | - |  |
| STEAM SYSTEMS | 205-211 | - | - | None | - | - |  |
| Thermostatic Traps | 212-212 | valve_control | equipment_operational | True | boiler | application_guidance, parameter_spec | Thermostatic traps for steam systems, related to valve control. |
| Steam Systems | 213-213 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Steam systems design guidance, not specific to a single equipment type. |
| 12. PRESSURE-REDUCING VALVES | 214-214 | valve_control | equipment_operational | True | boiler | application_guidance, parameter_spec | Pressure-reducing valves for steam systems. |
| Steam Systems | 215-217 | - | - | None | - | - |  |
| 16. TEMPERATURE CONTROL | 218-218 | - | - | None | - | - |  |
| Steam Systems | 219-221 | general_hvac_design | system_design | True | general_hvac | parameter_spec, performance_spec | Steam system sizing and pressure differential calculations for design. |
| DISTRICT HEATING AND COOLING | 222-248 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | District heating and cooling system master planning and central plant design. |
| DISTRIBUTION SYSTEM CONSTRUCTION | 249-249 | - | - | None | - | - |  |
| District Heating and Cooling | 250-250 | - | - | None | - | - |  |
| Standards: AWWA C300, AWWA C301, AWWA C302, | 251-251 | - | - | None | - | - |  |
| District Heating and Cooling | 252-271 | - | - | None | - | - |  |
| HYDRONIC HEATING AND COOLING | 272-282 | - | - | None | - | - |  |
| PIPING CIRCUITS | 283-283 | general_hvac_design | system_design | True | general_hvac | parameter_spec, application_guidance | Piping circuit design including tank and pressure considerations. |
| Hydronic Heating and Cooling | 284-290 | - | - | None | - | - |  |
| Two-Pipe Systems | 291-291 | - | - | None | - | - |  |
| Hydronic Heating and Cooling | 292-292 | general_hvac_design | system_design | True | general_hvac | parameter_spec, operational_sequence | Hydronic heating and cooling system control sequences and valve types. |
| Air Elimination | 293-293 | - | - | None | - | - |  |
| Hydronic Heating and Cooling | 294-294 | general_hvac_design | system_design | True | general_hvac | application_guidance, fault_diagnostic_rule | Temperature measurement points and troubleshooting guidance for hydronic systems. |
| Freeze Prevention | 295-295 | general_hvac_design | system_design | True | general_hvac | performance_spec, application_guidance | Freeze prevention design for circulating water systems. |
| Hydronic Heating and Cooling | 296-297 | - | - | None | - | - |  |
| CONDENSER WATER SYSTEMS | 298-300 | - | - | None | - | - |  |
| 3. LOW-TEMPERATURE | 301-301 | cooling_tower | equipment_operational | True | cooling_tower | performance_spec, operational_sequence | Low-temperature cooling tower operation and freeze protection. |
| MEDIUM- AND HIGH-TEMPERATURE WATER HEATING | 302-302 | boiler | system_design | True | boiler | parameter_spec, performance_spec | Medium- and high-temperature water heating system design. |
| 2. BASIC SYSTEM | 303-303 | - | - | None | - | - |  |
| Medium- and High-Temperature Water Heating | 304-309 | - | - | None | - | - |  |
| INFRARED RADIANT HEATING | 310-312 | - | - | None | - | - |  |
| 3. SYSTEM EFFICIENCY | 313-313 | general_hvac_design | system_design | True | general_hvac | application_guidance | System efficiency indicators for infrared radiant heating. |
| Infrared Radiant Heating | 314-316 | - | - | None | - | - |  |
| REFERENCES | 317-317 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | References section, general guidance. |
| GERMICIDAL ULTRAVIOLET LAMP SYSTEMS | 318-324 | - | - | None | - | - |  |
| 4. UV-C LEDS | 325-325 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | UV-C LEDs application in HVAC, general topic. |
| Germicidal Ultraviolet Lamp Systems | 326-328 | - | - | None | - | - |  |
| PET, s = (4) | 329-329 | - | - | None | - | - |  |
| Germicidal Ultraviolet Lamp Systems | 330-333 | - | - | None | - | - |  |
| V ARIABLE REFRIGERANT FLOW | 334-335 | - | - | None | - | - |  |
| Variable Refrigerant Flow | 336-336 | general_hvac_design | system_design | True | general_hvac | performance_spec, application_guidance | Variable refrigerant flow system cost and life expectancy comparison. |
| 2. EQUIPMENT | 337-337 | general_hvac_design | system_design | True | general_hvac | parameter_spec, performance_spec | VRF equipment types and performance parameters. |
| Variable Refrigerant Flow | 338-338 | - | - | None | - | - |  |
| Heating Operation | 339-339 | - | - | None | - | - |  |
| Variable Refrigerant Flow | 340-340 | - | - | None | - | - |  |
| High-Heating-Performan ce Air-Source VRF Units | 341-341 | - | - | None | - | - |  |
| Variable Refrigerant Flow | 342-344 | general_hvac_design | system_design | True | general_hvac | performance_spec, application_guidance | VRF system performance characteristics and application guidance. |
| Integrated Method | 345-345 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Integrated method for outdoor air pretreatment with VRF. |
| Variable Refrigerant Flow | 346-348 | - | - | None | - | - |  |
| DUCT CONSTRUCTION | 349-355 | - | - | None | - | - |  |
| Round, Flat Oval, and Rectangular Ducts | 356-356 | - | - | None | - | - |  |
| Duct Construction | 357-359 | - | - | None | - | - |  |
| 10. RIGID PLASTIC DUCTS | 360-360 | - | - | None | - | - |  |
| Duct Construction | 361-363 | - | - | None | - | - |  |
| ROOM AIR DISTRIBUTION EQUIPMENT | 364-364 | - | - | None | - | - |  |
| 2. SYSTEM CLASSIFICATIONS | 365-365 | - | - | None | - | - |  |
| Room Air Distribution Equipment | 366-368 | - | - | None | - | - |  |
| GRILLES | 369-369 | air_distribution | system_design | True | general_hvac | application_guidance, performance_spec | Grille selection and placement for air distribution. |
| Room Air Distribution Equipment | 370-370 | - | - | None | - | - |  |
| Supply Air Diff user Accessories | 371-371 | - | - | None | - | - |  |
| Room Air Distribution Equipment | 372-374 | - | - | None | - | - |  |
| FAN-COIL UNITS | 375-375 | ahu | equipment_operational | True | ahu | application_guidance | Fan-coil units, a type of air handling unit. |
| Room Air Distribution Equipment | 376-381 | - | - | None | - | - |  |
| FANS | 382-382 | - | - | None | - | - |  |
| Type Impeller Design Housing DesignCentrifugal Fans | 383-383 | - | - | None | - | - |  |
| Performance Curves* Performance Characteristics Applications | 384-384 | air_distribution | equipment_operational | True | general_hvac | application_guidance, performance_spec | Fan performance curves and characteristics for air distribution. |
| Type Impeller Design Housing DesignCross-flow | 385-385 | - | - | None | - | - |  |
| Performance Curves* Performance Characteristics Applications | 386-386 | - | - | None | - | - |  |
| 3. TESTING AND RATING | 387-392 | - | - | None | - | - |  |
| 12. SERIES FAN OPERATION | 393-393 | air_distribution | equipment_operational | True | general_hvac | application_guidance | Series fan operation guidance. |
| 15. ARRANGEMENT AND INSTALLATION | 394-398 | - | - | None | - | - |  |
| Final Report .BIBLIOGRAPHY | 399-399 | - | - | None | - | - |  |
| HUMIDIFIERS | 400-406 | general_hvac_design | system_design | True | general_hvac | parameter_spec, application_guidance | Humidifier selection and application guidance. |
| Residential Humidifiers for Central Air Systems | 407-412 | - | - | None | - | - |  |
| Selecting Humidifiers | 413-413 | - | - | None | - | - |  |
| 5. CONTROLS | 414-418 | - | - | None | - | - |  |
| AIR-COOLING AND DEHUMIDIFYING COILS | 419-435 | ahu | equipment_operational | True | ahu | application_guidance, performance_spec, parameter_spec | Air-cooling and dehumidifying coils, key AHU component. |
| DESICCANT DEHUMIDIFICATION AND | 436-437 | desiccant_system | system_design | True | desiccant_system | parameter_spec, performance_spec | Desiccant dehumidification equipment and performance. |
| Desiccant Dehumidification and Pressure-Drying Equipment | 438-450 | - | - | None | - | - |  |
| EQUIPMENT TYPES | 451-451 | - | - | None | - | - |  |
| Desiccant Dehumidification and Pressure-Drying Equipment | 452-452 | - | - | None | - | - |  |
| MECHANICAL DEHUMIDIFIERS AND | 453-454 | desiccant_system | equipment_operational | True | general_hvac | application_guidance | Mechanical dehumidifiers and related components. |
| Mechanical Dehumidifiers and Related Components | 455-455 | - | - | None | - | - |  |
| General-Purpose Dehumidifiers | 456-456 | desiccant_system | equipment_operational | True | general_hvac | application_guidance | General-purpose dehumidifiers. |
| Mechanical Dehumidifiers and Related Components | 457-459 | general_hvac_design | system_design | True | general_hvac | performance_spec, application_guidance | Mechanical dehumidifiers and DX-DOAS units. |
| Industrial Dehumidifiers | 460-460 | - | - | None | - | - |  |
| Mechanical Dehumidifiers and Related Components | 461-464 | desiccant_system | equipment_operational | True | general_hvac | application_guidance | Section covers mechanical dehumidifiers, related to desiccant systems. |
| BIBLIOGRAPHY | 465-465 | - | - | None | - | - |  |
| AIR-TO-AIR ENERGY RECOVERY EQUIPMENT | 466-474 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section covers air-to-air energy recovery equipment, a general HVAC design topic. |
| Heat Pipe Heat Exchangers | 475-475 | - | - | None | - | - |  |
| Air-to-Air Energy Recovery Equipment | 476-476 | general_hvac_design | system_design | True | general_hvac | application_guidance | Continuation of air-to-air energy recovery equipment. |
| Thermosiphon Heat Exchangers | 477-477 | - | - | None | - | - |  |
| Air-to-Air Energy Recovery Equipment | 478-488 | - | - | None | - | - |  |
| 6. COMPARISON OF AIR-TO-AIR HEAT OR HEAT | 489-489 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec, performance_spec | Comparison of air-to-air heat exchangers characteristics. |
| Air-to-Air Energy Recovery Equipment | 490-504 | - | - | None | - | - |  |
| AIR-HEATING COILS | 505-509 | - | - | None | - | - |  |
| UNIT VENTILATORS, UNIT HEATERS, | 510-510 | - | - | None | - | - |  |
| Fig. 1 Typical Unit Ventilators | 511-511 | - | - | None | - | - |  |
| Unit Ventilators, Unit Heaters, and Makeup Air Units | 512-512 | - | - | None | - | - |  |
| 2. UNIT HEATERS | 513-513 | - | - | None | - | - |  |
| Unit Ventilators, Unit Heaters, and Makeup Air Units | 514-519 | - | - | None | - | - |  |
| AIR CLEANERS FOR PARTICULATE CONTAMINANTS | 520-526 | - | - | None | - | - |  |
| General Ventilation (HV AC) Testing | 527-527 | - | - | None | - | - |  |
| Air Cleaners for Particulate Contaminants | 528-530 | - | - | None | - | - |  |
| Antimicrobial Treatment of Filter Media | 531-531 | - | - | None | - | - |  |
| Air Cleaners for Particulate Contaminants | 532-535 | - | - | None | - | - |  |
| AIR POLLUTION CONTROL AND | 536-537 | - | - | None | - | - |  |
| Air Pollution Control and Industrial Process Cleaning | 538-539 | - | - | None | - | - |  |
| Operation Concentration Particle Size CycloneHigh | 540-540 | - | - | None | - | - |  |
| HV AC Applications (SI)Table 3 Collectors Used in Industry ( Continued ) | 541-541 | - | - | None | - | - |  |
| Air Pollution Control and Industrial Process Cleaning | 542-552 | - | - | None | - | - |  |
| 3. GASEOUS CONTAMINANT | 553-553 | - | - | None | - | - |  |
| Air Pollution Control and Industrial Process Cleaning | 554-556 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section covers air pollution control and industrial process cleaning, general HVAC design. |
| V = TGMvC1A (13) | 557-557 | - | - | None | - | - |  |
| Air Pollution Control and Industrial Process Cleaning | 558-566 | - | - | None | - | - |  |
| AUTOMATIC FUEL-BURNING SYSTEMS | 567-583 | - | - | None | - | - |  |
| STOKER TYPES BY FUEL-FEED METHODS | 584-584 | - | - | None | - | - |  |
| Automatic Fuel-Burning Systems | 585-585 | - | - | None | - | - |  |
| 5. CONTROLS | 586-586 | boiler | equipment_operational | True | boiler | application_guidance | Section discusses controls for boilers and stokers. |
| Automatic Fuel-Burning Systems | 587-589 | boiler | equipment_operational | True | boiler | application_guidance, parameter_spec, operational_sequence | Section discusses automatic fuel-burning systems, including limit controls for boilers. |
| BOILERS | 590-593 | - | - | None | - | - |  |
| Electric Boilers | 594-594 | - | - | None | - | - |  |
| Fuel-Fired Boilers | 595-596 | - | - | None | - | - |  |
| Water Level Controls | 597-597 | - | - | None | - | - |  |
| FURNACES | 598-598 | - | - | None | - | - |  |
| Heat Sources | 599-600 | boiler | equipment_operational | True | boiler | application_guidance | Section covers heat sources for furnaces, related to boilers. |
| Indoor/Outdoor Fu rnace Variations | 601-601 | - | - | None | - | - |  |
| 3. COMMERCIAL EQUIPMENT | 602-603 | boiler | equipment_operational | True | boiler | application_guidance | Section covers commercial furnace equipment, related to boilers. |
| Equipment Sizing | 604-607 | - | - | None | - | - |  |
| RESIDENTIAL IN-SPACE HEATING EQUIPMENT | 608-612 | - | - | None | - | - |  |
| Fireplace Inserts | 613-613 | - | - | None | - | - |  |
| Residential In-Space Heating Equipment | 614-614 | - | - | None | - | - |  |
| CHIMNEY, VENT, AND FIREPLACE SYSTEMS | 615-625 | - | - | None | - | - |  |
| K rise, Dt = 131 Pa. | 626-626 | - | - | None | - | - |  |
| Chimney, Vent, and Fireplace Systems | 627-647 | - | - | None | - | - |  |
| AGA Standard Z223.1-2015. National Fire Protection Association, | 648-648 | - | - | None | - | - |  |
| HYDRONIC HEAT-DISTRIBUTING UNITS | 649-650 | - | - | None | - | - |  |
| Hydronic Heat-Distributing Units and Radiators | 651-653 | - | - | None | - | - |  |
| REFERENCES | 654-654 | - | - | None | - | - |  |
| SOLAR ENERGY EQUIPMENT AND SYSTEMS | 655-655 | - | - | None | - | - |  |
| MWp of PV power was installed globally, corresponding to 1 | 656-656 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section discusses PVT modules, a general HVAC design topic. |
| Solar Energy Equipment and Systems | 657-669 | - | - | None | - | - |  |
| HEAT EXCHANGERS | 670-670 | - | - | None | - | - |  |
| Solar Energy Equipment and Systems | 671-671 | - | - | None | - | - |  |
| Differential Temperature Controllers | 672-672 | - | - | None | - | - |  |
| Solar Energy Equipment and Systems | 673-677 | - | - | None | - | - |  |
| REFERENCES | 678-678 | - | - | None | - | - |  |
| Solar Energy Equipment and Systems | 679-679 | - | - | None | - | - |  |
| COMPRESSORS | 680-681 | chiller | equipment_operational | True | chiller | application_guidance | Section covers compressors, key component of chillers. |
| Actual Compressor | 682-683 | - | - | None | - | - |  |
| Suction and Discharge Pulsations | 684-687 | - | - | None | - | - |  |
| Performance Data | 688-690 | - | - | None | - | - |  |
| Special Devices | 691-691 | - | - | None | - | - |  |
| 3. ROTARY COMPRESSORS | 692-698 | - | - | None | - | - |  |
| Twin-Screw Compressors | 699-706 | - | - | None | - | - |  |
| Energy Efficiency | 707-707 | - | - | None | - | - |  |
| Noise and Vibration | 708-709 | chiller | equipment_operational | True | chiller | application_guidance | Section covers noise and vibration in compressors, related to chillers. |
| Development Status and Performance | 710-712 | - | - | None | - | - |  |
| Mach Number | 713-718 | - | - | None | - | - |  |
| Oil-Free Centrifugal Compressors | 719-723 | chiller | equipment_operational | True | chiller | application_guidance, performance_spec, maintenance_procedure | Section covers oil-free centrifugal compressors, a key chiller component. |
| CONDENSERS | 724-725 | cooling_tower | equipment_operational | True | cooling_tower | application_guidance | Section covers condensers, related to cooling towers. |
| Refrigerant-Side F ilm Coefficient | 726-726 | - | - | None | - | - |  |
| Tube-Wall Resistance | 727-727 | - | - | None | - | - |  |
| WATER PRESSURE DROP | 728-730 | - | - | None | - | - |  |
| MPa (gage), and the desi gn temperature does not exceed | 731-737 | cooling_tower | equipment_operational | True | cooling_tower | application_guidance | Continuation of condenser section, related to cooling towers. |
| HEAT TRANSFER | 738-743 | - | - | None | - | - |  |
| COOLING TOWERS | 744-764 | - | - | None | - | - |  |
| Counterflow Integration | 765-765 | - | - | None | - | - |  |
| Cooling Towers | 766-769 | - | - | None | - | - |  |
| EV APORATIVE AIR-COOLING EQUIPMENT | 770-771 | - | - | None | - | - |  |
| Evaporative Air-Cooling Equipment | 772-776 | - | - | None | - | - |  |
| High-Velocity Spray-Type Air Washers | 777-777 | - | - | None | - | - |  |
| Evaporative Air-Cooling Equipment | 778-780 | - | - | None | - | - |  |
| REFERENCES | 781-781 | - | - | None | - | - |  |
| Evaporative Air-Cooling Equipment | 782-783 | - | - | None | - | - |  |
| LIQUID COOLERS | 784-788 | - | - | None | - | - |  |
| Oil Return | 789-789 | - | - | None | - | - |  |
| LIQUID-CHILLING SYSTEMS | 790-790 | chiller | equipment_operational | True | chiller | application_guidance | Section covers liquid-chilling systems, directly related to chillers. |
| Multiple-Chiller Systems | 791-791 | chiller | equipment_operational | True | chiller | application_guidance | Section covers multiple-chiller systems. |
| Liquid-Chilling Systems | 792-792 | - | - | None | - | - |  |
| CONTROL | 793-793 | - | - | None | - | - |  |
| Liquid-Chilling Systems | 794-796 | - | - | None | - | - |  |
| 3. CENTRIFUGAL LIQUID CHILLERS | 797-797 | - | - | None | - | - |  |
| Liquid-Chilling Systems | 798-804 | - | - | None | - | - |  |
| SPECIAL APPLICATIONS | 805-805 | - | - | None | - | - |  |
| CENTRIFUGAL PUMPS | 806-808 | - | - | None | - | - |  |
| Vertical In-Line Pump | 809-809 | - | - | None | - | - |  |
| Centrifugal Pumps | 810-816 | - | - | None | - | - |  |
| Duty Standby | 817-817 | pump | equipment_operational | True | pump | application_guidance | Section covers duty standby pumping systems. |
| Centrifugal Pumps | 818-818 | - | - | None | - | - |  |
| Variable-Speed Central Pumping | 819-819 | - | - | None | - | - |  |
| Centrifugal Pumps | 820-820 | - | - | None | - | - |  |
| 15. ENERGY CONSERV ATION IN PUMPING | 821-821 | - | - | None | - | - |  |
| Centrifugal Pumps | 822-823 | - | - | None | - | - |  |
| MOTORS, MOTOR CONTROLS, AND | 824-825 | - | - | None | - | - |  |
| Motors, Motor Controls, and Variable-Frequency Drives | 826-830 | - | - | None | - | - |  |
| Direct-Current Motor Starting | 831-831 | - | - | None | - | - |  |
| Motors, Motor Controls, and Variable-Frequency Drives | 832-832 | - | - | None | - | - |  |
| Detecting Bearing Currents | 833-833 | - | - | None | - | - |  |
| Strategies for Mitigating Bearing Currents | 834-837 | - | - | None | - | - |  |
| Power Transistor Characteristics | 838-838 | - | - | None | - | - |  |
| Motor Ratings and NEMA Standards | 839-839 | pump | equipment_operational | True | pump | application_guidance | Section covers motor ratings and NEMA standards for pumps. |
| Motor Noise and Drive Carrier Frequencies | 840-844 | - | - | None | - | - |  |
| VA LV E S | 845-846 | - | - | None | - | - |  |
| 2. MANUAL V ALVES | 847-848 | - | - | None | - | - |  |
| Balancing Valve Selection | 849-849 | - | - | None | - | - |  |
| Butterfly Valves | 850-851 | - | - | None | - | - |  |
| Control of Automatic Valves | 852-857 | valve_control | equipment_operational | True | valve_control | application_guidance | Section covers control of automatic valves. |
| Makeup Water Valves | 858-859 | - | - | None | - | - |  |
| HEAT EXCHANGERS | 860-862 | - | - | None | - | - |  |
| Double-Wall Heat Exchangers | 863-863 | - | - | None | - | - |  |
| Heat Exchangers | 864-865 | - | - | None | - | - |  |
| UNITARY AIR CONDITIONERS AND HEAT PUMPS | 866-870 | - | - | None | - | - |  |
| Engine-Driven Heat Pumps and Air Conditioners | 871-871 | - | - | None | - | - |  |
| Unitary Air Conditioners and Heat Pumps | 872-874 | - | - | None | - | - |  |
| Add-On Heat Pumps | 875-875 | - | - | None | - | - |  |
| Unitary Air Conditioners and Heat Pumps | 876-880 | - | - | None | - | - |  |
| ROOM AIR CONDITIONERS AND PACKAGED | 881-882 | - | - | None | - | - |  |
| Room Air Conditioners and Packaged Terminal Air Conditioners | 883-885 | - | - | None | - | - |  |
| SIZES AND CLASSIFICATIONS | 886-886 | - | - | None | - | - |  |
| Room Air Conditioners and Packaged Terminal Air Conditioners | 887-887 | - | - | None | - | - |  |
| PERFORMANCE AND SAFETY TESTING | 888-888 | - | - | None | - | - |  |
| THERMAL STORAGE | 889-897 | - | - | None | - | - |  |
| 2. LATENT COOL STORAGE TECHNOLOGY | 898-898 | - | - | None | - | - |  |
| Thermal Storage | 899-915 | - | - | None | - | - |  |
| Ice (and PCM) Storage Systems | 916-916 | - | - | None | - | - |  |
| Thermal Storage | 917-929 | - | - | None | - | - |  |
| DEDICATED OUTDOOR AIR SYSTEMS | 930-932 | - | - | None | - | - |  |
| SUPPLY TO INTAKE OF LOCAL UNITS | 933-933 | - | - | None | - | - |  |
| Dedicated Outdoor Air Systems | 934-934 | - | - | None | - | - |  |
| ELECTRIFICATION | 935-935 | - | - | None | - | - |  |
| Dedicated Outdoor Air Systems | 936-936 | - | - | None | - | - |  |
| CODES AND STANDARDS | 937-937 | - | - | None | - | - |  |
| Air Con | 938-938 | - | - | None | - | - |  |
| Codes and Standards | 939-939 | - | - | None | - | - |  |
| Fired Steam Generators ASME ASME PTC 4-2013 | 940-940 | - | - | None | - | - |  |
| Codes and Standards | 941-941 | - | - | None | - | - |  |
| Hermetic Refrigerant Motor-Compressors UL/CSA UL 984-1996/C22.2 No.140.2-96 | 942-942 | - | - | None | - | - |  |
| Codes and Standards | 943-943 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section lists codes and standards relevant to HVAC design. |
| Dehumidifiers Commercial Systems Overview ACCA ACCA Manual CS-1993 | 944-944 | - | - | None | - | - |  |
| Codes and Standards | 945-945 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section covers codes and standards for duct systems. |
| SystemsAIHA ANSI/AIHA Z9.2-2012 | 946-946 | - | - | None | - | - |  |
| Codes and Standards | 947-947 | - | - | None | - | - |  |
| Refrigeration Equipment CSA CAN/CSA-C22.2 No. 120-13 | 948-948 | - | - | None | - | - |  |
| Codes and Standards | 949-949 | - | - | None | - | - |  |
| Gas-Fired Pool Heaters CSA ANSI Z21.56-2014/CSA 4.7-2014 | 950-950 | - | - | None | - | - |  |
| Codes and Standards | 951-953 | - | - | None | - | - |  |
| Test Uncertainty ASME ASME PTC 19.1-2013 | 954-954 | - | - | None | - | - |  |
| Codes and Standards | 955-955 | - | - | None | - | - |  |
| General Welding Guidelines (2009) NCPWB NCPWB | 956-956 | - | - | None | - | - |  |
| Codes and Standards | 957-957 | general_hvac_design | system_design | True | general_hvac | application_guidance | Section covers codes and standards for pumps and piping. |
| Use in Mobile Air-Conditioning SystemsSAE SAE J2099-2012 | 958-958 | - | - | None | - | - |  |
| Codes and Standards | 959-959 | - | - | None | - | - |  |
| MeasurementsASA ANSI/ASA S1.6-1984 (R2011) | 960-960 | - | - | None | - | - |  |
| Codes and Standards | 961-961 | - | - | None | - | - |  |
| LP-Gas Regulators UL ANSI/UL 144-2012 | 962-962 | - | - | None | - | - |  |
| Codes and Standards | 963-963 | - | - | None | - | - |  |
| Solid-Fuel-Fired Central Heating Appliances CSA CAN/CSA-B366.1-11 | 964-964 | - | - | None | - | - |  |
| Codes and Standards | 965-965 | - | - | None | - | - |  |
| SMACNA Sheet Metal and Air Conditioning Contractors’ | 966-966 | - | - | None | - | - |  |
| Additions and Corrections | 967-967 | - | - | None | - | - |  |
| I.1COMPOSITE INDEX | 968-968 | - | - | None | - | - |  |
| outdoor, S2.9refrigeration, S3.4 | 969-969 | - | - | None | - | - |  |
| Composite Index I.3 | 970-971 | - | - | None | - | - |  |
| Composite Index I.5 | 972-972 | - | - | None | - | - |  |
| Cavitation , F3.13 | 973-973 | - | - | None | - | - |  |
| Composite Index I.7 | 974-974 | - | - | None | - | - |  |
| gas, S31.20oil, S31.11 | 975-975 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section is an index, provides topic reference. |
| Composite Index I.9 | 976-977 | unknown | system_topic_reference | False | general_hvac | application_guidance | Composite index page, no actionable content. |
| Composite Index I.11 | 978-978 | - | - | None | - | - |  |
| Brayton cycle, R47.11 | 979-979 | - | - | None | - | - |  |
| Composite Index I.13 | 980-981 | - | - | None | - | - |  |
| Composite Index I.15 | 982-983 | - | - | None | - | - |  |
| Composite Index I.17 | 984-985 | - | - | None | - | - |  |
| Composite Index I.19 | 986-987 | - | - | None | - | - |  |
| Composite Index I.21 | 988-989 | unknown | system_topic_reference | False | general_hvac | application_guidance | Composite index, not suitable for extraction. |
| Composite Index I.23 | 990-991 | unknown | system_topic_reference | False | general_hvac | application_guidance | Composite index page, no actionable content. |
| Composite Index I.25 | 992-992 | - | - | None | - | - |  |
| Mold , A64.1; F25.16 | 993-993 | - | - | None | - | - |  |
| Composite Index I.27 | 994-994 | - | - | None | - | - |  |
| control, A49.51transmission, A39.37 | 995-995 | unknown | system_topic_reference | False | general_hvac | application_guidance | Index page, not suitable for extraction. |
| Composite Index I.29 | 996-996 | - | - | None | - | - |  |
| Refrigerants , F29.1 | 997-997 | - | - | None | - | - |  |
| Composite Index I.31 | 998-999 | unknown | system_topic_reference | False | general_hvac | application_guidance | Composite index page, no actionable content. |
| Composite Index I.33 | 1000-1001 | unknown | system_topic_reference | False | general_hvac | application_guidance | Composite index page, no actionable content. |
| Composite Index I.35 | 1002-1003 | - | - | None | - | - |  |
| Composite Index I.37 | 1004-1004 | - | - | None | - | - |  |
| capacity, S28.3control, A48.17; S28.3location, S28.1selection, S28.1types, S28.1 | 1005-1005 | unknown | system_topic_reference | False | general_hvac | application_guidance | Index page, no actionable content. |
| Composite Index I.39 | 1006-1006 | - | - | None | - | - |  |
