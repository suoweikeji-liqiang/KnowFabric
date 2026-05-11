# Codex Follow-up Tasks (post W1-W3 sweep)

**Status:** Action list — execute in order
**Last Updated:** 2026-05-11
**Audience:** Codex / executing agent
**Parent plan:** [docs/34_compile-gap-and-execution-plan.md](34_compile-gap-and-execution-plan.md)

---

## 0. Why this doc exists

[docs/34_compile-gap-and-execution-plan.md](34_compile-gap-and-execution-plan.md) 的 W1 + W2-W3 主线基础设施 + §11 视觉支线基础设施已经全部建好，288 个测试全过，`scripts/check-all` 4 个 gate 全过。

但有 3 个真正的"端到端跑通"环节没完成，导致 KnowFabric 当前还不能真正给 sw_base_model 喂权威 KO：

1. **跨源合并 plumbing 没接通** —— W3 D5 多源回测 4 个指标全 0%，根因是 [packages/compiler/cross_source_merger.py:13](../packages/compiler/cross_source_merger.py:13) 用了 mechanical `resolve_single_name`，没用 LLM-assisted `group_and_normalize`
2. **MiMo 视觉抽取没真跑批** —— `output/visual_evidence_batch/` 不存在，本月 14 亿 token 额度未消化
3. **端到端 smoke 没跑** —— 没有一份真实 manual 走完整产线（v0.2 字段 + 跨源合并 + visual evidence 三件套同时落地）

本文档把这三件事拆成可执行任务，加一个可选的收尾任务（packages/review/applier.py 主流程抽取）。

任务必须按顺序执行：T1 → T2 → T3 → T4。T1 是其他任务的前置（不修 T1，T3 的"三件套都在"无法验证）。

---

## T1. 修 merger 的 canonical_key plumbing（必做，1-2 小时）

### T1.1 症状

[output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md) 显示：

| 指标 | 目标 | 实际 |
|------|------|------|
| multi-source rate | ≥ 20% | **0%** |
| partial_conflict | ≥ 3 | **0** |
| material_conflict | ≥ 1 | **0** |
| agreed | ≥ 5 | **0** |

38 个 KO 全部 `consensus_state = single_source`。

### T1.2 根因

[packages/compiler/cross_source_merger.py:13](../packages/compiler/cross_source_merger.py:13)：

```python
from packages.compiler.canonical_key import resolve_single_name
```

[packages/compiler/cross_source_merger.py:144-151](../packages/compiler/cross_source_merger.py:144)：

```python
for name in names_by_candidate:
    key = resolve_single_name(
        name,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
    )
    canonical_keys.append(key)
```

`resolve_single_name` 是 mechanical slugify。Trane 的 `"Active Chilled Water Setpoint"` 和 McQuay 的 `"动态冷冻水设定"` 走这条路得到两个不同的 key → 无 overlap → 不合并。

[packages/compiler/canonical_key.py:244](../packages/compiler/canonical_key.py:244) 的 `group_and_normalize(names, ...)` 已经写好，能 LLM-grouping 跨语言名字到同一个 canonical_key，**但 merger 没调它**。

### T1.3 修法

改 [packages/compiler/cross_source_merger.py](../packages/compiler/cross_source_merger.py)：

**Step 1**：把 import 改成同时引入两个函数（保留 mechanical 作 fallback）：

```python
from packages.compiler.canonical_key import resolve_single_name, group_and_normalize
```

**Step 2**：把 line 143-151 的循环替换为两阶段处理。先尝试 LLM grouping（一次性把所有候选 names 送进去），LLM 失败时退回 mechanical：

