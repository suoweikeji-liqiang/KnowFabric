# Ontology Gap Notes

This batch maps ASHRAE Guideline 36 terminal-unit sections 5.7-5.14 to `hvac:ahu`.

Reason: the current HVAC ontology does not define a dedicated `vav_terminal_unit` or `terminal_unit` equipment class. Mapping to `ahu` keeps the knowledge reachable through the existing airside equipment anchor and avoids introducing a new class without reviewing sw_base_model alignment.

Future candidate class:

- `vav_terminal_unit` or broader `terminal_unit`
- Useful for separating AHU plant-level/air-handler-level sequences from terminal-box sequences
- Would carry `operational_sequence`, `fault_diagnostic_rule`, `commissioning_step`, and `parameter_spec`

This is not blocking for the current model-reviewed import. The current API smoke confirms all accepted items are visible under `ahu`.
