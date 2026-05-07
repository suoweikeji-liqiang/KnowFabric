#!/usr/bin/env python3
"""Merge and audit ASHRAE G36 parallel section-context extraction outputs."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.dedupe_standard_knowledge import DedupeRow, group_duplicate_rows  # noqa: E402
from scripts.run_ashrae_guideline36_vertical import sha1_text, write_jsonl  # noqa: E402
from scripts.run_standard_import_pipeline import _normalize_standard_candidate  # noqa: E402


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path} must contain JSON object lines")
            rows.append(payload)
    return rows


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verified_paths_from_summary(summary: dict[str, Any]) -> list[Path]:
    paths = []
    for item in summary.get("results", []):
        report = (item.get("summary") or {}).get("report")
        if report:
            paths.append(Path(report).parent / "candidates_llm_verified.jsonl")
    return paths


def load_parallel_candidates(summary_path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = load_json(summary_path)
    rows: list[dict[str, Any]] = []
    for path in verified_paths_from_summary(summary):
        for row in load_jsonl(path):
            rows.append({**row, "source_run_dir": str(path.parent)})
    return summary, rows


def exact_dedup_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        groups[dedupe_key(row)].append(row)
    final, duplicate_rows = [], []
    for rows in groups.values():
        best = max(rows, key=keep_sort_key)
        merged = merge_group(best, rows)
        final.append(merged)
        duplicate_rows.extend(row for row in rows if row.get("candidate_id") != best.get("candidate_id"))
    return sorted(final, key=candidate_sort_key), duplicate_rows


def dedupe_key(row: dict[str, Any]) -> str:
    return str(row.get("canonical_key_candidate") or "")


def keep_sort_key(row: dict[str, Any]) -> tuple[int, int, float, int]:
    return (
        trust_rank(str(row.get("trust_level") or "")),
        len(row.get("source_chunk_ids") or []),
        float(row.get("confidence_score") or 0.0),
        len(str((row.get("structured_payload_candidate") or {}).get("summary") or "")),
    )


def trust_rank(value: str) -> int:
    return {"L4": 4, "L3": 3, "L2": 2, "L1": 1}.get(value.upper(), 0)


def merge_group(best: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    merged = copy.deepcopy(best)
    chunk_ids = unique_values(chunk for row in rows for chunk in row.get("source_chunk_ids", []))
    page_nos = sorted({int(page) for row in rows for page in row.get("source_page_nos", []) if page is not None})
    merged["source_chunk_ids"] = chunk_ids
    merged["source_page_nos"] = page_nos
    if chunk_ids:
        merged["chunk_id"] = chunk_ids[0]
    if page_nos:
        merged["page_no"] = page_nos[0]
    if len(chunk_ids) >= 2:
        merged["trust_level"] = "L4"
        merged["verification_reason"] = f"global cross-source corroboration: {len(chunk_ids)} chunks"
    merged["global_dedupe"] = {
        "exact_group_size": len(rows),
        "source_candidate_ids": unique_values(str(row.get("candidate_id")) for row in rows),
        "source_run_dirs": unique_values(str(row.get("source_run_dir")) for row in rows),
    }
    return merged


def unique_values(values) -> list[str]:
    return [item for item in dict.fromkeys(value for value in values if value)]


def candidate_sort_key(row: dict[str, Any]) -> tuple[str, int, str]:
    payload = row.get("structured_payload_candidate") or {}
    return (str(payload.get("section_id") or ""), int(row.get("page_no") or 0), str(row.get("canonical_key_candidate") or ""))


def fuzzy_groups(candidates: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    rows = [to_dedupe_row(row) for row in candidates]
    return group_duplicate_rows(rows, threshold)


def to_dedupe_row(row: dict[str, Any]) -> DedupeRow:
    payload = row.get("structured_payload_candidate") or {}
    return DedupeRow(
        knowledge_object_id=str(row.get("candidate_id") or sha1_text(json.dumps(row, sort_keys=True))),
        domain_id=str(row.get("domain_id") or "hvac"),
        ontology_class_id=str((row.get("equipment_class_candidate") or {}).get("equipment_class_id") or infer_equipment_scope(payload)),
        knowledge_object_type=str(row.get("knowledge_object_type") or payload.get("knowledge_type") or ""),
        canonical_key=str(row.get("canonical_key_candidate") or ""),
        title=str(payload.get("title") or ""),
        summary=str(payload.get("summary") or ""),
        section_id=str(payload.get("section_id") or ""),
        trust_level=str(row.get("trust_level") or "L3"),
        confidence_score=float(row.get("confidence_score") or 0.0),
        evidence_count=len(row.get("source_chunk_ids") or []),
        page_nos=tuple(int(page) for page in row.get("source_page_nos", []) if page is not None),
    )


def infer_equipment_scope(payload: dict[str, Any]) -> str:
    return str(payload.get("equipment_scope") or "ashrae_g36_scope")


def section_stats(summary: dict[str, Any]) -> list[dict[str, Any]]:
    stats = []
    for item in summary.get("results", []):
        parsed = item.get("summary") or {}
        stats.append(
            {
                "section": item.get("section"),
                "verified": int(parsed.get("verified") or 0),
                "l4": int(parsed.get("L4") or 0),
                "raw": int(parsed.get("raw") or 0),
                "anchor_passed": int(parsed.get("anchor_passed") or 0),
                "elapsed_seconds": float(item.get("elapsed_seconds") or 0.0),
                "report": parsed.get("report"),
            }
        )
    return stats


def build_merge_report(
    source_summary: dict[str, Any],
    raw: list[dict[str, Any]],
    exact: list[dict[str, Any]],
    exact_duplicates: list[dict[str, Any]],
    fuzzy: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    stats = section_stats(source_summary)
    low_output = [row for row in stats if row["verified"] <= args.low_output_threshold]
    trust = Counter(row.get("trust_level") or "unknown" for row in exact)
    types = Counter(row.get("knowledge_object_type") or "unknown" for row in exact)
    return {
        "mode": "ashrae_g36_parallel_section_merge",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_summary_path": str(args.summary),
        "raw_candidate_count": len(raw),
        "exact_deduped_candidate_count": len(exact),
        "exact_duplicate_count": len(exact_duplicates),
        "fuzzy_duplicate_group_count": len(fuzzy),
        "fuzzy_review_duplicate_count": sum(len(group["duplicates"]) for group in fuzzy),
        "trust_breakdown": dict(trust),
        "type_breakdown": dict(types),
        "section_stats": stats,
        "low_output_sections": low_output,
        "fuzzy_duplicate_groups": fuzzy,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ASHRAE G36 Parallel Section Merge Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Source summary: `{report['source_summary_path']}`",
        f"- Raw candidates: {report['raw_candidate_count']}",
        f"- Exact-deduped candidates: {report['exact_deduped_candidate_count']}",
        f"- Exact duplicate rows merged: {report['exact_duplicate_count']}",
        f"- Fuzzy duplicate groups for review: {report['fuzzy_duplicate_group_count']}",
        f"- Fuzzy review duplicate rows: {report['fuzzy_review_duplicate_count']}",
        f"- Trust breakdown: {format_counter(report['trust_breakdown'])}",
        f"- Type breakdown: {format_counter(report['type_breakdown'])}",
        "",
        "## Section Stats",
        "",
        "| Section | Raw | Anchor passed | Verified | L4 | Elapsed | Report |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["section_stats"]:
        lines.append(
            f"| `{row['section']}` | {row['raw']} | {row['anchor_passed']} | {row['verified']} | "
            f"{row['l4']} | {row['elapsed_seconds']:.1f}s | `{row['report']}` |"
        )
    lines.extend(render_low_output(report))
    lines.extend(render_fuzzy_groups(report))
    return "\n".join(lines)


def format_counter(counter: dict[str, int]) -> str:
    return ", ".join(f"{key}: {value}" for key, value in sorted(counter.items())) or "none"


def render_low_output(report: dict[str, Any]) -> list[str]:
    lines = ["", "## Low Output Sections", ""]
    if not report["low_output_sections"]:
        return lines + ["None"]
    for row in report["low_output_sections"]:
        lines.append(f"- §{row['section']}: verified={row['verified']}, L4={row['l4']}, report=`{row['report']}`")
    return lines


def render_fuzzy_groups(report: dict[str, Any]) -> list[str]:
    lines = ["", "## Fuzzy Duplicate Groups For Review", ""]
    if not report["fuzzy_duplicate_groups"]:
        return lines + ["None"]
    for index, group in enumerate(report["fuzzy_duplicate_groups"][:30], start=1):
        keep = group["keep"]
        lines.append(f"### Group {index}")
        lines.append(f"Keep review candidate: `{keep['knowledge_object_id']}` §{keep['section_id']} {keep['title']}")
        for row in group["duplicates"]:
            lines.append(f"- Possible duplicate: `{row['knowledge_object_id']}` §{row['section_id']} {row['title']}")
        lines.append("")
    if len(report["fuzzy_duplicate_groups"]) > 30:
        lines.append(f"_Markdown truncated: {len(report['fuzzy_duplicate_groups']) - 30} more groups in JSON._")
    return lines


def write_outputs(output_dir: Path, report: dict[str, Any], exact: list[dict[str, Any]], exact_duplicates: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(output_dir / "candidates_llm_verified_global_exact_deduped.jsonl", exact)
    write_jsonl(output_dir / "candidates_llm_exact_duplicates_merged.jsonl", exact_duplicates)
    write_json(output_dir / "candidates_input.json", build_candidate_input(report, exact))
    write_json(output_dir / "merge_report.json", report)
    (output_dir / "MERGE_REPORT.md").write_text(render_markdown(report) + "\n", encoding="utf-8")


def build_candidate_input(report: dict[str, Any], exact: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [_normalize_standard_candidate(row, standard="ashrae-g36") for row in exact]
    return {
        "generation_mode": "ashrae_g36_parallel_section_context_merge",
        "domain_id": "hvac",
        "candidate_entries": entries,
        "metadata": {
            "source_summary_path": report["source_summary_path"],
            "source_merge_report": "MERGE_REPORT.md",
            "standard": "ashrae-g36",
            "standard_id": "ASHRAE Guideline 36-2021",
            "doc_id": first_value(entries, "doc_id"),
            "doc_name": first_value(entries, "doc_name"),
            "total_candidates": len(entries),
            "raw_candidate_count": report["raw_candidate_count"],
            "exact_duplicate_count": report["exact_duplicate_count"],
            "fuzzy_duplicate_group_count": report["fuzzy_duplicate_group_count"],
            "l4_final": report["trust_breakdown"].get("L4", 0),
            "l3_final": report["trust_breakdown"].get("L3", 0),
        },
    }


def first_value(entries: list[dict[str, Any]], key: str) -> Any:
    for entry in entries:
        if entry.get(key) is not None:
            return entry[key]
    return None


def default_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("workspace/ashrae_g36_parallel_sections_merged") / stamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, help="parallel_sections_summary.json from run_ashrae_g36_parallel_sections.py")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--fuzzy-threshold", type=float, default=0.86)
    parser.add_argument("--low-output-threshold", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    source_summary, raw = load_parallel_candidates(args.summary)
    exact, exact_duplicates = exact_dedup_candidates(raw)
    fuzzy = fuzzy_groups(exact, args.fuzzy_threshold)
    report = build_merge_report(source_summary, raw, exact, exact_duplicates, fuzzy, args)
    write_outputs(output_dir, report, exact, exact_duplicates)
    print(
        f"raw={len(raw)} exact_deduped={len(exact)} fuzzy_groups={len(fuzzy)} "
        f"report={output_dir / 'MERGE_REPORT.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