```python
# Step 1: Try LLM-assisted cross-lingual grouping first
canonical_map: dict[str, str] = {}
try:
    canonical_map = group_and_normalize(
        names=names_by_candidate,
        domain_id=domain_id,
        equipment_class_id=equipment_class_id,
        knowledge_object_type=knowledge_object_type,
        backend_name=backend_name,
    )
except Exception:
    canonical_map = {}

# Step 2: Fall back to mechanical for any names LLM didn't cover
canonical_keys = []
for name in names_by_candidate:
    key = canonical_map.get(name)
    if not key:
        key = resolve_single_name(
            name,
            domain_id=domain_id,
            equipment_class_id=equipment_class_id,
            knowledge_object_type=knowledge_object_type,
        )
    canonical_keys.append(key)
```

**Step 3**：默认 backend_name 改成走 MiMo（消化 §11.2 B 段预算）。在 `merge_candidates` 的 docstring 加一行说明：「`backend_name` defaults to MiMo backend `mimo-compiler` per docs/34 §11.2 B-band allocation; pass DeepSeek backend name to switch.」

实际默认值可以在调用方（apply 路径）设置，merger 函数本身保持 `backend_name: str | None = None`。

### T1.4 验证

**单元测试**：新增 `tests/test_cross_source_merger_crosslingual.py`，至少 1 个 case：

- Input：两个 candidates，name 分别是 `"Active Chilled Water Setpoint"`（authority_level=`oem_manual`, publisher=`Trane`）和 `"动态冷冻水设定"`（authority_level=`oem_manual`, publisher=`McQuay`），数值一致
- Mock LLM 返回 `{"groups": [{"canonical_key": "chiller_chilled_water_supply_temperature_setpoint", "member_names": ["Active Chilled Water Setpoint", "动态冷冻水设定"]}]}`
- 断言 merger 输出 1 个 KO，`authority_summary_json.layers` 长度 == 2，`consensus_state == "agreed"`

测试 pass 后跑 `pytest tests/ -x` 不能有回归（≥ 288 个全过，含新增）。

**重跑 W3 D5 回测**：

重新跑 [scripts/run_w3_multisource_baseline.py](../scripts/run_w3_multisource_baseline.py)（如不存在，先用现有 fixture 跑一次 Trane CVGF + McQuay）。

**Done means**：

更新 [output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md)，4 个指标必须全达标：

| 指标 | 目标 | 必须 |
|------|------|------|
| multi-source rate | ≥ 20% | 达标 |
| partial_conflict | ≥ 3 | 达标 |
| material_conflict | ≥ 1 | 达标 |
| agreed | ≥ 5 | 达标 |

如果 fixture 数据量不够撑指标，先在 REPORT 注明"single-doc-pair test passed, full regression pending T3 end-to-end smoke"，但**单元测试必须 pass**。

### T1.5 风险

- LLM grouping 不稳定 / 输出格式错 → 已有 hash cache + register 机制 + mechanical fallback，不会阻塞 apply
- LLM 调用配额 → 每次 grouping ~6k tokens，跑 1000 个 manual 才用 6M tokens，14 亿额度远超
- 已注册 canonical_key 被错合并 → registry append-only 不动；仅新候选受 LLM 影响

---

## T2. 真跑一次 MiMo 视觉抽取（必做，1 天内）

### T2.1 为什么

§11 整套视觉基础设施（[packages/extraction/visual.py](../packages/extraction/visual.py) + [packages/extraction/visual_triage.py](../packages/extraction/visual_triage.py) + [scripts/run_visual_evidence_batch.py](../scripts/run_visual_evidence_batch.py)）已经写好，包括 8.4e8 token cap 和 resume 支持。

但 `output/visual_evidence_batch/` 目录不存在。**一行真数据没产**。

小米 MiMo 14 亿 token 本月额度在持续倒计时，每天不消化 = 浪费 4500 万 token。这一步不能再等。

### T2.2 操作

**选择素材**：从 [workspace/hvac_source_inventory/20260507T083207Z/source_inventory.csv](../workspace/hvac_source_inventory/20260507T083207Z/source_inventory.csv) 挑 3-5 个高价值低文本 PDF：

