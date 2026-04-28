"""Tests for OpenAI-compatible LLM backend comparison helpers."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import backend_from_dict
from scripts.compare_llm_compile_backends import compare_llm_compile_backends, load_backend_configs


def test_backend_from_dict_resolves_api_key_env() -> None:
    os.environ["DEEPSEEK_API_KEY"] = "secret-token"
    backend = backend_from_dict(
        {
            "name": "deepseek-remote",
            "api_base_url": "https://example.com/v1",
            "model": "deepseek-chat",
            "api_key_env": "DEEPSEEK_API_KEY",
            "timeout_seconds": 45,
        }
    )
    assert backend.name == "deepseek-remote"
    assert backend.api_key == "secret-token"
    assert backend.timeout_seconds == 45


def test_load_backend_configs_accepts_wrapped_json_list() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "backends.json"
        path.write_text(
            json.dumps(
                {
                    "backends": [
                        {
                            "name": "mlx-local",
                            "api_base_url": "http://127.0.0.1:8080/v1",
                            "model": "mlx-model",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        backends = load_backend_configs(path)

    assert len(backends) == 1
    assert backends[0].name == "mlx-local"


def test_compare_llm_compile_backends_writes_rule_and_backend_reports() -> None:
    backends = [
        backend_from_dict(
            {
                "name": "deepseek-remote",
                "api_base_url": "https://example.com/v1",
                "model": "deepseek-chat",
            }
        ),
        backend_from_dict(
            {
                "name": "mlx-local",
                "api_base_url": "http://127.0.0.1:8080/v1",
                "model": "mlx-model",
            }
        ),
    ]

    def fake_generator(domain_id: str, **kwargs):
        backend = kwargs.get("llm_backend")
        enable_llm = kwargs.get("enable_llm", True)
        if not enable_llm:
            return {
                "candidate_entries": [
                    {
                        "doc_id": "doc_1",
                        "chunk_id": "chunk_1",
                        "equipment_class_candidate": {"equipment_class_id": "ahu"},
                        "knowledge_object_type": "fault_code",
                        "canonical_key_candidate": "E01",
                        "compile_metadata": {"method": "rule_compiler"},
                    }
                ],
                "metadata": {"candidate_knowledge_types": ["fault_code"]},
            }
        if backend and backend.name == "deepseek-remote":
            return {
                "candidate_entries": [
                    {
                        "doc_id": "doc_1",
                        "chunk_id": "chunk_1",
                        "equipment_class_candidate": {"equipment_class_id": "ahu"},
                        "knowledge_object_type": "maintenance_procedure",
                        "canonical_key_candidate": "coil_cleaning",
                        "compile_metadata": {"method": "llm_compiler"},
                    }
                ],
                "metadata": {"candidate_knowledge_types": ["maintenance_procedure"]},
            }
        return {
            "candidate_entries": [
                {
                    "doc_id": "doc_1",
                    "chunk_id": "chunk_1",
                    "equipment_class_candidate": {"equipment_class_id": "ahu"},
                    "knowledge_object_type": "maintenance_procedure",
                    "canonical_key_candidate": "coil_cleaning",
                    "compile_metadata": {"method": "llm_compiler"},
                },
                {
                    "doc_id": "doc_1",
                    "chunk_id": "chunk_2",
                    "equipment_class_candidate": {"equipment_class_id": "ahu"},
                    "knowledge_object_type": "application_guidance",
                    "canonical_key_candidate": "ahu_sequence",
                    "compile_metadata": {"method": "llm_compiler"},
                },
            ],
            "metadata": {"candidate_knowledge_types": ["application_guidance", "maintenance_procedure"]},
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        report = compare_llm_compile_backends(
            domain_id="hvac",
            output_dir=tmp_dir,
            backends=backends,
            doc_id="doc_1",
            equipment_class_id="ahu",
            generator=fake_generator,
        )
        report_path = Path(report["report_path"])
        assert report_path.exists()
        assert len(report["runs"]) == 3
        assert report["runs"][0]["name"] == "rule-baseline"
        assert report["runs"][1]["name"] == "deepseek-remote"
        assert report["runs"][2]["name"] == "mlx-local"
        assert any(
            item["left"] == "deepseek-remote" and item["right"] == "mlx-local"
            for item in report["overlap_matrix"]
        )
