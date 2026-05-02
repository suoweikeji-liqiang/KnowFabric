# Contract v0.2 Proposal — Authority Hierarchy & Conflict Resolution

> **Status**: ✅ APPLIED 2026-05-01 — operator approved on `agree`, paired changes merged into both [docs/24](24_knowfabric-sw-base-model-contract.md) and `sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`. This file remains as the historical proposal record.
> **Original Status**: PROPOSAL — paired PR required between KnowFabric and sw_base_model before merging
> **Date**: 2026-05-01
> **Companion design**: [docs/27_authority-schema-upgrade-design.md](27_authority-schema-upgrade-design.md)
> **Current contract**: [docs/24_knowfabric-sw-base-model-contract.md](24_knowfabric-sw-base-model-contract.md) **v0.2** (was v0.1 at proposal time)
> **Target SHA baseline**: ✅ ACHIEVED — `7aa6193d0a44b596d1f3e97a3aff0af495c3cd35aa5ff9693d61de00482efdd1` (replaces v0.1 baseline `46db2983...`)

---

## 0. Why a contract bump

Contract v0.1 established ownership boundary, ID conventions, ontology versioning, and feedback channels — but said nothing about **authority of knowledge sources**. The Round-2 vertical proved that single-source OEM-manual KOs can be produced cleanly; the next vertical (and any real production use) will need to handle:

- Multi-source KOs (ASHRAE + Trane both describing same parameter)
- Authority-typed sources (industry_standard vs oem_manual vs field_observation)
- Conflict surfacing (when sources disagree)
- Operator field truth (field observations override formal standards with documented justification)

Without contract v0.2, sw_base_model agent control plane has no defined way to consume authority-aware responses. The schema upgrade in docs/27 changes API responses; the contract must reflect this.

---

## 1. Changes summary (apply to BOTH `docs/24_knowfabric-sw-base-model-contract.md` and `sw_base_model/design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`)

### Change 1: Add a new authority subsection to §2 (归属边界)

Add after §2.2 (KnowFabric 拥有：领域知识内容):

```markdown
### 2.4 权威分层归属

知识源的权威分层（authority typing）属于 KnowFabric 内部模型，由 KnowFabric 维护：

- Document 层的 `authority_level` / `publisher` / `standard_id` 等字段属于 KnowFabric Document 表
- KO 层的 `authority_summary_json` / `consensus_state` / `highest_authority_level` 属于 KnowFabric KO 表
- 跨源 corroboration 与冲突检测逻辑属于 KnowFabric 编译流水线

sw_base_model 不复制权威分层模型，**只通过契约 §4 数据流读取**这些字段做下游决策（agent 选择信源、合规判定、用户展示）。

权威分层的 enum 值（authority_level 枚举集）由 KnowFabric 在 `packages/core/semantic_contract_v2.py` 维护，作为契约附录引用。新增枚举值需要 contract bump（PATCH 版本即可）。
```

### Change 2: Replace §4.2 with authority-aware data flow

Replace §4.2 in current contract with:

