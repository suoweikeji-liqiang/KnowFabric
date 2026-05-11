# Merger Production Integration — Reject the "Corpus Gap" Misdiagnosis

**Status:** Action list — execute in order
**Last Updated:** 2026-05-11
**Audience:** Codex / executing agent
**Parent plan:** [docs/34_compile-gap-and-execution-plan.md](34_compile-gap-and-execution-plan.md), [docs/35_codex-followup-tasks.md](35_codex-followup-tasks.md)

---

## 0. 为什么开这一份

[docs/35 §D3](35_codex-followup-tasks.md) 跑完后，commit `e4956a8` 的 W3 D5 报告诊断结论是：

> D3: cross-brand merge blocked by corpus gap — Trane CVGF (EN) and McQuay (ZH) parameter sets have no semantic overlap. Need York/Carrier extraction for EN-EN cross-brand pairs.

**这个诊断是错的，而且错得离谱**。本文用 DB 真实数据反驳，并给出真正的根因 + 修复路径。

如果不纠正这个诊断，KnowFabric 会继续花时间"找更多英文手册"，而真正的 plumbing 问题继续被绕过。

---

## 1. 神话 vs 现实

| 神话（Codex W3 D5 报告 / 后续口头复述） | 现实（DB 真实数据） |
|---|---|
| "Trane EN + McQuay ZH，没有英文跨品牌可合并" | DB 里 chiller parameter_spec KO **来自 4 本 manual**：Trane CVGF / Carrier 19XR / 麦克维尔 × 2 |
| "Carrier 是中文" | Carrier 19XR 的 15 条 KO **全部是英文 parameter_name** |
| "Trane 是英文" | Trane CVGF 的 25 条 KO **是中英混合**（英文 setpoint + 中文系统术语） |
| "代码基础设施全部就绪" | `merge_with_existing` 和 `merge_candidates` **生产代码 0 次调用**，只在 tests 里有 |
| "缺英文品牌手册" | 跨品牌同概念明显存在（见 §2.2），缺的是把 merger 接入产线 |

---

## 2. 硬证据

### 2.1 Carrier 19XR 是纯英文，且 canonical_key 全是 hash fallback

DB 查询（`packages.db.models_v2.KnowledgeObjectV2` JOIN `KnowledgeObjectEvidenceV2`，filter `doc_id='doc_55e5ec4e4ee84e9a'`）：

```
pname="Evaporator Leaving Water Temperature Setpoint"
  canonical_key=hvac:centrifugal_chiller:parameter:080e0fbc99
pname="Oil Sump Temperature Limit"
  canonical_key=hvac:centrifugal_chiller:parameter:128f938ca8
pname="High Pressure Cutout"
  canonical_key=hvac:centrifugal_chiller:parameter:23b62395c5
pname="Motor Current Limit"
  canonical_key=hvac:centrifugal_chiller:parameter:bf2cb6624f
pname="Condenser Leaving Water Temperature Setpoint"
  canonical_key=hvac:centrifugal_chiller:parameter:f479eee225
...（共 15 条，全部英文 parameter_name，全部 hash canonical_key）
```

**hash 形式的 canonical_key（如 `080e0fbc99`）是 [packages/compiler/canonical_key.py](../packages/compiler/canonical_key.py) 的 `_hashed_slug` mechanical fallback**。它出现在 DB 里只能说明一件事：**这些 KO 落库时根本没经过 `group_and_normalize`**。

### 2.2 跨品牌同概念明显存在

把 Trane CVGF 的英文参数和 Carrier 19XR 的英文参数对照：

| 概念 | Trane CVGF | Carrier 19XR |
|------|-----------|--------------|
| 冷冻水出水温度设定 | `External Chilled Water Setpoint` / `Front Panel Chilled Water Setpoint` | `Evaporator Leaving Water Temperature Setpoint` |
| 电流限制 | `External Current Limit Setpoint` / `Front Panel Current Limit Setpoint` | `Motor Current Limit` |
| 冷凝侧出水温度 | （Trane CVGF 控制项里没显式列） | `Condenser Leaving Water Temperature Setpoint` |
| 油压差 | （Trane 自动管理）  | `Oil Pressure Differential Setpoint` |

这些英文参数名**完全有语义重叠**。LLM grouping 把它们送进 `group_and_normalize` 一定能识别同概念。

### 2.3 Trane CVGF 本身是中英混合

```
pname="容量控制软载时间"        ← 中文
pname="Front Panel Chilled Water Setpoint"   ← 英文
pname="电流限制控制软载时间"     ← 中文
pname="External Current Limit Setpoint"      ← 英文
pname="滤波器时间"              ← 中文
pname="External Chilled Water Setpoint"      ← 英文
pname="最大容量限制"            ← 中文
pname="Outdoor Maximum Reset"   ← 英文
```

