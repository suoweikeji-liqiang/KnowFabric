# KnowFabric Admin Web 设计系统规范 (v1.0)

> **设计原则**：高信息密度、视觉降噪、权威层级绝对清晰、冲突零容忍隐藏。

## 1. 色彩系统 (Color System)

采用低饱和度的冷灰（Slate）作为中性主色，以确保长时间使用的视觉舒适度。高饱和度色彩仅用于状态指示和冲突警告。

### 1.1 中性主色 (Neutral Palette)
*   **背景 (Background)**
    *   `bg-slate-50` (#f8fafc) - 页面全局底层背景
    *   `bg-white` (#ffffff) - 面板、卡片、表格背景
    *   `bg-slate-100` (#f1f5f9) - 表头背景、Hover 状态背景、只读字段背景
*   **边框 (Border)**
    *   `border-slate-200` (#e2e8f0) - 常规分割线、表格网格线
    *   `border-slate-300` (#cbd5e1) - 强分割线、输入框边框
    *   `border-slate-800` (#1e293b) - 选中状态或高对比度边框（Linear 风格）
*   **文字 (Text)**
    *   `text-slate-900` (#0f172a) - 一级文本（标题、核心数据）
    *   `text-slate-600` (#475569) - 二级文本（正文、表头、次要属性）
    *   `text-slate-400` (#94a3b8) - 三级文本（占位符、禁用状态、辅助说明）

### 1.2 权威等级视觉编码 (Authority Level Codes)
*核心原则：看颜色和图标就能识别信息来源的可靠度。*

| 等级 (Level) | 颜色 (Tailwind) | 视觉样式 (Badge Style) | 图标建议 (Icon) |
| :--- | :--- | :--- | :--- |
| `industry_standard` | **Blue** (`blue-600`) | 蓝字 + 浅蓝底 + 实线边框 | 🛡️ 盾牌 (Shield) |
| `regulatory_code` | **Purple** (`purple-600`) | 紫字 + 浅紫底 + 实线边框 | ⚖️ 天平 (Scale) |
| `oem_manual` | **Slate** (`slate-700`) | 深灰字 + 浅灰底 + 实线边框 | 🏭 工厂/厂商 Logo |
| `vendor_application_note`| **Gray** (`gray-500`) | 中灰字 + 透明底 + 实线边框 | 📄 文档 (Document) |
| `internal_sop` | **Teal** (`teal-600`) | 墨绿字 + 浅绿底 + 实线边框 | 📋 剪贴板 (Clipboard) |
| `field_observation` | **Orange** (`orange-600`) | **橙底白字 (高亮反白)** | 🎯 准星/眼睛 (Target) |
| `academic_reference` | **Sky** (`sky-500`) | 天蓝字 + 透明底 + 实线边框 | 📚 书本 (Book) |
| `unspecified` | **Slate** (`slate-400`) | 浅灰字 + 透明底 + **虚线边框** | ❓ 问号 (Question) |

*(注：`field_observation` 作为操作员独家信号，采用唯一的反白高亮设计，在列表中极具跳跃感。)*

### 1.3 共识状态视觉编码 (Consensus State Codes)
*   `single_source` (单一来源): `text-slate-500` + 灰色单点图标
*   `agreed` (多源一致): `text-emerald-600` + 绿色双勾图标
*   `partial_conflict` (部分冲突): `text-amber-600` + 黄色警告图标 (⚠️) - 需注意
*   `material_conflict` (实质冲突): `bg-rose-50 border-rose-500 text-rose-700` + 红色闪烁/粗体警告图标 (🚨) - **强视觉阻断，强制处理**

### 1.4 信任等级视觉编码 (Trust Level Codes)
采用类似手机信号格的视觉隐喻（4格）：
*   `L4`: 📶 四格全满 (`text-indigo-600`)
*   `L3`: 📶 三格满一格空 (`text-indigo-500`)
*   `L2`: 📶 两格满两格空 (`text-indigo-400`)
*   `L1`: 📶 一格满三格空 (`text-indigo-300`)

### 1.5 操作色 (Action Colors)
*   **Confirm / Primary**: `bg-indigo-600 hover:bg-indigo-700 text-white` (主操作)
*   **Cancel / Neutral**: `bg-white border-slate-300 text-slate-700 hover:bg-slate-50` (次操作)
*   **Danger / Reject**: `bg-rose-600 hover:bg-rose-700 text-white` (拒绝/删除)

---

## 2. 排版规则 (Typography)

采用高密度排版，基准字号比常规 SaaS 小 1px，以在单屏容纳更多数据。

*   **字体栈 (Font Stack)**: 
    *   Sans: `Inter, -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif`
    *   Mono (用于代码、数值、标准号): `JetBrains Mono, "Fira Code", monospace`
*   **层级 (Hierarchy)**:
    *   **H1 (页面标题)**: 18px (text-lg), Font-semibold, Line-height 28px
    *   **H2 (面板/卡片标题)**: 14px (text-sm), Font-semibold, Line-height 20px
    *   **Body (正文/表格内容)**: 13px (text-[13px]), Font-normal, Line-height 20px
    *   **Small (元数据/标签/引文)**: 11px (text-[11px]), Font-medium, Line-height 16px
    *   **Code/Value (数值/参数)**: 12px (text-xs), Font-mono

---

## 3. 间距系统 (Spacing System)

严格遵循 4px 栅格系统，打造紧凑的工业仪表盘感。

*   `2px` / `4px` (xs): 组件内部间距（如：图标与文字之间、标签内部）
*   `8px` (sm): 紧密相关元素间距（如：表单 Label 与 Input 之间、同行按钮之间）
*   `12px` / `16px` (md): 模块内部分割（如：卡片内边距、段落间距）
*   `24px` (lg): 独立面板之间的间距、页面外边距
*   **高密度固定值**:
    *   表格行高 (Table Row Height): `32px` (极度紧凑)
    *   输入框高度 (Input Height): `28px` (小尺寸) 或 `32px` (标准尺寸)

---

## 4. 组件清单 (Component Inventory)

| 组件名称 | 用途描述 | 状态/变体 | 来源 |
| :--- | :--- | :--- | :--- |
| `AuthorityBadge` | 展示文档或 KO 的权威等级 | 8 种等级变体 (见 1.2) | **新增** |
| `ConsensusIndicator` | 展示 KO 的共识状态 | 4 种状态变体 (见 1.3) | **新增** |
| `TrustLevelBar` | 展示 L1-L4 信号强度 | 4 个等级的信号格 | **新增** (扩展自 StatusBadge) |
| `AuthorityLayerCard` | 详情页中展示单条支撑源的迷你卡片 | 包含层级、引文、数值摘要、是否受限 | **新增** |
| `ConflictWarningBox` | 针对 material_conflict 的醒目提示框 | 红色边框、带仲裁按钮入口 | **新增** |
| `LLMSuggestField` | 带有 LLM 建议值、置信度、确认/修改按钮的输入组件 | 待确认、已确认、手动修改状态 | **新增** |
| `ClauseTreeNode` | 标准文档浏览器的左侧树状节点 | 展开/折叠、选中高亮、带 KO 数量角标 | **新增** |
| `SplitPane` | 冲突仲裁页的多源对照容器 | 左右双栏、三栏、拖拽调整列宽 | **新增** (扩展自 Panel) |
| `DataTable` | 全局列表展示 | **需开启高密度模式 (32px行高)**、支持多选、支持行内状态高亮 | *复用现有* |
| `Panel` / `Drawer` | 容器组件 | 优先使用 Drawer 进行详情展示，避免 Modal 遮挡上下文 | *复用现有* |
| `Tabs` | 页面内视图切换 | 紧凑型下划线样式 | *复用现有* |