```markdown
### 4.2 KnowFabric → sw_base_model（sw_base_model 只读消费）

sw_base_model 各子项目消费 KnowFabric 的方式：

| 子项目 | 消费内容 | 接口 |
|--------|---------|------|
| SP1 项目理解 | `typical_points` / `typical_relations`（按 equipment_class）| `GET /api/v2/domains/{domain}/equipment-classes/{class}` |
| SP2 评估引擎 | KO 内容 + 权威分层 | `GET /api/v2/domains/{domain}/equipment-classes/{class}/{ko-type}` |
| SP3 能力工厂 | KO ID 锚定 + authority_layers 用于 capability scope | KO ID 字符串引用 |
| Agent Control Plane (DESIGN-09) | KnowFabric MCP 工具集 + authority_layers | MCP tool catalog |

每个 KO 响应必须包含的权威字段（v0.2 起强制）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `trust_level` | string | L1/L2/L3/L4，单源信号强度 |
| `consensus_state` | string | `single_source` / `agreed` / `partial_conflict` / `material_conflict` |
| `highest_authority_level` | string | 所有支撑源中最高的 authority_level |
| `authority_layers` | array | 所有支撑源的列表，每条含 level + publisher + citation + value_summary |
| `conflict_summary` | string \| null | 当 consensus_state 为冲突时填充 |

新增 query 参数（v0.2 起支持）：

| 参数 | 类型 | 说明 |
|------|------|------|
| `min_authority_level` | string | 仅返回此等级及以上的 KO（如 `industry_standard` 仅返回标准类） |
| `consensus_filter` | string | 过滤 consensus_state（如 `agreed_only` 排除冲突）|

sw_base_model 不得：

- 在本地复刻 KO 类型定义
- 修改 KnowFabric 返回的 KO 内容（只读消费，本地可缓存但不可改写）
- **绕过 authority_layers 直接判定知识权威**——必须通过 KnowFabric 暴露字段
- 绕过 ontology_version 校验
```

### Change 3: New §11 — 权威分层与冲突仲裁规则（NEW SECTION）

Insert as new §11, before §12 (open questions, currently §10 — renumber):

```markdown
## 11. 权威分层与冲突仲裁规则

### 11.1 权威等级枚举

| 等级 | slug | 形式权威排名 |
|------|------|-------------|
| 行业标准 | `industry_standard` | 1（最高形式权威）|
| 监管法规 | `regulatory_code` | 2 |
| OEM 手册 | `oem_manual` | 3 |
| 厂商应用文档 | `vendor_application_note` | 4 |
| 内部 SOP | `internal_sop` | 5 |
| 现场观察 | `field_observation` | 6（最高实践权威）|
| 学术参考 | `academic_reference` | 7 |
| 未指定 | `unspecified` | fallback |

### 11.2 跨源 corroboration 规则

KnowFabric 在编译 KO 时按以下逻辑设置 `consensus_state`：

- 单源 → `single_source`
- 多源同值（容差内）→ `agreed`
- 多源值差异在领域可接受范围（如默认值 10°F vs 12°F 仅 ±20%）→ `partial_conflict` + `conflict_summary` 描述差异
- 多源值材质性差异（如默认值 10°F vs 50°F）→ `material_conflict` + `conflict_summary` 描述

### 11.3 冲突仲裁原则（agent 消费时遵守）

**KnowFabric 不替消费方决定信源**。冲突 KO 完整暴露，由消费方按场景决策。但契约推荐以下默认仲裁顺序（agent 实现可参考）：

1. **现场观察 + 充分样本**（≥ 5 项目实测）覆盖 OEM 手册和行业标准——这是操作员场景独有信号
2. **较新的 industry_standard** 覆盖较旧的 industry_standard
3. **industry_standard** 覆盖 `oem_manual`（标准定义合规边界）
4. **同一 vendor 的较新 oem_manual revision** 覆盖较旧 revision
5. **oem_manual** 覆盖 `vendor_application_note`
6. 任何形式权威 ≥ `oem_manual` 的源 覆盖 `academic_reference`

### 11.4 现场观察特殊待遇

`field_observation` 类知识可以**反向**覆盖 `industry_standard`（运维真值优先），但必须满足：

- 该 KO 的 `authority_layers` 中存在 `field_validation` 角色 evidence
- KnowFabric KO 表的 `deviation_justification_json` 字段（v0.2 新增）必须填写：
  - 偏离的标准引用（如 `ASHRAE 90.1-2022 §6.5.3.2`）
  - 偏离的实测样本量（项目数 + 观测时长）
  - 偏离原因（运行环境、负荷特征、地理气候等）

不满足上述条件的现场观察不能覆盖 industry_standard。

### 11.5 标准文档分块、全文入库与版权保护

工业标准文档（`authority_level ∈ {industry_standard, regulatory_code}`）使用 **clause-based chunking**：

- chunk 单元为标准条款（如 §6.5.3.2），不是页面段落
- evidence_citation 字段格式：`<standard_id> §<clause>`，例如 `ASHRAE 90.1-2022 §6.5.3.2`
- 同一条款在不同 revision 中可能版本不同；契约建议保留 `historical_revision` 角色 evidence 用于审计追溯

OEM 手册保持页面段落分块；evidence_citation 格式：`<doc_name> p.<page_no>`。

**全文入库与 verbatim 保护（v0.2 强制）**：

操作员决定（2026-05-01）：标准文档**全文 verbatim 入库**到 `content_chunk.cleaned_text`，每个条款一个 chunk。这保证证据链完整、支持未来 RAG 用法。

为应对版权约束（ASHRAE 等明确禁止再分发但允许内部使用），契约约束如下：

- KnowFabric Document 表必须有 `is_redistributable` BOOLEAN 字段
- 默认值：`industry_standard` / `regulatory_code` / `unspecified` 类型 doc 默认 `false`；`oem_manual` / `internal_sop` / `field_observation` 默认 `true`
- API 序列化层（`packages/retrieval/semantic_service.py`）必须强制：
  - 当 `is_redistributable = false` 时，响应中的 `evidence_text` 替换为 `<citation> + 200-字符 paraphrased summary`，并设置 `redistribution_restricted: true` 标记
  - sw_base_model（受信任内部消费方）若需要 verbatim 全文，**必须显式传 `include_restricted_evidence: true` query 参数**才能获得
  - `include_restricted_evidence` 调用 KnowFabric 必须记审计 log
  - **任何外部消费面**（例如 sw_base_model 上层 agent 直接 expose 给客户的 chat surface）**禁止**设置此参数

sw_base_model 在 agent control plane 实现时必须保证：受版权限制的 verbatim 文本只在受控内部环境流通，**不得通过 sw_base_model 任何对外接口（chat、UI、报表）泄露给最终用户**。这一条是契约硬约束，违反将构成版权风险事件。

### 11.6 ontology_version 与 authority 解耦

`ontology_version`（契约 §5）和 `authority_level` 是正交概念：

- ontology_version 描述 sw_base_model 结构本体的版本（equipment_class / point_class / relation_type 目录）
- authority_level 描述 KnowFabric 知识源的形式权威分层

两者独立演进。ontology bump 不强制 KO 重审；authority_level 字段加入或修改也不需要 ontology bump。
```

