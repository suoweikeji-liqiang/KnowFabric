# Compile Gap Diagnosis and Execution Plan

**Status:** Direction Note + Execution Plan
**Last Updated:** 2026-05-11
**Scope:** 当前实现与 vNext compile/check/publish 设计 + v0.2 契约的差距诊断，以及补救执行计划。

本文不取代 [docs/23_vnext-compile-check-publish-direction.md](23_vnext-compile-check-publish-direction.md) 的方向论述，也不取代 [docs/24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md) 的契约约束。本文回答两个问题：

1. 项目实际做到了什么、缺了什么、为什么差距是结构性的
2. 接下来 4 周如何按优先级把差距补上

---

## 0. 前提假设

本计划成立的前提是：**当前方向（ontology-first + Compile/Check/Publish + v0.2 契约）是对的**。要做的是把承诺的活儿干完，不是改方向。

如果操盘手决定重新评估方向，本计划必须重写。其他读者继续读之前请先确认这个前提。

---

## 1. KnowFabric 是什么

KnowFabric 不是搜索引擎、不是 RAG、不是文档管理系统、不是对外的知识产品。

KnowFabric 是 **sw_base_model 的领域知识编译器** —— 把工业（暖通、驱动）领域的：

- OEM 厂家手册（特灵、约克、ABB ⋯）
- 行业标准（ASHRAE、GB ⋯）
- 维修 SOP、内部工程笔记
- 现场观察事件

这些**形式各异、版本打架、措辞不同、有扫描件、有中英混杂**的原始素材，编译成 sw_base_model 的 agent 能直接消费的：

- 类型化知识对象（KO）：`fault_code` / `parameter_spec` / `operational_sequence` / `diagnostic_step` 等
- 带六层证据链（doc → page → chunk → evidence_text → KO → delivery）
- 带权威分层（industry_standard > oem_manual > field_observation ⋯）
- 带跨源共识状态（agreed / partial_conflict / material_conflict）
- 带适用范围（brand / model / applicability scope）

类比：跟 LLVM 把源代码编译成机器能执行的指令是同一件事，只是把"源代码"换成"工业原始资料"，"机器指令"换成"agent 能消费的 KO"。

---

## 2. 价值在哪里

### 2.1 对 sw_base_model 的价值

具体场景：客户现场 York YK 离心机监控显示冷冻水出水 47°F，sw_base_model 的 agent 要回答"正常吗"。

**没有合格 KnowFabric 时**，agent 能给的答复是"我搜了一下，找到几段相关文本，看起来可能正常"。这种答复是 demo 级别，到不了产品。

**有合格 KnowFabric 时**，agent 能给的答复是：

> 基于 ASHRAE G36 §5.22 + York YK manual p.43 + 你们另外 3 个项目的 York YK 实测数据，这型机的合规设定点应为 44°F ± 1°F。当前 47°F 偏离 3°F，超出 ASHRAE 容差。注意约克手册建议高湿度环境上调到 45°F，请确认现场湿度。建议动作：[A/B/C]。引用 [证据链]。

差距不在"能不能搜到"，差距在"agent 能不能给出有依据、可审计、带兼容性判断的回答"。这种回答能力**只能靠预先编译好的、带权威分层的 KO** 才能给出，临场让 LLM 读 PDF 拼是不稳定、不可审计、塞不下、上一秒 ASHRAE 下一秒变维基的。

### 2.2 为什么这件事别人做不出

开源 RAG 解决前 30%（找到相关文本）。剩下 70%（知识权威化、跨源合并、兼容性标注、健康检查）是脏苦工程活，要凑齐三个条件：

1. 懂行业（setpoint / sequence of operation / fault family 是什么）
2. 懂权威分层（行业标准 vs OEM 手册 vs 现场观察的相互覆盖关系）
3. 有真实多源对比 + 现场反馈回流

操盘手凑齐了这三个条件（运营公司 + sw_base_model 做下游消费方 + 几百个真实项目），是真护城河。

---

## 3. 当前实现现状（2026-05-11 快照）

### 3.1 做得对的地方（这些别动）

