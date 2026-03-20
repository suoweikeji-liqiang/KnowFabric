#!/usr/bin/env python3
"""Preflight checks for the external evaluation demo environment."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.demo_bundle_inventory import default_demo_example_query_paths, default_demo_fixture_paths


def _status(name: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    payload = {"name": name, "status": status, "detail": detail}
    payload.update(extra)
    return payload


def _read_env_file(path: str | Path = ".env") -> dict[str, str]:
    values: dict[str, str] = {}
    file_path = Path(path)
    if not file_path.exists():
        return values
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _check_python_version() -> dict[str, Any]:
    actual = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected = "3.11.x"
    if (sys.version_info.major, sys.version_info.minor) == (3, 11):
        return _status("python", "passed", f"Using supported interpreter {actual}.", actual=actual, expected=expected)
    return _status("python", "failed", f"Use Python 3.11 for the current pinned dependency set, not {actual}.", actual=actual, expected=expected)


def _check_config_source(env_values: dict[str, str]) -> dict[str, Any]:
    env_exists = Path(".env").exists()
    database_url = os.environ.get("DATABASE_URL") or env_values.get("DATABASE_URL")
    if env_exists and database_url:
        return _status("config", "passed", "Found `.env` and a database URL.", database_url=database_url)
    if database_url:
        return _status("config", "passed", "Using environment variables without a local `.env` file.", database_url=database_url)
    return _status("config", "failed", "No DATABASE_URL found. Create `.env` from `.env.example` or export DATABASE_URL.")


def _check_required_paths(paths: list[Path], label: str) -> dict[str, Any]:
    missing = [str(path) for path in paths if not path.exists()]
    if not missing:
        return _status(label, "passed", f"All {label.replace('_', ' ')} are present.", checked=len(paths))
    return _status(label, "failed", f"Missing {label.replace('_', ' ')}: {', '.join(missing)}", missing=missing)


def _default_db_checker(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def _check_database_connectivity(
    database_url: str | None,
    db_checker: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if not database_url:
        return _status("database", "failed", "Database connectivity could not be checked because DATABASE_URL is missing.")
    checker = db_checker or _default_db_checker
    try:
        checker(database_url)
    except SQLAlchemyError as exc:
        return _status("database", "failed", f"Database check failed: {exc}")
    except Exception as exc:  # pragma: no cover - defensive guard
        return _status("database", "failed", f"Unexpected database check failure: {exc}")
    return _status("database", "passed", "Database connection succeeded.", database_url=database_url)


def _check_output_dir(output_dir: str | Path) -> dict[str, Any]:
    target = Path(output_dir)
    probe = target / ".write_probe"
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return _status("output_dir", "failed", f"Output directory is not writable: {exc}", output_dir=str(target))
    return _status("output_dir", "passed", "Output directory is writable.", output_dir=str(target))


def _default_health_fetcher(base_url: str) -> tuple[int, dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/health"
    try:
        with urlopen(url) as response:
            return response.getcode(), json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        payload = json.loads(body) if body else {"detail": exc.reason}
        return exc.code, payload
    except URLError as exc:
        return 0, {"detail": str(exc)}


def _check_api_health(
    api_base_url: str | None,
    health_fetcher: Callable[[str], tuple[int, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if not api_base_url:
        return _status("api_health", "skipped", "API health was not checked because no base URL was provided.")
    fetcher = health_fetcher or _default_health_fetcher
    code, payload = fetcher(api_base_url)
    service = payload.get("service") if isinstance(payload, dict) else None
    if code == 200 and service == "api":
        return _status("api_health", "passed", "API health endpoint responded successfully.", base_url=api_base_url, http_status=code)
    return _status("api_health", "failed", f"API health check failed with status {code}.", base_url=api_base_url, http_status=code, payload=payload)


def check_api_health(
    api_base_url: str | None,
    *,
    health_fetcher: Callable[[str], tuple[int, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Check the API /health endpoint without running the full preflight suite."""

    return _check_api_health(api_base_url, health_fetcher=health_fetcher)


def _summarize(checks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"passed": 0, "failed": 0, "skipped": 0}
    for item in checks:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    return summary


def check_demo_environment(
    *,
    output_dir: str | Path = "output/demo",
    api_base_url: str | None = None,
    db_checker: Callable[[str], None] | None = None,
    health_fetcher: Callable[[str], tuple[int, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Check whether the current environment is ready for the demo bundle flow."""

    env_values = _read_env_file(".env")
    database_url = os.environ.get("DATABASE_URL") or env_values.get("DATABASE_URL")
    checks = [
        _check_python_version(),
        _check_required_paths([Path(".env.example"), Path("alembic.ini")], "repo_files"),
        _check_required_paths(default_demo_example_query_paths(), "example_queries"),
        _check_required_paths(default_demo_fixture_paths(), "demo_fixtures"),
        _check_config_source(env_values),
        _check_database_connectivity(database_url, db_checker=db_checker),
        _check_output_dir(output_dir),
        check_api_health(api_base_url, health_fetcher=health_fetcher),
    ]
    return {
        "check_mode": "demo_environment_preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(Path(output_dir)),
        "api_base_url": api_base_url,
        "checks": checks,
        "summary": _summarize(checks),
    }


def build_demo_environment_summary_text(report: dict[str, Any]) -> str:
    """Render a terminal-friendly summary of demo environment readiness."""

    lines = [
        "Demo Environment Preflight",
        (
            f"Checks: {report['summary']['passed']} passed, "
            f"{report['summary']['failed']} failed, {report['summary']['skipped']} skipped"
        ),
    ]
    for item in report["checks"]:
        lines.append(f"- {item['status'].upper()} {item['name']}: {item['detail']}")
    return "\n".join(lines)


def ensure_demo_environment_ready(
    *,
    output_dir: str | Path = "output/demo",
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Raise a readable error when the demo environment is not ready."""

    report = check_demo_environment(output_dir=output_dir, api_base_url=api_base_url)
    if report["summary"]["failed"] > 0:
        raise RuntimeError(build_demo_environment_summary_text(report))
    return report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output/demo", help="Output directory to test for writability")
    parser.add_argument("--api-base-url", help="Optional API base URL to validate through /health")
    parser.add_argument("--output", help="Optional JSON output path for the preflight report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    report = check_demo_environment(
        output_dir=args.output_dir,
        api_base_url=args.api_base_url,
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(build_demo_environment_summary_text(report))
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"Demo environment preflight failed: {exc}")
        raise SystemExit(1)
