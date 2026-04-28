"""Tests for semantic demo query loading and execution."""

import tempfile
import sys
from pathlib import Path

import yaml
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import (
    ChunkOntologyAnchorV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyClassV2,
    OntologyMappingV2,
)
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.run_semantic_demo_queries import (
    build_semantic_demo_summary_text,
    default_demo_report_path,
    load_semantic_demo_queries,
    run_semantic_demo_queries,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
HVAC_EXAMPLE_FILE = HVAC_V2_ROOT / "examples/example_queries.yaml"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
DRIVE_EXAMPLE_FILE = DRIVE_V2_ROOT / "examples/example_queries.yaml"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        engine,
        tables=[
            Document.__table__,
            DocumentPage.__table__,
            ContentChunk.__table__,
            OntologyClassV2.__table__,
            OntologyAliasV2.__table__,
            OntologyMappingV2.__table__,
            ChunkOntologyAnchorV2.__table__,
            KnowledgeObjectV2.__table__,
            KnowledgeObjectEvidenceV2.__table__,
        ],
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_ontology(session_factory) -> None:
    db = session_factory()
    try:
        for root in (HVAC_V2_ROOT, DRIVE_V2_ROOT):
            bundle = load_domain_package_v2(root)
            db.execute(OntologyClassV2.__table__.insert(), build_ontology_class_rows(bundle))
            db.execute(OntologyAliasV2.__table__.insert(), build_ontology_alias_rows(bundle))
            mapping_rows = build_ontology_mapping_rows(bundle)
            if mapping_rows:
                db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
        db.commit()
    finally:
        db.close()


def _seed_demo_knowledge(session_factory) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_demo_ahu",
                    "file_hash": "hash_demo_ahu",
                    "storage_path": "/tmp/doc_demo_ahu.pdf",
                    "file_name": "Demo AHU Authority.pdf",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1,
                    "source_domain": "hvac",
                    "parse_status": "complete",
                    "is_active": True,
                },
                {
                    "doc_id": "doc_demo_chiller",
                    "file_hash": "hash_demo_chiller",
                    "storage_path": "/tmp/doc_demo_chiller.pdf",
                    "file_name": "Demo Chiller Authority.pdf",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1,
                    "source_domain": "hvac",
                    "parse_status": "complete",
                    "is_active": True,
                },
                {
                    "doc_id": "doc_demo_drive",
                    "file_hash": "hash_demo_drive",
                    "storage_path": "/tmp/doc_demo_drive.pdf",
                    "file_name": "Demo Drive Authority.pdf",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1,
                    "source_domain": "drive",
                    "parse_status": "complete",
                    "is_active": True,
                },
            ],
        )
        db.execute(
            DocumentPage.__table__.insert(),
            [
                {
                    "page_id": "page_demo_ahu_1",
                    "doc_id": "doc_demo_ahu",
                    "page_no": 1,
                    "raw_text": "AHU zone group mode guidance",
                    "cleaned_text": "AHU zone group mode guidance",
                    "page_type": "application_guide",
                },
                {
                    "page_id": "page_demo_ahu_2",
                    "doc_id": "doc_demo_ahu",
                    "page_no": 2,
                    "raw_text": "AHU preventive airflow maintenance plan",
                    "cleaned_text": "AHU preventive airflow maintenance plan",
                    "page_type": "maintenance_guide",
                },
                {
                    "page_id": "page_demo_chiller_1",
                    "doc_id": "doc_demo_chiller",
                    "page_no": 3,
                    "raw_text": "Chiller design capacity guidance",
                    "cleaned_text": "Chiller design capacity guidance",
                    "page_type": "technical_manual",
                },
                {
                    "page_id": "page_demo_drive_fault_1",
                    "doc_id": "doc_demo_drive",
                    "page_no": 10,
                    "raw_text": "Drive fault A7C1 guidance",
                    "cleaned_text": "Drive fault A7C1 guidance",
                    "page_type": "fault_code_reference",
                },
                {
                    "page_id": "page_demo_drive_param_1",
                    "doc_id": "doc_demo_drive",
                    "page_no": 11,
                    "raw_text": "Drive parameter p0604 guidance",
                    "cleaned_text": "Drive parameter p0604 guidance",
                    "page_type": "parameter_manual",
                },
                {
                    "page_id": "page_demo_drive_app_1",
                    "doc_id": "doc_demo_drive",
                    "page_no": 12,
                    "raw_text": "Drive pump and fan application guidance",
                    "cleaned_text": "Drive pump and fan application guidance",
                    "page_type": "application_guide",
                },
                {
                    "page_id": "page_demo_drive_ops_1",
                    "doc_id": "doc_demo_drive",
                    "page_no": 13,
                    "raw_text": "Drive wiring grounding guidance",
                    "cleaned_text": "Drive wiring grounding guidance",
                    "page_type": "commissioning_guide",
                },
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_demo_ahu_1",
                    "doc_id": "doc_demo_ahu",
                    "page_id": "page_demo_ahu_1",
                    "page_no": 1,
                    "chunk_index": 0,
                    "raw_text": "AHU zone group mode guidance",
                    "cleaned_text": "AHU zone group mode guidance",
                    "text_excerpt": "AHU zone group mode guidance",
                    "chunk_type": "guidance_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
                {
                    "chunk_id": "chunk_demo_ahu_2",
                    "doc_id": "doc_demo_ahu",
                    "page_id": "page_demo_ahu_2",
                    "page_no": 2,
                    "chunk_index": 0,
                    "raw_text": "AHU preventive airflow maintenance plan",
                    "cleaned_text": "AHU preventive airflow maintenance plan",
                    "text_excerpt": "AHU preventive airflow maintenance plan",
                    "chunk_type": "procedure_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
                {
                    "chunk_id": "chunk_demo_chiller_1",
                    "doc_id": "doc_demo_chiller",
                    "page_id": "page_demo_chiller_1",
                    "page_no": 3,
                    "chunk_index": 0,
                    "raw_text": "Chiller design capacity guidance",
                    "cleaned_text": "Chiller design capacity guidance",
                    "text_excerpt": "Chiller design capacity guidance",
                    "chunk_type": "spec_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
                {
                    "chunk_id": "chunk_demo_drive_fault_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_fault_1",
                    "page_no": 10,
                    "chunk_index": 0,
                    "raw_text": "Drive fault A7C1 guidance",
                    "cleaned_text": "Drive fault A7C1 guidance",
                    "text_excerpt": "Drive fault A7C1 guidance",
                    "chunk_type": "fault_code_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
                {
                    "chunk_id": "chunk_demo_drive_param_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_param_1",
                    "page_no": 11,
                    "chunk_index": 0,
                    "raw_text": "Drive parameter p0604 guidance",
                    "cleaned_text": "Drive parameter p0604 guidance",
                    "text_excerpt": "Drive parameter p0604 guidance",
                    "chunk_type": "parameter_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
                {
                    "chunk_id": "chunk_demo_drive_app_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_app_1",
                    "page_no": 12,
                    "chunk_index": 0,
                    "raw_text": "Drive pump and fan application guidance",
                    "cleaned_text": "Drive pump and fan application guidance",
                    "text_excerpt": "Drive pump and fan application guidance",
                    "chunk_type": "guidance_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
                {
                    "chunk_id": "chunk_demo_drive_ops_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_ops_1",
                    "page_no": 13,
                    "chunk_index": 0,
                    "raw_text": "Drive wiring grounding guidance",
                    "cleaned_text": "Drive wiring grounding guidance",
                    "text_excerpt": "Drive wiring grounding guidance",
                    "chunk_type": "wiring_block",
                    "evidence_anchor": "{\"line\": 1}",
                },
            ],
        )
        db.execute(
            ChunkOntologyAnchorV2.__table__.insert(),
            [
                {
                    "chunk_anchor_id": "anchor_demo_ahu_1",
                    "chunk_id": "chunk_demo_ahu_1",
                    "ontology_class_key": "hvac:ahu",
                    "domain_id": "hvac",
                    "ontology_class_id": "ahu",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
                {
                    "chunk_anchor_id": "anchor_demo_ahu_2",
                    "chunk_id": "chunk_demo_ahu_2",
                    "ontology_class_key": "hvac:ahu",
                    "domain_id": "hvac",
                    "ontology_class_id": "ahu",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
                {
                    "chunk_anchor_id": "anchor_demo_chiller_1",
                    "chunk_id": "chunk_demo_chiller_1",
                    "ontology_class_key": "hvac:chiller",
                    "domain_id": "hvac",
                    "ontology_class_id": "chiller",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
                {
                    "chunk_anchor_id": "anchor_demo_drive_fault_1",
                    "chunk_id": "chunk_demo_drive_fault_1",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "domain_id": "drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
                {
                    "chunk_anchor_id": "anchor_demo_drive_param_1",
                    "chunk_id": "chunk_demo_drive_param_1",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "domain_id": "drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
                {
                    "chunk_anchor_id": "anchor_demo_drive_app_1",
                    "chunk_id": "chunk_demo_drive_app_1",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "domain_id": "drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
                {
                    "chunk_anchor_id": "anchor_demo_drive_ops_1",
                    "chunk_id": "chunk_demo_drive_ops_1",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "domain_id": "drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "match_method": "seed",
                    "confidence_score": 0.9,
                    "is_primary": True,
                    "match_metadata_json": {"source": "test"},
                },
            ],
        )
        db.execute(
            KnowledgeObjectV2.__table__.insert(),
            [
                {
                    "knowledge_object_id": "ko_demo_ahu_app",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:ahu",
                    "ontology_class_id": "ahu",
                    "knowledge_object_type": "application_guidance",
                    "canonical_key": "ahu_zone_group_operating_mode",
                    "title": "Demo AHU Zone Group Operating Mode",
                    "summary": "Zone groups served by one AHU operate in the same mode.",
                    "structured_payload_json": {
                        "application_type": "ahu_sequence",
                        "guidance": "All zones in a zone group move together into the same operating mode.",
                    },
                    "applicability_json": {},
                    "confidence_score": 0.9,
                    "trust_level": "L3",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_ahu_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_demo_ahu_maint",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:ahu",
                    "ontology_class_id": "ahu",
                    "knowledge_object_type": "maintenance_procedure",
                    "canonical_key": "ahu_preventive_airflow_maintenance_plan",
                    "title": "Demo AHU Preventive Airflow Maintenance Plan",
                    "summary": "Run preventive maintenance for airflow reliability.",
                    "structured_payload_json": {
                        "maintenance_task": "maintenance",
                        "task_type": "maintenance",
                        "steps": ["Clean filters", "Inspect dampers", "Clean coils"],
                    },
                    "applicability_json": {},
                    "confidence_score": 0.88,
                    "trust_level": "L3",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_ahu_2",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_demo_chiller_capacity",
                    "domain_id": "hvac",
                    "ontology_class_key": "hvac:chiller",
                    "ontology_class_id": "chiller",
                    "knowledge_object_type": "performance_spec",
                    "canonical_key": "design_chiller_capacity",
                    "title": "Demo Chiller Design Capacity",
                    "summary": "Design capacity should be defined in tons.",
                    "structured_payload_json": {
                        "parameter_name": "design_capacity",
                        "parameter_category": "capacity",
                        "rated_value": "QchX in tons",
                    },
                    "applicability_json": {},
                    "confidence_score": 0.93,
                    "trust_level": "L3",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_chiller_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_demo_drive_fault",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "fault_code",
                    "canonical_key": "A7C1",
                    "title": "Demo Drive Fault A7C1",
                    "summary": "Drive communication warning fault.",
                    "structured_payload_json": {
                        "fault_code": "A7C1",
                        "fault_name": "Fieldbus Adapter A Communication",
                    },
                    "applicability_json": {"brand": "ABB", "model_family": "ACH531"},
                    "confidence_score": 0.92,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_drive_fault_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_demo_drive_param",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "parameter_spec",
                    "canonical_key": "p0604_motor_temperature_alarm_threshold",
                    "title": "Demo Drive Parameter p0604",
                    "summary": "Motor temperature alarm threshold parameter.",
                    "structured_payload_json": {
                        "parameter_name": "p0604",
                        "parameter_category": "temperature_protection",
                    },
                    "applicability_json": {"brand": "Siemens", "model_family": "G120XA"},
                    "confidence_score": 0.92,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_drive_param_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_demo_drive_app",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "application_guidance",
                    "canonical_key": "pump_fan_application_control",
                    "title": "Demo Drive Pump and Fan Application Control",
                    "summary": "Use the drive for pump and fan applications.",
                    "structured_payload_json": {
                        "application_type": "pump_fan",
                        "guidance": "Use the drive application functions for pump and fan control.",
                    },
                    "applicability_json": {"brand": "Danfoss", "model_family": "FC111"},
                    "confidence_score": 0.86,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_drive_app_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
                {
                    "knowledge_object_id": "ko_demo_drive_ops",
                    "domain_id": "drive",
                    "ontology_class_key": "drive:variable_frequency_drive",
                    "ontology_class_id": "variable_frequency_drive",
                    "knowledge_object_type": "wiring_guidance",
                    "canonical_key": "shield_grounding_control_cable_shield_360",
                    "title": "Demo Drive Shield Grounding",
                    "summary": "Ground the control cable shield 360 degrees.",
                    "structured_payload_json": {
                        "wiring_topic": "shield_grounding",
                        "guidance": "Ground the external shield of the control cable 360 degrees.",
                    },
                    "applicability_json": {"brand": "ABB", "model_family": "ACH531"},
                    "confidence_score": 0.87,
                    "trust_level": "L2",
                    "review_status": "approved",
                    "primary_chunk_id": "chunk_demo_drive_ops_1",
                    "package_version": "2.0.0-alpha",
                    "ontology_version": "2.0.0-alpha",
                },
            ],
        )
        db.execute(
            KnowledgeObjectEvidenceV2.__table__.insert(),
            [
                {
                    "knowledge_evidence_id": "koev_demo_ahu_app",
                    "knowledge_object_id": "ko_demo_ahu_app",
                    "chunk_id": "chunk_demo_ahu_1",
                    "doc_id": "doc_demo_ahu",
                    "page_id": "page_demo_ahu_1",
                    "page_no": 1,
                    "evidence_text": "All zones in a zone group move together into the same operating mode.",
                    "evidence_role": "primary",
                    "confidence_score": 0.9,
                },
                {
                    "knowledge_evidence_id": "koev_demo_ahu_maint",
                    "knowledge_object_id": "ko_demo_ahu_maint",
                    "chunk_id": "chunk_demo_ahu_2",
                    "doc_id": "doc_demo_ahu",
                    "page_id": "page_demo_ahu_2",
                    "page_no": 2,
                    "evidence_text": "Clean filters, inspect dampers, and clean coils.",
                    "evidence_role": "primary",
                    "confidence_score": 0.88,
                },
                {
                    "knowledge_evidence_id": "koev_demo_chiller_capacity",
                    "knowledge_object_id": "ko_demo_chiller_capacity",
                    "chunk_id": "chunk_demo_chiller_1",
                    "doc_id": "doc_demo_chiller",
                    "page_id": "page_demo_chiller_1",
                    "page_no": 3,
                    "evidence_text": "QchX is the design capacity of Chiller X in tons.",
                    "evidence_role": "primary",
                    "confidence_score": 0.93,
                },
                {
                    "knowledge_evidence_id": "koev_demo_drive_fault",
                    "knowledge_object_id": "ko_demo_drive_fault",
                    "chunk_id": "chunk_demo_drive_fault_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_fault_1",
                    "page_no": 10,
                    "evidence_text": "A7C1 drive communication fault.",
                    "evidence_role": "primary",
                    "confidence_score": 0.92,
                },
                {
                    "knowledge_evidence_id": "koev_demo_drive_param",
                    "knowledge_object_id": "ko_demo_drive_param",
                    "chunk_id": "chunk_demo_drive_param_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_param_1",
                    "page_no": 11,
                    "evidence_text": "p0604 defines the motor temperature alarm threshold.",
                    "evidence_role": "primary",
                    "confidence_score": 0.92,
                },
                {
                    "knowledge_evidence_id": "koev_demo_drive_app",
                    "knowledge_object_id": "ko_demo_drive_app",
                    "chunk_id": "chunk_demo_drive_app_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_app_1",
                    "page_no": 12,
                    "evidence_text": "Use the drive application functions for pump and fan control.",
                    "evidence_role": "primary",
                    "confidence_score": 0.86,
                },
                {
                    "knowledge_evidence_id": "koev_demo_drive_ops",
                    "knowledge_object_id": "ko_demo_drive_ops",
                    "chunk_id": "chunk_demo_drive_ops_1",
                    "doc_id": "doc_demo_drive",
                    "page_id": "page_demo_drive_ops_1",
                    "page_no": 13,
                    "evidence_text": "Ground the external shield of the control cable 360 degrees.",
                    "evidence_role": "primary",
                    "confidence_score": 0.87,
                },
            ],
        )
        db.commit()
    finally:
        db.close()


def test_load_semantic_demo_queries_reads_hvac_example_file() -> None:
    examples = load_semantic_demo_queries(HVAC_EXAMPLE_FILE)
    ids = {item["id"] for item in examples}
    assert "ahu_application_guidance_demo" in ids
    assert "cooling_tower_parameter_profile_demo" in ids
    assert len(examples) >= 6


def test_load_semantic_demo_queries_reads_drive_example_file() -> None:
    examples = load_semantic_demo_queries(DRIVE_EXAMPLE_FILE)
    ids = {item["id"] for item in examples}
    assert "drive_fault_knowledge_demo" in ids
    assert "drive_operational_guidance_demo" in ids
    assert len(examples) >= 4


def test_run_semantic_demo_queries_executes_expected_queries(monkeypatch) -> None:
    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_demo_knowledge(session_factory)
    monkeypatch.setattr("scripts.run_semantic_demo_queries.SessionLocal", session_factory)

    payload = {
        "examples": [
            {
                "id": "ahu_application_demo",
                "description": "Application guidance check for AHU.",
                "query": "application guidance for ahu",
                "query_type": "application_guidance",
                "expected_contract": "application_guidance_by_equipment_class",
                "request": {
                    "domain_id": "hvac",
                    "equipment_class_id": "ahu",
                    "application_type": "ahu_sequence",
                    "min_trust_level": "L3",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["ahu_zone_group_operating_mode"],
            },
            {
                "id": "ahu_maintenance_demo",
                "description": "Maintenance guidance check for AHU.",
                "query": "maintenance guidance for ahu",
                "query_type": "maintenance_guidance",
                "expected_contract": "maintenance_guidance_by_equipment_class",
                "request": {
                    "domain_id": "hvac",
                    "equipment_class_id": "ahu",
                    "min_trust_level": "L3",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["ahu_preventive_airflow_maintenance_plan"],
            },
            {
                "id": "chiller_profile_demo",
                "description": "Parameter profile check for chiller.",
                "query": "parameter profile for chiller",
                "query_type": "parameter_profile",
                "expected_contract": "parameter_profile_by_equipment_class",
                "request": {
                    "domain_id": "hvac",
                    "equipment_class_id": "chiller",
                    "min_trust_level": "L3",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["design_chiller_capacity"],
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        example_path = Path(tmp_dir) / "demo_queries.yaml"
        example_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        report = run_semantic_demo_queries(example_path)

    assert report["summary"] == {
        "total_examples": 3,
        "passed": 3,
        "failed": 0,
    }
    assert all(item["status"] == "passed" for item in report["results"])
    summary_text = build_semantic_demo_summary_text(report)
    assert "Semantic Demo Query Summary" in summary_text
    assert "PASS" in summary_text
    assert all(item["required_review_status"] == "approved" for item in report["results"])


def test_run_semantic_demo_queries_supports_drive_queries(monkeypatch) -> None:
    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_demo_knowledge(session_factory)
    monkeypatch.setattr("scripts.run_semantic_demo_queries.SessionLocal", session_factory)

    payload = {
        "examples": [
            {
                "id": "drive_fault_demo",
                "description": "Fault knowledge check for drive.",
                "query": "fault knowledge for drive A7C1",
                "query_type": "fault_knowledge",
                "expected_contract": "fault_knowledge_by_equipment_class",
                "request": {
                    "domain_id": "drive",
                    "equipment_class_id": "variable_frequency_drive",
                    "fault_code": "A7C1",
                    "min_trust_level": "L2",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["A7C1"],
            },
            {
                "id": "drive_parameter_demo",
                "description": "Parameter profile check for drive.",
                "query": "parameter profile for drive p0604",
                "query_type": "parameter_profile",
                "expected_contract": "parameter_profile_by_equipment_class",
                "request": {
                    "domain_id": "drive",
                    "equipment_class_id": "variable_frequency_drive",
                    "parameter_name": "p0604",
                    "min_trust_level": "L2",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["p0604_motor_temperature_alarm_threshold"],
            },
            {
                "id": "drive_application_demo",
                "description": "Application guidance check for drive.",
                "query": "application guidance for drive pump fan",
                "query_type": "application_guidance",
                "expected_contract": "application_guidance_by_equipment_class",
                "request": {
                    "domain_id": "drive",
                    "equipment_class_id": "variable_frequency_drive",
                    "application_type": "pump_fan",
                    "min_trust_level": "L2",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["pump_fan_application_control"],
            },
            {
                "id": "drive_operational_demo",
                "description": "Operational guidance check for drive.",
                "query": "operational guidance for drive wiring",
                "query_type": "operational_guidance",
                "expected_contract": "operational_guidance_by_equipment_class",
                "request": {
                    "domain_id": "drive",
                    "equipment_class_id": "variable_frequency_drive",
                    "guidance_type": "wiring_guidance",
                    "min_trust_level": "L2",
                    "limit": 5,
                },
                "required_review_status": "approved",
                "expected_canonical_keys": ["shield_grounding_control_cable_shield_360"],
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        example_path = Path(tmp_dir) / "drive_demo_queries.yaml"
        example_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        report = run_semantic_demo_queries(example_path)

    assert report["summary"] == {
        "total_examples": 4,
        "passed": 4,
        "failed": 0,
    }
    assert all(item["status"] == "passed" for item in report["results"])


def test_run_semantic_demo_queries_fails_when_review_status_does_not_match(monkeypatch) -> None:
    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_demo_knowledge(session_factory)
    monkeypatch.setattr("scripts.run_semantic_demo_queries.SessionLocal", session_factory)

    payload = {
        "examples": [
            {
                "id": "strict_status_demo",
                "description": "Require a wrong review status to force failure.",
                "query": "application guidance for ahu",
                "query_type": "application_guidance",
                "expected_contract": "application_guidance_by_equipment_class",
                "request": {
                    "domain_id": "hvac",
                    "equipment_class_id": "ahu",
                    "application_type": "ahu_sequence",
                    "min_trust_level": "L3",
                    "limit": 5,
                },
                "required_review_status": "pending",
                "expected_canonical_keys": ["ahu_zone_group_operating_mode"],
            },
        ]
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        example_path = Path(tmp_dir) / "strict_demo_queries.yaml"
        example_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        report = run_semantic_demo_queries(example_path)

    assert report["summary"] == {
        "total_examples": 1,
        "passed": 0,
        "failed": 1,
    }
    assert report["results"][0]["wrong_review_status_canonical_keys"] == ["ahu_zone_group_operating_mode"]


def test_default_demo_report_path_uses_stable_name() -> None:
    path = default_demo_report_path("domain_packages/drive/v2/examples/example_queries.yaml", "output/demo")
    assert str(path) == "output/demo/drive__example_queries__semantic_demo_report.json"
