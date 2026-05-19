# 41 M2 Integration Phase Retrospective

- **Phase**: M2 接入 (KnowFabric ↔ sw_base_model integration plumbing)
- **Duration**: 2026-05-01 → 2026-05-19 (18 working days)
- **Outcome**: Production SP2 detector engine shipped, contract v0.2.3 stable, M2 接入 phase declared CLOSED on Day 18
- **Author**: Claude (KnowFabric session) — operator-driven

> 写这份不是为了庆功，是为了下次 M3 不踩同样的坑。

---

## 1 What this phase was supposed to deliver

启动时（5月初）这两条目标都没写在 charter 里，是工作过程中逐步明确的：

- **G1**：sw_base_model 这一侧能用契约 v0.2 协议消费 KnowFabric KO 库（不是 mock、不是 stub，是真 REST 路径）
- **G2**：契约 v0.2 在双仓里 SHA-mirror 稳定 + CI guard 不哑火，能挡未来 drift
- **G3**：P0 评估场景 1 (数据可信度) 至少有 detector engine production code，从 spike phase 升到 production phase

回头看，三个目标全达成，外加意外修了 7-9 项 friction，超出最初想象的"contract + 写个 client"工作量。

## 2 What actually happened — 18 天序列

```
Day 1-3   契约 drift discovery + 收口
   核心动作: KnowFabric Path A 同步 docs/24 + 同步 sw_base_model mirror
   隐藏问题: Codex 改了 sw_base_model working tree 但没 commit → 双仓 SHA drift
   CI 守卫 worktree 模式 silent-skip bug → drift 没被拦住
   解法: sw_base_model session commit + push c0110d6 + check-contract-mirror 改 git rev-parse

Day 3-7   Spike v1 + 8 项原始 friction (F1-F8)
   核心动作: scripts/spike_centrifugal_chiller_param_baseline.py 跑通三态判断
   关键发现: F1 verbatim leak (版权风险), F2 server 自动选边违反 §11.2 协议
   暴露的: 不接触真实 KO consumption 写 protocol 是空中楼阁

Day 7-12  9 项 friction 修复 + 契约演化
   F1 verbatim leak → 替换为 citation-only stub (放弃 truncate 模式)
   F2 fallback range nulling → server 主动 null + range_disclaimer flag
   F4/F7 wire-type + 关系 → 契约 §4.2 补字段
   F5 display_language CJK detection → 立即生效
   F6 unit dup → guard
   F8 chunk dedup → forward-only
   F9 prose range extraction → forward-only
   契约 v0.2.x → v0.2.1 → v0.2.2

Day 12-14 Spike v2 (fault_code) + 6 项新 friction (F10-F15)
   B 路径暴露 fault_code KO 自身特殊性: trust_level 全 L3, 字段稀疏
   F10 default min_trust_level=L4 是 documentation bug (我 REPLY 004 写错了方向)
   F14 /fault-knowledge 是 union endpoint (返回 3 种 KO type)
   F11/F13/F15 deferred 进 M3 backlog

Day 14-15 F10/F14 修 + 契约 v0.2.3
   API default L4 → L1 (5 endpoint 统一)
   契约 §4.2 加 min_trust_level + union endpoint 注

Day 15-18 Production SP2 detector (A 段)
   apps/sp2_assessment/ 1085 行 stdlib-only production code
   ParameterSpecDetector + FaultCodeDetector + KnowFabricClient (含 TTL cache)
   17 单元测试 + 11 demo case + 163k x cache speedup
   F16 (cache invalidation API) 新发现, 低优先级 defer
```

## 3 Outcomes — 量化交付

| 维度 | 数值 |
| --- | --- |
| 契约演化 | 5 个版本 (v0.2 → v0.2.x → v0.2.1 → v0.2.2 → v0.2.3) |
| KnowFabric commits | 13 |
| sw_base_model commits | 5 |
| 跨仓 REPLY 文件 | 17 (14 KNOWFABRIC + 4 SW + 1 handoff) — gitignored 3 份过时 |
| Friction 总数 | 16 (F1-F16) |
| Fixed friction | 10 (F1-F2, F4-F10, F14) |
| Deferred friction | 5 (F11, F13, F15, F16, F3-by-corpus) |
| By-design (no fix) | 1 (F12) |
| Production code | 1085 行 (sw_base_model) + 多 100s 行 (KnowFabric server fixes) |
| Tests added | 30+ (17 detector + 6 F1/F2 contract + 6 F6/F9 merger + 2 F8 merger + 1 F5 detect) |
| Pytest count | 438 → 450 (+12) |
| Live demo verification | 11 case 全过 (cache benchmark + 4 scenario types) |
| Cross-repo conflicts | **0** (整个 phase 0 git conflict) |

