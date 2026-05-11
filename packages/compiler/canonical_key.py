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
CONCEPT_GROUP_TASK = "concept_group_and_normalize"


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
    """Check if any input name is already registered under a canonical_key with the expected type prefix.

    Prefers semantic keys over auto-generated hashed keys (key_* pattern).
    """
    registry = _load_registry()
    keys = registry.get("canonical_keys", {})
    matches: list[str] = []
    for name in names:
        for existing_key, aliases in keys.items():
            if name in aliases and f":{type_prefix}:" in existing_key:
                matches.append(existing_key)
    if not matches:
        return None
    # Prefer non-hashed (semantic) keys
    semantic = [k for k in matches if not k.split(":")[-1].startswith("key_")]
    return semantic[0] if semantic else matches[0]


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
        "You are a domain knowledge engineer normalizing industrial HVAC equipment parameter "
        "names into stable, machine-friendly canonical keys.\n\n"
        "CRITICAL RULES — violations will corrupt the knowledge base:\n"
        "1. Different physical quantities MUST stay in different groups, even if their names "
        "share words. Examples of WRONG merges:\n"
        '   - "Differential to Start" + "Differential to Stop" → DIFFERENT (start vs stop threshold)\n'
        '   - "Return Maximum Reset" + "Outdoor Maximum Reset" → DIFFERENT (return water vs outdoor air)\n'
        '   - "Front Panel X" + "External X" → DIFFERENT (local panel vs remote input)\n'
        '   - "Return Reset Ratio" + "Return Maximum Reset" → DIFFERENT (ratio vs absolute limit)\n'
        "2. Cross-language synonyms ARE the same concept and SHOULD be merged:\n"
        '   - "Chilled Water Setpoint" + "冷冻水出水温度设定" → SAME\n'
        '   - "Current Limit" + "电流限制" → SAME\n'
        "3. Same quantity with different unit (F vs C) IS the same concept — merge.\n"
        "4. canonical_key format: lowercase, underscores only, concise (3-5 words).\n"
        "5. Prefer ASHRAE/IEC standard terminology.\n"
        "6. When uncertain whether two names are the same quantity, keep them SEPARATE.\n\n"
        "Return JSON with groups array. Each group has: canonical_key, normalized_name, "
        "member_names (from input), rationale (one sentence)."
    )
    user_prompt = json.dumps(
        {
            "task": CONCEPT_GROUP_TASK,
            "domain_id": domain_id,
            "equipment_class_id": equipment_class_id,
            "knowledge_object_type": knowledge_object_type,
            "key_format": key_format,
            "input_names": names,
            "required_output": {
                "groups": [
                    {
                        "canonical_key": key_format,
                        "normalized_name": "concise_slug",
                        "member_names": ["name1", "name2"],
                        "rationale": "why these are the same concept",
                    }
                ]
            },
        },
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _llm_group_and_normalize(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
) -> list[dict[str, Any]]:
    """Call LLM (temperature 0) to group names by concept and assign canonical keys.

    Returns list of group dicts: {canonical_key, normalized_name, member_names, rationale}.
    """
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

    groups = body.get("groups")
    if not isinstance(groups, list) or not groups:
        # Fallback: all names in one group with mechanical key
        domain_slug = _slugify_part(domain_id)
        equipment_slug = _slugify_part(equipment_class_id)
        type_prefix = _knowledge_type_prefix(knowledge_object_type)
        slug = _slugify_part(names[0]) if names else "unknown"
        if not slug:
            slug = _hashed_slug(names[0]) if names else "unknown"
        return [{
            "canonical_key": f"{domain_slug}:{equipment_slug}:{type_prefix}:{slug}",
            "normalized_name": slug,
            "member_names": list(names),
            "rationale": "Mechanical fallback — LLM returned no groups",
        }]

    # Validate and clean groups
    validated = []
    seen_names = set()
    for g in groups:
        if not isinstance(g, dict):
            continue
        ck = str(g.get("canonical_key") or "").strip()
        members = g.get("member_names") or []
        if not isinstance(members, list):
            members = [str(members)]
        members = [str(m) for m in members if str(m).strip()]
        members = [m for m in members if m not in seen_names]
        if not ck or not members:
            continue
        for m in members:
            seen_names.add(m)
        validated.append({
            "canonical_key": ck,
            "normalized_name": str(g.get("normalized_name", "") or ""),
            "member_names": members,
            "rationale": str(g.get("rationale", "") or ""),
        })

    # Any names not in any group → each gets its own mechanical group
    domain_slug = _slugify_part(domain_id)
    equipment_slug = _slugify_part(equipment_class_id)
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    for name in names:
        if name not in seen_names:
            slug = _slugify_part(name)
            if not slug:
                slug = _hashed_slug(name)
            validated.append({
                "canonical_key": f"{domain_slug}:{equipment_slug}:{type_prefix}:{slug}",
                "normalized_name": slug,
                "member_names": [name],
                "rationale": "Unmatched by LLM — mechanical key",
            })

    return validated


def group_and_normalize(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
) -> dict[str, str]:
    """Group names by concept and normalize each group to a canonical key.

    Returns a mapping of name → canonical_key. Each unique concept gets one key.
    Names that refer to different physical quantities get different keys.
    """
    if not names:
        return {}

    cleaned = [str(n).strip() for n in names if str(n).strip()]
    if not cleaned:
        return {}

    # 1. Hash cache
    input_hash = _hash_inputs(cleaned, knowledge_object_type)
    if input_hash in HASH_CACHE:
        cached = HASH_CACHE[input_hash]
        if isinstance(cached, dict):
            return cached

    # 2. LLM grouping + normalization
    groups = _llm_group_and_normalize(
        cleaned,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
        backend_name=backend_name,
    )

    # 3. Build name→key map, register all names
    mapping: dict[str, str] = {}
    for g in groups:
        ck = g["canonical_key"]
        _register(g["member_names"], ck)
        for name in g["member_names"]:
            mapping[name] = ck

    HASH_CACHE[input_hash] = mapping
    return mapping


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
    """Append new entries to the registry, removing names from any other keys.

    A name can only belong to one canonical_key at a time.
    """
    registry = _load_registry()
    keys = registry.setdefault("canonical_keys", {})
    # Remove these names from any other keys they were previously registered under
    for existing_key, aliases in list(keys.items()):
        if existing_key == canonical_key:
            continue
        keys[existing_key] = [a for a in aliases if a not in names]
        if not keys[existing_key]:
            del keys[existing_key]
    # Add to the target key
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

    # 2. Registry lookup — if any names are already registered, reuse that key
    #    and register any new names under it too
    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    registered = _lookup_registry(cleaned, type_prefix)
    if registered is not None:
        # Register any new names under the existing key
        _register(cleaned, registered)
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
