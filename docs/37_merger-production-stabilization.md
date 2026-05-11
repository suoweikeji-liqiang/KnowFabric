# Merger Production Stabilization — Recover, Default-On, Fix Conflict Semantics

**Status:** Action list — execute in order
**Last Updated:** 2026-05-11
**Audience:** Codex / executing agent
**Parent plan:** [docs/36_merger-production-integration.md](36_merger-production-integration.md)

---

## 0. 为什么开这一份

[docs/36](36_merger-production-integration.md) 跑完后（commits `e734ff2`, `449045f`, `ae2edd8`）有一个真的突破：**KnowFabric 历史第一个真 cross-brand multi-layer KO 诞生**（`oil_temperature_control`: Trane 95°F + McQuay 32°C + McQuay 38°C, 3 layers）。

但跑通过程出 5 个新问题，需要本轮收尾：

1. **Carrier 19XR 的 15 条历史 KO 永久丢失**（F 任务跑前未备份、重抽失败）
2. **E 任务半完成**（加了 `--use-merger` flag 但默认 False，旧 INSERT 路径仍是默认）
3. **12 个 material_conflict 大部分是假阳性**（value 为空时被错判 conflict）
4. **唯一真 cross-brand KO 也被错判 material_conflict**（95°F vs 32-38°C 实际接近，缺单位换算）
5. **真 cross-brand 数量 1 个**（doc 36 §4.3 G 任务要求 ≥ 3）

本文档把这 5 件事拆成 R1-R5 任务，按依赖顺序执行。

执行完后 KnowFabric 才算"产线跨源合并稳定可用"，可以进入下一轮（规模化跑批 + sw_base_model 接入 smoke）。

---

## 1. 当前 DB 状态（事实快照）

```
=== chiller parameter_spec KOs by source doc ===
  Trane CVGF:    11 KOs   (was 25 before F)
  McQuay 主:     10 KOs   (was 11 before F)
  McQuay PE/WS:   9 KOs   (was 5 before F)
  Carrier 19XR:   0 KOs   ← was 15, all lost in F rebuild

=== consensus_state ===
  single_source:    736
  material_conflict: 12   ← all 12 are chiller multi-layer
  agreed:             0   ← suspicious
  partial_conflict:   0   ← suspicious

=== cross-publisher multi-layer KOs ===
  1 (oil_temperature_control: Trane + McQuay)

=== hash canonical_keys ===
  0  ← F task achievement, do not regress
```

---

## 2. R1：恢复 Carrier 19XR KOs（必须，1 天）

### 2.1 背景

Carrier 19XR (doc_id = `doc_55e5ec4e4ee84e9a`, file=`【开利】19XR离心机开机运行维护说明书97页-制冷百家网.pdf`) 在 F 任务前 DB 里有 15 条 chiller parameter_spec KO，全部是英文 parameter_name：

```
Evaporator Leaving Water Temperature Setpoint
Oil Sump Temperature Limit
Evaporator Approach Temperature
High Pressure Cutout
Low Pressure Cutout
Condenser Refrigerant High Pressure Setpoint
Chiller Capacity
Cooling Water Flow Rate
Evaporator Refrigerant Low Pressure Setpoint
Condenser Approach Temperature
Anti-Recycle Time Delay
Evaporator Water Pressure Drop
Motor Current Limit
Oil Pressure Differential Setpoint
Condenser Leaving Water Temperature Setpoint
```

操盘手确认无 DB backup，必须重抽。

### 2.2 重抽路径

文本 LLM 抽取已经失败（"scan-quality PDF with too little text"）。改用 **MiMo 视觉抽取** —— 这刚好是 [docs/34 §11](34_compile-gap-and-execution-plan.md) 视觉支线的目标场景，且 14 亿 MiMo 配额尚有 99% 余量。

**操作**：

1. 新建 `scripts/extract_kos_from_visual_pages.py`（或扩展现有 `scripts/run_visual_evidence_batch.py`），输入 doc_id + page 范围，对每一页：
   - 渲染 PNG（已有 `packages/extraction/page_renderer.py`）
   - 调 MiMo omni 多模态（已有 `packages/extraction/visual.py`），但 prompt 改为"抽取 chiller parameter_spec KO"而不是"分类页面"
   - 输出 candidate JSON（含 parameter_name / value / unit / evidence_quote / page_no / image_path）

