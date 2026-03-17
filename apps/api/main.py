"""API service entry point."""
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import Optional

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.core.semantic_contract_v2 import EquipmentClassExplainEnvelope, SemanticApiEnvelope
from packages.db.session import get_db
from packages.retrieval.service import RetrievalService
from packages.retrieval.semantic_service import SemanticRetrievalService

# Setup logging
setup_logging(settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="KnowFabric API",
    version="0.1.0",
    description="Industrial Knowledge Injection Platform"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "KnowFabric API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/api/v1/chunks/search", response_model=dict)
async def search_chunks(
    query: str = Query(..., description="Search query"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    doc_id: Optional[str] = Query(None, description="Filter by document ID"),
    limit: int = Query(20, ge=1, le=100, description="Result limit"),
    db: Session = Depends(get_db)
):
    """
    Search chunks with mandatory traceability.

    All results include:
    - chunk_id: Unique chunk identifier
    - doc_id: Source document ID
    - page_no: Source page number
    - evidence_text: Evidence text snippet
    """
    retrieval = RetrievalService()
    results = retrieval.search_chunks(
        db=db,
        query=query,
        domain=domain,
        doc_id=doc_id,
        limit=limit
    )

    # Validate traceability fields
    for result in results:
        if not all([
            result.get('chunk_id'),
            result.get('doc_id'),
            result.get('page_no') is not None,
            result.get('evidence_text')
        ]):
            raise ValueError("Result missing mandatory traceability fields")

    return {
        "success": True,
        "data": results,
        "metadata": {
            "total": len(results),
            "limit": limit,
            "query": query
        }
    }


@app.get(
    "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}",
    response_model=EquipmentClassExplainEnvelope,
)
async def explain_equipment_class(
    domain_id: str,
    equipment_class_id: str,
    language: str = Query("en", description="Preferred response language"),
    db: Session = Depends(get_db),
):
    """Explain a canonical equipment class from synced ontology metadata."""

    semantic = SemanticRetrievalService()
    try:
        result = semantic.explain_equipment_class(
            db=db,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            language=language,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Semantic index not ready. Run migrations and ontology sync first.",
        ) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Equipment class not found")

    return {
        "success": True,
        "data": result,
        "metadata": {
            "contract_version": "2026-03-17",
            "query_type": "explain_equipment_class",
            "filters_applied": {
                "domain_id": domain_id,
                "equipment_class_id": equipment_class_id,
                "language": language,
            },
            "total": 1,
            "limit": 1,
            "compatibility_surfaces": ["/api/v1/chunks/search", "trace_evidence", "search_knowledge"],
        },
    }


@app.get(
    "/api/v2/domains/{domain_id}/equipment-classes/{equipment_class_id}/fault-knowledge",
    response_model=SemanticApiEnvelope,
)
async def get_fault_knowledge(
    domain_id: str,
    equipment_class_id: str,
    fault_code: Optional[str] = Query(None, description="Optional fault code filter"),
    brand: Optional[str] = Query(None, description="Optional brand filter"),
    model_family: Optional[str] = Query(None, description="Optional model family filter"),
    include_related_symptoms: bool = Query(True, description="Include symptom and diagnostic knowledge"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    min_trust_level: str = Query("L4", pattern="^L[1-4]$", description="Minimum trust level"),
    limit: int = Query(20, ge=1, le=100, description="Result limit"),
    db: Session = Depends(get_db),
):
    """Retrieve evidence-grounded fault knowledge by canonical equipment class."""

    semantic = SemanticRetrievalService()
    try:
        result = semantic.get_fault_knowledge(
            db=db,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            fault_code=fault_code,
            brand=brand,
            model_family=model_family,
            include_related_symptoms=include_related_symptoms,
            min_confidence=min_confidence,
            min_trust_level=min_trust_level,
            limit=limit,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Semantic knowledge store not ready. Run migrations and populate knowledge objects first.",
        ) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Equipment class not found")

    return {
        "success": True,
        "data": result,
        "metadata": {
            "contract_version": "2026-03-17",
            "query_type": "fault_knowledge",
            "filters_applied": {
                "domain_id": domain_id,
                "equipment_class_id": equipment_class_id,
                "fault_code": fault_code,
                "brand": brand,
                "model_family": model_family,
                "include_related_symptoms": include_related_symptoms,
                "min_confidence": min_confidence,
                "min_trust_level": min_trust_level,
            },
            "total": len(result["items"]),
            "limit": limit,
            "compatibility_surfaces": ["/api/v1/chunks/search", "trace_evidence", "search_knowledge"],
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
