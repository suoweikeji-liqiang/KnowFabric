# KnowFabric Admin Web UI Design Brief (for Claude)

> **目的**：本文档供 Claude 一次性读完、获得设计 KnowFabric admin web UI 所需的全部上下文。
> **使用方式**：作为附件上传给 Claude，配合本仓库 `docs/29_admin-web-ui-design-prompt.md` 的提示词使用。
> **日期**：2026-05-01
> **设计目标**：重新设计 KnowFabric admin web，使其具备权威分层（authority hierarchy）感知能力，让人工录入与审阅高效易用。

---

## 1. 产品本质（设计师必须知道的两层）

KnowFabric 是一个**工业领域知识权威引擎**，不是聊天机器人，不是文档管理系统。它的工作是：

```
原始工业文档（OEM 手册、ASHRAE 标准、内部 SOP、现场观察日志）
    ↓ 编译
结构化知识对象（fault_code / parameter_spec / diagnostic_step 等 8 类）
    ↓ 权威分层 + 证据链 + 健康检查
对外暴露给上层智能运维平台 sw_base_model
```

**用户**：操作员是工业运维公司的领域专家 + AI 工程师。他们运营数百个真实 HVAC / 变频器项目，现在通过这个 admin web 维护知识库。**不是普通用户，是高密度专业人员**。

**核心矛盾**：每条知识必须可追溯到原始文档的 verbatim 证据 + 必须知道权威等级。当前 admin web 没有"权威"概念，所有源被同等对待。这是要重设计的根本原因。

---

## 2. 权威分层数据模型（设计师必须 grok 的概念）

每个**文档（Document）**有一个 `authority_level`：

| 等级 slug | 含义 | 示例 | UI 标识建议 |
|----------|------|------|------------|
| `industry_standard` | 行业标准 | ASHRAE 90.1, IEC 61800, Brick Schema | 蓝色标签 + 盾牌图标 |
| `regulatory_code` | 监管法规 | 国标 GB-T, 地方建筑规范 | 紫色标签 |
| `oem_manual` | 厂商手册 | Trane CVGF 操作手册, York YK 维修指南 | 灰色标签 + 厂商 logo |
| `vendor_application_note` | 厂商应用文档 | Trane 工程通报 | 浅灰标签 |
| `internal_sop` | 内部规程 | 公司调试 playbook | 绿色标签 |
| `field_observation` | 现场观察 | 项目现场实测 + 工程师确认 | 橙色高亮（操作员独家信号）|
| `academic_reference` | 学术参考 | ASHRAE Handbook, 教科书 | 浅蓝标签 |
| `unspecified` | 未指定 | 历史遗留 | 灰色虚线标签 |

每个**知识对象（Knowledge Object, KO）**有：

- `trust_level`（L1/L2/L3/L4，单源信号强度）
- `consensus_state`（`single_source` / `agreed` / `partial_conflict` / `material_conflict`）
- `highest_authority_level`（所有支撑源中最高的）
- `authority_layers`（**关键字段**：所有支撑源的列表，每个含 level + publisher + citation + value_summary）
- `conflict_summary`（冲突时填）

**冲突示例**：当 ASHRAE 90.1 §6.5.3.2 说 chilled water reset 是 10°F，Trane 手册 p.29 说是 12°F，运维实测确认 10°F 更可靠——这是 `material_conflict`，UI 必须把三个源同屏对照展示，操作员选择仲裁。

---

## 3. 要设计的 6 个页面 / 模块

### 3.1 Document Ingest（文档入库）— 新建

**任务**：操作员上传一份 PDF（手册或标准），系统调 LLM 自动建议权威元数据，操作员 confirm/correct，入库。

**关键交互**：
- 拖拽上传或文件选择
- LLM 建议：authority_level / publisher / standard_id / publication_year / vendor_brand 等
- 每个建议字段旁边显示置信度 + "edit"图标
- 一键"接受全部建议"或逐项修改
- 顶部突出显示 `is_redistributable` 开关（标准类默认 OFF）
- 上传按钮 disabled 直到 authority_level 至少被 confirm

### 3.2 Document Library（文档库）— 新建

**任务**：浏览所有已入库文档，按权威等级分组 / 过滤，批量编辑权威元数据。

**关键交互**：
- 默认 grid view，按 authority_level 分组（卡片形式）
- 每张卡片显示：file_name + 权威标签 + publisher + 关联 KO 数
- 右侧 filter panel：authority_level 多选、publisher 搜索、is_redistributable toggle
- 多选后批量改 authority_level（典型场景：操作员发现某批 OEM 手册类型识别错了）
- 列表 view 切换（更密集，给重度用户）

### 3.3 Authority Classification Review（权威分类审阅）— 新建

**任务**：LLM 自动建议的权威元数据需要人审过。这是一个待审队列。

