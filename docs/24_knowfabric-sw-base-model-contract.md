# KnowFabric × sw_base_model 集成契约

> **状态**：v0.2 binding contract / 2026-05-01
>
> **镜像位置**：
> - KnowFabric: `docs/24_knowfabric-sw-base-model-contract.md`
> - sw_base_model: `design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`
>
> **强制纪律**：本文件第 1-11 节内容在两个仓库必须保持一致。任何修改必须通过双仓库配对 PR 同时落地，CI 校验 SHA 一致。

---

## 0. 文档权威性

本文件是 KnowFabric 与 sw_base_model 之间的强制约束契约，不是建议性设计或方向性文档。

- 两个仓库各持一份；内容（除头部位置注释外）必须一致
- 修改契约必须配对 PR，单边修改的 PR 一律拒绝
- 契约修订递增版本号，记录在底部 CHANGELOG
- 本契约高于任一仓库的内部设计文档；冲突时以契约为准

---

## 1. 背景与角色

KnowFabric 是 sw_base_model 的**领域知识编译 + 权威引擎**。
sw_base_model 是面向客户的产品载体，KnowFabric 是它的内容供给层。

两者各自的内部架构由各自仓库的设计文档定义。本契约只定义两者之间的边界、数据流、ID 命名和强制纪律。

---

## 2. 归属边界（核心条款）

### 2.1 sw_base_model 拥有：结构本体（Structural Ontology）

- `equipment_class` 目录（Brick + 223P + `ext:` 扩展）
- `point_class` 目录（Brick 点类型 + tags）
- `relation_type` 目录（`feeds`, `hasPoint`, `isPartOf`, `ext:interlocksWith` 等）
- `location_class` 目录（Brick Location 层级 + `ext:`）
- `ontology.yaml` 文件作为单一事实源
- Brick → 223P / 223P → Open223 结构映射
- `ontology_version` 版本号的发布权（semver）

### 2.2 KnowFabric 拥有：领域知识内容（Domain Knowledge Content）

- 全部 KO 类型：`fault_code` / `parameter_spec` / `performance_spec` / `diagnostic_step` / `maintenance_procedure` / `commissioning_step` / `application_guidance` / `symptom` / `wiring_guidance`
- 别名 / 多语言标签 / OEM 命名变体（canonical_term ↔ vendor naming）
- chunk_ontology_anchor（外键引用，不存定义）
- 六层证据链 + verbatim 校验
- Trust Level 自动分层（L1-L4）
- 健康检查输出（Compile / Check / Publish vNext）
- OCR + LLM 编译流水线

### 2.3 边界示意

```
        sw_base_model（产品载体）
        ┌───────────────────────────────────┐
        │ SP1 项目实例    SP2 评估引擎       │
        │ SP3 能力工厂    SP4 平台工程      │
        │ Agent Control Plane (DESIGN-09)   │
        │                                   │
        │  ┌──────────────────────────┐    │
        │  │ 结构本体 (ontology.yaml) │    │
        │  │ - equipment_class        │    │
        │  │ - point_class            │    │
        │  │ - relation_type          │    │
        │  │ - location_class         │    │
        │  │ - ontology_version       │    │
        │  └──────────────────────────┘    │
        └───────────┬───────────────────────┘
                    │ ID 引用 (read-only)
                    │ ontology_version 同步
                    ▼
        KnowFabric（领域知识内容引擎）
        ┌───────────────────────────────────┐
        │  ┌──────────────────────────┐    │
        │  │ Knowledge Objects (KO)   │    │
        │  │ - fault_code             │    │
        │  │ - parameter_spec         │    │
        │  │ - diagnostic_step  ...   │    │
        │  │                          │    │
        │  │ Evidence Chain           │    │
        │  │ Trust Levels (L1-L4)     │    │
        │  │ Health Checks            │    │
        │  └──────────────────────────┘    │
        │                                   │
        │  Compile Pipeline: OCR + LLM      │
        └───────────┬───────────────────────┘
                    │ KO 查询响应
                    │ Health 报告
                    │ MCP 工具调用响应
                    ▼ (read-only)
                sw_base_model 上层
```

### 2.4 权威分层归属

知识源的权威分层（authority typing）属于 KnowFabric 内部模型，由 KnowFabric 维护：

- Document 层的 `authority_level` / `publisher` / `standard_id` / `is_redistributable` 等字段属于 KnowFabric Document 表
- KO 层的 `authority_summary_json` / `consensus_state` / `highest_authority_level` 属于 KnowFabric KO 表
- 跨源 corroboration 与冲突检测逻辑属于 KnowFabric 编译流水线