| 项目 | 实现位置 | 状态 |
|------|---------|------|
| Document/Page/Chunk 三层 + 强制 traceability | [packages/db/models.py](../packages/db/models.py) | 稳定 |
| LLM 抽取 + judge 两阶段 | [packages/compiler/llm_compiler.py](../packages/compiler/llm_compiler.py)、各 `scripts/run_*` | 稳定 |
| Verbatim chunk anchoring（防幻觉） | 散布在 `scripts/run_hvac_doclevel_extraction_batch.py` 等 | 稳定，但逻辑没抽到 packages |
| 文档级单次大上下文抽取（ASHRAE G36 196k tokens 一发） | [scripts/run_ashrae_g36_parallel_sections.py](../scripts/run_ashrae_g36_parallel_sections.py) 等 | 稳定 |
| LLM 文档/章节路由（刚落地） | [scripts/route_standard_sections_with_llm.py](../scripts/route_standard_sections_with_llm.py) | 新，刚跑通 |
| Trust level L3/L4（同文档内 chunk 数） | apply 路径 | 稳定但语义不到位（见 4.1） |
| 标准条款级 chunking + clause citation | G36 vertical | 稳定 |

### 3.2 缺的地方（按严重度排）

| 缺口 | 现状 | 设计要求来源 |
|------|------|-------------|
| **跨源合并** | 同一参数在 5 本手册 → 5 条独立 KO，靠事后 `dedupe_standard_knowledge.py` 去重 | doc 23 §"What 'Compile' Means"、doc 24 §4.2 |
| **权威仲裁** | 0 行代码实现 §11.3 的 6 条规则；所有 KO 都是 `single_source` | doc 24 §11.3 |
| **v0.2 契约字段未落地** | `consensus_state` / `authority_layers` / `highest_authority_level` / `conflict_summary` / `redistribution_restricted` 在存储和 API 都没加 | doc 24 §4.2、§11.5 |
| **concept brief / relation view** | 完全没有 | doc 23 §"Compiled Knowledge Asset Forms" |
| **health checks 骨架化** | [packages/health/checks.py](../packages/health/checks.py) 只实现 weak_evidence / anchor_uncertainty / coverage_gap / applicability_missing；conflict / drift / applicability ambiguity / anchor quality 缺 | doc 23 §"Check"、§"Health Checks As A Maintenance Mechanism" |
| **工程包结构空壳** | `packages/extraction/`、`packages/review/`、`pipelines/` 都是空 README；70+ 脚本散在 `scripts/` | [CLAUDE.md](../CLAUDE.md) Module Dependency Rules |
| **alias mining** | 无独立 LLM 别名挖掘 pass；vendor naming 变体只能靠 review 手填 | doc 24 §2.2 |

### 3.3 默契性偏离

[docs/26_ai-assisted-compilation-pilot-milestone.md](26_ai-assisted-compilation-pilot-milestone.md) 明确写 `parameter_spec` 保留 rule-first，但实际最新的 run 3（`output/parameter_spec_vertical/20260506T083330Z_*`）是纯 LLM 文档级抽取，rule baseline 返回 0 candidates。

这本身不是坏事（单文档大 context LLM 抽取效果确实比规则好），但说明 milestone 26 文档已经不反映真实路线。本文档生效后，应在 W4 之前同步修订 doc 26。

---

## 4. 为什么现状不合适

### 4.1 单文档抽取 ≠ 知识编译

当前流水线对每份文档独立处理 → 出候选 → judge → 存 JSONL → review → 落 KnowledgeObjectV2。

**document-local 是结构性问题**：

- 同一参数 ("chilled water setpoint") 在特灵手册说 44°F、约克说 42°F、ASHRAE 说 44°F
- 当前输出：3 条互相不知道彼此存在的 KO 候选
- 应该输出：1 条 KO，3 条 authority_layer，consensus_state = `partial_conflict`

这意味着 KnowFabric 把自己**最值钱的那部分活儿没干，推给了 sw_base_model 下游**。sw_base_model 不是为了拼数据碎片而生的，它是给客户做项目级运维判断的。

trust level L3/L4 当前是"同文档内 chunk 命中数"，**不是跨源 corroboration 强度**。语义跟设计差一层。

### 4.2 v0.2 契约 5 天前签字，0 行字段落地

[docs/24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md) §4.2（2026-05-01 binding）强制要求 KO 响应必须带：

- `consensus_state`
- `highest_authority_level`
- `authority_layers`
- `conflict_summary`
- `redistribution_restricted`