**关键交互**：
- 队列形式（左侧列表，右侧详情）
- 详情区显示：文档第一页缩略图 + LLM 建议 + 置信度 + LLM 推断理由
- 大按钮："Confirm" / "Correct"
- Correct 模式下展开所有字段供修改 + 必填 reason 注释
- 进度条："4/12 已审"

### 3.4 KO Review Center（知识对象审阅中心）— 改造现有 ReviewCenterPage

**任务**：审阅 LLM 抽取出的 KO 候选（这是当前最常用的页面，要权威感知化）。

**当前状态**：
- 已经有 review pack 列表 + candidate 详情 + accept/reject 决策
- 但**完全不显示 authority context**

**新增**：
- 每条 candidate 卡片显示 `consensus_state` 标签（agreed / single_source / partial_conflict / material_conflict）
- 详情区展开 `authority_layers`：每条源用一张迷你卡片，含 level 标签 + citation + value_summary
- 多源时左右分屏对照（agreed 时静默合并，conflict 时强制分屏）
- 拒绝按钮旁加 "mark as deviation justified"（用于现场观察反向覆盖标准）
- 顶部全局过滤："只看冲突 KO" / "只看 L4" / "只看 industry_standard 支撑的"

### 3.5 Conflict Resolution（冲突仲裁）— Review Center 子页

**任务**：当 KO 是 `material_conflict` 时，专门页面让操作员仲裁。

**关键交互**：
- 大屏 split-pane：左侧源 A 全文 + citation，右侧源 B 全文 + citation（多源时支持 3-way）
- 中间：差异点高亮（数值不同、范围不同、单位不同）
- 操作员选项：
  - "Accept both, surface conflict to consumer"（保留两源，下游决策）
  - "Pick winner: A" / "Pick winner: B"（指定权威方）
  - "Mark deviation justified by field observation"（必填 deviation_justification：偏离的标准引用 + 实测样本量 + 偏离原因）
- 决策必须有 reviewer_id + 理由文字

### 3.6 Standard Document Navigator（标准文档浏览器）— 新建

**任务**：操作员要快速定位 ASHRAE 等标准的某条款，看它关联了哪些 KO。

**关键交互**：
- 左侧：clause 树（§6 → §6.5 → §6.5.3 → §6.5.3.2）
- 右侧：点击条款显示该条款的 verbatim 全文（受 is_redistributable 控制，未授权时只显示 citation + 摘要）
- 底部：该条款支撑的 KO 列表（点击跳到 Review Center）
- 顶部：标准切换器（ASHRAE 90.1-2022 / Guideline 36-2021 / IEC 61800-3 等）

---

## 4. UX 原则（6 条非妥协项）

1. **LLM 辅助 + 人最终拍板**。所有权威字段由 LLM 在 ingest 时建议，人只需确认/修正。**禁止 10 字段空白手填表单**。
2. **批量操作一等公民**。列表页默认多选 + 批量修改。单条编辑是兜底，不是主路径。
3. **Provenance 始终可见**。任何展示 KO 的地方一键能跳到原始文档条款/页。
4. **冲突不可隐藏**。`material_conflict` KO 在任何列表里有醒目标识；不允许静默 approve。
5. **双语标签**。UI 标签中文为主英文为辅；KO 内容按源语言展示，旁边可选自动翻译提示。
6. **只读外宾模式**。view-only 角色给非编辑利益相关方查看（不可改权威元数据）。

---

## 5. 视觉与技术约束

**技术栈**（必须符合）：
- React + TypeScript + Vite
- 已有目录：`apps/admin-web/src/pages/` + `apps/admin-web/src/components/`
- 现有组件可参考：`Panel`, `DataTable`, `MasterDetailPage`, `Tabs`, `StatusBadge`
- 状态管理：`usePersistentPageState` hook 模式
- 数据获取：`useAsyncResource` hook 模式

**视觉方向**：
- **工业专业感**：高密度、低饱和度主色、深色边框、表格密集
- **不要消费级 SaaS 风格**：避免大量留白、卡通插图、淡彩 CTA
- 参考方向：Datadog dashboards、Grafana、Linear（密集但不混乱）
- 反例：Notion、Airtable（消费级、太空旷）

**信息密度**：
- 列表页一屏至少 20 行
- 详情页同时展示 3-4 个数据维度
- 不滥用 modal；优先 inline edit + drawer

**桌面端优先**：移动响应式 v0.2 不做。

---

## 6. 真实样本数据（让 Claude 不用 lorem ipsum）

### 真实 parameter_spec KO 示例

