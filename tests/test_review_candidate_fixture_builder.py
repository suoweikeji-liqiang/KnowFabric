"""Tests for reviewed chunk-candidate fixture building."""

import json
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
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
from packages.domain_kit_v2.manual_fixture import build_manual_fixture_rows, load_manual_fixture
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
)
from scripts.backfill_manual_knowledge_from_chunks import backfill_manual_fixture_from_chunks
from scripts.build_manual_fixture_from_review_candidates import (
    build_manual_fixture_from_review_candidate_file,
    build_manual_fixture_from_review_candidates,
)
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"
DRIVE_PARAMETER_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/drive_parameter_profiles.json"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
            db.execute(OntologyMappingV2.__table__.insert(), build_ontology_mapping_rows(bundle))
        db.commit()
    finally:
        db.close()


def _seed_fixture_chunks(session_factory, fixture_path: Path) -> None:
    fixture = load_manual_fixture(fixture_path)
    rows = build_manual_fixture_rows(fixture)
    db = session_factory()
    try:
        db.execute(Document.__table__.insert(), rows["documents"])
        db.execute(DocumentPage.__table__.insert(), rows["pages"])
        db.execute(ContentChunk.__table__.insert(), rows["chunks"])
        db.commit()
    finally:
        db.close()


def _review_payload_for_hvac_faults(session_factory) -> dict:
    payload = generate_chunk_backfill_candidates(
        "hvac",
        doc_id="doc_aux_module_faults",
        equipment_class_id="air_cooled_modular_heat_pump",
    )
    accepted = {
        "E22": {
            "title": "Reviewed AUX E22 High Pressure Switch Protection",
            "summary": "Reviewed from chunk candidate and confirmed as high-pressure protection.",
            "structured_payload": {
                "fault_code": "E22",
                "fault_name": "High Pressure Switch Protection",
                "recommended_actions": [
                    "Inspect the high-pressure switch state",
                    "Check condenser airflow",
                ],
            },
            "applicability": {"brand": "AUX", "model_family": "X Module Unit"},
            "trust_level": "L2",
        }
    }
    for entry in payload["candidate_entries"]:
        if entry["canonical_key_candidate"] in accepted:
            entry["review_decision"] = "accepted"
            entry["curation"] = accepted[entry["canonical_key_candidate"]]
        else:
            entry["review_decision"] = "rejected"
    return payload


def _review_payload_for_drive_parameters(session_factory) -> dict:
    payload = generate_chunk_backfill_candidates(
        "drive",
        doc_id="doc_siemens_g120xa_manual",
        equipment_class_id="variable_frequency_drive",
    )
    curated = {
        "p0604": {
            "title": "Reviewed Siemens p0604 Motor Temperature Alarm Threshold",
            "summary": "Reviewed parameter candidate for the alarm threshold row.",
            "structured_payload": {
                "parameter_name": "p0604",
                "parameter_category": "temperature_protection",
                "default_value": "130 C",
            },
            "applicability": {"brand": "Siemens", "model_family": "G120XA"},
            "trust_level": "L2",
        },
        "p0605": {
            "title": "Reviewed Siemens p0605 Motor Temperature Fault Threshold",
            "summary": "Reviewed parameter candidate for the fault threshold row.",
            "structured_payload": {
                "parameter_name": "p0605",
                "parameter_category": "temperature_protection",
                "default_value": "145 C",
            },
            "applicability": {"brand": "Siemens", "model_family": "G120XA"},
            "trust_level": "L2",
        },
    }
    for entry in payload["candidate_entries"]:
        entry["review_decision"] = "accepted"
        entry["curation"] = curated[entry["canonical_key_candidate"]]
    return payload


def test_build_manual_fixture_from_review_candidates_for_hvac(monkeypatch) -> None:
    """Accepted fault review candidates should convert into one manual fixture."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = _review_payload_for_hvac_faults(session_factory)
    db = session_factory()
    try:
        fixture = build_manual_fixture_from_review_candidates(payload, db)
    finally:
        db.close()

    assert fixture["equipment_class_id"] == "air_cooled_modular_heat_pump"
    assert len(fixture["manual_entries"]) == 1
    entry = fixture["manual_entries"][0]
    assert entry["knowledge_object_type"] == "fault_code"
    assert entry["canonical_key"] == "E22"
    assert entry["doc"]["doc_id"] == "doc_aux_module_faults"
    assert entry["source_manual"]["path"] == "/Users/asteroida/a00238/11、奥克斯/【奥克斯】中央空调故障代码(模块机、多联机).pdf"


def test_build_manual_fixture_from_review_candidates_requires_curation(monkeypatch) -> None:
    """Accepted candidates without required curation fields should fail fast."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "hvac",
        doc_id="doc_aux_module_faults",
        equipment_class_id="air_cooled_modular_heat_pump",
    )
    payload["candidate_entries"][0]["review_decision"] = "accepted"
    payload["candidate_entries"][0]["curation"] = {
        "title": "Incomplete reviewed entry",
        "structured_payload": {"fault_code": "E01"},
        "applicability": {},
        "trust_level": "L2",
    }
    db = session_factory()
    try:
        try:
            build_manual_fixture_from_review_candidates(payload, db)
        except ValueError as exc:
            assert "missing curation fields" in str(exc)
        else:
            raise AssertionError("Expected curation validation failure")
    finally:
        db.close()


def test_review_candidate_fixture_can_feed_existing_chunk_backfill(monkeypatch) -> None:
    """Reviewed candidate fixture should round-trip into the existing backfill script."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, DRIVE_PARAMETER_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)
    monkeypatch.setattr("scripts.backfill_manual_knowledge_from_chunks.SessionLocal", session_factory)

    payload = _review_payload_for_drive_parameters(session_factory)
    with tempfile.TemporaryDirectory() as tmp_dir:
        review_path = Path(tmp_dir) / "reviewed_candidates.json"
        fixture_path = Path(tmp_dir) / "reviewed_fixture.json"
        review_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        fixture = build_manual_fixture_from_review_candidate_file(review_path)
        fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
        equipment_class_key, knowledge_count = backfill_manual_fixture_from_chunks(fixture_path)

    db = session_factory()
    try:
        assert equipment_class_key == "drive:variable_frequency_drive"
        assert knowledge_count == 2
        assert db.query(KnowledgeObjectV2).filter(KnowledgeObjectV2.domain_id == "drive").count() == 2
    finally:
        db.close()


if __name__ == "__main__":
    class _MonkeyPatch:
        def __init__(self) -> None:
            self._patches = []

        def setattr(self, target: str, value) -> None:
            module_name, attr_name = target.rsplit(".", 1)
            module = __import__(module_name, fromlist=[attr_name])
            original = getattr(module, attr_name)
            setattr(module, attr_name, value)
            self._patches.append((module, attr_name, original))

        def undo(self) -> None:
            while self._patches:
                module, attr_name, original = self._patches.pop()
                setattr(module, attr_name, original)

    monkeypatch = _MonkeyPatch()
    test_build_manual_fixture_from_review_candidates_for_hvac(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_build_manual_fixture_from_review_candidates_requires_curation(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_review_candidate_fixture_can_feed_existing_chunk_backfill(monkeypatch)
    monkeypatch.undo()
    print("Review candidate fixture builder checks passed")