Codex 在 W3 D5 报告中假定 "Trane (EN)" 是事实错误。

### 2.4 merger 生产代码 0 次调用

```bash
$ grep -rn "merge_with_existing\|merge_candidates" /scripts/ /packages/ \
    --exclude-dir=__pycache__
packages/compiler/cross_source_merger.py: (函数定义本身)
tests/test_cross_source_merger.py: (测试)
tests/test_cross_source_merger_crosslingual.py: (测试)
```

**`scripts/apply_review_packs_batch.py`、`scripts/apply_ready_review_bundle.py`、`packages/review/applier.py` 一处都没调 merger**。

W3 D5 跑出的 5 个 multi-layer KO 是**一次性 hack 跑批**的 artifact，**不是产线 capability 的证明**。

### 2.5 历史 KO 大多用 mechanical canonical_key 落库

`centrifugal_chiller` 79 个 parameter_spec KO 的 canonical_key 模式：

- Trane CVGF 25 条：人读式 (`chilled_water_setpoint`、`outdoor_maximum_reset` 等) —— **这是 W3 D5 hack 跑批过 merger 出的少数 KO**
- Carrier 19XR 15 条：**全 hash** (`080e0fbc99` 等)
- 麦克维尔 11 + 5 条：**全 hash**（一两条例外）

**80% 的历史 KO 是 mechanical canonical_key，永远不会跟新候选合并**，哪怕 merger 之后接入产线也无法救它们 —— 必须重建 canonical_key。

---

## 3. 真正的根因

跨源合并不发生**不是因为缺手册**，而是因为：

### 3.1 merger 没接入产线

[scripts/apply_review_packs_batch.py](../scripts/apply_review_packs_batch.py) / [scripts/apply_ready_review_bundle.py](../scripts/apply_ready_review_bundle.py) 当前流程：

```
review-pack candidates
  → 直接 INSERT INTO knowledge_object (canonical_key=candidate.canonical_key_candidate, ...)
  → 直接 INSERT INTO knowledge_object_evidence (...)
```

**没有任何一步调 `merge_with_existing` 或 `merge_candidates`**。所以：

- 每本 manual 的候选独立落 KO
- 同概念在 5 本 manual 出现 → 落 5 个独立 KO（不合并）
- 落库时 candidate.canonical_key_candidate 已经是 mechanical 形式（per-doc 抽取阶段产生）

### 3.2 历史 KO 的 canonical_key 是 mechanical fallback

即使 merger 接入产线，[packages/compiler/cross_source_merger.py:344-356](../packages/compiler/cross_source_merger.py:344) 的 update/insert 判定用 `canonical_key in ko_id_map`：

```python
for ko_dict in merged:
    canonical_key = ko_dict["canonical_key"]
    if canonical_key in ko_id_map:        # ← 用 canonical_key 匹配老 KO
        ko_dict["knowledge_object_id"] = ko_id_map[canonical_key]
        stats["updated_existing"] += 1
    else:
        ko_dict["knowledge_object_id"] = _generate_ko_id(...)
        stats["new_merged"] += 1
```

LLM grouping 新跑出的 canonical_key 跟老 KO 当年用 mechanical 存的 canonical_key **不一致** → 永远走 INSERT 分支 → DB 膨胀（同概念产生 2 份 KO）。

---

## 4. 修复路径

按依赖排：F → E → G。

### 4.1 任务 F：历史 KO 的 canonical_key 全量重建（必须先做，半天）

**目标**：让 DB 里所有现存 KO 的 canonical_key 都经过一次 `group_and_normalize`，建立可用的 canonical_key 全局映射。

**操作**：

新建 `scripts/rebuild_canonical_keys.py`：

```python
"""One-shot job: rebuild canonical_key for all existing KOs by running them
through group_and_normalize per (ontology_class_id, knowledge_object_type) bucket."""

from packages.compiler.canonical_key import group_and_normalize
from packages.db.models_v2 import KnowledgeObjectV2
from packages.db.session import SessionLocal

def main():
    db = SessionLocal()
    # Group KOs by (anchor, type)
    buckets = {}
    for ko in db.query(KnowledgeObjectV2).all():
        key = (ko.ontology_class_id, ko.knowledge_object_type)
        buckets.setdefault(key, []).append(ko)

    for (anchor, ko_type), kos in buckets.items():
        names = [
            (ko.structured_payload_json or {}).get("parameter_name")
            or (ko.structured_payload_json or {}).get("title")
            or ko.title or ko.canonical_key
            for ko in kos
        ]
        # LLM-grouped canonical_keys
        mapping = group_and_normalize(
            names=names,
            domain_id="hvac",
            equipment_class_id=anchor,
            knowledge_object_type=ko_type,
            backend_name="mimo-compiler",
        )
        # Update each KO's canonical_key to LLM-resolved value
        for ko, name in zip(kos, names):
            new_ck = mapping.get(name)
            if new_ck and new_ck != ko.canonical_key:
                print(f"{ko.knowledge_object_id}: {ko.canonical_key} -> {new_ck}")
                ko.canonical_key = new_ck
        db.commit()
```

