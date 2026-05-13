"""Compiler run and audit packet helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from packages.compiler.contracts import CompilerAuditPacket, CompilerRun, LLMAuditRecord, SourceManifestEntry

AUDIT_SCHEMA_VERSION = "2026-05-13"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _entry_evidence_list(entry: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = entry.get("evidence") or []
    if isinstance(evidence, dict):
        return [evidence]
    return evidence if isinstance(evidence, list) else []


def _collect_doc_ids(payload: dict[str, Any]) -> list[str]:
    doc_ids: set[str] = set()
    for entry in payload.get("candidate_entries") or []:
        if not isinstance(entry, dict):
            continue
        for evidence in _entry_evidence_list(entry):
            doc_id = evidence.get("doc_id") if isinstance(evidence, dict) else None
            if doc_id:
                doc_ids.add(str(doc_id))
    return sorted(doc_ids)


def _collect_authority_levels(payload: dict[str, Any]) -> list[str]:
    levels: set[str] = set()
    for entry in payload.get("candidate_entries") or []:
        authority = entry.get("authority_summary_json") if isinstance(entry, dict) else None
        layers = authority.get("layers", []) if isinstance(authority, dict) else []
        for layer in layers:
            level = layer.get("authority_level") if isinstance(layer, dict) else None
            if level:
                levels.add(str(level))
    return sorted(levels)


def build_review_pack_source_manifest_entry(
    pack_path: str | Path,
    payload: dict[str, Any],
) -> SourceManifestEntry:
    path = Path(pack_path)
    return SourceManifestEntry(
        source_id=path.stem,
        source_type="review_pack",
        path=str(path),
        content_sha256=sha256_file(path),
        domain_id=payload.get("domain_id"),
        doc_ids=_collect_doc_ids(payload),
        authority_levels=_collect_authority_levels(payload),
        metadata={
            "review_mode": payload.get("review_mode"),
            "candidate_count": len(payload.get("candidate_entries") or []),
        },
    )


def build_file_source_manifest_entry(
    source_path: str | Path,
    *,
    source_type: str = "derived_artifact",
    domain_id: str | None = None,
    authority_levels: list[str] | None = None,
    is_redistributable: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> SourceManifestEntry:
    path = Path(source_path)
    return SourceManifestEntry(
        source_id=path.stem,
        source_type=source_type,
        path=str(path),
        content_sha256=sha256_file(path),
        domain_id=domain_id,
        authority_levels=authority_levels or [],
        is_redistributable=is_redistributable,
        metadata=metadata or {},
    )


def build_compiler_run(
    *,
    compiler_run_id: str,
    pipeline: str,
    source_manifest: list[SourceManifestEntry],
    domain_id: str | None = None,
    package_version: str | None = None,
    ontology_version: str | None = None,
    llm_backend: str | None = None,
    parameters: dict[str, Any] | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> CompilerRun:
    return CompilerRun(
        compiler_run_id=compiler_run_id,
        pipeline=pipeline,
        started_at=started_at or utc_now_iso(),
        finished_at=finished_at,
        domain_id=domain_id,
        package_version=package_version,
        ontology_version=ontology_version,
        llm_backend=llm_backend,
        parameters=parameters or {},
        source_manifest=source_manifest,
    )


def build_compiler_audit_packet(
    *,
    compiler_run: CompilerRun,
    summary: dict[str, Any],
    results: list[dict[str, Any]],
) -> CompilerAuditPacket:
    failed_count = sum(1 for result in results if result.get("status") == "failed")
    flags = ["has_failed_results"] if failed_count else []
    return CompilerAuditPacket(
        audit_schema_version=AUDIT_SCHEMA_VERSION,
        compiler_run=compiler_run,
        source_manifest=compiler_run.source_manifest,
        summary=summary,
        results=results,
        integrity_checks={
            "source_manifest_count": len(compiler_run.source_manifest),
            "result_count": len(results),
            "failed_result_count": failed_count,
        },
        audit_flags=flags,
    )


def write_compiler_audit_packet(path: str | Path, packet: CompilerAuditPacket) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = packet.model_dump(mode="json")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***REDACTED***" if key.lower() in {"api_key", "authorization"} else _redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_secrets(item) for item in value]
    return value


def build_llm_audit_recorder(
    *,
    output_root: str | Path,
    compiler_run_id: str,
    call_site: str,
    backend_name: str | None = None,
    model: str | None = None,
    date_label: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[dict[str, Any]], Path]:
    """Build a JSONL recorder for replayable LLM request/response audits."""

    active_date = date_label or datetime.now(timezone.utc).strftime("%Y%m%d")
    target = Path(output_root) / "llm_audit" / active_date / f"{compiler_run_id}.jsonl"

    def record(payload: dict[str, Any]) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        row = LLMAuditRecord(
            audit_schema_version=AUDIT_SCHEMA_VERSION,
            compiler_run_id=compiler_run_id,
            call_site=call_site,
            recorded_at=utc_now_iso(),
            backend_name=backend_name,
            model=model,
            request=_redact_secrets(payload.get("request") or {}),
            response=_redact_secrets(payload.get("response")),
            error=str(payload["error"]) if payload.get("error") else None,
            metadata=metadata or {},
        )
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return target

    return record
