# Standard Reference Semantic Follow-up

## Conclusion

- All 7 standard references are now parseable/chunked.
- A trial run of the generic chunk-backfill candidate export on ASHRAE 211 produced `0` candidates.
- Conclusion: these standard references should not be pushed through the generic OEM/chunk-backfill semantic path.
- Required next path: standard-specific extractor or explicit section/chapter selection workflow.

## Items

- ASHRAE手册2019.pdf: status=`chunked_via_retry` doc_id=`doc_ashrae2019_retry_available` chunks=`None` next=`standard_specific_extractor_or_section_selection_required`
  note: AES-encrypted PDF now parseable after installing cryptography; retry batch succeeded at output/hvac_standard_reference_retry/20260509T155102Z_hvac_source_batch
- ASHRAE 211能源审计最佳实践.pdf: status=`chunked` doc_id=`doc_c019162f43d44d06` chunks=`20` next=`standard_specific_extractor_or_section_selection_required`
  note: generic chunk-backfill candidate export returned 0 candidates on ASHRAE 211; do not use OEM/generic candidate path directly
- 空调 系统 设计 手册 Ashrae 特别 出版物.pdf: status=`chunked` doc_id=`doc_06f8fa1cac644fe2` chunks=`931` next=`standard_specific_extractor_or_section_selection_required`
  note: generic chunk-backfill candidate export returned 0 candidates on ASHRAE 211; do not use OEM/generic candidate path directly
- ASHRAE绿色建筑指南.pdf: status=`chunked` doc_id=`doc_38a89d59e8394e2d` chunks=`2160` next=`standard_specific_extractor_or_section_selection_required`
  note: generic chunk-backfill candidate export returned 0 candidates on ASHRAE 211; do not use OEM/generic candidate path directly
- ASHRAE手册 - HVAC系统和设备篇.pdf: status=`chunked` doc_id=`doc_a5de4244eeda4637` chunks=`6642` next=`standard_specific_extractor_or_section_selection_required`
  note: generic chunk-backfill candidate export returned 0 candidates on ASHRAE 211; do not use OEM/generic candidate path directly
- ASHRAE手册2024.pdf: status=`chunked` doc_id=`doc_4a9b0fec1dfb4103` chunks=`6546` next=`standard_specific_extractor_or_section_selection_required`
  note: generic chunk-backfill candidate export returned 0 candidates on ASHRAE 211; do not use OEM/generic candidate path directly
- ASHRAE手册 - 基础理论篇.pdf: status=`chunked` doc_id=`doc_2a7ec347e5f44d9e` chunks=`6391` next=`standard_specific_extractor_or_section_selection_required`
  note: generic chunk-backfill candidate export returned 0 candidates on ASHRAE 211; do not use OEM/generic candidate path directly
