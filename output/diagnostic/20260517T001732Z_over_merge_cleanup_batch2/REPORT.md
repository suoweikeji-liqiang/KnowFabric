# Over-merge Cleanup Batch 2 Report

## Summary

- Backup: `/tmp/cleanup_batch2_pre_20260517T002246Z.sql`
- Active over_merge before: 29
- Active over_merge after: 0
- KO total: 9981 -> 10012 (net +31)
- Max layers: 8
- Bad identity count (`ontology_class_id = ''` or `canonical_key LIKE 'hvac::%'`): 0
- Canonical key collision count: 0
- Remaining `over_merge` rows: 4, all `review_status=rejected` (`ko_0003dc96ea6cfa09`, `ko_0a5634c7d18e0843`, plus batch 1 rejected garbage `ko_01a4a4047927d344`, `ko_75c3a5d18c8eaa43`)

## Operations

| old_ko_id | action | new_ko_ids / state | reason |
| --- | --- | --- | --- |
| `ko_0003dc96ea6cfa09` | reject_old | `` | evidence_all_unrelated |
| `ko_0a5634c7d18e0843` | reject_old | `` | evidence_all_startup_or_runtime_not_shutdown |
| `ko_2ba76711e02b5977` | state_only | `value_disagreement` | post-batch1 audit |
| `ko_0375092c506a85d8` | split | `ko_153b5ac79d50e1ef;ko_afb07bdae294ae8a` | polarity: high pressure; polarity: low pressure |
| `ko_04dc5b2658675b79` | split | `ko_c08be308ac51a42f;ko_3c9bcd473b05dba1` | cross-topic pressure fault; kept oil pressure evidence |
| `ko_050ac03ff6e2b012` | split | `ko_dd1bf2e52db527ef;ko_4362e66faa129cfe` | cross-topic standard evidence; kept climate design evidence |
| `ko_051d666042fe81b7` | split | `ko_142e81d48518f58f;ko_48cd6e165034730c` | VOC/formaldehyde concept; unit ventilator concept |
| `ko_05b9aebdde71d566` | split | `ko_b451ac0ab2f009d8;ko_c15d1b6c2a74b2aa` | different concept: discharge pressure; different concept: slide valve |
| `ko_09774088f47b820e` | split | `ko_e5087c56eafacc7b;ko_089ed2490ecd65b6` | duct: cold duct; duct: hot deck |
| `ko_0a2c2eebadb6cf7a` | split | `ko_d26e4307f3f97972;ko_c299ebd3120bcd8c;ko_8ed8b2c1f6c413c9` | cross-topic water quality; kept voltage evidence; ocr garbage |
| `ko_0aa1d7491394e13d` | split | `ko_c57f0df338badfaa;ko_4f1404365b540a83` | fault_code number |
| `ko_0d80e765f6b64a5c` | split | `ko_5455fa8b83b86eff;ko_8e12f7dd8703907d` | fault_code number |
| `ko_178654fc424a0af4` | split | `ko_aa0c8a9f85876f81;ko_062ec61c2e07a700` | heating vs cooling |
| `ko_2108bb796ebd7b19` | split | `ko_e7125201d01b575e;ko_4c9397da8f5aff04` | different component: compressor; different component: filter drier |
| `ko_22c130aad4ba2827` | split | `ko_f70add546e7a4b75;ko_e65a4778ed0d164e;ko_795e0a9b6095e1dc;ko_8034d32d194e4a01` | refrigerant split |
| `ko_2cb2a95fb07241cc` | split | `ko_ebeda05be643f557;ko_f0e40fdc0024c413` | subsystem: refrigerant side; subsystem: water side |
| `ko_3d285aa3a09556b2` | split | `ko_0bc07187af50b8b8;ko_5cb26f01b225eb4a` | control delta; rated condition |
| `ko_497eb8d85aae2821` | split | `ko_f1cb867e53c88035;ko_47e6643603278ea8;ko_e7fbc04f252e8219` | fault_code number |
| `ko_4a7e489f00e85fa8` | split | `ko_24db42b7182d4ede;ko_81ad4fef0576796a` | polarity: high pressure; polarity: low pressure |
| `ko_5d02f6cccbb51a2a` | split | `ko_f03ea9b600722f30;ko_fbe65a7798733883` | cross-topic test temperature; kept pumpout evidence |
| `ko_69ed0c22154f8e08` | split | `ko_32a6334605cafc3b;ko_92e966d1836827e5` | refrigerant split |
| `ko_7f9870a9f4f55691` | split | `ko_87abb28bc981ab98;ko_cf7640cac29bd614;ko_5731046fd666f5ce` | refrigerant split |
| `ko_899d764444a01370` | split | `ko_2e4b51e9fae51a17;ko_d8566a0cf06e9c99` | mode: hold; mode: unload |
| `ko_933017f2e086099d` | split | `ko_ef1961dcc4c6a5f4;ko_a1a2df084622bb30` | kept alarm rule; section header only |
| `ko_d117735fd9164c58` | split | `ko_a88cac6fbc0946c7;ko_2aee2bd542069c2a;ko_098aae1272438c0b` | refrigerant split |
| `ko_d53103623a638535` | split | `ko_8661bc1d95fb04b8;ko_5c913b8d21eeb76e` | cross-topic voltage evidence; kept ambient condition |
| `ko_e0075dafbff580a7` | split | `ko_211117294ea114f5;ko_d6f40ff04baad2d7` | heating evidence in cooling KO; kept cooling evidence |
| `ko_ec0f999bae1fab30` | split | `ko_e62f549a70240f9b;ko_67b3758a0225b9e5` | cross-topic standard evidence; kept entering water evidence |
| `ko_f8fea0a88ba94ce1` | state_only | `value_disagreement/published` | refrigerant split |

