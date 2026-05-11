# LLM Routed Section Matrix

- Document: `ASHRAE手册 - 基础理论篇.pdf`
- Doc ID: `doc_2a7ec347e5f44d9e`
- Backend: `deepseek-parameter-spec`
- Document family: `standard_reference`
- Document lane: `system_design`
- Default equipment anchor: `general_hvac`
- Equipment pipeline: `True`

| Section | Pages | Topic | Goal | Extract | Anchor | Allowed Types | Reason |
|---|---:|---|---|---|---|---|---|
| Table 1 Standard Atmospheric Data for Altitudes to 10 000 m | 7-7 | - | - | None | - | - |  |
| Table 2 Thermodynamic Properties of Moist Air at Standard Atmospheric Pressure,  | 8-10 | - | - | None | - | - |  |
| Table 3 Thermodynamic Properties of Water at Saturation | 11-16 | - | - | None | - | - |  |
| Fig. 1 ASHRAE Psychrometric Chart No. 1 | 17-17 | - | - | None | - | - |  |
| Fig. 3 Schematic Solution for Example 2 | 18-18 | - | - | None | - | - |  |
| Fig. 6 Adiabatic Mixing of Two Moist Airstreams | 19-19 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Adiabatic mixing of moist airstreams, providing performance specs for psychrometric proces |
| Fig. 9 Schematic Solution for Example 5 | 20-20 | - | - | None | - | - |  |
| Fig. 11 Schematic Solution for Example 6 | 21-21 | - | - | None | - | - |  |
| Table 4 Calculated Diffusion Coefficients for Water/Air at 101.325 kPa | 22-23 | - | - | None | - | - |  |
| Fig. 1 Energy Flows in General Thermodynamic System | 24-28 | - | - | None | - | - |  |
| Fig. 4 Azeotropic Behavior Shown on T-x Diagram | 29-29 | - | - | None | - | - |  |
| Fig. 7 Carnot Vapor Compression Cycle | 30-30 | chiller | system_topic_reference | True | chiller | performance_spec | Section describes Carnot vapor compression cycle, fundamental to chiller performance. |
| Table 1 Thermodynamic Property Data for Example 2 | 31-31 | - | - | None | - | - |  |
| Fig. 11 Processes of Lorenz Refrigeration Cycle | 32-32 | chiller | system_design | True | chiller | performance_spec | Lorenz refrigeration cycle diagram, providing performance specs for chiller cycle analysis |
| Fig. 12 Areas on T-s Diagram Representing Refrigerating Effect and Work Supplied | 33-33 | chiller | system_design | True | chiller | performance_spec | T-s diagram for zeotropic refrigerant cycle, providing performance specs for chiller desig |
| Table 2 Thermodynamic Property Values for Example 4 | 34-34 | - | - | None | - | - |  |
| Table 3 Measured and Computed Thermodynamic Properties of R-22 for Example 5 | 35-35 | chiller | system_design | True | chiller | performance_spec | Measured and computed thermodynamic properties of R-22, providing performance specs for ch |
| Table 4 Energy Transfers and Irreversibility Rates for Refrigeration System in E | 36-36 | chiller | system_topic_reference | True | chiller | performance_spec | Section provides energy transfers and irreversibility rates for refrigeration system, rele |
| Fig. 17 Single-Effect Absorption Cycle | 37-38 | chiller | system_design | True | chiller | performance_spec | Single-effect absorption cycle diagram, providing performance specs for chiller design. |
| Table 5 Refrigerant/Absorbent Pairs | 39-39 | - | - | None | - | - |  |
| Fig. 20 Single-Effect Water/Lithium Bromide Absorption Cycle Dühring Plot | 40-40 | - | - | None | - | - |  |
| Table 8 Simulation Results for Single-Effect Water/Lithium Bromide Absorption Ch | 41-41 | - | - | None | - | - |  |
| Table 9 Inputs and Assumptions for Double-Effect Water-Lithium Bromide Model (Fi | 42-42 | - | - | None | - | - |  |
| Table 12 State Point Data for Single-Effect Ammonia/Water Cycle (Figure 22) | 43-45 | chiller | system_design | True | chiller | performance_spec | State point data for ammonia/water cycle, providing performance specs for chiller analysis |
| Fig. 1 Velocity Profiles and Gradients in Shear Flows | 46-47 | - | - | None | - | - |  |
| Fig. 3 Velocity Fluctuation at Point in Turbulent Flow | 48-48 | - | - | None | - | - |  |
| Fig. 8 Geometric Separation, Flow Development, and Loss in Flow Through Orifice | 49-49 | - | - | None | - | - |  |
| Table 1 Drag Coefficients | 50-50 | - | - | None | - | - |  |
| Fig. 12 Blower and Duct System for Example 1 | 51-51 | - | - | None | - | - |  |
| Fig. 13 Relation Between Friction Factor and Reynolds Number | 52-52 | - | - | None | - | - |  |
| Table 3 Fitting Loss Coefficients of Turbulent Flow | 53-53 | - | - | None | - | - |  |
| Fig. 14 Diagram for Example 2 | 54-54 | - | - | None | - | - |  |
| Fig. 18 Differential Pressure Flowmeters | 55-55 | valve_control | system_design | True | general_hvac | operational_sequence | Differential pressure flowmeters and control damper operation, providing operational seque |
| Fig. 19 Flowmeter Coefficients | 56-56 | - | - | None | - | - |  |
| Fig. 20 Temporal Increase in Velocity Following Sudden Application of Pressure | 57-57 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section discusses temporal increase in velocity following sudden application of pressure,  |
| Fig. 21 Cavitation in Flows in Orifice or Valve | 58-60 | - | - | None | - | - |  |
| Table 1 Heat Transfer Coefficients by Convection Type | 61-61 | - | - | None | - | - |  |
| Fig. 2 Interface Resistance Across Two Layers | 62-62 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Interface resistance across layers, providing performance specs for heat transfer in build |
| Table 2 One-Dimensional Conduction Shape Factors | 63-63 | - | - | None | - | - |  |
| Fig. 5 Efficiency of Annular Fins of Constant Thickness | 64-64 | - | - | None | - | - |  |
| Table 3 Multidimensional Conduction Shape Factors | 65-65 | - | - | None | - | - |  |
| Fig. 8 Efficiency of Four Types of Spines | 66-66 | - | - | None | - | - |  |
| Fig. 9 Rectangular Tube Array | 67-68 | - | - | None | - | - |  |
| Table 4 Values of C1 and U1 in Equations (14) to (17) | 69-69 | - | - | None | - | - |  |
| Fig. 12 Transient Temperatures for Infinite Cylinder, m = 1/Bi | 70-70 | - | - | None | - | - |  |
| Fig. 14 Solid Cylinder Exposed to Fluid | 71-72 | - | - | None | - | - |  |
| Table 5 Emissivities and Absorptivities of Some Surfaces | 73-73 | - | - | None | - | - |  |
| Fig. 16 Diagram for Example 8 | 74-75 | - | - | None | - | - |  |
| Table 7 Emissivity of Moist Air and CO2 in Typical Room | 76-76 | - | - | None | - | - |  |
| Fig. 19 Boundary Layer Build-up in Entrance Region of Tube or Channel | 77-77 | - | - | None | - | - |  |
| Table 8 Forced-Convection Correlations | 78-78 | - | - | None | - | - |  |
| Fig. 21 Heat Transfer Coefficient for Turbulent Flow of Water Inside Tubes | 79-79 | - | - | None | - | - |  |
| Table 9 Natural Convection Correlations | 80-80 | - | - | None | - | - |  |
| Fig. 23 Diagram for Example 12 | 81-82 | - | - | None | - | - |  |
| Table 10 Equations for Computing Heat Exchanger Effectiveness, N = NTU | 83-83 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Equations for heat exchanger effectiveness, providing performance specs for heat exchanger |
| Fig. 25 Plate Parameters | 84-84 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Plate parameters for heat exchangers, providing parameter specs for design. |
| Table 11 Single-Phase Heat Transfer and Pressure Drop Correlations for Plate Exc | 85-85 | - | - | None | - | - |  |
| Fig. 27 Typical Tube-Side Enhancements | 86-86 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Typical tube-side enhancements, providing parameter specs for heat exchanger design. |
| Fig. 29 Enhanced Surfaces for Gases | 87-87 | - | - | None | - | - |  |
| Table 12 Equations for Augmented Forced Convection (Single Phase) | 88-88 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Equations for augmented forced convection are fundamental heat transfer correlations used  |
| Table 15 Worldwide Status of Active Techniques | 89-89 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Status of active techniques provides application guidance for heat transfer enhancement in |
| Table 17 Selected Studies on Rotation | 90-90 | - | - | None | - | - |  |
| Table 18 Selected Previous Work with EHD Enhancement of Single-Phase Heat Transf | 91-96 | - | - | None | - | - |  |
| Fig. 1 Characteristic Pool Boiling Curve | 97-97 | - | - | None | - | - |  |
| Fig. 3 Correlation of Pool Boiling Data in Terms of Reduced Pressure | 98-98 | - | - | None | - | - |  |
| Table 1 Equations for Natural Convection Boiling Heat Transfer | 99-100 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Natural convection boiling heat transfer equations are performance specs for two-phase flo |
| Table 2 Correlations for Local Heat Transfer Coefficients in Horizontal Tube Bun | 101-101 | - | - | None | - | - |  |
| Fig. 5 Flow Regimes in Typical Smooth Horizontal Tube Evaporator | 102-102 | - | - | None | - | - |  |
| Table 3 Equations for Forced Convection Boiling in Tubes | 103-104 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Forced convection boiling equations are performance specs for heat exchangers in HVAC. |
| Fig. 7 Film Boiling Correlation | 105-107 | - | - | None | - | - |  |
| Table 4 Heat Transfer Coefficient/Nusselt Number Correlations for Film-Type Cond | 108-109 | - | - | None | - | - |  |
| Fig. 8 Origin of Noncondensable Resistance | 110-110 | - | - | None | - | - |  |
| Table 5 Constants in Equation (29d) for Different Void Fraction Correlations | 111-112 | - | - | None | - | - |  |
| Fig. 9 Qualitative Pressure Drop Characteristics of Two-Phase Flow Regime | 113-113 | - | - | None | - | - |  |
| Table 6 Constant and Exponents in Correlation of Lee and Lee (2001) | 114-114 | - | - | None | - | - |  |
| Fig. 11 Schematic Flow Representation of a Typical Force- Fed Microchannel Heat  | 115-115 | - | - | None | - | - |  |
| Fig. 12 Thermal Performance Comparison of Different High-Heat-Flux Cooling Techn | 116-116 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Thermal performance comparison of cooling technologies provides performance data for HVAC  |
| Fig. 13 Scanning Electron Microscope Images of Various Nanostructures: (A) Silic | 117-122 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section covers two-phase flow and nanostructures, relevant to advanced HVAC design. |
| CHAPTER 6: MASS TRANSFER | 123-123 | - | - | None | - | - |  |
| Table 1 Mass Diffusivities for Gases in Air* | 124-124 | - | - | None | - | - |  |
| Fig. 1 Diffusion of Water Vapor Through Stagnant Air | 125-125 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Diffusion of water vapor through air is a parameter spec for mass transfer in HVAC. |
| Fig. 3 Equimolar Counterdiffusion | 126-126 | - | - | None | - | - |  |
| Table 2 Material Values for Example 4 | 127-127 | - | - | None | - | - |  |
| Fig. 6 Nomenclature for Convective Mass Transfer from Internal Surface Impermeab | 128-128 | - | - | None | - | - |  |
| Fig. 7 Water-Saturated Flat Plate in Flowing Airstream | 129-129 | - | - | None | - | - |  |
| Fig. 9 Vaporization and Absorption in Wetted-Wall Column | 130-130 | - | - | None | - | - |  |
| Fig. 12 Sensible Heat Transfer j-Factors for Parallel Plate Exchanger | 131-132 | - | - | None | - | - |  |
| Fig. 14 Air Washer Humidification Process on Psychrometric Chart | 133-133 | - | - | None | - | - |  |
| Fig. 15 Graphical Solution for Air-State Path in Parallel-Flow Air Washer | 134-134 | - | - | None | - | - |  |
| Fig. 17 Graphical Solution for Air-State Path in Dehumidifying Coil with Constan | 135-137 | - | - | None | - | - |  |
| Fig. 1 Example of Feedback Control: Discharge Air Temperature Control | 138-138 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Feedback control example illustrates operational sequence for discharge air temperature co |
| Fig. 4 Two-Position Control | 139-139 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Two-position control is a fundamental control operational sequence. |
| Fig. 6 Proportional plus Integral (PI) Control | 140-140 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Proportional plus integral control is a key operational sequence for modulating control. |
| Fig. 7 Floating Control Showing Variations in Controlled Variable as Load Change | 141-141 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Floating control variations with load changes is an operational sequence. |
| Fig. 9 Typical Single- and Double-Seated Two-Way Globe Valves | 142-142 | valve_control | system_topic_reference | True | general_hvac | application_guidance | Section describes single- and double-seated two-way globe valves, directly relevant to val |
| Fig. 12 Typical Multiblade Dampers | 143-143 | general_hvac_design | system_topic_reference | True | general_hvac | maintenance_procedure | Multiblade dampers section includes maintenance procedure for dampers. |
| Fig. 14 Inherent Curves for Partially Ducted and Louvered Dampers (RP-1157) | 144-144 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Inherent curves for dampers describe operational sequence for damper control. |
| Fig. 15 Inherent Curves for Ducted and Plenum-Mounted Dampers (RP-1157) | 145-148 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Inherent curves for ducted and plenum-mounted dampers provide application guidance. |
| Fig. 16 Dead-Band Thermostat | 149-149 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Dead-band thermostat is an operational sequence for temperature control. |
| Fig. 18 Retrofit of Existing Pneumatic Control with Electronic Sensors and Contr | 150-151 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Retrofit of pneumatic control with electronic sensors is an operational sequence. |
| Fig. 19 OSI Reference Model | 152-152 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | OSI reference model is part of control system operational sequence. |
| Fig. 20 Hierarchical Network for Three-Tier System Architecture | 153-153 | - | - | None | - | - |  |
| Table 1 Comparison of Fiber Optic Technology | 154-154 | valve_control | system_topic_reference | True | general_hvac | application_guidance | Section discusses twisted-pair copper cable and telecommunications outlets, which are rela |
| Table 2 Some Standard Communication Protocols Applicable to BAS | 155-156 | - | - | None | - | - |  |
| Fig. 23 Response of Discharge Air Temperature to Step Change in Set Points at Va | 157-159 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec, operational_sequence | Section provides controller tuning parameters and procedures, relevant to HVAC control des |
| Table 1 Typical Sound Pressures and Sound Pressure Levels | 160-160 | - | - | None | - | - |  |
| Table 2 Examples of Sound Power Outputs and Sound Power Levels | 161-161 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Section provides sound power outputs and levels, relevant to HVAC acoustic design. |
| Table 3 Combining Two Sound Levels | 162-163 | - | - | None | - | - |  |
| Table 6 Combining Decibels to Determine Overall Sound Pressure Level | 164-164 | - | - | None | - | - |  |
| Table 7 Guidelines for Determining Equipment Sound Levels in the Presence of Con | 165-170 | - | - | None | - | - |  |
| Fig. 3 Contour for Determining Partition’s STC | 171-172 | - | - | None | - | - |  |
| Fig. 4 Free-Field Equal Loudness Contours for Pure Tones | 173-173 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Section discusses free-field equal loudness contours, relevant to HVAC acoustic performanc |
| Table 8 Subjective Effect of Changes in Sound Pressure Level, Broadband Sounds ( | 174-174 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Subjective effect of sound pressure level changes is a performance spec for acoustics. |
| Fig. 7 NC (Noise Criteria) Curves and Sample Spectrum (Curve with Symbols) | 175-175 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | NC curves and sample spectrum provide performance criteria for noise control. |
| Fig. 9 Vibration Transmissibility T as Function of fd / fn | 176-176 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Vibration transmissibility as function of frequency ratio provides application guidance fo |
| Fig. 11 Two-Degrees-of-Freedom System | 177-177 | - | - | None | - | - |  |
| Fig. 13 Transmissibility T as Function of fd/fn1 with k2/k1 = 10 and M2/M1 = 40 | 178-180 | - | - | None | - | - |  |
| CHAPTER 9: THERMAL COMFORT | 181-181 | - | - | None | - | - |  |
| Fig. 1 Thermal Interaction of Human Body and Environment | 182-184 | - | - | None | - | - |  |
| Table 3 Skin Heat Loss Equations | 185-185 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Skin heat loss equations are parameter specs for thermal comfort analysis. |
| Table 4 Typical Metabolic Heat Generation for Various Activities | 186-186 | - | - | None | - | - |  |
| Table 5 Heart Rate and Oxygen Consumption at Different Activity Levels | 187-187 | - | - | None | - | - |  |
| Table 7 Typical Insulation and Permeability Values for Western Clothing Ensemble | 188-188 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Table of insulation and permeability values for clothing ensembles is a parameter spec for |
| Table 9 Garment Insulation Values | 189-190 | - | - | None | - | - |  |
| Fig. 3 Mean Value of Angle Factor Between Seated Person and Horizontal or Vertic | 191-191 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Angle factor values for seated person are parameter specs for thermal comfort calculations |
| Table 10 Equations for Predicting Thermal Sensation Y of Men, Women, and Men and | 192-192 | - | - | None | - | - |  |
| Fig. 7 Predicted Rate of Unsolicited Thermal Operating Complaints | 193-193 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Predicted rate of thermal complaints is a performance spec for comfort evaluation. |
| Table 11 Model Parameters | 194-194 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Section provides model parameters for building maintenance and space temperature, relevant |
| Fig. 9 Percentage of People Expressing Discomfort Caused by Asymmetric Radiation | 195-195 | - | - | None | - | - |  |
| Fig. 12 Percentage of Seated People Dissatisfied as Function of Air Temperature  | 196-196 | air_distribution | system_topic_reference | True | general_hvac | application_guidance | Section discusses vertical air temperature difference and occupant dissatisfaction, releva |
| Fig. 13 Percentage of People Dissatisfied as Function of Floor Temperature | 197-197 | - | - | None | - | - |  |
| Fig. 15 Air Temperatures and Mean Radiant Temperatures Necessary for Comfort (PM | 198-198 | - | - | None | - | - |  |
| Fig. 16 Predicted Percentage of Dissatisfied (PPD) as Function of Predicted Mean | 199-200 | - | - | None | - | - |  |
| Fig. 18 Effect of Thermal Environment on Discomfort | 201-201 | - | - | None | - | - |  |
| Table 12 Evaluation of Heat Stress Index | 202-202 | - | - | None | - | - |  |
| Fig. 20 Recommended Heat Stress Exposure Limits for Heat Acclimatized Workers | 203-203 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Heat stress exposure limits are parameter specs for safety design. |
| Table 13 Equivalent Wind Chill Temperatures of Cold Environments | 204-204 | - | - | None | - | - |  |
| Fig. 23 Thermal Inertias of Excised, Bloodless, and Normal Living Skin | 205-205 | - | - | None | - | - |  |
| Fig. 24 Recommended Temperature Set Points for HVAC with PEC Systems and Energy  | 206-206 | - | - | None | - | - |  |
| Fig. 25 Schematic Design of Heat Stress and Heat Disorders | 207-207 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Schematic design of heat stress includes parameter specs for physiological limits. |
| Fig. 26 Acclimatization to Heat Resulting from Daily Exposure of Five Subjects t | 208-213 | - | - | None | - | - |  |
| CHAPTER 10: INDOOR ENVIRONMENTAL HEALTH | 214-214 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Chapter on indoor environmental health provides operational sequences for health-based des |
| Table 1 Selected Illnesses Related to Exposure in Buildings | 215-217 | general_hvac_design | system_topic_reference | True | general_hvac | symptom | Table of illnesses related to building exposure provides symptom knowledge. |
| Table 2 OSHA Permissible Exposure Limits (PELs) for Particlesa | 218-219 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | OSHA PELs for particles are parameter specs for air quality design. |
| Table 3 Primary and Secondary Standards for Particle Pollution | 220-222 | - | - | None | - | - |  |
| Table 4 Pathogens with Potential for Airborne Transmission | 223-224 | - | - | None | - | - |  |
| Table 5 Comparison of Indoor Environment Standards and Guidelines | 225-225 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Comparison of indoor environment standards provides parameter specs. |
| Table 6 Selected SVOCs Found in Indoor Environments | 226-226 | - | - | None | - | - |  |
| Table 7 Indoor Concentrations and Body Burden of Selected Semivolatile Organic C | 227-228 | - | - | None | - | - |  |
| Table 8 Inorganic Gas Comparative Criteria | 229-229 | - | - | None | - | - |  |
| Fig. 1 Related Human Sensory, Physiological, and Health Responses for Prolonged  | 230-230 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Human sensory and health responses figure is a performance spec for comfort. |
| Fig. 2 Isotherms for Comfort, Discomfort, Physiological Strain, Effective Temper | 231-231 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Isotherms for comfort and heat stroke are parameter specs. |
| Table 9 Approximate Surface Temperature Limits to Avoid Pain and Injury | 232-232 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Surface temperature limits to avoid pain are parameter specs. |
| Fig. 5 Median Perception Thresholds to Horizontal (Solid Lines) and Vertical (Da | 233-233 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Section provides vibration perception thresholds, relevant to HVAC system vibration design |
| Table 10 Ratios of Acceptable to Threshold Vibration Levels | 234-234 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Section provides ratios of acceptable to threshold vibration levels, relevant to HVAC desi |
| Table 12 2015 Action Levels for Radon Concentration Indoors | 235-235 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Radon action levels provide application guidance for indoor air quality. |
| Fig. 8 Maximum Permissible Levels of Radio Frequency Radiation for Human Exposur | 236-236 | - | - | None | - | - |  |
| 3.6 Outdoor Air Ventilation and Health | 237-243 | - | - | None | - | - |  |
| CHAPTER 11: AIR CONTAMINANTS | 244-245 | - | - | None | - | - |  |
| Fig. 2 Relative Deposition Efficiencies of Different-Sized Particles in the Thre | 246-246 | - | - | None | - | - |  |
| Table 2 Relation of Screen Mesh to Sieve Opening Size | 247-247 | - | - | None | - | - |  |
| Fig. 4 Typical Urban Outdoor Distributions of Ultrafine or Nuclei (n) Particles, | 248-249 | - | - | None | - | - |  |
| Table 3 Common Molds on Water-Damaged Building Materials | 250-250 | - | - | None | - | - |  |
| Table 4 Example Case of Airborne Fungi in Building and Outdoor Air | 251-251 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Example case of airborne fungi provides application guidance for IAQ assessment. |
| Table 5 Major Chemical Families of Gaseous Air Contaminants | 252-253 | - | - | None | - | - |  |
| Table 6 Characteristics of Selected Gaseous Air Contaminants | 254-254 | - | - | None | - | - |  |
| Table 7 Gaseous Contaminant Sample Collection Techniques | 255-255 | - | - | None | - | - |  |
| Table 8 Analytical Methods to Measure Gaseous Contaminant Concentration | 256-256 | - | - | None | - | - |  |
| Table 9 Classification of Indoor Organic Contaminants by Volatility | 257-257 | - | - | None | - | - |  |
| Table 10 VOCs Commonly Found in Buildings* | 258-259 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Table of VOCs commonly found in buildings is a performance spec for air quality. |
| Table 12 National Ambient Air Quality Standards for the United States | 260-261 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | National ambient air quality standards provide operational sequences for compliance. |
| Table 13 Sources and Indoor and Outdoor Concentrations of Selected Indoor Contam | 262-262 | - | - | None | - | - |  |
| Table 14 Flammable Limits of Some Gases and Vapors | 263-268 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Flammable limits of gases and vapors are parameter specs for safety. |
| Table 1 Odor Thresholds, ACGIH TLVs, and TLV/Threshold Ratios of Selected Gaseou | 269-271 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Odor thresholds and TLVs are parameter specs for air quality. |
| Table 2 Examples of Category Scales | 272-273 | - | - | None | - | - |  |
| Table 3 Sensory Pollution Load from Different Pollution Sources | 274-276 | - | - | None | - | - |  |
| CHAPTER 13: INDOOR ENVIRONMENTAL MODELING | 277-277 | - | - | None | - | - |  |
| Fig. 1 (A) Grid Point Distribution and (B) Control Volume Around Grid Point P | 278-279 | general_hvac_design | system_topic_reference | True | general_hvac | operational_sequence | Grid point distribution and control volume description is an operational sequence for CFD  |
| Fig. 3 Block-Structured Grid for Two-Dimensional Flow Simulation Through 90° Elb | 280-280 | - | - | None | - | - |  |
| Fig. 5 Circle Meshing | 281-281 | - | - | None | - | - |  |
| Fig. 6 Boundary Condition Locations Around Diffuser Used in Box Method | 282-282 | - | - | None | - | - |  |
| Fig. 9 Typical Velocity Distribution in Near-Wall Region | 283-283 | - | - | None | - | - |  |
| Fig. 12 Duct with Symmetry Geometry | 284-289 | - | - | None | - | - |  |
| Fig. 13 Airflow Path Diagram | 290-293 | - | - | None | - | - |  |
| Fig. 14 Floor Plan of Living Area Level of Manufactured House | 294-294 | - | - | None | - | - |  |
| Table 1 Summary of Multizone Model Validation Reports | 295-295 | - | - | None | - | - |  |
| Fig. 17 Multizone Representation of Ductwork in Belly and Crawlspace | 296-296 | - | - | None | - | - |  |
| Table 2 Leakage Values of Model Airflow Components | 297-299 | - | - | None | - | - |  |
| CHAPTER 14: CLIMATIC DESIGN INFORMATION | 300-300 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Climatic design information chapter provides performance specs for design conditions. |
| Fig. 1 Locations of Weather Stations | 301-302 | - | - | None | - | - |  |
| Table 1 Design Conditions for Atlanta, GA, USA | 303-303 | - | - | None | - | - |  |
| Table 1A Nomenclature for Tables of Climatic Design Conditions | 304-306 | - | - | None | - | - |  |
| Table 3 Time Zones in United States and Canada | 307-307 | - | - | None | - | - |  |
| Fig. 3 Solar Angles for Vertical and Horizontal Surfaces | 308-309 | - | - | None | - | - |  |
| Table 4 Surface Orientations and Azimuths, Measured from South | 310-310 | - | - | None | - | - |  |
| Table 6 Fraction of Daily Temperature Range | 311-311 | - | - | None | - | - |  |
| Table 8 Derived Hourly Temperatures for Atlanta, GA for July for 5% Design Condi | 312-312 | - | - | None | - | - |  |
| Table 9 Locations Representing Various Climate Types | 313-313 | - | - | None | - | - |  |
| Fig. 4 Uncertainty versus Period Length for Various Dry-Bulb Temperatures, by Cl | 314-314 | - | - | None | - | - |  |
| Fig. 5 Frequency and Duration of Episodes Exceeding Design Dry-Bulb Temperature  | 315-347 | - | - | None | - | - |  |
| Fig. 1 Construction Details of Typical Double-Glazing Unit | 348-349 | - | - | None | - | - |  |
| Fig. 2 Various Framing Configurations for Residential Fenestration | 350-351 | - | - | None | - | - |  |
| Fig. 3 Center-of-Glass U-Factor for Vertical Double- and Triple-Pane Glazing Uni | 352-352 | - | - | None | - | - |  |
| Table 1 Representative Fenestration Frame U-Factors in W/(m2·K), Vertical Orient | 353-353 | - | - | None | - | - |  |
| Table 2 Indoor Surface Heat Transfer Coefficient hi in W/(m2·K), Vertical Orient | 354-354 | - | - | None | - | - |  |
| Table 3 Air Space Coefficients for Horizontal Heat Flow | 355-355 | - | - | None | - | - |  |
| Table 4 U-Factors for Various Fenestration Products in W/(m2·K)i | 356-357 | - | - | None | - | - |  |
| Table 5 Glazing U-Factors for Various Wind Speeds in W/(m2·K) | 358-359 | - | - | None | - | - |  |
| Table 7 Design U-factors for Revolving Doors in W/(m2·K) | 360-360 | - | - | None | - | - |  |
| Table 9 Design U-Factors for Double-Skin Steel Sectional, Tilt-Up, and Aircraft  | 361-361 | - | - | None | - | - |  |
| Fig. 9 Normalized Solar Transmittance for Five Common Glass Substrates as Functi | 362-362 | - | - | None | - | - |  |
| Fig. 12 Spectral Transmittances and Reflectances of Strongly Spectrally Selectiv | 363-363 | - | - | None | - | - |  |
| Fig. 13 Solar Spectrum, Human Eye Response Spectrum, Scaled Blackbody Radiation  | 364-364 | - | - | None | - | - |  |
| Fig. 14 Demonstration of Two Spectrally Selective Glazing Concepts, Showing Idea | 365-366 | - | - | None | - | - |  |
| Fig. 15 Components of Solar Radiant Heat Gain with Double-Pane Fenestration, Inc | 367-368 | - | - | None | - | - |  |
| Table 10 Visible Transmittance Tv, Solar Heat Gain Coefficient (SHGC), Solar Tra | 369-376 | - | - | None | - | - |  |
| Table 11 Solar Heat Gain Coefficients for Domed Horizontal Skylights | 377-377 | - | - | None | - | - |  |
| Table 12 Performance Characteristics of Typical TDDs | 378-378 | dynamic_glazing | system_topic_reference | True | general_hvac | parameter_spec, performance_spec | Section discusses performance characteristics of tubular daylighting devices (TDDs), relev |
| Table 13 Solar Heat Gain Coefficients for Standard Hollow Glass Block Wall Panel | 379-379 | - | - | None | - | - |  |
| Fig. 18 Instantaneous Heat Balance for Sunlit Glazing Material | 380-380 | - | - | None | - | - |  |
| Fig. 20 Vertical and Horizontal Projections and Related Profile Angles for Verti | 381-382 | - | - | None | - | - |  |
| Fig. 22 Geometry of Slat-Type Sunshades | 383-383 | - | - | None | - | - |  |
| Fig. 25 Geometry of Drapery Fabrics | 384-385 | - | - | None | - | - |  |
| Table 14A IAC Values for Louvered Shades: Uncoated Single Glazings | 386-386 | - | - | None | - | - |  |
| Table 14B IAC Values for Louvered Shades: Uncoated Double Glazings | 387-388 | - | - | None | - | - |  |
| Table 14C IAC Values for Louvered Shades: Coated Double Glazings with 0.2 Low-e | 389-390 | - | - | None | - | - |  |
| Table 14D IAC Values for Louvered Shades: Coated Double Glazings with 0.1 Low-e | 391-392 | - | - | None | - | - |  |
| Table 14E IAC Values for Louvered Shades: Double Glazings with 0.05 Low-e | 393-394 | - | - | None | - | - |  |
| Table 14F IAC Values for Louvered Shades: Triple Glazing | 395-396 | - | - | None | - | - |  |
| Table 14G IAC Values for Draperies, Roller Shades, and Insect Screens | 397-399 | - | - | None | - | - |  |
| Table 15 Summary of Environmental Control Capabilities of Draperies | 400-401 | - | - | None | - | - |  |
| Fig. 27 Window-to-Wall Ratio Versus Annual Electricity Use in kWh/(m2·floor·year | 402-402 | dynamic_glazing | system_topic_reference | True | general_hvac | performance_spec | Section discusses window-to-wall ratio versus annual electricity use, relevant to fenestra |
| Fig. 29 Visible Transmittance Versus SHGC at Various Spectral Selectivities | 403-403 | - | - | None | - | - |  |
| Table 16 Spectral Selectivity of Several Glazings | 404-404 | - | - | None | - | - |  |
| Fig. 30 Temperature Distribution on Indoor Surfaces of Glazing Unit | 405-405 | - | - | None | - | - |  |
| Fig. 31 Minimum Indoor Surface Temperatures Before Condensation Occurs | 406-406 | - | - | None | - | - |  |
| Fig. 34 Fenestration Effects on Thermal Comfort: Long-Wave Radiation, Solar Radi | 407-407 | - | - | None | - | - |  |
| Table 17 Sound Transmittance Loss for Various Types of Glass | 408-415 | - | - | None | - | - |  |
| CHAPTER 16: VENTILATION AND INFILTRATION | 416-416 | - | - | None | - | - |  |
| Fig. 2 Simple All-Air Air-Handling Unit with Associated Airflows | 417-417 | - | - | None | - | - |  |
| Fig. 4 Entrainment Flow Within a Space | 418-418 | - | - | None | - | - |  |
| Fig. 5 Underfloor Air Distribution to Occupied Space Above | 419-424 | - | - | None | - | - |  |
| Fig. 7 Compartmentation Effect in Buildings | 425-428 | - | - | None | - | - |  |
| Fig. 8 Increase in Airflow by Increasing Area of One Opening | 429-429 | - | - | None | - | - |  |
| Fig. 9 Airflow Rate Versus Pressure Difference Data from Whole-House Pressurizat | 430-431 | - | - | None | - | - |  |
| Fig. 10 Envelope Leakage Measurements | 432-433 | - | - | None | - | - |  |
| Fig. 12 Histogram of Infiltration Values for Low-Income Housing | 434-436 | - | - | None | - | - |  |
| Table 3 Total Ventilation Air Requirements | 437-438 | - | - | None | - | - |  |
| Table 6 Basic Model Wind Coefficient Cw | 439-439 | - | - | None | - | - |  |
| Table 9 Enhanced Model Shelter Factor s | 440-441 | - | - | None | - | - |  |
| Table 11 Air Leakage Areas for Internal Partitions in Commercial Buildings (at 7 | 442-442 | - | - | None | - | - |  |
| Fig. 16 Pressure Factor for Automatic Doors | 443-454 | - | - | None | - | - |  |
| CHAPTER 17: RESIDENTIAL COOLING AND HEATING LOAD CALCULATIONS | 455-456 | - | - | None | - | - |  |
| Table 1 RLF Limitations | 457-458 | - | - | None | - | - |  |
| Table 2 Typical Fenestration Characteristicsa | 459-459 | - | - | None | - | - |  |
| Table 5 Typical IDF Values, L/(s·cm2) | 460-461 | - | - | None | - | - |  |
| Table 8 Roof Solar Absorptance aroof | 462-462 | - | - | None | - | - |  |
| Table 9 Peak Irradiance Equations | 463-463 | - | - | None | - | - |  |
| Table 14 Interior Attenuation Coefficients (IACcl) | 464-464 | - | - | None | - | - |  |
| Table 15 Summary of RLF Cooling Load Equations | 465-465 | - | - | None | - | - |  |
| Table 17 Example House Characteristics | 466-466 | - | - | None | - | - |  |
| Table 19 Example House Component Quantities | 467-467 | - | - | None | - | - |  |
| Table 23 Example House Total Sensible Loads | 468-470 | - | - | None | - | - |  |
| CHAPTER 18: NONRESIDENTIAL COOLING AND HEATING LOAD CALCULATIONS | 471-471 | - | - | None | - | - |  |
| Fig. 2 Thermal Storage Effect in Cooling Load from Lights | 472-473 | - | - | None | - | - |  |
| Table 1 Representative Rates at Which Heat and Moisture Are Given Off by Human B | 474-474 | - | - | None | - | - |  |
| Table 2 Lighting Power Densities Using Space-by-Space Method | 475-475 | - | - | None | - | - |  |
| Table 3 Lighting Heat Gain Parameters for Typical Operating Conditions | 476-476 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec | Section provides lighting heat gain parameters, relevant to HVAC cooling load calculation. |
| Table 4B Minimum Average Full-Load Efficiency for Polyphase Small Electric Motor | 477-477 | - | - | None | - | - |  |
| Table 5A Recommended Rates of Radiant and Convective Heat Gain from Unhooded Ele | 478-478 | - | - | None | - | - |  |
| Table 5C Recommended Rates of Radiant Heat Gain from Hooded Electric Appliances  | 479-479 | - | - | None | - | - |  |
| Table 5F Recommended Rates of Radiant and Convective Heat Gain from Warewashing  | 480-480 | - | - | None | - | - |  |
| Table 7 Recommended Heat Gain from Typical Laboratory Equipment | 481-481 | - | - | None | - | - |  |
| Table 8C Recommended Heat Gain for Typical Tablet PC | 482-482 | - | - | None | - | - |  |
| Table 9 Recommended Heat Gain for Typical Printers | 483-483 | - | - | None | - | - |  |
| Table 12 Diversity Factor for Different Equipment | 484-486 | - | - | None | - | - |  |
| Fig. 6 Schematic of Wall Conduction Process | 487-488 | - | - | None | - | - |  |
| Table 13 Single-Layer Glazing Data Produced by WINDOW 7.4.6 | 489-489 | - | - | None | - | - |  |
| Fig. 7 Schematic View of General Heat Balance Zone | 490-492 | - | - | None | - | - |  |
| Fig. 9 CTS for Light to Heavy Walls | 493-493 | - | - | None | - | - |  |
| Table 14 Recommended Radiative/Convective Splits for Internal Heat Gains | 494-494 | - | - | None | - | - |  |
| Table 15 Solar Absorptance Values of Various Surfaces | 495-495 | - | - | None | - | - |  |
| Table 16 Wall Conduction Time Series (CTS) | 496-502 | - | - | None | - | - |  |
| Table 17 Roof Conduction Time Series (CTS) | 503-506 | - | - | None | - | - |  |
| Table 18 Thermal Properties and Code Numbers of Layers Used in Wall and Roof Des | 507-507 | - | - | None | - | - |  |
| Table 20 Representative Solar RTS Values for Light to Heavy Construction | 508-508 | - | - | None | - | - |  |
| Table 22 Average U-Factor for Basement Walls with Uniform Insulation | 509-509 | - | - | None | - | - |  |
| Table 24 Heat Loss Coefficient Fp of Slab Floor Construction | 510-510 | - | - | None | - | - |  |
| Table 25 Common Sizing Calculations in Other Chapters | 511-512 | - | - | None | - | - |  |
| Fig. 15 Schematic Diagram of Typical Return Air Plenum | 513-513 | - | - | None | - | - |  |
| Fig. 16 Single-Room Example Office | 514-514 | - | - | None | - | - |  |
| Table 26 Summary of RTS Load Calculation Procedures | 515-516 | - | - | None | - | - |  |
| Table 27 Monthly/Hourly 5% Design Temperatures for Hartsfield-Jackson Atlanta In | 517-517 | - | - | None | - | - |  |
| Table 28 Cooling Load Component: Lighting, W | 518-519 | - | - | None | - | - |  |
| Table 29B Conduction: Wall Component of Sol-Air Temperatures, Heat Input, Heat G | 520-520 | - | - | None | - | - |  |
| Table 30 Window Component of Heat Gain (No Blinds or Overhang) (Month 7) | 521-521 | - | - | None | - | - |  |
| Table 31 Window Component of Cooling Load (No Blinds or Overhang) (Month 7) | 522-522 | - | - | None | - | - |  |
| Table 33 Window Component of Cooling Load (with Blinds and Overhang) (Month 7) | 523-523 | - | - | None | - | - |  |
| Table 35 Single-Room Example Peak Cooling Load (Sept.5:00 PM) for ASHRAE Example | 524-524 | - | - | None | - | - |  |
| Table 36 Block Load Example: Envelope Area Summary, m2 | 525-525 | - | - | None | - | - |  |
| Table 38 Block Load Example—Second Floor Loads for ASHRAE Example Office Buildin | 526-526 | - | - | None | - | - |  |
| Table 39 Block Load Example—Overall Building Loads for ASHRAE Example Office Bui | 527-530 | - | - | None | - | - |  |
| Fig. 17 First Floor Shell and Core Plan | 531-531 | - | - | None | - | - |  |
| Fig. 18 Second Floor Shell and Core Plan | 532-532 | - | - | None | - | - |  |
| Fig. 19 East/West Elevations, Elevation Details, and Perimeter Section | 533-533 | - | - | None | - | - |  |
| Fig. 20 First Floor Tenant Plan | 534-534 | - | - | None | - | - |  |
| Fig. 21 Second Floor Tenant Plan | 535-535 | - | - | None | - | - |  |
| Fig. 22 3D View | 536-536 | - | - | None | - | - |  |
| CHAPTER 19: ENERGY ESTIMATING AND MODELING METHODS | 537-537 | - | - | None | - | - |  |
| Fig. 1 Overall Modeling Strategy | 538-542 | - | - | None | - | - |  |
| Fig. 3 Uncounted Ventilation Degree-Hours versus Counted Cooling Degree-Hours | 543-543 | - | - | None | - | - |  |
| Table 1 Sample Annual Bin Data | 544-544 | - | - | None | - | - |  |
| Table 2 Calculation of Annual Heating Energy Consumption for Example 2 | 545-551 | - | - | None | - | - |  |
| Table 3 Correlation Coefficients for Off-Design Relationships | 552-553 | - | - | None | - | - |  |
| Fig. 7 Fan Part-Load Curve Obtained from Measured Field Data under ASHRAE RP-823 | 554-555 | - | - | None | - | - |  |
| Fig. 8 Psychrometric Schematic of Cooling Coil Processes | 556-557 | - | - | None | - | - |  |
| Fig. 9 Example Boiler Model: Efficiency as Function of Part-Load Ratio | 558-559 | - | - | None | - | - |  |
| Fig. 12 Algorithm for Calculating Performance of VAV with System Reheat | 560-561 | - | - | None | - | - |  |
| Fig. 13 Split-Flux Method | 562-562 | - | - | None | - | - |  |
| Fig. 15 Backward Ray-Tracing Method | 563-563 | - | - | None | - | - |  |
| Table 4 Single-Variate Models Applied to Utility Billing Data | 564-564 | - | - | None | - | - |  |
| Fig. 16 Steady-State, Single-Variate Models for Modeling Energy Use in Residenti | 565-569 | - | - | None | - | - |  |
| Fig. 18 Neural Network Prediction of Whole-Building, Hourly Chilled-Water Consum | 570-570 | - | - | None | - | - |  |
| Table 5 Capabilities of Different Forward and Data-Driven Modeling Methods | 571-571 | - | - | None | - | - |  |
| Table 6 Calibration Methods and Techniques | 572-572 | - | - | None | - | - |  |
| Table 7 ANSI/ASHRAE Standard 140 Validation Test Matrix | 573-573 | - | - | None | - | - |  |
| Table 8 Validation Techniques | 574-575 | - | - | None | - | - |  |
| Table 9 Types of Extrapolation | 576-577 | - | - | None | - | - |  |
| Fig. 20 Calibration Cases Conceptual Flow | 578-589 | - | - | None | - | - |  |
| Fig. 1 Classification of Air Diffusion Methods | 590-591 | - | - | None | - | - |  |
| Fig. 5 Example Airflow Patterns (Nonisothermal) of Outlet Group B | 592-592 | - | - | None | - | - |  |
| Fig. 9 Example Airflow Patterns (Nonisothermal) of Outlet Group E (High Velocity | 593-593 | - | - | None | - | - |  |
| Table 1 Generic Values for Centerline Velocity Constant Kc3a for Commercial Supp | 594-594 | - | - | None | - | - |  |
| Fig. 13 Cross-Sectional Velocity Profiles for Straight-Flow Turbulent Jets | 595-596 | - | - | None | - | - |  |
| Fig. 15 Schematic Diagram of Major Flow Elements in Room with Displacement Venti | 597-599 | - | - | None | - | - |  |
| CHAPTER 21: DUCT DESIGN | 600-600 | - | - | None | - | - |  |
| Fig. 1 Thermal Gravity Effect for Example 1 | 601-601 | - | - | None | - | - |  |
| Fig. 4 Illustrative 6-Path, 9-Section System | 602-602 | - | - | None | - | - |  |
| Fig. 5 Single Stack with Fan for Examples 3 and 4 | 603-603 | - | - | None | - | - |  |
| Fig. 7 Pressure Changes During Flow in Ducts | 604-604 | - | - | None | - | - |  |
| Fig. 8 Pressure Loss Correction Factor for Flexible Duct Not Fully Extended | 605-605 | - | - | None | - | - |  |
| Table 2 Solution for Example 6 | 606-607 | - | - | None | - | - |  |
| Fig. 10 Friction Chart for Round Duct (p = 1.20 kg/m3 and e = 0.09 mm) | 608-608 | - | - | None | - | - |  |
| Table 4 Equivalent Flat Oval Duct Dimensions* | 609-609 | - | - | None | - | - |  |
| Table 6 200 mm VAV Box Data | 610-610 | - | - | None | - | - |  |
| Table 7 ED7-2 Loss Coefficients | 611-611 | - | - | None | - | - |  |
| Fig. 16 Fitting ED7-2 (Fan Inlet, Centrifugal Fan, SISW, with 4-Gore Elbow) | 612-613 | - | - | None | - | - |  |
| Fig. 17 Comparison of Various Mechanical Equipment Room Locations | 614-614 | - | - | None | - | - |  |
| Table 8 Solution for Example 7 | 615-615 | - | - | None | - | - |  |
| Fig. 19 Criteria for Louver Sizing | 616-616 | - | - | None | - | - |  |
| Fig. 21 Maximum Airflow of Round, Flat Oval, and Rectangular Ducts as Function o | 617-617 | - | - | None | - | - |  |
| Table 9 Maximum Airflow of Round, Flat Oval and Rectangular Ducts as Function of | 618-618 | - | - | None | - | - |  |
| Fig. 24 Guidelines for Centrifugal Fan Installations | 619-619 | - | - | None | - | - |  |
| Table 10 Options for Selecting 90° Takeoff | 620-620 | - | - | None | - | - |  |
| Table 12 Recommended Maximum Airflow Velocities to Achieve Specified Acoustic De | 621-621 | - | - | None | - | - |  |
| Table 13 Guide for Selecting Low-Pressure System Friction Rate* | 622-622 | - | - | None | - | - |  |
| Fig. 25 Economizer Duct System Shown | 623-623 | - | - | None | - | - |  |
| Table 14 Example 8, Equal Friction Design | 624-624 | - | - | None | - | - |  |
| Table 15 Example 8, Static Regain Design | 625-626 | - | - | None | - | - |  |
| Table 18 System Unbalance | 627-627 | - | - | None | - | - |  |
| Fig. 31 System Schematic with Section Numbers for Example 9 | 628-628 | - | - | None | - | - |  |
| Table 20 Loss Coefficient Summary by Sections for Example 9 | 629-629 | - | - | None | - | - |  |
| Fig. 32 Total Pressure Grade Line for Example 9 | 630-631 | air_distribution | system_topic_reference | True | general_hvac | performance_spec | Section discusses duct design and total pressure grade line, relevant to air distribution. |
| CHAPTER 22: PIPE DESIGN | 632-632 | - | - | None | - | - |  |
| Table 1 Common Applications of Pipe, Fittings, and Valves for Heating and Air Co | 633-635 | - | - | None | - | - |  |
| Table 2 Manufacturers’ Recommendationsa,b for Plastic Materials | 636-636 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec, performance_spec | Table of manufacturers' recommendations for plastic materials, providing parameter and per |
| Table 4 K Factors: Flanged Welded Steel Pipe Fittings | 637-637 | - | - | None | - | - |  |
| Table 6 Summary of K Values for Steel Ells, Reducers, and Expansions | 638-638 | - | - | None | - | - |  |
| Table 8 Test Summary for Loss Coefficients K and Equivalent Loss Lengths | 639-639 | - | - | None | - | - |  |
| Table 9 Test Summary for Loss Coefficients K of PVC Tees | 640-641 | - | - | None | - | - |  |
| Table 11 Suggested Hanger Spacing and Rod Size for Straight Horizontal Runs | 642-642 | - | - | None | - | - |  |
| Table 12 Suggested Maximum Spacing Between Hangers/Support for PVC and CPVC Pipe | 643-643 | - | - | None | - | - |  |
| Table 13 Thermal Expansion of Metal Pipe | 644-644 | - | - | None | - | - |  |
| Table 14 Pipe Loop Design for A53 Grade B Carbon Steel Pipe Through 200°C | 645-645 | - | - | None | - | - |  |
| Table 15 Allowable Stressesa for Pipe and Tube | 646-646 | - | - | None | - | - |  |
| Table 16 Steel Pipe Data | 647-647 | - | - | None | - | - |  |
| Table 17 Copper Tube Data | 648-648 | - | - | None | - | - |  |
| Table 18 Properties of Pipe Materialsa | 649-649 | - | - | None | - | - |  |
| Table 20 Internal Working Pressure for Copper Tube Joints | 650-651 | - | - | None | - | - |  |
| Fig. 8 Flexible Ball Joint | 652-652 | - | - | None | - | - |  |
| Table 23 Maximum Water Velocity to Minimize Erosion | 653-654 | - | - | None | - | - |  |
| Table 25 Demand Weights of Fixtures in Fixture Unitsa | 655-655 | - | - | None | - | - |  |
| Fig. 13 Variation of Pressure Loss with Flow Rate for Various Faucets and Cocks | 656-656 | - | - | None | - | - |  |
| Fig. 14 Friction Loss for Water in Commercial Steel Pipe (Schedule 40) | 657-657 | - | - | None | - | - |  |
| Table 26 Allowable Number of 25 mm Flush Valves Served by Various Sizes of Water | 658-658 | - | - | None | - | - |  |
| Table 28 Iron and Copper Elbow Equivalents* | 659-659 | - | - | None | - | - |  |
| Table 30 Comparative Capacity of Steam Lines at Various Pitches for Steam and Co | 660-660 | - | - | None | - | - |  |
| Table 32 Flow Rate of Steam in Schedule 40 Pipe | 661-661 | - | - | None | - | - |  |
| Fig. 18 Flow Rate and Velocity of Steam in Schedule 40 Pipe at Saturation Pressu | 662-662 | - | - | None | - | - |  |
| Table 34 Return Main and Riser Capacities for Low-Pressure Systems, g/s | 663-663 | - | - | None | - | - |  |
| Fig. 20 Types of Condensate Return Systems | 664-664 | - | - | None | - | - |  |
| Table 36 Vented Wet Condensate Return for Gravity Flow Based on Darcy-Weisbach E | 665-665 | - | - | None | - | - |  |
| Table 40 Maximum Capacity of Gas Pipe in Litres per Second | 666-666 | - | - | None | - | - |  |
| Table 41 Recommended Nominal Size for Fuel Oil Suction Lines from Tank to Pump ( | 667-667 | - | - | None | - | - |  |
| Table 42 Recommended Nominal Size for Fuel Oil Suction Lines from Tank to Pump ( | 668-670 | - | - | None | - | - |  |
| Fig. 1 Determination of Economic Thickness of Insulation | 671-671 | - | - | None | - | - |  |
| Table 2 Minimum Pipe Insulation Thickness,a mm | 672-672 | - | - | None | - | - |  |
| Table 4 Insulation Thickness Required to Prevent Surface Condensation | 673-673 | - | - | None | - | - |  |
| Table 5 Design Weather Data for Condensation Control | 674-674 | - | - | None | - | - |  |
| Table 6 Time to Cool Water to Freezing, h | 675-675 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Table on time to cool water to freezing, relevant to insulation and system protection; inc |
| Fig. 5 Insertion Loss Versus Mass of Jacket | 676-676 | - | - | None | - | - |  |
| Table 7 Insertion Loss for Pipe Insulation Materials, dB | 677-679 | - | - | None | - | - |  |
| Table 9 Thermal Conductivities of Cylindrical Pipe Insulation at 12.8 and 24°C | 680-682 | - | - | None | - | - |  |
| Table 11 Minimum Saddle Lengths for Use with 32 kg/m3 Polyisocyanurate Foam Insu | 683-683 | - | - | None | - | - |  |
| Fig. 6 Insulating Pipe Hangers | 684-686 | - | - | None | - | - |  |
| Fig. 8 R-Value Required to Prevent Condensation on Surface with Emittance e = 0. | 687-688 | - | - | None | - | - |  |
| Table 12 Emittance Data of Commonly Used Materials | 689-689 | - | - | None | - | - |  |
| Table 16 Inner and Outer Diameters of Standard Flexible Closed-Cell Tubing Insul | 690-690 | - | - | None | - | - |  |
| Table 18 Heat Loss from Bare Copper Tube to Still Air at 27°C, W/m | 691-692 | - | - | None | - | - |  |
| Fig. 1 Wind Flow Pattern Around High-Rise Building Slab | 693-693 | - | - | None | - | - |  |
| Fig. 3 Surface Flow Patterns for Normal and Oblique Winds | 694-694 | - | - | None | - | - |  |
| Fig. 6 Amplification Factor K in Horizontal Plane at y = 2 m above Ground for Co | 695-695 | - | - | None | - | - |  |
| Table 1 Atmospheric Boundary Layer Parameters | 696-696 | - | - | None | - | - |  |
| Fig. 8 Local Pressure Coefficients (Cp x 100) for High-Rise Building with Varyin | 697-697 | - | - | None | - | - |  |
| Fig. 9 Local Pressure Coefficients for Low-Rise Building with Varying Wind Direc | 698-698 | - | - | None | - | - |  |
| Table 2 Typical Relationship of Hourly Wind Speed Umet to Annual Average Wind Sp | 699-699 | - | - | None | - | - |  |
| Fig. 15 Sensitivity of System Volume to Locations of Building Openings, Intakes, | 700-700 | - | - | None | - | - |  |
| Fig. 17 Effect of Wind-Assisted and Wind-Opposed Flow | 701-702 | - | - | None | - | - |  |
| Fig. 18 Flow Patterns Around Rectangular Block Building | 703-710 | - | - | None | - | - |  |
| CHAPTER 25: HEAT, AIR, AND MOISTURE CONTROL IN BUILDING ASSEMBLIES—FUNDAMENTALS | 711-711 | - | - | None | - | - |  |
| Fig. 1 Hygrothermal Loads and Alternating Diurnal or Seasonal Directions Acting  | 712-712 | - | - | None | - | - |  |
| Fig. 2 Solar Vapor Drive and Interstitial Condensation | 713-713 | - | - | None | - | - |  |
| Fig. 4 Measured Reduction in Catch Ratio Close to Façade of One-Story Building a | 714-716 | - | - | None | - | - |  |
| Fig. 5 Heat Flux by Thermal Radiation and Combined Convection and Conduction Acr | 717-718 | - | - | None | - | - |  |
| Fig. 6 Examples of Airflow Patterns | 719-719 | air_distribution | system_design | True | general_hvac | performance_spec, operational_sequence | Examples of airflow patterns, providing performance specs and operational sequences for ai |
| Fig. 7 Sorption Isotherms for Porous Building Materials | 720-720 | - | - | None | - | - |  |
| Fig. 8 Sorption Isotherm and Suction Curve for Autoclaved Aerated Concrete (AAC) | 721-721 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Sorption isotherm and suction curve for AAC, providing material performance data for build |
| Fig. 9 Capillary Rise in Hydrophilic Materials | 722-722 | - | - | None | - | - |  |
| Fig. 10 Moisture Fluxes by Vapor Diffusion and Liquid Flow in Single Capillary o | 723-728 | - | - | None | - | - |  |
| CHAPTER 26: HEAT, AIR, AND MOISTURE CONTROL IN BUILDING ASSEMBLIES—MATERIAL PROP | 729-729 | - | - | None | - | - |  |
| Fig. 2 Variation of Apparent Thermal Conductivity with Fiber Diameter and Densit | 730-731 | - | - | None | - | - |  |
| Fig. 3 Working Principle of Capillary-Active Interior Insulation | 732-735 | - | - | None | - | - |  |
| Table 1 Building and Insulating Materials: Design Valuesa | 736-740 | - | - | None | - | - |  |
| Table 2 Emissivity of Various Surfaces and Effective Emittances of Facing Air Sp | 741-741 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Table of emissivity values and effective emittances, providing performance specs for build |
| Table 3 Thermal Resistances of Plane Air Spaces,a,b,c (m2·K)/W | 742-743 | - | - | None | - | - |  |
| Table 4 Air Permeability of Different Materials | 744-744 | general_hvac_design | system_topic_reference | True | general_hvac | performance_spec | Table of air permeability of materials, providing performance specs for building envelope  |
| Table 5 Typical Water Vapor Permeance and Permeability for Common Building Mater | 745-745 | - | - | None | - | - |  |
| Table 6 Water Vapor Permeance at Various Relative Humidities and Capillary Water | 746-747 | - | - | None | - | - |  |
| Table 7 Sorption/Desorption Isotherms of Building Materials at Various Relative  | 748-748 | - | - | None | - | - |  |
| Table 9 Typical Apparent Thermal Conductivity Values for Rocks, W/(m·K) | 749-751 | - | - | None | - | - |  |
| CHAPTER 27: HEAT, AIR , AND MOISTURE CONTROL IN BUILDING ASSEMBLIES—EXAMPLES | 752-752 | - | - | None | - | - |  |
| Fig. 2 Roof Assembly (Example 2) | 753-753 | - | - | None | - | - |  |
| Fig. 3 (A) Wall Assembly for Example 3, with Equivalent Electrical Circuits: (B) | 754-754 | - | - | None | - | - |  |
| Fig. 4 Insulated Concrete Block Wall (Example 4) | 755-755 | - | - | None | - | - |  |
| Fig. 5 Wall Section and Equivalent Electrical Circuit (Example 5) | 756-756 | - | - | None | - | - |  |
| Fig. 7 Corner Composed of Homogeneous Material Showing Locations of Isotherms | 757-757 | - | - | None | - | - |  |
| Fig. 9 Brick Veneer Shelf for Example 6 | 758-759 | - | - | None | - | - |  |
| Fig. 10 Dew-Point Calculation in Wood-Framed Wall (Example 8) | 760-761 | - | - | None | - | - |  |
| Fig. 12 Drying Wet Sheathing, Summer (Example 9) | 762-763 | general_hvac_design | system_design | True | general_hvac | application_guidance, operational_sequence | Drying wet sheathing example, providing application guidance and operational sequences for |
| CHAPTER 28: COMBUSTION AND FUELS | 764-764 | - | - | None | - | - |  |
| Table 2 Flammability Limits and Ignition Temperatures of Common Fuels in Fuel/Ai | 765-765 | - | - | None | - | - |  |
| Table 3 Heating Values of Substances Occurring in Common Fuels | 766-766 | - | - | None | - | - |  |
| Fig. 1 Altitude Effects on Gas Combustion Appliances | 767-768 | - | - | None | - | - |  |
| Table 4 Propane/Air and Butane/Air Gas Mixtures | 769-769 | - | - | None | - | - |  |
| Table 8 Typical Compounds and Concentrations Found in Syngas from Thermal Gasifi | 770-770 | - | - | None | - | - |  |
| Fig. 2 Approximate Viscosity of Fuel Oils | 771-771 | - | - | None | - | - |  |
| Table 9 Sulfur Content of Marketed Fuel Oils | 772-772 | - | - | None | - | - |  |
| Table 11 Classification of Coals by Ranka | 773-773 | - | - | None | - | - |  |
| Table 12 Typical Ultimate Analyses for Coals | 774-774 | - | - | None | - | - |  |
| Table 14 Theoretical Air Requirements for Stoichiometric Combustion of Various F | 775-775 | - | - | None | - | - |  |
| Table 15 Approximate Maximum Theoretical (Stoichiometric) CO2 Values, and CO2 Va | 776-776 | - | - | None | - | - |  |
| Fig. 5 Influence of Sulfur Oxides on Flue Gas Dew Point | 777-778 | - | - | None | - | - |  |
| Fig. 6 Flue Gas Losses with Various Fuels | 779-779 | - | - | None | - | - |  |
| Table 16 NOx Emission Factors for Combustion Sources | 780-782 | - | - | None | - | - |  |
| Fig. 7 Feedback Loop Stability Model Defined by Baade (1978, 2004) | 783-784 | - | - | None | - | - |  |
| CHAPTER 29: REFRIGERANTS | 785-785 | - | - | None | - | - |  |
| Table 1 Refrigerant Data and Safety Classifications | 786-786 | - | - | None | - | - |  |
| Table 2 Data and Safety Classifications for Refrigerant Blends | 787-788 | - | - | None | - | - |  |
| Table 3B Refrigerant Environmental Properties | 789-789 | - | - | None | - | - |  |
| Table 4 Environmental Properties of Refrigerant Blends; based on Montreal Protoc | 790-790 | - | - | None | - | - |  |
| Table 5 Physical Properties of Selected Refrigerantsa | 791-791 | - | - | None | - | - |  |
| Table 7 Electrical Properties of Refrigerant Vapors | 792-792 | - | - | None | - | - |  |
| Table 8 Comparative Refrigerant Performance per Kilowatt of Refrigeration | 793-793 | chiller | system_topic_reference | True | chiller | parameter_spec, performance_spec | Section covers refrigerant performance and leak detection, directly relevant to chillers. |
| Table 9 Swelling of Elastomers in Liquid Refrigerants at Room Temperature, % Lin | 794-796 | - | - | None | - | - |  |
| CHAPTER 30: THERMOPHYSICAL PROPERTIES OF REFRIGERANTS | 797-797 | - | - | None | - | - |  |
| Fig. 1 Pressure-Enthalpy Diagram for Refrigerant 12 | 798-799 | - | - | None | - | - |  |
| Fig. 2 Pressure-Enthalpy Diagram for Refrigerant 22 | 800-801 | - | - | None | - | - |  |
| Fig. 3 Pressure-Enthalpy Diagram for Refrigerant 23 | 802-803 | - | - | None | - | - |  |
| Fig. 4 Pressure-Enthalpy Diagram for Refrigerant 32 | 804-805 | - | - | None | - | - |  |
| Fig. 5 Pressure-Enthalpy Diagram for Refrigerant 123 | 806-807 | - | - | None | - | - |  |
| Fig. 6 Pressure-Enthalpy Diagram for Refrigerant 124 | 808-809 | - | - | None | - | - |  |
| Fig. 7 Pressure-Enthalpy Diagram for Refrigerant 125 | 810-811 | - | - | None | - | - |  |
| Fig. 8 Pressure-Enthalpy Diagram for Refrigerant 134a | 812-815 | - | - | None | - | - |  |
| Fig. 9 Pressure-Enthalpy Diagram for Refrigerant 143a | 816-817 | - | - | None | - | - |  |
| Fig. 10 Pressure-Enthalpy Diagram for Refrigerant 152a | 818-819 | - | - | None | - | - |  |
| Fig. 11 Pressure-Enthalpy Diagram for Refrigerant 245fa | 820-821 | - | - | None | - | - |  |
| Fig. 12 Pressure-Enthalpy Diagram for Refrigerant R-1233zd(E) | 822-823 | - | - | None | - | - |  |
| Fig. 13 Pressure-Enthalpy Diagram for Refrigerant 1234yf | 824-825 | - | - | None | - | - |  |
| Fig. 14 Pressure-Enthalpy Diagram for Refrigerant 1234ze(E) | 826-827 | - | - | None | - | - |  |
| Fig. 15 Pressure-Enthalpy Diagram for Refrigerant 404A | 828-829 | - | - | None | - | - |  |
| Fig. 16 Pressure-Enthalpy Diagram for Refrigerant 407C | 830-831 | - | - | None | - | - |  |
| Fig. 17 Pressure-Enthalpy Diagram for Refrigerant 410A | 832-833 | - | - | None | - | - |  |
| Fig. 18 Pressure-Enthalpy Diagram for Refrigerant 507A | 834-835 | - | - | None | - | - |  |
| Fig. 19 Pressure-Enthalpy Diagram for Refrigerant 717 (Ammonia) | 836-837 | - | - | None | - | - |  |
| Fig. 20 Pressure-Enthalpy Diagram for Refrigerant 718 (Water/Steam) | 838-839 | - | - | None | - | - |  |
| Fig. 21 Pressure-Enthalpy Diagram for Refrigerant 744 (Carbon Dioxide) | 840-841 | - | - | None | - | - |  |
| Fig. 22 Pressure-Enthalpy Diagram for Refrigerant 50 (Methane) | 842-843 | - | - | None | - | - |  |
| Fig. 23 Pressure-Enthalpy Diagram for Refrigerant 170 (Ethane) | 844-845 | - | - | None | - | - |  |
| Fig. 24 Pressure-Enthalpy Diagram for Refrigerant 290 (Propane) | 846-847 | - | - | None | - | - |  |
| Fig. 25 Pressure-Enthalpy Diagram for Refrigerant 600 (n-Butane) | 848-849 | - | - | None | - | - |  |
| Fig. 26 Pressure-Enthalpy Diagram for Refrigerant 600a (Isobutane) | 850-851 | - | - | None | - | - |  |
| Fig. 27 Pressure-Enthalpy Diagram for Refrigerant 1150 (Ethylene) | 852-853 | - | - | None | - | - |  |
| Fig. 28 Pressure-Enthalpy Diagram for Refrigerant 1270 (Propylene) | 854-855 | - | - | None | - | - |  |
| Fig. 29 Pressure-Enthalpy Diagram for Refrigerant 704 (Helium) | 856-857 | - | - | None | - | - |  |
| Fig. 30 Pressure-Enthalpy Diagram for Refrigerant 728 (Nitrogen) | 858-859 | - | - | None | - | - |  |
| Fig. 31 Pressure-Enthalpy Diagram for Refrigerant 729 (Air) | 860-861 | - | - | None | - | - |  |
| Fig. 32 Pressure-Enthalpy Diagram for Refrigerant 732 (Oxygen) | 862-863 | - | - | None | - | - |  |
| Fig. 33 Pressure-Enthalpy Diagram for Refrigerant 740 (Argon) | 864-865 | - | - | None | - | - |  |
| Fig. 34 Enthalpy-Concentration Diagram for Ammonia/Water Solutions | 866-868 | - | - | None | - | - |  |
| Fig. 35 Equilibrium Chart for Aqueous Lithium Bromide Solutions | 869-869 | - | - | None | - | - |  |
| Fig. 38 Viscosity of Aqueous Solutions of Lithium Bromide | 870-874 | - | - | None | - | - |  |
| Table 1 Properties of Pure Calcium Chloride* Brines | 875-875 | - | - | None | - | - |  |
| Fig. 4 Thermal Conductivity of Calcium Chloride Brines | 876-876 | - | - | None | - | - |  |
| Table 2 Properties of Pure Sodium Chloridea Brines | 877-877 | - | - | None | - | - |  |
| Fig. 8 Thermal Conductivity of Sodium Chloride Brines | 878-878 | - | - | None | - | - |  |
| Table 3 Physical Properties of Ethylene Glycol and Propylene Glycol | 879-879 | - | - | None | - | - |  |
| Table 5 Freezing and Boiling Points of Aqueous Solutions of Propylene Glycol | 880-880 | - | - | None | - | - |  |
| Table 7 Specific Heat of Aqueous Solutions of Ethylene Glycol | 881-881 | - | - | None | - | - |  |
| Table 9 Viscosity of Aqueous Solutions of Ethylene Glycol | 882-882 | - | - | None | - | - |  |
| Table 11 Specific Heat of Aqueous Solutions of Propylene Glycol | 883-883 | - | - | None | - | - |  |
| Table 13 Viscosity of Aqueous Solutions of Propylene Glycol | 884-884 | - | - | None | - | - |  |
| Fig. 16 Viscosity of Aqueous Solutions of Industrially Inhibited Propylene Glyco | 885-886 | - | - | None | - | - |  |
| Table 16 Physical Properties of d-Limonene | 887-887 | - | - | None | - | - |  |
| CHAPTER 32: SORBENTS AND DESICCANTS | 888-888 | - | - | None | - | - |  |
| Table 1 Vapor Pressures and Dew-Point Temperatures Corresponding to Different Re | 889-889 | - | - | None | - | - |  |
| Fig. 5 Surface Vapor Pressure of Water/Lithium Chloride Solutions | 890-890 | - | - | None | - | - |  |
| Fig. 6 Adsorption and Structural Characteristics of Some Experimental Silica Gel | 891-891 | - | - | None | - | - |  |
| Fig. 7 Sorption Isotherms of Various Desiccants | 892-893 | - | - | None | - | - |  |
| Table 1 Properties of Vapor | 894-894 | - | - | None | - | - |  |
| Table 2 Properties of Liquids | 895-895 | - | - | None | - | - |  |
| Table 3 Properties of Solids | 896-897 | - | - | None | - | - |  |
| CHAPTER 34 : ENERGY RESOURCES | 898-900 | - | - | None | - | - |  |
| Fig. 2 World Primary Energy Production by Resource: 2004 Versus 2014 | 901-901 | - | - | None | - | - |  |
| Fig. 5 World Recoverable Coal Reserves: 2015 | 902-902 | - | - | None | - | - |  |
| Fig. 9 Coal Consumption in United States, China, and India, 1980-2014 | 903-903 | - | - | None | - | - |  |
| Fig. 14 Per Capita United States Energy Consumption | 904-904 | - | - | None | - | - |  |
| Fig. 17 Projected Total U.S. Energy Consumption by Resource | 905-906 | - | - | None | - | - |  |
| CHAPTER 35 : SUSTAINABILITY | 907-909 | - | - | None | - | - |  |
| Fig. 1 Cooling Tower Noise Barrier | 910-910 | - | - | None | - | - |  |
| Fig. 2 Effect of Montreal Protocol on Global Chlorofluorocarbon (CFC) Production | 911-912 | - | - | None | - | - |  |
| Fig. 3 Electricity Generation by Fuel, 1980–2030 | 913-914 | - | - | None | - | - |  |
| Table 1 Example Benchmark and Energy Targets for University Research Laboratory | 915-918 | sustainability_general | audit_methodology | True | general_hvac | performance_spec | Benchmark and energy targets for university research lab, providing performance specs for  |
| CHAPTER 36 : MOISTURE MANAGEMENT IN BUILDINGS | 919-919 | - | - | None | - | - |  |
| Fig. 1 Dynamic Interaction Between Air, Moisture, and Materials in HVAC Systems  | 920-921 | - | - | None | - | - |  |
| Fig. 5 Annual Monthly Averaged Indoor/Outdoor Vapor Pressure Difference in Bedro | 922-922 | - | - | None | - | - |  |
| Table 3 Vapor Released by Fuel Burning | 923-923 | - | - | None | - | - |  |
| Table 7 Vapor Release Rates by Percentile | 924-924 | - | - | None | - | - |  |
| Table 8 Measured Surface Film Coefficients for Diffusion, Related to Pool Surfac | 925-925 | - | - | None | - | - |  |
| Table 9 Finland and Estonia, Indoor Climate, Boundaries (Weekly Means) | 926-926 | - | - | None | - | - |  |
| Fig. 14 Indoor/Outdoor Vapor Pressure Difference with Intersect at 0°C for 71 Rh | 927-927 | - | - | None | - | - |  |
| Table 10 Indoor Air Temperature and Indoor/Outdoor Vapor Pressure Difference: Me | 928-928 | - | - | None | - | - |  |
| Fig. 18 Sedlbauer’s Isopleth System for Class I Substrates: Time Until Germinati | 929-932 | - | - | None | - | - |  |
| CHAPTER 37 : MEASUREMENT AND INSTRUMEN | 933-933 | - | - | None | - | - |  |
| Fig. 1 Measurement and Instrument Terminology | 934-934 | - | - | None | - | - |  |
| Fig. 2 Errors in Measurement of Variable X | 935-935 | general_hvac_design | system_topic_reference | True | general_hvac | parameter_spec, performance_spec | Errors in measurement of variable X, providing parameter and performance specs for instrum |
| Table 1 Common Temperature Measurement Techniques | 936-937 | - | - | None | - | - |  |
| Fig. 3 Typical Resistance Thermometer Circuit | 938-938 | - | - | None | - | - |  |
| Fig. 5 Basic Thermistor Circuit | 939-939 | - | - | None | - | - |  |
| Table 2 Thermocouple Tolerances on Initial Values of Electromotive Force Versus  | 940-941 | - | - | None | - | - |  |
| Table 3 Humidity Sensor Properties | 942-947 | - | - | None | - | - |  |
| Table 4 Air Velocity Measurement | 948-948 | air_distribution | system_topic_reference | True | general_hvac | parameter_spec, performance_spec | Section provides air velocity measurement methods, relevant to air distribution systems. |
| Fig. 6 Standard Pitot Tube | 949-949 | - | - | None | - | - |  |
| Fig. 7 Pitot-Static Probe Pressure Coefficient Yaw Angular Dependence | 950-950 | - | - | None | - | - |  |
| Fig. 8 Measuring Points for Rectangular and Round Duct Traverse | 951-952 | - | - | None | - | - |  |
| Table 5 Volumetric or Mass Flow Rate Measurement | 953-953 | - | - | None | - | - |  |
| Fig. 9 Typical Herschel-Type Venturi Meter | 954-954 | - | - | None | - | - |  |
| Fig. 12 Variable-Area Flowmeter | 955-956 | - | - | None | - | - |  |
| Fig. 13 Nondispersive Infrared Carbon Dioxide Sensor | 957-957 | - | - | None | - | - |  |
| Fig. 16 Closed-Cell Photoacoustic Carbon Dioxide Sensor | 958-958 | - | - | None | - | - |  |
| Fig. 22 Wattmeter in Single-Phase Circuit Measuring Power Load plus Loss in Pote | 959-959 | - | - | None | - | - |  |
| Fig. 27 Three-Wire, Three-Phase Power-Factor Meter | 960-963 | - | - | None | - | - |  |
| Fig. 28 Madsen’s Comfort Meter | 964-964 | - | - | None | - | - |  |
| Fig. 29 Adsorption Isotherm and Desorption Isotherm for Hygroscopic Material | 965-972 | - | - | None | - | - |  |
| CHAPTER 38 : ABBREVIATIONS AND SYMBOLS | 973-973 | - | - | None | - | - |  |
| Table 1 Abbreviations for Text, Drawings, and Computer Programs | 974-981 | - | - | None | - | - |  |
| Table 3 Classification of Hazardous Materials and Designation of Colorsa | 982-982 | - | - | None | - | - |  |
| Table 4 Size of Legend Letters | 983-983 | - | - | None | - | - |  |
| Table 1 Conversions to I-P and SI Units | 984-984 | - | - | None | - | - |  |
| Table 2 Conversion Factors | 985-985 | - | - | None | - | - |  |
| Selected Codes and Standards Published by Various Societies and Associations | 986-1014 | general_hvac_design | system_topic_reference | True | general_hvac | application_guidance | Section lists codes and standards, providing application guidance for HVAC design. |