sw_base_model 不复制权威分层模型，**只通过契约 §4 数据流读取**这些字段做下游决策（agent 选择信源、合规判定、用户展示）。

权威分层的 enum 值（authority_level 枚举集，见 §11.1）由 KnowFabric 在 `packages/core/semantic_contract_v2.py` 维护，作为契约附录引用。新增枚举值需要 contract bump（PATCH 版本即可）。

---

## 3. ID 命名规范

| 对象类型 | 命名空间 | 权威方 | 示例 |
|---------|---------|--------|------|
| equipment_class | `brick:` 或 `ext:` | sw_base_model | `brick:Centrifugal_Chiller`, `ext:Air_Compressor` |
| point_class | `brick:` 或 `ext:` | sw_base_model | `brick:Chilled_Water_Supply_Temperature_Sensor` |
| relation_type | `brick:` 或 `ext:` | sw_base_model | `brick:feeds`, `ext:interlocksWith` |
| location_class | `brick:` 或 `ext:` | sw_base_model | `brick:Server_Room`, `ext:Data_Hall` |
| KO ID | `<ko_type>:<unique_slug>` | KnowFabric | `fc:york_yk_chiller_F101`, `ps:ahu_supply_air_temp_setpoint` |
| ontology_version | semver + 标准戳 | sw_base_model | `1.3.0+brick1.3` |

**约束**：

- KnowFabric 不得自行创造 `brick:` 或 `ext:` 前缀的 ID。所有结构 ID 来自 sw_base_model 的 `ontology.yaml`。
- sw_base_model 不得定义 KO 类型或 KO 实例。引用 KnowFabric KO 仅通过 KO ID 字符串。
- KO ID 内部 slug 由 KnowFabric 决定唯一性策略，但前缀必须是契约 §2.2 列出的 KO 类型之一。

---

## 4. 数据流契约

### 4.1 sw_base_model → KnowFabric（KnowFabric 只读消费）

KnowFabric 在编译 KO 时必须：

1. 从 sw_base_model 拉取 `ontology.yaml`（拉取方式：HTTP API 或定期同步脚本，由 sw_base_model 暴露端点）
2. 校验 KO 引用的 `equipment_class_id` 在当前 ontology_version 下存在
3. 在每个生成的 KO 上戳 `curated_against_ontology_version`

KnowFabric 不得：

- 在本地缓存 ontology 定义超过外键所需的字段
- 修改任何 `brick:` / `ext:` ID 的语义
- 引入新的 `brick:` / `ext:` ID 而不通过 sw_base_model PR

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
| `redistribution_restricted` | bool | 当任一支撑源 `is_redistributable=false` 时为 true |

新增 query 参数（v0.2 起支持）：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `min_authority_level` | string | `unspecified`（即包含全部）| 仅返回此等级及以上的 KO |
| `consensus_filter` | string | `all` | 过滤 consensus_state（如 `agreed_only` 排除冲突）|
| `include_restricted_evidence` | bool | `false` | 受信任内部消费方传 `true` 可获取 verbatim 全文（见 §11.5）；外部 surface 必须保持 `false` |

sw_base_model 不得：

- 在本地复刻 KO 类型定义
- 修改 KnowFabric 返回的 KO 内容（只读消费，本地可缓存但不可改写）
- **绕过 authority_layers 直接判定知识权威**——必须通过 KnowFabric 暴露字段
- 绕过 ontology_version 校验
- 在外部 surface（chat、UI、报表）泄露 `redistribution_restricted=true` 的 verbatim evidence_text

### 4.3 反馈通道（sw_base_model → KnowFabric）

sw_base_model 必须把以下事件回流到 KnowFabric：

| 事件 | 触发源 | KnowFabric 端点 | 用途 |
|------|--------|----------------|------|
| KO 命中确认 | SP2 评估生成的 finding 经工程师确认有效 | `POST /api/v2/feedback/ko-confirmation` | trust 分提升 |
| KO 反驳 | finding 被工程师标记误报 | `POST /api/v2/feedback/ko-rejection` | trust 分降级 / 进入冲突队列 |
| 缺口信号 | SP2 查询返回 empty / 低置信，但工单确认确有该模式 | `POST /api/v2/feedback/coverage-gap` | Coverage Gap check 加权 |
| 冲突信号 | 现场数据与 KO parameter_spec 范围不一致 | `POST /api/v2/feedback/conflict-evidence` | Conflict Detection 输入 |

KnowFabric 必须暴露上述端点，并保证：

- 幂等性（同一事件重复提交不重复更新 trust）
- 写入日志保留 sw_base_model 触发源（project_id + finding_id + reviewer_id）
- 反馈不直接修改 KO 内容，只产生 review_pack 候选项

