"""Tests for batch bootstrapping review pack curation drafts."""

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
from scripts.bootstrap_review_packs_batch import bootstrap_review_pack_directory
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
            mapping_rows = build_ontology_mapping_rows(bundle)
            if mapping_rows:
                db.execute(OntologyMappingV2.__table__.insert(), mapping_rows)
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


def test_bootstrap_review_pack_directory_writes_separate_bootstrapped_dir(monkeypatch) -> None:
    """Batch bootstrap should write bootstrapped copies and a report without mutating source packs."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = _build_pack_dir(monkeypatch, session_factory, tmp_dir)
        source_pack = pack_dir / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        original = json.loads(source_pack.read_text(encoding="utf-8"))
        original["candidate_entries"][0]["review_decision"] = "accepted"
        source_pack.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")

        report = bootstrap_review_pack_directory(pack_dir, default_trust_level="L2")

        bootstrapped_dir = Path(report["output_dir"])
        bootstrapped_pack = bootstrapped_dir / source_pack.name
        assert report["summary"] == {"bootstrapped": 2, "unchanged": 0, "failed": 0}
        assert Path(report["report_path"]).exists()
        assert bootstrapped_pack.exists()
        assert json.loads(source_pack.read_text(encoding="utf-8"))["candidate_entries"][0]["curation"]["title"] == ""
        assert json.loads(bootstrapped_pack.read_text(encoding="utf-8"))["candidate_entries"][0]["curation"]["title"].startswith(
            "Draft Fault Code"
        )


def test_bootstrap_review_pack_directory_can_make_pack_ready(monkeypatch) -> None:
    """Bootstrapped output should pass readiness for packs that only lacked draft curation."""

    session_factory = _build_session_factory()
    _seed_ontology(session_factory)
    _seed_fixture_chunks(session_factory, HVAC_FIXTURE)
    monkeypatch.setattr("scripts.build_manual_fixture_from_review_candidates.SessionLocal", session_factory)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pack_dir = _build_pack_dir(monkeypatch, session_factory, tmp_dir)
        aux_pack = pack_dir / "hvac__doc_aux_module_faults__air_cooled_modular_heat_pump.json"
        payload = json.loads(aux_pack.read_text(encoding="utf-8"))
        for entry in payload["candidate_entries"]:
            entry["review_decision"] = "accepted" if entry["canonical_key_candidate"] == "E22" else "rejected"
        aux_pack.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        before = check_review_pack_directory(pack_dir)
        assert before["summary"]["blocked_invalid"] == 1

        report = bootstrap_review_pack_directory(pack_dir, default_trust_level="L2")
        after = check_review_pack_directory(report["output_dir"])

    assert after["summary"] == {
        "ready": 1,
        "blocked_pending": 1,
        "blocked_no_accepted": 0,
        "blocked_invalid": 0,
    }


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
    test_bootstrap_review_pack_directory_writes_separate_bootstrapped_dir(monkeypatch)
    monkeypatch.undo()
    monkeypatch = _MonkeyPatch()
    test_bootstrap_review_pack_directory_can_make_pack_ready(monkeypatch)
    monkeypatch.undo()
    print("Review pack batch bootstrap checks passed")
