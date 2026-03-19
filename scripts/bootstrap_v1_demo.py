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

from scripts.build_v1_demo_brief import build_v1_demo_brief
from scripts.run_semantic_demo_queries import default_demo_report_path, run_semantic_demo_queries
from scripts.seed_manual_validation_fixtures import seed_manual_fixture
from scripts.sync_ontology_package_v2 import sync_domain_package

DEFAULT_DOMAINS = ("hvac", "drive")
DEFAULT_FIXTURE_PATHS = (
    "tests/fixtures/manual_validation/hvac_demo_ahu_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_chiller_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_condenser_water_pump_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_chilled_water_pump_authority.json",
    "tests/fixtures/manual_validation/hvac_demo_cooling_tower_authority.json",
    "tests/fixtures/manual_validation/drive_vfd_faults.json",
    "tests/fixtures/manual_validation/drive_parameter_profiles.json",
    "tests/fixtures/manual_validation/drive_application_guidance.json",
    "tests/fixtures/manual_validation/drive_commissioning_guidance.json",
)
DEFAULT_EXAMPLE_QUERY_FILES = (
    "domain_packages/hvac/v2/examples/example_queries.yaml",
    "domain_packages/drive/v2/examples/example_queries.yaml",
)


def default_demo_fixture_paths() -> list[Path]:
    """Return the committed fixture paths required for the v1 demo."""

    return [Path(path) for path in DEFAULT_FIXTURE_PATHS]


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


def bootstrap_v1_demo(
    *,
    output_dir: str | Path = "output/demo",
    brief_path: str | Path = "output/demo/v1_demo_brief.md",
    config_path: str | Path = "alembic.ini",
) -> dict[str, Any]:
    """Upgrade DB, sync ontology, seed demo knowledge, run demo queries, and build the brief."""

    upgrade_database(config_path)
    ontology_sync = sync_demo_ontologies()
    seeded = seed_demo_knowledge()
    reports = run_demo_reports(output_dir=output_dir)
    brief_target = build_v1_demo_brief(
        report_paths=[item["report_path"] for item in reports],
        output_path=brief_path,
    )
    return {
        "bootstrap_mode": "v1_demo_bootstrap",
        "ontology_sync": ontology_sync,
        "seeded_fixtures": seeded,
        "reports": reports,
        "brief_path": str(brief_target),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output/demo", help="Directory for generated demo reports")
    parser.add_argument("--brief-output", default="output/demo/v1_demo_brief.md", help="Markdown brief output path")
    parser.add_argument("--alembic-config", default="alembic.ini", help="Alembic config path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    result = bootstrap_v1_demo(
        output_dir=args.output_dir,
        brief_path=args.brief_output,
        config_path=args.alembic_config,
    )
    print(
        f"Bootstrapped v1 demo with {len(result['seeded_fixtures'])} fixture file(s), "
        f"{sum(item['passed'] for item in result['reports'])} passing query checks, "
        f"brief={result['brief_path']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - script exit path
        print(f"V1 demo bootstrap failed: {exc}")
        raise SystemExit(1)