---

## 5. ontology_version 同步协议

- sw_base_model 维护 `ontology.yaml` 的 semver 版本号
- 版本规则：
  - **MAJOR**：不向后兼容（删除类、改 ID 含义）
  - **MINOR**：新增类 / 扩展 typical_points / 扩展 typical_relations
  - **PATCH**：文档修订、不影响 KnowFabric 引用的修复
- KnowFabric 每个 KO 必须戳 `curated_against_ontology_version`
- sw_base_model bump MAJOR 时，KnowFabric 必须运行 re-validation pass，不通过的 KO 进入 review 队列
- KnowFabric Coverage Gap check 必须包含一项：`curated_against_ontology_version` 落后超过 N 个 MINOR（默认 N=3）的 KO
- ontology_version 的发布在 sw_base_model 仓库通过 git tag + CHANGELOG 完成；KnowFabric 通过订阅或定期拉取识别版本变更

---

## 6. MCP 工具注册协议

sw_base_model 的 Agent Control Plane（DESIGN-09）必须把 KnowFabric MCP 工具注册到自己的 tool catalog：

```yaml
# 注册到 sw_base_model agent control plane 的 tool catalog 示例
- tool_id: knowfabric.get_fault_knowledge
  source: knowfabric_mcp_server
  endpoint: <knowfabric_mcp_endpoint>
  scope: read_only
  authentication: <见 §10 待决项 O1>
  expected_response_schema: SemanticApiEnvelope
    # 参见 KnowFabric packages/core/semantic_contract_v2.py
```

**调用约定**：

- agent 调 KnowFabric 工具时，sw_base_model trace 必须记录工具名 + 参数 + 响应摘要
- agent 不直接绕过 sw_base_model control plane 调 KnowFabric（统一走 control plane）
- KnowFabric MCP 工具响应必须保持 idempotent + read-only
- 工具响应中的 KO ID 字符串可以被 agent 引用、聚合、对外展示，但 agent 不得修改

**初始注册的 KnowFabric MCP 工具集**（见 KnowFabric `apps/mcp/main.py`）：

- `knowfabric.get_equipment_class_explanation`
- `knowfabric.get_fault_knowledge`
- `knowfabric.get_parameter_profile`
- `knowfabric.get_maintenance_guidance`
- `knowfabric.get_application_guidance`
- `knowfabric.get_operational_guidance`

---

## 7. CI 强制纪律

### 7.1 KnowFabric 仓库

- `scripts/check-forbidden-deps`：禁止 import 任何 `sw_base_model` 路径
- 新增 `scripts/check-contract-mirror`：校验本契约文件 §1-11 节的 SHA 与 sw_base_model 端镜像一致
- `scripts/check-all` 串入新增检查

### 7.2 sw_base_model 仓库

- 新增 `scripts/check-knowfabric-boundary`：禁止 import 或重定义 KnowFabric KO 类型（fault_code / parameter_spec 等的 schema）
- 新增 `scripts/check-contract-mirror`：同上
- 任何 ontology.yaml 修改必须 bump ontology_version

### 7.3 双仓库联合

- 任一仓库修改契约文件 §1-11 节，必须配对 PR；双方 CI 必须看到对端 PR 的 SHA 才能通过
- 修改 ontology.yaml 必须 bump ontology_version 并发布 git tag
- 契约 CHANGELOG 双向同步

---

## 8. 一次性迁移地图（30 天内执行）

| 当前位置 | 资产 | 目标位置 | 操作 |
|---------|------|---------|------|
| KnowFabric `OntologyClassV2` 表 | equipment_class 定义 | sw_base_model `ontology.yaml` | 导出 + 转译 + 删除 KnowFabric 表 |
| KnowFabric `OntologyAliasV2` 表 | 领域别名 | KnowFabric（保持） | 不变 |
| KnowFabric `OntologyMappingV2` 表 | 外部标准映射 | 拆分：结构映射 → sw_base_model；OEM 命名变体 → KnowFabric | 按 mapping_type 字段拆分 |
| KnowFabric `ChunkOntologyAnchorV2` 表 | 锚点引用 | KnowFabric（保持） | 字段从内嵌定义改为纯 FK 字符串 |
| KnowFabric `KnowledgeObjectV2` 表 | KO 内容 | KnowFabric（保持） | 增加 `curated_against_ontology_version` 字段 |
| KnowFabric `KnowledgeObjectEvidenceV2` 表 | 证据链 | KnowFabric（保持） | 不变 |

迁移过程的具体任务见各仓库的实施计划：

- KnowFabric: `docs/25_knowfabric-side-contract-implementation-plan.md`
- sw_base_model: `docs/plans/2026-04-27-knowfabric-contract-implementation-plan.md`