### Change 4: Update §10 (open questions) — partially close v0.1 items, add v0.2 items

In current §10, mark these as resolved:

- O3 KnowFabric 对外通道命运 → **CLOSED**: KnowFabric 内部基础设施定位已在 charter 改写落实（contract v0.1 §9）；外部产品化推迟到 sw_base_model 自身产品化稳定后再考虑
- O4 OntologyClassV2 seed 接收方式 → **CLOSED**: 已通过 v0.1.0 + v0.2.0 ontology bump 流程吸收 KnowFabric seed + 手抄 DESIGN-01 §2.5 补完点类/关系类

Add new open questions for v0.2:

| # | 问题 | 决策方 | 截止 / 状态 |
|---|------|--------|----------|
| O6 | 现场观察样本量阈值 N（覆盖 industry_standard 所需最小样本数）默认值 | 操盘手 | 30 天 |
| O7 | 标准文档全文是否在 KnowFabric 存 | 操盘手 | **CLOSED 2026-05-01: 全文入库**。版权通过 `is_redistributable` 字段控制：默认 false，API 在 false 时用 citation+摘要替换 evidence_text 输出；内部 MCP 调用方传 `include_restricted_evidence: true` 可获取 verbatim 全文。详见 §11.5。|
| O8 | `min_authority_level` query 默认值（无显式参数时是否返回 unspecified 类）| 操盘手 | 与 v0.2 上线同期 |
| O9 | 历史 KO 的 authority_summary 是否需要重审（已入库的 23 条 parameter_spec 自动 backfill 为 single_source/oem_manual 是否可接受）| 操盘手 | v0.2 上线前 |
| O10 | sw_base_model 在 SP2 评估生成 finding 时，是否在 finding 上附 `consumed_authority_layers` 元数据用于审计 | 联合评估 | v0.2 上线后 60 天 |
| O11 | sw_base_model agent 调用 KnowFabric 时是否被授权传 `include_restricted_evidence: true`，以及是否有审计要求 | 联合评估 | 与 v0.2 上线同期 |