**治理纪律例外**：[docs/34 §6](34_compile-gap-and-execution-plan.md) 治理纪律 2 写明 "canonical_key 一经发布永不改"。本文档特批一次性例外，理由：现存 KO 的 canonical_key **80% 是 mechanical hash fallback，不属于"权威发布"**，重建不会破坏下游引用稳定性（下游目前还没真消费 KO ID）。重建完成后，治理纪律 2 恢复生效。

**Done means**：

- 跑完后 DB 里 chiller parameter_spec 的 79 个 KO 数量**显著减少**（同概念被合并）
- 没有 `hash` 形式的 canonical_key（grep canonical_key 全部是 `^hvac:[a-z_]+:[a-z_]+:[a-z_]+$` 形式）
- 至少 1 个新 KO 的 `authority_layers` 长度 ≥ 2 且 publishers 跨品牌（Trane + Carrier 至少 1 对）

### 4.2 任务 E：把 merger 接入生产 apply 路径（1 天）

**目标**：让 `scripts/apply_review_packs_batch.py` / `scripts/apply_ready_review_bundle.py` 走 `merge_with_existing` 落库，而不是直接 INSERT。

**修改 [scripts/apply_review_packs_batch.py](../scripts/apply_review_packs_batch.py)**：

定位 candidate → KO 落库的核心循环。改为：

```python
from packages.compiler.cross_source_merger import merge_with_existing
from collections import defaultdict

def apply_review_pack(pack_path, db, ...):
    bundle = load_review_pack(pack_path)
    verified = [c for c in bundle.candidates if c.review_decision == "accepted"]

    # Group by (ontology_class_id, knowledge_object_type)
    grouped = defaultdict(list)
    for cand in verified:
        cand_dict = candidate_to_merger_dict(cand)  # 转换为 merger 期望的 dict 形式
        key = (
            cand.equipment_class_candidate.equipment_class_id,
            cand.knowledge_object_type,
        )
        grouped[key].append(cand_dict)

    total_stats = {"new_merged": 0, "updated_existing": 0, "material_conflicts": 0}
    for (anchor, ko_type), candidates in grouped.items():
        stats = merge_with_existing(
            session=db,
            new_candidates=candidates,
            domain_id="hvac",
            equipment_class_id=anchor,
            ontology_class_key=f"hvac:{anchor}",
            knowledge_object_type=ko_type,
            backend_name="mimo-compiler",
        )
        for k, v in stats.items():
            total_stats[k] += v
    return total_stats
```

`candidate_to_merger_dict` 转换函数必须确保：
- `evidence[]` 数组里每条有 `doc_id` (doc_xxx 格式)、`chunk_id`、`page_id`、`page_no`、`evidence_text`
- 顶层有 `parameter_name` 或 `title`（merger 提取 names 用）
- 顶层有 `authority_level`、`publisher`、`citation`（merger 构造 authority_layer 用）
- 顶层有 `confidence_score`、`trust_level`

**[scripts/apply_ready_review_bundle.py](../scripts/apply_ready_review_bundle.py)** 同样改造。

**Done means**：

- apply 一次 review-pack 后，DB 里 KO 数量不再线性增长（同概念被合并）
- `scripts/apply_review_packs_batch.py` thin CLI ≤ 100 行（业务逻辑抽到 [packages/review/applier.py](../packages/review/applier.py)）
- `pytest tests/test_apply_review*.py` 全过（必要时改 fixture 适应新合并行为）

### 4.3 任务 G：跨品牌合并真实回测（半天）

**目标**：证明 E + F 后，DB 里至少 3 个 multi-layer KO 跨**真正不同的品牌**。

**操作**：

1. 跑 F (rebuild_canonical_keys.py)
2. 跑 E 改后的 apply 路径，重 apply 一次 chiller 的所有 review-packs（Trane CVGF + Carrier 19XR + 麦克维尔 × 2）
3. SQL 验证：

```sql
-- Multi-layer KOs with cross-brand publishers
SELECT canonical_key,
       jsonb_array_length(authority_summary_json->'layers') AS n_layers,
       (SELECT array_agg(DISTINCT layer->>'publisher')
        FROM jsonb_array_elements(authority_summary_json->'layers') layer
       ) AS publishers
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND jsonb_array_length(authority_summary_json->'layers') >= 2;
```

**期望产出**：