外加 query 参数 `min_authority_level` / `consensus_filter` / `include_restricted_evidence`。

实际：[packages/db/models_v2.py](../packages/db/models_v2.py) 的 `KnowledgeObjectV2` 一个字段都没有；[packages/retrieval/semantic_service.py](../packages/retrieval/semantic_service.py) 不返回这些字段；[apps/api/main.py](../apps/api/main.py) 没有这些 query 参数。

**这就是 memory 里早就标的 "biggest risk is the unwritten contract between the two repos"，5 天就现形了**。sw_base_model 按 v0.2 接 KnowFabric → 拿到一堆空字段。

### 4.3 工程上脚本化代替了模块化

- `pipelines/` 只有 README
- `packages/extraction/` 只有 README
- `packages/review/` 只有 README
- `scripts/` 70+ 个文件

每来一个新课题（G36 全本 / G36 章节 / OEM 文档级 / multimodal / MiMo OCR）就新写一个脚本，跑完出 JSONL，靠后续脚本去合并 / 去重 / apply。

CLAUDE.md 把模块边界写成 binding contract，但实际工程把所有真活都甩进 `scripts/`，binding 没生效。再走 2-3 个月，`scripts/` 会变成谁都不敢碰的考古现场。

---

## 5. 执行计划

### 5.1 总览

| 周次 | 主题 | 目标 |
|------|------|------|
| W1 | v0.2 契约字段落地 | 解除 sw_base_model 接入阻塞 |
| W2–W3 | 跨源合并 + 权威仲裁 | 补"编译"环节 —— 核心活 |
| W2 起持续 | packages 收敛 | scripts/ 70+ 散件 → 稳定模块 |
| W4+ | health 检查补齐 | conflict / drift / applicability / anchor |

每个阶段的 done means 必须可机器/可审计验证。

---

### 5.2 W1：v0.2 契约字段落地（5 工作日）

**为什么先做**：sw_base_model M2 V1 等着接，今天 API 一个 authority 字段都不返。这是当前最高优先级阻塞项。

#### D1：DB schema + 模型

新建：

- `migrations/versions/008_add_authority_fields.py`：给 `knowledge_object` 表加
  - `consensus_state` `VARCHAR(32) NOT NULL DEFAULT 'single_source'`
  - `highest_authority_level` `VARCHAR(32) NULL`
  - `authority_summary_json` `JSON NULL`
  - `conflict_summary` `TEXT NULL`
  - `deviation_justification_json` `JSON NULL`
- `migrations/versions/009_add_document_redistributable.py`：给 `document` 表加
  - `is_redistributable` `BOOLEAN NOT NULL`，server default 通过迁移 SQL 按 `authority_level` 推断（`industry_standard|regulatory_code|unspecified` → false，其余 → true）

同步更新 [packages/db/models_v2.py](../packages/db/models_v2.py) 对应字段。

**Done means**：`alembic upgrade head` 通过；老的 23 条 KO 默认 `single_source` + 老的 Document 默认 `is_redistributable` 正确不报错；`pytest tests/` 全过。

#### D2：历史 KO 回填 + apply 路径写入

- 新建 `scripts/backfill_authority_v02.py`：给所有现存 KO 填
  ```json
  {
    "authority_summary_json": {
      "layers": [{
        "authority_level": "<推断>",
        "publisher": "<from doc>",
        "citation": "<from evidence>",
        "evidence_role": "primary",
        "value_summary": "<from structured_payload>"
      }]
    },
    "consensus_state": "single_source",
    "highest_authority_level": "<推断>"
  }
  ```
- 改 [scripts/apply_review_packs_batch.py](../scripts/apply_review_packs_batch.py)：新落地 KO 必须填这 5 个字段（即使全是 single_source 也填，保证流程统一）。

**Done means**：DB 里没有 `authority_summary_json IS NULL` 的 KO；新加 KO 通过 apply 流程落地后字段完整。

#### D3：semantic_service 序列化

改 [packages/retrieval/semantic_service.py](../packages/retrieval/semantic_service.py)：

