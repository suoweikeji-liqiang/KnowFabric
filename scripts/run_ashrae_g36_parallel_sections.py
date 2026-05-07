#!/usr/bin/env python3
"""Run ASHRAE G36 full-book-aware extraction in parallel focus-section jobs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DOC_ID = "doc_4bbd3703c4f84be4"
DEFAULT_EXTRACT_BACKEND = "deepseek-parameter-spec"
DEFAULT_JUDGE_BACKEND = "deepseek-v4-pro-judge"
DEFAULT_SECTIONS = tuple(f"5.{index}" for index in range(1, 23))


@dataclass(frozen=True)
class SectionJob:
    section: str
    command: list[str]


def parse_sections(value: str) -> list[str]:
    if value.strip().lower() == "all":
        return list(DEFAULT_SECTIONS)
    return [item.strip() for item in value.split(",") if item.strip()]


def build_jobs(args: argparse.Namespace, workspace: Path) -> list[SectionJob]:
    return [SectionJob(section, build_command(args, section, workspace)) for section in parse_sections(args.sections)]


def build_command(args: argparse.Namespace, section: str, workspace: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/run_ashrae_g36_full_book.py",
        "--doc-id",
        args.doc_id,
        "--extract-backend",
        args.extract_backend,
        "--judge-backend",
        args.judge_backend,
        "--output-dir",
        args.extract_output_dir,
        "--budget-rmb",
        str(args.budget_rmb_per_section),
        "--extract-max-tokens",
        str(args.extract_max_tokens),
        "--judge-max-tokens",
        str(args.judge_max_tokens),
        "--extract-timeout-seconds",
        str(args.extract_timeout_seconds),
        "--judge-timeout-seconds",
        str(args.judge_timeout_seconds),
        "--max-extract-seconds",
        str(args.max_extract_seconds),
        "--target-candidates",
        str(args.target_candidates_per_section),
        "--max-raw-candidates",
        str(args.max_raw_candidates_per_section),
        "--focus-sections",
        section,
    ]


def run_job(job: SectionJob, *, dry_run: bool = False) -> dict[str, Any]:
    start = time.monotonic()
    print(f"[{job.section}] + {' '.join(job.command)}", flush=True)
    if dry_run:
        return {"section": job.section, "status": "dry_run", "command": job.command}
    completed = subprocess.run(job.command, text=True, capture_output=True)
    result = {
        "section": job.section,
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "summary": parse_summary_from_stdout(completed.stdout),
    }
    if completed.returncode != 0:
        print(f"[{job.section}] failed rc={completed.returncode}", flush=True)
    else:
        summary = result["summary"] or {}
        print(f"[{job.section}] verified={summary.get('verified')} L4={summary.get('L4')} report={summary.get('report')}", flush=True)
    return result


def parse_summary_from_stdout(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        if not line.startswith("summary "):
            continue
        return parse_summary_line(line)
    return None


def parse_summary_line(line: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for part in line.split()[1:]:
        key, sep, value = part.partition("=")
        if not sep:
            continue
        result[key] = coerce_summary_value(value)
    return result


def coerce_summary_value(value: str) -> Any:
    if value.startswith("¥"):
        try:
            return float(value[1:])
        except ValueError:
            return value
    try:
        return int(value)
    except ValueError:
        return value


def run_jobs(args: argparse.Namespace, jobs: list[SectionJob]) -> list[dict[str, Any]]:
    if args.dry_run or args.workers <= 1:
        return [run_job(job, dry_run=args.dry_run) for job in jobs]
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_job, job, dry_run=False): job for job in jobs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if args.fail_fast and result["status"] != "pass":
                raise RuntimeError(f"Section {result['section']} failed")
    return sorted(results, key=lambda item: section_sort_key(item["section"]))


def section_sort_key(section: str) -> tuple[int, ...]:
    return tuple(int(part) if part.isdigit() else 0 for part in section.split("."))


def write_summary(workspace: Path, args: argparse.Namespace, results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = build_summary(args, results)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "parallel_sections_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (workspace / "PARALLEL_SECTIONS_SUMMARY.md").write_text(render_markdown(summary) + "\n", encoding="utf-8")
    return summary


def build_summary(args: argparse.Namespace, results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [item for item in results if item["status"] == "pass"]
    failed = [item for item in results if item["status"] == "fail"]
    return {
        "mode": "ashrae_g36_parallel_fullbook_focus_sections",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doc_id": args.doc_id,
        "workers": args.workers,
        "dry_run": args.dry_run,
        "section_count": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "total_verified": sum(int((item.get("summary") or {}).get("verified") or 0) for item in passed),
        "total_l4": sum(int((item.get("summary") or {}).get("L4") or 0) for item in passed),
        "results": results,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# ASHRAE G36 Parallel Full-Book Focus Sections Summary",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Doc ID: `{summary['doc_id']}`",
        f"- Workers: {summary['workers']}",
        f"- Dry run: {summary['dry_run']}",
        f"- Sections: {summary['section_count']}",
        f"- Passed/failed: {summary['passed']}/{summary['failed']}",
        f"- Total verified: {summary['total_verified']}",
        f"- Total L4: {summary['total_l4']}",
        "",
        "| Section | Status | Verified | L4 | Report |",
        "|---|---|---:|---:|---|",
    ]
    for item in summary["results"]:
        parsed = item.get("summary") or {}
        lines.append(
            f"| `{item['section']}` | {item['status']} | {parsed.get('verified', '-')} | "
            f"{parsed.get('L4', '-')} | `{parsed.get('report', '-')}` |"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc-id", default=DEFAULT_DOC_ID)
    parser.add_argument("--sections", default="all", help="Comma-separated top-level sections or 'all'")
    parser.add_argument("--extract-backend", default=DEFAULT_EXTRACT_BACKEND)
    parser.add_argument("--judge-backend", default=DEFAULT_JUDGE_BACKEND)
    parser.add_argument("--extract-output-dir", default="output/ashrae_guideline36_parallel_fullbook")
    parser.add_argument("--workspace-root", default="workspace/ashrae_g36_parallel_sections")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--budget-rmb-per-section", type=float, default=10.0)
    parser.add_argument("--target-candidates-per-section", type=int, default=40)
    parser.add_argument("--max-raw-candidates-per-section", type=int, default=80)
    parser.add_argument("--extract-max-tokens", type=int, default=80_000)
    parser.add_argument("--judge-max-tokens", type=int, default=50_000)
    parser.add_argument("--extract-timeout-seconds", type=int, default=1200)
    parser.add_argument("--judge-timeout-seconds", type=int, default=1200)
    parser.add_argument("--max-extract-seconds", type=float, default=1200.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = Path(args.workspace_root) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    jobs = build_jobs(args, workspace)
    results = run_jobs(args, jobs)
    summary = write_summary(workspace, args, results)
    print(f"sections={summary['section_count']} passed={summary['passed']} failed={summary['failed']} summary={workspace / 'PARALLEL_SECTIONS_SUMMARY.md'}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"ASHRAE G36 parallel section extraction failed: {exc}")
        raise SystemExit(1)
