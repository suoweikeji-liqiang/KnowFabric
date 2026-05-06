# ASHRAE G36 Backfill Summary

Generated: 2026-05-06T11:08:55.289330+00:00

## Review Result

- Human reviewed candidates: 22
- Accepted: 21
- Rejected: 1
- Backfilled now: 15 under `hvac:chiller`
- Deferred: 7

## Readiness / Apply

- Readiness: ready 1, blocked 0
- Apply: applied 1, failed 0
- Fixture: `workspace/review_round_ashrae_g36/review_packs/applied_fixtures/hvac__doc_4bbd3703c4f84be4__chiller__fixture.json`

## Deferred Entries

- #3: `human_rejected_wrong_ko_type`
- #17: `no_boiler_or_hot_water_plant_class_in_current_sw_base_model_ontology`
- #18: `no_boiler_or_hot_water_plant_class_in_current_sw_base_model_ontology`
- #19: `no_boiler_or_hot_water_plant_class_in_current_sw_base_model_ontology`
- #20: `no_boiler_or_hot_water_plant_class_in_current_sw_base_model_ontology`
- #21: `no_boiler_or_hot_water_plant_class_in_current_sw_base_model_ontology`
- #22: `no_boiler_or_hot_water_plant_class_in_current_sw_base_model_ontology`

## API Smoke

- `application-guidance`: 1 item
- `parameter-profiles`: 3 items, including the ASHRAE G36 T&R parameter spec plus existing performance specs
- `fault-knowledge`: 4 `fault_diagnostic_rule` items
- `operational-guidance`: 10 items, including 9 `operational_sequence` items
- `operational-guidance?guidance_type=operational_sequence`: 9 items

## Notes

- `fault_diagnostic_rule` and `operational_sequence` had to be added to the semantic API type whitelists.
- Multi-chunk evidence is now supported by the manual fixture builder and chunk-backed backfill path.
- `min_trust_level=L3` now behaves as a lower bound and includes L4 items.
