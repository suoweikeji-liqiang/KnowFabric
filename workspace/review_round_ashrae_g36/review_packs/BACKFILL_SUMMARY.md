# ASHRAE G36 Backfill Summary

Generated: 2026-05-06T11:08:55.289330+00:00
Updated: 2026-05-06T12:04:29Z

## Review Result

- Human reviewed candidates: 22
- Accepted: 21
- Rejected: 1
- Backfilled now: 21 total
  - 15 under `hvac:chiller`
  - 6 under `hvac:hot_water_plant`
- Deferred: 1

## Readiness / Apply

- Readiness: ready 2, blocked 0
- Apply: applied 2, failed 0
- Fixtures:
  - `workspace/review_round_ashrae_g36/review_packs/applied_fixtures/hvac__doc_4bbd3703c4f84be4__chiller__fixture.json`
  - `workspace/review_round_ashrae_g36/review_packs/applied_fixtures/hvac__doc_4bbd3703c4f84be4__hot_water_plant__fixture.json`

## Deferred Entries

- #3: `human_rejected_wrong_ko_type`

No accepted current-ontology entries remain deferred after adding `boiler` and `hot_water_plant`.

## API Smoke

- `application-guidance`: 1 item
- `parameter-profiles`: 3 items, including the ASHRAE G36 T&R parameter spec plus existing performance specs
- `fault-knowledge`: 4 `fault_diagnostic_rule` items
- `operational-guidance`: 10 items, including 9 `operational_sequence` items
- `operational-guidance?guidance_type=operational_sequence`: 9 items
- `hot_water_plant/operational-guidance`: 6 `operational_sequence` items

## Notes

- `fault_diagnostic_rule` and `operational_sequence` had to be added to the semantic API type whitelists.
- Multi-chunk evidence is now supported by the manual fixture builder and chunk-backed backfill path.
- `min_trust_level=L3` now behaves as a lower bound and includes L4 items.
- `boiler` and `hot_water_plant` were added to the HVAC ontology to host ASHRAE G36 heating hot-water sequences.