Full machine-readable log: `batch2_split_log.csv`.

## Additional Active Cases After Batch 1

The live SQL set contained seven active IDs beyond the prompt table, not four. They were handled conservatively with the same audit policy:
- `ko_2ba76711e02b5977`: state_only -> value_disagreement (post-batch1 audit)
- `ko_3d285aa3a09556b2`: split -> ko_0bc07187af50b8b8;ko_5cb26f01b225eb4a (control delta; rated condition)
- `ko_69ed0c22154f8e08`: split -> ko_32a6334605cafc3b;ko_92e966d1836827e5 (refrigerant split)
- `ko_7f9870a9f4f55691`: split -> ko_87abb28bc981ab98;ko_cf7640cac29bd614;ko_5731046fd666f5ce (refrigerant split)
- `ko_d117735fd9164c58`: split -> ko_a88cac6fbc0946c7;ko_2aee2bd542069c2a;ko_098aae1272438c0b (refrigerant split)
- `ko_e0075dafbff580a7`: split -> ko_211117294ea114f5;ko_d6f40ff04baad2d7 (heating evidence in cooling KO; kept cooling evidence)
- `ko_f8fea0a88ba94ce1`: state_only -> value_disagreement/published (refrigerant split)

No uncertain extra case was force-split without a deterministic axis. `ko_2ba76711e02b5977` and `ko_f8fea0a88ba94ce1` were retagged to `value_disagreement` rather than split because their evidence remained same-concept value disagreement after inspection.

## Verification

- Dry-run: active over_merge 29 -> 0 with rollback, no FK/key errors
- Oracle: PASS (`scripts/verify_cross_publisher_merge.py --skip-precheck`)
- Pytest: PASS, `438 passed`
- Gates: PASS, `bash scripts/check-all` all 4 gates
- SQL sanity: active over_merge 0; bad identity 0; canonical collision 0; max_layers 8

## Notes

- Evidence was not physically deleted. Evidence rows were either moved to new published KOs or moved to rejected KOs for traceability.
- FK-safe ordering was used: insert target KO, move evidence, delete superseded old KO.
- Rejected whole-KO cases remain in DB as rejected trace records, so raw `consensus_state=over_merge` is 4 while active over_merge is 0.
