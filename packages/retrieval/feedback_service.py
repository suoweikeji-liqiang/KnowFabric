"""Feedback ingestion service for sw_base_model review signals."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from packages.db.models_v2 import KOFeedbackEventV2


class KOFeedbackBase(BaseModel):
    project_id: str
    finding_id: str
    reviewer_id: str
    knowledge_object_id: str


class KOConfirmation(KOFeedbackBase):
    pass


class KORejection(KOFeedbackBase):
    reason: str | None = None


class CoverageGapSignal(BaseModel):
    project_id: str
    equipment_class_id: str
    expected_ko_type: str
    expected_pattern: str
    triggered_by_finding_id: str | None = None


class ConflictEvidence(BaseModel):
    project_id: str
    knowledge_object_id: str
    field_observation: dict[str, Any]
    observation_window: str
    reviewer_id: str


def _event_identity(event_type: str, payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    finding_id = payload.get("finding_id") or payload.get("triggered_by_finding_id")
    reviewer_id = payload.get("reviewer_id")
    knowledge_object_id = payload.get("knowledge_object_id")
    return finding_id, reviewer_id, knowledge_object_id


def _event_key(event_type: str, payload: dict[str, Any]) -> str:
    finding_id, _, knowledge_object_id = _event_identity(event_type, payload)
    base = [event_type, payload["project_id"], finding_id or "", knowledge_object_id or ""]
    if event_type == "coverage_gap":
        base.extend([payload["equipment_class_id"], payload["expected_ko_type"], payload["expected_pattern"]])
    if event_type == "conflict_evidence":
        base.append(payload["observation_window"])
    return "|".join(base)


def _event_id(event_key: str) -> str:
    return f"fb_{uuid.uuid5(uuid.NAMESPACE_URL, event_key).hex[:24]}"


def persist_feedback_event(db: Session, event_type: str, model: BaseModel) -> dict[str, str]:
    """Persist a feedback event idempotently without changing KO trust scores."""

    payload = model.model_dump()
    event_key = _event_key(event_type, payload)
    existing = db.query(KOFeedbackEventV2).filter_by(event_key=event_key).one_or_none()
    if existing is not None:
        return {"event_id": existing.event_id, "status": "duplicate"}

    finding_id, reviewer_id, knowledge_object_id = _event_identity(event_type, payload)
    event = KOFeedbackEventV2(
        event_id=_event_id(event_key),
        event_key=event_key,
        event_type=event_type,
        project_id=payload["project_id"],
        finding_id=finding_id,
        reviewer_id=reviewer_id,
        knowledge_object_id=knowledge_object_id,
        payload_json=payload,
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        duplicate = db.query(KOFeedbackEventV2).filter_by(event_key=event_key).one()
        return {"event_id": duplicate.event_id, "status": "duplicate"}
    return {"event_id": event.event_id, "status": "accepted"}