## 4 What worked well — keep these patterns

### 4.1 跨仓信箱机制

KNOWFABRIC_REPLY_NNN ↔ SW_REPLY_NNN 文件 + 操作员手动转发模式：

- 文件路径明确，编号清晰，trace 完整
- 选择性 commit (REPLY 008 §二 c 策略) — 决策点保留，过程性 noise 跳过
- 各 session 不需要互相 import context；handoff 文件就是 anchor
- 0 conflict 跑 17 round

**对未来 M3+**：继续这个模式，命名约定不动。如果 session 数从 2 升到 3+，引入命名空间（如 `SW_TO_KF_REPLY_NNN.md`）。

### 4.2 Paired contract update with SHA baseline

契约改动 → 双仓 paired update + SHA 重算 + check-all 双绿 → 双仓 commit + push。

- 5 个版本演化 0 mirror drift
- CI 守卫修过 worktree silent-skip 后真挡得住

**对未来 M3+**：契约任何改动都走 paired update，不要单边推。

### 4.3 Spike → friction → fix → re-spike 循环

- Spike v1 拉真数据撞到 F1-F8
- 修完之后 Spike v1 retest 验证修复在 server 端实际生效
- Spike v2 (fault_code) 重复同样模式撞到 F10-F15

**对未来 M3+**：先 spike 暴露 friction，不要在协议层 over-engineer。

### 4.4 Forward-only fix + deferred retroactive

F8/F9 都是"代码改了，存量数据下次 regroup 时自然清理"。避免每次 fix 都跑全库 retroactive。

**对未来 M3+**：保持这种区分。retroactive 单独排期。

### 4.5 实证胜过文档断言

我多次靠"看实际代码"+"实测 API 返回"+"查 DB 状态" 校正自己（和 sw_base_model session）的判断。

**对未来 M3+**：先 grep / curl / psql 看现实，再写结论。

## 5 What broke / went wrong — fix these patterns

### 5.1 我（KnowFabric session）犯过 3 次事实错误

| Reply | 错 | 影响 |
| --- | --- | --- |
| REPLY 001 / 003 §六 | endpoint 路径写成 `/api/v2/knowledge_objects`（不存在）| sw_base_model session 按错路径会 404，浪费一轮 |
| REPLY 004 §四 | `min_trust_level=L4` 写"默认最低全要"，实际 L4 是最严过滤 | sw_base_model session B 段撞 F10 才暴露 |
| REPLY 006 §一 | 误判 "§11.2 mirror 已同步"，没查 git status | sw_base_model session 已经 grep 找证据反驳我 |

**根因**：我没看实际代码/文件，靠记忆写。

**未来防御**：写 REPLY 前先 grep 实际 endpoint / 跑 curl / 查 git status，不要靠 conversation 记忆下断言。

### 5.2 Codex 的 paired commit "改了没 commit" bug

Day 3 时 Codex 同步 sw_base_model mirror 改了 working tree 但没 commit + push。直到 sw_base_model session B 段时 worktree pull 才暴露。

**根因**：Codex 跨仓改动后没强校验 git status；操作员/我没复核。

**未来防御**：任何跨仓 paired update 后**强制**跑 `git status` 两边 + `bash scripts/check-all` 两边，不通过不发 REPLY。

### 5.3 CI 守卫 worktree silent-skip bug

`check-contract-mirror` 用相对路径 `../sw_base_model/...`，worktree 模式下解析到不存在路径，`[ -f ... ]` false 静默 skip。

**根因**：原作者没考虑 worktree mode 的相对路径解析。

**修法**：sw_base_model session 改用 `git rev-parse --git-common-dir` 算主仓根。KnowFabric 这边 fallback `../../../../` 凑巧 work，没修但也建议 port 同样模式。

