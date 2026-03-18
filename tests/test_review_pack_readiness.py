"""Tests for review pack readiness checking."""

import json
import sys
import tempfile
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
from scripts.build_review_packs_from_candidates import write_review_packs_from_candidate_file
from scripts.check_review_pack_readiness import check_review_pack_directory
from scripts.generate_chunk_backfill_candidates import generate_chunk_backfill_candidates

REPO_ROOT = Path(__file__).resolve().parent.parent
HVAC_V2_ROOT = REPO_ROOT / "domain_packages/hvac/v2"
DRIVE_V2_ROOT = REPO_ROOT / "domain_packages/drive/v2"
HVAC_FIXTURE = REPO_ROOT / "tests/fixtures/manual_validation/hvac_module_faults.json"


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


def _build_pack_dir(monkeypatch, session_factory, tmp_dir: str) -> Path:
    monkeypatch.setattr("scripts.generate_chunk_backfill_candidates.SessionLocal", session_factory)
    payload = generate_chunk_backfill_candidates(
        "hvac",
        equipment_class_id="air_cooled_modular_heat_pump",
    )
    candidate_path = Path(tmp_dir) / "candidates.json"
    candidate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pack_dir = Path(tmp_dir) / "review_packs"
    write_review_packs_from_candidate_file(candidate_path, pack_dir, default_trust_level="L2")
    return pack_dir


def _load_pack(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_pack(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_check_review_pack_directory_reports_ready_and_pending(monkeypatch) -> None:
    """Readiness check should distinguish ready packs from still-pending ones."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = _build_pack_dir(monkeypatch, session_factory, tmp_dir)
        aux_pack = pack_dir / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        aux_payload = _load_pack(aux_pack)
        for entry in aux_payload["candidate_entries"]:
            if entry["canonical_key_candidate"] == "E22":
                entry["review_decision"] = "accepted"
                entry["curation"]["title"] = "Reviewed AUX E22"
                entry["curation"]["summary"] = "Ready for apply."
                entry["curation"]["applicability"] = {"brand": "AUX", "model_family": "X Module Unit"}
            else:
                entry["review_decision"] = "rejected"
        _save_pack(aux_pack, aux_payload)

        report = check_review_pack_directory(pack_dir)

    assert report["summary"] == {
        "ready": 1,
        "blocked_pending": 1,
        "blocked_no_accepted": 0,
        "blocked_invalid": 0,
    }
    assert report["results"] == [
        {
            "pack_file": "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json",
            "pack_path": str(Path(report["pack_dir"]) / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"),
            "doc_id": "doc_aux_module_faults",
            "doc_name": "AUX Central AC Fault Codes (Modular and VRF).pdf",
            "equipment_class_id": "air_cooled_modular_heat_pump",
            "equipment_class_key": "hvac:air_cooled_modular_heat_pump",
            "candidate_count": 3,
            "accepted_count": 1,
            "rejected_count": 2,
            "pending_count": 0,
            "status": "ready",
            "blocker": None,
            "ready_manual_entries": 1,
            "fixture_equipment_class_key": "hvac:air_cooled_modular_heat_pump",
        },
        {
            "pack_file": "hvac__doc_guoxiang_kms_manual__air_cooled_modular_heat_pump.json",
            "pack_path": str(Path(report["pack_dir"]) / "hvac__doc_guoxiang_kms_manual__air_cooled_modular_heat_pump.json"),
            "doc_id": "doc_guoxiang_kms_manual",
            "doc_name": "Guoxiang KMS Modular Unit User Manual.pdf",
            "equipment_class_id": "air_cooled_modular_heat_pump",
            "equipment_class_key": "hvac:air_cooled_modular_heat_pump",
            "candidate_count": 2,
            "accepted_count": 0,
            "rejected_count": 0,
            "pending_count": 2,
            "status": "blocked_pending",
            "blocker": "pending_review_decisions",
        },
    ]


def test_check_review_pack_directory_reports_no_accepted_and_invalid(monkeypatch) -> None:
    """Readiness check should catch rejected-only and invalid accepted packs."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = _build_pack_dir(monkeypatch, session_factory, tmp_dir)
        aux_pack = pack_dir / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        aux_payload = _load_pack(aux_pack)
        for entry in aux_payload["candidate_entries"]:
            entry["review_decision"] = "accepted"
        _save_pack(aux_pack, aux_payload)

        guoxiang_pack = pack_dir / "hvac__doc_guoxiang_kms_manual__air_cooled_modular_heat_pump.json"
        guoxiang_payload = _load_pack(guoxiang_pack)
        for entry in guoxiang_payload["candidate_entries"]:
            entry["review_decision"] = "rejected"
        _save_pack(guoxiang_pack, guoxiang_payload)

        report = check_review_pack_directory(pack_dir)

    assert report["summary"] == {
        "ready": 0,
        "blocked_pending": 0,
        "blocked_no_accepted": 1,
        "blocked_invalid": 1,
    }
    assert report["results"][0]["status"] == "blocked_invalid"
    assert "curation.title must be a non-empty string" in report["results"][0]["blocker"]
    assert report["results"][1]["status"] == "blocked_no_accepted"
    assert report["results"][1]["blocker"] == "no_accepted_entries"


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
    test_check_review_pack_directory_reports_ready_and_pending(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_check_review_pack_directory_reports_no_accepted_and_invalid(monkeypatch)
    monkeypatch.undo()
    print("Review pack readiness checks passed")
