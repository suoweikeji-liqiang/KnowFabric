# KnowFabric × sw_base_model 集成契约

> **状态**：v0.1 binding contract / 2026-04-27
>
> **镜像位置**：
> - KnowFabric: `docs/24_knowfabric-sw-base-model-contract.md`
> - sw_base_model: `design/DESIGN-10-KNOWFABRIC-INTEGRATION.md`
>
> **强制纪律**：本文件第 1-10 节内容在两个仓库必须保持一致。任何修改必须通过双仓库配对 PR 同时落地，CI 校验 SHA 一致。

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
| SP1 项目理解 | `typical_points` / `typical_relations`（按 equipment_class） | `GET /api/v2/domains/{domain}/equipment-classes/{class}` |
| SP2 评估引擎 | KO 内容（fault_code / parameter_spec / diagnostic_step 等） | `GET /api/v2/domains/{domain}/equipment-classes/{class}/{ko-type}` |
| SP3 能力工厂 | KO ID 锚定（一条规则适用于哪个 KO） | KO ID 字符串引用 |
| Agent Control Plane (DESIGN-09) | KnowFabric MCP 工具集 | MCP tool catalog 注册 |

sw_base_model 不得：

- 在本地复刻 KnowFabric KO 类型定义
- 修改 KnowFabric 返回的 KO 内容（只读消费，本地可缓存但不可改写）
- 绕过 ontology_version 校验

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
- 新增 `scripts/check-contract-mirror`：校验本契约文件 §1-10 节的 SHA 与 sw_base_model 端镜像一致
- `scripts/check-all` 串入新增检查

### 7.2 sw_base_model 仓库

- 新增 `scripts/check-knowfabric-boundary`：禁止 import 或重定义 KnowFabric KO 类型（fault_code / parameter_spec 等的 schema）
- 新增 `scripts/check-contract-mirror`：同上
- 任何 ontology.yaml 修改必须 bump ontology_version

### 7.3 双仓库联合

- 任一仓库修改契约文件 §1-10 节，必须配对 PR；双方 CI 必须看到对端 PR 的 SHA 才能通过
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

| # | 问题 | 决策方 | 截止 |
|---|------|--------|------|
| O1 | KnowFabric API/MCP 调用的鉴权方案（API Key / mTLS / JWT） | 操盘手 | 30 天 |
| O2 | ontology_version bump 的发布节奏（按需 / 月度） | sw_base_model 团队 | 30 天 |
| O3 | KnowFabric KO 是否保留对外发布通道（vNext 权威发布愿景，独立产品 optionality） | 操盘手 | 60 天 |
| O4 | sw_base_model 接收 KnowFabric OntologyClassV2 seed 时是否完全采纳（是否要做人工审阅） | 联合评估 | 14 天 |
| O5 | KnowFabric MCP 工具被 agent 调用时是否需要 audit log 双写到 sw_base_model（重复 trace） | 平台工程 | 30 天 |

---

## CHANGELOG

- **v0.1** (2026-04-27)：初版契约。归属边界确立，OntologyClassV2 迁移计划制定，MCP 工具注册协议草案，反馈通道接口定义。
