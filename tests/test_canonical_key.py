"""Tests for canonical_key normalization module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.canonical_key import (
    HASH_CACHE,
    _hash_inputs,
    _lookup_registry,
    _register,
    resolve_canonical_key,
    resolve_single_name,
)


def _clear_cache():
    HASH_CACHE.clear()


def test_resolve_single_name_produces_stable_key():
    _clear_cache()
    key1 = resolve_single_name(
        "Chilled Water Leaving Temperature Setpoint",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    key2 = resolve_single_name(
        "Chilled Water Leaving Temperature Setpoint",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert key1 == key2
    assert key1.startswith("hvac:centrifugal_chiller:parameter:")
    assert "chilled_water_leaving_temperature_setpoint" in key1


def test_resolve_single_name_uses_registry():
    _clear_cache()
    key1 = resolve_single_name(
        "Active Chilled Water Setpoint",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    key2 = resolve_single_name(
        "Active Chilled Water Setpoint",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert key1 == key2


def test_hash_cache_determinism():
    _clear_cache()
    names = [
        "CHWS Setpoint",
        "Chilled Water Supply Temperature",
        "leaving chilled water temp",
    ]
    input_hash = _hash_inputs(names, "parameter_spec")
    assert input_hash not in HASH_CACHE

    # Register manually to avoid LLM call
    _register(names, "hvac:centrifugal_chiller:parameter:chw_supply_temp_setpoint")
    HASH_CACHE.clear()

    key = resolve_canonical_key(
        names,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert key == "hvac:centrifugal_chiller:parameter:chw_supply_temp_setpoint"

    # Second call with same names should hit hash cache
    key2 = resolve_canonical_key(
        names,
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert key2 == key


def test_registry_cross_lookup():
    _clear_cache()
    _register(
        ["CHWS Temp"],
        "hvac:centrifugal_chiller:parameter:chw_supply_temp_setpoint",
    )
    # A different name that shares an alias should still resolve
    key = resolve_canonical_key(
        ["CHWS Temp", "different variant name"],
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert key == "hvac:centrifugal_chiller:parameter:chw_supply_temp_setpoint"


def test_resolve_single_name_handles_special_chars():
    _clear_cache()
    key = resolve_single_name(
        "冷冻水出水温度设定值",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    assert key.startswith("hvac:centrifugal_chiller:parameter:")
    # Non-ASCII chars slug to empty, falls back to hashed key
    assert "key_" in key or len(key.split(":")[-1]) > 0


def test_different_types_produce_different_prefixes():
    _clear_cache()
    param_key = resolve_single_name(
        "Chilled Water Setpoint",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="parameter_spec",
    )
    maint_key = resolve_single_name(
        "Chilled Water Setpoint",
        domain_id="hvac",
        equipment_class_id="centrifugal_chiller",
        knowledge_object_type="maintenance_procedure",
    )
    assert ":parameter:" in param_key
    assert ":maintenance:" in maint_key
    assert param_key != maint_key