**Prompt 模板**：

```
You are extracting configurable parameter specifications from a centrifugal chiller manual page image. Return strict JSON with shape:

{
  "candidates": [{
    "parameter_name": "...",
    "value": "...",
    "unit": "...",
    "range_min": "...",
    "range_max": "...",
    "default_value": "...",
    "description": "...",
    "evidence_quote": "verbatim visible text",
    "confidence": 0.0
  }]
}

Rules:
- Only extract configurable setpoints, limits, default values, range bounds, or mode selections an operator/commissioning engineer would set
- Skip component names, signal labels, marketing copy
- evidence_quote MUST be visible in the image (exact text)
- Return [] if page has no parameters
```

2. 跑 doc_55e5ec4e4ee84e9a 全 97 页（按 §2.4 配额，安全）
3. candidates 走 review pack → apply 路径（必须用 R2 完成后的 default-on merger，否则又会写成单 KO）

### 2.3 配额预算

97 pages × ~3k tokens/page = ~30万 tokens。占 §11 A 段 8.4 亿预算的 0.04%。完全在预算内。

### 2.4 Done means

- DB 查询 `SELECT COUNT(*) FROM knowledge_object_evidence WHERE doc_id='doc_55e5ec4e4ee84e9a' AND knowledge_object_id IN (SELECT knowledge_object_id FROM knowledge_object WHERE ontology_class_id='centrifugal_chiller')` 返回 ≥ 10
- 至少 1 个 KO 的 parameter_name 含 "Chilled Water" 或 "Leaving Water"（用于 R5 跨品牌验证）
- 抽出的 KO 必须经过 R2 完成后的 merger 路径落库（不是直接 INSERT）

### 2.5 风险

- MiMo 视觉抽 parameter_spec 准确率未验证 → 先跑 5 页 sample，操盘手抽审，再放开全 97 页
- 扫描 PDF 渲染分辨率不够 → 把渲染 DPI 提到 300 (page_renderer 检查并调高)
- 抽出来都是英文 parameter_name → 这正是我们要的（用于 cross-brand 合并）

---

## 3. R2：E 任务真完成（必须，半天）

### 3.1 现状

[scripts/apply_review_packs_batch.py:74](../scripts/apply_review_packs_batch.py:74)：

```python
def ..._apply(..., use_merger: bool = False, ...)
```

默认 `False`。意味着任何新 apply 默认走旧 INSERT 路径，跨源合并不发生。

W3 D5 REPORT 自己承认 "merge_candidates still not wired into production apply path (Task E)"。这跟 commit message "Task E+F complete" 自相矛盾。

### 3.2 操作

**Step 1**：把所有 `use_merger` 默认值改为 `True`。

涉及位置（grep `use_merger\s*[:=]\s*False`）：

```
scripts/apply_review_packs_batch.py:74    use_merger: bool = False, ...
scripts/apply_review_packs_batch.py:137   use_merger: bool = False, ...
scripts/apply_review_packs_batch.py:178   use_merger: bool = False, ...
scripts/apply_review_packs_batch.py:204   parser.add_argument("--use-merger", action="store_true", ...)
```

全部默认改 True。CLI flag 改为 `--no-merger` (action="store_false", 给极少数 emergency fallback 场景留口子)。

**Step 2**：删除旧 INSERT 路径。

`scripts/apply_review_packs_batch.py` 和 [packages/review/applier.py](../packages/review/applier.py) 里直接 `db.add(KnowledgeObjectV2(...))` 的代码全部删除。所有 KO 落库必须经 `apply_with_merger` → `merge_with_existing` → upsert。

如果有路径不走 merger（如 backfill 脚本），逐个评估：
- `backfill_authority_v02.py`：是一次性历史回填脚本，**保留**直接 INSERT（已经跑过，不会再跑）
- 其他 `apply_*` 脚本：必须走 merger

**Step 3**：更新现有 [tests/test_apply_review*.py](../tests/) 适应新默认。如有测试依赖旧 INSERT 行为，改为 merger 行为。

### 3.3 Done means

- `grep -n "use_merger" scripts/ packages/` 显示所有 default 都是 `True`
- `grep -rn "db.add(KnowledgeObjectV2\|session.add(KnowledgeObjectV2" scripts/ packages/` **不含**任何 apply 路径（只允许 backfill 脚本保留）
- 跑一次 `python scripts/apply_review_packs_batch.py <test pack>` (不传 flag) → 日志显示 `apply_with_merger ...` 被调
- `pytest tests/` 全过