筛选条件：
- `text_quality ∈ {low_or_no_text, partial_text}`
- `document_kind_guess ∈ {service_manual, controller_manual, operation_installation_manual}`
- `page_count` 在 30-150 范围（太短无视觉证据，太长烧配额）
- 优先级：含品牌 Trane / York / Carrier / Daikin / McQuay

选 3 个起步即可，不要一上来 5 个。

**跑批**：

```bash
python scripts/run_visual_evidence_batch.py \
    --inventory workspace/hvac_source_inventory/20260507T083207Z/source_inventory.csv \
    --doc-ids <挑出的 3 个 doc_id 逗号分隔> \
    --backend-name mimo-visual \
    --output-dir output/visual_evidence_batch \
    --execute
```

如脚本现有 CLI 不支持上述参数，先调整 CLI 让其支持（这是 §11 计划的一部分），但**不要重构脚本核心逻辑**。

**Token 预算监控**：跑批必须实时输出累计 tokens；预算逼近 5 千万（A 段 8.4 亿的 6%）时输出 warning；超 1 亿停止（保留余量给后续 doc）。

### T2.3 验证

**数据库层**：

```sql
SELECT image_type, COUNT(*) FROM document_page_image GROUP BY image_type;
SELECT doc_id, COUNT(*) FROM document_page_image GROUP BY doc_id;
```

每个 doc 至少有 5 行 `document_page_image`，至少 2 种 `image_type`（说明 triage 在工作）。

**人审样本**：

随机抽 20 个 `document_page_image` 行，操盘手审：
- `image_type` 准确率 ≥ 70%
- `vl_summary` 可读、不空、不明显幻觉
- `vl_entities` 中至少 60% 在源图像里能找到对应文字 / 实体

**Done means**：

写一份 [output/visual_evidence_batch/<run_id>/REPORT.md](../output/visual_evidence_batch/) ：

| 字段 | 内容 |
|------|------|
| Documents processed | 3-5 |
| Pages rendered | 总数 |
| MiMo calls | 总数 |
| Tokens consumed | 估算（input + output） |
| Avg tokens / page | |
| Pages with high-confidence vl_entities (≥ 0.7) | 数 / 占比 |
| Pages flagged uncertain | 数 / 占比 |
| Token budget remaining | 8.4e8 - consumed |
| Operator audit accuracy | 20 个样本中 image_type 正确率 |

### T2.4 注意

- **MiMo backend 走 `mimo-v2-omni`** 多模态模型，不是 text-only（修复参考 commit `4286a8a`）
- 渲染 PNG 写 `storage/page_images/<doc_id>/page_<no>.png`，**不入仓库**
- 如果跑批中断（网络 / timeout），用 resume 模式继续：脚本必须查 `document_page_image` 已存在的 page_image_id 自动跳过
- 不要在这一步做 KO 关联（visual_evidence_anchor 表的写入是 T3 的事，这里只填 `document_page_image`）

---

## T3. 端到端 smoke：完整产线跑通一个 manual（必做，1 天内）

### T3.1 为什么

T1 修完跨源合并、T2 跑出真视觉抽取后，必须**至少跑通一个完整 manual 端到端**，把所有 W1-W3 的产物在一个 KO 的查询响应里同时验证到。

否则各个零件单独看都对，组装起来可能在某个接缝处断。

### T3.2 操作

**素材**：Trane CVGF 400-1000 chiller manual（已经在库，doc_id = `doc_883beab5e0004a2c`），加上 ASHRAE G36 §5.22 章节（已在库）。这两个一起跑能命中：
- v0.2 字段（authority_layers / consensus_state）—— OEM manual vs industry standard 两个 authority_level
- 跨源合并 —— G36 的某些 setpoint 跟 Trane 重名（如冷冻水 setpoint）
- visual evidence —— Trane CVGF 有接线图、控制屏页面（先在 T2 已跑过的话）

**操作**：