- 每个 KO 响应 envelope 加 `authority_layers` / `consensus_state` / `highest_authority_level` / `conflict_summary` / `redistribution_restricted`
- 新增 query 参数：`min_authority_level` / `consensus_filter` / `include_restricted_evidence`
- 当 `is_redistributable=false` 且 `include_restricted_evidence=false`：把 `evidence_text` 替换为 `<citation> + ≤200 字 paraphrase`，envelope 标 `redistribution_restricted: true`
- 当 `include_restricted_evidence=true`：返回 verbatim + 写 audit log（log 内容：caller、KO ID、doc ID、timestamp）

**Done means**：手测 `/api/v2/domains/hvac/equipment-classes/centrifugal_chiller/parameter-specs` 看到完整 v0.2 envelope。

#### D4：API 路由 + MCP 工具对齐

- [apps/api/main.py](../apps/api/main.py) 6 个 v2 路由（equipment-class-explanation / fault-knowledge / parameter-profile / maintenance-guidance / application-guidance / operational-guidance）补 3 个新 query 参数
- [apps/mcp/main.py](../apps/mcp/main.py) 6 个对应 MCP 工具响应 schema 跟 API 对齐
- 新增集成测试：
  - 测 1：ASHRAE chunk 不传 `include_restricted_evidence` → 返回 paraphrase
  - 测 2：传 `include_restricted_evidence=true` → 返回 verbatim + audit log 落盘
  - 测 3：`min_authority_level=oem_manual` → 过滤掉 `unspecified` 类 KO

**Done means**：`pytest tests/` 全过 + 3 个新加的契约测试通过。

#### D5：契约 mirror + 配对 PR

- [scripts/check-contract-mirror](../scripts/check-contract-mirror) 跑通，新 §1-11 SHA 写到 `scripts/contract_sha_baseline.txt`
- 跟 sw_base_model 的镜像 PR 同步上车（双仓库 CI 必须看到对端 PR SHA 才能合）

**Done means**：sw_base_model 那边能拉一个 KnowFabric 实例做端到端调用，拿到完整 v0.2 envelope；`scripts/check-all` 全过。

#### W1 不做的事

- 不做跨源合并（W2-W3 的活，挤进来 D5 走不完）
- 不做 `conflict_summary` 真值填充（先全部 NULL）
- 不动 admin-web UI（等字段稳了再说）
- 不重写 [docs/26_ai-assisted-compilation-pilot-milestone.md](26_ai-assisted-compilation-pilot-milestone.md)（W4 之前再说）

---

### 5.3 W2–W3：跨源合并 + 权威仲裁（10 工作日）

**为什么是核心**：这一步不做，KnowFabric 永远只是"打孔机"，永远不是"编译器"。其余改进都是装饰。

#### W2 D1-D2：canonical_key 归一化

新建 `packages/compiler/canonical_key.py`：

```
输入: ontology_anchor + knowledge_type + 一组候选的 parameter_name/title
输出: 1 个稳定 canonical_key + 把每个候选 map 到它

机制:
  1. 查 packages/compiler/canonical_key_registry.yaml (append-only)
  2. 未命中 → LLM 归一化 (deepseek-v4-pro, temperature 0)
  3. LLM 输出走 hash 缓存 (sha1(sorted(inputs)) → canonical_key)
  4. 一旦写到 KnowledgeObjectV2.canonical_key，注册到 registry，永不改
```

**硬约束**：canonical_key 一经发布不可修改（改了等于换 KO，破坏下游 KO ID 引用）。registry 是 append-only。

**Done means**：给 `["Active Chilled Water Setpoint", "动态冷冻水设定", "CHWS Setpoint", "leaving water temperature setpoint"]` → 稳定输出 `chiller_chilled_water_supply_temperature_setpoint`；跑 10 次同输出。

#### W2 D3-D4：跨候选合并器

新建 `packages/compiler/cross_source_merger.py`：

```
输入: 同 ontology_anchor + 同 knowledge_type 的 N 个 verified 候选
处理:
  1. canonical_key 归一化 → 分组
  2. 每组内逐候选 → 1 条 authority_layer
     {authority_level, publisher, citation, value_summary, evidence_role, doc_id, chunk_ids}
  3. 数值/范围/默认值比较 → consensus_state
     - 全同（数值 ±5% 内或字符串完全相同）→ agreed
     - 部分差异在容差内 → partial_conflict
     - 显著差异 → material_conflict
     - 1 个源 → single_source
  4. highest_authority_level = min(rank) over layers (rank 见 doc 24 §11.1)
  5. 输出 1 个 KO + N 条 evidence rows
```