---

## 4. R3：修 merger 的空值判定（必须，2 小时）

### 4.1 现状

12 个 multi-layer KO 全部 `material_conflict`、0 个 `agreed`、0 个 `partial_conflict`。这是 [packages/compiler/cross_source_merger.py](../packages/compiler/cross_source_merger.py) `_values_agree` / `_compute_consensus_state` 的 bug：

当多个 candidates 的 value 字段都是空（即只有 parameter_name 没有具体数值时），merger 应该判 `single_value_unknown`（或 `agreed_no_data`），不是 `material_conflict`。

material_conflict 应该只在**有真值且差异显著**时触发。

### 4.2 操作

改 [packages/compiler/cross_source_merger.py](../packages/compiler/cross_source_merger.py):

**`_values_agree` 逻辑增加空值短路**：

```python
def _values_agree(v1: Any, v2: Any) -> bool:
    # 新增：双方都空 → 算 agree (无数据可比，但不冲突)
    if _is_empty(v1) and _is_empty(v2):
        return True
    # 新增：一方空 → 算 agree (用有数据那方)
    if _is_empty(v1) or _is_empty(v2):
        return True
    # ... 原有数值/字符串比较逻辑

def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.lower() in ("none", "null", "n/a", "-")
```

**`_compute_consensus_state` 新增 `single_value_unknown` 状态**：

```python
def _compute_consensus_state(layers: list[dict[str, Any]]) -> tuple[str, str | None]:
    if len(layers) == 1:
        return "single_source", None

    values = [l.get("value_summary") for l in layers]
    non_empty = [v for v in values if not _is_empty(v)]

    # 新增：所有 layer 都没真值 → single_value_unknown
    if len(non_empty) == 0:
        return "single_value_unknown", "all sources lack explicit values; only parameter name confirmed"

    # 新增：只有 1 个 layer 有值 → 当作 agreed（缺数据不算冲突）
    if len(non_empty) == 1:
        return "agreed", None

    # 原有逻辑：多 layer 有真值 → 走 agreed / partial_conflict / material_conflict
    ...
```

如果 `consensus_state` 字段是 enum 且 schema 限制，需要 migration 加 `single_value_unknown` 到允许值。

### 4.3 Done means

- 重跑 R5 回测后：12 个 material_conflict 中**多数转为 `single_value_unknown` 或 `agreed`**
- 只有真正有差异的（如 oil_temperature_control 不同温度值）保留 `material_conflict` / `partial_conflict`
- DB 查询 `SELECT consensus_state, COUNT(*) FROM knowledge_object GROUP BY consensus_state` 应该有 ≥ 3 种状态而不是 2 种

---

## 5. R4：单位换算（必须，3 小时）

### 5.1 现状

唯一真 cross-brand KO `oil_temperature_control` 被错判 `material_conflict`：

```
Trane:  "95°F"   = 35°C
McQuay: "32°C"
McQuay: "38°C"
```

95°F 实际跟 32-38°C 接近，应该是 `partial_conflict` 或 `agreed_with_unit_normalization`，不是 `material_conflict`。

merger 没有单位换算逻辑。

### 5.2 操作

新建 `packages/compiler/unit_normalize.py`：

```python
"""Normalize values with units to canonical form for consensus comparison."""

import re
from typing import Optional

# 温度：内部 canonical = °C
def normalize_temperature(value_str: str) -> Optional[float]:
    """Parse '95°F' / '95 F' / '32°C' / '38°C' / '95F' etc., return °C."""
    s = value_str.strip().lower().replace(" ", "")
    m = re.match(r"^(-?\d+\.?\d*)°?([fc])$", s)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2)
    if unit == "f":
        return (num - 32) * 5 / 9
    return num

# 压力：内部 canonical = bar
def normalize_pressure(value_str: str) -> Optional[float]:
    """Parse '120 psi' / '8.3 bar' / '120psi' etc., return bar."""
    s = value_str.strip().lower().replace(" ", "")
    m = re.match(r"^(\d+\.?\d*)(psi|bar|mpa|kpa)$", s)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2)
    if unit == "psi":
        return num * 0.0689476
    if unit == "mpa":
        return num * 10
    if unit == "kpa":
        return num / 100
    return num

# 流量：内部 canonical = L/s (扩展用)
# 时间：内部 canonical = seconds (扩展用)
```