**未来防御**：跨仓比对脚本必须用 absolute path resolution + fail loud on missing peer。

### 5.4 我 REPLY 文件命名规则不一致

REPLY 001-005 一开始没编号策略，是边写边加。REPLY 006 之后才规整。

**未来防御**：M3 第一份 REPLY 之前就定好命名 + commit 策略，不要边写边变。

### 5.5 文档与代码 drift 暴露过晚

F10 (min_trust_level default) 是文档与 API 行为的方向相反，spike v1 没撞上是因为 parameter_spec 数据多 L4，等 spike v2 切到 fault_code 才暴露。

**根因**：单一 KO type 的 spike 不够全面，看不到跨类型的契约 quirk。

**未来防御**：契约层补 invariant test（contract conformance test）— 对每个 KO type 跑一次默认 query，至少应该返回 > 0 结果，否则告警。这是 contract-level smoke test。

## 6 Friction 全谱（F1-F16）

| F | 严重度 | 类型 | 处置 | Commit |
| --- | --- | --- | --- | --- |
| F1 | 高 | 契约 §11.5 verbatim leak | ✓ fixed | 845639f |
| F2 | 高 | server 自动选边 (value_disagreement) | ✓ fixed | 2681038 |
| F3 | 中 | authority_level 全 unspecified | by corpus, not blocker | — |
| F4 | 中 | wire-type docs gap | ✓ fixed in a15d742 | — |
| F5 | 中 | display_language 语义 | ✓ fixed | f61253e |
| F6 | 低 | value_summary unit dup | ✓ fixed | 9390590 |
| F7 | 低 | trust_level vs confidence | ✓ fixed in a15d742 | — |
| F8 | 中 | chunk dedup | ✓ fixed (forward-only) | 0f53b41 |
| F9 | 中 | layer-level range from prose | ✓ fixed (forward-only) | 160b78a |
| F10 | 中 | min_trust_level default L4 | ✓ fixed | b1f1d87 |
| F11 | 中 | fault_code field sparseness | deferred (compile pipeline) | — |
| F12 | 低 | range_disclaimer fault_code no-op | by design | — |
| F13 | 中 | OEM synonym aggregate | deferred (server enhancement) | — |
| F14 | 中 | /fault-knowledge union doc | ✓ fixed in b1f1d87 | — |
| F15 | 中 | fault under-merge | deferred (compile pipeline) | — |
| F16 | 低 | cache invalidation API | deferred (M3 event protocol) | — |

## 7 Cross-repo 信箱 process — process 评价

### 7.1 实测可行

17 round 0 conflict，规则简单（操作员手动转发 + REPLY 文件 anchor）。两个 session 互相不知道对方在做什么，但通过文件状态对得上。

### 7.2 弱点

- **依赖操作员人肉转发**：如果操作员忙 / 忘转 / 转错版本，链条断
- **REPLY 文件爆炸**：18 天 17 份 REPLY，加上 4 份 SW_REPLY，21 份文件在仓里。M3 如果 30 天可能 50+ 份
- **gitignore 规则不一致**：001/003/005 gitignored，002/004/006-014 commit；新读 trace 的人不知道 gitignored 那 3 份是错的

### 7.3 改进建议（M3 启动时实施）

- **REPLY 命名加角色标识**：`KF_TO_SW_NNN.md` / `SW_TO_KF_NNN.md`，单向流向显式
- **REPLY 状态字段**：每份 REPLY 开头加 `Status: draft / sent / acked / superseded`，便于扫描
- **commit 策略写进 PROCESS.md 而不是某个 REPLY 内**：现在 REPLY 008 §二的规则是 ad-hoc 的，下次新人不知道去哪里查

## 8 Lessons for M3+

### 8.1 战略

1. **Spike 优先**：M3 任何新 milestone 起步先写一个 spike 撞 friction，不要直接进 production。M2 接入的 sequence (spike v1 → friction → fix → spike v2 → production A) 是对的
2. **契约演化常态化**：18 天 5 个契约版本是正常节奏，不是失败。每次小步推 + paired update 比"一次性大改"风险低
3. **Friction 分级早做**：F1-F16 的 (高/中/低/by-design/deferred) 分级让 fix 路径清晰。M3 启动 friction tracker 应该一开始就有
4. **Forward-only 优先于 retroactive**：retroactive 全库 regroup 是大动作，能 forward-fix 就 forward，retroactive 单独排期

