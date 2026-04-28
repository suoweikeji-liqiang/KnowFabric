"""API tests for sw_base_model feedback ingestion."""

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.db.models_v2 import KOFeedbackEventV2
from packages.db.session import Base, get_db


def _build_client() -> TestClient:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[KOFeedbackEventV2.__table__])
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _post(client: TestClient, path: str, payload: dict):
    response = client.post(path, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_feedback_endpoints_accept_all_event_types() -> None:
    client = _build_client()
    try:
        confirmation = {
            "project_id": "proj_1",
            "finding_id": "find_1",
            "reviewer_id": "rev_1",
            "knowledge_object_id": "fc:york_F101",
        }
        rejection = {**confirmation, "finding_id": "find_2", "reason": "false positive"}
        coverage = {
            "project_id": "proj_1",
            "equipment_class_id": "brick:Chiller",
            "expected_ko_type": "fault_code",
            "expected_pattern": "low evaporator flow trip",
        }
        conflict = {
            "project_id": "proj_1",
            "knowledge_object_id": "ps:chw_setpoint",
            "field_observation": {"value": 3.0, "unit": "degC"},
            "observation_window": "2026-04-28T00:00:00Z/2026-04-28T01:00:00Z",
            "reviewer_id": "rev_1",
        }

        assert _post(client, "/api/v2/feedback/ko-confirmation", confirmation)["status"] == "accepted"
        assert _post(client, "/api/v2/feedback/ko-rejection", rejection)["status"] == "accepted"
        assert _post(client, "/api/v2/feedback/coverage-gap", coverage)["status"] == "accepted"
        assert _post(client, "/api/v2/feedback/conflict-evidence", conflict)["status"] == "accepted"
    finally:
        app.dependency_overrides.clear()


def test_feedback_endpoint_is_idempotent() -> None:
    client = _build_client()
    payload = {
        "project_id": "proj_1",
        "finding_id": "find_1",
        "reviewer_id": "rev_1",
        "knowledge_object_id": "fc:york_F101",
    }
    try:
        first = _post(client, "/api/v2/feedback/ko-confirmation", payload)
        second = _post(client, "/api/v2/feedback/ko-confirmation", payload)
        assert first["event_id"] == second["event_id"]
        assert second["status"] == "duplicate"
    finally:
        app.dependency_overrides.clear()


def test_feedback_endpoint_rejects_missing_required_field() -> None:
    client = _build_client()
    try:
        response = client.post(
            "/api/v2/feedback/ko-confirmation",
            json={"project_id": "proj_1", "finding_id": "find_1", "reviewer_id": "rev_1"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