### Change 5: CHANGELOG entry

Append to §CHANGELOG:

```markdown
- **v0.2** (待发布日期, 2026-05-XX)：
  - 新增权威分层枚举（§11.1）
  - 新增 §11 权威分层与冲突仲裁规则
  - §4.2 数据流响应字段新增 `consensus_state` / `highest_authority_level` / `authority_layers` / `conflict_summary`
  - §4.2 新增 query 参数 `min_authority_level` / `consensus_filter` / `include_restricted_evidence`
  - §2.4 明确 KnowFabric 维护权威分层模型
  - §10 关闭 O3 / O4 / O7，新增 O6 / O8-O11
  - 现场观察反向覆盖标准的 `deviation_justification_json` 字段引入
  - 标准文档 clause-based 分块协议（§11.5）
  - 标准文档全文 verbatim 入库政策 + `is_redistributable` 版权保护机制（§11.5）
```

---

## 2. Mirror PR coordination

KnowFabric and sw_base_model 必须**同步 PR**，CI 强制 SHA 校验：

1. KnowFabric PR：编辑 `docs/24_knowfabric-sw-base-model-contract.md`，应用本提案 §1 全部 5 个变更
2. sw_base_model PR：编辑 `design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`，应用相同 5 个变更（除头部"镜像位置"位置注释外，§1-11 全部内容必须 byte-identical）
3. 两端重新计算 §1-11 SHA（注意：第 11 节是新增，重新计算后 baseline 应该和 v0.1 不同）
4. 两端的 `scripts/contract_sha_baseline.txt` 同步更新到新 SHA
5. 两端 PR 互相 reference 后再 merge

只有 KnowFabric 单边 merge 会立即触发 `check-contract-mirror` 失败，sw_base_model 那边也一样。

---

## 3. Implementation depends on this proposal being accepted

The schema upgrade in docs/27 cannot be executed until contract v0.2 is in place, because:

- Adding `authority_layers` to API responses without contract endorsement = sw_base_model has no defined way to consume them
- Standard documents cannot be ingested with `authority_level = industry_standard` until contract recognizes the enum

Recommended order:

1. Operator reviews this proposal + docs/27 design
2. Operator decides on the 5 open questions in docs/27 §9 (D1-D6)
3. Operator decides on contract O6-O10 in §10 above
4. Operator approves; paired PRs filed in both repos applying §1 changes
5. After paired PRs merge, schema implementation per docs/27 begins
6. ASHRAE validation experiment (docs/27 §8.3) is the contract v0.2 acceptance gate

---

## 4. Cost / risk note

**Effort**: contract bump itself is 1 day of paired-PR work; schema implementation per docs/27 is ~2 weeks.

**Risk**: this is a **non-breaking** addition contract-wise. Existing v0.1 consumers ignoring the new fields keep working. The new defaults (e.g., `consensus_state = "single_source"` for legacy KOs) are conservative and don't change existing semantics.

**Reversibility**: contract v0.2 → v0.3 path remains additive. No feature in v0.2 closes a future option.

---

## 5. Acceptance gate

Operator approves this proposal by responding with:

- "agree" → proceed to paired PRs + schema work
- "modify X" → list specific changes wanted before approval
- "park" → keep doc 27 + 28 as exploration only, don't ship until later

Default if no response in 7 days: parked. This proposal does not auto-promote.