| 必须满足 | 目标 |
|---------|------|
| Cross-brand multi-layer KOs (publishers 数组长度 ≥ 2 且含 ≥ 2 个不同品牌) | ≥ 3 条 |
| 例如 Trane + Carrier 合并的"冷冻水出水温度设定" | ≥ 1 条 |
| chiller parameter_spec 总 KO 数 | 显著低于 79（合并真发生） |

**更新 [output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md)**，写真数据，撤回 "corpus gap" 诊断。

---

## 5. 验收（本轮 done）

完成下列 5 条本轮才算关闭：

1. F：DB 里所有 KO 的 canonical_key 不再含 hash 形式（mechanical fallback 标志），全部为人读式
2. E：`scripts/apply_*` 调 `merge_with_existing` —— grep 必须找到调用
3. G：至少 3 条 cross-brand multi-layer KO 落库，其中 Trane + Carrier 至少 1 对
4. [output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md) 真数据更新，**撤回 D3 corpus gap 诊断**
5. `pytest tests/` 全过；`bash scripts/check-all` 全过

---

## 6. 不做的事

| 项目 | 为什么不做 |
|------|----------|
| 找更多英文品牌手册（York / Daikin 全量 ingest）| corpus 已经够；先解决产线 plumbing |
| 重写 docs/35 §D3 | 留作历史佐证（W3 D5 报告里 corpus gap 诊断错的过程） |
| 改 v0.2 契约字段 | 不动 |
| 跑大批量视觉 | 等 E + F + G 跑通再说 |
| 修复 W3 D5 hack 跑批的旧 artifact | 直接被 E + F 跑出的新数据替代 |
| Visual evidence 流程改动 | 跟本文无关 |

---

## 7. 给 Codex 的执行约束

1. **不要**继续诊断 corpus gap。本文已经证明 corpus 充足，再次给出"need more manuals"结论的 PR 一律 reject
2. F 必须先于 E（F 没跑过，E 跑会产生 DB 膨胀）
3. F 是一次性 job，跑完 commit 一次 canonical_key 重建记录
4. F 跑前 `pg_dump knowfabric > /tmp/pre_canonical_rebuild_backup.sql`
5. E 改 apply 路径时，先保留旧路径作 fallback（加 `--use-merger` flag 渐进切换），跑完 E 验证 OK 后删除旧路径
6. F 的 canonical_key 重命名属于本次特批例外。F 完成后治理纪律 2（canonical_key append-only）恢复生效。后续任何 canonical_key 改名一律拒绝
7. 任何 LLM 调用必须经过 `_request_json_completion`，不要新建 HTTP client
8. G 验证用真 SQL，不要用 unit test mock 数据
9. 如果 F 跑完之后 cross-brand 合并数仍 = 0，**先停下来不要再写代码**，dump 一份 `output/diagnostic/<run_id>/group_and_normalize_trace.jsonl`（每个 LLM 调用的 input/output）让操盘手审，**不要再次给出 corpus gap 诊断**

---

## 8. 一个常见的反向辩护（提前回应）

**辩护**：「Carrier 的参数名 hash 是因为它们语义上跟 Trane 不重叠，所以 LLM grouping 没找到 group」

**反驳**：

1. Carrier 的 hash canonical_key 是**单 candidate 走 `resolve_single_name` 的产物**，**不是** group_and_normalize 返回的结果。`_hashed_slug` 只在 `resolve_single_name` 找不到 stable mapping 且 slugify 也失败时才会用 —— 但 "Evaporator Leaving Water Temperature Setpoint" 这种英文 slugify 一定能产生 `evaporator_leaving_water_temperature_setpoint` 之类的人读 slug，**不会 fallback 到 hash**

2. 所以 hash canonical_key 的存在唯一可能解释：**Carrier 19XR 的 KO 落库时调的是某个不同的 canonical_key 生成路径**（可能是更早的 LLM compiler 老版本，或者临时的兜底逻辑），**完全没经过 group_and_normalize**

3. 把 Carrier 的 15 个英文参数名跟 Trane 的同类英文参数名一起送进 `group_and_normalize`，让 LLM 自己判断是不是同概念 —— 这是 F 任务的核心动作。如果 F 跑完 LLM 仍然把 Trane "External Chilled Water Setpoint" 和 Carrier "Evaporator Leaving Water Temperature Setpoint" 判为不同概念，那才有"corpus gap"或"prompt 工程"问题。**当前根本没跑过这一步，没有资格说 corpus gap**

---

## CHANGELOG

- **2026-05-11**：初稿。基于 commit `e4956a8` 后的 DB 真实数据，反驳 W3 D5 "corpus gap" 诊断，把跨源合并问题重定向为产线 plumbing 问题。E/F/G 三任务。