改 [packages/compiler/cross_source_merger.py](../packages/compiler/cross_source_merger.py) `_values_agree`：

```python
from packages.compiler.unit_normalize import normalize_temperature, normalize_pressure

def _values_agree(v1: Any, v2: Any) -> bool:
    if _is_empty(v1) and _is_empty(v2): return True
    if _is_empty(v1) or _is_empty(v2): return True

    s1, s2 = str(v1).strip(), str(v2).strip()
    if s1 == s2: return True

    # 新增：试温度单位换算
    t1, t2 = normalize_temperature(s1), normalize_temperature(s2)
    if t1 is not None and t2 is not None:
        return abs(t1 - t2) / max(abs(t1), abs(t2), 1.0) <= 0.10  # ±10%

    # 新增：试压力单位换算
    p1, p2 = normalize_pressure(s1), normalize_pressure(s2)
    if p1 is not None and p2 is not None:
        return abs(p1 - p2) / max(abs(p1), abs(p2), 1.0) <= 0.10

    # ... 原有数值比较逻辑
```

### 5.3 Done means

- 跑测试：`assert _values_agree("95°F", "35°C") == True`（95F = 35C，±10% 内）
- 跑测试：`assert _values_agree("95°F", "32°C") == True`（95F = 35C，距离 32C 约 8.6%，±10% 内）
- 跑测试：`assert _values_agree("100°F", "50°C") == False`（100F = 37.8C，距离 50C 约 24%，超 ±10%）
- 重跑回测后 `oil_temperature_control` 的 consensus_state 从 `material_conflict` 变成 `agreed` 或 `partial_conflict`

### 5.4 注意

- 只做温度和压力两种单位（chiller 域最常用），其他单位（流量 / 时间 / 容量）留下一轮
- 不要在 unit_normalize.py 里做太多花活；保持简单可测试
- ±10% 容差是初始值，靠回测调整

---

## 6. R5：真 cross-brand 验证（必须，半天）

### 6.1 前置

R1 + R2 + R3 + R4 全部完成。

### 6.2 操作

1. 跑 `scripts/extract_kos_from_visual_pages.py --doc-id doc_55e5ec4e4ee84e9a` 完整重抽 Carrier 19XR
2. apply 通过 R2 default-on merger 路径
3. SQL 验证：

```sql
-- Cross-brand multi-layer KOs
SELECT canonical_key,
       jsonb_array_length(authority_summary_json->'layers') AS n_layers,
       (SELECT array_agg(DISTINCT layer->>'publisher')
        FROM jsonb_array_elements(authority_summary_json->'layers') layer
       ) AS publishers,
       consensus_state
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND jsonb_array_length(authority_summary_json->'layers') >= 2
  AND (SELECT COUNT(DISTINCT layer->>'publisher')
       FROM jsonb_array_elements(authority_summary_json->'layers') layer
      ) >= 2
ORDER BY n_layers DESC;
```

### 6.3 Done means（硬指标）

| 指标 | 目标 |
|------|------|
| cross-publisher multi-layer KOs (publishers 数 ≥ 2 个不同品牌) | **≥ 3 条** |
| 含 Trane + Carrier 合并的 KO（如冷冻水设定相关） | ≥ 1 条 |
| chiller parameter_spec 总 KO 数（30 + Carrier 重抽） | 显著小于 45（合并真发生） |
| consensus_state 分布有 ≥ 3 种状态 | 不再全是 material_conflict |

### 6.4 更新报告

更新 [output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md)：

- 撤回顶部口径与底部 "Remaining" 的自相矛盾
- 列出 ≥ 3 条 cross-brand KO 的实际数据（publishers、values、consensus_state）
- 写明 doc 36 §4.3 G 任务真正达标

---

## 7. 验收（本轮 done）

完成下列 7 条本轮才算关闭：

