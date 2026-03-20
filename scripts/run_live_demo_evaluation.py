#!/usr/bin/env python3
"""Run the full external-evaluation flow and emit a manifest."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.bootstrap_v1_demo import bootstrap_v1_demo, run_api_smoke_reports
from scripts.build_v1_demo_brief import build_v1_demo_brief
from scripts.check_demo_environment import (
    build_demo_environment_summary_text,
    check_api_health,
    check_demo_environment,
)


@dataclass
class ApiServiceHandle:
    """Running API service plus the resources needed to stop it cleanly."""

    process: subprocess.Popen[str]
    log_path: Path
    log_file: Any
    command: list[str]


def default_preflight_report_path(output_dir: str | Path = "output/demo") -> Path:
    """Build the default preflight report path for the live evaluation flow."""

    return Path(output_dir) / "demo_environment_preflight.json"


def default_live_evaluation_manifest_path(output_dir: str | Path = "output/demo") -> Path:
    """Build the default manifest path for the live evaluation flow."""

    return Path(output_dir) / "live_demo_evaluation_manifest.json"


def default_api_log_path(output_dir: str | Path = "output/demo") -> Path:
    """Build the default API service log path for the live evaluation flow."""

    return Path(output_dir) / "api_service.log"


def default_cover_note_path(output_dir: str | Path = "output/demo") -> Path:
    """Build the default evaluator cover note path for the live evaluation flow."""

    return Path(output_dir) / "EVALUATOR_NOTE.md"


def _write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _write_text(path: str | Path, content: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def _build_api_command(host: str, port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "apps.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]


def _parse_api_base_url(base_url: str) -> tuple[str, int]:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"Unsupported API base URL: {base_url}")
    if parsed.path not in {"", "/"}:
        raise ValueError("API base URL must not include a path")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.hostname, port


def start_api_service(
    *,
    api_base_url: str,
    log_path: str | Path,
) -> ApiServiceHandle:
    """Start the API service for live smoke evaluation."""

    host, port = _parse_api_base_url(api_base_url)
    command = _build_api_command(host, port)
    env = os.environ.copy()
    env["API_HOST"] = host
    env["API_PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"
    repo_root = Path(__file__).resolve().parent.parent
    target_log_path = Path(log_path)
    target_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = target_log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=repo_root,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return ApiServiceHandle(process=process, log_path=target_log_path, log_file=log_file, command=command)


def _tail_text(path: str | Path, line_count: int = 20) -> str:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-line_count:])


def wait_for_api_service(
    handle: ApiServiceHandle,
    *,
    api_base_url: str,
    startup_timeout: float = 30.0,
) -> dict[str, Any]:
    """Wait until the API health endpoint is ready or fail with log context."""

    deadline = time.monotonic() + startup_timeout
    while time.monotonic() < deadline:
        health = check_api_health(api_base_url)
        if health["status"] == "passed":
            return health
        if handle.process.poll() is not None:
            log_tail = _tail_text(handle.log_path) if handle.log_path.exists() else ""
            raise RuntimeError(f"API service exited before becoming healthy.\n{log_tail}")
        time.sleep(0.5)
    raise RuntimeError(f"API service did not become healthy within {startup_timeout} seconds.")


def stop_api_service(handle: ApiServiceHandle) -> None:
    """Stop the API service and release any open log handles."""

    try:
        if handle.process.poll() is None:
            handle.process.terminate()
            try:
                handle.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                handle.process.kill()
                handle.process.wait(timeout=5)
    finally:
        handle.log_file.close()


def _surface_status(reports: list[dict[str, Any]], field_name: str = "failed") -> str:
    if not reports:
        return "pending"
    return "passed" if sum(int(item[field_name]) for item in reports) == 0 else "failed"


def _primary_artifacts(
    output_dir: str | Path,
    preflight_report_path: str | Path,
    brief_path: str | Path,
    api_log_path: str | Path,
    manifest_path: str | Path,
    cover_note_path: str | Path,
) -> dict[str, str]:
    return {
        "artifact_bundle_root": str(Path(output_dir)),
        "preflight_report": str(preflight_report_path),
        "brief": str(brief_path),
        "api_log": str(api_log_path),
        "manifest": str(manifest_path),
        "cover_note": str(cover_note_path),
    }


def _handoff_notes(preflight_status: str, bootstrap_status: str, api_status: str) -> list[str]:
    if preflight_status != "passed":
        return ["Resolve preflight failures before handing this environment to evaluators."]
    if bootstrap_status != "passed":
        return ["Bootstrap artifacts are incomplete; rerun the demo bundle before external handoff."]
    if api_status != "passed":
        return ["Live API smoke is not green; inspect the API log and smoke reports before handoff."]
    return [
        "This bundle is ready for external evaluation.",
        "Share the brief first and keep the manifest alongside it for machine-readable validation.",
    ]


def _handoff_payload(
    output_dir: str | Path,
    preflight_report_path: str | Path,
    brief_path: str | Path,
    api_log_path: str | Path,
    manifest_path: str | Path,
    cover_note_path: str | Path,
    bootstrap_result: dict[str, Any],
    statuses: dict[str, str],
) -> dict[str, Any]:
    domain_ids = sorted(item["domain_id"] for item in bootstrap_result.get("ontology_sync", []))
    return {
        "ready_for_external_evaluation": statuses["overall"] == "passed",
        "recommended_entrypoint": f"python3 scripts/run_live_demo_evaluation.py --output-dir {Path(output_dir)}",
        "domain_ids": domain_ids,
        "primary_artifacts": _primary_artifacts(
            output_dir,
            preflight_report_path,
            brief_path,
            api_log_path,
            manifest_path,
            cover_note_path,
        ),
        "notes": _handoff_notes(statuses["preflight"], statuses["bootstrap"], statuses["api"]),
    }


def build_evaluator_cover_note(manifest: dict[str, Any]) -> str:
    """Render a concise evaluator-facing note for the bundle root."""

    handoff = manifest["handoff"]
    artifacts = handoff["primary_artifacts"]
    status = manifest["statuses"]["overall"].upper()
    domain_ids = ", ".join(handoff["domain_ids"]) if handoff["domain_ids"] else "none"
    notes = "\n".join(f"- {note}" for note in handoff["notes"])
    return "\n".join(
        [
            "# KnowFabric Evaluation Bundle",
            "",
            f"Overall status: {status}",
            f"Domains: {domain_ids}",
            "",
            "Recommended reading order:",
            f"1. `{Path(artifacts['brief']).name}`",
            f"2. `{Path(artifacts['manifest']).name}`",
            f"3. `*_api_smoke_report.json`, `*_mcp_smoke_report.json`, `*_semantic_demo_report.json` as needed",
            "",
            "Bundle notes:",
            notes,
            "",
            "Primary artifacts:",
            f"- Brief: `{artifacts['brief']}`",
            f"- Manifest: `{artifacts['manifest']}`",
            f"- Preflight report: `{artifacts['preflight_report']}`",
            f"- API log: `{artifacts['api_log']}`",
            "",
            "This bundle is read-only and evidence-backed. It does not include a UI-first shell, project-instance modeling, or runtime control logic.",
            "",
        ]
    )


def _evaluation_manifest(
    *,
    output_dir: str | Path,
    preflight_report_path: str | Path,
    preflight_report: dict[str, Any],
    bootstrap_result: dict[str, Any],
    live_api_health: dict[str, Any],
    api_reports: list[dict[str, Any]],
    brief_path: str | Path,
    api_log_path: str | Path,
    manifest_path: str | Path,
    cover_note_path: str | Path,
    api_base_url: str,
    command: list[str],
) -> dict[str, Any]:
    bootstrap_status = "passed" if _surface_status(bootstrap_result["reports"]) == "passed" and _surface_status(bootstrap_result["mcp_reports"]) == "passed" else "failed"
    api_status = _surface_status(api_reports)
    statuses = {
        "preflight": "passed" if preflight_report["summary"]["failed"] == 0 else "failed",
        "bootstrap": bootstrap_status,
        "api": api_status,
    }
    statuses["overall"] = "passed" if all(status == "passed" for status in statuses.values()) else "failed"
    return {
        "evaluation_mode": "live_demo_evaluation_runner",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base_url": api_base_url,
        "paths": {
            "output_dir": str(Path(output_dir)),
            "preflight_report": str(preflight_report_path),
            "api_log": str(api_log_path),
            "brief": str(brief_path),
            "manifest": str(manifest_path),
        },
        "statuses": statuses,
        "counts": {
            "semantic_checks_passed": sum(int(item["passed"]) for item in bootstrap_result["reports"]),
            "mcp_checks_passed": sum(int(item["passed"]) for item in bootstrap_result["mcp_reports"]),
            "api_checks_passed": sum(int(item["passed"]) for item in api_reports),
        },
        "preflight_summary": preflight_report["summary"],
        "live_api_health": live_api_health,
        "bootstrap": bootstrap_result,
        "api_reports": api_reports,
        "api_command": command,
        "handoff": _handoff_payload(
            output_dir,
            preflight_report_path,
            brief_path,
            api_log_path,
            manifest_path,
            cover_note_path,
            bootstrap_result,
            statuses,
        ),
    }


def build_live_demo_evaluation_summary_text(manifest: dict[str, Any]) -> str:
    """Render a terminal-friendly summary of the live evaluation result."""

    return "\n".join(
        [
            "Live Demo Evaluation Summary",
            f"Overall: {manifest['statuses']['overall'].upper()}",
            f"Preflight: {manifest['statuses']['preflight'].upper()}",
            f"Bootstrap: {manifest['statuses']['bootstrap'].upper()}",
            f"API Smoke: {manifest['statuses']['api'].upper()}",
            f"Brief: {manifest['paths']['brief']}",
            f"API Log: {manifest['paths']['api_log']}",
        ]
    )


def run_live_demo_evaluation(
    *,
    output_dir: str | Path = "output/demo",
    brief_path: str | Path = "output/demo/v1_demo_brief.md",
    manifest_path: str | Path | None = None,
    preflight_report_path: str | Path | None = None,
    api_log_path: str | Path | None = None,
    cover_note_path: str | Path | None = None,
    api_base_url: str = "http://127.0.0.1:8000",
    startup_timeout: float = 30.0,
) -> dict[str, Any]:
    """Run preflight, bootstrap, live API smoke, and emit a manifest."""

    output_root = Path(output_dir)
    preflight_target = Path(preflight_report_path) if preflight_report_path else default_preflight_report_path(output_root)
    manifest_target = Path(manifest_path) if manifest_path else default_live_evaluation_manifest_path(output_root)
    api_log_target = Path(api_log_path) if api_log_path else default_api_log_path(output_root)
    cover_note_target = Path(cover_note_path) if cover_note_path else default_cover_note_path(output_root)

    preflight = check_demo_environment(output_dir=output_root)
    if preflight["summary"]["failed"] > 0:
        raise RuntimeError(build_demo_environment_summary_text(preflight))
    _write_json(preflight_target, preflight)

    bootstrap_result = bootstrap_v1_demo(
        output_dir=output_root,
        brief_path=brief_path,
        run_preflight=False,
        run_mcp_smoke=True,
        api_base_url=None,
    )

    handle = start_api_service(api_base_url=api_base_url, log_path=api_log_target)
    try:
        live_health = wait_for_api_service(handle, api_base_url=api_base_url, startup_timeout=startup_timeout)
        api_reports = run_api_smoke_reports(api_base_url, output_dir=output_root)
    finally:
        stop_api_service(handle)

    brief_target = build_v1_demo_brief(report_dir=output_root, output_path=brief_path)
    manifest = _evaluation_manifest(
        output_dir=output_root,
        preflight_report_path=preflight_target,
        preflight_report=preflight,
        bootstrap_result=bootstrap_result,
        live_api_health=live_health,
        api_reports=api_reports,
        brief_path=brief_target,
        api_log_path=api_log_target,
        manifest_path=manifest_target,
        cover_note_path=cover_note_target,
        api_base_url=api_base_url,
        command=handle.command,
    )
    _write_json(manifest_target, manifest)
    _write_text(cover_note_target, build_evaluator_cover_note(manifest))
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output/demo", help="Directory for reports, logs, and the final manifest")
    parser.add_argument("--brief-output", default="output/demo/v1_demo_brief.md", help="Markdown brief output path")
    parser.add_argument("--manifest-output", help="Optional explicit path for the live evaluation manifest")
    parser.add_argument("--preflight-output", help="Optional explicit path for the preflight JSON report")
    parser.add_argument("--api-log", help="Optional explicit path for the API service log")
    parser.add_argument("--cover-note", help="Optional explicit path for the evaluator cover note")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000", help="Base URL for the temporary API service")
    parser.add_argument("--startup-timeout", type=float, default=30.0, help="Seconds to wait for the API /health endpoint")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    manifest = run_live_demo_evaluation(
        output_dir=args.output_dir,
        brief_path=args.brief_output,
        manifest_path=args.manifest_output,
        preflight_report_path=args.preflight_output,
        api_log_path=args.api_log,
        cover_note_path=args.cover_note,
        api_base_url=args.api_base_url,
        startup_timeout=args.startup_timeout,
    )
    print(build_live_demo_evaluation_summary_text(manifest))
    return 0 if manifest["statuses"]["overall"] == "passed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Live demo evaluation failed: {exc}")
        raise SystemExit(1)
