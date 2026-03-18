"""Tests for chunk-backed backfill candidate generation."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import OntologyAliasV2, OntologyClassV2, OntologyMappingV2
from packages.db.session import Base
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.manual_fixture import build_manual_fixture_rows, load_manual_fixture
from packages.domain_kit_v2.projection import (
    build_ontology_alias_rows,
    build_ontology_class_rows,
    build_ontology_mapping_rows,
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


def _seed_alias_match_chunk(session_factory) -> None:
    db = session_factory()
    try:
        db.execute(
            Document.__table__.insert(),
            [
                {
                    "doc_id": "doc_drive_alias_match",
                    "file_hash": "hash_doc_drive_alias_match",
                    "storage_path": "/tmp/doc_drive_alias_match.pdf",
                    "file_name": "ABB HVAC drive fault reference.pdf",
                    "file_ext": "pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1,
                    "source_domain": "drive",
                    "parse_status": "complete",
                    "is_active": True,
                }
            ],
        )
        db.execute(
            DocumentPage.__table__.insert(),
            [
                {
                    "page_id": "page_drive_alias_match_1",
                    "doc_id": "doc_drive_alias_match",
                    "page_no": 1,
                    "raw_text": "HVAC drive fault A7C1 fieldbus adapter communication warning.",
                    "cleaned_text": "HVAC drive fault A7C1 fieldbus adapter communication warning.",
                    "page_type": "fault_code_reference",
                }
            ],
        )
        db.execute(
            ContentChunk.__table__.insert(),
            [
                {
                    "chunk_id": "chunk_drive_alias_match_a7c1",
                    "doc_id": "doc_drive_alias_match",
                    "page_id": "page_drive_alias_match_1",
                    "page_no": 1,
                    "chunk_index": 0,
                    "raw_text": "HVAC drive fault A7C1 fieldbus adapter communication warning.",
                    "cleaned_text": "HVAC drive fault A7C1 fieldbus adapter communication warning.",
                    "text_excerpt": "HVAC drive A7C1",
                    "chunk_type": "fault_code_block",
                    "evidence_anchor": "{\"line\": 1}",
                }
            ],
        )
        db.commit()
    finally:
        db.close()


def test_generate_chunk_backfill_candidates_for_hvac_faults(monkeypatch) -> None:
    """Known HVAC equipment class should yield fault-code review candidates."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "hvac",
        doc_id="doc_aux_module_faults",
        equipment_class_id="air_cooled_modular_heat_pump",
    )

    keys = {item["canonical_key_candidate"] for item in payload["candidate_entries"]}
    assert payload["metadata"]["scanned_chunks"] == 3
    assert payload["metadata"]["matched_chunks"] == 3
    assert payload["metadata"]["candidate_hit_rate"] == 1.0
    assert keys == {"E01", "E22", "E23"}
    assert all(item["knowledge_object_type"] == "fault_code" for item in payload["candidate_entries"])
    assert all(
        item["match_metadata"]["equipment_selection_method"] == "input_filter"
        for item in payload["candidate_entries"]
    )


def test_generate_chunk_backfill_candidates_for_drive_parameters(monkeypatch) -> None:
    """Known drive equipment class should yield parameter review candidates."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, DRIVE_PARAMETER_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "drive",
        doc_id="doc_siemens_g120xa_manual",
        equipment_class_id="variable_frequency_drive",
    )

    keys = {item["canonical_key_candidate"] for item in payload["candidate_entries"]}
    assert keys == {"p0604", "p0605"}
    assert all(item["knowledge_object_type"] == "parameter_spec" for item in payload["candidate_entries"])
    assert all(
        item["structured_payload_candidate"]["parameter_name"] in {"p0604", "p0605"}
        for item in payload["candidate_entries"]
    )


def test_generate_chunk_backfill_candidates_can_alias_match_equipment_class(monkeypatch) -> None:
    """Alias-rich chunk text should resolve an equipment class without an explicit override."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_alias_match_chunk(session_factory)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates("drive", doc_id="doc_drive_alias_match")

    assert payload["metadata"]["total_candidates"] == 1
    assert payload["metadata"]["doc_summaries"] == [
        {
            "doc_id": "doc_drive_alias_match",
            "doc_name": "ABB HVAC drive fault reference.pdf",
            "scanned_chunks": 1,
            "matched_chunks": 1,
            "candidate_entries": 1,
            "candidate_hit_rate": 1.0,
        }
    ]
    candidate = payload["candidate_entries"][0]
    assert candidate["equipment_class_candidate"]["equipment_class_id"] == "variable_frequency_drive"
    assert candidate["knowledge_object_type"] == "fault_code"
    assert candidate["canonical_key_candidate"] == "A7C1"
    assert candidate["match_metadata"]["equipment_selection_method"] == "alias_match"
    assert "hvac drive" in candidate["equipment_class_candidate"]["matched_aliases"]


def test_generate_chunk_backfill_candidates_includes_multi_doc_summaries(monkeypatch) -> None:
    """Cross-document candidate generation should expose per-doc hit statistics."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)

    payload = generate_chunk_backfill_candidates(
        "hvac",
        equipment_class_id="air_cooled_modular_heat_pump",
    )

    assert payload["metadata"]["scanned_chunks"] == 5
    assert payload["metadata"]["matched_chunks"] == 5
    assert payload["metadata"]["candidate_hit_rate"] == 1.0
    assert payload["metadata"]["doc_summaries"] == [
        {
            "doc_id": "doc_aux_module_faults",
            "doc_name": "AUX Central AC Fault Codes (Modular and VRF).pdf",
            "scanned_chunks": 3,
            "matched_chunks": 3,
            "candidate_entries": 3,
            "candidate_hit_rate": 1.0,
        },
        {
            "doc_id": "doc_guoxiang_kms_manual",
            "doc_name": "Guoxiang KMS Modular Unit User Manual.pdf",
            "scanned_chunks": 2,
            "matched_chunks": 2,
            "candidate_entries": 2,
            "candidate_hit_rate": 1.0,
        },
    ]


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
    test_generate_chunk_backfill_candidates_for_hvac_faults(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_generate_chunk_backfill_candidates_for_drive_parameters(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_generate_chunk_backfill_candidates_can_alias_match_equipment_class(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_generate_chunk_backfill_candidates_includes_multi_doc_summaries(monkeypatch)
    monkeypatch.undo()
    print("Chunk backfill candidate checks passed")
