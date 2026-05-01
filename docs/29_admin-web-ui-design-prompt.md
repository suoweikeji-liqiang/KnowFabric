# KnowFabric Admin Web UI 重设计 — Claude 提示词

> **使用说明**：把 [`docs/29_admin-web-ui-design-brief.md`](29_admin-web-ui-design-brief.md) 作为附件上传给 Claude，然后把下面 PROMPT 部分整段复制进 Claude 对话框。
>
> 推荐使用支持 artifacts 的 Claude（claude.ai 网页版，或 Claude in Cursor / Claude Desktop with code mode），这样 HTML 原型可以直接渲染查看。

---

## PROMPT（直接复制以下内容）

```
你是一个专业的 SaaS 产品设计师，专精工业领域 dashboard 和高密度信息工作台
设计（参考 Datadog / Grafana / Linear 的密度水平，避免 Notion / Airtable 的
空荡感）。

我已经把附件 docs/29_admin-web-ui-design-brief.md 上传给你。请先完整读完简
报、特别是 §1-§8 全部内容，然后按以下步骤交付：

## 第一阶段（先做这个，做完停下来等我反馈）

输出一份**设计系统规范** artifact（markdown 格式），包含：

1. **色彩系统**
   - 中性主色（背景、边框、文字 3 级）
   - 8 种 authority_level 的视觉编码（每个 enum 一个色 + 一个图标 / 形状）
   - 4 种 consensus_state 的视觉编码（agreed / single_source / partial_conflict
     / material_conflict — 后两者必须有警示色）
   - 4 种 trust_level 的视觉编码（L1-L4）
   - 操作色（confirm 主色 / cancel 中性 / danger 警示）

2. **排版规则**
   - 字体栈（含中文优先字体）
   - 标题、正文、表格、code 4 个层级的字号 + 行高 + 字重

3. **间距系统**
   - 4px / 8px / 16px / 24px / 32px 的语义化用法
   - 列表行高、卡片内边距、面板边距的固定值

4. **组件清单**
   - 列出本次设计需要的全部组件（authority_badge / consensus_indicator /
     conflict_warning / authority_layer_card / clause_tree_node 等）
   - 每个组件描述用途 + 关键状态 + 是否复用现有 admin-web 组件
   - 标注哪些是新增、哪些扩展自现有 Panel / DataTable / Tabs / StatusBadge

输出后停下来。等我说"continue"再进入第二阶段。

## 第二阶段（我说 continue 后开始）

逐张页面输出 **HTML + TailwindCSS 高保真原型** artifact，每张页面一个独立
artifact（这样我能在浏览器里逐张看），按以下顺序：

1. KO Review Center（改造现有 page，最高优先级因为它是日常使用最频繁的）
2. Conflict Resolution sub-page（带 material_conflict 真实示例数据）
3. Document Ingest（带 LLM 建议字段 + 置信度展示）
4. Document Library（grid + filter panel + 批量操作）
5. Authority Classification Review（队列 + 详情双栏）
6. Standard Document Navigator（clause 树 + 全文展示，包含 redistribution
   restricted 状态展示）

每张页面 artifact 的要求：

- 使用简报 §6 的真实样本数据（不要 lorem ipsum）
- 中文 UI 文案为主，关键技术字段保留英文（如 brick_class / trust_level）
- 至少一个 hover state 和一个 active / selected state 可见
- 包含 conflict_state 显著的视觉案例（KO Review 那张必须展示一条
  material_conflict）
- TailwindCSS 用 CDN，不依赖任何外部 npm
- 每张页面顶部加一个简短注释，说明设计要点

每输出 1-2 张页面，停下来等我反馈"good"或"adjust X"，再继续下一张。**不
要一次性堆 6 张**。

## 第三阶段（6 张页面都过了之后）

输出最后两份 artifact：

1. **信息架构图**（markdown + ascii diagram 即可）：从顶级导航菜单到 6 张
   页面 + 子页 + tab 的层级关系。
2. **关键交互细节**（markdown）：6 张页面每张一段，描述最关键的 3-5 个交
   互（怎么点、怎么搜、怎么跳）。重点说明跨页面的导航路径，例如"从冲突
   仲裁页保存后跳回 KO Review Center 并 highlight 刚处理的 KO"。

## 设计纪律（必读，违反任何一条都要标注理由）

- 简报 §4 的 6 条 UX 原则不能违反。如果某个设计违反，必须显式标注 +
  解释为什么这是更好的取舍。
- 高密度优先：列表页一屏 ≥ 20 行；不滥用 modal；优先 inline edit + drawer。
- 工业专业感优先：避免大量留白、卡通插图、淡彩配色、消费级 CTA 风格。
- LLM 辅助永远要给人留 confirm/correct 入口；不允许"AI 自动决定+人工事后
  发现"的姿势。
- 冲突永远显眼，不能藏。

## 最后一条

如果你在阅读简报时发现任何关键信息缺失（数据模型字段、页面任务定义、技术
约束），先列出问题让我回答，再开始第一阶段。不要靠猜补全。

开始吧。第一阶段做完停下。
```

---

## 操作步骤

1. **打开 Claude 网页版** (claude.ai) 或 Claude in Cursor / Claude Desktop。
2. **新建对话**，附件上传 `docs/29_admin-web-ui-design-brief.md`。
3. 把上面 PROMPT 整段（从 `你是一个专业的 SaaS 产品设计师` 到 `第一阶段做完停下`）复制进对话框，发送。
4. 等 Claude 输出第一阶段的设计系统规范 artifact。**先认真审一遍**，不满意的地方告诉它"adjust X"——这是后续 6 张页面的视觉根基，根基歪了页面全错。
5. 满意后说 "continue"，进入第二阶段。一张张审，每张满意了再让它做下一张。
6. 第三阶段的 IA + 交互文档过了之后，就把所有 artifact 收下来。

## 收到设计后下一步

把 Claude 输出的 artifact 整理到 `apps/admin-web/design/v0.2/` 下：

```
apps/admin-web/design/v0.2/
├── design-system.md            # 第一阶段产出
├── ko-review-center.html       # 第二阶段第 1 张
├── conflict-resolution.html
├── document-ingest.html
├── document-library.html
├── authority-classification.html
├── standard-doc-navigator.html
├── ia-and-navigation.md        # 第三阶段
└── interaction-details.md
```

操作员审一遍后，就可以再起一个 Codex prompt 让它把 HTML 原型转成真正的 React 组件并集成到现有 admin-web。**那是下一个 vertical**，不是这一波。

---

## 给 Claude 哪些可以变化

简报里"非妥协项"（§4 的 6 条 UX 原则、§5 的技术栈）不能变；其他设计选择（具体配色、字体、间距、组件取舍）由 Claude 提议、你审。这是设计协作模式，不是规格强加。
