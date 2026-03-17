# Rebuild Session Kickoff

**Status:** Operator Guide
**Last Updated:** 2026-03-17

This document is the recommended starting point for any new AI-assisted work session on the KnowFabric rebuild track.

---

## Purpose

Use this guide when opening a new session and you want the agent to continue the ontology-first rebuild without drifting back into the legacy Phase 1 assumptions.

The rebuild direction is defined by:

- `docs/adr/0003-promote-knowfabric-to-domain-knowledge-authority.md`
- `docs/09_ontology-authority-architecture.md`
- `docs/10_rebuild-plan.md`

---

## Session Guardrails

Every rebuild session must preserve these rules:

1. Keep the six-layer evidence discipline intact.
2. Do not move project-instance modeling into KnowFabric.
3. Do not treat generic RAG plumbing as the product boundary.
4. Prefer introducing `v2` package structures beside legacy files before deleting legacy structures.
5. Do not start storage migrations until ontology identifiers and package contracts are stable.
6. Run `bash scripts/check-all` before closing the session if files were changed.

---

## Recommended First Five Minutes

Ask the agent to do these things first:

1. Read `CLAUDE.md`.
2. Read `docs/README.md`.
3. Read ADR-0003 and the rebuild architecture/plan docs.
4. Inspect the current `domain_packages/` layout and git status.
5. Restate the next concrete rebuild task before editing.

---

## Suggested Session Prompt

Copy the prompt below into a new session when you want execution, not just brainstorming.

```text
你现在在 /Users/asteroida/work/KnowFabric 仓库中工作，请接手 KnowFabric 的 ontology-first rebuild track。

开始前先阅读这些文件并按其约束工作：
- CLAUDE.md
- docs/README.md
- docs/adr/0003-promote-knowfabric-to-domain-knowledge-authority.md
- docs/09_ontology-authority-architecture.md
- docs/10_rebuild-plan.md
- 如有需要，再参考 docs/03_domain-package-spec.md 和 docs/05_phase-plan.md 了解 legacy 基线

这次工作的硬边界：
1. 保留六层证据链，不允许跳过 Document -> Page -> Chunk。
2. KnowFabric 只拥有设备类本体、知识对象、证据追溯和语义化交付契约；不要把项目实例、站点拓扑、点位绑定、运行控制塞进来。
3. 优先把新结构做成 v2 形式，尽量与 legacy 并存，不要直接破坏旧结构，除非证据充分。
4. 如果要改 schema、包结构或 API，请先说明你看到的现状、差距和准备采取的最小可逆路径。
5. 如果有代码或文档改动，结束前运行 bash scripts/check-all。

工作方式：
- 先检查当前仓库状态和相关目录，再开始编辑。
- 先给出你对当前任务的理解和一个短计划，然后直接执行。
- 做出合理假设，但在最终说明里明确写出。
- 优先推进 docs/10_rebuild-plan.md 里的 immediate backlog，除非我另有指示。

本次请先判断最适合推进的下一步，并直接开始；如果存在明显更优的切入点，也可以调整，但要解释原因。
```

---

## Good Next Tasks

If the new session needs a concrete ticket, start with one of these:

1. Define the schema contract for `domain_packages/*/package.yaml` and `ontology/classes.yaml`.
2. Create an `hvac` domain package `v2` skeleton beside the legacy package.
3. Draft storage contracts for ontology classes, aliases, mappings, chunk anchors, and knowledge objects.
4. Draft semantic API and MCP contracts for ontology-based knowledge delivery.

---

## When To Stop And Escalate

Pause and ask for a decision only when:

- a change would collapse the boundary between KnowFabric and downstream runtime systems
- a migration would destroy legacy package structure without a compatibility path
- ontology identifiers cannot be stabilized without a domain decision
