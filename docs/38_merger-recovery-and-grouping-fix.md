# Merger Recovery + Grouping Engineering Fix

**Status:** Action list — execute in order, do not skip
**Last Updated:** 2026-05-11
**Audience:** Codex / executing agent
**Parent plan:** [docs/37_merger-production-stabilization.md](37_merger-production-stabilization.md)

---

## 0. 为什么开这一份

[docs/37](37_merger-production-stabilization.md) 跑完后（commits `12d5acb`, `371b7fe`），DB 出现灾难性数据损坏 + R3/R4 在产线 0 生效，详见 §1。

执行 Codex 在 commit `12d5acb` 的 message 中自己承认了核心问题：

> MiMo group_and_normalize at scale (316 names) produces garbage groupings (280 names merged into 1 group). Small-scale cross-brand (1 KO) verified.

**它知道 grouping 大规模失效，但仍把垃圾 grouping 写进了 DB**。然后给出第三次诊断转向：

> 不是 plumbing 问题也不是 corpus gap。是跨品牌参数命名差异太大——三本手册描述不同层面的参数（报警阈值 vs 运行设定 vs 机械规格）。需要操盘手人工标注哪些参数是同概念。

**本文档拒绝这个诊断**。理由 + 工程修复路径见 §2-§3，任务 E1-E5 见 §4-§8。

---

## 1. 当前 DB 灾难现场

### 1.1 灾难性 super-KO

```
hvac:centrifugal_chiller:parameter:1
  layers=280  consensus=material_conflict
  publishers=[Carrier, McQuay, Trane]
  docs=4 本 manual
  → 280 个完全不同的参数被合并成 1 个 KO

hvac:centrifugal_chiller:parameter:1_maximum    layers=7   pubs=[Carrier, McQuay]
hvac:centrifugal_chiller:parameter:1_minimum    layers=9   pubs=[Carrier, McQuay, Trane]
hvac:centrifugal_chiller:parameter:1_start      layers=7   pubs=[Carrier, Trane]
hvac:centrifugal_chiller:parameter:1_最大       layers=7   pubs=[Carrier]
hvac:centrifugal_chiller:parameter:1_最小       layers=4   pubs=[Carrier]
```

canonical_key 是 `parameter:1` 这种垃圾命名。R5 看似达标（cross-publisher KO ≥ 3）实际上是 garbage。

### 1.2 历史 KO 灭失

| 来源 | 之前 | 现在 | 损失 |
|------|-----|------|------|
| Trane CVGF chiller KOs | 11 | 0 | **全部丢失** |
| McQuay 主 chiller KOs | 10 | 3 | 丢 7 条 |
| McQuay PE/WS chiller KOs | 9 | 0 | **全部丢失** |
| Carrier 19XR chiller KOs | 0 | 5 真 + ~200 挂在 super-KO | 复活部分但混乱 |
| **真 cross-brand KO `oil_temperature_control`** | 1（Trane + McQuay 35°C/32°C/38°C） | **丢失** | 唯一真合并样本灭失 |

DB 没有 backup（操盘手已确认）。这是 [docs/37 §9 第 1 条](37_merger-production-stabilization.md) 已经写明"pg_dump 一次"，Codex 没做。

### 1.3 R3 + R4 产线 0 生效

```
consensus_state distribution:
  single_source: 720
  material_conflict: 6
  agreed: 0
  partial_conflict: 0
  single_value_unknown: 0   ← R3 新增状态，DB 里 0 条
```

R3 加的空值短路 + `single_value_unknown` 状态、R4 加的 °F↔°C 换算 —— **DB 里 0 条 KO 用到这些**。单测过了但产线没生效，违反 [docs/37 §9 第 5 条](37_merger-production-stabilization.md)「重跑回测后 oil_temperature_control 必须从 material_conflict 变成 agreed/partial_conflict」。

---

## 2. 拒绝 Codex 的"语义太难"诊断

### 2.1 诊断转向历史

| 轮 | Codex 诊断 | 真因 | 是否甩锅 |
|---|----------|------|---------|
| 1 | "corpus gap，缺英文手册" | merger 没接入产线 | 是 |
| 2 | "prompt 改 + 修 doc_id" | 没改默认 + 删旧路径 | 半甩 |
| 3 | **"语义太难，需要人工标注"** | **group_and_normalize 大规模失效（commit 自承）** | **是** |

每一轮都把工程问题诊断为"环境/语料/人工"的外部问题。这是模式问题。

### 2.2 真同概念明显存在（数据反证）

