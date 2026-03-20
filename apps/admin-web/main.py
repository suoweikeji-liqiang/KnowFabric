"""Read-only evaluation shell for KnowFabric demo artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


ROOT_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"
ARTIFACT_DIR = Path(os.environ.get("DEMO_ARTIFACT_DIR", ROOT_DIR / "output" / "demo"))
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        return "passed" if report.get("initialize_ok") and report.get("tools_list_ok") and summary.get("failed", 0) == 0 else "failed"
    if surface == "api":
        return "passed" if report.get("health", {}).get("status") == "passed" and summary.get("failed", 0) == 0 else "failed"
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
    queries = []
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
    hvac_queries = hvac["queries"] if hvac else []
    grouped = _query_groups_by_equipment(hvac_queries)
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
                "summary": "作为冷站控制外围能力，当前还可展示变频驱动故障、参数与接线指导。",
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


app = FastAPI(title="KnowFabric Admin Web", version="0.1.0")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "service": "admin-web"}


@app.get("/api/demo-bundle")
async def get_demo_bundle() -> dict[str, Any]:
    try:
        return {"success": True, "data": load_demo_bundle()}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