1. **R1**: Carrier 19XR 至少 10 条 chiller parameter_spec KO 重建到 DB（且来自 MiMo 视觉抽取流程）
2. **R2**: `use_merger` 全部默认 True；apply 路径无直接 INSERT 痕迹；`--no-merger` 是 opt-out
3. **R3**: merger 空值判定加 `single_value_unknown` + `agreed` 短路；重跑后多数假阳性消失
4. **R4**: 温度 / 压力单位换算到位；`_values_agree("95°F", "32°C")` 单测过
5. **R5**: cross-publisher multi-layer KOs **≥ 3 条**（硬指标）；含 ≥ 1 条 Trane + Carrier 合并
6. `pytest tests/` 全过；`bash scripts/check-all` 全过
7. [output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md) 真数据更新，去掉自相矛盾

---

## 8. 不做的事（防止散）

| 项目 | 为什么不做 |
|------|----------|
| 大批量 ingest 新 manual | 先把 Carrier 19XR 恢复 + 跨品牌验证 ≥ 3 条 |
| 重写 docs/26 / docs/35 / docs/36 | 留作历史佐证 |
| 改 v0.2 契约字段 | 不动 |
| 跑大批量 MiMo 视觉抽 page_image (§11 主线) | 等 R1 验证 MiMo 视觉抽 parameter_spec 准确率可接受后再说 |
| 加流量 / 时间 / 容量等其他单位换算 | 留下一轮，R4 只做温度 + 压力 |
| 重构 health checks 跑批入口 | 跟本文无关 |
| 概念片合成实验（§11.6 D5）| 等本轮关闭 |

---

## 9. 给 Codex 的执行约束

1. **F 任务的教训**：删数据前必须 `pg_dump knowfabric > /tmp/<task>_backup_<date>.sql`。本轮 R1 之前 dump 一次（虽然 Carrier 当前已经空了，dump 是保留新增数据的安全网）

2. **R2 的 done 判据是"默认行为变了"，不是"加了 flag"**。如果再次提交"加了 --use-merger flag 但默认 False"，直接 reject。所有 default 都必须 True 才算 R2 done

3. **R1 的 done 判据是"DB 里 Carrier 19XR 有 ≥10 条 KO"**，不是"脚本写完跑过"。必须 SQL 验证

4. **R5 的 done 判据是"cross-publisher KO ≥ 3 条"**，不是"multi-layer KO ≥ 3 条"。**publishers 数组必须含 ≥ 2 个不同的品牌**才算数。同 publisher 内合并不算

5. **R3 + R4 的 done 判据要看实际 KO 的 consensus_state 变化**，不只看单测过。重跑回测后 `oil_temperature_control` 必须从 material_conflict 变成 agreed/partial_conflict

6. R1 用 MiMo 视觉抽取**必须走 `packages/extraction/visual.py` 的 `_request_json_completion`**，不要新建 HTTP client

7. R1 输出的 candidates 必须经过 R2 完成后的 merger 路径落库，**不能用旧 INSERT 路径**。所以 R2 必须先于 R1 完成。**执行顺序：R2 → R3 → R4 → R1 → R5**

8. R1 之前先跑 5 页 sample 抽审准确率；准确率 ≥ 70% 才放开全 97 页

9. 任何新加的 consensus_state 枚举值（如 `single_value_unknown`）需要看 schema 是否允许；如不允许走 migration

10. 不要再给"corpus gap"诊断。corpus 足够，问题在产线 plumbing + 数据语义。再次给出"need more manuals"结论的 PR 一律 reject

---

## 10. 执行顺序

```
R2 (E 完成)
  ↓
R3 (空值判定)
  ↓
R4 (单位换算)
  ↓
R1 (Carrier 重抽，走 R2 后的 merger 路径)
  ↓
R5 (回测验证 ≥ 3 cross-brand)
```

为什么 R2 必须先：R1 抽出的 candidates 要直接走 merger 落库，否则又会产生独立 KO 不合并。

为什么 R3 + R4 在 R5 前：跨品牌合并产生后立刻面临"同概念不同单位/缺值"的判定，没修 R3+R4 出来的 cross-brand KO 全是假阳性 material_conflict。

---

## CHANGELOG

- **2026-05-11**：初稿。基于 docs/36 跑通后的 5 个问题，定义 R1-R5 任务收尾。Carrier 19XR 数据恢复走 MiMo 视觉抽取（与 §11 视觉支线协同）。E 任务从"加 flag"升级到"切默认 + 删旧路径"。merger 加空值判定 + 单位换算。