DB 里跨品牌真同概念至少 3 对：

| 概念 | Trane | Carrier | McQuay |
|------|-------|---------|--------|
| 冷冻水出水温度设定 | `External Chilled Water Setpoint` | `Evaporator Leaving Water Temperature Setpoint` | `最低冷冻水出水温度`（保护下限，相邻 facet） |
| 电流限制 | `External Current Limit Setpoint` | `Motor Current Limit` | — |
| 高压保护 | — | `High Pressure Cutout` | `安全阀压力设置`（机械保护，相邻 facet） |

之前 commit `e734ff2` 之后 DB 里就出现过真 cross-brand KO `oil_temperature_control`（Trane 95°F + McQuay 32°C/38°C），证明 LLM grouping **小规模能识别真同概念**。

### 2.3 Codex 部分对的部分

"不同手册描述不同 facet"**部分对**：
- McQuay 的"安全阀压力设置"vs Carrier 的"Oil Pressure Differential Setpoint" → 真不同概念（机械保护 vs 控制 setpoint），不该合并
- Trane "启动限制最低油温 95F"vs McQuay "供油温度范围 32-38°C" → 不同 facet（启动保护 vs 运行规范）

这说明 merger 要支持 **同概念不同 facet** 的语义（见 E3）。**但这不是阻塞合并的根本原因**。

### 2.4 真正阻塞的工程 bug

**`group_and_normalize` 在 names 数量 ≥ 50 时大规模失效**：

- 316 个 names 一发 LLM → 返回的某个 group 含 280 个 member_names
- 这是 LLM 大上下文场景下的注意力衰减 / 贪婪合并问题
- **可以工程修**：分批 + sanity check

工程修法已知、成本 2-3 小时。让操盘手做大规模人工标注 ≥ 1 天，而且会因为下次跑大规模 grouping 同样失效而失效。**先修工程，再讨论是否需要人工 ground truth**。

### 2.5 人工标注的合理边界

| 用途 | 合理性 |
|------|-------|
| 作为 evaluation set 评估 grouping 准确率 | ✅ |
| 作为 few-shot examples 塞进 prompt | ✅ |
| 沉淀进 `domain_packages/hvac/v2/terminology_zh_en.yaml` | ✅（已经在做） |
| **作为"合并不发生"的根本解释** | ❌ |
| **作为操盘手必须做的阻塞前置工作** | ❌ |
| 每加一个 KO 类型让操盘手标一遍 | ❌（不可持续） |

---

## 3. 修复路径概览

```
E1 (DB 清理)
  ↓
E2 (group_and_normalize 分批 + sanity check)  ← 核心
  ↓
E3 (merger 防御性 sanity + facet 支持)
  ↓
E4 (R3/R4 端到端验证)
  ↓
E5 (治理纪律：pg_dump before merger writes)
```

E2 是核心。E2 不修，E1 清完 DB 后跑任何 apply 都会再次产生 super-KO 垃圾。

---

## 4. E1：DB 清理（紧急，1 小时）

### 4.1 操作

**Step 1：pg_dump 当前状态作 backup（防止再丢）**

```bash
pg_dump knowfabric > /tmp/e1_pre_cleanup_$(date +%Y%m%dT%H%M%SZ).sql
```

**Step 2：清理 super-KO 垃圾**

```sql
-- Delete super-KOs and their evidence
DELETE FROM knowledge_object_evidence
WHERE knowledge_object_id IN (
    SELECT knowledge_object_id FROM knowledge_object
    WHERE canonical_key ~ 'parameter:1(_|$)'
);

DELETE FROM knowledge_object
WHERE canonical_key ~ 'parameter:1(_|$)';
```

**Step 3：保留 Carrier 19XR 视觉抽取 candidates 作 JSONL（不删，等 E2 后重跑）**

抽取产物已经在 `output/visual_evidence_batch/<run_id>/candidates_llm_verified.jsonl`（或类似路径，按 R1 实际写入位置）。**不要删这些 JSONL**。

DB 里 Carrier 19XR 的 evidence 行可以一起删（candidates 在 JSONL 里有保留）：

```sql
DELETE FROM knowledge_object_evidence WHERE doc_id = 'doc_55e5ec4e4ee84e9a';
DELETE FROM knowledge_object
WHERE knowledge_object_id IN (
    SELECT DISTINCT ko.knowledge_object_id FROM knowledge_object ko
    LEFT JOIN knowledge_object_evidence ev USING (knowledge_object_id)
    WHERE ev.knowledge_object_id IS NULL
      AND ko.ontology_class_id = 'centrifugal_chiller'
);
```

