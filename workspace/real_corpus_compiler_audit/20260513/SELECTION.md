# Real Corpus Compiler Audit Selection

- Date: 2026-05-13
- Branch: `codex/knowledge-compiler-hardening`
- Goal: run a small, high-quality corpus through the hardened compiler chain and audit whether the output is traceable enough for manual review.

## Selection Criteria

- Prefer authoritative standards, guidelines, and technical manuals over catalogs, marketing brochures, training slides, or scanned-only files.
- Prefer PDFs with extractable text and stable page references.
- Avoid duplicate standards in both IP/SI forms unless the audit specifically needs unit-system comparison.
- Do not use obsolete standards as current authority sources.
- Keep the first run small enough for line-by-line review.

## Selected Documents

| Role | Source | Pages | Text Quality | Reason |
| --- | --- | ---: | --- | --- |
| International rating standard | `ANSI-AHRI-Standard-550-590-2023-I-P-editorial-update.pdf` | 82 | good | Current AHRI water-chilling / heat-pump water-heating package performance rating standard; strong for parameter and performance-spec extraction. |
| Control-sequence authority guide | `ashrae_guideline_36_2021_high_performance_sequences.pdf` | 292 | good | High-value HVAC sequence guideline; already central to the project but useful to re-run through the new audit chain. |
| Domestic OEM technical manual | `【格力】C系列离心式冷水机组技术手册（69页）-.pdf` | 69 | good | Chinese technical service manual with dense parameter/control/parts content; tests Chinese extraction without using low-quality scans. |

## Held Out

| Source | Reason |
| --- | --- |
| `ANSI-AHRI-Standard-551-591-2023-SI-editorial-update.pdf` | Good source, but same standard family as AHRI 550/590. Hold for later unit-system comparison instead of duplicating the first audit. |
| `ashrae_211_energy_audit_best_practices.pdf` | Extractable, but it is a short slide deck about ASHRAE 211 rather than the standard text. Too weak as a primary authority document. |
| `trane_cvgf_400_1000_chiller_manual.pdf` | Useful fallback OEM manual, but text samples include watermark/control-character noise. Hold until the cleaner Chinese manual run is assessed. |
| `GB19577-2004冷水机组能效限定值及能源效率等级.pdf` | Text is extractable, but the standard is obsolete. Do not use as current authority evidence. |
| `GB 19577-2024` | Official national standard metadata confirms it is current, but the official full-text download requires verification. It should be introduced after a clean official PDF is obtained, not via an unverified mirror. |

## Domestic Standard Gap

`GB 19577-2024 热泵和冷水机组能效限定值及能效等级` should be added to the real corpus after a clean official copy is available. The official SAMR page marks it as current, published 2024-04-29 and implemented 2025-02-01.
