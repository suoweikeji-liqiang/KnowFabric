"""Minimal stdio MCP server for KnowFabric."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from packages.core.config import settings
from packages.core.logging import setup_logging
from packages.core.semantic_contract_v2 import (
    MCP_TOOL_EXPLAIN_EQUIPMENT_CLASS,
    MCP_TOOL_GET_APPLICATION_GUIDANCE,
    MCP_TOOL_GET_FAULT_KNOWLEDGE,
    MCP_TOOL_GET_MAINTENANCE_GUIDANCE,
    MCP_TOOL_GET_OPERATIONAL_GUIDANCE,
    MCP_TOOL_GET_PARAMETER_PROFILE,
)
from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal
from packages.domain_kit_v2.loader import discover_v2_package_roots, load_domain_package_v2
from packages.retrieval.semantic_service import SemanticRetrievalService
from packages.retrieval.service import RetrievalService


setup_logging(settings.log_level)


LEGACY_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_knowledge",
        "description": "Search chunk knowledge with full source traceability.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "domain": {
                    "type": "string",
                    "description": "Domain filter such as 'hvac' or 'drive'",
                },
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "trace_evidence",
        "description": "Trace a chunk back to chunk, page, and document evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "string", "description": "Chunk identifier to trace"}
            },
            "required": ["chunk_id"],
        },
    },
    {
        "name": "list_domains",
        "description": "List available domains and their v2 package coverage.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class McpProtocolError(Exception):
    """Protocol-level error for JSON-RPC handling."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class KnowFabricMcpServer:
    """Minimal MCP server implementation over stdio."""

    def __init__(self) -> None:
        self.retrieval = RetrievalService()
        self.semantic = SemanticRetrievalService()
        self.server_info = {
            "name": "knowfabric-mcp",
            "version": "0.1.0",
        }
        self.tool_schemas = LEGACY_MCP_TOOLS + [
            MCP_TOOL_GET_FAULT_KNOWLEDGE,
            MCP_TOOL_GET_PARAMETER_PROFILE,
            MCP_TOOL_GET_MAINTENANCE_GUIDANCE,
            MCP_TOOL_GET_APPLICATION_GUIDANCE,
            MCP_TOOL_GET_OPERATIONAL_GUIDANCE,
            MCP_TOOL_EXPLAIN_EQUIPMENT_CLASS,
        ]

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle one JSON-RPC request and return a response if needed."""

        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") or {}

        if method == "notifications/initialized":
            return None
        try:
            if method == "initialize":
                result = self._initialize()
            elif method == "tools/list":
                result = self._tools_list()
            elif method == "tools/call":
                result = self._tools_call(params)
            else:
                raise McpProtocolError(-32601, f"Method not found: {method}")
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except McpProtocolError as exc:
            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": exc.code, "message": exc.message},
            }

    def _initialize(self) -> dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.server_info,
            "capabilities": {"tools": {}},
        }

    def _tools_list(self) -> dict[str, Any]:
        return {"tools": self.tool_schemas}

    def _tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if tool_name == "search_knowledge":
            payload = self._search_knowledge(arguments)
        elif tool_name == "trace_evidence":
            payload = self._trace_evidence(arguments)
        elif tool_name == "list_domains":
            payload = self._list_domains()
        elif tool_name == "get_fault_knowledge":
            payload = self._semantic_fault_knowledge(arguments)
        elif tool_name == "get_parameter_profile":
            payload = self._semantic_parameter_profile(arguments)
        elif tool_name == "get_maintenance_guidance":
            payload = self._semantic_maintenance_guidance(arguments)
        elif tool_name == "get_application_guidance":
            payload = self._semantic_application_guidance(arguments)
        elif tool_name == "get_operational_guidance":
            payload = self._semantic_operational_guidance(arguments)
        elif tool_name == "explain_equipment_class":
            payload = self._semantic_explain_equipment_class(arguments)
        else:
            raise McpProtocolError(-32602, f"Unknown tool: {tool_name}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2),
                }
            ]
        }

    def _with_session(self, fn):
        session = SessionLocal()
        try:
            return fn(session)
        finally:
            session.close()

    def _search_knowledge(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments.get("query")
        if not query:
            raise McpProtocolError(-32602, "search_knowledge requires 'query'")

        def run(session):
            results = self.retrieval.search_chunks(
                db=session,
                query=query,
                domain=arguments.get("domain"),
                limit=int(arguments.get("limit", 10)),
            )
            return {
                "success": True,
                "data": results,
                "metadata": {"total": len(results), "query": query},
            }

        return self._with_session(run)

    def _trace_evidence(self, arguments: dict[str, Any]) -> dict[str, Any]:
        chunk_id = arguments.get("chunk_id")
        if not chunk_id:
            raise McpProtocolError(-32602, "trace_evidence requires 'chunk_id'")

        def run(session):
            row = (
                session.query(ContentChunk, DocumentPage, Document)
                .join(DocumentPage, ContentChunk.page_id == DocumentPage.page_id)
                .join(Document, ContentChunk.doc_id == Document.doc_id)
                .filter(ContentChunk.chunk_id == chunk_id)
                .one_or_none()
            )
            if row is None:
                raise McpProtocolError(-32004, "Chunk not found")
            chunk, page, document = row
            return {
                "success": True,
                "data": {
                    "chunk": {
                        "chunk_id": chunk.chunk_id,
                        "page_no": chunk.page_no,
                        "chunk_type": chunk.chunk_type,
                        "cleaned_text": chunk.cleaned_text,
                        "evidence_anchor": chunk.evidence_anchor,
                    },
                    "page": {
                        "page_id": page.page_id,
                        "page_no": page.page_no,
                        "cleaned_text": page.cleaned_text,
                        "page_type": page.page_type,
                    },
                    "document": {
                        "doc_id": document.doc_id,
                        "file_name": document.file_name,
                        "source_domain": document.source_domain,
                        "storage_path": document.storage_path,
                    },
                },
            }

        return self._with_session(run)

    def _list_domains(self) -> dict[str, Any]:
        domains = []
        for root in discover_v2_package_roots("domain_packages"):
            bundle = load_domain_package_v2(root)
            equipment_classes = [
                item.id
                for item in bundle.ontology_classes.classes
                if item.kind == "equipment"
            ]
            domains.append(
                {
                    "domain_id": bundle.package.domain_id,
                    "domain_name": bundle.package.domain_name,
                    "package_version": bundle.package.package_version,
                    "supported_knowledge_objects": bundle.package.supported_knowledge_objects,
                    "equipment_classes": equipment_classes,
                }
            )
        return {"success": True, "data": domains, "metadata": {"total": len(domains)}}

    def _semantic_fault_knowledge(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not arguments.get("domain_id") or not arguments.get("equipment_class_id"):
            raise McpProtocolError(-32602, "get_fault_knowledge requires 'domain_id' and 'equipment_class_id'")

        def run(session):
            result = self.semantic.get_fault_knowledge(
                db=session,
                domain_id=arguments["domain_id"],
                equipment_class_id=arguments["equipment_class_id"],
                fault_code=arguments.get("fault_code"),
                brand=arguments.get("brand"),
                model_family=arguments.get("model_family"),
                include_related_symptoms=bool(arguments.get("include_related_symptoms", True)),
                min_confidence=arguments.get("min_confidence"),
                min_trust_level=arguments.get("min_trust_level", "L4"),
                limit=int(arguments.get("limit", 20)),
                language=arguments.get("language", "en"),
            )
            if result is None:
                raise McpProtocolError(-32004, "Equipment class not found")
            return result

        return self._with_session(run)

    def _semantic_parameter_profile(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not arguments.get("domain_id") or not arguments.get("equipment_class_id"):
            raise McpProtocolError(-32602, "get_parameter_profile requires 'domain_id' and 'equipment_class_id'")

        def run(session):
            result = self.semantic.get_parameter_profiles(
                db=session,
                domain_id=arguments["domain_id"],
                equipment_class_id=arguments["equipment_class_id"],
                parameter_category=arguments.get("parameter_category"),
                parameter_name=arguments.get("parameter_name"),
                brand=arguments.get("brand"),
                model_family=arguments.get("model_family"),
                min_confidence=arguments.get("min_confidence"),
                min_trust_level=arguments.get("min_trust_level", "L4"),
                limit=int(arguments.get("limit", 20)),
                language=arguments.get("language", "en"),
            )
            if result is None:
                raise McpProtocolError(-32004, "Equipment class not found")
            return result

        return self._with_session(run)

    def _semantic_maintenance_guidance(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not arguments.get("domain_id") or not arguments.get("equipment_class_id"):
            raise McpProtocolError(-32602, "get_maintenance_guidance requires 'domain_id' and 'equipment_class_id'")

        def run(session):
            result = self.semantic.get_maintenance_guidance(
                db=session,
                domain_id=arguments["domain_id"],
                equipment_class_id=arguments["equipment_class_id"],
                task_type=arguments.get("task_type"),
                brand=arguments.get("brand"),
                model_family=arguments.get("model_family"),
                include_diagnostic_steps=bool(arguments.get("include_diagnostic_steps", True)),
                min_confidence=arguments.get("min_confidence"),
                min_trust_level=arguments.get("min_trust_level", "L4"),
                limit=int(arguments.get("limit", 20)),
                language=arguments.get("language", "en"),
            )
            if result is None:
                raise McpProtocolError(-32004, "Equipment class not found")
            return result

        return self._with_session(run)

    def _semantic_application_guidance(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not arguments.get("domain_id") or not arguments.get("equipment_class_id"):
            raise McpProtocolError(-32602, "get_application_guidance requires 'domain_id' and 'equipment_class_id'")

        def run(session):
            result = self.semantic.get_application_guidance(
                db=session,
                domain_id=arguments["domain_id"],
                equipment_class_id=arguments["equipment_class_id"],
                application_type=arguments.get("application_type"),
                brand=arguments.get("brand"),
                model_family=arguments.get("model_family"),
                min_confidence=arguments.get("min_confidence"),
                min_trust_level=arguments.get("min_trust_level", "L4"),
                limit=int(arguments.get("limit", 20)),
                language=arguments.get("language", "en"),
            )
            if result is None:
                raise McpProtocolError(-32004, "Equipment class not found")
            return result

        return self._with_session(run)

    def _semantic_operational_guidance(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not arguments.get("domain_id") or not arguments.get("equipment_class_id"):
            raise McpProtocolError(-32602, "get_operational_guidance requires 'domain_id' and 'equipment_class_id'")

        def run(session):
            result = self.semantic.get_operational_guidance(
                db=session,
                domain_id=arguments["domain_id"],
                equipment_class_id=arguments["equipment_class_id"],
                guidance_type=arguments.get("guidance_type"),
                brand=arguments.get("brand"),
                model_family=arguments.get("model_family"),
                min_confidence=arguments.get("min_confidence"),
                min_trust_level=arguments.get("min_trust_level", "L4"),
                limit=int(arguments.get("limit", 20)),
                language=arguments.get("language", "en"),
            )
            if result is None:
                raise McpProtocolError(-32004, "Equipment class not found")
            return result

        return self._with_session(run)

    def _semantic_explain_equipment_class(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if not arguments.get("domain_id") or not arguments.get("equipment_class_id"):
            raise McpProtocolError(-32602, "explain_equipment_class requires 'domain_id' and 'equipment_class_id'")

        def run(session):
            result = self.semantic.explain_equipment_class(
                db=session,
                domain_id=arguments["domain_id"],
                equipment_class_id=arguments["equipment_class_id"],
                language=arguments.get("language", "en"),
            )
            if result is None:
                raise McpProtocolError(-32004, "Equipment class not found")
            return result

        return self._with_session(run)


def main() -> int:
    server = KnowFabricMcpServer()
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
        except json.JSONDecodeError:
            continue
        response = server.handle_request(request)
        if response is None:
            continue
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