---

## 9. KnowFabric 身份重定位

随着此契约生效，KnowFabric 的对外定位从"embeddable knowledge engineering engine"降级为"sw_base_model 的领域知识引擎"。

此契约要求 KnowFabric：

- 重写 `README.md` 主页面：清楚说明它服务于 sw_base_model
- 重写 `docs/00_repo-charter.md`：删除"NOT an end-user application"等外部产品语言、删除"三类消费者（AI Agents / Developers / Upstream Applications）"框架
- `run_live_demo_evaluation.py` 等外部评估脚本：保留代码但降级为可选演示工具，不再是主交付物
- `docs/22_external-evaluation-guide.md`：标注为"历史外部评估流程，当前不主推"

**保留**：

- 六层证据链
- chunks-as-truth-source 原则
- 模块边界纪律 + CI 强制
- Compile / Check / Publish vNext 方向（doc 23）

---

## 10. 待解决的开放问题

| # | 问题 | 决策方 | 截止 / 状态 |
|---|------|--------|-----------|
| O1 | KnowFabric API/MCP 调用的鉴权方案（API Key / mTLS / JWT）| 操盘手 | 30 天 |
| O2 | ontology_version bump 的发布节奏（按需 / 月度）| sw_base_model 团队 | 30 天 |
| O3 | KnowFabric KO 是否保留对外发布通道 | 操盘手 | **CLOSED v0.2 (2026-05-01)**：内部基础设施定位已在 charter 改写落实（§9）；外部产品化推迟到 sw_base_model 自身产品化稳定后再考虑 |
| O4 | sw_base_model 接收 KnowFabric OntologyClassV2 seed 时是否完全采纳 | 联合评估 | **CLOSED v0.2 (2026-05-01)**：已通过 v0.1.0 + v0.2.0 ontology bump 流程吸收 KnowFabric seed + 手抄 DESIGN-01 §2.5 补完点类/关系类 |
| O5 | KnowFabric MCP 工具被 agent 调用时是否需要 audit log 双写到 sw_base_model | 平台工程 | 30 天 |
| O6 | 现场观察样本量阈值 N（覆盖 industry_standard 所需最小样本数）默认值 | 操盘手 | 30 天（建议起步 N=5）|
| O7 | 标准文档全文是否在 KnowFabric 存 | 操盘手 | **CLOSED v0.2 (2026-05-01)**：全文 verbatim 入库；版权通过 `is_redistributable` + `include_restricted_evidence` 字段控制（见 §11.5）|
| O8 | `min_authority_level` query 默认值（无显式参数时是否返回 unspecified 类）| 操盘手 | 与 v0.2 上线同期（v0.2 暂定默认 `unspecified`）|
| O9 | 历史 KO 的 authority_summary 是否需要重审（已入库 23 条 parameter_spec 自动 backfill 为 single_source/oem_manual 是否可接受）| 操盘手 | v0.2 上线前（v0.2 暂定可接受）|
| O10 | sw_base_model 在 SP2 评估生成 finding 时，是否在 finding 上附 `consumed_authority_layers` 元数据用于审计 | 联合评估 | v0.2 上线后 60 天 |
| O11 | sw_base_model agent 调用 KnowFabric 时是否被授权传 `include_restricted_evidence: true`，及审计要求 | 联合评估 | 与 v0.2 上线同期（v0.2 暂定：内部受信调用必传必审计）|

---

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

1. **现场观察 + 充分样本**（≥ O6 阈值项目实测）覆盖 OEM 手册和行业标准——这是操作员场景独有信号
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

---

## CHANGELOG

- **v0.2** (2026-05-01)：
  - 新增权威分层枚举（§11.1）+ §11 权威分层与冲突仲裁规则
  - §4.2 数据流响应字段新增 `consensus_state` / `highest_authority_level` / `authority_layers` / `conflict_summary` / `redistribution_restricted`
  - §4.2 新增 query 参数 `min_authority_level` / `consensus_filter` / `include_restricted_evidence`
  - §2.4 明确 KnowFabric 维护权威分层模型
  - §10 关闭 O3 / O4 / O7，新增 O6 / O8-O11
  - 现场观察反向覆盖标准的 `deviation_justification_json` 字段引入（§11.4）
  - 标准文档 clause-based 分块协议 + 全文 verbatim 入库 + `is_redistributable` 版权保护机制（§11.5）
  - 强制纪律范围 §1-10 → §1-11
- **v0.1** (2026-04-27)：初版契约。归属边界确立，OntologyClassV2 迁移计划制定，MCP 工具注册协议草案，反馈通道接口定义。
