#!/usr/bin/env python3
"""Bootstrap the v1 demo knowledge store and generate demo artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.check_demo_environment import ensure_demo_environment_ready
from scripts.demo_bundle_inventory import (
    DEFAULT_DOMAINS,
    DEFAULT_EXAMPLE_QUERY_FILES,
    default_demo_fixture_paths as inventory_demo_fixture_paths,
)
from scripts.build_v1_demo_brief import build_v1_demo_brief
from scripts.run_api_demo_smoke import default_api_smoke_report_path, run_api_demo_smoke
from scripts.run_mcp_demo_smoke import default_mcp_smoke_report_path, run_mcp_demo_smoke
from scripts.run_semantic_demo_queries import default_demo_report_path, run_semantic_demo_queries
from scripts.seed_manual_validation_fixtures import seed_manual_fixture
from scripts.sync_ontology_package_v2 import sync_domain_package

def default_demo_fixture_paths() -> list[Path]:
    """Return the committed fixture paths required for the v1 demo."""

    return inventory_demo_fixture_paths()


def upgrade_database(config_path: str | Path = "alembic.ini") -> None:
    """Apply migrations through Alembic."""

    command.upgrade(Config(str(config_path)), "head")


def sync_demo_ontologies(domains: tuple[str, ...] = DEFAULT_DOMAINS) -> list[dict[str, Any]]:
    """Sync the ontology metadata for the demo domains."""

    results = []
    for domain_id in domains:
        domain, class_count, alias_count, mapping_count = sync_domain_package(Path("domain_packages") / domain_id / "v2")
        results.append(
            {
                "domain_id": domain,
                "class_count": class_count,
                "alias_count": alias_count,
                "mapping_count": mapping_count,
            }
        )
    return results


def seed_demo_knowledge(fixture_paths: list[Path] | None = None) -> list[dict[str, Any]]:
    """Seed the committed v1 demo fixtures."""

    results = []
    for path in fixture_paths or default_demo_fixture_paths():
        equipment_class_key, knowledge_count = seed_manual_fixture(path)
        results.append(
            {
                "fixture_path": str(path),
                "equipment_class_key": equipment_class_key,
                "knowledge_count": knowledge_count,
            }
        )
    return results


def run_demo_reports(example_query_files: tuple[str, ...] = DEFAULT_EXAMPLE_QUERY_FILES, output_dir: str | Path = "output/demo") -> list[dict[str, Any]]:
    """Run the fixed domain demo query files and write their JSON reports."""

    reports = []
    for example_path in example_query_files:
        report = run_semantic_demo_queries(example_path)
        report_path = default_demo_report_path(example_path, output_dir)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports.append(
            {
                "example_file": example_path,
                "report_path": str(report_path),
                "passed": report["summary"]["passed"],
                "failed": report["summary"]["failed"],
            }
        )
    return reports


def run_mcp_smoke_reports(
    example_query_files: tuple[str, ...] = DEFAULT_EXAMPLE_QUERY_FILES,
    output_dir: str | Path = "output/demo",
) -> list[dict[str, Any]]:
    """Run the fixed domain demo query files against the MCP tool surface."""

    reports = []
    for example_path in example_query_files:
        report = run_mcp_demo_smoke(example_path)
        report_path = default_mcp_smoke_report_path(example_path, output_dir)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports.append(
            {
                "example_file": example_path,
                "report_path": str(report_path),
                "passed": report["summary"]["passed"],
                "failed": report["summary"]["failed"],
                "initialize_ok": report["initialize_ok"],
                "tools_list_ok": report["tools_list_ok"],
            }
        )
    return reports


def run_api_smoke_reports(
    base_url: str,
    example_query_files: tuple[str, ...] = DEFAULT_EXAMPLE_QUERY_FILES,
    output_dir: str | Path = "output/demo",
) -> list[dict[str, Any]]:
    """Run the fixed domain demo query files against a live API service."""

    reports = []
    for example_path in example_query_files:
        report = run_api_demo_smoke(example_path, base_url=base_url)
        report_path = default_api_smoke_report_path(example_path, output_dir)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports.append(
            {
                "example_file": example_path,
                "report_path": str(report_path),
                "passed": report["summary"]["passed"],
                "failed": report["summary"]["failed"],
                "health_status": report["health"]["status"],
                "health_http_status": report["health"]["http_status"],
            }
        )
    return reports


def bootstrap_v1_demo(
    *,
    output_dir: str | Path = "output/demo",
    brief_path: str | Path = "output/demo/v1_demo_brief.md",
    config_path: str | Path = "alembic.ini",
    run_preflight: bool = True,
    run_mcp_smoke: bool = True,
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Upgrade DB, sync ontology, seed demo knowledge, run demo queries, and build the brief."""

    preflight = ensure_demo_environment_ready(output_dir=output_dir, api_base_url=api_base_url) if run_preflight else None
    upgrade_database(config_path)
    ontology_sync = sync_demo_ontologies()
    seeded = seed_demo_knowledge()
    reports = run_demo_reports(output_dir=output_dir)
    mcp_reports = run_mcp_smoke_reports(output_dir=output_dir) if run_mcp_smoke else []
    api_reports = run_api_smoke_reports(api_base_url, output_dir=output_dir) if api_base_url else []
    brief_target = build_v1_demo_brief(
        report_paths=[item["report_path"] for item in reports],
        report_dir=output_dir,
        output_path=brief_path,
    )
    return {
        "bootstrap_mode": "v1_demo_bootstrap",
        "preflight": preflight,
        "ontology_sync": ontology_sync,
        "seeded_fixtures": seeded,
        "reports": reports,
        "mcp_reports": mcp_reports,
        "api_reports": api_reports,
        "brief_path": str(brief_target),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output/demo", help="Directory for generated demo reports")
    parser.add_argument("--brief-output", default="output/demo/v1_demo_brief.md", help="Markdown brief output path")
    parser.add_argument("--alembic-config", default="alembic.ini", help="Alembic config path")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip the environment preflight checks")
    parser.add_argument("--skip-mcp-smoke", action="store_true", help="Skip the in-process MCP smoke run")
    parser.add_argument("--api-base-url", help="Optional base URL for a running API service to include live HTTP smoke")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = bootstrap_v1_demo(
        output_dir=args.output_dir,
        brief_path=args.brief_output,
        config_path=args.alembic_config,
        run_preflight=not args.skip_preflight,
        run_mcp_smoke=not args.skip_mcp_smoke,
        api_base_url=args.api_base_url,
    )
    api_status = "skipped" if not result["api_reports"] else str(sum(item["passed"] for item in result["api_reports"]))
    mcp_status = "skipped" if not result["mcp_reports"] else str(sum(item["passed"] for item in result["mcp_reports"]))
    print(
        f"Bootstrapped v1 demo with {len(result['seeded_fixtures'])} fixture file(s), "
        f"{sum(item['passed'] for item in result['reports'])} passing semantic checks, "
        f"mcp={mcp_status}, "
        f"api={api_status}, "
        f"brief={result['brief_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"V1 demo bootstrap failed: {exc}")
        raise SystemExit(1)
