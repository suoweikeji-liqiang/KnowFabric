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
