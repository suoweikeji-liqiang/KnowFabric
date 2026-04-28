"""Operator-facing admin web and internal workbench shell."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.exc import OperationalError


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.models_v2 import ChunkOntologyAnchorV2, KnowledgeObjectEvidenceV2, KnowledgeObjectV2, OntologyClassV2
from packages.db.session import SessionLocal
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.domain_kit_v2.manual_fixture import load_manual_fixture
from packages.chunking.service import ChunkingService
from packages.compiler.llm_compiler import default_enabled_llm_types
from packages.core.config import settings
from packages.ingest.service import IngestService
from packages.parser.service import ParserService
from packages.storage.manager import StorageManager
from scripts.apply_review_packs_batch import discover_review_pack_paths, inspect_review_pack
from scripts.apply_ready_review_bundle import apply_ready_review_bundle
from scripts.bootstrap_review_pack_curation import bootstrap_review_pack_file
from scripts.build_manual_fixture_from_review_candidates import build_manual_fixture_from_review_candidate_file
from scripts.check_review_pack_readiness import assess_review_pack_readiness
from scripts.prepare_review_pipeline_bundle import prepare_review_pipeline_bundle


STATIC_DIR = Path(__file__).resolve().parent / "static"
ARTIFACT_DIR = Path(os.environ.get("DEMO_ARTIFACT_DIR", ROOT_DIR / "output" / "demo"))
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures" / "manual_validation"
DOMAIN_PACKAGES_DIR = ROOT_DIR / "domain_packages"
WORKBENCH_REVIEW_ROOT = Path(
    os.environ.get("WORKBENCH_REVIEW_ROOT", os.environ.get("WORKBENCH_REVIEW_DIR", ROOT_DIR / "tmp" / "review_workspaces"))
)
ADMIN_WEB_HOST = os.environ.get("ADMIN_WEB_HOST", "127.0.0.1")
ADMIN_WEB_PORT = int(os.environ.get("ADMIN_WEB_PORT", "4173"))

COLD_PLANT_PRIMARY_ORDER = [
    "chiller",
    "chilled_water_pump",
    "condenser_water_pump",
    "cooling_tower",
]
COVERAGE_DOMAIN_LABELS = {
    "hvac": "暖通空调",
    "drive": "变频驱动",
}
KNOWLEDGE_TYPE_LABELS = {
    "fault_code": "故障代码",
    "parameter_spec": "参数规范",
    "application_guidance": "应用指导",
    "maintenance_procedure": "维护流程",
    "performance_spec": "性能规范",
    "symptom": "症状",
    "diagnostic_step": "诊断步骤",
    "commissioning_step": "调试步骤",
    "wiring_guidance": "接线指导",
}
REVIEW_BLOCKER_LABELS = {
    "pending_review_decisions": "仍有候选项待审阅",
    "no_accepted_entries": "当前没有可发布的已接受候选",
}
COLD_PLANT_CARD_META = {
    "chiller": {
        "label": "冷水机组",
        "role": "核心制冷设备",
        "focus": "展示设计容量、最小压差约束与冷机运行边界。",
    },
    "chilled_water_pump": {
        "label": "冷冻水泵",
        "role": "负荷侧输配",
        "focus": "展示分阶段设计转速和最小转速设定。",
    },
    "condenser_water_pump": {
        "label": "冷却水泵",
        "role": "冷源侧输配",
        "focus": "展示冷却水流量保障与分阶段泵速控制。",
    },
    "cooling_tower": {
        "label": "冷却塔",
        "role": "散热末端",
        "focus": "展示设计湿球、逼近温差和液位控制阈值。",
    },
    "ahu": {
        "label": "空气处理机组",
        "role": "下游联动对象",
        "focus": "展示冷站知识如何向末端空气系统运行模式和维护指导延展。",
    },
}
NAV_ITEMS = [
    {"id": "inbox", "label": "收件箱", "description": "今日优先级"},
    {"id": "documents", "label": "文档录入", "description": "录入与资料面板"},
    {"id": "review", "label": "候选审阅", "description": "审阅、校准与保存"},
    {"id": "apply", "label": "应用执行", "description": "准备度与应用"},
    {"id": "coverage", "label": "覆盖盘点", "description": "领域与设备类覆盖"},
    {"id": "demo", "label": "演示交付", "description": "演示与交付产物"},
]
COMMAND_SHORTCUTS = [
    {
        "label": "准备审阅包",
        "command": "python3 scripts/prepare_review_pipeline_bundle.py <domain> review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id>",
        "purpose": "从已有 Chunk 直接准备可审阅包。",
    },
    {
        "label": "准备审阅包（LLM 编译）",
        "command": "python3 scripts/prepare_review_pipeline_bundle.py <domain> review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id> --llm-backend-config llm_backends.json --llm-backend-name deepseek-remote --llm-type maintenance_procedure --llm-type application_guidance",
        "purpose": "使用 OpenAI 兼容编译后端增强维护流程和应用指导候选。",
    },
    {
        "label": "应用就绪审阅包",
        "command": "python3 scripts/apply_ready_review_bundle.py review_bundle",
        "purpose": "批量应用已完成审阅的审阅包。",
    },
    {
        "label": "质量门检查",
        "command": "bash scripts/check-all",
        "purpose": "在结束会话前跑绑定质量门。",
    },
]
REVIEW_STEPS = [
    "导入文档并确认领域与设备类。",
    "生成基于 Chunk 的候选项或审阅包。",
    "并排查看 Chunk、证据与审阅字段。",
    "接受、拒绝或保留待处理状态，再应用已就绪审阅包。",
]
APPLY_RULES = [
    "只有已就绪的审阅包可以进入应用。",
    "应用前必须保留 doc / page / Chunk 追溯链。",
    "本体设备类与知识对象必须同域对齐。",
    "应用后优先回查 API/MCP 读面，而不是只看文件写入。",
]

STORAGE_MANAGER = StorageManager(settings.storage_root)
INGEST_SERVICE = IngestService(STORAGE_MANAGER)
PARSER_SERVICE = ParserService(STORAGE_MANAGER)
CHUNKING_SERVICE = ChunkingService()


def _slugify(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip()).strip("_").lower()
    return value or "workspace"


def _workspace_id(domain_id: str, doc_id: str | None, equipment_class_id: str | None) -> str:
    parts = [domain_id]
    if doc_id:
        parts.append(doc_id)
    if equipment_class_id:
        parts.append(equipment_class_id)
    stem = "__".join(_slugify(item) for item in parts if item)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{stem}__{timestamp}"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _resolve_artifact_path(path: str | Path | None, *, base_dir: Path = ROOT_DIR) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def _load_optional_json(path: str | Path | None, *, base_dir: Path = ROOT_DIR) -> dict[str, Any] | None:
    resolved = _resolve_artifact_path(path, base_dir=base_dir)
    if not resolved or not resolved.exists():
        return None
    return _load_json(resolved)


def _load_optional_fixture(path: str | Path | None, *, base_dir: Path = ROOT_DIR) -> dict[str, Any] | None:
    resolved = _resolve_artifact_path(path, base_dir=base_dir)
    if not resolved or not resolved.exists():
        return None
    try:
        return load_manual_fixture(resolved)
    except Exception:
        return None


def _artifact_url(path: str | Path | None) -> str | None:
    if not path:
        return None
    return f"/artifacts/{Path(path).name}"


def _surface_key(path: Path) -> str:
    name = path.name
    if name.endswith("__api_smoke_report.json"):
        return "api"
    if name.endswith("__mcp_smoke_report.json"):
        return "mcp"
    return "semantic"


def _domain_id(report: dict[str, Any]) -> str:
    example_file = Path(report.get("example_file", ""))
    if len(example_file.parts) >= 2:
        return example_file.parts[1]
    return "unknown"


def _surface_status(report: dict[str, Any], surface: str) -> str:
    summary = report.get("summary", {})
    if surface == "mcp":
        checks_ok = report.get("initialize_ok") and report.get("tools_list_ok")
        return "passed" if checks_ok and summary.get("failed", 0) == 0 else "failed"
    if surface == "api":
        health_ok = report.get("health", {}).get("status") == "passed"
        return "passed" if health_ok and summary.get("failed", 0) == 0 else "failed"
    return "passed" if summary.get("failed", 0) == 0 else "failed"


def _normalize_query_item(item: dict[str, Any], surface: str) -> dict[str, Any]:
    highlights = item.get("found_items") or []
    first = highlights[0] if highlights else {}
    return {
        "id": item.get("id"),
        "description": item.get("description"),
        "query": item.get("query"),
        "query_type": item.get("query_type"),
        "surface": surface,
        "status": item.get("status"),
        "equipment_class_id": item.get("request", {}).get("equipment_class_id"),
        "canonical_keys": item.get("found_canonical_keys", []),
        "title": first.get("title"),
        "summary": first.get("summary"),
        "display_language": first.get("display_language"),
    }


def _domain_payload(domain_id: str, reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    queries: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    report_urls: dict[str, str | None] = {}
    for surface, report in sorted(reports.items()):
        statuses[surface] = _surface_status(report, surface)
        report_urls[surface] = _artifact_url(report.get("_path"))
        queries.extend(_normalize_query_item(item, surface) for item in report.get("results", []))
    return {
        "domain_id": domain_id,
        "label": COVERAGE_DOMAIN_LABELS.get(domain_id, domain_id),
        "statuses": statuses,
        "report_urls": report_urls,
        "queries": queries,
    }


def _load_reports(bundle_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for path in sorted(bundle_dir.glob("*__*.json")):
        if path.name in {"live_demo_evaluation_manifest.json", "demo_environment_preflight.json"}:
            continue
        report = _load_json(path)
        report["_path"] = str(path)
        grouped.setdefault(_domain_id(report), {})[_surface_key(path)] = report
    return grouped


def _query_groups_by_equipment(queries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in queries:
        equipment_class_id = item.get("equipment_class_id")
        if not equipment_class_id:
            continue
        grouped.setdefault(str(equipment_class_id), []).append(item)
    return grouped


def _cold_plant_card(equipment_class_id: str, queries: list[dict[str, Any]]) -> dict[str, Any]:
    meta = COLD_PLANT_CARD_META[equipment_class_id]
    highlights = [
        {
            "title": item.get("title") or item.get("description") or item.get("id"),
            "summary": item.get("summary") or item.get("query"),
            "surface": item.get("surface"),
            "query_type": item.get("query_type"),
        }
        for item in queries
    ]
    return {
        "equipment_class_id": equipment_class_id,
        "label": meta["label"],
        "role": meta["role"],
        "focus": meta["focus"],
        "query_count": len(queries),
        "highlights": highlights,
    }


def _cold_plant_scenario(domains: list[dict[str, Any]]) -> dict[str, Any]:
    hvac = next((item for item in domains if item["domain_id"] == "hvac"), None)
    drive = next((item for item in domains if item["domain_id"] == "drive"), None)
    grouped = _query_groups_by_equipment(hvac["queries"] if hvac else [])
    primary_cards = [
        _cold_plant_card(equipment_class_id, grouped[equipment_class_id])
        for equipment_class_id in COLD_PLANT_PRIMARY_ORDER
        if grouped.get(equipment_class_id)
    ]
    downstream_cards = [
        _cold_plant_card("ahu", grouped["ahu"])
        for _ in [0]
        if grouped.get("ahu")
    ]
    extension_domains = []
    if drive:
        extension_domains.append(
            {
                "domain_id": drive["domain_id"],
                "label": drive["label"],
                "query_count": len(drive["queries"]),
                "summary": "作为冷站控制外围能力，还可展示变频驱动故障、参数和接线指导。",
            }
        )
    return {
        "id": "cold_plant_control",
        "title": "冷站控制知识演示",
        "subtitle": "围绕冷水机组、冷冻水泵、冷却水泵与冷却塔的参数、约束、维护和控制知识，形成面向试点客户的中文演示视图。",
        "demo_steps": [
            "先看冷水机组设计容量与最小压差，确定冷站主机的能力边界。",
            "再看冷冻水泵与冷却水泵的分阶段转速和最小转速，说明输配控制约束。",
            "最后看冷却塔设计湿球与逼近温差，串联出完整冷站控制逻辑。",
            "如需扩展，再下钻到 AHU 联动和变频驱动故障/参数知识。",
        ],
        "customer_questions": [
            "这套系统能不能把冷站控制边界条件说清楚？",
            "泵速、最小流量、冷却塔条件这些知识有没有证据支撑？",
            "客户后续导入自己的资料后，能不能复用同一条交付链？",
            "如果需要给运维或设计团队展示，能不能不用直接看 JSON？",
        ],
        "primary_cards": primary_cards,
        "downstream_cards": downstream_cards,
        "extension_domains": extension_domains,
    }


def load_demo_bundle(bundle_dir: Path = ARTIFACT_DIR) -> dict[str, Any]:
    manifest_path = bundle_dir / "live_demo_evaluation_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing evaluation manifest: {manifest_path}")
    manifest = _load_json(manifest_path)
    reports = _load_reports(bundle_dir)
    domains = [_domain_payload(domain_id, grouped) for domain_id, grouped in sorted(reports.items())]
    return {
        "bundle_language": manifest.get("bundle_language", "zh"),
        "generated_at": manifest.get("generated_at"),
        "statuses": manifest.get("statuses", {}),
        "counts": manifest.get("counts", {}),
        "handoff": manifest.get("handoff", {}),
        "paths": {
            "brief": _artifact_url(manifest.get("paths", {}).get("brief")),
            "manifest": _artifact_url(manifest_path),
            "preflight_report": _artifact_url(manifest.get("paths", {}).get("preflight_report")),
            "api_log": _artifact_url(manifest.get("paths", {}).get("api_log")),
            "cover_note": _artifact_url(manifest.get("handoff", {}).get("primary_artifacts", {}).get("cover_note")),
        },
        "brief_text": _load_optional_text(bundle_dir / "v1_demo_brief.md"),
        "cover_note_text": _load_optional_text(bundle_dir / "EVALUATOR_NOTE.md"),
        "scenario": _cold_plant_scenario(domains),
        "domains": domains,
    }


def _load_inventory_path(domain_id: str) -> Path:
    return DOMAIN_PACKAGES_DIR / domain_id / "v2" / "coverage" / "knowledge_inventory.yaml"


def _ensure_document_record(
    documents: dict[str, dict[str, Any]],
    path: Path,
    entry: dict[str, Any],
) -> None:
    doc = entry["doc"]
    page = entry["page"]
    record = documents.setdefault(
        doc["doc_id"],
        {
            "doc_id": doc["doc_id"],
            "file_name": doc["file_name"],
            "source_domain": doc["source_domain"],
            "fixture_paths": set(),
            "equipment_classes": set(),
            "knowledge_types": set(),
            "page_refs": set(),
            "page_types": set(),
            "brands": set(),
            "model_families": set(),
            "entry_count": 0,
        },
    )
    record["fixture_paths"].add(str(path.relative_to(ROOT_DIR)))
    record["equipment_classes"].add(entry.get("equipment_class_id") or entry.get("equipment_class_key", "").split(":")[-1])
    record["knowledge_types"].add(entry.get("knowledge_object_type", "fault_code"))
    record["page_refs"].add(page["page_no"])
    record["page_types"].add(page["page_type"])
    applicability = entry.get("applicability", {})
    if applicability.get("brand"):
        record["brands"].add(applicability["brand"])
    if applicability.get("model_family"):
        record["model_families"].add(applicability["model_family"])
    record["entry_count"] += 1


def _finalize_document_records(documents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    finalized = []
    for record in documents.values():
        finalized.append(
            {
                "doc_id": record["doc_id"],
                "file_name": record["file_name"],
                "source_domain": record["source_domain"],
                "fixture_paths": sorted(record["fixture_paths"]),
                "equipment_classes": sorted(record["equipment_classes"]),
                "knowledge_types": sorted(record["knowledge_types"]),
                "page_refs": sorted(record["page_refs"]),
                "page_types": sorted(record["page_types"]),
                "brands": sorted(record["brands"]),
                "model_families": sorted(record["model_families"]),
                "entry_count": record["entry_count"],
            }
        )
    return sorted(finalized, key=lambda item: (item["source_domain"], item["file_name"]))


def _load_fixture_catalog(base_dir: Path = FIXTURE_DIR) -> list[dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for path in sorted(base_dir.glob("*.json")):
        fixture = _load_json(path)
        for entry in fixture.get("manual_entries", []):
            materialized_entry = {
                **entry,
                "equipment_class_id": fixture.get("equipment_class_id"),
                "equipment_class_key": fixture.get("equipment_class_key"),
            }
            _ensure_document_record(documents, path, materialized_entry)
    return _finalize_document_records(documents)


def _load_documents_from_db() -> list[dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = (
            session.query(
                Document.doc_id,
                Document.file_name,
                Document.source_domain,
                Document.parse_status,
                Document.import_time,
                func.count(func.distinct(DocumentPage.page_id)).label("page_count"),
                func.count(func.distinct(ContentChunk.chunk_id)).label("chunk_count"),
            )
            .outerjoin(DocumentPage, DocumentPage.doc_id == Document.doc_id)
            .outerjoin(ContentChunk, ContentChunk.doc_id == Document.doc_id)
            .filter(Document.is_active.is_(True))
            .group_by(
                Document.doc_id,
                Document.file_name,
                Document.source_domain,
                Document.parse_status,
                Document.import_time,
            )
            .order_by(Document.import_time.desc(), Document.doc_id.desc())
            .all()
        )
        documents = []
        for row in rows:
            documents.append(
                {
                    "doc_id": row.doc_id,
                    "file_name": row.file_name,
                    "source_domain": row.source_domain,
                    "source_kind": "db",
                    "parse_status": row.parse_status,
                    "page_count": int(row.page_count or 0),
                    "chunk_count": int(row.chunk_count or 0),
                    "import_time": row.import_time.isoformat() if row.import_time else None,
                    "storage_path": None,
                    "fixture_paths": [],
                    "equipment_classes": [],
                    "knowledge_types": [],
                    "page_refs": [],
                    "page_types": [],
                    "brands": [],
                    "model_families": [],
                    "entry_count": int(row.chunk_count or 0),
                    "actionable": bool(row.source_domain),
                }
            )
        return documents
    finally:
        session.close()


def _load_document_catalog() -> dict[str, Any]:
    try:
        db_documents = _load_documents_from_db()
        db_available = True
    except OperationalError:
        db_documents = []
        db_available = False
    fixture_documents = [
        {**item, "source_kind": "fixture", "actionable": False}
        for item in _load_fixture_catalog()
    ]
    return {
        "db_available": db_available,
        "documents": db_documents,
        "fixture_samples": fixture_documents,
    }


def _document_summary(db, doc_id: str) -> dict[str, Any]:
    row = (
        db.query(
            Document.doc_id,
            Document.file_name,
            Document.source_domain,
            Document.parse_status,
            Document.import_time,
            Document.storage_path,
            func.count(func.distinct(DocumentPage.page_id)).label("page_count"),
            func.count(func.distinct(ContentChunk.chunk_id)).label("chunk_count"),
        )
        .outerjoin(DocumentPage, DocumentPage.doc_id == Document.doc_id)
        .outerjoin(ContentChunk, ContentChunk.doc_id == Document.doc_id)
        .filter(Document.doc_id == doc_id)
        .group_by(
            Document.doc_id,
            Document.file_name,
            Document.source_domain,
            Document.parse_status,
            Document.import_time,
            Document.storage_path,
        )
        .one()
    )
    return {
        "doc_id": row.doc_id,
        "file_name": row.file_name,
        "source_domain": row.source_domain,
        "source_kind": "db",
        "parse_status": row.parse_status,
        "page_count": int(row.page_count or 0),
        "chunk_count": int(row.chunk_count or 0),
        "import_time": row.import_time.isoformat() if row.import_time else None,
        "storage_path": row.storage_path,
        "fixture_paths": [],
        "equipment_classes": [],
        "knowledge_types": [],
        "page_refs": [],
        "page_types": [],
        "brands": [],
        "model_families": [],
        "entry_count": int(row.chunk_count or 0),
        "actionable": True,
    }


def _run_document_parse(doc_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        return PARSER_SERVICE.parse_document(db, doc_id)
    finally:
        db.close()


def _run_document_chunk(doc_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        return CHUNKING_SERVICE.chunk_document(db, doc_id)
    finally:
        db.close()


async def _import_uploaded_document(upload: UploadFile, source_domain: str | None) -> dict[str, Any]:
    suffix = Path(upload.filename or "upload.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        temp_path = Path(handle.name)
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    db = SessionLocal()
    try:
        doc_id = INGEST_SERVICE.import_document(
            db,
            str(temp_path),
            source_domain=source_domain,
        )
        if doc_id is None:
            raise ValueError("Duplicate document detected")
        return _document_summary(db, doc_id)
    finally:
        db.close()
        temp_path.unlink(missing_ok=True)


def _priority_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["equipment_class_id"]): item for item in items}


def _inventory_entries(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = inventory.get("current_fixture_coverage", {}).get("equipment_classes", [])
    return {str(item["equipment_class_id"]): item for item in items}


def _coverage_status(covered: list[str], missing: list[str]) -> str:
    if not covered:
        return "uncovered"
    if missing:
        return "partial"
    return "covered"


def _equipment_coverage_rows(domain_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    bundle = load_domain_package_v2(DOMAIN_PACKAGES_DIR / domain_id / "v2")
    inventory = _load_yaml(_load_inventory_path(domain_id)).get("coverage_inventory", {})
    inventory_map = _inventory_entries(inventory)
    priority = _priority_map(inventory.get("internal_priority_queue", []))
    rows = []
    for item in bundle.ontology_classes.classes:
        if item.kind != "equipment":
            continue
        entry = inventory_map.get(item.id, {})
        covered = list(entry.get("covered_knowledge_objects", []))
        missing = [anchor for anchor in item.knowledge_anchors if anchor not in covered]
        focus = priority.get(item.id, {})
        rows.append(
            {
                "equipment_class_id": item.id,
                "label": item.label.get("zh") or item.label.get("en") or item.id,
                "coverage_status": entry.get("coverage_status") or _coverage_status(covered, missing),
                "covered_knowledge_objects": covered,
                "missing_knowledge_objects": missing,
                "supported_knowledge_objects": list(item.knowledge_anchors),
                "fixture_paths": list(entry.get("fixture_paths", [])),
                "notes": entry.get("notes"),
                "next_targets": list(focus.get("target_knowledge_objects", [])),
                "rationale": focus.get("rationale"),
            }
        )
    rows.sort(key=lambda item: (item["coverage_status"] == "covered", item["coverage_status"] == "partial", item["label"]))
    return inventory, rows


def _domain_workbench_payload(domain_id: str) -> dict[str, Any]:
    bundle = load_domain_package_v2(DOMAIN_PACKAGES_DIR / domain_id / "v2")
    inventory, rows = _equipment_coverage_rows(domain_id)
    covered = sum(1 for row in rows if row["covered_knowledge_objects"])
    uncovered = sum(1 for row in rows if not row["covered_knowledge_objects"])
    return {
        "domain_id": bundle.package.domain_id,
        "domain_name": COVERAGE_DOMAIN_LABELS.get(bundle.package.domain_id, bundle.package.domain_name),
        "supported_knowledge_objects": bundle.package.supported_knowledge_objects,
        "covered_equipment_classes": covered,
        "uncovered_equipment_classes": uncovered,
        "priority_queue": inventory.get("internal_priority_queue", []),
        "equipment_classes": rows,
    }


def _console_review_status(value: str | None) -> str:
    if value in {"approved", "accepted"}:
        return "accepted"
    if value == "rejected":
        return "rejected"
    if value == "review_ready":
        return "review_ready"
    return "pending"


def _console_publish_status(value: str | None) -> str:
    if value in {"approved", "accepted"}:
        return "published"
    if value == "rejected":
        return "archived"
    if value == "review_ready":
        return "reviewed"
    return "draft"


def _console_source_type(file_name: str) -> str:
    lowered = file_name.lower()
    if "ashrae" in lowered or "authority" in lowered or "baseline" in lowered:
        return "authority"
    if any(token in lowered for token in ["abb", "siemens", "carrier", "manual", "guide"]):
        return "vendor"
    return "manual"


def _console_stage_summary(parse_status: str | None, chunk_count: int) -> str:
    if parse_status == "failed":
        return "处理失败，需回查原始资料。"
    if chunk_count > 0:
        return "已完成切块，可继续进入审阅和成果查看。"
    if parse_status in {"completed", "parsed"}:
        return "已完成解析，等待切块。"
    return "已导入，等待后续处理。"


def _console_stage_timeline(parse_status: str | None, chunk_count: int) -> list[str]:
    timeline = ["导入完成"]
    if parse_status in {"completed", "parsed"}:
        timeline.append("解析完成")
    if chunk_count > 0:
        timeline.append("切块完成")
    if parse_status == "failed":
        timeline.append("处理失败")
    return timeline


def _console_applicability_labels(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    labels: list[str] = []
    for key, value in payload.items():
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            labels.extend(str(item) for item in value if item not in (None, ""))
        else:
            labels.append(str(value))
    return labels


def _console_language_candidates(language: str | None) -> list[str]:
    if not language:
        return ["zh", "en"]
    candidates = [language]
    base_language = language.split("-", 1)[0]
    if base_language not in candidates:
        candidates.append(base_language)
    if "zh" not in candidates:
        candidates.append("zh")
    if "en" not in candidates:
        candidates.append("en")
    return candidates


def _console_public_structured_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    source = payload or {}
    return {
        key: value
        for key, value in source.items()
        if not str(key).startswith("_")
    }


def _contains_cjk(text: str | None) -> bool:
    if not text:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _compact_display_text(text: str | None, *, limit: int = 36) -> str:
    value = str(text or "").replace("\n", " ").strip()
    if len(value) <= limit:
        return value
    return f"{value[:limit]}..."


def _console_localized_summary(
    summary: str | None,
    *,
    domain_id: str,
    equipment_label: str,
    covered_count: int,
    missing_count: int,
) -> str:
    value = str(summary or "").strip()
    if _contains_cjk(value):
        return value
    if covered_count and missing_count:
        return f"{equipment_label} 已形成部分覆盖，当前还缺 {missing_count} 类知识对象。"
    if covered_count and not missing_count:
        return f"{equipment_label} 当前已形成相对完整的知识覆盖。"
    return f"{equipment_label} 当前仍缺少可直接交付的知识成果。"


def _console_publish_summary(item: dict[str, Any], domain_id: str) -> str:
    if item.get("status") == "ready":
        accepted = int(item.get("accepted_count") or 0)
        return f"{item.get('doc_name') or item['pack_file']} 已具备发布条件，当前可应用 {accepted} 条成果。"
    pending = int(item.get("pending_count") or 0)
    return f"{item.get('doc_name') or item['pack_file']} 仍有 {pending} 条候选未就绪，暂不能发布。"


def _console_pack_status(value: str | None) -> str:
    if value == "review_complete" or value == "ready":
        return "ready"
    if value in {"blocked_no_accepted", "blocked_invalid"}:
        return "blocked"
    return "pending"


def _console_release_status_from_counts(success_count: int, failure_count: int) -> str:
    if success_count > 0 and failure_count == 0:
        return "success"
    if success_count > 0:
        return "partial"
    return "failed"


def _console_release_note_blocker(blocker: str | None) -> str | None:
    if not blocker:
        return None
    return REVIEW_BLOCKER_LABELS.get(blocker, blocker)


def _console_knowledge_type_label(value: str | None) -> str:
    if not value:
        return "未标注类型"
    return KNOWLEDGE_TYPE_LABELS.get(value, value)


def _console_pack_type_label(detail: dict[str, Any] | None, *, accepted_only: bool = False) -> str:
    if not isinstance(detail, dict):
        return "审阅包"
    types = []
    for entry in detail.get("candidate_entries", []):
        if accepted_only and entry.get("review_decision") != "accepted":
            continue
        knowledge_type = str(entry.get("knowledge_object_type") or "").strip()
        if knowledge_type and knowledge_type not in types:
            types.append(knowledge_type)
    if not types:
        return "审阅包"
    return " / ".join(_console_knowledge_type_label(item) for item in types)


def _fixture_from_review_pack(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        return build_manual_fixture_from_review_candidate_file(path)
    except Exception:
        return None


def _release_item_note(
    *,
    canonical_key: str | None,
    trust_level: str | None,
    extra: str | None = None,
) -> str:
    parts = []
    if canonical_key:
        parts.append(str(canonical_key))
    if trust_level:
        parts.append(f"可信 {trust_level}")
    if extra:
        parts.append(extra)
    return " · ".join(parts)


def _release_item_from_manual_entry(
    entry: dict[str, Any],
    *,
    pack_file: str,
    fixture: dict[str, Any],
    equipment_class_label: str,
    result: str,
    extra_note: str | None = None,
) -> dict[str, Any]:
    doc = entry.get("doc", {})
    return {
        "name": entry.get("title") or entry.get("canonical_key") or entry.get("knowledge_object_id"),
        "type": _console_knowledge_type_label(entry.get("knowledge_object_type")),
        "result": result,
        "note": _release_item_note(
            canonical_key=entry.get("canonical_key"),
            trust_level=entry.get("trust_level"),
            extra=extra_note,
        ),
        "packId": pack_file,
        "knowledgeObjectId": entry.get("knowledge_object_id"),
        "canonicalKey": entry.get("canonical_key"),
        "docId": doc.get("doc_id"),
        "docName": doc.get("file_name"),
        "equipmentClassId": fixture.get("equipment_class_id"),
        "equipmentClassLabel": equipment_class_label,
    }


def _release_fallback_item(
    *,
    pack_file: str,
    pack_name: str,
    result: str,
    extra_note: str | None,
    pack_meta: dict[str, Any],
    equipment_class_label: str,
) -> dict[str, Any]:
    return {
        "name": pack_name,
        "type": "审阅包",
        "result": result,
        "note": extra_note or "",
        "packId": pack_file,
        "knowledgeObjectId": None,
        "canonicalKey": None,
        "docId": pack_meta.get("doc_id"),
        "docName": pack_meta.get("doc_name"),
        "equipmentClassId": pack_meta.get("equipment_class_id"),
        "equipmentClassLabel": equipment_class_label,
    }


def _review_pack_updated_at(path: Path, detail: dict[str, Any] | None = None) -> str:
    if isinstance(detail, dict):
        bootstrap_metadata = detail.get("bootstrap_metadata")
        if isinstance(bootstrap_metadata, dict) and bootstrap_metadata.get("generated_at"):
            return str(bootstrap_metadata["generated_at"])
        if detail.get("generated_at"):
            return str(detail["generated_at"])
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _review_pack_candidate_ids(detail: dict[str, Any] | None) -> list[str]:
    if not isinstance(detail, dict):
        return []
    return [
        str(entry.get("candidate_id"))
        for entry in detail.get("candidate_entries", [])
        if entry.get("candidate_id")
    ]


def _publish_preview_record_id(workspace_id: str) -> str:
    return f"preview__{_slugify(workspace_id)}"


def _publish_run_record_id(workspace_id: str, generated_at: str | None) -> str:
    return f"apply__{_slugify(workspace_id)}__{_slugify(generated_at or 'latest')}"


def _console_resolve_display_content(
    knowledge_object: KnowledgeObjectV2,
    language: str = "zh",
) -> tuple[str, str, dict[str, Any], str]:
    payload = knowledge_object.structured_payload_json or {}
    localized_display = payload.get("_localized_display", {})
    structured_payload = _console_public_structured_payload(payload)
    if isinstance(localized_display, dict):
        for candidate in _console_language_candidates(language):
            candidate_payload = localized_display.get(candidate)
            if not isinstance(candidate_payload, dict):
                continue
            localized_title = candidate_payload.get("title") or knowledge_object.title or knowledge_object.canonical_key
            localized_summary = candidate_payload.get("summary") or knowledge_object.summary or ""
            localized_structured_payload = candidate_payload.get("structured_payload")
            if isinstance(localized_structured_payload, dict):
                structured_payload = {
                    **structured_payload,
                    **localized_structured_payload,
                }
            return str(localized_title), str(localized_summary), structured_payload, candidate
    return (
        str(knowledge_object.title or knowledge_object.canonical_key),
        str(knowledge_object.summary or ""),
        structured_payload,
        "en",
    )


def _console_resolve_class_label(labels_json: dict[str, Any] | None, fallback: str, language: str = "zh") -> str:
    labels = labels_json or {}
    for candidate in _console_language_candidates(language):
        value = labels.get(candidate)
        if isinstance(value, str) and value.strip():
            return value
    return fallback


def _console_ontology_label_map(
    db,
    *,
    domain_ids: list[str],
    language: str = "zh",
) -> dict[tuple[str, str], str]:
    ontology_rows = (
        db.query(
            OntologyClassV2.domain_id,
            OntologyClassV2.ontology_class_id,
            OntologyClassV2.primary_label,
            OntologyClassV2.labels_json,
        )
        .filter(OntologyClassV2.domain_id.in_(domain_ids))
        .all()
    )
    return {
        (str(row.domain_id), str(row.ontology_class_id)): _console_resolve_class_label(
            row.labels_json,
            str(row.primary_label),
            language,
        )
        for row in ontology_rows
    }


def _console_documents_index() -> dict[str, dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(
                Document.doc_id,
                Document.file_name,
                Document.source_domain,
                Document.parse_status,
                Document.import_time,
            )
            .order_by(Document.import_time.desc(), Document.doc_id)
            .all()
        )
        return {
            str(row.doc_id): {
                "id": row.doc_id,
                "fileName": row.file_name,
                "domainId": row.source_domain or "hvac",
                "equipmentClasses": [],
                "status": "parsed" if row.parse_status in {"completed", "parsed"} else "imported",
                "pageCount": 0,
                "chunkCount": 0,
                "importedAt": row.import_time.isoformat() if row.import_time else "-",
                "sourceType": _console_source_type(row.file_name or ""),
                "stageSummary": _console_stage_summary(row.parse_status, 0),
                "stageTimeline": _console_stage_timeline(row.parse_status, 0),
                "pageNotes": [],
                "chunkHighlights": [],
                "linkedAssetIds": [],
            }
            for row in rows
        }
    finally:
        db.close()


def load_console_knowledge_assets(language: str = "zh") -> dict[str, Any]:
    db = SessionLocal()
    try:
        knowledge_objects = (
            db.query(KnowledgeObjectV2)
            .order_by(KnowledgeObjectV2.updated_at.desc(), KnowledgeObjectV2.knowledge_object_id)
            .all()
        )
        if not knowledge_objects:
            return {"assets": [], "relatedDocumentsByAsset": {}}

        document_index = _console_documents_index()
        ontology_label_map = _console_ontology_label_map(
            db,
            domain_ids=[item.domain_id for item in knowledge_objects],
            language=language,
        )
        evidence_rows = (
            db.query(
                KnowledgeObjectEvidenceV2.knowledge_object_id,
                KnowledgeObjectEvidenceV2.doc_id,
                KnowledgeObjectEvidenceV2.page_no,
                KnowledgeObjectEvidenceV2.chunk_id,
                KnowledgeObjectEvidenceV2.evidence_text,
                Document.file_name,
            )
            .join(Document, Document.doc_id == KnowledgeObjectEvidenceV2.doc_id)
            .filter(
                KnowledgeObjectEvidenceV2.knowledge_object_id.in_(
                    [item.knowledge_object_id for item in knowledge_objects]
                )
            )
            .order_by(
                KnowledgeObjectEvidenceV2.knowledge_object_id,
                KnowledgeObjectEvidenceV2.page_no,
                KnowledgeObjectEvidenceV2.chunk_id,
            )
            .all()
        )

        evidence_by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
        related_docs_by_object: dict[str, list[str]] = defaultdict(list)
        for row in evidence_rows:
            evidence_by_object[str(row.knowledge_object_id)].append(
                {
                    "docId": row.doc_id,
                    "documentName": row.file_name,
                    "pageNo": row.page_no,
                    "chunkId": row.chunk_id,
                    "excerpt": (row.evidence_text or "")[:160],
                    "evidenceText": row.evidence_text,
                }
            )
            if row.doc_id not in related_docs_by_object[str(row.knowledge_object_id)]:
                related_docs_by_object[str(row.knowledge_object_id)].append(row.doc_id)

        related_assets_map: dict[str, list[str]] = defaultdict(list)
        by_equipment: dict[tuple[str, str], list[str]] = defaultdict(list)
        for item in knowledge_objects:
            by_equipment[(item.domain_id, item.ontology_class_id)].append(item.knowledge_object_id)
        for keys in by_equipment.values():
            for current in keys:
                related_assets_map[current] = [value for value in keys if value != current][:4]

        assets = []
        related_documents_by_asset: dict[str, list[dict[str, Any]]] = {}
        for item in knowledge_objects:
            knowledge_id = str(item.knowledge_object_id)
            evidences = evidence_by_object.get(knowledge_id, [])
            related_doc_ids = related_docs_by_object.get(knowledge_id, [])
            title, summary, structured_payload, display_language = _console_resolve_display_content(item, language)
            equipment_class_label = ontology_label_map.get(
                (str(item.domain_id), str(item.ontology_class_id)),
                str(item.ontology_class_id),
            )
            related_documents_by_asset[knowledge_id] = [
                document_index[doc_id]
                for doc_id in related_doc_ids
                if doc_id in document_index
            ]
            assets.append(
                {
                    "id": knowledge_id,
                    "title": title,
                    "canonicalKey": item.canonical_key,
                    "domainId": item.domain_id,
                    "equipmentClass": item.ontology_class_id,
                    "equipmentClassLabel": equipment_class_label,
                    "type": item.knowledge_object_type,
                    "reviewStatus": _console_review_status(item.review_status),
                    "publishStatus": _console_publish_status(item.review_status),
                    "sourceDocument": evidences[0]["documentName"] if evidences else "-",
                    "updatedAt": item.updated_at.isoformat() if item.updated_at else "",
                    "summary": summary,
                    "trustLevel": item.trust_level,
                    "applicability": _console_applicability_labels(item.applicability_json),
                    "payload": json.dumps(structured_payload, ensure_ascii=False, indent=2),
                    "displayLanguage": display_language,
                    "evidence": evidences,
                    "relatedAssets": related_assets_map.get(knowledge_id, []),
                }
            )
        return {
            "assets": assets,
            "relatedDocumentsByAsset": related_documents_by_asset,
        }
    finally:
        db.close()


def _console_linked_asset_ids_by_doc(assets: list[dict[str, Any]]) -> dict[str, list[str]]:
    linked: dict[str, list[str]] = defaultdict(list)
    for asset in assets:
        asset_id = str(asset["id"])
        for evidence in asset.get("evidence", []):
            doc_id = str(evidence.get("docId") or "")
            if doc_id and asset_id not in linked[doc_id]:
                linked[doc_id].append(asset_id)
    return linked


def _console_prepare_targets_by_doc(
    db,
    *,
    doc_ids: list[str],
    language: str = "zh",
) -> dict[str, list[dict[str, Any]]]:
    if not doc_ids:
        return {}
    rows = (
        db.query(
            ContentChunk.doc_id,
            ChunkOntologyAnchorV2.domain_id,
            ChunkOntologyAnchorV2.ontology_class_id,
            func.count(func.distinct(ChunkOntologyAnchorV2.chunk_id)).label("anchor_count"),
        )
        .join(ContentChunk, ContentChunk.chunk_id == ChunkOntologyAnchorV2.chunk_id)
        .filter(ContentChunk.doc_id.in_(doc_ids))
        .group_by(
            ContentChunk.doc_id,
            ChunkOntologyAnchorV2.domain_id,
            ChunkOntologyAnchorV2.ontology_class_id,
        )
        .order_by(ContentChunk.doc_id, func.count(func.distinct(ChunkOntologyAnchorV2.chunk_id)).desc())
        .all()
    )
    label_map = _console_ontology_label_map(
        db,
        domain_ids=sorted({str(row.domain_id) for row in rows if row.domain_id}),
        language=language,
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.doc_id)].append(
            {
                "domainId": row.domain_id,
                "equipmentClassId": row.ontology_class_id,
                "equipmentClassLabel": label_map.get(
                    (str(row.domain_id), str(row.ontology_class_id)),
                    str(row.ontology_class_id),
                ),
                "anchorCount": int(row.anchor_count or 0),
            }
        )
    return grouped


def load_console_documents(language: str = "zh") -> dict[str, Any]:
    assets_payload = load_console_knowledge_assets(language=language)
    asset_index = {str(item["id"]): item for item in assets_payload["assets"]}
    linked_ids_by_doc = _console_linked_asset_ids_by_doc(assets_payload["assets"])
    db_documents = _load_documents_from_db()
    db = SessionLocal()
    try:
        prepare_targets_by_doc = _console_prepare_targets_by_doc(
            db,
            doc_ids=[str(item["doc_id"]) for item in db_documents],
            language=language,
        )
    finally:
        db.close()
    documents = []
    linked_assets_by_document: dict[str, list[dict[str, Any]]] = {}
    for item in db_documents:
        doc_id = str(item["doc_id"])
        linked_ids = linked_ids_by_doc.get(doc_id, [])
        asset_matches = [asset_index[asset_id] for asset_id in linked_ids if asset_id in asset_index]
        linked_assets_by_document[doc_id] = asset_matches
        prepare_targets = list(prepare_targets_by_doc.get(doc_id, []))
        if not prepare_targets:
            prepare_targets = [
                {
                    "domainId": str(asset["domainId"]),
                    "equipmentClassId": str(asset["equipmentClass"]),
                    "equipmentClassLabel": str(asset.get("equipmentClassLabel") or asset["equipmentClass"]),
                    "anchorCount": len(asset.get("evidence", [])),
                }
                for asset in asset_matches
            ]
        equipment_classes = sorted({target["equipmentClassId"] for target in prepare_targets})
        equipment_class_labels = sorted(
            {
                str(target["equipmentClassLabel"])
                for target in prepare_targets
            }
        )
        documents.append(
            {
                "id": doc_id,
                "fileName": item["file_name"],
                "domainId": item["source_domain"] or "hvac",
                "equipmentClasses": equipment_classes,
                "equipmentClassLabels": equipment_class_labels,
                "status": "chunked" if int(item.get("chunk_count") or 0) > 0 else "parsed" if item.get("parse_status") in {"completed", "parsed"} else "imported",
                "pageCount": int(item.get("page_count") or 0),
                "chunkCount": int(item.get("chunk_count") or 0),
                "importedAt": item.get("import_time") or "-",
                "sourceType": _console_source_type(item.get("file_name") or ""),
                "stageSummary": _console_stage_summary(item.get("parse_status"), int(item.get("chunk_count") or 0)),
                "stageTimeline": _console_stage_timeline(item.get("parse_status"), int(item.get("chunk_count") or 0)),
                "pageNotes": [],
                "chunkHighlights": [],
                "linkedAssetIds": linked_ids,
                "prepareTargets": prepare_targets,
            }
        )
    return {
        "documents": documents,
        "linkedAssetsByDocument": linked_assets_by_document,
    }


def _console_coverage_status(row: dict[str, Any]) -> str:
    covered = list(row.get("covered_knowledge_objects", []))
    missing = list(row.get("missing_knowledge_objects", []))
    if not covered:
        return "missing"
    if missing:
        return "partial"
    return "covered"


def load_console_domain_assets(language: str = "zh") -> dict[str, Any]:
    knowledge_assets = load_console_knowledge_assets(language=language)
    documents_payload = load_console_documents(language=language)
    document_index = {str(item["id"]): item for item in documents_payload["documents"]}
    assets_by_coverage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    documents_by_coverage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for asset in knowledge_assets["assets"]:
        coverage_id = f'{asset["domainId"]}__{asset["equipmentClass"]}'
        assets_by_coverage[coverage_id].append(asset)
        seen_docs = {doc["id"] for doc in documents_by_coverage[coverage_id]}
        for evidence in asset.get("evidence", []):
            doc_id = str(evidence.get("docId") or "")
            if doc_id in document_index and doc_id not in seen_docs:
                documents_by_coverage[coverage_id].append(document_index[doc_id])
                seen_docs.add(doc_id)

    coverage = []
    for path in sorted(DOMAIN_PACKAGES_DIR.glob("*/v2/package.yaml")):
        domain_id = path.parent.parent.name
        for row in _domain_workbench_payload(domain_id)["equipment_classes"]:
            coverage_id = f'{domain_id}__{row["equipment_class_id"]}'
            coverage.append(
                {
                    "id": coverage_id,
                    "label": row["label"],
                    "domainId": domain_id,
                    "status": _console_coverage_status(row),
                    "coveredTypes": list(row.get("covered_knowledge_objects", [])),
                    "missingTypes": list(row.get("missing_knowledge_objects", [])),
                    "assetCount": len(assets_by_coverage.get(coverage_id, [])),
                    "documentCount": len(documents_by_coverage.get(coverage_id, [])),
                    "updatedAt": "",
                    "summary": _console_localized_summary(
                        row.get("rationale") or row.get("notes") or "",
                        domain_id=domain_id,
                        equipment_label=row["label"],
                        covered_count=len(list(row.get("covered_knowledge_objects", []))),
                        missing_count=len(list(row.get("missing_knowledge_objects", []))),
                    ),
                    "relatedDocumentIds": [item["id"] for item in documents_by_coverage.get(coverage_id, [])],
                    "relatedAssetIds": [item["id"] for item in assets_by_coverage.get(coverage_id, [])],
                }
            )
    return {
        "coverage": coverage,
        "documentsByCoverage": documents_by_coverage,
        "assetsByCoverage": assets_by_coverage,
    }


def _console_pack_model(
    *,
    pack_file: str,
    domain_id: str | None,
    equipment_class_id: str | None,
    equipment_class_label: str,
    status: str | None,
    accepted_count: int,
    pending_count: int,
    rejected_count: int,
    workspace_id: str,
    name: str,
    detail: dict[str, Any] | None = None,
    pack_path: Path | None = None,
) -> dict[str, Any]:
    return {
        "id": pack_file,
        "name": name,
        "domainId": domain_id or "hvac",
        "equipmentClass": equipment_class_id or "",
        "equipmentClassLabel": equipment_class_label,
        "status": _console_pack_status(status),
        "updatedAt": _review_pack_updated_at(pack_path, detail) if pack_path else "",
        "candidateIds": _review_pack_candidate_ids(detail),
        "acceptedCount": int(accepted_count or 0),
        "pendingCount": int(pending_count or 0),
        "rejectedCount": int(rejected_count or 0),
        "workspaceId": workspace_id,
    }


def load_console_review_center(language: str = "zh") -> dict[str, Any]:
    workspace = load_review_workspace()
    if not workspace.get("available"):
        return {
            "workspaceId": workspace.get("workspace_id"),
            "packs": [],
            "candidates": [],
            "candidatesByPack": {},
        }
    knowledge_assets = load_console_knowledge_assets(language=language)
    asset_by_trace: dict[tuple[str, str, str], dict[str, Any]] = {}
    for asset in knowledge_assets.get("assets", []):
        for evidence in asset.get("evidence", []):
            trace_key = (
                str(evidence.get("docId") or ""),
                str(evidence.get("chunkId") or ""),
                str(asset.get("type") or ""),
            )
            if all(trace_key):
                asset_by_trace[trace_key] = asset
    active_workspace_id = str(workspace.get("workspace_id") or "default")
    root = Path(str(workspace.get("resolved_dir")))
    db = SessionLocal()
    try:
        ontology_label_map = _console_ontology_label_map(
            db,
            domain_ids=[
                str(item.get("domain_id"))
                for item in workspace.get("packs", [])
                if item.get("domain_id")
            ],
            language=language,
        )
    finally:
        db.close()
    candidates = []
    candidates_by_pack: dict[str, list[dict[str, Any]]] = {}
    packs = []
    for pack in workspace.get("packs", []):
        pack_path = root / pack["pack_file"]
        detail = _review_pack_detail(pack_path)
        equipment_class_label = ontology_label_map.get(
            (str(pack.get("domain_id")), str(pack.get("equipment_class_id"))),
            str(pack.get("equipment_class_id") or ""),
        )
        pack_candidates = []
        for entry in detail.get("candidate_entries", []):
            candidate_id = str(entry.get("candidate_id"))
            matched_asset = asset_by_trace.get(
                (
                    str(detail.get("doc_id") or ""),
                    str(entry.get("chunk_id") or ""),
                    str(entry.get("knowledge_object_type") or ""),
                )
            )
            title = str(entry.get("curation", {}).get("title") or "").strip()
            if not title:
                if matched_asset and matched_asset.get("title"):
                    title = str(matched_asset["title"])
            if not title:
                excerpt = str(entry.get("text_excerpt") or "")
                title = _compact_display_text(excerpt, limit=28) if _contains_cjk(excerpt) else str(entry.get("canonical_key_candidate") or "")
            summary = str(entry.get("curation", {}).get("summary") or "").strip()
            if not summary:
                if matched_asset and matched_asset.get("summary"):
                    summary = str(matched_asset["summary"])
            if not summary:
                fallback_text = str(entry.get("evidence_text") or entry.get("text_excerpt") or "")
                summary = _compact_display_text(fallback_text, limit=80)
            candidate = {
                "id": candidate_id,
                "packId": pack["pack_file"],
                "workspaceId": active_workspace_id,
                "title": title,
                "canonicalKey": entry.get("canonical_key_candidate"),
                "type": entry.get("knowledge_object_type"),
                "status": _console_review_status(entry.get("review_decision")),
                "pageNo": entry.get("page_no"),
                "chunkId": entry.get("chunk_id"),
                "summary": summary,
                "trustLevel": str(entry.get("curation", {}).get("trust_level") or "L3"),
                "payload": json.dumps(entry.get("curation", {}).get("structured_payload") or {}, ensure_ascii=False, indent=2),
                "evidence": {
                    "docId": detail.get("doc_id"),
                    "documentName": detail.get("doc_name"),
                    "pageNo": entry.get("page_no"),
                    "chunkId": entry.get("chunk_id"),
                    "excerpt": entry.get("text_excerpt") or "",
                    "evidenceText": entry.get("evidence_text") or "",
                },
                "compileMetadata": entry.get("compile_metadata") or {},
                "healthFindings": entry.get("health_findings") or [],
                "sourceDocument": detail.get("doc_name"),
            }
            candidates.append(candidate)
            pack_candidates.append(candidate)
        candidates_by_pack[pack["pack_file"]] = pack_candidates
        packs.append(
            _console_pack_model(
                pack_file=pack["pack_file"],
                domain_id=pack.get("domain_id"),
                equipment_class_id=pack.get("equipment_class_id"),
                equipment_class_label=equipment_class_label,
                status=pack.get("status"),
                accepted_count=int(pack.get("accepted_count") or 0),
                pending_count=int(pack.get("pending_count") or 0),
                rejected_count=int(pack.get("rejected_count") or 0),
                workspace_id=active_workspace_id,
                name=pack.get("doc_name") or pack["pack_file"],
                detail=detail,
                pack_path=pack_path,
            )
        )
    return {
        "workspaceId": active_workspace_id,
        "packs": packs,
        "candidates": candidates,
        "candidatesByPack": candidates_by_pack,
    }


def load_console_publish_records() -> dict[str, Any]:
    review_workspace = load_review_workspace()
    workspace_id = str(review_workspace.get("workspace_id") or "default")
    apply_workspace = load_apply_workspace(workspace_id)
    latest_apply = apply_workspace.get("latest_apply") or {}
    root = Path(str(review_workspace.get("resolved_dir"))) if review_workspace.get("resolved_dir") else None

    pack_lookup = {item["pack_file"]: item for item in review_workspace.get("packs", [])}
    db = SessionLocal()
    try:
        ontology_label_map = _console_ontology_label_map(
            db,
            domain_ids=[
                str(item.get("domain_id"))
                for item in review_workspace.get("packs", [])
                if item.get("domain_id")
            ],
        )
    finally:
        db.close()

    pack_details: dict[str, dict[str, Any]] = {}
    pack_models: dict[str, dict[str, Any]] = {}
    pack_labels: dict[str, str] = {}
    pack_paths: dict[str, Path] = {}
    for pack_file, pack_meta in pack_lookup.items():
        pack_path = root / pack_file if root else None
        detail = _review_pack_detail(pack_path) if pack_path and pack_path.exists() else None
        pack_details[pack_file] = detail or {}
        equipment_class_label = ontology_label_map.get(
            (str(pack_meta.get("domain_id")), str(pack_meta.get("equipment_class_id"))),
            str(pack_meta.get("equipment_class_id") or ""),
        )
        pack_labels[pack_file] = equipment_class_label
        if pack_path and pack_path.exists():
            pack_paths[pack_file] = pack_path
        pack_models[pack_file] = _console_pack_model(
            pack_file=pack_file,
            domain_id=pack_meta.get("domain_id"),
            equipment_class_id=pack_meta.get("equipment_class_id"),
            equipment_class_label=equipment_class_label,
            status=pack_meta.get("status"),
            accepted_count=int(pack_meta.get("accepted_count") or 0),
            pending_count=int(pack_meta.get("pending_count") or 0),
            rejected_count=int(pack_meta.get("rejected_count") or 0),
            workspace_id=workspace_id,
            name=pack_meta.get("doc_name") or pack_file,
            detail=detail,
            pack_path=pack_path,
        )

    linked_packs_by_record: dict[str, list[dict[str, Any]]] = {}
    records = []
    latest_record_id: str | None = None

    latest_apply_generated_at = str(latest_apply.get("generated_at") or "") or None
    apply_report = _load_optional_json(latest_apply.get("paths", {}).get("apply_report")) if latest_apply else None
    prepare_manifest = _load_optional_json(latest_apply.get("paths", {}).get("prepare_manifest")) if latest_apply else None
    if latest_apply and apply_report:
        record_id = _publish_run_record_id(workspace_id, latest_apply_generated_at)
        apply_results = list(apply_report.get("results", []))
        linked_pack_ids = [str(item.get("pack_file")) for item in apply_results if item.get("pack_file")]
        linked_packs_by_record[record_id] = [
            pack_models[pack_file]
            for pack_file in linked_pack_ids
            if pack_file in pack_models
        ]
        errors = [
            str(item.get("error"))
            for item in apply_results
            if item.get("status") == "failed" and item.get("error")
        ]
        items = []
        for item in apply_results:
            pack_file = str(item.get("pack_file") or "")
            pack_meta = pack_lookup.get(pack_file, {})
            fixture = _load_optional_fixture(item.get("fixture_path")) or _fixture_from_review_pack(pack_paths.get(pack_file))
            result_label = "success" if item.get("status") == "applied" else "failed"
            extra_note = None
            if item.get("status") == "applied":
                extra_note = "已写入知识库"
            elif item.get("error"):
                extra_note = f"发布失败：{item['error']}"
            if fixture and fixture.get("manual_entries"):
                items.extend(
                    _release_item_from_manual_entry(
                        entry,
                        pack_file=pack_file,
                        fixture=fixture,
                        equipment_class_label=pack_labels.get(pack_file, pack_meta.get("equipment_class_id") or ""),
                        result=result_label,
                        extra_note=extra_note,
                    )
                    for entry in fixture.get("manual_entries", [])
                )
            else:
                items.append(
                    _release_fallback_item(
                        pack_file=pack_file,
                        pack_name=pack_meta.get("doc_name") or pack_file,
                        result=result_label,
                        extra_note=extra_note or "未解析出知识对象明细",
                        pack_meta=pack_meta,
                        equipment_class_label=pack_labels.get(pack_file, pack_meta.get("equipment_class_id") or ""),
                    )
                )
        success_count = int(latest_apply.get("summary", {}).get("applied") or 0)
        failure_count = int(latest_apply.get("summary", {}).get("failed") or 0)
        records.append(
            {
                "id": record_id,
                "recordMode": "apply_run",
                "workspaceId": workspace_id,
                "executedAt": latest_apply_generated_at or "",
                "domainId": (prepare_manifest or {}).get("domain_id") or next(
                    (pack.get("domainId") for pack in linked_packs_by_record[record_id]),
                    "hvac",
                ),
                "status": _console_release_status_from_counts(success_count, failure_count),
                "successCount": success_count,
                "failureCount": failure_count,
                "workspace": workspace_id,
                "operator": "-",
                "summary": f"已执行发布，成功应用 {success_count} 个审阅包，失败 {failure_count} 个。",
                "detailsText": latest_apply.get("summary_text"),
                "artifactPaths": latest_apply.get("paths", {}),
                "items": items,
                "errors": errors,
                "linkedPackIds": linked_pack_ids,
            }
        )
        latest_record_id = record_id
    else:
        preview_id = _publish_preview_record_id(workspace_id)
        readiness_results = list(apply_workspace.get("results", []))
        linked_pack_ids = [str(item.get("pack_file")) for item in readiness_results if item.get("pack_file")]
        linked_packs_by_record[preview_id] = [
            pack_models[pack_file]
            for pack_file in linked_pack_ids
            if pack_file in pack_models
        ]
        ready_count = int(apply_workspace.get("summary", {}).get("ready") or 0)
        blocked_count = sum(
            int(apply_workspace.get("summary", {}).get(key) or 0)
            for key in ["blocked_pending", "blocked_no_accepted", "blocked_invalid"]
        )
        errors = []
        items = []
        for item in readiness_results:
            pack_file = str(item.get("pack_file") or "")
            blocker = _console_release_note_blocker(item.get("blocker"))
            if blocker:
                errors.append(f"{pack_file}: {blocker}")
            fixture = _fixture_from_review_pack(pack_paths.get(pack_file))
            result_label = "success" if item.get("status") == "ready" else "failed"
            extra_note = "；".join(
                part
                for part in [
                    f"状态 {item.get('status')}",
                    blocker,
                ]
                if part
            ) or None
            if fixture and fixture.get("manual_entries"):
                items.extend(
                    _release_item_from_manual_entry(
                        entry,
                        pack_file=pack_file,
                        fixture=fixture,
                        equipment_class_label=pack_labels.get(pack_file, item.get("equipment_class_id") or ""),
                        result=result_label,
                        extra_note=extra_note,
                    )
                    for entry in fixture.get("manual_entries", [])
                )
            else:
                items.append(
                    _release_fallback_item(
                        pack_file=pack_file,
                        pack_name=item.get("doc_name") or pack_file,
                        result=result_label,
                        extra_note="；".join(
                            part
                            for part in [
                                f"接受 {int(item.get('accepted_count') or 0)} / 拒绝 {int(item.get('rejected_count') or 0)} / 待处理 {int(item.get('pending_count') or 0)}",
                                extra_note,
                            ]
                            if part
                        ),
                        pack_meta=pack_lookup.get(pack_file, {}),
                        equipment_class_label=pack_labels.get(pack_file, item.get("equipment_class_id") or ""),
                    )
                )
        _, workspace_dir = _resolve_workspace_dir(workspace_id)
        prepare_manifest_path = workspace_dir / "prepare_manifest.json"
        prepare_payload = _load_optional_json(prepare_manifest_path)
        records.append(
            {
                "id": preview_id,
                "recordMode": "workspace_snapshot",
                "workspaceId": workspace_id,
                "executedAt": str((prepare_payload or {}).get("generated_at") or ""),
                "domainId": (prepare_payload or {}).get("domain_id") or next(
                    (pack.get("domainId") for pack in linked_packs_by_record[preview_id]),
                    "hvac",
                ),
                "status": _console_release_status_from_counts(ready_count, blocked_count),
                "successCount": ready_count,
                "failureCount": blocked_count,
                "workspace": workspace_id,
                "operator": "-",
                "summary": f"当前工作区有 {ready_count} 个审阅包可发布，{blocked_count} 个审阅包仍未就绪。",
                "detailsText": None,
                "artifactPaths": (prepare_payload or {}).get("paths", {}),
                "items": items,
                "errors": errors,
                "linkedPackIds": linked_pack_ids,
            }
        )
        latest_record_id = preview_id
    return {
        "workspaceId": workspace_id,
        "latestRecordId": latest_record_id,
        "records": records,
        "linkedPacksByRecord": linked_packs_by_record,
    }


def _summaries(
    domains: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    fixture_samples: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "domain_count": len(domains),
        "document_count": len(documents),
        "fixture_count": len(fixture_samples),
        "covered_equipment_classes": sum(item["covered_equipment_classes"] for item in domains),
        "uncovered_equipment_classes": sum(item["uncovered_equipment_classes"] for item in domains),
        "priority_target_count": sum(len(item["priority_queue"]) for item in domains),
    }


def _inbox_cards(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for domain in domains:
        for item in domain["priority_queue"][:2]:
            cards.append(
                {
                    "domain_id": domain["domain_id"],
                    "equipment_class_id": item["equipment_class_id"],
                    "target_knowledge_objects": item["target_knowledge_objects"],
                    "rationale": item["rationale"],
                }
            )
    return cards[:4]


def _coverage_watch(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    watch = []
    for domain in domains:
        watch.append(
            {
                "domain_id": domain["domain_id"],
                "domain_name": domain["domain_name"],
                "covered_equipment_classes": domain["covered_equipment_classes"],
                "uncovered_equipment_classes": domain["uncovered_equipment_classes"],
                "supported_knowledge_objects": domain["supported_knowledge_objects"],
            }
        )
    return watch


def _demo_summary() -> dict[str, Any]:
    try:
        bundle = load_demo_bundle()
    except FileNotFoundError:
        return {"available": False}
    return {
        "available": True,
        "overall_status": bundle.get("statuses", {}).get("overall"),
        "generated_at": bundle.get("generated_at"),
        "scenario": bundle.get("scenario"),
        "paths": bundle.get("paths", {}),
        "counts": bundle.get("counts", {}),
    }


def _workspace_root(base_dir: Path = WORKBENCH_REVIEW_ROOT) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _is_legacy_workspace(base_dir: Path) -> bool:
    if (base_dir / "prepare_manifest.json").exists():
        return True
    if (base_dir / "apply_ready_manifest.json").exists():
        return True
    return bool(_valid_review_pack_paths(base_dir))


def _workspace_ids(base_dir: Path = WORKBENCH_REVIEW_ROOT) -> list[str]:
    root = _workspace_root(base_dir)
    ids: list[str] = []
    if _is_legacy_workspace(root):
        ids.append("default")
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if (path / "prepare_manifest.json").exists() or (path / "apply_ready_manifest.json").exists():
            ids.append(path.name)
    return ids


def _resolve_workspace_dir(
    workspace_id: str | None = None,
    *,
    base_dir: Path = WORKBENCH_REVIEW_ROOT,
    create: bool = False,
) -> tuple[str, Path]:
    root = _workspace_root(base_dir)
    ids = _workspace_ids(root)
    if workspace_id == "default" and _is_legacy_workspace(root):
        return "default", root
    if workspace_id:
        target = root / workspace_id
        if create:
            target.mkdir(parents=True, exist_ok=True)
        return workspace_id, target
    if ids:
        chosen = ids[-1]
        if chosen == "default":
            return "default", root
        return chosen, root / chosen
    target = root / "default"
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return "default", target


def _workspace_info(workspace_id: str, path: Path) -> dict[str, Any]:
    manifest_path = path / "prepare_manifest.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    return {
        "workspace_id": workspace_id,
        "path": str(path),
        "domain_id": manifest.get("domain_id"),
        "generated_at": manifest.get("generated_at"),
        "doc_id": manifest.get("filters_applied", {}).get("doc_id"),
        "equipment_class_id": manifest.get("filters_applied", {}).get("equipment_class_id"),
    }


def _workspace_pack_dir(workspace_dir: Path) -> Path:
    manifest_path = workspace_dir / "prepare_manifest.json"
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
        bootstrapped = manifest.get("paths", {}).get("bootstrapped_review_pack_dir")
        if bootstrapped:
            target = Path(bootstrapped)
            if target.exists():
                return target
    return workspace_dir


def _review_status_from_counts(inspection: dict[str, Any]) -> str:
    if inspection.get("pending_count", 0) > 0:
        return "blocked_pending"
    if inspection.get("accepted_count", 0) == 0:
        return "blocked_no_accepted"
    return "review_complete"


def _review_pack_summary(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    inspection = inspect_review_pack(payload)
    equipment = payload.get("equipment_class", {})
    return {
        "pack_file": path.name,
        "pack_path": str(path),
        "doc_id": payload.get("doc_id"),
        "doc_name": payload.get("doc_name"),
        "domain_id": payload.get("domain_id"),
        "equipment_class_id": equipment.get("equipment_class_id"),
        "equipment_class_key": equipment.get("equipment_class_key"),
        "candidate_count": inspection["candidate_count"],
        "accepted_count": inspection["accepted_count"],
        "rejected_count": inspection["rejected_count"],
        "pending_count": inspection["pending_count"],
        "status": _review_status_from_counts(inspection),
    }


def _review_pack_detail(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    inspection = inspect_review_pack(payload)
    payload["review_summary"] = {
        **inspection,
        "status": _review_status_from_counts(inspection),
    }
    return payload


def _valid_review_pack_paths(root: Path) -> list[Path]:
    paths = []
    for path in discover_review_pack_paths(root):
        try:
            payload = _load_json(path)
        except Exception:
            continue
        if payload.get("review_mode") == "chunk_backfill_review_pack":
            paths.append(path)
    return paths


def _validate_review_pack_payload(existing_path: Path, payload: dict[str, Any]) -> None:
    if payload.get("review_mode") != "chunk_backfill_review_pack":
        raise ValueError("Payload is not a review pack")
    entries = payload.get("candidate_entries")
    if not isinstance(entries, list):
        raise ValueError("Review pack must contain candidate_entries")
    existing = _load_json(existing_path)
    inspect_review_pack(payload)
    if payload.get("doc_id") != existing.get("doc_id"):
        raise ValueError("Review pack doc_id is immutable")
    if payload.get("domain_id") != existing.get("domain_id"):
        raise ValueError("Review pack domain_id is immutable")
    expected_equipment = existing.get("equipment_class", {}).get("equipment_class_id")
    actual_equipment = payload.get("equipment_class", {}).get("equipment_class_id")
    if actual_equipment != expected_equipment:
        raise ValueError("Review pack equipment_class_id is immutable")
    existing_candidates = {
        str(entry.get("candidate_id")) for entry in existing.get("candidate_entries", [])
    }
    payload_candidates = {
        str(entry.get("candidate_id")) for entry in entries
    }
    if payload_candidates != existing_candidates:
        raise ValueError("Review pack candidate set must not change")
    for entry in entries:
        if not isinstance(entry.get("candidate_id"), str) or not entry["candidate_id"]:
            raise ValueError("Each review entry must keep a stable candidate_id")
        curation = entry.get("curation")
        if curation is not None and not isinstance(curation, dict):
            raise ValueError("Each review entry curation block must be an object")
        if entry.get("review_decision") == "accepted":
            if not isinstance(curation, dict):
                raise ValueError(f"Accepted entry {entry['candidate_id']} requires a curation block")
            if not isinstance(curation.get("structured_payload"), dict):
                raise ValueError(f"Accepted entry {entry['candidate_id']} requires structured_payload")
            if not isinstance(curation.get("applicability"), dict):
                raise ValueError(f"Accepted entry {entry['candidate_id']} requires applicability")
            if not isinstance(curation.get("title"), str) or not curation["title"].strip():
                raise ValueError(f"Accepted entry {entry['candidate_id']} requires a non-empty title")
            if not isinstance(curation.get("summary"), str) or not curation["summary"].strip():
                raise ValueError(f"Accepted entry {entry['candidate_id']} requires a non-empty summary")


def load_review_workspace(
    workspace_id: str | None = None,
    *,
    review_root: Path = WORKBENCH_REVIEW_ROOT,
) -> dict[str, Any]:
    base_dir = _workspace_root(Path(review_root))
    active_workspace_id, workspace_dir = _resolve_workspace_dir(workspace_id, base_dir=base_dir)
    root = _workspace_pack_dir(workspace_dir)
    workspaces = [
        _workspace_info(item, base_dir if item == "default" and _is_legacy_workspace(base_dir) else base_dir / item)
        for item in _workspace_ids(base_dir)
    ]
    if not root.exists():
        return {
            "configured_dir": str(base_dir),
            "resolved_dir": str(root),
            "available": False,
            "workspace_id": active_workspace_id,
            "workspaces": workspaces,
            "pack_count": 0,
            "packs": [],
        }
    packs = [_review_pack_summary(path) for path in _valid_review_pack_paths(root)]
    return {
        "configured_dir": str(base_dir),
        "resolved_dir": str(root),
        "available": True,
        "workspace_id": active_workspace_id,
        "workspaces": workspaces,
        "pack_count": len(packs),
        "packs": packs,
    }


def save_review_pack(
    workspace_id: str | None,
    pack_file: str,
    payload: dict[str, Any],
    *,
    review_root: Path = WORKBENCH_REVIEW_ROOT,
) -> dict[str, Any]:
    active_workspace_id, workspace_dir = _resolve_workspace_dir(workspace_id, base_dir=Path(review_root))
    target = _workspace_pack_dir(workspace_dir) / pack_file
    if not target.exists():
        raise FileNotFoundError(f"Review pack not found: {target}")
    _validate_review_pack_payload(target, payload)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    target.write_text(rendered, encoding="utf-8")
    detail = _review_pack_detail(target)
    detail["workspace_id"] = active_workspace_id
    return detail


def bootstrap_review_pack(
    workspace_id: str | None,
    pack_file: str,
    *,
    review_root: Path = WORKBENCH_REVIEW_ROOT,
) -> dict[str, Any]:
    active_workspace_id, workspace_dir = _resolve_workspace_dir(workspace_id, base_dir=Path(review_root))
    target = _workspace_pack_dir(workspace_dir) / pack_file
    if not target.exists():
        raise FileNotFoundError(f"Review pack not found: {target}")
    payload = bootstrap_review_pack_file(target, default_trust_level="L3")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    detail = _review_pack_detail(target)
    detail["workspace_id"] = active_workspace_id
    return detail


def _latest_apply_result(workspace_dir: Path) -> dict[str, Any] | None:
    manifest_path = workspace_dir / "apply_ready_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = _load_json(manifest_path)
    stats = _load_optional_json(manifest.get("paths", {}).get("stats"))
    summary_path = _resolve_artifact_path(manifest.get("paths", {}).get("summary_text"))
    summary_text = _load_optional_text(summary_path) if summary_path and summary_path.exists() else None
    return {
        "generated_at": manifest.get("generated_at"),
        "ready_pack_count": manifest.get("ready_pack_count"),
        "summary": manifest.get("summary", {}),
        "paths": manifest.get("paths", {}),
        "stats": stats,
        "summary_text": summary_text,
    }


def load_apply_workspace(
    workspace_id: str | None = None,
    *,
    review_root: Path = WORKBENCH_REVIEW_ROOT,
) -> dict[str, Any]:
    base_dir = _workspace_root(Path(review_root))
    active_workspace_id, workspace_dir = _resolve_workspace_dir(workspace_id, base_dir=base_dir)
    root = _workspace_pack_dir(workspace_dir)
    workspaces = [
        _workspace_info(item, base_dir if item == "default" and _is_legacy_workspace(base_dir) else base_dir / item)
        for item in _workspace_ids(base_dir)
    ]
    if not root.exists():
        return {
            "configured_dir": str(base_dir),
            "resolved_dir": str(root),
            "available": False,
            "workspace_id": active_workspace_id,
            "workspaces": workspaces,
            "summary": {"ready": 0, "blocked_pending": 0, "blocked_no_accepted": 0, "blocked_invalid": 0},
            "results": [],
            "report_path": None,
            "can_apply_bundle": (workspace_dir / "prepare_manifest.json").exists(),
            "latest_apply": _latest_apply_result(workspace_dir),
        }
    pack_paths = _valid_review_pack_paths(root)
    results = [assess_review_pack_readiness(path) for path in pack_paths]
    summary = {
        "ready": sum(1 for item in results if item["status"] == "ready"),
        "blocked_pending": sum(1 for item in results if item["status"] == "blocked_pending"),
        "blocked_no_accepted": sum(1 for item in results if item["status"] == "blocked_no_accepted"),
        "blocked_invalid": sum(1 for item in results if item["status"] == "blocked_invalid"),
    }
    return {
        "configured_dir": str(base_dir),
        "resolved_dir": str(root),
        "available": True,
        "workspace_id": active_workspace_id,
        "workspaces": workspaces,
        "summary": summary,
        "results": results,
        "report_path": None,
        "can_apply_bundle": (workspace_dir / "prepare_manifest.json").exists(),
        "latest_apply": _latest_apply_result(workspace_dir),
    }


def run_apply_ready(
    workspace_id: str | None,
    *,
    review_root: Path = WORKBENCH_REVIEW_ROOT,
) -> dict[str, Any]:
    active_workspace_id, workspace_dir = _resolve_workspace_dir(workspace_id, base_dir=Path(review_root))
    manifest_path = workspace_dir / "prepare_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Prepare manifest not found: {manifest_path}")
    result = apply_ready_review_bundle(workspace_dir, prepare_manifest_path=manifest_path)
    result["workspace_id"] = active_workspace_id
    result["publish_record_id"] = _publish_run_record_id(active_workspace_id, result.get("generated_at"))
    result["readiness"] = load_apply_workspace(active_workspace_id, review_root=review_root)
    return result


def run_prepare_bundle(
    domain_id: str,
    *,
    doc_id: str | None,
    equipment_class_id: str | None,
    workspace_id: str | None = None,
    llm_backend_config_path: str | None = None,
    llm_backend_name: str | None = None,
    enable_llm: bool = True,
    llm_types: tuple[str, ...] | list[str] | None = None,
    review_root: Path = WORKBENCH_REVIEW_ROOT,
) -> dict[str, Any]:
    root = _workspace_root(Path(review_root))
    resolved_workspace_id = workspace_id or _workspace_id(domain_id, doc_id, equipment_class_id)
    _, base_dir = _resolve_workspace_dir(resolved_workspace_id, base_dir=root, create=True)
    manifest = prepare_review_pipeline_bundle(
        domain_id,
        base_dir,
        doc_id=doc_id,
        equipment_class_id=equipment_class_id,
        default_trust_level="L3",
        llm_backend_config_path=llm_backend_config_path,
        llm_backend_name=llm_backend_name,
        enable_llm=enable_llm,
        llm_enabled_types=llm_types,
    )
    return {
        "workspace_id": resolved_workspace_id,
        "prepare_manifest": manifest,
        "compiler": manifest.get("compiler", {}),
        "review_workspace": load_review_workspace(resolved_workspace_id, review_root=review_root),
        "apply_workspace": load_apply_workspace(resolved_workspace_id, review_root=review_root),
    }


def load_workbench_payload() -> dict[str, Any]:
    domains = [
        _domain_workbench_payload(path.parent.parent.name)
        for path in sorted(DOMAIN_PACKAGES_DIR.glob("*/v2/package.yaml"))
    ]
    document_catalog = _load_document_catalog()
    return {
        "title": "KnowFabric 知识工程工作台",
        "subtitle": "面向知识工程团队的内部工作台，聚焦文档录入、候选审阅、应用执行与覆盖盘点。",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "navigation": NAV_ITEMS,
        "summary": _summaries(domains, document_catalog["documents"], document_catalog["fixture_samples"]),
        "views": {
            "inbox": {
                "cards": _inbox_cards(domains),
                "rules": [
                    "优先补能形成闭环的设备类，而不是平均撒开。",
                    "先看证据与 Chunk，再决定审阅字段。",
                    "能用 apply-ready 走通的流程，优先不要回退到手写样例。"
                ],
            },
            "documents": {
                **document_catalog,
            },
            "review": {
                "workflow_steps": REVIEW_STEPS,
                "command_shortcuts": COMMAND_SHORTCUTS,
                "compiler_defaults": {
                    "default_enabled_types": list(default_enabled_llm_types()),
                    "backend_config_path": settings.llm_backend_config_path,
                    "backend_name": settings.llm_backend_name,
                },
                "supported_types": sorted(
                    {
                        knowledge_type
                        for domain in domains
                        for knowledge_type in domain["supported_knowledge_objects"]
                    }
                ),
                "focus_targets": _inbox_cards(domains),
                "workspace": load_review_workspace(),
            },
            "apply": {
                "rules": APPLY_RULES,
                "command_shortcuts": COMMAND_SHORTCUTS,
                "coverage_watch": _coverage_watch(domains),
                "workspace": load_apply_workspace(),
            },
            "coverage": {
                "domains": domains,
            },
            "demo": _demo_summary(),
        },
    }


app = FastAPI(title="KnowFabric Admin Web", version="0.2.0")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "service": "admin-web"}


@app.get("/api/demo-bundle")
async def get_demo_bundle() -> dict[str, Any]:
    try:
        return {"success": True, "data": load_demo_bundle()}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/workbench")
async def get_workbench() -> dict[str, Any]:
    return {"success": True, "data": load_workbench_payload()}


@app.get("/api/console/knowledge-assets")
async def get_console_knowledge_assets() -> dict[str, Any]:
    try:
        return {"success": True, "data": load_console_knowledge_assets()}
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Knowledge asset tables are not ready. Run migrations and semantic data bootstrap first.",
        ) from exc


@app.get("/api/console/documents")
async def get_console_documents() -> dict[str, Any]:
    try:
        return {"success": True, "data": load_console_documents()}
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Document tables are not ready. Run migrations and document bootstrap first.",
        ) from exc


@app.get("/api/console/domain-assets")
async def get_console_domain_assets() -> dict[str, Any]:
    try:
        return {"success": True, "data": load_console_domain_assets()}
    except OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail="Domain asset data is not ready. Run migrations and semantic bootstrap first.",
        ) from exc


@app.get("/api/console/review-center")
async def get_console_review_center() -> dict[str, Any]:
    return {"success": True, "data": load_console_review_center()}


@app.get("/api/console/publish-records")
async def get_console_publish_records() -> dict[str, Any]:
    return {"success": True, "data": load_console_publish_records()}


@app.post("/api/workbench/documents/import")
async def post_import_document(
    file: UploadFile = File(...),
    source_domain: str | None = Form(default=None),
) -> dict[str, Any]:
    try:
        document = await _import_uploaded_document(file, source_domain)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": document}


@app.post("/api/workbench/documents/{doc_id}/parse")
async def post_parse_document(doc_id: str) -> dict[str, Any]:
    try:
        result = _run_document_parse(doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "data": result}


@app.post("/api/workbench/documents/{doc_id}/chunk")
async def post_chunk_document(doc_id: str) -> dict[str, Any]:
    try:
        result = _run_document_chunk(doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"success": True, "data": result}


@app.get("/api/workbench/review-packs")
async def get_review_packs(workspace_id: str | None = None) -> dict[str, Any]:
    return {"success": True, "data": load_review_workspace(workspace_id)}


@app.get("/api/workbench/review-packs/{pack_file}")
async def get_review_pack(pack_file: str, workspace_id: str | None = None) -> dict[str, Any]:
    active_workspace_id, workspace_dir = _resolve_workspace_dir(workspace_id)
    target = _workspace_pack_dir(workspace_dir) / pack_file
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Review pack not found: {pack_file}")
    detail = _review_pack_detail(target)
    detail["workspace_id"] = active_workspace_id
    return {"success": True, "data": detail}


@app.put("/api/workbench/review-packs/{pack_file}")
async def put_review_pack(
    pack_file: str,
    workspace_id: str | None = None,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    try:
        active_workspace_id = workspace_id or payload.get("workspace_id")
        saved = save_review_pack(active_workspace_id, pack_file, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": saved}


@app.post("/api/workbench/review-packs/{pack_file}/bootstrap")
async def post_bootstrap_review_pack(pack_file: str, workspace_id: str | None = None) -> dict[str, Any]:
    try:
        bootstrapped = bootstrap_review_pack(workspace_id, pack_file)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": bootstrapped}


@app.get("/api/workbench/apply")
async def get_apply_workspace(workspace_id: str | None = None) -> dict[str, Any]:
    return {"success": True, "data": load_apply_workspace(workspace_id)}


@app.post("/api/workbench/apply/run")
async def post_apply_ready(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    try:
        active_workspace_id = payload.get("workspace_id")
        result = run_apply_ready(active_workspace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": result}


@app.post("/api/workbench/review-bundle/prepare")
async def post_prepare_review_bundle(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        llm_types = payload.get("llm_types")
        normalized_llm_types = tuple(str(item) for item in llm_types) if isinstance(llm_types, list) else None
        result = run_prepare_bundle(
            str(payload.get("domain_id") or ""),
            doc_id=payload.get("doc_id"),
            equipment_class_id=payload.get("equipment_class_id"),
            workspace_id=payload.get("workspace_id"),
            llm_backend_config_path=payload.get("llm_backend_config_path"),
            llm_backend_name=payload.get("llm_backend_name"),
            enable_llm=bool(payload.get("enable_llm", True)),
            llm_types=normalized_llm_types,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": result}


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/favicon.ico")
async def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


app.mount("/artifacts", StaticFiles(directory=ARTIFACT_DIR, check_dir=False), name="artifacts")
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=ADMIN_WEB_HOST,
        port=ADMIN_WEB_PORT,
        reload=True,
    )
