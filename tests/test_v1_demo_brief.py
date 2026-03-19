"""Tests for the v1 demo brief builder."""

import json
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_v1_demo_brief import (
    build_v1_demo_brief,
    build_v1_demo_brief_markdown,
    discover_demo_report_paths,
)


def _sample_report(domain: str, query_type: str, equipment_class_id: str, canonical_keys: list[str]) -> dict:
    return {
        "demo_mode": "semantic_example_query_runner",
        "generated_at": "2026-03-19T12:00:00+00:00",
        "example_file": f"domain_packages/{domain}/v2/examples/example_queries.yaml",
        "summary": {
            "total_examples": 1,
            "passed": 1,
            "failed": 0,
        },
        "results": [
            {
                "id": f"{domain}_{query_type}_demo",
                "description": "sample",
                "query": "sample query",
                "query_type": query_type,
                "expected_contract": "sample_contract",
                "request": {
                    "domain_id": domain,
                    "equipment_class_id": equipment_class_id,
                },
                "status": "passed",
                "item_count": len(canonical_keys),
                "found_canonical_keys": canonical_keys,
                "found_review_statuses": {key: "approved" for key in canonical_keys},
                "expected_canonical_keys": canonical_keys,
                "missing_canonical_keys": [],
                "required_review_status": "approved",
                "wrong_review_status_canonical_keys": [],
            }
        ],
    }


def test_build_v1_demo_brief_markdown_summarizes_domains_and_keys() -> None:
    rendered = build_v1_demo_brief_markdown(
        [
            _sample_report("hvac", "application_guidance", "ahu", ["ahu_zone_group_operating_mode"]),
            _sample_report("drive", "fault_knowledge", "variable_frequency_drive", ["A7C1"]),
        ]
    )

    assert "# KnowFabric V1 Demo Brief" in rendered
    assert "Domains covered: 2" in rendered
    assert "### Hvac" in rendered
    assert "### Drive" in rendered
    assert "`ahu_zone_group_operating_mode`" in rendered
    assert "`A7C1`" in rendered


def test_build_v1_demo_brief_discovers_reports_and_writes_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_dir = Path(tmp_dir) / "demo"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "hvac__example_queries__semantic_demo_report.json").write_text(
            json.dumps(_sample_report("hvac", "parameter_profile", "chiller", ["design_chiller_capacity"])) + "\n",
            encoding="utf-8",
        )
        (report_dir / "drive__example_queries__semantic_demo_report.json").write_text(
            json.dumps(_sample_report("drive", "fault_knowledge", "variable_frequency_drive", ["A7C1"])) + "\n",
            encoding="utf-8",
        )

        discovered = discover_demo_report_paths(report_dir)
        assert len(discovered) == 2

        output_path = report_dir / "v1_demo_brief.md"
        target = build_v1_demo_brief(report_dir=report_dir, output_path=output_path)

        assert target == output_path
        rendered = output_path.read_text(encoding="utf-8")
        assert "design_chiller_capacity" in rendered
        assert "A7C1" in rendered
