"""Read-only semantic retrieval helpers for ontology metadata."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from packages.db.models import Document
from packages.db.models_v2 import (
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyClassV2,
    OntologyMappingV2,
)

TRUST_RANK = {"L1": 0, "L2": 1, "L3": 2, "L4": 3}
FAULT_KNOWLEDGE_TYPES = ("fault_code", "symptom", "diagnostic_step")


class SemanticRetrievalService:
    """Read-only access to rebuild-track ontology metadata."""

    def _get_equipment_class(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
    ) -> OntologyClassV2 | None:
        return (
            db.query(OntologyClassV2)
            .filter(OntologyClassV2.domain_id == domain_id)
            .filter(OntologyClassV2.ontology_class_id == equipment_class_id)
            .filter(OntologyClassV2.class_kind == "equipment")
            .filter(OntologyClassV2.is_active.is_(True))
            .one_or_none()
        )

    def _get_parent_class_id(self, db: Session, ontology_class: OntologyClassV2) -> str | None:
        if not ontology_class.parent_class_key:
            return None
        parent = (
            db.query(OntologyClassV2)
            .filter(OntologyClassV2.ontology_class_key == ontology_class.parent_class_key)
            .one_or_none()
        )
        return parent.ontology_class_id if parent else None

    def _matches_fault_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        fault_code: str | None,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
    ) -> bool:
        if TRUST_RANK[knowledge_object.trust_level] > TRUST_RANK[min_trust_level]:
            return False
        if min_confidence is not None:
            score = knowledge_object.confidence_score or 0.0
            if score < min_confidence:
                return False
        if not fault_code:
            return self._matches_applicability(knowledge_object, brand, model_family)
        return self._matches_fault_code(knowledge_object, fault_code) and self._matches_applicability(
            knowledge_object,
            brand,
            model_family,
        )

    def _matches_fault_code(self, knowledge_object: KnowledgeObjectV2, fault_code: str) -> bool:
        if knowledge_object.canonical_key == fault_code:
            return True
        for source in (knowledge_object.structured_payload_json, knowledge_object.applicability_json or {}):
            value = source.get("fault_code")
            if value == fault_code:
                return True
            if isinstance(value, list) and fault_code in value:
                return True
        return False

    def _matches_applicability(
        self,
        knowledge_object: KnowledgeObjectV2,
        brand: str | None,
        model_family: str | None,
    ) -> bool:
        applicability = knowledge_object.applicability_json or {}
        if brand and applicability.get("brand") not in (None, brand):
            return False
        if model_family and applicability.get("model_family") not in (None, model_family):
            return False
        return True

    def _sort_fault_knowledge(self, knowledge_objects: list[KnowledgeObjectV2]) -> list[KnowledgeObjectV2]:
        return sorted(
            knowledge_objects,
            key=lambda item: (
                TRUST_RANK.get(item.trust_level, 99),
                -(item.confidence_score or 0.0),
                item.knowledge_object_type,
                item.canonical_key,
            ),
        )

    def _load_evidence_map(
        self,
        db: Session,
        knowledge_object_ids: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        rows = (
            db.query(KnowledgeObjectEvidenceV2, Document)
            .join(Document, Document.doc_id == KnowledgeObjectEvidenceV2.doc_id)
            .filter(KnowledgeObjectEvidenceV2.knowledge_object_id.in_(knowledge_object_ids))
            .order_by(KnowledgeObjectEvidenceV2.knowledge_object_id, KnowledgeObjectEvidenceV2.evidence_role, KnowledgeObjectEvidenceV2.page_no)
            .all()
        )
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for evidence, document in rows:
            grouped[evidence.knowledge_object_id].append(
                {
                    "doc_id": evidence.doc_id,
                    "doc_name": document.file_name,
                    "page_no": evidence.page_no,
                    "chunk_id": evidence.chunk_id,
                    "evidence_text": evidence.evidence_text,
                    "evidence_role": evidence.evidence_role,
                }
            )
        return grouped

    def explain_equipment_class(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
        language: str = "en",
    ) -> dict[str, Any] | None:
        """Return an ontology-backed equipment class explanation."""

        ontology_class = self._get_equipment_class(db, domain_id, equipment_class_id)
        if ontology_class is None:
            return None

        aliases = (
            db.query(OntologyAliasV2)
            .filter(OntologyAliasV2.domain_id == domain_id)
            .filter(OntologyAliasV2.ontology_class_id == equipment_class_id)
            .order_by(OntologyAliasV2.language_code, OntologyAliasV2.is_preferred.desc(), OntologyAliasV2.alias_text)
            .all()
        )
        mappings = (
            db.query(OntologyMappingV2)
            .filter(OntologyMappingV2.domain_id == domain_id)
            .filter(OntologyMappingV2.ontology_class_id == equipment_class_id)
            .order_by(OntologyMappingV2.mapping_system, OntologyMappingV2.is_primary.desc())
            .all()
        )

        alias_groups: dict[str, list[str]] = defaultdict(list)
        for item in aliases:
            alias_groups[item.language_code].append(item.alias_text)

        label = ontology_class.labels_json.get(language) or ontology_class.primary_label
        return {
            "equipment_class": {
                "equipment_class_id": ontology_class.ontology_class_id,
                "label": label,
                "domain_id": ontology_class.domain_id,
            },
            "class_kind": ontology_class.class_kind,
            "parent_class_id": self._get_parent_class_id(db, ontology_class),
            "labels": ontology_class.labels_json,
            "aliases": dict(alias_groups),
            "external_mappings": [
                {
                    "mapping_system": item.mapping_system,
                    "external_id": item.external_id,
                    "is_primary": item.is_primary,
                    "mapping_metadata": item.mapping_metadata_json or {},
                }
                for item in mappings
            ],
            "supported_knowledge_anchors": ontology_class.knowledge_anchors_json,
        }

    def get_fault_knowledge(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
        fault_code: str | None = None,
        brand: str | None = None,
        model_family: str | None = None,
        include_related_symptoms: bool = True,
        min_confidence: float | None = None,
        min_trust_level: str = "L4",
        limit: int = 20,
    ) -> dict[str, Any] | None:
        """Return evidence-grounded fault knowledge attached to an equipment class."""

        ontology_class = self._get_equipment_class(db, domain_id, equipment_class_id)
        if ontology_class is None:
            return None

        types = FAULT_KNOWLEDGE_TYPES if include_related_symptoms else ("fault_code",)
        knowledge_objects = (
            db.query(KnowledgeObjectV2)
            .filter(KnowledgeObjectV2.domain_id == domain_id)
            .filter(KnowledgeObjectV2.ontology_class_id == equipment_class_id)
            .filter(KnowledgeObjectV2.knowledge_object_type.in_(types))
            .all()
        )
        filtered = [
            item
            for item in knowledge_objects
            if self._matches_fault_filters(
                item,
                fault_code,
                brand,
                model_family,
                min_confidence,
                min_trust_level,
            )
        ]
        ranked = self._sort_fault_knowledge(filtered)[:limit]
        evidence_map = self._load_evidence_map(db, [item.knowledge_object_id for item in ranked])
        label = ontology_class.labels_json.get("en") or ontology_class.primary_label
        return {
            "equipment_class": {
                "equipment_class_id": ontology_class.ontology_class_id,
                "label": label,
                "domain_id": ontology_class.domain_id,
            },
            "items": [
                {
                    "knowledge_object_id": item.knowledge_object_id,
                    "knowledge_object_type": item.knowledge_object_type,
                    "canonical_key": item.canonical_key,
                    "equipment_class": {
                        "equipment_class_id": ontology_class.ontology_class_id,
                        "label": label,
                        "domain_id": ontology_class.domain_id,
                    },
                    "title": item.title,
                    "summary": item.summary,
                    "structured_payload": item.structured_payload_json,
                    "applicability": item.applicability_json or {},
                    "confidence": item.confidence_score,
                    "trust_level": item.trust_level,
                    "review_status": item.review_status,
                    "evidence": evidence_map.get(item.knowledge_object_id, []),
                }
                for item in ranked
                if evidence_map.get(item.knowledge_object_id)
            ],
        }
