"""Shared local LLM backend config loader for scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from packages.compiler.llm_compiler import OpenAICompatibleBackend, backend_from_dict

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKEND_CONFIG = REPO_ROOT / "scripts" / "llm_backends.json"
LOCAL_LLM_ENV = REPO_ROOT / ".env.llm.local"


def read_local_env(path: Path = LOCAL_LLM_ENV) -> dict[str, str]:
    """Read a simple KEY=value local env file without mutating process env."""

    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def load_backend(name: str, config_path: str | Path | None = None) -> tuple[OpenAICompatibleBackend, dict[str, Any]]:
    """Load one OpenAI-compatible backend by name from the shared script config."""

    path = Path(config_path) if config_path else DEFAULT_BACKEND_CONFIG
    data = json.loads(path.read_text(encoding="utf-8"))
    local_env = read_local_env()
    for item in data.get("backends", []):
        if item.get("name") == name:
            resolved = resolve_local_overrides(dict(item), local_env)
            return backend_from_dict(resolved), resolved
    raise ValueError(f"Backend '{name}' not found in {path}")


def resolve_local_overrides(item: dict[str, Any], local_env: dict[str, str]) -> dict[str, Any]:
    """Apply local secret/base-url overrides declared by *_env fields."""

    api_key_env = item.get("api_key_env")
    if api_key_env and not item.get("api_key"):
        item["api_key"] = os.getenv(str(api_key_env)) or local_env.get(str(api_key_env))

    api_base_env = item.get("api_base_url_env")
    if api_base_env:
        item["api_base_url"] = os.getenv(str(api_base_env)) or local_env.get(str(api_base_env)) or item.get("api_base_url")

    if is_mimo_backend(item):
        item["api_base_url"] = os.getenv("MIMO_API_BASE_URL") or local_env.get("MIMO_API_BASE_URL") or item.get("api_base_url")
    return item


def is_mimo_backend(item: dict[str, Any]) -> bool:
    name = str(item.get("name") or "").lower()
    model = str(item.get("model") or "").lower()
    return "mimo" in name or "mimo" in model
