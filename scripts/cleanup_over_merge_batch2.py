#!/usr/bin/env python3
"""Split true over-merge KOs from the human audit batch 2."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.cross_source_merger import assert_valid_ko_identity
from packages.compiler.llm_compiler import _slugify_part
from packages.db.session import SessionLocal


REJECT_OLD_IDS = {
    "ko_0003dc96ea6cfa09": "evidence_all_unrelated",
    "ko_0a5634c7d18e0843": "evidence_all_startup_or_runtime_not_shutdown",
}

STATE_ONLY = {
    "ko_2ba76711e02b5977": "value_disagreement",
}


@dataclass(frozen=True)
class SplitGroup:
    key: str
    title: str
    suffix: str
    reason: str
    review_status: str = "published"
    consensus_state: str | None = None


def _contains(text: str, *needles: str) -> bool:
    return any(needle.lower() in text.lower() for needle in needles)


def _fc_number(text: str) -> str | None:
    match = re.search(r"\bFC\s*#?\s*(\d+)\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _refrigerant_key(text: str, *, page_no: str | int = "") -> str | None:
    compact = text.replace("-", "").replace(" ", "").lower()
    if "r407c" in compact:
        return "r407c"
    if "r134a" in compact:
        return "r134a"
    if "r22" in compact:
        return "r22"
    if "refrigerant600a" in compact or "600a" in compact or "isobutane" in compact:
        return "r600a"
    if "refrigerant732" in compact or "oxygen" in compact:
        return "r732"
    if "refrigerant740" in compact or "argon" in compact:
        return "r740"
    if str(page_no) == "861":
        return "r134a"
    return None


def _classify_pressure_and_fault(old_ko_id: str, text: str) -> SplitGroup | None:
    if old_ko_id in {"ko_0375092c506a85d8", "ko_4a7e489f00e85fa8"}:
        if "低压" in text:
            return SplitGroup("low_pressure_cutout", "低压断开", "low_pressure_cutout", "polarity: low pressure")
        return SplitGroup("high_pressure_cutout", "高压断开", "high_pressure_cutout", "polarity: high pressure")

    if old_ko_id == "ko_2cb2a95fb07241cc":
        if "水侧" in text:
            return SplitGroup("water_side_pressure", "水侧最大允许压力", "water_side_pressure", "subsystem: water side")
        return SplitGroup("refrigerant_side_pressure", "冷媒侧最大允许压力", "refrigerant_side_pressure", "subsystem: refrigerant side")

    if old_ko_id in {"ko_0aa1d7491394e13d", "ko_0d80e765f6b64a5c", "ko_497eb8d85aae2821"}:
        number = _fc_number(text) or "unknown"
        title_prefix = {
            "ko_0aa1d7491394e13d": "AFDD Fault Condition",
            "ko_0d80e765f6b64a5c": "HW Plant",
            "ko_497eb8d85aae2821": "AFDD",
        }[old_ko_id]
        return SplitGroup(f"fc_{number}", f"{title_prefix} FC#{number}", f"fc_{number}", "fault_code number")
    return None


def _classify_concept_pair(old_ko_id: str, text: str) -> SplitGroup | None:
    if old_ko_id == "ko_05b9aebdde71d566":
        if "滑阀" in text:
            return SplitGroup("slide_valve_trigger", "滑阀位置触发", "slide_valve_trigger", "different concept: slide valve")
        return SplitGroup("discharge_pressure_limit", "排气压力限定值", "discharge_pressure_limit", "different concept: discharge pressure")

    if old_ko_id == "ko_2108bb796ebd7b19":
        if "干燥过滤器" in text:
            return SplitGroup("filter_drier_service", "干燥过滤器拆装", "filter_drier_service", "different component: filter drier")
        return SplitGroup("compressor_disassembly", "压缩机拆卸步骤", "compressor_disassembly", "different component: compressor")

    if old_ko_id == "ko_899d764444a01370":
        if "保持" in text:
            return SplitGroup("hold_current_limit", "1# 压缩机电流限定值(保持)", "hold_current_limit", "mode: hold")
        return SplitGroup("unload_current_limit", "1# 压缩机电流限定值(卸载)", "unload_current_limit", "mode: unload")

    if old_ko_id == "ko_178654fc424a0af4":
        if "制热" in text:
            return SplitGroup("heating_rated_power", "制热额定总输入功率", "heating_rated_power", "heating vs cooling")
        return SplitGroup("cooling_rated_power", "制冷额定总输入功率", "cooling_rated_power", "heating vs cooling")

    if old_ko_id == "ko_09774088f47b820e":
        if _contains(text, "hot-deck", "hot duct"):
            return SplitGroup("hot_deck_control", "Hot Deck Temperature Control", "hot_deck_control", "duct: hot deck")
        return SplitGroup("cold_duct_control", "Cold Duct Temperature Control", "cold_duct_control", "duct: cold duct")
    return None


def _classify_rejected_mix(old_ko_id: str, text: str) -> SplitGroup | None:
    if old_ko_id == "ko_0a2c2eebadb6cf7a":
        if _contains(text, "冷却水水质", "氯离子", "全硬度", "ph（25"):
            return SplitGroup("rejected_water_quality", "水质证据误抽取", "rejected_water_quality", "cross-topic water quality", "rejected", "single_source")
        if _contains(text, "⍤", "\x7f"):
            return SplitGroup("rejected_ocr_garbage", "OCR乱码证据", "rejected_ocr_garbage", "ocr garbage", "rejected", "single_source")
        return SplitGroup("main_power_voltage_variation", "主电源电压波动", "main_power_voltage_variation", "kept voltage evidence")

    if old_ko_id == "ko_d53103623a638535":
        if _contains(text, "电压", "频率", "相间", "电源"):
            return SplitGroup("rejected_voltage_scope", "电源范围误抽取", "rejected_voltage_scope", "cross-topic voltage evidence", "rejected", "single_source")
        return SplitGroup("ambient_temperature_range", "设置环境温度范围", "ambient_temperature_range", "kept ambient condition")

    if old_ko_id == "ko_5d02f6cccbb51a2a":
        if "试验时" in text or "气体温度" in text:
            return SplitGroup("rejected_test_temperature", "试验温度误抽取", "rejected_test_temperature", "cross-topic test temperature", "rejected", "single_source")
        return SplitGroup("pumpout_start_setpoint", "抽空启动设定点", "pumpout_start_setpoint", "kept pumpout evidence")

    if old_ko_id == "ko_04dc5b2658675b79":
        if _contains(text, "低压保护", "蒸发压力", "高压保护"):
            return SplitGroup("rejected_evap_pressure_fault", "蒸发压力保护误抽取", "rejected_evap_pressure_fault", "cross-topic pressure fault", "rejected", "single_source")
        return SplitGroup("low_oil_pressure_differential", "油压差过低", "low_oil_pressure_differential", "kept oil pressure evidence")
    return None


def _classify_standard_mix(old_ko_id: str, text: str, page_no: str | int) -> SplitGroup | None:
    if old_ko_id == "ko_22c130aad4ba2827":
        refrigerant = _refrigerant_key(text, page_no=page_no) or "unknown_refrigerant"
        return SplitGroup(refrigerant, f"{refrigerant.upper()} normal boiling point", refrigerant, "refrigerant split")

    if old_ko_id == "ko_050ac03ff6e2b012":
        if _contains(text, "climatic design", "stationcooling", "paul "):
            return SplitGroup("outdoor_design_temperatures", "outdoor design temperatures", "outdoor_design_temperatures", "kept climate design evidence")
        return SplitGroup("rejected_unrelated_standard", "无关标准证据", "rejected_unrelated_standard", "cross-topic standard evidence", "rejected", "single_source")

    if old_ko_id == "ko_051d666042fe81b7":
        if _contains(text, "formaldehyde", "voc", "solvent", "vapor"):
            return SplitGroup("voc_formaldehyde", "Maximum solvent vapor concentration", "voc_formaldehyde", "VOC/formaldehyde concept")
        return SplitGroup("unit_ventilator_selection", "Unit ventilator selection", "unit_ventilator_selection", "unit ventilator concept")

    if old_ko_id == "ko_ec0f999bae1fab30":
        if _contains(text, "selecting twi", "ground coil", "entering water"):
            return SplitGroup("entering_water_temperature_selection", "entering water temperature selection", "entering_water_temperature_selection", "kept entering water evidence")
        return SplitGroup("rejected_unrelated_standard", "无关标准证据", "rejected_unrelated_standard", "cross-topic standard evidence", "rejected", "single_source")

    if old_ko_id == "ko_933017f2e086099d":
        if _contains(text, "above cooling setpoint", "level 4 alarm"):
            return SplitGroup("zone_temperature_alarm_rule", "Zone Temperature Alarm Rule", "zone_temperature_alarm_rule", "kept alarm rule")
        return SplitGroup("rejected_section_header", "Zone Temperature Alarms section header", "rejected_section_header", "section header only", "rejected", "single_source")
    return None


def _classify_post_batch1_case(old_ko_id: str, text: str, page_no: str | int) -> SplitGroup | None:
    if old_ko_id == "ko_3d285aa3a09556b2":
        if "额定温度" in text:
            return SplitGroup("rated_leaving_water_temperature", "标准空调工况出水额定温度", "rated_leaving_water_temperature", "rated condition")
        return SplitGroup("cooling_restart_delta", "制冷模式出水温度重启偏差", "cooling_restart_delta", "control delta")

    if old_ko_id in {"ko_69ed0c22154f8e08", "ko_7f9870a9f4f55691", "ko_d117735fd9164c58", "ko_f8fea0a88ba94ce1"}:
        refrigerant = _refrigerant_key(text, page_no=page_no)
        if old_ko_id == "ko_f8fea0a88ba94ce1" and not refrigerant:
            refrigerant = "r134a"
        if not refrigerant:
            refrigerant = "generic"
        base_title = {
            "ko_69ed0c22154f8e08": "润滑油型号",
            "ko_7f9870a9f4f55691": "名义制冷量",
            "ko_d117735fd9164c58": "名义制热量",
            "ko_f8fea0a88ba94ce1": "额定制冷量(制冷工况)",
        }[old_ko_id]
        return SplitGroup(refrigerant, f"{base_title} {refrigerant.upper()}", refrigerant, "refrigerant split")

    if old_ko_id == "ko_e0075dafbff580a7":
        if _contains(text, "制热", "热盘管"):
            return SplitGroup("rejected_heating_table", "制热表格误抽取", "rejected_heating_table", "heating evidence in cooling KO", "rejected", "single_source")
        return SplitGroup("cooling_capacity", "制冷量", "cooling_capacity", "kept cooling evidence")

    if old_ko_id == "ko_2ba76711e02b5977":
        return SplitGroup("heating_capacity", "制热量", "heating_capacity", "same concept different coil rows", "published", "value_disagreement")
    return None


def classify_evidence_group(old_ko_id: str, evidence: dict[str, Any]) -> SplitGroup:
    """Classify one evidence row into its split target."""

    raw_text = str(evidence.get("evidence_text") or "")
    text = " ".join(raw_text.split())
    page_no = evidence.get("page_no", "")
    for classifier in (
        _classify_pressure_and_fault,
        _classify_concept_pair,
        _classify_rejected_mix,
    ):
        group = classifier(old_ko_id, text)
        if group:
            return group
    for classifier in (_classify_standard_mix, _classify_post_batch1_case):
        group = classifier(old_ko_id, text, page_no)
        if group:
            return group
    return SplitGroup("needs_human_review", "needs human review", "needs_human_review", "no deterministic rule", "published", "over_merge")


def _stable_id(prefix: str, seed: str) -> str:
    return f"{prefix}_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:16]}"


def _json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if value is not None else {}


def _load_old_ko(session: Any, ko_id: str) -> dict[str, Any] | None:
    row = session.execute(
        text("SELECT * FROM knowledge_object WHERE knowledge_object_id = :ko_id"),
        {"ko_id": ko_id},
    ).mappings().first()
    return dict(row) if row else None


def _load_evidence(session: Any, ko_id: str) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            "SELECT ev.*, d.file_name, d.vendor_brand, d.publisher "
            "FROM knowledge_object_evidence ev "
            "LEFT JOIN document d ON d.doc_id = ev.doc_id "
            "WHERE ev.knowledge_object_id = :ko_id "
            "ORDER BY ev.page_no, ev.knowledge_evidence_id"
        ),
        {"ko_id": ko_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def _unique_canonical_key(session: Any, base_key: str, *, old_ko_id: str, new_ko_id: str) -> str:
    candidate = base_key
    counter = 2
    while session.execute(
        text(
            "SELECT 1 FROM knowledge_object "
            "WHERE canonical_key = :key "
            "AND knowledge_object_id NOT IN (:old_id, :new_id) LIMIT 1"
        ),
        {"key": candidate, "old_id": old_ko_id, "new_id": new_ko_id},
    ).first():
        candidate = f"{base_key}_{counter}"
        counter += 1
    return candidate


def _new_key(old_key: str, suffix: str) -> str:
    slug = _slugify_part(suffix) or _stable_id("key", suffix)
    return f"{old_key}_{slug}"


def _layer_for_evidence(ev: dict[str, Any], *, group: SplitGroup, old_ko: dict[str, Any]) -> dict[str, Any]:
    publisher = ev.get("publisher") or ev.get("vendor_brand") or "unknown"
    payload = {
        "parameter_name": group.title,
        "title": group.title,
        "summary": str(ev.get("evidence_text") or "")[:240],
    }
    if group.key.startswith("fc_"):
        payload["fault_code"] = group.key.upper().replace("_", "#")
    return {
        "authority_level": old_ko.get("highest_authority_level") or "unspecified",
        "publisher": publisher,
        "citation": ev.get("evidence_citation"),
        "source_name": group.title,
        "structured_payload": payload,
        "value_summary": str(ev.get("evidence_text") or "")[:160],
        "evidence_role": "primary",
        "doc_id": ev.get("doc_id"),
        "chunk_id": ev.get("chunk_id"),
    }


def _consensus_for_group(group: SplitGroup, evidence_rows: list[dict[str, Any]]) -> str:
    if group.consensus_state:
        return group.consensus_state
    if group.review_status == "rejected":
        return "single_source"
    return "single_source" if len(evidence_rows) <= 1 else "value_disagreement"


def _build_new_ko_payload(
    session: Any, *, old_ko: dict[str, Any], group: SplitGroup, evidence_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    new_id = _stable_id("ko", f"cleanup_batch2:{old_ko['knowledge_object_id']}:{group.key}")
    canonical_key = _unique_canonical_key(
        session,
        _new_key(old_ko["canonical_key"], group.suffix),
        old_ko_id=old_ko["knowledge_object_id"],
        new_ko_id=new_id,
    )
    assert_valid_ko_identity(
        {"ontology_class_id": old_ko["ontology_class_id"], "canonical_key": canonical_key},
        context=f"cleanup batch2 {new_id}",
    )
    layers = [_layer_for_evidence(ev, group=group, old_ko=old_ko) for ev in evidence_rows]
    structured_payload = dict(layers[0]["structured_payload"])
    summary = str(evidence_rows[0].get("evidence_text") or old_ko.get("summary") or "")[:500]
    consensus_state = _consensus_for_group(group, evidence_rows)
    review_status = group.review_status
    payload = {
        "knowledge_object_id": new_id,
        "domain_id": old_ko["domain_id"],
        "ontology_class_key": f"hvac:{old_ko['ontology_class_id']}",
        "ontology_class_id": old_ko["ontology_class_id"],
        "knowledge_object_type": old_ko["knowledge_object_type"],
        "canonical_key": canonical_key,
        "title": group.title,
        "summary": summary,
        "structured_payload_json": json.dumps(structured_payload, ensure_ascii=False),
        "applicability_json": json.dumps(_json(old_ko.get("applicability_json")), ensure_ascii=False),
        "confidence_score": old_ko.get("confidence_score"),
        "trust_level": old_ko.get("trust_level") or "L3",
        "review_status": review_status,
        "primary_chunk_id": evidence_rows[0]["chunk_id"],
        "authority_summary_json": json.dumps({"layers": layers}, ensure_ascii=False),
        "consensus_state": consensus_state,
        "conflict_summary": None if consensus_state != "over_merge" else old_ko.get("conflict_summary"),
        "highest_authority_level": old_ko.get("highest_authority_level") or "unspecified",
        "deviation_justification_json": json.dumps(_json(old_ko.get("deviation_justification_json")), ensure_ascii=False),
        "package_version": old_ko.get("package_version") or "0.2.0",
        "ontology_version": old_ko.get("ontology_version") or "0.2.0",
        "curated_against_ontology_version": old_ko.get("curated_against_ontology_version"),
    }


def _upsert_new_ko(session: Any, payload: dict[str, Any]) -> None:
    session.execute(
        text(
            "INSERT INTO knowledge_object (knowledge_object_id, domain_id, ontology_class_key, ontology_class_id, "
            "knowledge_object_type, canonical_key, title, summary, structured_payload_json, applicability_json, "
            "confidence_score, trust_level, review_status, primary_chunk_id, authority_summary_json, consensus_state, "
            "conflict_summary, highest_authority_level, deviation_justification_json, package_version, ontology_version, "
            "curated_against_ontology_version) "
            "VALUES (:knowledge_object_id, :domain_id, :ontology_class_key, :ontology_class_id, :knowledge_object_type, "
            ":canonical_key, :title, :summary, CAST(:structured_payload_json AS json), CAST(:applicability_json AS json), "
            ":confidence_score, :trust_level, :review_status, :primary_chunk_id, CAST(:authority_summary_json AS json), "
            ":consensus_state, :conflict_summary, :highest_authority_level, CAST(:deviation_justification_json AS json), "
            ":package_version, :ontology_version, :curated_against_ontology_version) "
            "ON CONFLICT (knowledge_object_id) DO UPDATE SET "
            "canonical_key = EXCLUDED.canonical_key, title = EXCLUDED.title, summary = EXCLUDED.summary, "
            "structured_payload_json = EXCLUDED.structured_payload_json, review_status = EXCLUDED.review_status, "
            "primary_chunk_id = EXCLUDED.primary_chunk_id, authority_summary_json = EXCLUDED.authority_summary_json, "
            "consensus_state = EXCLUDED.consensus_state, conflict_summary = EXCLUDED.conflict_summary"
        ),
        payload,
    )


def _insert_or_update_new_ko(
    session: Any,
    *,
    old_ko: dict[str, Any],
    group: SplitGroup,
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = _build_new_ko_payload(session, old_ko=old_ko, group=group, evidence_rows=evidence_rows)
    _upsert_new_ko(session, payload)
    return {
        "new_ko_id": payload["knowledge_object_id"],
        "new_canonical_key": payload["canonical_key"],
        "title": payload["title"],
        "review_status": payload["review_status"],
        "consensus_state": payload["consensus_state"],
    }


def _group_evidence(ko_id: str, evidence_rows: list[dict[str, Any]]) -> dict[str, tuple[SplitGroup, list[dict[str, Any]]]]:
    grouped: dict[str, tuple[SplitGroup, list[dict[str, Any]]]] = {}
    for ev in evidence_rows:
        group = classify_evidence_group(ko_id, ev)
        grouped.setdefault(group.key, (group, []))[1].append(ev)
    return grouped


def _state_only_from_group(session: Any, ko_id: str, group: SplitGroup) -> list[dict[str, Any]]:
    state = group.consensus_state or ("single_source" if group.review_status == "rejected" else "value_disagreement")
    session.execute(
        text("UPDATE knowledge_object SET consensus_state = :state, review_status = :status WHERE knowledge_object_id = :ko_id"),
        {"state": state, "status": group.review_status, "ko_id": ko_id},
    )
    return [{
        "old_ko_id": ko_id,
        "action": "state_only",
        "reason": group.reason,
        "new_ko_ids": "",
        "detail": f"{state}/{group.review_status}",
    }]


def _move_grouped_evidence(session: Any, ko_id: str, old_ko: dict[str, Any], grouped: dict[str, tuple[SplitGroup, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    created = []
    for group, rows in grouped.values():
        created_info = _insert_or_update_new_ko(session, old_ko=old_ko, group=group, evidence_rows=rows)
        session.execute(
            text(
                "UPDATE knowledge_object_evidence SET knowledge_object_id = :new_id "
                "WHERE knowledge_object_id = :old_id AND knowledge_evidence_id = ANY(:evidence_ids)"
            ),
            {
                "new_id": created_info["new_ko_id"],
                "old_id": ko_id,
                "evidence_ids": [row["knowledge_evidence_id"] for row in rows],
            },
        )
        created.append({**created_info, "group_key": group.key, "reason": group.reason, "evidence_count": len(rows)})
    return created


def _split_ko(session: Any, ko_id: str) -> list[dict[str, Any]]:
    old_ko = _load_old_ko(session, ko_id)
    if not old_ko:
        return []
    evidence_rows = _load_evidence(session, ko_id)
    if not evidence_rows:
        return []

    grouped = _group_evidence(ko_id, evidence_rows)
    if len(grouped) == 1:
        return _state_only_from_group(session, ko_id, next(iter(grouped.values()))[0])

    created = _move_grouped_evidence(session, ko_id, old_ko, grouped)
    session.execute(text("DELETE FROM knowledge_object WHERE knowledge_object_id = :ko_id"), {"ko_id": ko_id})
    return [{
        "old_ko_id": ko_id,
        "action": "split",
        "reason": "; ".join(sorted({item["reason"] for item in created})),
        "new_ko_ids": ";".join(item["new_ko_id"] for item in created),
        "detail": json.dumps(created, ensure_ascii=False, sort_keys=True),
    }]


def _reject_old(session: Any, ko_id: str, reason: str) -> list[dict[str, Any]]:
    if not _load_old_ko(session, ko_id):
        return []
    session.execute(
        text("UPDATE knowledge_object SET review_status = 'rejected' WHERE knowledge_object_id = :ko_id"),
        {"ko_id": ko_id},
    )
    return [{"old_ko_id": ko_id, "action": "reject_old", "reason": reason, "new_ko_ids": "", "detail": ""}]


def _state_only(session: Any, ko_id: str, state: str) -> list[dict[str, Any]]:
    if not _load_old_ko(session, ko_id):
        return []
    session.execute(
        text("UPDATE knowledge_object SET consensus_state = :state WHERE knowledge_object_id = :ko_id"),
        {"state": state, "ko_id": ko_id},
    )
    return [{"old_ko_id": ko_id, "action": "state_only", "reason": "post-batch1 audit", "new_ko_ids": "", "detail": state}]


def active_over_merge_ids(session: Any) -> set[str]:
    rows = session.execute(text(
        "SELECT knowledge_object_id FROM knowledge_object "
        "WHERE consensus_state = 'over_merge' AND review_status <> 'rejected'"
    )).all()
    return {row[0] for row in rows}


def run_cleanup(session: Any) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    active = active_over_merge_ids(session)
    for ko_id, reason in REJECT_OLD_IDS.items():
        if ko_id in active:
            logs.extend(_reject_old(session, ko_id, reason))
    for ko_id, state in STATE_ONLY.items():
        if ko_id in active:
            logs.extend(_state_only(session, ko_id, state))
    for ko_id in sorted(active_over_merge_ids(session)):
        logs.extend(_split_ko(session, ko_id))
    return logs


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["old_ko_id", "action", "reason", "new_ko_ids", "detail"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    session = SessionLocal()
    try:
        before = len(active_over_merge_ids(session))
        logs = run_cleanup(session)
        after = len(active_over_merge_ids(session))
        if args.dry_run:
            session.rollback()
        else:
            session.commit()
        _write_csv(output_dir / "batch2_split_log.csv", logs)
        (output_dir / "cleanup_summary.json").write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "dry_run": args.dry_run,
                    "active_over_merge_before": before,
                    "active_over_merge_after": after,
                    "operation_count": len(logs),
                    "logs": logs,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "dry_run": args.dry_run,
            "active_over_merge_before": before,
            "active_over_merge_after": after,
            "operation_count": len(logs),
            "output_dir": str(output_dir),
        }, sort_keys=True))
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
