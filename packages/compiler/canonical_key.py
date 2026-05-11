"""Stable canonical-key normalization with LLM-assisted semantic merging.

Registry is append-only — once a canonical_key is published, it is never changed.
Hash cache ensures determinism: same sorted inputs always produce the same key.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from packages.compiler.llm_compiler import (
    _hashed_slug,
    _knowledge_type_prefix,
    _request_json_completion,
    _slugify_part,
    resolve_backend,
)

REGISTRY_PATH = Path(__file__).resolve().parent / "canonical_key_registry.yaml"
HASH_CACHE: dict[str, str] = {}

CANONICAL_KEY_TASK = "canonical_key_normalization"


def _load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {"canonical_keys": {}}


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _hash_inputs(names: list[str], knowledge_object_type: str = "") -> str:
    payload = json.dumps({"names": sorted(names), "type": knowledge_object_type}, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _lookup_registry(names: list[str], type_prefix: str) -> str | None:
    """Check if any input name is already registered under a canonical_key with the expected type prefix."""
    registry = _load_registry()
    keys = registry.get("canonical_keys", {})
    for name in names:
        for existing_key, aliases in keys.items():
            if name in aliases and f":{type_prefix}:" in existing_key:
                return existing_key
    return None


def _build_prompt(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
) -> list[dict[str, str]]:
    domain_slug = _slugify_part(domain_id)
    equipment_slug = _slugify_part(equipment_class_id)
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    key_format = f"{domain_slug}:{equipment_slug}:{type_prefix}:<normalized_name>"

    system_prompt = (
        "You are a domain knowledge engineer normalizing industrial equipment parameter names "
        "into stable, machine-friendly canonical keys. Your output must be deterministic.\n\n"
        "Rules:\n"
        "1. canonical_key must be lowercase, underscores only, no spaces or punctuation.\n"
        "2. Prefer standard industry terminology (ASHRAE, IEC, ISO conventions).\n"
        "3. Merge synonyms aggressively: 'CHWS temp', 'chilled water supply temperature', "
        "'leaving chilled water temp' are the same concept.\n"
        "4. The normalized_name part should be concise (3-5 words max).\n"
        "5. Do NOT invent new distinctions. If inputs are clearly the same concept, merge them.\n\n"
        "Return only: {\"canonical_key\": \"...\", \"normalized_name\": \"...\", \"rationale\": \"...\"}"
    )
    user_prompt = json.dumps(
        {
            "task": CANONICAL_KEY_TASK,
            "domain_id": domain_id,
            "equipment_class_id": equipment_class_id,
            "knowledge_object_type": knowledge_object_type,
            "key_format": key_format,
            "input_names": names,
        },
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _llm_normalize(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
) -> str:
    """Call LLM (temperature 0) to normalize names into one canonical key."""
    backend = resolve_backend(backend_name=backend_name)
    if backend is None:
        raise RuntimeError("No LLM backend available for canonical key normalization")

    messages = _build_prompt(
        names,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
    )

    try:
        body = _request_json_completion(
            messages,
            backend,
            response_format={"type": "json_object"},
        )
    except Exception:
        body = {}

    candidate = str(body.get("canonical_key") or "").strip()
    if candidate:
        return candidate

    # Mechanical fallback
    domain_slug = _slugify_part(domain_id)
    equipment_slug = _slugify_part(equipment_class_id)
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    slug = _slugify_part(names[0])
    if not slug:
        slug = _hashed_slug(names[0])
    return f"{domain_slug}:{equipment_slug}:{type_prefix}:{slug}"


def _register(names: list[str], canonical_key: str) -> None:
    """Append new entries to the registry. Never overwrites existing keys."""
    registry = _load_registry()
    keys = registry.setdefault("canonical_keys", {})
    existing = keys.setdefault(canonical_key, [])
    for name in names:
        if name not in existing:
            existing.append(name)
    _save_registry(registry)


def resolve_canonical_key(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
) -> str:
    """Resolve a set of names to one stable canonical key.

    Resolution order:
    1. Hash cache (in-memory, same process)
    2. Registry lookup (on-disk, cross-process)
    3. LLM normalization (temperature 0) + register + cache
    """
    if not names:
        raise ValueError("At least one name is required")

    cleaned = [str(n).strip() for n in names if str(n).strip()]
    if not cleaned:
        raise ValueError("No non-empty names provided")

    # 1. Hash cache
    input_hash = _hash_inputs(cleaned, knowledge_object_type)
    if input_hash in HASH_CACHE:
        return HASH_CACHE[input_hash]

    # 2. Registry lookup
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    registered = _lookup_registry(cleaned, type_prefix)
    if registered is not None:
        HASH_CACHE[input_hash] = registered
        return registered

    # 3. LLM normalization
    canonical_key = _llm_normalize(
        cleaned,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
        backend_name=backend_name,
    )

    # 4. Register + cache
    _register(cleaned, canonical_key)
    HASH_CACHE[input_hash] = canonical_key
    return canonical_key


def resolve_single_name(
    name: str,
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
) -> str:
    """Resolve a single name — registry lookup first, then mechanical normalization."""
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Name must not be empty")

    input_hash = _hash_inputs([cleaned], knowledge_object_type)
    if input_hash in HASH_CACHE:
        return HASH_CACHE[input_hash]

    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    registered = _lookup_registry([cleaned], type_prefix)
    if registered is not None:
        HASH_CACHE[input_hash] = registered
        return registered

    domain_slug = _slugify_part(domain_id)
    equipment_slug = _slugify_part(equipment_class_id)
    slug = _slugify_part(cleaned)
    if not slug:
        slug = _hashed_slug(cleaned)
    canonical_key = f"{domain_slug}:{equipment_slug}:{type_prefix}:{slug}"

    _register([cleaned], canonical_key)
    HASH_CACHE[input_hash] = canonical_key
    return canonical_key
