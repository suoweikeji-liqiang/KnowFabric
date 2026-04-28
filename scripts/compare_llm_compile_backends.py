#!/usr/bin/env python3
"""Compare rule-only and OpenAI-compatible LLM compiler backends on one scope."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import OpenAICompatibleBackend, load_backend_configs
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates


def candidate_identity(entry: dict[str, Any]) -> tuple[str, str, str, str, str]:
    """Return one stable identity tuple for a compiler candidate."""

    return (
        str(entry.get("doc_id")),
        str(entry.get("chunk_id")),
        str(entry.get("equipment_class_candidate", {}).get("equipment_class_id")),
        str(entry.get("knowledge_object_type")),
        str(entry.get("canonical_key_candidate")),
    )


def summarize_backend_run(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Build one concise summary for one backend run."""

    identities = {candidate_identity(entry) for entry in payload.get("candidate_entries", [])}
    compiler_methods = sorted(
        {
            str(entry.get("compile_metadata", {}).get("method") or "unknown")
            for entry in payload.get("candidate_entries", [])
        }
    )
    return {
        "name": name,
        "candidate_count": len(payload.get("candidate_entries", [])),
        "knowledge_types": payload.get("metadata", {}).get("candidate_knowledge_types", []),
        "compiler_methods": compiler_methods,
        "identities": sorted(list(identities)),
    }


def build_overlap_matrix(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build pairwise overlap statistics from backend summaries."""

    overlap_rows = []
    for left in summaries:
        left_set = set(tuple(item) for item in left["identities"])
        for right in summaries:
            right_set = set(tuple(item) for item in right["identities"])
            shared = len(left_set & right_set)
            overlap_rows.append(
                {
                    "left": left["name"],
                    "right": right["name"],
                    "shared_candidates": shared,
                    "left_total": len(left_set),
                    "right_total": len(right_set),
                }
            )
    return overlap_rows


def compare_llm_compile_backends(
    *,
    domain_id: str,
    output_dir: str | Path,
    backends: list[OpenAICompatibleBackend],
    doc_id: str | None = None,
    chunk_id: str | None = None,
    equipment_class_id: str | None = None,
    limit: int = 100,
    generator: Callable[..., dict[str, Any]] = generate_chunk_backfill_candidates,
) -> dict[str, Any]:
    """Run one rule baseline plus multiple LLM compiler backend comparisons."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    runs = []
    baseline_payload = generator(
        domain_id,
        doc_id=doc_id,
        chunk_id=chunk_id,
        equipment_class_id=equipment_class_id,
        limit=limit,
        enable_llm=False,
    )
    baseline_path = destination / "rule_baseline_candidates.json"
    baseline_path.write_text(json.dumps(baseline_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runs.append({"name": "rule-baseline", "payload": baseline_payload, "path": str(baseline_path)})

    for backend in backends:
        payload = generator(
            domain_id,
            doc_id=doc_id,
            chunk_id=chunk_id,
            equipment_class_id=equipment_class_id,
            limit=limit,
            llm_backend=backend,
            enable_llm=True,
        )
        candidate_path = destination / f"{backend.name}__candidates.json"
        candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        runs.append({"name": backend.name, "payload": payload, "path": str(candidate_path)})

    summaries = [summarize_backend_run(run["name"], run["payload"]) for run in runs]
    report = {
        "compare_mode": "llm_compile_backend_compare",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain_id": domain_id,
        "filters_applied": {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "equipment_class_id": equipment_class_id,
            "limit": limit,
        },
        "runs": [
            {
                "name": run["name"],
                "candidate_path": run["path"],
                "candidate_count": len(run["payload"].get("candidate_entries", [])),
                "compiler_methods": summaries[index]["compiler_methods"],
                "knowledge_types": summaries[index]["knowledge_types"],
            }
            for index, run in enumerate(runs)
        ],
        "overlap_matrix": build_overlap_matrix(summaries),
    }
    report_path = destination / "llm_compile_backend_compare_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain_id", help="Domain scope such as 'hvac' or 'drive'")
    parser.add_argument("output_dir", help="Directory where comparison artifacts should be written")
    parser.add_argument("--backend-config", required=True, help="JSON file describing OpenAI-compatible backends")
    parser.add_argument("--doc-id", dest="doc_id", help="Optional document filter")
    parser.add_argument("--chunk-id", dest="chunk_id", help="Optional chunk filter")
    parser.add_argument("--equipment-class-id", dest="equipment_class_id", help="Optional equipment class filter")
    parser.add_argument("--limit", type=int, default=100, help="Maximum candidate entries to keep per run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = compare_llm_compile_backends(
        domain_id=args.domain_id,
        output_dir=args.output_dir,
        backends=load_backend_configs(args.backend_config),
        doc_id=args.doc_id,
        chunk_id=args.chunk_id,
        equipment_class_id=args.equipment_class_id,
        limit=args.limit,
    )
    print(
        f"Compared {len(report['runs']) - 1} LLM backend(s) against the rule baseline. "
        f"Report: {report['report_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"LLM backend comparison failed: {exc}")
        raise SystemExit(1)
