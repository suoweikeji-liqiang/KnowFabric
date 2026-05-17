"""Read-only semantic retrieval helpers for ontology metadata."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from packages.compiler.contracts import extract_compile_metadata, public_health_flags
from packages.core.sw_base_model_ontology_client import SwBaseModelOntologyClient
from packages.db.models import Document
from packages.db.models_v2 import (
    DocumentPageImageV2,
    KnowledgeObjectEvidenceV2,
    KnowledgeObjectV2,
    OntologyAliasV2,
    OntologyMappingV2,
    VisualEvidenceAnchorV2,
)

TRUST_RANK = {"L1": 0, "L2": 1, "L3": 2, "L4": 3}
AUTHORITY_RANK = {
    "field_observation": 6,
    "industry_standard": 5,
    "regulatory_code": 4,
    "oem_manual": 3,
    "vendor_application_note": 2,
    "academic_reference": 1,
    "internal_sop": 0,
    "unspecified": -1,
}
FAULT_KNOWLEDGE_TYPES = ("fault_code", "fault_diagnostic_rule", "symptom", "diagnostic_step")
PARAMETER_PROFILE_TYPES = ("parameter_spec", "performance_spec")
MAINTENANCE_GUIDANCE_TYPES = ("maintenance_procedure", "diagnostic_step")
APPLICATION_GUIDANCE_TYPES = ("application_guidance",)
OPERATIONAL_GUIDANCE_TYPES = (
    "commissioning_step",
    "operational_sequence",
    "wiring_guidance",
    "application_guidance",
)


class SemanticRetrievalService:
    """Read-only access to rebuild-track ontology metadata."""

    def __init__(self, ontology_client: SwBaseModelOntologyClient | None = None) -> None:
        self.ontology_client = ontology_client or SwBaseModelOntologyClient()

    def _language_candidates(self, language: str | None) -> list[str]:
        if not language:
            return ["en"]
        candidates = [language]
        base_language = language.split("-", 1)[0]
        if base_language not in candidates:
            candidates.append(base_language)
        if "en" not in candidates:
            candidates.append("en")
        return candidates

    def _localized_display_payload(self, knowledge_object: KnowledgeObjectV2) -> dict[str, Any]:
        payload = knowledge_object.structured_payload_json or {}
        localized_display = payload.get("_localized_display", {})
        return localized_display if isinstance(localized_display, dict) else {}

    def _public_structured_payload(self, knowledge_object: KnowledgeObjectV2) -> dict[str, Any]:
        payload = knowledge_object.structured_payload_json or {}
        return {
            key: value
            for key, value in payload.items()
            if not str(key).startswith("_")
        }

    def _resolve_display_content(
        self,
        knowledge_object: KnowledgeObjectV2,
        language: str,
    ) -> tuple[str | None, str | None, dict[str, Any], str]:
        localized_display = self._localized_display_payload(knowledge_object)
        structured_payload = self._public_structured_payload(knowledge_object)
        for candidate in self._language_candidates(language):
            candidate_payload = localized_display.get(candidate)
            if not isinstance(candidate_payload, dict):
                continue
            localized_title = candidate_payload.get("title") or knowledge_object.title
            localized_summary = candidate_payload.get("summary") or knowledge_object.summary
            localized_structured_payload = candidate_payload.get("structured_payload")
            if isinstance(localized_structured_payload, dict):
                structured_payload = {
                    **structured_payload,
                    **localized_structured_payload,
                }
            return localized_title, localized_summary, structured_payload, candidate
        return knowledge_object.title, knowledge_object.summary, structured_payload, "en"

    def _get_equipment_class(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
    ) -> dict[str, Any] | None:
        equipment_class = self.ontology_client.get_equipment_class(equipment_class_id)
        if equipment_class is not None:
            equipment_class["domain_id"] = domain_id
        return equipment_class

    def _get_parent_class_id(self, db: Session, ontology_class: dict[str, Any]) -> str | None:
        return ontology_class.get("parent_class_id")

    def _meets_min_trust_level(self, knowledge_object: KnowledgeObjectV2, min_trust_level: str) -> bool:
        return TRUST_RANK.get(knowledge_object.trust_level, -1) >= TRUST_RANK[min_trust_level]

    def _meets_min_authority_level(self, knowledge_object: KnowledgeObjectV2, min_authority_level: str | None) -> bool:
        if not min_authority_level:
            return True
        ko_rank = AUTHORITY_RANK.get(knowledge_object.highest_authority_level, -1)
        return ko_rank >= AUTHORITY_RANK.get(min_authority_level, -1)

    def _matches_consensus_filter(self, knowledge_object: KnowledgeObjectV2, consensus_filter: str | None) -> bool:
        if not consensus_filter:
            return True
        return knowledge_object.consensus_state == consensus_filter

    def _matches_fault_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        fault_code: str | None,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
    ) -> bool:
        if not self._meets_min_trust_level(knowledge_object, min_trust_level):
            return False
        if not self._meets_min_authority_level(knowledge_object, min_authority_level):
            return False
        if not self._matches_consensus_filter(knowledge_object, consensus_filter):
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

    def _matches_common_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
    ) -> bool:
        if not self._meets_min_trust_level(knowledge_object, min_trust_level):
            return False
        if not self._meets_min_authority_level(knowledge_object, min_authority_level):
            return False
        if not self._matches_consensus_filter(knowledge_object, consensus_filter):
            return False
        if min_confidence is not None:
            score = knowledge_object.confidence_score or 0.0
            if score < min_confidence:
                return False
        return self._matches_applicability(knowledge_object, brand, model_family)

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

    def _matches_parameter_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        parameter_category: str | None,
        parameter_name: str | None,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
    ) -> bool:
        if not self._matches_common_filters(
            knowledge_object,
            brand,
            model_family,
            min_confidence,
            min_trust_level,
            min_authority_level=min_authority_level,
            consensus_filter=consensus_filter,
        ):
            return False
        payload = knowledge_object.structured_payload_json
        if parameter_category and payload.get("parameter_category") != parameter_category:
            return False
        if parameter_name and knowledge_object.canonical_key != parameter_name:
            if payload.get("parameter_name") != parameter_name:
                return False
        return True

    def _matches_maintenance_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        task_type: str | None,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
    ) -> bool:
        if not self._matches_common_filters(
            knowledge_object,
            brand,
            model_family,
            min_confidence,
            min_trust_level,
            min_authority_level=min_authority_level,
            consensus_filter=consensus_filter,
        ):
            return False
        if not task_type:
            return True
        payload = knowledge_object.structured_payload_json
        return payload.get("task_type") == task_type or payload.get("maintenance_task") == task_type

    def _matches_application_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        application_type: str | None,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
    ) -> bool:
        if not self._matches_common_filters(
            knowledge_object,
            brand,
            model_family,
            min_confidence,
            min_trust_level,
            min_authority_level=min_authority_level,
            consensus_filter=consensus_filter,
        ):
            return False
        if not application_type:
            return True
        payload = knowledge_object.structured_payload_json
        return payload.get("application_type") == application_type

    def _matches_operational_filters(
        self,
        knowledge_object: KnowledgeObjectV2,
        guidance_type: str | None,
        brand: str | None,
        model_family: str | None,
        min_confidence: float | None,
        min_trust_level: str,
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
    ) -> bool:
        if not self._matches_common_filters(
            knowledge_object,
            brand,
            model_family,
            min_confidence,
            min_trust_level,
            min_authority_level=min_authority_level,
            consensus_filter=consensus_filter,
        ):
            return False
        if not guidance_type:
            return True
        return knowledge_object.knowledge_object_type == guidance_type

    def _sort_fault_knowledge(self, knowledge_objects: list[KnowledgeObjectV2]) -> list[KnowledgeObjectV2]:
        return sorted(
            knowledge_objects,
            key=lambda item: (
                -TRUST_RANK.get(item.trust_level, -1),
                -(item.confidence_score or 0.0),
                item.knowledge_object_type,
                item.canonical_key,
            ),
        )

    def _sort_semantic_items(self, knowledge_objects: list[KnowledgeObjectV2]) -> list[KnowledgeObjectV2]:
        return sorted(
            knowledge_objects,
            key=lambda item: (
                -TRUST_RANK.get(item.trust_level, -1),
                -(item.confidence_score or 0.0),
                item.knowledge_object_type,
                item.canonical_key,
            ),
        )

    def _load_evidence_map(
        self,
        db: Session,
        knowledge_object_ids: list[str],
        *,
        include_restricted_evidence: bool = False,
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
            is_redistributable = bool(getattr(document, "is_redistributable", False))
            evidence_text = evidence.evidence_text
            redistribution_restricted = False
            if not is_redistributable and not include_restricted_evidence:
                # Contract §11.5: when redistribution is restricted, evidence_text
                # MUST NOT leak any verbatim substring from the original source.
                # Replace with a citation-only stub derived from non-content metadata
                # (document name + page). Downstream still receives structured
                # parameter value via authority_layers / structured_payload; only
                # the prose quote is suppressed.
                evidence_text = (
                    f"[Restricted source: {document.file_name}, p.{evidence.page_no}] "
                    f"Verbatim quote suppressed per redistribution policy. "
                    f"Request with include_restricted_evidence=true for full text."
                )
                redistribution_restricted = True
            grouped[evidence.knowledge_object_id].append(
                {
                    "doc_id": evidence.doc_id,
                    "doc_name": document.file_name,
                    "page_no": evidence.page_no,
                    "chunk_id": evidence.chunk_id,
                    "evidence_text": evidence_text,
                    "evidence_role": evidence.evidence_role,
                    "authority_role": getattr(evidence, "authority_role", None) or None,
                    "evidence_citation": getattr(evidence, "evidence_citation", None) or None,
                    "redistribution_restricted": redistribution_restricted,
                }
            )
        return grouped

    def _load_visual_evidence_map(
        self,
        db: Session,
        knowledge_object_ids: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        try:
            rows = (
                db.query(VisualEvidenceAnchorV2, DocumentPageImageV2)
                .join(DocumentPageImageV2, DocumentPageImageV2.page_image_id == VisualEvidenceAnchorV2.page_image_id)
                .filter(VisualEvidenceAnchorV2.knowledge_object_id.in_(knowledge_object_ids))
                .order_by(VisualEvidenceAnchorV2.knowledge_object_id, VisualEvidenceAnchorV2.page_no)
                .all()
            )
        except Exception:
            return defaultdict(list)
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for anchor, page_image in rows:
            grouped[anchor.knowledge_object_id].append({
                "page_image_id": page_image.page_image_id,
                "page_no": page_image.page_no,
                "bbox": anchor.bbox,
                "image_path": page_image.image_path if getattr(page_image, "image_path", None) else None,
                "image_type": page_image.image_type,
                "vl_summary": page_image.vl_summary,
                "model_used": anchor.model_used,
                "confidence": anchor.confidence,
                "evidence_role": anchor.evidence_role,
            })
        return grouped

    def _build_semantic_collection(
        self,
        db: Session,
        ontology_class: dict[str, Any],
        knowledge_objects: list[KnowledgeObjectV2],
        total_count: int,
        language: str = "en",
        *,
        include_restricted_evidence: bool = False,
    ) -> dict[str, Any]:
        ko_ids = [item.knowledge_object_id for item in knowledge_objects]
        evidence_map = self._load_evidence_map(
            db, ko_ids, include_restricted_evidence=include_restricted_evidence,
        )
        visual_evidence_map = self._load_visual_evidence_map(db, ko_ids)
        labels = ontology_class.get("labels") or {}
        label = labels.get(language) or ontology_class["primary_label"]
        items: list[dict[str, Any]] = []
        for item in knowledge_objects:
            evidence = evidence_map.get(item.knowledge_object_id)
            if not evidence:
                continue
            title, summary, structured_payload, display_language = self._resolve_display_content(item, language)
            compiler_metadata = extract_compile_metadata(item.structured_payload_json)
            health_flags = public_health_flags(item.structured_payload_json)
            authority_summary = item.authority_summary_json or {}
            authority_layers = authority_summary.get("layers", []) if isinstance(authority_summary, dict) else []
            any_restricted = any(ev.get("redistribution_restricted", False) for ev in evidence)
            items.append(
                {
                    "knowledge_object_id": item.knowledge_object_id,
                    "knowledge_object_type": item.knowledge_object_type,
                    "canonical_key": item.canonical_key,
                    "equipment_class": {
                        "equipment_class_id": ontology_class["ontology_class_id"],
                        "label": label,
                        "domain_id": item.domain_id,
                    },
                    "title": title,
                    "summary": summary,
                    "structured_payload": structured_payload,
                    "applicability": item.applicability_json or {},
                    "confidence": item.confidence_score,
                    "trust_level": item.trust_level,
                    "review_status": item.review_status,
                    "display_language": display_language,
                    "compilation_method": compiler_metadata.get("method"),
                    "compiler_version": compiler_metadata.get("version"),
                    "health_flags": health_flags,
                    "consensus_state": item.consensus_state,
                    "highest_authority_level": item.highest_authority_level,
                    "authority_layers": authority_layers,
                    "conflict_summary": item.conflict_summary,
                    "deviation_justification": item.deviation_justification_json or {},
                    "redistribution_restricted": any_restricted,
                    "evidence": evidence,
                    "visual_evidence": visual_evidence_map.get(item.knowledge_object_id, []),
                }
            )
        return {
            "equipment_class": {
                "equipment_class_id": ontology_class["ontology_class_id"],
                "label": label,
                "domain_id": ontology_class["domain_id"],
            },
            "items": items,
            "total_count": total_count,
            "returned_count": len(items),
            "has_more": total_count > len(items),
        }

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

        labels = ontology_class.get("labels") or {}
        label = labels.get(language) or ontology_class["primary_label"]
        return {
            "equipment_class": {
                "equipment_class_id": ontology_class["ontology_class_id"],
                "label": label,
                "domain_id": domain_id,
            },
            "class_kind": "equipment",
            "parent_class_id": self._get_parent_class_id(db, ontology_class),
            "labels": labels,
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
            "typical_points": self.ontology_client.get_typical_points(equipment_class_id),
            "typical_relations": self.ontology_client.get_typical_relations(equipment_class_id),
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
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
        include_restricted_evidence: bool = False,
        limit: int = 100,
        language: str = "en",
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
                min_authority_level=min_authority_level,
                consensus_filter=consensus_filter,
            )
        ]
        total_count = len(filtered)
        ranked = self._sort_fault_knowledge(filtered)[:limit]
        return self._build_semantic_collection(
            db, ontology_class, ranked, total_count=total_count, language=language,
            include_restricted_evidence=include_restricted_evidence,
        )

    def get_parameter_profiles(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
        parameter_category: str | None = None,
        parameter_name: str | None = None,
        brand: str | None = None,
        model_family: str | None = None,
        min_confidence: float | None = None,
        min_trust_level: str = "L4",
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
        include_restricted_evidence: bool = False,
        limit: int = 100,
        language: str = "en",
    ) -> dict[str, Any] | None:
        """Return evidence-grounded parameter and performance knowledge."""

        ontology_class = self._get_equipment_class(db, domain_id, equipment_class_id)
        if ontology_class is None:
            return None
        knowledge_objects = (
            db.query(KnowledgeObjectV2)
            .filter(KnowledgeObjectV2.domain_id == domain_id)
            .filter(KnowledgeObjectV2.ontology_class_id == equipment_class_id)
            .filter(KnowledgeObjectV2.knowledge_object_type.in_(PARAMETER_PROFILE_TYPES))
            .all()
        )
        filtered = [
            item
            for item in knowledge_objects
            if self._matches_parameter_filters(
                item,
                parameter_category,
                parameter_name,
                brand,
                model_family,
                min_confidence,
                min_trust_level,
                min_authority_level=min_authority_level,
                consensus_filter=consensus_filter,
            )
        ]
        total_count = len(filtered)
        ranked = self._sort_semantic_items(filtered)[:limit]
        return self._build_semantic_collection(
            db, ontology_class, ranked, total_count=total_count, language=language,
            include_restricted_evidence=include_restricted_evidence,
        )

    def get_maintenance_guidance(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
        task_type: str | None = None,
        brand: str | None = None,
        model_family: str | None = None,
        include_diagnostic_steps: bool = True,
        min_confidence: float | None = None,
        min_trust_level: str = "L4",
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
        include_restricted_evidence: bool = False,
        limit: int = 100,
        language: str = "en",
    ) -> dict[str, Any] | None:
        """Return evidence-grounded maintenance guidance attached to an equipment class."""

        ontology_class = self._get_equipment_class(db, domain_id, equipment_class_id)
        if ontology_class is None:
            return None
        types = MAINTENANCE_GUIDANCE_TYPES if include_diagnostic_steps else ("maintenance_procedure",)
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
            if self._matches_maintenance_filters(
                item,
                task_type,
                brand,
                model_family,
                min_confidence,
                min_trust_level,
                min_authority_level=min_authority_level,
                consensus_filter=consensus_filter,
            )
        ]
        total_count = len(filtered)
        ranked = self._sort_semantic_items(filtered)[:limit]
        return self._build_semantic_collection(
            db, ontology_class, ranked, total_count=total_count, language=language,
            include_restricted_evidence=include_restricted_evidence,
        )

    def get_application_guidance(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
        application_type: str | None = None,
        brand: str | None = None,
        model_family: str | None = None,
        min_confidence: float | None = None,
        min_trust_level: str = "L4",
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
        include_restricted_evidence: bool = False,
        limit: int = 100,
        language: str = "en",
    ) -> dict[str, Any] | None:
        """Return evidence-grounded application guidance attached to an equipment class."""

        ontology_class = self._get_equipment_class(db, domain_id, equipment_class_id)
        if ontology_class is None:
            return None
        knowledge_objects = (
            db.query(KnowledgeObjectV2)
            .filter(KnowledgeObjectV2.domain_id == domain_id)
            .filter(KnowledgeObjectV2.ontology_class_id == equipment_class_id)
            .filter(KnowledgeObjectV2.knowledge_object_type.in_(APPLICATION_GUIDANCE_TYPES))
            .all()
        )
        filtered = [
            item
            for item in knowledge_objects
            if self._matches_application_filters(
                item,
                application_type,
                brand,
                model_family,
                min_confidence,
                min_trust_level,
                min_authority_level=min_authority_level,
                consensus_filter=consensus_filter,
            )
        ]
        total_count = len(filtered)
        ranked = self._sort_semantic_items(filtered)[:limit]
        return self._build_semantic_collection(
            db, ontology_class, ranked, total_count=total_count, language=language,
            include_restricted_evidence=include_restricted_evidence,
        )

    def get_operational_guidance(
        self,
        db: Session,
        domain_id: str,
        equipment_class_id: str,
        guidance_type: str | None = None,
        brand: str | None = None,
        model_family: str | None = None,
        min_confidence: float | None = None,
        min_trust_level: str = "L4",
        min_authority_level: str | None = None,
        consensus_filter: str | None = None,
        include_restricted_evidence: bool = False,
        limit: int = 100,
        language: str = "en",
    ) -> dict[str, Any] | None:
        """Return evidence-grounded commissioning, wiring, and application guidance."""

        ontology_class = self._get_equipment_class(db, domain_id, equipment_class_id)
        if ontology_class is None:
            return None
        knowledge_objects = (
            db.query(KnowledgeObjectV2)
            .filter(KnowledgeObjectV2.domain_id == domain_id)
            .filter(KnowledgeObjectV2.ontology_class_id == equipment_class_id)
            .filter(KnowledgeObjectV2.knowledge_object_type.in_(OPERATIONAL_GUIDANCE_TYPES))
            .all()
        )
        filtered = [
            item
            for item in knowledge_objects
            if self._matches_operational_filters(
                item,
                guidance_type,
                brand,
                model_family,
                min_confidence,
                min_trust_level,
                min_authority_level=min_authority_level,
                consensus_filter=consensus_filter,
            )
        ]
        total_count = len(filtered)
        ranked = self._sort_semantic_items(filtered)[:limit]
        return self._build_semantic_collection(
            db, ontology_class, ranked, total_count=total_count, language=language,
            include_restricted_evidence=include_restricted_evidence,
        )