```json
{
  "knowledge_object_id": "ko_c8f98514ec68facf",
  "title": "外部冷冻水设定值",
  "summary": "外部冷冻水设定值，可对冷冻水设定在远程进行修改。建立在 1A16 J2-2 至 J2-6（接地）的输入基础上。",
  "knowledge_object_type": "parameter_spec",
  "trust_level": "L4",
  "consensus_state": "single_source",
  "highest_authority_level": "oem_manual",
  "authority_layers": [
    {
      "level": "oem_manual",
      "publisher": "Trane",
      "standard_id": null,
      "citation": "Trane CVGF 400-1000 操作维护手册 p.45",
      "value_summary": "范围 34-65°F (-36.7~18.3°C), 默认可调",
      "evidence_count": 2,
      "redistribution_restricted": false
    }
  ],
  "structured_payload": {
    "parameter_name": "External Chilled Water Setpoint",
    "value": "可调",
    "unit": "°F",
    "range_min": "34",
    "range_max": "65",
    "description": "外部冷冻水设定值，2-10 VDC 和 4-20 mA 对应于 34 至 65°F (-36.7~18.3°C) 的 CWS 范围。"
  },
  "applicability": {
    "domain_id": "hvac",
    "equipment_class": "brick:Centrifugal_Chiller",
    "vendor_brand": "Trane",
    "model_family": "CVGF"
  },
  "review_status": "approved",
  "evidence": [
    {
      "doc_id": "doc_883beab5e0004a2c",
      "doc_name": "trane_cvgf_400_1000_chiller_manual.pdf",
      "page_no": 45,
      "evidence_text": "外部冷冻水设定 External Chilled Water Setpoint(ECWS) 外部冷冻水设定可对冷冻水的设定在远程进行修改。外部冷冻水设定建立在 1A16 J2-2 至 J2-6(接地) 的输入基础上。"
    }
  ]
}
```

### 真实冲突示例（待你想象设计成 material_conflict）

```json
{
  "knowledge_object_id": "ko_imagined_conflict_example",
  "title": "Chilled Water Reset Maximum",
  "consensus_state": "material_conflict",
  "highest_authority_level": "industry_standard",
  "conflict_summary": "ASHRAE 90.1-2022 规定最大重置 10°F；Trane CVGF 手册写 12°F；运维实测建议 10°F 更稳定。",
  "authority_layers": [
    {
      "level": "industry_standard",
      "publisher": "ASHRAE",
      "standard_id": "ASHRAE 90.1-2022",
      "citation": "ASHRAE 90.1-2022 §6.5.3.2",
      "value_summary": "10°F",
      "redistribution_restricted": true
    },
    {
      "level": "oem_manual",
      "publisher": "Trane",
      "citation": "Trane CVGF 操作手册 p.29",
      "value_summary": "12°F",
      "redistribution_restricted": false
    },
    {
      "level": "field_observation",
      "publisher": "operator's fleet",
      "citation": "23 项目实测 2024Q4-2025Q1",
      "value_summary": "10°F 推荐",
      "redistribution_restricted": false
    }
  ]
}
```

### 真实 Document 列表示例

| file_name | authority_level | publisher | standard_id | redistributable |
|-----------|----------------|-----------|-------------|-----------------|
| trane_cvgf_400_1000_chiller_manual.pdf | oem_manual | Trane | — | ✓ |
| ashrae_901_2022_excerpt_section_6_5.pdf | industry_standard | ASHRAE | ASHRAE 90.1-2022 | ✗ |
| iec_61800_3_2017_emc.pdf | industry_standard | IEC | IEC 61800-3:2017 | ✗ |
| internal_chiller_commissioning_playbook_v3.md | internal_sop | 公司内部 | — | ✓ |
| project_PRJ_2024_087_field_log.json | field_observation | 公司内部 | — | ✓ |

---

## 7. 期望的设计交付

希望 Claude 给出：

1. **设计系统规范**（一份 markdown）：色彩、排版、间距、组件清单、权威等级视觉编码（每个 enum 怎么显示）
2. **6 张页面的 HTML+Tailwind 高保真原型**（每张页面一个 artifact，操作员可以直接在浏览器看）
   - 用真实样本数据（不用 lorem ipsum）
   - 包含至少一种 hover / focus / active 状态
   - Chinese 文案为主，英文标签辅助
   - 包含至少一个 conflict_state 显著的视觉示例
3. **信息架构 + 导航说明**（一份简短 markdown）：从顶级菜单到各页面跳转的关系图
4. **关键交互的细节描述**（每张页面一段）：怎么点、怎么拖、怎么搜、怎么跳

不要做：
- 移动端响应式
- 完整 React 组件实现（设计阶段 HTML 即可）
- 后端 API 调用
- 国际化框架配置
- 多主题切换

---

## 8. 你（Claude）开始前问自己的事

1. 操作员每天用这个界面 4-8 小时——**任何一个 click 多一次都是 bug**
2. 工业领域的"professionalism"是数据密度、不是空荡留白
3. 权威分层是这个产品的核心差异——**视觉编码必须显眼**，看一眼就知道哪条来自标准、哪条来自厂商手册、哪条来自现场实测
4. 冲突不能藏——material_conflict KO 在任何列表都要有警示色 + 醒目图标
5. 中文工业专业领域用户——文案要精准，避免互联网产品的客气措辞（"喔！这里有个新通知" ✗ → "12 条待审" ✓）

设计如果违反任何一条 UX 原则（§4），请明确标注并解释为什么这是更好的取舍。
