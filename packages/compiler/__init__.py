"""Compiler helpers for authority candidate generation."""

from .contracts import (
    DEFAULT_COMPILER_VERSION,
    attach_internal_metadata,
    build_compile_metadata,
    extract_compile_metadata,
    extract_health_signals,
    public_health_flags,
)
from .llm_compiler import OpenAICompatibleBackend, backend_from_dict, default_backend
from .llm_compiler import DEFAULT_LLM_ENABLED_TYPES, default_enabled_llm_types, load_backend_configs, resolve_backend

__all__ = [
    "DEFAULT_COMPILER_VERSION",
    "DEFAULT_LLM_ENABLED_TYPES",
    "OpenAICompatibleBackend",
    "attach_internal_metadata",
    "backend_from_dict",
    "build_compile_metadata",
    "default_backend",
    "default_enabled_llm_types",
    "extract_compile_metadata",
    "extract_health_signals",
    "load_backend_configs",
    "public_health_flags",
    "resolve_backend",
]
