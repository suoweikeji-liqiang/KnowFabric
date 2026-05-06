# ASHRAE G36 Backfill Summary

Generated: 2026-05-06T11:08:55.289330+00:00

## Review Result

- Human reviewed candidates: 22
- Accepted: 21
- Rejected: 1
- Backfilled now: 13 under `hvac:chiller`
- Deferred: 9

## Readiness / Apply

- Readiness: ready 1, blocked 0
- Apply: applied 1, failed 0
- Fixture: `workspace/review_round_ashrae_g36/review_packs/applied_fixtures/hvac__doc_4bbd3703c4f84be4__chiller__fixture.json`

## Deferred Entries

- #2: `multi_chunk_evidence_not_supported_by_current_manual_fixture_builder`
- #3: `human_rejected_wrong_ko_type`
- #6: `multi_chunk_evidence_not_supported_by_current_manual_fixture_builder`
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
- `operational-guidance`: 8 items, including 7 `operational_sequence` items
- `operational-guidance?guidance_type=operational_sequence`: 7 items

## Notes

- `fault_diagnostic_rule` and `operational_sequence` had to be added to the semantic API type whitelists.
- `min_trust_level=L3` currently excludes L4 because the existing ranking logic treats the filter as an upper bound. This was observed but not fixed in this step.
