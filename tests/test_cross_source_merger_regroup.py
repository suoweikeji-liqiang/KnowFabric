"""Tests for regrouping persisted knowledge objects."""

from packages.compiler.cross_source_merger import _ko_to_candidates


class _Ko:
    title = "Oil Temperature Control"
    summary = "Oil temperature control summary."
    confidence_score = 0.9
    trust_level = "L2"
    review_status = "published"
    highest_authority_level = "manufacturer"
    knowledge_object_id = "ko_1"
    structured_payload_json = {"parameter_name": "Oil Temperature Control", "value": "48-52 C"}
    authority_summary_json = {
        "layers": [
            {
                "doc_id": "doc_gree",
                "publisher": "Gree",
                "citation": "Gree manual p.66",
                "authority_level": "manufacturer",
                "value_summary": "Oil Temperature Control",
            }
        ]
    }


class _Session:
    def query(self, _model):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return [
            type("Evidence", (), {
                "chunk_id": "chunk_1",
                "doc_id": "doc_gree",
                "page_id": "page_66",
                "page_no": 66,
                "evidence_text": (
                    "11 根据冷冻水出温和设定的 PID参数自动控制导叶开闭\n"
                    "正常运行供油温度应稳定在35～50℃。"
                ),
                "evidence_role": "primary_manufacturer",
            })()
        ]


def test_ko_to_candidates_keeps_structured_name_over_evidence_first_line() -> None:
    """Regroup must not rename KOs from noisy evidence text first lines."""

    candidates = _ko_to_candidates(_Ko(), session=_Session())

    assert candidates[0]["structured_payload"]["parameter_name"] == "Oil Temperature Control"
    assert candidates[0]["title"] == "Oil Temperature Control"
    assert candidates[0]["publisher"] == "Gree"


class _ValueSummaryKo:
    title = "30 psipsid"
    summary = "Maximum differential pressure setting."
    confidence_score = 0.9
    trust_level = "L3"
    review_status = "published"
    highest_authority_level = "manufacturer"
    knowledge_object_id = "ko_pressure"
    structured_payload_json = {
        "parameter_name": "最大压差设定值",
        "default_value": "30 psi",
        "unit": "psid",
    }
    authority_summary_json = {
        "layers": [
            {
                "doc_id": "doc_trane",
                "publisher": "Trane",
                "citation": "Trane p.43",
                "authority_level": "manufacturer",
                "value_summary": "30 psipsid",
            }
        ]
    }


class _ValueSummarySession:
    def query(self, _model):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return [
            type("Evidence", (), {
                "chunk_id": "chunk_pressure",
                "doc_id": "doc_trane",
                "page_id": "page_43",
                "page_no": 43,
                "evidence_text": "最大压差 标准设为30 psi",
                "evidence_role": "primary_manufacturer",
            })()
        ]


def test_ko_to_candidates_does_not_promote_value_summary_to_parameter_name() -> None:
    """Regroup names must come from source names, not value/default summaries."""

    candidates = _ko_to_candidates(_ValueSummaryKo(), session=_ValueSummarySession())

    assert candidates[0]["structured_payload"]["parameter_name"] == "最大压差设定值"
    assert candidates[0]["title"] == "最大压差设定值"


class _MultiLayerSameDocKo:
    title = "Oil group"
    summary = "Multiple parameters from one manual."
    confidence_score = 0.9
    trust_level = "L3"
    review_status = "published"
    highest_authority_level = "manufacturer"
    knowledge_object_id = "ko_multi"
    structured_payload_json = {"parameter_name": "供油温度范围"}
    authority_summary_json = {
        "layers": [
            {
                "doc_id": "doc_gree",
                "chunk_id": "chunk_temp",
                "publisher": "Gree",
                "source_name": "供油温度范围",
                "value_summary": "[35, 50]",
                "structured_payload": {
                    "parameter_name": "供油温度范围",
                    "range_min": "35",
                    "range_max": "50",
                    "unit": "C",
                },
            },
            {
                "doc_id": "doc_gree",
                "chunk_id": "chunk_pressure",
                "publisher": "Gree",
                "source_name": "油压差范围（运行）",
                "value_summary": "[150, 250]",
                "structured_payload": {
                    "parameter_name": "油压差范围（运行）",
                    "range_min": "150",
                    "range_max": "250",
                    "unit": "kPa",
                },
            },
        ]
    }


class _MultiLayerSameDocSession:
    def query(self, _model):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return [
            type("Evidence", (), {
                "chunk_id": "chunk_temp",
                "doc_id": "doc_gree",
                "page_id": "page_66",
                "page_no": 66,
                "evidence_text": "供油温度稳定，在35-50范围内",
                "evidence_role": "primary_manufacturer",
            })(),
            type("Evidence", (), {
                "chunk_id": "chunk_pressure",
                "doc_id": "doc_gree",
                "page_id": "page_66",
                "page_no": 66,
                "evidence_text": "供油压力比油箱压力高150-250kPa",
                "evidence_role": "supporting_manufacturer",
            })(),
        ]


def test_ko_to_candidates_matches_layers_by_chunk_not_only_doc() -> None:
    """Multiple layers from one document must keep their own source names."""

    candidates = _ko_to_candidates(_MultiLayerSameDocKo(), session=_MultiLayerSameDocSession())

    names = [candidate["structured_payload"]["parameter_name"] for candidate in candidates]
    assert names == ["供油温度范围", "油压差范围（运行）"]
    assert candidates[1]["structured_payload"]["range_min"] == "150"
    assert candidates[1]["structured_payload"]["unit"] == "kPa"


def test_ko_to_candidates_uses_layer_summary_when_expanding_overmerged_ko() -> None:
    """Expanded regroup candidates must not inherit stale aggregate KO summaries."""

    candidates = _ko_to_candidates(_MultiLayerSameDocKo(), session=_MultiLayerSameDocSession())

    assert candidates[0]["summary"] == "供油温度稳定，在35-50范围内"
    assert candidates[1]["summary"] == "供油压力比油箱压力高150-250kPa"