数值容差初始用 ±5%（保守），靠 review 反馈调。

**Done means**：丢进 5 个候选（3 个说 44°F、2 个说 42°F）→ 输出 1 个 KO，`consensus_state=partial_conflict`，`authority_layers` 含 5 条。

#### W2 D5：authority_level 自动判定

新建 `packages/compiler/authority_classifier.py`：

```
输入: Document (file_name, publisher, doc_kind, source_metadata)
输出: authority_level ∈ doc 24 §11.1 枚举

规则优先:
  - file_name contains "ASHRAE Guideline|Standard|GB/T|GB " → industry_standard
  - file_name contains "regulatory|法规|强制" → regulatory_code
  - publisher in OEM 白名单 (Trane/York/Carrier/Daikin/McQuay/约克/特灵/...) → oem_manual
  - source_metadata.kind == "field_observation" → field_observation
  - source_metadata.kind == "internal_sop" → internal_sop
  - 其余 + LLM 兜底 (deepseek-v4-pro, temperature 0)
```

**Done means**：现存所有 Document 的 `authority_level` 自动标完；人工抽样 20 条 ≥ 90% 准确；is_redistributable 也跟着重算。

#### W3 D1-D2：merger 接入 apply 流程

改 [scripts/apply_review_packs_batch.py](../scripts/apply_review_packs_batch.py)：

从「逐候选写 KO」改成：

```
1. 把本次 batch 候选 + 已在 DB 的同 ontology_anchor + knowledge_type KO 一起送进 merger
2. merger 输出: 新 KO + 老 KO 的 authority_layer 增量 + consensus 重算
3. 按差量 upsert (UPDATE existing or INSERT new)
4. 触发 material_conflict 的 KO → 自动进 review_pack，review_status='conflict_review_required'，不直接 publish
```

老 `dedupe_standard_knowledge.py` 在此之后弃用，逻辑迁到 merger。

**Done means**：连续 apply 5 本 chiller manual，DB 里同一参数的 KO 数量 ≤ 5（不是 5 个独立 KO，至少能看到几个合并发生）。

#### W3 D3：authority arbitration

新建 `packages/compiler/authority_arbitration.py`：实现 doc 24 §11.3 的 6 条规则：

1. field_observation w/ ≥ N 项目实测样本（N 取 doc 24 §10 O6 默认 5）覆盖 industry_standard
2. 较新 industry_standard 覆盖较旧 industry_standard
3. industry_standard 覆盖 oem_manual
4. 同 vendor 较新 oem_manual 覆盖较旧
5. oem_manual 覆盖 vendor_application_note
6. authority ≥ oem_manual 覆盖 academic_reference

输出 `recommended_value` + `arbitration_reason` 进 `authority_summary_json.arbitration`。

**Done means**：当一个 KO 同时含 industry_standard + oem_manual 不同值时，能自动按规则选优并写 reason。

#### W3 D4：冲突进 review

- `material_conflict` KO 强制进 review_pack，`review_status='conflict_review_required'`
- `partial_conflict` KO 可 publish 但 `conflict_summary` 必填
- review 通过的 KO 可手填 `deviation_justification_json`（覆盖 industry_standard 时 doc 24 §11.4 必填）

**Done means**：跑出一个 material_conflict 案例，进了 review → 人审选了优先源 → KO 状态变 published。

#### W3 D5：真实多源回测

跑这 6 个源（操盘手协助找齐）：

- 特灵 CVGF（已有，`doc_883beab5e0004a2c`）
- 约克 YK manual
- 开利离心机 manual
- 大金离心机 manual
- 麦克维尔离心机 manual
- ASHRAE G36 chiller-related sections

记录指标：

| 指标 | 目标 |
|------|------|
| multi-source rate (KOs with ≥2 authority_layers / total KOs) | ≥ 20% |
| partial_conflict KO 数 | ≥ 3 |
| material_conflict KO 数 | ≥ 1 |
| agreed KO 数 | ≥ 5 |

**Done means**：4 个指标全达 + 产出 `output/w3_multisource_baseline/REPORT.md` 供操盘手抽审。

