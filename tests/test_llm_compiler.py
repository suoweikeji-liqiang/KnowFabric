"""Tests for LLM compiler key normalization and constrained candidate output."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.llm_compiler import ChunkContextWindow, compile_llm_candidates, normalize_llm_canonical_key
from packages.db.models import ContentChunk, Document, DocumentPage


def _sample_chunk() -> tuple[ContentChunk, DocumentPage, Document]:
    return (
        ContentChunk(
            chunk_id="chunk_ahu_1",
            doc_id="doc_ahu_1",
            page_id="page_ahu_1",
            page_no=94,
            chunk_index=0,
            cleaned_text="inspect ductwork and calibrate the ahu to deliver the correct airflow rates",
            text_excerpt="inspect ductwork and calibrate the ahu to deliver the correct airflow rates",
            chunk_type="procedure_block",
        ),
        DocumentPage(
            page_id="page_ahu_1",
            doc_id="doc_ahu_1",
            page_no=94,
            cleaned_text="inspect ductwork and calibrate the ahu to deliver the correct airflow rates",
            page_type="maintenance_guide",
        ),
        Document(
            doc_id="doc_ahu_1",
            file_hash="hash_doc_ahu_1",
            storage_path="/tmp/doc_ahu_1.pdf",
            file_name="AHU Maintenance.pdf",
            file_ext="pdf",
            mime_type="application/pdf",
            file_size=1,
            source_domain="hvac",
            parse_status="complete",
            is_active=True,
        ),
    )


def _sample_guidance_chunk() -> tuple[ContentChunk, DocumentPage, Document]:
    return (
        ContentChunk(
            chunk_id="chunk_ahu_guidance_1",
            doc_id="doc_ahu_guidance_1",
            page_id="page_ahu_guidance_1",
            page_no=71,
            chunk_index=0,
            cleaned_text="zone groups served by a single air handler operate together and enter the same mode",
            text_excerpt="zone groups served by a single air handler operate together and enter the same mode",
            chunk_type="guidance_block",
        ),
        DocumentPage(
            page_id="page_ahu_guidance_1",
            doc_id="doc_ahu_guidance_1",
            page_no=71,
            cleaned_text="zone groups served by a single air handler operate together and enter the same mode",
            page_type="application_guide",
        ),
        Document(
            doc_id="doc_ahu_guidance_1",
            file_hash="hash_doc_ahu_guidance_1",
            storage_path="/tmp/doc_ahu_guidance_1.pdf",
            file_name="AHU Application Guidance.pdf",
            file_ext="pdf",
            mime_type="application/pdf",
            file_size=1,
            source_domain="hvac",
            parse_status="complete",
            is_active=True,
        ),
    )


def _sample_spec_chunk() -> tuple[ContentChunk, DocumentPage, Document]:
    return (
        ContentChunk(
            chunk_id="chunk_ahu_spec_1",
            doc_id="doc_ahu_spec_1",
            page_id="page_ahu_spec_1",
            page_no=24,
            chunk_index=0,
            cleaned_text="primary chilled water pump design speed by stage",
            text_excerpt="primary chilled water pump design speed by stage",
            chunk_type="spec_block",
        ),
        DocumentPage(
            page_id="page_ahu_spec_1",
            doc_id="doc_ahu_spec_1",
            page_no=24,
            cleaned_text="primary chilled water pump design speed by stage",
            page_type="technical_manual",
        ),
        Document(
            doc_id="doc_ahu_spec_1",
            file_hash="hash_doc_ahu_spec_1",
            storage_path="/tmp/doc_ahu_spec_1.pdf",
            file_name="AHU Spec Manual.pdf",
            file_ext="pdf",
            mime_type="application/pdf",
            file_size=1,
            source_domain="hvac",
            parse_status="complete",
            is_active=True,
        ),
    )


def test_normalize_llm_canonical_key_namespaces_plain_language_keys() -> None:
    key = normalize_llm_canonical_key(
        "Inspect and calibrate AHU for correct airflow",
        domain_id="hvac",
        equipment_class_id="ahu",
        knowledge_object_type="maintenance_procedure",
        fallback_text="inspect ductwork and calibrate the ahu to deliver the correct airflow rates",
    )
    assert key == "hvac:ahu:maintenance:inspect_and_calibrate_ahu_for_correct_airflow"


def test_normalize_llm_canonical_key_preserves_existing_namespace() -> None:
    key = normalize_llm_canonical_key(
        "HVAC:AHU:Maintenance:Calibrate Airflow",
        domain_id="hvac",
        equipment_class_id="ahu",
        knowledge_object_type="maintenance_procedure",
        fallback_text="ignored",
    )
    assert key == "hvac:ahu:maintenance:calibrate_airflow"


def test_normalize_llm_canonical_key_inserts_missing_type_segment() -> None:
    key = normalize_llm_canonical_key(
        "hvac:ahu:inspect_and_calibrate_airflow",
        domain_id="hvac",
        equipment_class_id="ahu",
        knowledge_object_type="maintenance_procedure",
        fallback_text="inspect ductwork and calibrate the ahu to deliver the correct airflow rates",
    )
    assert key == "hvac:ahu:maintenance:inspect_and_calibrate_airflow"


def test_compile_llm_candidates_normalizes_machine_keys(monkeypatch) -> None:
    chunk, page, document = _sample_chunk()

    def fake_request(_messages, _backend):
        return {
            "candidates": [
                {
                    "knowledge_object_type": "maintenance_procedure",
                    "canonical_key_candidate": "Inspect and calibrate AHU for correct airflow",
                    "structured_payload_candidate": {
                        "task_type": "inspection",
                        "steps": ["Inspect ductwork and calibrate the AHU"],
                    },
                    "confidence_score": 0.91,
                    "rationale": "maintenance instruction detected",
                }
            ]
        }

    monkeypatch.setattr("packages.compiler.llm_compiler._request_json_completion", fake_request)

    payload = compile_llm_candidates(
        domain_id="hvac",
        chunk=chunk,
        page=page,
        document=document,
        equipment_match={
            "equipment_class_id": "ahu",
            "equipment_class_key": "hvac:ahu",
            "label": "AHU",
            "knowledge_anchors": ["maintenance_procedure"],
        },
        context_window=ChunkContextWindow(chunk_ids=["chunk_ahu_1"], combined_text=chunk.cleaned_text),
        backend=type(
            "Backend",
            (),
            {
                "name": "gemma-local",
                "model": "gemma-local",
                "api_base_url": "http://127.0.0.1:7999/v1",
                "api_key": "4496",
                "timeout_seconds": 30,
            },
        )(),
    )

    assert len(payload) == 1
    assert payload[0]["canonical_key_candidate"] == "hvac:ahu:maintenance:inspect_and_calibrate_ahu_for_correct_airflow"


def test_compile_llm_candidates_rejects_application_guidance_on_spec_context(monkeypatch) -> None:
    chunk, page, document = _sample_spec_chunk()

    def fake_request(_messages, _backend):
        return {
            "candidates": [
                {
                    "knowledge_object_type": "application_guidance",
                    "canonical_key_candidate": "hvac:ahu:application:primary_pump_speed_staging",
                    "structured_payload_candidate": {
                        "application_type": "ahu_sequence",
                        "guidance": "Primary pump speed by stage",
                    },
                    "confidence_score": 0.91,
                    "rationale": "should be filtered before request is used",
                }
            ]
        }

    monkeypatch.setattr("packages.compiler.llm_compiler._request_json_completion", fake_request)

    payload = compile_llm_candidates(
        domain_id="hvac",
        chunk=chunk,
        page=page,
        document=document,
        equipment_match={
            "equipment_class_id": "ahu",
            "equipment_class_key": "hvac:ahu",
            "label": "AHU",
            "knowledge_anchors": ["application_guidance"],
        },
        context_window=ChunkContextWindow(chunk_ids=["chunk_ahu_spec_1"], combined_text=chunk.cleaned_text),
        backend=type(
            "Backend",
            (),
            {
                "name": "gemma-local",
                "model": "gemma-local",
                "api_base_url": "http://127.0.0.1:7999/v1",
                "api_key": "4496",
                "timeout_seconds": 30,
            },
        )(),
    )

    assert payload == []


def test_compile_llm_candidates_allows_application_guidance_on_guidance_context(monkeypatch) -> None:
    chunk, page, document = _sample_guidance_chunk()

    def fake_request(_messages, _backend):
        return {
            "candidates": [
                {
                    "knowledge_object_type": "application_guidance",
                    "canonical_key_candidate": "Zone Group Operation",
                    "structured_payload_candidate": {
                        "application_type": "ahu_sequence",
                        "guidance": "Zone groups served by a single air handler operate together.",
                    },
                    "confidence_score": 0.91,
                    "rationale": "guidance text clearly describes a shared operating mode",
                }
            ]
        }

    monkeypatch.setattr("packages.compiler.llm_compiler._request_json_completion", fake_request)

    payload = compile_llm_candidates(
        domain_id="hvac",
        chunk=chunk,
        page=page,
        document=document,
        equipment_match={
            "equipment_class_id": "ahu",
            "equipment_class_key": "hvac:ahu",
            "label": "AHU",
            "knowledge_anchors": ["application_guidance"],
        },
        context_window=ChunkContextWindow(chunk_ids=["chunk_ahu_guidance_1"], combined_text=chunk.cleaned_text),
        backend=type(
            "Backend",
            (),
            {
                "name": "gemma-local",
                "model": "gemma-local",
                "api_base_url": "http://127.0.0.1:7999/v1",
                "api_key": "4496",
                "timeout_seconds": 30,
            },
        )(),
    )

    assert len(payload) == 1
    assert payload[0]["canonical_key_candidate"] == "hvac:ahu:application:zone_group_operation"
