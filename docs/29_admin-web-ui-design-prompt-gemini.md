# KnowFabric Admin Web UI 重设计 — Gemini 提示词

> **使用说明**：把 [`docs/29_admin-web-ui-design-brief.md`](29_admin-web-ui-design-brief.md) 作为附件上传给 Gemini，然后把下面 PROMPT 部分整段复制进对话框。
>
> **推荐工具**：[Google AI Studio](https://aistudio.google.com)（免费 + 支持 1M+ context + 支持 Canvas 渲染 HTML 原型 + 支持文件上传）。
> **推荐模型**：Gemini 2.5 Pro（设计任务下 Pro > Flash；如果有 Gemini 3 优先用）。
> **必开**：右上角 "Run settings" → 把 **Temperature** 调到 0.3-0.5（不要默认 1.0，会过于发散）；**System instructions** 留空（PROMPT 已含）。

---

## 操作步骤

1. 打开 https://aistudio.google.com，新建对话（"Create new prompt"）。
2. 模型选 **Gemini 2.5 Pro**（侧栏 model selector）。
3. 把 Temperature 调到 **0.4**。
4. 点 "+" 上传文件，选 `docs/29_admin-web-ui-design-brief.md`。
5. 把下面 PROMPT 整段复制进对话框，发送。
6. Gemini 第一阶段会输出**设计系统规范**。仔细审，不满意说"adjust X 然后重新输出第一阶段"。
7. 满意后说 **"continue, output stage 2 page 1 only"**（Gemini 比 Claude 更容易一口气堆很多页，每张明确 page N only 才会乖乖一张张来）。
8. 6 张页面一张张审 + correct + continue。
9. 第三阶段：`continue, output stage 3`。
10. 把所有 Canvas / 代码块下载或复制到 `apps/admin-web/design/v0.2/`：

```
apps/admin-web/design/v0.2/
├── design-system.md
├── ko-review-center.html
├── conflict-resolution.html
├── document-ingest.html
├── document-library.html
├── authority-classification.html
├── standard-doc-navigator.html
├── ia-and-navigation.md
└── interaction-details.md
```

---

## PROMPT（直接复制以下内容，全部）

```
你是一位资深 SaaS 产品设计师，专精工业领域 dashboard 和高密度信息工作台
设计。视觉参考是 Datadog / Grafana / Linear 这种密度水平，要避免 Notion /
Airtable 那种空荡的消费级风格。

我已经把附件 docs/29_admin-web-ui-design-brief.md 上传给你。

【非常重要的纪律，违反任何一条都视为失败】

R1. 严格按"分阶段"模式执行：第一阶段 → 等我说 continue → 第二阶段每张页
    面单独输出 → 等我说 continue → 第三阶段。
R2. 永远不要一次性输出多张页面。第二阶段的 6 张 HTML 必须每张一个独立代
    码块、每张一次输出，等我说 "continue, output stage 2 page N" 才输
    出下一张。
R3. 每段输出之后明确说 "等待 continue 指令" 并停下。不要替我决定下一步。
R4. 输出代码必须是完整的、可直接渲染的 HTML 代码块（用 ```html ... ```
    包裹）；TailwindCSS 用 CDN 链接（https://cdn.tailwindcss.com），不依
    赖任何 npm 包，浏览器直接打开就能看。
R5. 真实样本数据要用，不要 lorem ipsum。简报 §6 提供了真实数据，你必须
    使用。
R6. 简报 §4 的 6 条 UX 原则不能违反。如果某个设计违反，必须显式标注 +
    解释为什么这是更好的取舍。
R7. 如果你发现简报里有关键信息缺失（数据模型、任务定义、技术约束），先
    停下来列出问题让我回答，再开始工作。不要靠猜补全。

【先读完简报全部内容，特别是 §1-§8。然后按以下三阶段交付】

== 第一阶段：设计系统规范 ==

输出一份 markdown 格式的设计系统文档，包含：

1. 色彩系统
   - 中性主色（背景、边框、文字 3 级）—— 给具体 HEX
   - 8 种 authority_level 的视觉编码（每个 enum 给一个 HEX 色 + 一个图
     标符号 / Unicode 或 Lucide icon name）
   - 4 种 consensus_state 的视觉编码（agreed / single_source /
     partial_conflict / material_conflict —— 后两者必须有警示色）
   - 4 种 trust_level 的视觉编码（L1 / L2 / L3 / L4）
   - 操作色（confirm 主色 / cancel 中性 / danger 警示）

2. 排版
   - 字体栈（含中文优先字体，例如 PingFang SC / Noto Sans SC fallback）
   - 标题、正文、表格、code 4 个层级的字号 + 行高 + 字重

3. 间距系统
   - 4 / 8 / 16 / 24 / 32 px 的语义化用法
   - 列表行高、卡片内边距、面板边距固定值

4. 组件清单
   - 列出本次设计需要的全部组件（authority_badge / consensus_indicator
     / conflict_warning / authority_layer_card / clause_tree_node 等）
   - 每个组件描述用途 + 关键状态 + 是否复用现有 admin-web 组件
     （Panel / DataTable / Tabs / StatusBadge）
   - 标注新增 vs 扩展自现有

输出后**停下**，明确说"等待 continue, output stage 2 page 1 指令"。

== 第二阶段：6 张页面 HTML+Tailwind 原型，每张一个独立 artifact ==

按以下顺序，**每次只输出一张**：

页面 1: KO Review Center（最高优先级；改造现有 page）
页面 2: Conflict Resolution（必须含 material_conflict 真实样本）
页面 3: Document Ingest（含 LLM 建议字段 + 置信度展示）
页面 4: Document Library（grid + filter panel + 批量操作）
页面 5: Authority Classification Review（队列 + 详情双栏）
页面 6: Standard Document Navigator（clause 树 + 全文展示 +
        redistribution restricted 状态展示）

每张页面必须满足：

- 完整可渲染的 HTML 文档（包含 <!DOCTYPE>、<head>、<body>，TailwindCSS
  CDN 引入）
- 用简报 §6 的真实样本数据（不要 lorem ipsum）
- 中文 UI 文案为主，关键技术字段保留英文（brick_class / trust_level /
  consensus_state 等）
- 至少一个 hover state 和一个 active / selected state 在 HTML 里可见
  （用注释 `<!-- hover state -->` 标出）
- 包含 conflict_state 显著的视觉案例（Page 1 KO Review Center 必须展
  示一条 material_conflict）
- 顶部 HTML 注释里写 3-5 行设计要点

每输出一张页面，**停下**，明确说"等待 continue, output stage 2 page N
指令"。N 是下一张的编号。

== 第三阶段：信息架构 + 关键交互 ==

第三阶段一次性输出两份 markdown artifact：

(A) 信息架构图：
- 顶级导航菜单到 6 张页面 + 子页 + tab 的层级关系
- 用 ASCII tree 或 Mermaid 表达
- 标注每条跳转路径

(B) 关键交互细节：
- 6 张页面，每张一段
- 每段描述最关键的 3-5 个交互（怎么点、怎么搜、怎么跳）
- 重点说明跨页面的导航路径，例如"从冲突仲裁页保存后跳回 KO Review
  Center 并 highlight 刚处理的 KO"

== 设计纪律快速校验 ==

每张页面输出时，自检以下 5 条，违反必须显式标注：

C1. 列表页一屏 ≥ 20 行（数据密度优先）
C2. 不滥用 modal —— 优先 inline edit / drawer
C3. LLM 辅助永远要有 confirm/correct 入口，不允许"AI 自动决定 + 人事后
    发现"
C4. material_conflict KO 在任何列表都有醒目警示色 + 图标，不可隐藏
C5. 工业专业感（Datadog / Grafana / Linear 风格），不是消费级 SaaS 风
    格（Notion / Airtable）

==

开始吧。**先做第一阶段，做完停下，等我说 continue**。
```

---

## Gemini 跑这套时常见的偏差 + 应对

| 偏差 | 症状 | 应对 |
|------|------|------|
| 超前输出 | 不等 continue 就一口气把 6 张页面全输出 | 立即说 "stop. you violated R1/R2. roll back to page 1 only and wait." |
| HTML 不完整 | 只输出局部片段、缺 `<!DOCTYPE>` 或 head | 说 "complete HTML document required. rewrite page N as full standalone document." |
| 用 lorem ipsum | 占位文本不用真实数据 | 说 "use real sample data from brief §6, not lorem ipsum. rewrite." |
| 设计违反 UX 原则但没标注 | 默默出了违反原则的设计没解释 | 说 "you violated UX principle X without disclosure. either fix or annotate why this is the better tradeoff." |
| 中文文案过软 | 用了 "您是否要..." "请问..." 这种客气词 | 说 "tighten the copy. industrial pro users want concise commands, not polite phrasing." |

## Claude / Gemini 设计能力的实际差异

兄弟你能感知到的：

- **Claude** 输出 HTML/Tailwind 的"完成度"高一档（自包含、CSS 一致性、视觉细节），但额度贵
- **Gemini 2.5 Pro** 完成度差一点点但 80% 够用，免费额度大；它的"复杂表格 / 树状结构"略生硬，但**信息密度高的工业 dashboard 反而是它的舒适区**——它不会过度装饰
- 同一份简报喂两边可能产出风格不同——这反而是好事，你可以把两个的输出做横向对比，挑组件级最好的拼成最终设计