#### W2-W3 风险

| 风险 | 应对 |
|------|------|
| canonical_key LLM 输出不稳定 → KO 重复 | hash cache + registry append-only + 离线评测（同输入跑 10 次必须同输出） |
| 数值容差太松 → 错合并 | 默认 ±5%，有问题靠 review 反馈调；不要先松后紧 |
| material_conflict 频繁触发 → review 队列爆 | 先只跑 chiller domain；其他类目跑前抽样 50 条手工标基线 |
| 老 KO 跳过 merger | apply 路径硬性要求所有 KO 必经 merger，加单元测试卡死 |

---

### 5.4 W2 起：scripts/ 收敛到 packages/（持续 4 周）

**为什么**：`pipelines/`、`packages/extraction/`、`packages/review/` 空壳，70+ scripts 散乱。再 2 个月没人能维护。

#### 收敛对照表

| 现在散在哪里 | 抽到 | 抽什么 |
|------------|------|--------|
| `scripts/run_hvac_doclevel_extraction_batch.py` 核心循环 | `packages/extraction/doc_level.py` | 单文档 LLM 抽取 |
| 上面那个 + `run_ashrae_g36_*.py` × 4 共用代码 | `packages/extraction/judge.py` | extract/judge 两阶段 |
| 上面那些 | `packages/extraction/anchor.py` | verbatim chunk anchoring |
| `run_ashrae_g36_full_book.py` + `_parallel_sections.py` + `_remaining_batches.py` | `packages/extraction/section_extractor.py` + 1 个统一 CLI | 按章节抽取（mode 参数控制） |
| `apply_review_packs_batch.py` 核心 | `packages/review/applier.py` | review-pack → KO 持久化 |
| `dedupe_standard_knowledge.py` | `packages/compiler/cross_source_merger.py`（W2-W3 已规划） | 弃用旧脚本 |
| `route_standard_sections_with_llm.py` | `packages/compiler/section_router.py` | LLM 文档/章节路由 |

#### 收敛目标

- `packages/extraction/` 3-4 个稳定模块
- `packages/review/` 有 `applier.py`
- `packages/compiler/` 6-7 个模块（含 W2-W3 新加的 + 现有 `llm_compiler.py` / `rule_compiler.py` / `equipment_matcher.py` / `contracts.py`）
- `scripts/` 减到 ≤ 30 个，每个 ≤ 100 行 thin CLI wrapper
- `pipelines/` 放 YAML 配置 + thin orchestrator（不放业务逻辑）

#### 治理规矩

写进 [CLAUDE.md](../CLAUDE.md)：**新加 scripts 前必须先查 `packages/` 有没有对应模块。没有就抽出来再写**。

**Done means**：`bash scripts/check-boundaries` 跑过 + `scripts/` 文件数 ≤ 30 + 三个 README-only 包都有实际代码。

---

### 5.5 W4+：health 检查补齐（长尾，按价值排）

只在 W1-W3 稳定后开始。按对 sw_base_model 价值排序：

#### P1：conflict_detection（KO 间冲突）

跟 cross_source_merger 互补：merger 管 KO 内冲突（同 canonical_key 的多源），这个管 KO 间冲突（不同 canonical_key 但本质同概念）。

- 扫所有 same-anchor + same-type KO 对，做 pairwise 数值/范围比较
- 产 finding → 进 review queue

#### P2：terminology_drift（vendor 命名变体）

- LLM 任务：给定同 ontology_anchor 下所有 `parameter_name`，输出哪些是同一概念的不同叫法
- 输出 alias 候选 → 进 review → 通过后写 `OntologyAliasV2`

#### P3：applicability_ambiguity（缺 brand/model 但 evidence 里有）

- LLM 读 evidence_text → 抽出隐含的 brand/model
- 进 review 决定接不接

#### P4：anchor_quality（ontology_anchor 是否合理）

- LLM 读 evidence_text → 判断 anchor 是否合理
- 不确定的进 review

#### 通用模式

每个 health check 都按 **扫描 → 产 finding → 进 review queue → 人审** 跑。**绝不自动改 KO**。

---

## 6. 治理纪律（贯穿所有阶段）