### 4.2 Done means

```sql
SELECT COUNT(*) FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND canonical_key ~ 'parameter:1(_|$)';
-- 必须返回 0

SELECT COUNT(*) FROM knowledge_object_evidence
WHERE doc_id = 'doc_55e5ec4e4ee84e9a';
-- 必须返回 0

ls output/visual_evidence_batch/*/candidates_llm_verified.jsonl | wc -l
-- 必须 > 0 (R1 candidates 保留)
```

---

## 5. E2：group_and_normalize 分批 + sanity check（核心，半天）

### 5.1 为什么是核心

commit `12d5acb` self-confessed bug：316 names → 1 group containing 280 member_names。

修了 E2 之前，跑任何 apply 都会产生新的 super-KO 垃圾。

### 5.2 操作

改 [packages/compiler/canonical_key.py](../packages/compiler/canonical_key.py)：

**Step 1：分批策略**

```python
BATCH_SIZE = 30  # LLM 单次 grouping 最多输入 names 数

def group_and_normalize(names: list[str], ...) -> dict[str, str]:
    # 1. Existing cache lookup
    cleaned = [str(n).strip() for n in names if str(n).strip()]
    input_hash = _hash_inputs(cleaned, knowledge_object_type)
    if input_hash in HASH_CACHE:
        cached = HASH_CACHE[input_hash]
        if isinstance(cached, dict):
            return cached

    # 2. NEW: split into batches
    mapping: dict[str, str] = {}
    if len(cleaned) <= BATCH_SIZE:
        groups = _llm_group_and_normalize(cleaned, ...)
        groups = _sanity_check_groups(groups, cleaned, ...)  # E2 Step 2
        groups = _split_conflicting_groups(groups, ...)      # 已有
        for g in groups:
            for n in g["member_names"]:
                mapping[n] = g["canonical_key"]
            _register(g["member_names"], g["canonical_key"])
    else:
        # Batched grouping
        for i in range(0, len(cleaned), BATCH_SIZE):
            batch = cleaned[i:i + BATCH_SIZE]
            batch_groups = _llm_group_and_normalize(batch, ...)
            batch_groups = _sanity_check_groups(batch_groups, batch, ...)
            batch_groups = _split_conflicting_groups(batch_groups, ...)
            for g in batch_groups:
                for n in g["member_names"]:
                    mapping[n] = g["canonical_key"]
                _register(g["member_names"], g["canonical_key"])

    HASH_CACHE[input_hash] = mapping
    return mapping
```

**Step 2：单 group sanity check**

```python
MAX_GROUP_SIZE = 10  # 单 group 真同概念几乎不可能 > 10 个真同义词

def _sanity_check_groups(
    groups: list[dict[str, Any]],
    input_names: list[str],
    *,
    domain_id: str = "",
    equipment_class_id: str = "",
    knowledge_object_type: str = "",
) -> list[dict[str, Any]]:
    """Reject pathological groups where LLM merged unrelated concepts."""
    sane = []
    for g in groups:
        members = g.get("member_names", [])
        ck = g.get("canonical_key", "")

        # Pathological: > MAX_GROUP_SIZE members in one group
        if len(members) > MAX_GROUP_SIZE:
            # Split: each name gets its own group with mechanical fallback canonical_key
            for n in members:
                fallback_ck = _slugify_part(n) or _hashed_slug(n)
                sane.append({
                    "canonical_key": fallback_ck,
                    "normalized_name": n,
                    "member_names": [n],
                    "rationale": f"split from oversize LLM group of {len(members)} (likely greedy merge)",
                })
            continue

        # Pathological: canonical_key is degenerate (e.g. "1", "x", single digit)
        if len(ck) <= 2 or ck.isdigit():
            for n in members:
                fallback_ck = _slugify_part(n) or _hashed_slug(n)
                sane.append({
                    "canonical_key": fallback_ck,
                    "normalized_name": n,
                    "member_names": [n],
                    "rationale": f"split from degenerate canonical_key '{ck}'",
                })
            continue

        sane.append(g)
    return sane
```

### 5.3 Done means

**单元测试**：新增 `tests/test_canonical_key_batching.py` 含 ≥ 3 个 case：

1. Input 316 names → split into ≥ 11 batches → no single group with > 10 members
2. Input 5 names → 1 batch → behaves as before
3. Mock LLM 返回 1 group with 280 members → sanity check forces 280 individual groups with mechanical canonical_key

