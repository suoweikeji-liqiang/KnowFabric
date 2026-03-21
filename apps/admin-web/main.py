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
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.exc import OperationalError


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.db.models import ContentChunk, Document, DocumentPage
from packages.db.session import SessionLocal
from packages.domain_kit_v2.loader import load_domain_package_v2
from packages.chunking.service import ChunkingService
from packages.core.config import settings
from packages.ingest.service import IngestService
from packages.parser.service import ParserService
from packages.storage.manager import StorageManager
from scripts.apply_review_packs_batch import discover_review_pack_paths, inspect_review_pack
from scripts.apply_ready_review_bundle import apply_ready_review_bundle
from scripts.bootstrap_review_pack_curation import bootstrap_review_pack_file
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
    {"id": "inbox", "label": "Inbox", "description": "今日优先级"},
    {"id": "documents", "label": "Documents", "description": "录入与资料面板"},
    {"id": "review", "label": "Review", "description": "候选审阅与校准"},
    {"id": "apply", "label": "Apply", "description": "准备度与应用"},
    {"id": "coverage", "label": "Coverage", "description": "覆盖盘点"},
    {"id": "demo", "label": "Demo", "description": "演示与交付产物"},
]
COMMAND_SHORTCUTS = [
    {
        "label": "Prepare Review Bundle",
        "command": "python3 scripts/prepare_review_pipeline_bundle.py <domain> review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id>",
        "purpose": "从已有 chunk 直接准备可审阅 bundle。",
    },
    {
        "label": "Apply Ready Bundle",
        "command": "python3 scripts/apply_ready_review_bundle.py review_bundle",
        "purpose": "批量应用已完成审阅的 pack。",
    },
    {
        "label": "Checks",
        "command": "bash scripts/check-all",
        "purpose": "在结束会话前跑绑定质量门。",
    },
]
REVIEW_STEPS = [
    "导入文档并确认 domain 与 equipment class。",
    "生成 chunk-backed candidate 或 review bundle。",
    "并排查看 chunk、evidence 与 curation 字段。",
    "接受、拒绝或保留 pending，再应用 ready pack。",
]
APPLY_RULES = [
    "只有 ready 的 pack 可以进入 apply。",
    "apply 前必须保留 doc / page / chunk 追溯链。",
    "ontology class 与 knowledge object 必须同域对齐。",
    "apply 后优先回查 API/MCP 读面，而不是只看文件写入。",
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
    labels = {"hvac": "HVAC", "drive": "变频驱动"}
    queries: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    report_urls: dict[str, str | None] = {}
    for surface, report in sorted(reports.items()):
        statuses[surface] = _surface_status(report, surface)
        report_urls[surface] = _artifact_url(report.get("_path"))
        queries.extend(_normalize_query_item(item, surface) for item in report.get("results", []))
    return {
        "domain_id": domain_id,
        "label": labels.get(domain_id, domain_id),
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
                "label": item.label.get("en") or item.id,
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
        "domain_name": bundle.package.domain_name,
        "supported_knowledge_objects": bundle.package.supported_knowledge_objects,
        "covered_equipment_classes": covered,
        "uncovered_equipment_classes": uncovered,
        "priority_queue": inventory.get("internal_priority_queue", []),
        "equipment_classes": rows,
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
        if (path / "prepare_manifest.json").exists() or _valid_review_pack_paths(path):
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
    stats_path = Path(manifest.get("paths", {}).get("stats", ""))
    summary_path = Path(manifest.get("paths", {}).get("summary_text", ""))
    stats = _load_json(stats_path) if stats_path.exists() else None
    summary_text = _load_optional_text(summary_path)
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
    result["readiness"] = load_apply_workspace(active_workspace_id, review_root=review_root)
    return result


def run_prepare_bundle(
    domain_id: str,
    *,
    doc_id: str | None,
    equipment_class_id: str | None,
    workspace_id: str | None = None,
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
    )
    return {
        "workspace_id": resolved_workspace_id,
        "prepare_manifest": manifest,
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
        "title": "KnowFabric Internal Workbench",
        "subtitle": "面向知识工程团队的内部工作台：聚焦文档导入、候选审阅、apply 和覆盖盘点。",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "navigation": NAV_ITEMS,
        "summary": _summaries(domains, document_catalog["documents"], document_catalog["fixture_samples"]),
        "views": {
            "inbox": {
                "cards": _inbox_cards(domains),
                "rules": [
                    "优先补能形成闭环的 equipment class，而不是平均撒开。",
                    "先看 evidence 与 chunk，再决定 curation 字段。",
                    "能用 apply-ready 走通的流程，优先不要回退到手写 fixture。"
                ],
            },
            "documents": {
                **document_catalog,
            },
            "review": {
                "workflow_steps": REVIEW_STEPS,
                "command_shortcuts": COMMAND_SHORTCUTS,
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
        result = run_prepare_bundle(
            str(payload.get("domain_id") or ""),
            doc_id=payload.get("doc_id"),
            equipment_class_id=payload.get("equipment_class_id"),
            workspace_id=payload.get("workspace_id"),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": True, "data": result}


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


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