1. **每个新 KO 必须经过 cross_source_merger**（哪怕只有 1 个 source，也填 single_source）
2. **canonical_key 一经发布永不改**（registry append-only）
3. **每个 LLM 调用必须可回放**：input + output 写 audit JSONL（`output/llm_audit/<date>/<run_id>.jsonl`），跑回测时离线重放
4. **新加 scripts 前查 packages**，没有就抽出来再写
5. **material_conflict 必须人审**，不自动 publish
6. **新 KO 必填**：`authority_summary_json`、`consensus_state`、`curated_against_ontology_version`、`highest_authority_level`
7. **scripts/llm_backends.json 永不入仓**（含 API key）
8. **改 v0.2 契约 §1-11 任何字段必须配对 PR + bump CHANGELOG**

---

## 7. 显式不做的事（防止散）

| 项目 | 为什么不做 |
|------|----------|
| vector embedding / 向量召回 | 跟跨源合并无关，W4 后再说 |
| admin-web UI 重构 | 现状能撑住，不动 |
| 跨域 graph 推理 | 等 HVAC 完整跑通 |
| fault_code / diagnostic_step 新 vertical | 先把 parameter_spec 跨源跑顺，再复制套路 |
| 自动 publish material_conflict KO | 风险大，必须人审 |
| retroactively 改老脚本命名 | 抽出来就抽，不抽就放着 |
| 重写 docs/26 milestone | 等 W4 路线确定后一并改 |
| 重新评估 ontology-first 方向 | 不在本计划内；要做就先暂停本计划 |

---

## 8. W1 第一周明确日程

| 天 | 必交 | 验证 |
|----|------|------|
| D1 | `migrations/008_add_authority_fields.py` + `migrations/009_add_document_redistributable.py` + models_v2.py 字段 | `alembic upgrade head` 通过 |
| D2 | `scripts/backfill_authority_v02.py` 跑完 + `apply_review_packs_batch.py` 写新字段 + 单元测试 | DB 无 `authority_summary_json IS NULL` 的 KO |
| D3 | `semantic_service.py` 返回 v0.2 envelope + 3 个 query 参数 + paraphrase 替换 | 手测 1 个 endpoint 看到完整 envelope |
| D4 | 6 个 v2 endpoint + 6 个 MCP 工具响应对齐 + 3 个新契约测试 | `pytest tests/` + `bash scripts/check-all` 全过 |
| D5 | `scripts/check-contract-mirror` 通过 + 新 SHA 写入 baseline + 配对 PR | sw_base_model 端拿到 v0.2 envelope |

W1 结束后 sw_base_model 不再被阻塞，可开始按 v0.2 接入。

---

## 9. 给 Codex 的执行约束

1. 按 W1 → W2-W3 顺序做，不要跳。W2 之前 v0.2 字段必须先落地
2. 每个 D 的产出必须可机器验证（migration / pytest / curl 手测）
3. 任何对 [docs/24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md) §1-11 的改动必须配对 sw_base_model PR
4. 任何 LLM 调用必须用 `packages/compiler/llm_compiler.py` 已有的 `_request_json_completion` 路径或扩展它，不要新建 HTTP client
5. 新增 SQLAlchemy 字段必须先 migration 后 model（保持 migration-first）
6. canonical_key registry yaml 单独 commit，不跟代码改动混
7. 每周末跑一次 `bash scripts/check-all`，记录 baseline 进度
8. 跑 W3 D5 多源回测前先跟操盘手确认能拿到那 5 本厂家手册
9. 涉及 `scripts/llm_backends.json` 的需求一律走 env var 注入，不要 print/log key
10. 跑 W1 D2 backfill 前先 `pg_dump knowfabric > /tmp/pre_v02_backup.sql`，能 rollback

---

## 10. 不属于本计划的开放问题

以下问题留给操盘手 / 联合评估，不阻塞 W1-W3 执行：

- doc 24 §10 中的 O1 / O2 / O5 / O6 / O10 / O11
- 是否给 fault_code / diagnostic_step 也开 LLM doc-level vertical（建议 W4 后再议）
- 是否需要 vector 召回作为 fallback（doc 31 已定不阻塞）
- admin-web 是否需要 v0.2 字段的 UI 展示（W4 后再议）

---

## CHANGELOG

- **2026-05-11**：初稿。诊断当前 compile gap，定义 W1-W4+ 执行计划。