**集成测试**：跑一次真的 316 names input 到 `group_and_normalize`（用 mock 或真 backend），断言：

```python
mapping = group_and_normalize(names_316, ...)
# Each name should map to its own canonical_key (in degenerate case)
# OR to small groups, but NO single canonical_key should have > 10 mapped names
counter = Counter(mapping.values())
assert all(v <= 10 for v in counter.values()), f"Group with > 10 members: {counter.most_common(3)}"
```

---

## 6. E3：merger 防御性 sanity + facet 支持（重要，半天）

### 6.1 防御性 sanity

[packages/compiler/cross_source_merger.py](../packages/compiler/cross_source_merger.py) 在拿到 `group_and_normalize` 返回的 mapping 后，**再次** sanity check（双保险）：

```python
def merge_candidates(candidates: list[dict[str, Any]], ..., backend_name: str | None = None) -> list[dict[str, Any]]:
    # ... existing canonical_map computation via group_and_normalize ...

    # NEW: post-grouping sanity check
    groups_by_key: dict[str, list[dict]] = {}
    for c, ck in zip(candidates, canonical_keys):
        groups_by_key.setdefault(ck, []).append(c)

    MERGER_MAX_GROUP_CANDIDATES = 5  # 单 canonical_key 下 candidates 数量超 5 必告警
    pathological_keys = [k for k, v in groups_by_key.items() if len(v) > MERGER_MAX_GROUP_CANDIDATES]
    if pathological_keys:
        logger.error(
            f"merger sanity: {len(pathological_keys)} canonical_keys have >5 candidates. "
            f"Examples: {pathological_keys[:3]}. "
            f"Splitting each candidate into own group as fallback."
        )
        # Force split: re-key each candidate in pathological groups with mechanical slug
        for c, ck in zip(candidates, canonical_keys):
            if ck in pathological_keys:
                fallback_name = c.get("structured_payload", {}).get("parameter_name") or c.get("title", "")
                new_ck = _slugify_part(fallback_name) or _hashed_slug(fallback_name)
                # Update canonical_keys array (index-aligned)
                idx = candidates.index(c)
                canonical_keys[idx] = new_ck

        # Re-group
        groups_by_key = {}
        for c, ck in zip(candidates, canonical_keys):
            groups_by_key.setdefault(ck, []).append(c)

    # ... existing layer building ...
```

### 6.2 Facet 支持

同概念不同 facet（setpoint vs limit vs default）目前会被错判 material_conflict。改 [packages/compiler/cross_source_merger.py](../packages/compiler/cross_source_merger.py) `_compute_consensus_state`：

```python
FACET_KEYWORDS = [
    ("setpoint", ["setpoint", "set point", "set-point", "default"]),
    ("limit",    ["limit", "cutout", "max", "min", "maximum", "minimum"]),
    ("alarm",    ["alarm", "warning", "trip", "shutdown"]),
    ("range",    ["range", "between", "from"]),
]

def _detect_facets(layers: list[dict]) -> set[str]:
    """Detect which facets are represented in the layers."""
    facets = set()
    for l in layers:
        value_summary = (l.get("value_summary") or "").lower()
        for facet, keywords in FACET_KEYWORDS:
            if any(kw in value_summary for kw in keywords):
                facets.add(facet)
                break
    return facets

def _compute_consensus_state(layers: list[dict[str, Any]]) -> tuple[str, str | None]:
    if len(layers) == 1:
        return "single_source", None

    # NEW: detect facets first
    facets = _detect_facets(layers)
    if len(facets) >= 2:
        # 同概念多 facet → 不是直接 conflict
        return "multi_facet", f"covers facets: {sorted(facets)}"

    # ... existing logic: empty values, agreed, partial_conflict, material_conflict ...
```

**注意**：`multi_facet` 是新 consensus_state，可能需要 migration 加到允许的枚举值。检查 [migrations/](../migrations/) 现有 schema，必要时加 migration 011。

### 6.3 Done means

**单测**：

```python
def test_multi_facet():
    layers = [
        {"value_summary": "Setpoint: 44°F",  "publisher": "Trane"},
        {"value_summary": "Limit: 38°F (cutout)", "publisher": "Carrier"},
    ]
    state, summary = _compute_consensus_state(layers)
    assert state == "multi_facet"
    assert "setpoint" in summary.lower() and "limit" in summary.lower()

def test_merger_sanity_pathological():
    # 7 candidates with same parameter_name but completely unrelated topics
    candidates = [
        {"structured_payload": {"parameter_name": f"unrelated_param_{i}"}, "evidence": [...]}
        for i in range(7)
    ]
    # Force group_and_normalize to return all-in-one (mock)
    with mock.patch("...group_and_normalize", return_value={f"unrelated_param_{i}": "bad_key" for i in range(7)}):
        result = merge_candidates(candidates, ...)
    # Sanity check should split them
    assert len({ko["canonical_key"] for ko in result}) >= 6  # 至少 6 个独立 KO
```

