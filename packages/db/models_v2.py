"""Draft rebuild-track storage models for ontology anchors and knowledge objects.

These models are intentionally not imported by ``packages.db.session.init_db`` yet.
They define the proposed persistence contract for the ontology-first rebuild
without activating new tables before migrations are approved.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from packages.db.session import Base


class OntologyClassV2(Base):
    """Canonical ontology class metadata persisted from v2 domain packages."""

    __tablename__ = "ontology_class"

    ontology_class_key = Column(String(196), primary_key=True)
    domain_id = Column(String(64), nullable=False, index=True)
    ontology_class_id = Column(String(128), nullable=False)
    package_version = Column(String(32), nullable=False)
    ontology_version = Column(String(32), nullable=False)
    parent_class_key = Column(String(196), ForeignKey("ontology_class.ontology_class_key"))
    class_kind = Column(String(32), nullable=False)
    primary_label = Column(String(255), nullable=False)
    labels_json = Column(JSON, nullable=False)
    knowledge_anchors_json = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("domain_id", "ontology_class_id", name="uq_ontology_class_domain_local_id"),
        Index("idx_ontology_class_domain_parent", "domain_id", "parent_class_key"),
    )


class OntologyAliasV2(Base):
    """Lookup terms that resolve user or document language to ontology classes."""

    __tablename__ = "ontology_alias"

    alias_id = Column(String(64), primary_key=True)
    ontology_class_key = Column(
        String(196),
        ForeignKey("ontology_class.ontology_class_key"),
        nullable=False,
        index=True,
    )
    domain_id = Column(String(64), nullable=False, index=True)
    ontology_class_id = Column(String(128), nullable=False)
    language_code = Column(String(16), nullable=False)
    alias_text = Column(String(512), nullable=False)
    normalized_alias = Column(String(512), nullable=False)
    is_preferred = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "domain_id",
            "ontology_class_id",
            "language_code",
            "normalized_alias",
            name="uq_ontology_alias_lookup",
        ),
        Index("idx_ontology_alias_language_lookup", "language_code", "normalized_alias"),
    )


class OntologyMappingV2(Base):
    """External interoperability mappings for canonical ontology classes."""

    __tablename__ = "ontology_mapping"

    mapping_id = Column(String(64), primary_key=True)
    ontology_class_key = Column(
        String(196),
        ForeignKey("ontology_class.ontology_class_key"),
        nullable=False,
        index=True,
    )
    domain_id = Column(String(64), nullable=False, index=True)
    ontology_class_id = Column(String(128), nullable=False)
    mapping_system = Column(String(64), nullable=False)
    external_id = Column(String(255), nullable=False)
    mapping_metadata_json = Column(JSON)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "domain_id",
            "ontology_class_id",
            "mapping_system",
            "external_id",
            name="uq_ontology_mapping_external_ref",
        ),
        Index("idx_ontology_mapping_lookup", "mapping_system", "external_id"),
    )


class ChunkOntologyAnchorV2(Base):
    """Anchor chunks to one or more ontology classes without replacing chunk truth."""

    __tablename__ = "chunk_ontology_anchor"

    chunk_anchor_id = Column(String(64), primary_key=True)
    chunk_id = Column(String(64), ForeignKey("content_chunk.chunk_id"), nullable=False, index=True)
    ontology_class_key = Column(
        String(196),
        ForeignKey("ontology_class.ontology_class_key"),
        nullable=False,
        index=True,
    )
    domain_id = Column(String(64), nullable=False, index=True)
    ontology_class_id = Column(String(128), nullable=False)
    match_method = Column(String(32), nullable=False, default="rule")
    confidence_score = Column(Float)
    is_primary = Column(Boolean, default=False, nullable=False)
    match_metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("chunk_id", "ontology_class_key", name="uq_chunk_ontology_anchor"),
        Index("idx_chunk_ontology_anchor_class_chunk", "ontology_class_key", "chunk_id"),
    )


class KnowledgeObjectV2(Base):
    """Typed knowledge object attached to an ontology class and backed by chunk evidence."""

    __tablename__ = "knowledge_object"

    knowledge_object_id = Column(String(64), primary_key=True)
    domain_id = Column(String(64), nullable=False, index=True)
    ontology_class_key = Column(
        String(196),
        ForeignKey("ontology_class.ontology_class_key"),
        nullable=False,
        index=True,
    )
    ontology_class_id = Column(String(128), nullable=False)
    knowledge_object_type = Column(String(64), nullable=False, index=True)
    canonical_key = Column(String(255), nullable=False)
    title = Column(String(512))
    summary = Column(Text)
    structured_payload_json = Column(JSON, nullable=False)
    applicability_json = Column(JSON)
    confidence_score = Column(Float)
    trust_level = Column(String(16), nullable=False, default="L4")
    review_status = Column(String(32), nullable=False, default="pending")
    primary_chunk_id = Column(String(64), ForeignKey("content_chunk.chunk_id"), nullable=False, index=True)
    package_version = Column(String(32), nullable=False)
    ontology_version = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "domain_id",
            "ontology_class_id",
            "knowledge_object_type",
            "canonical_key",
            name="uq_knowledge_object_canonical_key",
        ),
        Index(
            "idx_knowledge_object_anchor_type",
            "ontology_class_key",
            "knowledge_object_type",
        ),
    )


class KnowledgeObjectEvidenceV2(Base):
    """Traceable evidence rows for each knowledge object."""

    __tablename__ = "knowledge_object_evidence"

    knowledge_evidence_id = Column(String(64), primary_key=True)
    knowledge_object_id = Column(
        String(64),
        ForeignKey("knowledge_object.knowledge_object_id"),
        nullable=False,
        index=True,
    )
    chunk_id = Column(String(64), ForeignKey("content_chunk.chunk_id"), nullable=False, index=True)
    doc_id = Column(String(64), ForeignKey("document.doc_id"), nullable=False, index=True)
    page_id = Column(String(64), ForeignKey("document_page.page_id"), nullable=False, index=True)
    page_no = Column(Integer, nullable=False)
    evidence_text = Column(Text, nullable=False)
    evidence_role = Column(String(32), nullable=False, default="supporting")
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "knowledge_object_id",
            "chunk_id",
            "evidence_role",
            name="uq_knowledge_object_evidence_ref",
        ),
        Index(
            "idx_knowledge_object_evidence_trace",
            "knowledge_object_id",
            "doc_id",
            "page_no",
        ),
    )
