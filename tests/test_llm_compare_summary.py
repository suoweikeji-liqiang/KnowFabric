"""Tests for Markdown compare-summary rendering."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_llm_compile_compare_summary import build_llm_compile_compare_summary


def test_build_llm_compile_compare_summary_lists_unique_candidates() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        (base / "rule_baseline_candidates.json").write_text(
            json.dumps(
                {
                    "candidate_entries": [
                        {"canonical_key_candidate": "rule_key_a"},
                        {"canonical_key_candidate": "rule_key_b"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        (base / "deepseek-remote__candidates.json").write_text(
            json.dumps(
                {
                    "candidate_entries": [
                        {"canonical_key_candidate": "rule_key_a"},
                        {"canonical_key_candidate": "rule_key_b"},
                        {"canonical_key_candidate": "llm_key_c"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        report_path = base / "llm_compile_backend_compare_report.json"
        report_path.write_text(
            json.dumps(
                {
                    "domain_id": "hvac",
                    "filters_applied": {"equipment_class_id": "ahu"},
                    "runs": [
                        {
                            "name": "rule-baseline",
                            "candidate_path": str(base / "rule_baseline_candidates.json"),
                            "candidate_count": 2,
                            "compiler_methods": ["rule_compiler"],
                            "knowledge_types": ["maintenance_procedure"],
                        },
                        {
                            "name": "deepseek-remote",
                            "candidate_path": str(base / "deepseek-remote__candidates.json"),
                            "candidate_count": 3,
                            "compiler_methods": ["llm_compiler", "rule_compiler"],
                            "knowledge_types": ["maintenance_procedure"],
                        },
                    ],
                    "overlap_matrix": [
                        {
                            "left": "rule-baseline",
                            "right": "deepseek-remote",
                            "shared_candidates": 2,
                            "left_total": 2,
                            "right_total": 3,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        summary = build_llm_compile_compare_summary(report_path)

    assert "# LLM Compile Compare Summary" in summary
    assert "`deepseek-remote`" in summary
    assert "unique_over_baseline: llm_key_c" in summary
    assert "shared=2" in summary