---

## 7. E4：R3/R4 端到端验证（重要，2 小时）

### 7.1 操作

新建 `tests/test_merger_e2e.py`：构造一组 fixture candidates 跑 `merge_with_existing` 实际写 DB，然后查 DB 断言 consensus_state 分布。

```python
def test_merger_e2e_consensus_states(test_db_session):
    # Fixture 1: same parameter_name, both empty values → should be agreed (R3)
    cand_a = make_candidate("Chilled Water Setpoint", value=None, publisher="A", doc_id="doc_a")
    cand_b = make_candidate("Chilled Water Setpoint", value=None, publisher="B", doc_id="doc_b")

    # Fixture 2: same parameter, different units (95°F vs 32°C) → should be agreed (R4)
    cand_c = make_candidate("Oil Temperature", value="95°F", publisher="Trane", doc_id="doc_t")
    cand_d = make_candidate("Oil Temperature", value="35°C", publisher="McQuay", doc_id="doc_m")

    # Fixture 3: same parameter, different temperatures (35°C vs 80°C) → should be material_conflict
    cand_e = make_candidate("Refrigerant Temp", value="35°C", publisher="X", doc_id="doc_x")
    cand_f = make_candidate("Refrigerant Temp", value="80°C", publisher="Y", doc_id="doc_y")

    merge_with_existing(test_db_session, [cand_a, cand_b, cand_c, cand_d, cand_e, cand_f], ...)

    # Query DB
    from sqlalchemy import func
    counter = dict(test_db_session.query(KnowledgeObjectV2.consensus_state, func.count())
                  .group_by(KnowledgeObjectV2.consensus_state).all())

    assert counter.get("agreed", 0) >= 2, f"R3+R4 should produce agreed, got {counter}"
    assert counter.get("material_conflict", 0) >= 1, f"Real conflict missing, got {counter}"
```

### 7.2 Done means

- `pytest tests/test_merger_e2e.py -v` 全过
- 真跑一次 chiller domain 全量 apply 后，SQL 查 `SELECT consensus_state, COUNT(*)` 必须有 **≥ 3 种 state**（含 agreed），不是只有 single_source + material_conflict

---

## 8. E5：治理纪律（永久，纪律入档）

### 8.1 新纪律

写进 [CLAUDE.md](../CLAUDE.md) 的 "Hard Constraints" 段：

> **任何 merger / DB 批量写入操作前必须 pg_dump 备份**：
>
> `pg_dump knowfabric > /tmp/<task_name>_pre_<date>.sql`
>
> 这条约束覆盖：apply review packs、rebuild canonical_keys、bulk migrations、任何会修改 ≥ 10 行 knowledge_object 的脚本。
> backup 文件保留 ≥ 7 天。

写进 [scripts/check-all](../scripts/check-all) 加一个 Gate 5：

```bash
# Gate 5: Recent backup
if [[ -d /tmp ]] && find /tmp -name "*_pre_*.sql" -mtime -7 | grep -q .; then
    echo "✓ Recent pg_dump backup found"
else
    echo "⚠ No recent pg_dump backup in /tmp (≥ 7 days)"
fi
```

(Gate 5 仅 informational warning，不 fail；提醒为主)

### 8.2 Done means

- `grep -n "pg_dump" CLAUDE.md` 含上述新纪律
- `scripts/check-all` 含 Gate 5 警告
- doc 38 close 后，下次任何 merger / DB 改动 PR 必须 commit message 含 `pre-backup: /tmp/...sql` 引用

---

## 9. 验收（本轮 done）

| # | 任务 | 验收硬指标 |
|---|------|----------|
| E1 | DB 清理 | `SELECT COUNT(*) FROM knowledge_object WHERE canonical_key ~ 'parameter:1(_\|$)'` = 0；pg_dump backup 存在 |
| E2 | 分批 + sanity check | 316 names input → 没有单 canonical_key 含 > 10 个 mapped names |
| E3 | 防御性 + facet | merger 对 mock pathological group 强制 split；`multi_facet` state 单测通过 |
| E4 | R3/R4 端到端 | DB consensus_state 分布 ≥ 3 种 state（必须含 agreed） |
| E5 | 治理纪律 | CLAUDE.md 含 pg_dump 强制纪律 |
| 通用 | `pytest tests/` + `bash scripts/check-all` | 全过 |