1. 确认两个 doc 都已 ingest + parse + chunk
2. 跑 doc-level extraction（DeepSeek，已稳定）
3. Apply review packs，**经过修好的 cross_source_merger**
4. 关联 visual evidence（如 T2 已产 visual 数据，applier 把对应 KO 的 visual_evidence_anchor 行写入）
5. 调 API 查参数：

```bash
curl 'http://localhost:8000/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-specs?min_authority_level=oem_manual&consensus_filter=all&limit=20' | jq .
```

### T3.3 验证（三件套必须全到）

在返回的 envelope 里，至少 1 条 KO 必须**同时**满足：

1. `authority_summary_json.layers` 长度 ≥ 2（跨源合并真的发生）
2. `consensus_state ∈ {agreed, partial_conflict, material_conflict}`（不是 single_source）
3. `evidence_text` 真实可见（unless `is_redistributable=false`，那时应是 paraphrase + `redistribution_restricted: true`）
4. **如果 T2 视觉抽取产生了对应 chunk 的 visual evidence**：envelope 还应有 `visual_evidence` 数组非空，包含 `page_no` + `bbox` + `image_path` + `vl_summary`

把这个 KO 的 JSON 完整 dump 到 [output/e2e_smoke/<run_id>/sample_ko.json](../output/e2e_smoke/)。

**Done means**：写 [output/e2e_smoke/<run_id>/REPORT.md](../output/e2e_smoke/)：

- 跑的 doc 列表 + ontology_version
- 端到端产生的 KO 总数
- 跨源合并发生数（layers ≥ 2 的 KO 数 / 占比）
- 三件套都齐的 KO 数（authority + evidence + visual）
- 至少 1 条完整 JSON dump
- 任何失败步骤的诊断

### T3.4 不达标怎么办

如果 envelope 三件套有缺：

- 缺 authority_layers ≥ 2 → 跳回 T1 检查 merger 是否真在 apply 路径里调用
- 缺 evidence_text → 检查 [packages/retrieval/semantic_service.py](../packages/retrieval/semantic_service.py) 序列化路径
- 缺 visual_evidence → 检查 applier 是否真把 `visual_evidence_anchor` 行写入；查 [packages/review/applier.py](../packages/review/applier.py) 的 `apply_visual_evidence` 是否被调

记录在 REPORT 的"Issues found"段，操盘手 review 后决定是否继续 T4 或先修。

---

## T4. 把 apply 主流程抽到 packages/review/applier.py（可选，1 天内）

### T4.1 为什么

[packages/review/applier.py](../packages/review/applier.py) 当前 90 行，只放了 visual evidence 持久化（`build_visual_evidence_rows` / `apply_visual_evidence`）。