### 8.2 工程

1. **Contract conformance test**：对每个 KO type 跑 default query smoke test，挡 F10 类型方向错文档
2. **Worktree-safe CI scripts**：所有 cross-repo 脚本用 `git rev-parse --git-common-dir`
3. **跨仓 paired commit**: 写入 PROCESS.md，强制双仓 status 校验
4. **TTL cache** 是 production 黄金（实测 163k x），detector 必装

### 8.3 协议

1. **三态消费协议**（FAULT_MATCHED/AMBIGUOUS/NO_FAULT, OK_CONSENSUS/OEM_DISAGREEMENT/ANOMALY）证明可扩展：parameter_spec 三态 + fault_code 三态 + (TBD) diagnostic_step 三态
2. **range_disclaimer / range_arbitration_only** flag pattern 可复用：任何"server 不要自动决策"的场景都用 disclaimer flag 强迫消费方走详细数据
3. **Citation-only stub** 替换 verbatim truncation 是合规底线，不能只 truncate

## 9 Open questions / unresolved

### 9.1 KO 库质量长尾

F11 (fault_code 字段稀疏) / F13 (OEM synonym) / F15 (under-merge) 都是 compile pipeline 质量问题。M2 接入 phase 只是消费侧绕开了这些 quirk，KO 库本身的质量改善是 M3+ 的事。

具体：fault_code KO 库 100 个全 L3、`fault_code` 字段只 15/100 有值、`fault_meaning` 4/100 有值——这是 KnowFabric M1 corpus 的现状，不是 M2 接入留的债。

### 9.2 真 sensor stream 接入未做

SP2 detector engine 是 production code，但输入还是 mock signal。从 mock → 真 sensor 是 M3 主体工作（候选 1，5-10 天）。

### 9.3 Feedback emission 未做

DESIGN-10 §4.3 反馈通道 SDK 在 sw_base_model 端已存在 (`apps/assessment_feedback/`) 但 0 调用方。M3 候选 4。

### 9.4 MCP path 未启用

KnowFabric apps/mcp/ 是 server baseline 但 sw_base_model 未起 MCP client。M3 候选 3。

### 9.5 visual_evidence_anchor 表 0 行

Line 2 visual extraction 留的债，独立于 M2 接入 phase 但影响视觉证据消费。M3 KnowFabric backlog。

## 10 M3 推荐启动顺序（操作员决策点）

按"业务价值 / 前置依赖"双轴：

```
M3 候选 2 (持久 Finding store, 2-3 天) ← 必做，是候选 1 的数据底座
        ↓
M3 候选 1 (真 sensor stream, 5-10 天) ← M3 milestone 主体
        ↓ 并行
M3 候选 4 (Feedback emission, 2-3 天) ← KnowFabric session 干
        ↓ 并行
M3 候选 5 (F11/F13/F15 收尾, 3-5 天) ← KnowFabric session 独立
        ↓ 之后
M3 候选 3 (MCP path, 3-5 天) ← agent 路线看进度
```

### 10.1 M3 启动前操作员可以确认的 4 件事

1. M3 milestone 真正的产品意义是不是"真传感器接进来"？还是"agent 用 MCP 调 KO"？这俩排序决定候选 1 vs 3 谁先
2. F11/F13/F15 修复 (compile pipeline 改造) 跟 M3 候选 1 是平行还是前置？(我倾向平行，KO 库改进对 detector 是自然受益)
3. KnowFabric 这一侧的"23 个 MANUAL_REVIEW backlog" 还要不要清？长期 deferred，但占心智
4. 是否需要把 M2 接入 phase 这 17 份 REPLY 信箱内容 archive 一份 markdown summary，避免下次新 session 要读 21 份文件？

---

**M2 接入 phase declare CLOSED**. Production SP2 detector engine ready. Cross-repo contract v0.2.3 stable. Friction backlog 5 项 deferred 给 M3。

下一次 M3 启动 retrospective 时希望看到的事：F10 类的方向错文档没再出现，跨仓 SHA drift 没再出现，spike → friction → fix 模式延续。