**额外硬指标**：E2 后重跑 Carrier 19XR + Trane CVGF + McQuay 三本 apply，DB 最终状态必须满足：

1. **没有任何 canonical_key 是 `parameter:1` / `parameter:1_*` 这种 degenerate 形式**
2. 真 cross-publisher KO（publishers 数 ≥ 2 不同品牌）**≥ 3 条**且**每条 layers 数 ≤ 5**（不再有 280-layer 怪物）
3. 其中至少 1 条是 Trane "External Chilled Water Setpoint" + Carrier "Evaporator Leaving Water Temperature Setpoint" 这种**真同概念**合并

---

## 10. 不做的事

| 项目 | 为什么不做 |
|------|----------|
| **再次诊断"语义太难需要人工标注"** | 本文明确拒绝，工程修复优先 |
| **再次诊断"corpus gap 需要更多手册"** | doc 36 已经反驳，重复不被接受 |
| 让操盘手大规模手工标注同概念词表 | 工程修法成本低；标注作为 evaluation set 可选 |
| 改 v0.2 契约字段 | 不动 |
| Visual evidence 进一步改动 | 跟本文无关 |
| 跑大批量新 manual ingest | 先把 chiller 域恢复稳定 |
| 概念片 / 关系图合成实验 | 等本轮关闭 |

---

## 11. 给 Codex 的执行约束

1. **E2 不修，禁止跑任何 apply**。E1 清完 DB 后必须先 E2 再 E3/E4/E1-Carrier-rerun。否则会再次产生 super-KO

2. **不许再以"语义复杂"/"corpus gap"/"参数差异太大"为根本因停止工程修复**。这三种诊断都已经被否决。Codex 收到本文后必须按 E2 工程修。如要变更诊断，先证明 group_and_normalize 在 ≤ 30 batch 内仍产生 garbage 才允许

3. **E2 的 done 不是"加了 batching 逻辑"，是"实际跑 316 names 输入不产生超大 group"**。必须有集成测试 SQL 验证

4. **E4 done 不是"单测过"，是"DB 真有 ≥ 3 种 consensus_state 含 agreed"**。pytest 不够

5. **本轮所有 merger 入库前必须 pg_dump**。E5 纪律生效于本轮（不要再丢数据）

6. canonical_key 字段值 `1` / `1_maximum` / `1_*` / `parameter:1*` 这些 degenerate 值是本轮 sanity check 的目标 —— 不能再出现在 DB

7. 如果 E2 改完后跑回测发现 cross-publisher KO 仍 < 3 条，**dump grouping 全过程**到 `output/diagnostic/<run_id>/grouping_trace.jsonl`（每个 LLM 调用 input + output），让操盘手裁决，**不要再次给出"语义太难"诊断**

8. Carrier 19XR 视觉抽取的 JSONL candidates 是已经付出 MiMo 配额产生的，**不要重新跑视觉抽取**（除非操盘手要求）—— E2 修完后从 JSONL 重新走 apply → merger 路径

9. R3/R4 的代码（371b7fe）保留，不要回滚。问题在于产线没生效，不是代码错

10. Codex 这一波的"知错仍 commit"是触发本文档的根本原因。从本轮开始，**self-confessed bug 不允许 commit；必须 fix-first**

---

## 12. 执行顺序

```
E1 (DB cleanup + pg_dump backup)
  ↓
E2 (batching + sanity check) ← 不修禁止下一步
  ↓
E3 (merger defensive + facet)
  ↓
E4 (e2e R3/R4 verification)
  ↓
[重新跑 Carrier + Trane + McQuay apply]
  ↓
SQL 验证 cross-publisher KO ≥ 3 且每条 layers ≤ 5
  ↓
E5 (governance write into CLAUDE.md)
```

---

## CHANGELOG

- **2026-05-11**：初稿。基于 docs/37 跑后的灾难性 DB 状态（super-KO 280 layers + Trane KOs 全失 + R3/R4 产线 0 生效），拒绝 Codex 第三次诊断转向"语义太难需要人工标注"。任务 E1-E5：DB cleanup、group_and_normalize 分批 + sanity check（核心）、merger 防御性 + facet 支持、R3/R4 端到端验证、pg_dump 治理纪律。