但 `scripts/apply_review_packs_batch.py` 的主流程（review pack → KO 落库 + authority fields + cross_source_merger 调用）**还在 scripts/ 里**。这违反 [docs/34 §5.4](34_compile-gap-and-execution-plan.md#54-w2-起scripts-收敛到-packages持续-4-周) 的收敛目标。

T4 是 §5.4 "scripts/ 收敛" 的关键一步，但不阻塞 T1-T3，所以列为可选。**有时间就做**。

### T4.2 操作

把 [scripts/apply_review_packs_batch.py](../scripts/apply_review_packs_batch.py) 中以下逻辑抽到 [packages/review/applier.py](../packages/review/applier.py)：

- `apply_review_pack(pack_path, db_session, ...)` —— 单 pack 落库主函数
- `build_knowledge_object_row(candidate, merged_ko, ...)` —— 构造 KnowledgeObjectV2 行
- `build_evidence_rows(merged_ko, ...)` —— 构造 KnowledgeObjectEvidenceV2 行（含 v0.2 字段）

`scripts/apply_review_packs_batch.py` 改为 thin CLI（≤ 100 行）：

```python
# scripts/apply_review_packs_batch.py
from packages.review.applier import apply_review_pack
...
def main():
    args = parse_args()
    db = SessionLocal()
    for pack_path in args.pack_paths:
        apply_review_pack(pack_path, db, ...)
```

### T4.3 验证

`scripts/apply_review_packs_batch.py` 文件行数 ≤ 100；`packages/review/applier.py` 主流程函数齐全；`pytest tests/test_apply_review*.py` 全过。

`bash scripts/check-boundaries` 通过。

---

## 5. 执行顺序硬约束

| 阶段 | 任务 | 阻塞关系 |
|------|------|---------|
| 1 | T1 修 merger plumbing | 无 |
| 2 | T2 真跑 MiMo 视觉抽取 | 不依赖 T1，可并行；但建议 T1 先做完，避免操盘手注意力分散 |
| 3 | T3 端到端 smoke | **依赖 T1 + T2 完成** |
| 4 | T4 applier.py 收敛 | 可选；T3 跑完后再做 |

T3 是这一轮的"交付验收"，T1 + T2 是为它服务的。

---

## 6. 不做的事（防止散）

| 项目 | 为什么不做 |
|------|----------|
| 改 v0.2 契约字段 | W1 已完成 + 已 mirror，不要动 |
| 重写 doc 26 milestone | 等本轮所有任务完成后再说 |
| 概念片 / 关系图合成 | §11.6 D5 的活，**不在本轮**；等 T1-T3 跑通后再开 |
| 跑大批量（> 5 个 manual） | 本轮验证为主；规模化下一轮 |
| 修 health checks 跑批入口 | §5.5 的活，**不在本轮**；扩 4 维度的代码已写，跑批 CLI 等下一轮 |
| 重新评估方向 | 不在范围内 |
| 改 canonical_key registry yaml 已有条目 | append-only 硬约束（[docs/34 §6](34_compile-gap-and-execution-plan.md) 治理纪律 2） |
| 重构 scripts/ 大批量重命名 | 抽出来就抽，不抽就放着 |

---

## 7. 通用纪律（每个任务都适用）

1. **每个任务结束必须跑 `bash scripts/check-all`**，4 个 gate 全过
2. **每个任务结束必须跑 `pytest tests/ -x`**，288+ 测试全过
3. **每个任务结束必须 commit**，commit message 引用本文档（如 `feat(merger): T1 wire LLM canonical_key (docs/35 §T1)`）
4. **LLM 调用 audit log** 写 `output/llm_audit/<date>/<run_id>.jsonl`
5. **配额监控**：T2 任何 MiMo 调用必须经过 token tracker，超 1 亿停
6. **任何 schema 变更**走 migration-first（本轮没新 schema 变更，仅 T1 改逻辑、T2 写 row、T3 验证、T4 重组）
7. **不要新建 HTTP client**：LLM 调用走 [packages/compiler/llm_compiler.py](../packages/compiler/llm_compiler.py) 的 `_request_json_completion`
8. **不要 print API key** 或 commit `scripts/llm_backends.json`

---

## 8. Done means（本轮整体）

完成下列 5 条本轮才算关闭：

1. T1 单元测试 pass + W3 D5 回测 4 个指标全达标（或注明 single-pair pass + full pending T3）
2. T2 至少 3 个 PDF 跑出 `document_page_image` 行 + 操盘手抽 20 样本 image_type 准确率 ≥ 70%
3. T3 端到端跑通：至少 1 个 KO envelope 三件套（authority_layers ≥ 2 + evidence_text + 可选 visual_evidence）齐全
4. `pytest tests/` 全过；`bash scripts/check-all` 全过
5. 三份 REPORT.md 到位（W3 D5 update + T2 visual_evidence_batch + T3 e2e_smoke）

完成后 KnowFabric 才能宣称"真能给 sw_base_model 喂权威 KO"，进入下一轮（规模化跑批 + sw_base_model 接入 + 概念片 / 关系图实验）。

---

## CHANGELOG

- **2026-05-11**：初稿。基于 Codex W1-W3 sweep 后的实际状态，把 3 个端到端硬伤拆成 T1-T3 可执行任务，T4 作为 §5.4 收尾。
