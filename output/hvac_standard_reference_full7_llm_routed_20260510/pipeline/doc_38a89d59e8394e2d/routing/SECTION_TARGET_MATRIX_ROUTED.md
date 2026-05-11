# LLM Routed Section Matrix

- Document: `ASHRAE绿色建筑指南.pdf`
- Doc ID: `doc_38a89d59e8394e2d`
- Backend: `deepseek-parameter-spec`
- Document family: `cross_domain_sustainability_guide`
- Document lane: `sustainability_topic`
- Default equipment anchor: `general_hvac`
- Equipment pipeline: `False`

| Section | Pages | Topic | Goal | Extract | Anchor | Allowed Types | Reason |
|---|---:|---|---|---|---|---|---|
| pages_1 | 1-5 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Front matter, no technical content |
| C O N TE N TS | 6-15 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Table of contents, no extractable knowledge |
| A CKN OWLEDGMEN TS | 16-19 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Acknowledgments, no technical content |
| I N TR O D U C TI O N | 20-31 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Introduction, general overview |
| 5 C H AP TE R TW O | 32-32 | sustainability_general | system_topic_reference | False | general_hvac | performance_spec | Chapter 2 intro, green rating systems overview |
| C E R TI F I C ATI O N | 33-36 | sustainability_general | system_topic_reference | False | general_hvac | performance_spec | Voluntary green building rating systems, general info |
| “ P HI US +. ” | 37-37 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Passive House standard mention, no actionable detail |
| LE E D | 38-41 | sustainability_general | system_topic_reference | False | general_hvac | performance_spec | LEED description, general reference |
| S I TE S | 42-58 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Site strategies, general sustainability |
| NG B ank | 59-74 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Project strategies, early design, general |
| G A : A S H RA E | 75-79 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Reference list, no extractable knowledge |
| O VE RVI E W | 80-120 | sustainability_general | system_topic_reference | False | general_hvac | application_guidance | Overview of architect's role, general |
| C O N | 121-146 | general_hvac_design | system_design | True | general_hvac | maintenance_procedure | Conceptual engineering design, load determination, includes maintenance considerations |
| C O N S | 147-150 | sustainability_general | out_of_scope | False | none | - | Section covers sustainable sites and erosion control, not HVAC equipment or design. |
| SOU RCES OF FU RTH ER I N FO RMATI ON | 151-151 | sustainability_general | out_of_scope | False | none | - | Section is a list of further information sources, not technical content. |
| I N TR O D U C TI O N | 152-203 | sustainability_general | out_of_scope | False | none | - | Section introduces indoor environmental quality, general sustainability topic. |
| P R O | 204-204 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section discusses VRF systems, pros and cons, application guidance. |
| C O N | 205-209 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section continues VRF system discussion, limitations and applications. |
| (D O AS s ) | 210-210 | air_distribution | system_design | True | ahu | application_guidance, parameter_spec | Section covers Dedicated Outdoor Air Systems (DOAS), design and ventilation requirements. |
| P R O | 211-222 | air_distribution | system_design | True | ahu | application_guidance | Section continues DOAS pros, energy savings, IAQ compliance. |
| C O N | 223-225 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section discusses fuel utilization and emissions reduction, general HVAC topic. |
| P R O | 226-227 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section covers thermal efficiency and CO2 emissions, pros and cons. |
| C O N | 228-239 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section discusses limitations of certain heating systems, material constraints. |
| P R O | 240-241 | boiler | system_topic_reference | True | boiler | application_guidance | Section mentions district steam and fuel flexibility, boiler-related. |
| GE N E RAL D E SCRI P TI O N | 242-243 | desiccant_system | system_design | True | general_hvac | application_guidance | Desiccant cooling and dehumidification general description |
| P RO | 244-252 | desiccant_system | equipment_operational | True | general_hvac | parameter_spec, maintenance_procedure, application_guidance, operational_sequence | Pros and cons of desiccant equipment, includes operational and maintenance info |
| C O N | 253-268 | general_hvac_design | system_design | True | general_hvac | performance_spec | Energy use conversion and distribution systems, performance specs |
| WI N D | 269-279 | sustainability_general | out_of_scope | False | none | - | Section covers wind energy, renewable energy source, not HVAC equipment. |
| O VE R VI E W | 280-307 | sustainability_general | out_of_scope | False | none | - | Section covers sustainable lighting design, not HVAC. |
| WATE R- E N E R G Y N E XU S | 308-329 | sustainability_general | out_of_scope | False | none | - | Section covers water-energy nexus, general sustainability topic. |
| P R O | 330-334 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section discusses point-of-use hot water devices, pros and energy savings. |
| C O N | 335-343 | chiller | system_topic_reference | True | chiller | application_guidance | Section mentions district cooling and satellite chillers, condensate issues. |
| NOAA. Global Historical Climate Network Daily.  | 344-345 | sustainability_general | out_of_scope | False | none | - | Section is a list of further information sources, not technical content. |
| 2 9 C H A P TE R TH I R TE E N | 346-353 | sustainability_general | out_of_scope | False | none | - | Section introduces smart building systems, IoT, general topic. |
| S MAR T H ARD WAR E | 354-372 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section discusses smart hardware, CO2 sensors, AFDD, HVAC-related. |
| P E R F O R MA N C E | 373-384 | general_hvac_design | system_design | True | general_hvac | performance_spec | Residential applications, performance specs |
| F U TU R E TR E N D S | 385-397 | sustainability_general | out_of_scope | False | none | - | Section covers future trends in residential green building, not specific HVAC. |
| 0 b e c aus e i t i s no r | 398-403 | unknown | out_of_scope | False | none | - | Scrambled text, no meaningful content. |
| 8 7 C H A P TE R F I F TE E N | 404-410 | audit_process | audit_methodology | True | general_hvac | application_guidance | Chapter on existing buildings, discusses audits and retrofits. |
| 4E l e c t r i c a l p e a k | 411-421 | general_hvac_design | system_design | True | general_hvac | application_guidance | Discusses electrical peak shaving and load shifting via BAS/EMCS. |
| 0 5 C H A P TE R S I X TE E N | 422-429 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Chapter on emerging trends and climate change. |
| 1 3 AP P E N D I X | 430-430 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Appendix with building-type-specific green tips. |
| 4  A p p e n d i x | 431-432 | air_distribution | system_design | True | general_hvac | application_guidance | Discusses underfloor air distribution (UFAD) for performing arts spaces. |
| 6  A p p e n d i x | 433-434 | air_distribution | system_design | True | general_hvac | application_guidance | Mentions UFAD and heat recovery strategies. |
| 8  A p p e n d i x | 435-436 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Discusses sustainable options for healthcare facilities. |
| 0  Ap p e n d i x | 437-438 | sustainability_general | system_topic_reference | False | general_hvac | performance_spec | Appendix, health costs, general sustainability |
| 2  Ap p e n d i x | 439-440 | general_hvac_design | system_design | True | general_hvac | application_guidance | Discusses energy recovery and VAV systems. |
| 4  Ap p e n d i x | 441-442 | unknown | out_of_scope | False | none | - | References to FGI guidelines, not HVAC-specific. |
| 6  Ap p e n d i x | 443-444 | general_hvac_design | system_design | True | general_hvac | application_guidance | Discusses fail-safe operation, full/part-load efficiency, and energy recovery. |
| 8  Ap p e n d i x | 445-446 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Appendix on student residence halls, general description. |
| 0  Ap p e n d i x | 447-448 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Appendix on athletic and recreation facilities. |
| 2  Ap p e n d i x | 449-450 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Appendix on commercial office buildings. |
| 4  Ap p e n d i x | 451-452 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Appendix on K-12 school buildings. |
| 6  Ap p e n d i x | 453-454 | general_hvac_design | system_design | True | general_hvac | application_guidance | Discusses data centers, energy-intensive, mentions IT equipment. |
| 8  Ap p e n d i x | 455-459 | sustainability_general | system_topic_reference | True | general_hvac | application_guidance | Discusses electronic equipment and environmental requirements. |
| 4 3 R E F E RE N C E S | 460-474 | unknown | out_of_scope | False | none | - | References section, no actionable HVAC content. |
| (B RE EAM ® | 475-481 | sustainability_general | system_topic_reference | False | general_hvac | performance_spec | References and resources, BREEAM mention |
| AN D A C R O N YMS | 482-485 | sustainability_general | system_topic_reference | False | general_hvac | parameter_spec | Terms, definitions, acronyms, reference only |
| 6 9 I N D E X | 486-494 | unknown | out_of_scope | False | none | - | Index, no extractable content. |
