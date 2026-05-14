"""Stable canonical-key normalization with LLM-assisted semantic merging.

Registry is append-only — once a canonical_key is published, it is never changed.
Hash cache ensures determinism: same sorted inputs always produce the same key.
"""

from __future__ import annotations

import hashlib
import json
import os
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
TERMINOLOGY_PATHS = [
    Path(__file__).resolve().parents[2] / "domain_packages" / "hvac" / "v2" / "terminology_zh_en.yaml",
]
HASH_CACHE: dict[str, str] = {}

CANONICAL_KEY_TASK = "canonical_key_normalization"
CONCEPT_GROUP_TASK = "concept_group_and_normalize"
BATCH_SIZE = 30  # E2: max names per LLM call
MAX_GROUP_SIZE = 10  # E2: sanity — no single concept should have >10 true synonyms
EMBEDDING_RECLUSTER_MAX_SIZE = 8  # Rich-state guard: keep regroup layers below super-KO size


def _load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {"canonical_keys": {}}


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _hash_inputs(
    names: list[str],
    knowledge_object_type: str = "",
    facet_hints: dict[str, str | None] | None = None,
) -> str:
    payload = json.dumps(
        {"names": sorted(names), "type": knowledge_object_type, "facet_hints": facet_hints or {}},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _load_terminology() -> dict[str, list[str]]:
    """Load domain-specific terminology YAML files into a name→key mapping."""
    merged: dict[str, list[str]] = {}
    for path in TERMINOLOGY_PATHS:
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for ck, aliases in data.get("terms", {}).items():
            merged[ck] = list(aliases)
    return merged


def _lookup_registry(names: list[str], type_prefix: str) -> str | None:
    """Check if any input name is already registered under a canonical_key with the expected type prefix.

    Checks terminology YAML first (deterministic, human-reviewed),
    then dynamic registry. Prefers semantic keys over hashed keys.
    """
    # 1. Check terminology YAML (authoritative, human-reviewed)
    terminology = _load_terminology()
    for name in names:
        for ck, aliases in terminology.items():
            if name in aliases:
                domain_slug = _slugify_part(ck)  # terminology key format
                return ck  # Return the concept group name as-is

    # 2. Check dynamic registry
    registry = _load_registry()
    keys = registry.get("canonical_keys", {})
    matches: list[str] = []
    for name in names:
        for existing_key, aliases in keys.items():
            if name in aliases and f":{type_prefix}:" in existing_key:
                matches.append(existing_key)
    if not matches:
        return None
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
        "CRITICAL RULES — violations will corrupt the knowledge base:\n\n"
        "1. These are DIFFERENT concepts and MUST stay in separate groups:\n"
        '   - "X Front Panel" vs "X External" → DIFFERENT input source (local HMI vs remote analog)\n'
        '   - "X 水侧" vs "X 制冷剂侧" vs "X 空气侧" → DIFFERENT medium (water/refrigerant/air side)\n'
        '   - "Differential to Start" vs "Differential to Stop" → DIFFERENT threshold\n'
        '   - "X Return" vs "X Outdoor" vs "X Supply" → DIFFERENT reference point\n'
        '   - "X Reset" vs "X Reset Ratio" → DIFFERENT (absolute limit vs proportional ratio)\n'
        '   - "X Capacity" vs "X Capacity Limit" → DIFFERENT (actual vs constraint)\n'
        '   - "Maximum X" vs "Minimum X" → DIFFERENT (upper vs lower bound)\n\n'
        '   When names share core words but differ in: input source (Panel/External/Remote/Local), '
        'medium (water/refrigerant/air/oil), or bound (Max/Min/Start/Stop) → SEPARATE groups.\n\n'
        "2. These ARE the same concept and MUST be merged into one group:\n"
        '   - Cross-language: "Chilled Water Setpoint" + "冷冻水出水温度设定" → SAME\n'
        '   - Cross-language: "Current Limit" + "电流限制" → SAME\n'
        '   - Same quantity, different unit: 44F vs 7C → SAME concept\n'
        '   - Abbreviation vs full name: "CHWS" vs "Chilled Water Supply" → SAME\n\n'
        "3. canonical_key format: lowercase, underscores only, 3-5 words, ASHRAE/IEC terminology.\n"
        "4. When uncertain whether two names are the same quantity → keep them SEPARATE.\n\n"
        "Return JSON: {\"groups\": [{canonical_key, normalized_name, member_names, rationale}]}"
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


CONFLICTING_QUALIFIERS = [
    # (category, [mutually_exclusive_patterns])
    ("source", ["front panel", "external", "active", "default", "remote", "local"]),
    ("medium", ["水侧", "制冷剂侧", "空气侧", "油侧", "water side", "refrigerant side"]),
    ("bound", ["maximum", "minimum", "最高", "最低", "最大", "最小", "start", "stop"]),
    ("reference", ["return", "outdoor", "supply", "indoor", "outdoor air"]),
    ("type", ["setpoint", "limit", "reset", "pressure", "temperature", "ratio", "time"]),
]


def _find_qualifier(name: str, patterns: list[str]) -> str | None:
    lower = name.lower()
    for p in patterns:
        if p in lower:
            return p
    return None


def _split_conflicting_groups(
    groups: list[dict[str, Any]],
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
) -> list[dict[str, Any]]:
    """Split LLM groups where member names have conflicting qualifiers.

    E.g. 'Front Panel Chilled Water' and 'External Chilled Water' in the same
    group → split into separate groups (different input sources).
    """
    refined = []
    for g in groups:
        members = g.get("member_names", [])
        if len(members) <= 1:
            refined.append(g)
            continue

        # Check each qualifier category
        split = False
        for category, patterns in CONFLICTING_QUALIFIERS:
            qualifiers = {}
            for name in members:
                q = _find_qualifier(name, patterns)
                if q:
                    qualifiers.setdefault(q, []).append(name)
            # If multiple different qualifiers found in same category → split
            if len(qualifiers) >= 2:
                split = True
                for q, q_members in qualifiers.items():
                    suffix = q.replace(" ", "_")
                    ck = g.get("canonical_key", f"unknown_{suffix}")
                    if not ck.endswith(f"_{suffix}"):
                        ck = f"{ck}_{suffix}"
                    refined.append({
                        "canonical_key": ck,
                        "normalized_name": g.get("normalized_name", "") + f"_{suffix}",
                        "member_names": q_members,
                        "rationale": f"Split from group '{g.get('canonical_key','?')}' — conflicting {category} qualifier: {q}",
                    })
                # Any unqualified names stay in original group
                unqualified = [n for n in members if all(n not in v for v in qualifiers.values())]
                if unqualified:
                    refined.append({**g, "member_names": unqualified})
                break  # Only split once per group
        if not split:
            refined.append(g)
    return refined


def _sanity_check_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """E2: Reject pathological groups where LLM merged unrelated concepts.

    - Oversized groups (>MAX_GROUP_SIZE) → split each member to own group
    - Degenerate canonical_keys ("1", "x", single digit) → replace with mechanical slug
    """
    sane = []
    for g in groups:
        members = g.get("member_names", [])
        ck = g.get("canonical_key", "")

        if len(members) > MAX_GROUP_SIZE:
            for n in members:
                slug = _slugify_part(n) or _hashed_slug(n)
                sane.append({
                    "canonical_key": slug,
                    "normalized_name": n,
                    "member_names": [n],
                    "rationale": f"E2 split: {len(members)}-member group exceeds max {MAX_GROUP_SIZE}",
                })
            continue

        slug = ck.split(":")[-1] if ":" in ck else ck
        if len(slug) <= 2 or slug.isdigit():
            for n in members:
                slug = _slugify_part(n) or _hashed_slug(n)
                sane.append({
                    "canonical_key": slug,
                    "normalized_name": n,
                    "member_names": [n],
                    "rationale": f"E2 split: degenerate canonical_key '{ck}'",
                })
            continue

        sane.append(g)
    return sane


def _apply_terminology(
    names: list[str],
    terminology: dict[str, list[str]],
) -> tuple[dict[str, str], list[str]]:
    """Resolve names via terminology YAML. Returns (resolved_mapping, unresolved_names)."""
    resolved: dict[str, str] = {}
    remaining: list[str] = []
    for name in names:
        found = False
        for ck, aliases in terminology.items():
            if name in aliases:
                resolved[name] = ck
                found = True
                break
        if not found:
            remaining.append(name)
    return resolved, remaining


def _cluster_recursive(
    names: list[str],
    embeddings: list[list[float]],
    *,
    threshold: float = 0.78,
    max_size: int = 15,
) -> list[list[str]]:
    """K3: Recursive clustering — tighten threshold on oversized clusters."""
    from packages.compiler.clustering import cluster_by_cosine
    clusters = cluster_by_cosine(names, embeddings, threshold=threshold)
    result = []
    for cluster in clusters:
        if len(cluster) <= max_size:
            result.append(cluster)
        elif threshold < 0.95:
            indices = [names.index(n) for n in cluster if n in names]
            sub_names = [names[i] for i in indices]
            sub_embs = [embeddings[i] for i in indices]
            result.extend(_cluster_recursive(sub_names, sub_embs, threshold=threshold + 0.05, max_size=max_size))
        else:
            result.append(cluster)  # cap reached, accept large cluster
    return result


def _tighten_oversize_embedding_clusters(
    names: list[str],
    embeddings: list[list[float]],
    clusters: list[list[str]],
    *,
    threshold: float,
) -> list[list[str]]:
    """Re-cluster oversized embedding clusters with stricter thresholds.

    N3 trusts embedding clusters directly, so E2's LLM sanity check does not run.
    Rich-state regroup can therefore inherit single-linkage mega-clusters. Keep
    normal small clusters intact and only tighten clusters that exceed sanity size.
    """
    refined: list[list[str]] = []
    index_by_name = {name: i for i, name in enumerate(names)}
    for cluster in clusters:
        if len(cluster) <= MAX_GROUP_SIZE:
            refined.append(cluster)
            continue

        indices = [index_by_name[n] for n in cluster if n in index_by_name]
        sub_names = [names[i] for i in indices]
        sub_embs = [embeddings[i] for i in indices]
        tightened = _cluster_recursive(
            sub_names,
            sub_embs,
            threshold=min(threshold + 0.05, 0.95),
            max_size=EMBEDDING_RECLUSTER_MAX_SIZE,
        )
        for sub_cluster in tightened:
            if len(sub_cluster) > MAX_GROUP_SIZE:
                refined.extend([[n] for n in sub_cluster])
            else:
                refined.append(sub_cluster)
    return refined


def _dump_embedding_cluster_trace(
    names: list[str],
    clusters: list[list[str]],
    *,
    threshold: float,
    equipment_class_id: str,
    knowledge_object_type: str,
    raw_clusters: list[list[str]] | None = None,
) -> None:
    if os.environ.get("KNOWFABRIC_DUMP_CLUSTER_TRACE") != "1":
        return

    from datetime import datetime as _dt, timezone as _tz

    run_id = _dt.now(_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(f"output/diagnostic/{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": "embedding_cluster_trace",
        "equipment_class_id": equipment_class_id,
        "knowledge_object_type": knowledge_object_type,
        "threshold": threshold,
        "input_count": len(names),
        "input_names": names,
        "raw_cluster_count": len(raw_clusters or clusters),
        "raw_clusters": [
            {"size": len(cluster), "members": cluster}
            for cluster in sorted(raw_clusters or clusters, key=len, reverse=True)
        ],
        "cluster_count": len(clusters),
        "clusters": [
            {"size": len(cluster), "members": cluster}
            for cluster in sorted(clusters, key=len, reverse=True)
        ],
    }
    with open(out_dir / "embedding_cluster_trace.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _dump_grouping_trace(
    *,
    names: list[str],
    embeddings: list[list[float]],
    threshold: float,
    equipment_class_id: str,
    knowledge_object_type: str,
    facet_hints: dict[str, str | None],
    raw_clusters: list[list[str]],
    tightened_clusters: list[list[str]],
    facet_clusters: list[list[str]],
    mapping: dict[str, str],
) -> None:
    trace_dir = os.environ.get("KNOWFABRIC_GROUPING_TRACE_DIR")
    if not trace_dir:
        return

    from datetime import datetime as _dt, timezone as _tz

    out_dir = Path(trace_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pairwise = []
    if len(names) <= 80:
        from packages.compiler.clustering import cosine
        for i, left in enumerate(names):
            for j in range(i + 1, len(names)):
                pairwise.append({
                    "left": left,
                    "right": names[j],
                    "cosine": round(cosine(embeddings[i], embeddings[j]), 4),
                })
    entry = {
        "ts": _dt.now(_tz.utc).isoformat(),
        "stage": "group_via_embedding",
        "equipment_class_id": equipment_class_id,
        "knowledge_object_type": knowledge_object_type,
        "threshold": threshold,
        "input_names": sorted(names),
        "input_order": names,
        "facet_hints": {name: facet_hints.get(name) for name in sorted(names)},
        "raw_clusters": [
            {"size": len(cluster), "members": cluster}
            for cluster in sorted(raw_clusters, key=len, reverse=True)
        ],
        "tightened_clusters": [
            {"size": len(cluster), "members": cluster}
            for cluster in sorted(tightened_clusters, key=len, reverse=True)
        ],
        "facet_split_clusters": [
            {"size": len(cluster), "members": cluster}
            for cluster in sorted(facet_clusters, key=len, reverse=True)
        ],
        "mapping": {name: mapping[name] for name in sorted(mapping)},
        "pairwise_cosines": pairwise,
    }
    with open(out_dir / "grouping_trace.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _dump_refinement_trace(cluster_names: list[str], groups: list[dict], llm_response: dict) -> None:
    """N3: dump what LLM refinement did to each cluster."""
    import json as _json, os as _os
    from datetime import datetime as _dt, timezone as _tz
    from pathlib import Path as _Path
    run_id = _dt.now(_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = _Path(f"output/diagnostic/{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "cluster_size": len(cluster_names),
        "cluster_members": cluster_names,
        "llm_groups": [{"key": g.get("canonical_key","?"), "members": g.get("member_names",[]), "rationale": g.get("rationale","")} for g in groups],
    }
    with open(out_dir / "n3_llm_refinement_trace.jsonl", "a", encoding="utf-8") as f:
        f.write(_json.dumps(entry, ensure_ascii=False) + "\n")


def _llm_refine_cluster(
    cluster_names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
) -> list[dict[str, Any]]:
    """Ask LLM whether cluster names are same concept or should split by facet."""
    backend = resolve_backend(backend_name=backend_name)
    if backend is None or len(cluster_names) <= 1:
        suggested_ck = _slugify_part(cluster_names[0]) if cluster_names else "unknown"
        return [{"canonical_key": suggested_ck, "member_names": cluster_names,
                 "rationale": "No LLM backend or single name; trusted embedding cluster"}]

    type_prefix = _knowledge_type_prefix(knowledge_object_type)
    system = (
        f"You are normalizing {knowledge_object_type} names within a "
        f"{equipment_class_id} domain. The input names may be in different "
        f"languages (English / Chinese) or use different naming conventions "
        f"(e.g. 'X Setpoint' / 'X Setting' / 'Active X' / 'External X' / 'X 设定' / 'X 范围')."
        f"\n\nYour task: group names by PHYSICAL QUANTITY, not by surface form."
        f"\n\nRULES:"
        f"\n1. Cross-language translations of the same physical quantity = SAME group"
        f"   (e.g. 'Oil Pressure Differential' + '油压差' → same group)"
        f"\n2. Different naming conventions for the same physical quantity = SAME group"
        f"   (e.g. 'Front Panel Chilled Water Setpoint' + 'External Chilled Water Setpoint' + "
        f"'冷冻水出水温度' → same group; the Front Panel/External distinction is a SOURCE "
        f"of value, not a different physical quantity)"
        f"\n3. Different physical quantities = DIFFERENT groups"
        f"   (e.g. 'Chilled Water Setpoint' vs 'Safety Valve Pressure' → different groups)"
        f"\n4. Different FACETS of same quantity (setpoint vs limit vs alarm threshold) "
        f"   = DIFFERENT groups, but keep them similarly named to preserve relationship"
        f"   (e.g. 'Chilled Water Setpoint' vs 'Chilled Water Maximum' → different groups)"
        f"\n\nReturn strict JSON:"
        f' {{"groups": [{{"canonical_key": "snake_case_slug", "member_names": [...], '
        f'"rationale": "..."}}, ...]}}'
        f"\n\nEvery input name must appear in exactly one group."
    )
    user = json.dumps({"candidate_names": cluster_names}, ensure_ascii=False)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    try:
        payload = _request_json_completion(messages, backend, response_format={"type": "json_object"})
        groups = payload.get("groups") or []
        # N3: dump LLM refinement trace
        _dump_refinement_trace(cluster_names, groups, payload)
    except Exception:
        covered = set()
        for g in groups:
            for n in g.get("member_names", []):
                covered.add(n)
        missing = [n for n in cluster_names if n not in covered]
        if missing:
            for n in missing:
                groups.append({"canonical_key": _slugify_part(n) or _hashed_slug(n),
                               "member_names": [n], "rationale": "LLM did not assign; mechanical fallback"})
        return groups
    except Exception:
        suggested_ck = _slugify_part(cluster_names[0]) if cluster_names else "unknown"
        return [{"canonical_key": suggested_ck, "member_names": cluster_names,
                 "rationale": "LLM refinement failed; trusted embedding cluster"}]


def _group_via_embedding(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
    facet_hints: dict[str, Any] | None = None,
) -> dict[str, str]:
    """H2: embedding-first grouping — BGE-M3 → cosine clustering → LLM refine."""
    cleaned = [str(n).strip() for n in names if str(n).strip()]
    mapping: dict[str, str] = {}

    if not cleaned:
        return mapping

    # 1. Embedding on ALL names (YAML is naming hint, not pre-filter)
    from packages.compiler.embedding_client import embed_batch
    embeddings = embed_batch(cleaned)

    # 2. Clustering
    from packages.compiler.clustering import cluster_by_cosine
    threshold = 0.78
    raw_clusters = cluster_by_cosine(cleaned, embeddings, threshold=threshold)
    tightened_clusters = _tighten_oversize_embedding_clusters(
        cleaned,
        embeddings,
        raw_clusters,
        threshold=threshold,
    )
    clusters = _split_clusters_by_facet(tightened_clusters, facet_hints or {})
    clusters = _recluster_compatible_facet_clusters(
        clusters,
        cleaned,
        embeddings,
        facet_hints or {},
        threshold=threshold,
    )
    _dump_embedding_cluster_trace(
        cleaned,
        clusters,
        threshold=threshold,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
        raw_clusters=raw_clusters,
    )

    # 3. Terminology YAML as naming hint (not grouping)
    terminology = _load_terminology()
    yaml_name_to_key = {}
    for ck, aliases in terminology.items():
        for a in aliases:
            yaml_name_to_key[a] = ck

    # 4. Per-cluster resolution
    domain_slug = _slugify_part(domain_id)
    equipment_slug = _slugify_part(equipment_class_id)
    type_prefix = _knowledge_type_prefix(knowledge_object_type)

    for cluster_names in clusters:
        if len(cluster_names) == 1:
            n = cluster_names[0]
            yaml_key = yaml_name_to_key.get(n)
            if yaml_key:
                ck = f"{domain_slug}:{equipment_slug}:{type_prefix}:{yaml_key}"
            else:
                slug = _slugify_part(n) or _hashed_slug(n)
                ck = f"{domain_slug}:{equipment_slug}:{type_prefix}:{slug}"
            mapping[n] = ck
            _register([n], ck)
        elif len(cluster_names) <= 100:
            # N3: trust embedding cluster. Prefer YAML key as canonical_key name.
            yaml_ck = None
            for n in cluster_names:
                if n in yaml_name_to_key:
                    yaml_ck = yaml_name_to_key[n]
                    break
            if yaml_ck:
                ck = f"{domain_slug}:{equipment_slug}:{type_prefix}:{yaml_ck}"
            else:
                suggested_ck = _slugify_part(cluster_names[0]) or _hashed_slug(cluster_names[0])
                ck = f"{domain_slug}:{equipment_slug}:{type_prefix}:{suggested_ck}"
            for n in cluster_names:
                mapping[n] = ck
            _register(cluster_names, ck)
        else:
            # Oversize cluster (>100): trust embedding, use best YAML name as key
            yaml_ck = None
            for n in cluster_names:
                if n in yaml_name_to_key:
                    yaml_ck = yaml_name_to_key[n]
                    break
            if yaml_ck:
                ck = f"{domain_slug}:{equipment_slug}:{type_prefix}:{yaml_ck}"
            else:
                suggested_ck = _slugify_part(cluster_names[0]) or _hashed_slug(cluster_names[0])
                ck = f"{domain_slug}:{equipment_slug}:{type_prefix}:{suggested_ck}"
            for n in cluster_names:
                mapping[n] = ck
            _register(cluster_names, ck)

    _dump_grouping_trace(
        names=cleaned,
        embeddings=embeddings,
        threshold=threshold,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
        facet_hints=facet_hints or {},
        raw_clusters=raw_clusters,
        tightened_clusters=tightened_clusters,
        facet_clusters=clusters,
        mapping=mapping,
    )
    HASH_CACHE[_hash_inputs(cleaned, knowledge_object_type, facet_hints)] = mapping
    return mapping


def _split_clusters_by_facet(
    clusters: list[list[str]],
    facet_hints: dict[str, Any],
) -> list[list[str]]:
    """Split embedding clusters when known unit facets are dimensionally incompatible."""

    refined: list[list[str]] = []
    for cluster in clusters:
        quantity_groups = _split_by_quantity(cluster, facet_hints)
        for quantity_group in quantity_groups:
            refined.extend(_split_by_subtype(quantity_group, facet_hints))
    return refined


def _facet_quantity(hint: Any) -> str | None:
    if isinstance(hint, (list, tuple)):
        return str(hint[0]) if hint and hint[0] else None
    return str(hint) if hint else None


def _facet_subtype(hint: Any) -> str | None:
    if isinstance(hint, (list, tuple)) and len(hint) > 1:
        return str(hint[1]) if hint[1] else None
    return None


def _split_by_quantity(cluster: list[str], facet_hints: dict[str, Any]) -> list[list[str]]:
    known_quantities = {
        _facet_quantity(facet_hints.get(name))
        for name in cluster
        if _facet_quantity(facet_hints.get(name))
    }
    if len(known_quantities) < 2:
        return [cluster]

    by_quantity: dict[str, list[str]] = {}
    unknown: list[str] = []
    for name in cluster:
        quantity = _facet_quantity(facet_hints.get(name))
        if quantity:
            by_quantity.setdefault(quantity, []).append(name)
        else:
            unknown.append(name)
    groups = list(by_quantity.values())
    if unknown:
        groups.append(unknown)
    return groups


def _split_by_subtype(cluster: list[str], facet_hints: dict[str, Any]) -> list[list[str]]:
    known_subtypes = {
        _facet_subtype(facet_hints.get(name))
        for name in cluster
        if _facet_subtype(facet_hints.get(name))
    }
    has_unknown_subtype = any(
        _facet_quantity(facet_hints.get(name)) and not _facet_subtype(facet_hints.get(name))
        for name in cluster
    )
    if len(known_subtypes) < 2 or has_unknown_subtype:
        return [cluster]

    by_subtype: dict[str, list[str]] = {}
    for name in cluster:
        subtype = _facet_subtype(facet_hints.get(name))
        if subtype:
            by_subtype.setdefault(subtype, []).append(name)
        else:
            return [cluster]
    return list(by_subtype.values())


def _recluster_compatible_facet_clusters(
    clusters: list[list[str]],
    names: list[str],
    embeddings: list[list[float]],
    facet_hints: dict[str, Any],
    *,
    threshold: float,
) -> list[list[str]]:
    """Reconnect split fragments that have the same known facet/subtype."""

    index_by_name = {name: idx for idx, name in enumerate(names)}
    grouped: dict[tuple[str, str | None], list[str]] = {}
    passthrough: list[list[str]] = []
    for cluster in clusters:
        keys = {_facet_group_key(name, facet_hints) for name in cluster}
        keys.discard(None)
        if len(keys) == 1:
            key = next(iter(keys))
            if all(_facet_group_key(name, facet_hints) == key for name in cluster):
                grouped.setdefault(key, []).extend(cluster)
                continue
        passthrough.append(cluster)

    reclustered: list[list[str]] = []
    from packages.compiler.clustering import cluster_by_cosine
    for names_in_group in grouped.values():
        deduped = list(dict.fromkeys(names_in_group))
        if len(deduped) <= 1:
            reclustered.append(deduped)
            continue
        indices = [index_by_name[name] for name in deduped]
        sub_embeddings = [embeddings[idx] for idx in indices]
        reclustered.extend(cluster_by_cosine(deduped, sub_embeddings, threshold=threshold))
    return passthrough + reclustered


def _facet_group_key(name: str, facet_hints: dict[str, Any]) -> tuple[str, str] | None:
    hint = facet_hints.get(name)
    subtype = _facet_subtype(hint)
    if subtype:
        return "subtype", subtype
    quantity = _facet_quantity(hint)
    if not quantity:
        return None
    return "quantity", quantity


USE_EMBEDDING_FIRST = os.environ.get("KNOWFABRIC_USE_EMBEDDING_FIRST", "1") == "1"


def group_and_normalize(
    names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
    facet_hints: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Group names by concept and normalize each group to a canonical key.

    H2 (docs/39): embedding-first by default (BGE-M3 → cosine clustering → LLM refine).
    Set KNOWFABRIC_USE_EMBEDDING_FIRST=0 for E2 batched-LLM fallback.
    """
    cleaned = [str(n).strip() for n in names if str(n).strip()]
    if not cleaned:
        return {}

    input_hash = _hash_inputs(cleaned, knowledge_object_type, facet_hints)
    if input_hash in HASH_CACHE:
        cached = HASH_CACHE[input_hash]
        if isinstance(cached, dict):
            return cached

    if USE_EMBEDDING_FIRST:
        return _group_via_embedding(
            cleaned,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
            backend_name=backend_name,
            facet_hints=facet_hints,
        )

    # Fallback: E2 batched-LLM with sanity checks
    all_groups: list[dict[str, Any]] = []
    for i in range(0, len(cleaned), BATCH_SIZE):
        batch = cleaned[i:i + BATCH_SIZE]
        batch_groups = _llm_group_and_normalize(
            batch, domain_id=domain_id, equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type, backend_name=backend_name,
        )
        batch_groups = _sanity_check_groups(batch_groups)
        batch_groups = _split_conflicting_groups(batch_groups, domain_id, equipment_class_id, knowledge_object_type)
        all_groups.extend(batch_groups)

    mapping: dict[str, str] = {}
    for g in all_groups:
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
        cached = HASH_CACHE[input_hash]
        if isinstance(cached, str):
            return cached

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
        cached = HASH_CACHE[input_hash]
        if isinstance(cached, str):
            return cached

    # Check terminology YAML first (deterministic, human-reviewed)
    terminology = _load_terminology()
    for ck, aliases in terminology.items():
        if cleaned in aliases:
            key = f"{_slugify_part(domain_id)}:{_slugify_part(equipment_class_id)}:{_knowledge_type_prefix(knowledge_object_type)}:{ck}"
            HASH_CACHE[input_hash] = key
            return key

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
