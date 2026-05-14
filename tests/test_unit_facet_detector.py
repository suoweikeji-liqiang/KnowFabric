import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.compiler.unit_facet_detector import detect_unit_facet


def test_detects_pressure_differential_from_pressure_unit_and_name():
    assert detect_unit_facet("油压差范围", {"unit": "kPa"}) == "pressure_differential"


def test_detects_temperature_from_range_value_units():
    payload = {"range_min": "35℃", "range_max": "50℃"}
    assert detect_unit_facet("油温控制", payload) == "temperature"


def test_detects_temperature_from_summary_units():
    payload = {"summary": "正常运行供油温度应稳定在35～50℃。"}
    assert detect_unit_facet("供油温度范围", payload) == "temperature"


def test_detects_pressure_differential_from_summary_units():
    payload = {"summary": "正常运行供油压力比油箱压力高150～250kPa。"}
    assert detect_unit_facet("油压差范围（运行）", payload) == "pressure_differential"


def test_detects_time_from_value_unit():
    assert detect_unit_facet("Anti-Recycle Delay", {"value": "5 minute"}) == "time"


def test_unknown_unitless_spec_does_not_block_merge():
    assert detect_unit_facet("Generic Spec", {}) is None


def test_psid_is_pressure_differential():
    assert detect_unit_facet("Maximum Differential", {"unit": "psid"}) == "pressure_differential"
