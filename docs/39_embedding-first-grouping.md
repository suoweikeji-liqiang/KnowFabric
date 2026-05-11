# Embedding-First Grouping Upgrade

**Status:** Action list — execute in order
**Last Updated:** 2026-05-11
**Audience:** Codex / executing agent
**Parent plan:** [docs/38_merger-recovery-and-grouping-fix.md](38_merger-recovery-and-grouping-fix.md)

---

## 0. 为什么开这一份

[docs/38](38_merger-recovery-and-grouping-fix.md) 关闭后，[output/diagnostic/20260511T105130Z/grouping_trace.json](../output/diagnostic/20260511T105130Z/grouping_trace.json) 揭穿了一个关键事实：

```json
{"total_candidates": 147, "unique_names": 116,
 "llm_groups": 97, "mech_groups": 97,
 "llm_crossbrand_mech_split": 0}
```

**LLM grouping 在 batch=30 设置下与 mechanical slugify 完全一致**。当前 grouping 实质上等于 `_slugify_part`，LLM token 白花，0 个跨命名/跨语言同概念被识别。

DB 真实数据：

```
chiller KOs: 129
  Carrier 19XR: 78
  Trane CVGF: 20
  McQuay 主: 20
  McQuay PE/WS: 11

cross-publisher KOs: 1（是 F6 fixture artifact，不是产线产物）
cross-language KOs: 0
```

`Trane "External Chilled Water Setpoint"` 跟 `Carrier "Evaporator Leaving Water Temperature"` 跟 `McQuay "最低冷冻水出水温度"` 在 DB 里**仍然是 3 个独立 KO**。这是 KnowFabric 跨源合并能力的核心痛点。

本轮换 grouping 策略 —— **embedding-first clustering** —— 用语义向量做候选 cluster，再让 LLM 在小 cluster 内细化。任务 H1-H4 见 §4-§7。

---

## 1. 硬证据：BGE-M3 跨语言相似度测试（已跑）

操盘手环境跑 `bge-m3-mlx-4bit` (via oMLX, port 7999) 的测试结果：

| 配对 | A | B | cosine |
|------|---|---|--------|
| EN-CN-1 same | External Chilled Water Setpoint | 冷冻水出水温度设定 | **0.835** |
| EN-CN-2 same | Motor Current Limit | 电机电流限制 | **0.809** |
| EN-CN-3 same | Evaporator Leaving Water Temperature | 蒸发器出水温度 | **0.882** |
| EN-EN-1 same | External Chilled Water Setpoint | Evaporator Leaving Water Temperature Setpoint | **0.839** |
| EN-EN-2 same | External Current Limit Setpoint | Motor Current Limit | **0.800** |
| CN-CN-1 same | 冷冻水出水温度 | 最低冷冻水出水温度 | **0.981** |
| EN-EN diff | Chilled Water Setpoint | Safety Valve Pressure | **0.650** |
| CN-EN diff | 油压差 | Anti-Recycle Time Delay | **0.655** |
| EN-EN diff | Differential to Start | Guide Vane Opening Time | **0.625** |

**结论**：
- 同概念（含跨语言）：sim 0.80-0.98（6/6 ≥ 0.80）
- 不同概念：sim 0.62-0.66（3/3 ≤ 0.66）
- gap：0.14-0.20，足够区分
- Dim：1024
- 4-bit 量化在 chiller 域不掉链子

阈值 **0.78** 安全（同概念最低 0.80 仍命中；NEG 最高 0.655，buffer 0.125）。

---

## 2. 新架构：两阶段 embedding-first clustering

```
all candidate parameter_names
    ↓
[Stage 1] BGE-M3 embedding (本地, oMLX, port 7999)
    ↓
embeddings (1024-dim 向量)
    ↓
[Stage 2] 按 cosine ≥ 0.78 做 union-find clustering
    ↓
candidate clusters (每个 cluster ≤ 15 names, 跨语言跨命名都能聚到一起)
    ↓
[Stage 3] 每个 multi-name cluster 走一次 LLM (MiMo) 细化
    ↓
LLM 输出：
    - 真同概念 → 共享 canonical_key
    - 不同 facet（setpoint vs limit）→ 各自独立 canonical_key
    ↓
[Stage 4] 单 name cluster + LLM-refined groups → final mapping
    ↓
{name → canonical_key} dict
```

**取代当前 `_llm_group_and_normalize` 直接送 30 names 给 LLM 的策略**。新策略：
- embedding 处理"哪些名字可能相关"（跨语言/跨命名的语义连接）
- LLM 处理"相关的 names 是不是真同概念 / 多少个 facet"（小范围细判）

LLM 不再需要在 30+ names 里盲找同概念，**精度大幅提升 + 不会再 produce 280-member garbage**。

---

## 3. 修复路径概览

```
H1 (embedding_client + clustering 模块) ← 工程基础
  ↓
H2 (group_and_normalize 替换为 embedding-first 流程)
  ↓
H3 (chiller 域 corpus 重跑回测)
  ↓
H4 (docs/38 §9 全部验收 + 更新 W3 D5 REPORT)
```

---

## 4. H1：embedding_client + clustering 模块（半天）

### 4.1 新建 `packages/compiler/embedding_client.py`

```python
"""OpenAI-compatible embedding client for BGE-M3 via oMLX (local) or other backends."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional
from urllib import error, request

OMLX_BASE_URL = os.environ.get("OMLX_BASE_URL", "http://localhost:7999")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-m3-mlx-4bit")
EMBEDDING_DIM = 1024

CACHE_DIR = Path(os.environ.get("EMBEDDING_CACHE_DIR", "/tmp/knowfabric_embedding_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _api_key() -> str:
    key = os.environ.get("OMLX_API_KEY", "")
    if not key:
        raise RuntimeError("OMLX_API_KEY env var not set; oMLX requires authentication")
    return key


def _cache_path(text: str, model: str) -> Path:
    h = hashlib.sha1(f"{model}::{text}".encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"


def embed_one(text: str, *, model: str | None = None, retries: int = 3) -> list[float]:
    """Embed a single text. Caches result on disk by (model, text) hash."""
    model = model or EMBEDDING_MODEL
    cp = _cache_path(text, model)
    if cp.exists():
        return json.loads(cp.read_text())["embedding"]

    payload = {"model": model, "input": text}
    req = request.Request(
        f"{OMLX_BASE_URL.rstrip('/')}/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key()}",
        },
        method="POST",
    )

    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            with request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read())
            emb = body["data"][0]["embedding"]
            if len(emb) != EMBEDDING_DIM:
                raise RuntimeError(f"Expected dim {EMBEDDING_DIM}, got {len(emb)}")
            cp.write_text(json.dumps({"model": model, "text": text, "embedding": emb}))
            return emb
        except (error.URLError, error.HTTPError, KeyError, json.JSONDecodeError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
            continue

    raise RuntimeError(f"embedding failed after {retries} retries: {last_err}")


def embed_batch(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Embed multiple texts sequentially (oMLX may not support batch)."""
    return [embed_one(t, model=model) for t in texts]
```

### 4.2 新建 `packages/compiler/clustering.py`

```python
"""Cosine-similarity hierarchical clustering via union-find."""

from __future__ import annotations

import math


DEFAULT_THRESHOLD = 0.78  # see docs/39 §1; calibrated to BGE-M3 4-bit performance


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.parent[ri] = rj


def cluster_by_cosine(
    names: list[str],
    embeddings: list[list[float]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[list[str]]:
    """Greedy single-linkage clustering: any pair with sim ≥ threshold gets merged."""
    n = len(names)
    if n != len(embeddings):
        raise ValueError(f"names ({n}) and embeddings ({len(embeddings)}) length mismatch")
    if n == 0:
        return []

    uf = _UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):
            if cosine(embeddings[i], embeddings[j]) >= threshold:
                uf.union(i, j)

    clusters: dict[int, list[str]] = {}
    for i in range(n):
        clusters.setdefault(uf.find(i), []).append(names[i])
    return list(clusters.values())
```

### 4.3 新建测试

`tests/test_embedding_client.py`：

- Mock `urlopen` 返回 1024-dim 向量，断言 cache 命中后第二次调用不发请求
- 真调测试（如果 `OMLX_API_KEY` 在环境）：embed "test" 返回 1024-dim list

`tests/test_clustering.py`：

- 单 name → 单 cluster
- 高度相似的 3 个向量 → 1 cluster with 3 names
- 一对 sim > 0.78 + 一个孤立 → 2 clusters (含 2 names + 1 name)
- 大规模 100 个向量随机 → 不卡死

### 4.4 Done means

- `pytest tests/test_embedding_client.py tests/test_clustering.py` 全过
- `python -c "from packages.compiler.embedding_client import embed_one; print(len(embed_one('hello')))"` 输出 1024（需 OMLX_API_KEY 已设）
- cache 文件出现在 `/tmp/knowfabric_embedding_cache/`

---

## 5. H2：group_and_normalize 替换为 embedding-first 流程（1 天）

### 5.1 改 [packages/compiler/canonical_key.py](../packages/compiler/canonical_key.py)

**保留的部分**：
- terminology YAML 查找（高优先级 override）
- canonical_key registry append-only
- hash cache（基于输入 set）

**替换的部分**：
- 删掉 `BATCH_SIZE = 30` 分批逻辑
- 删掉直接送 30 names 给 LLM 的 `_llm_group_and_normalize` 调用
- 用下面的 embedding-first 流程替代

**新流程伪代码**：

```python
def group_and_normalize(names, *, domain_id, equipment_class_id, knowledge_object_type, backend_name=None):
    # 1. Existing cache + terminology YAML lookup
    cleaned = [str(n).strip() for n in names if str(n).strip()]
    if not cleaned:
        return {}

    input_hash = _hash_inputs(cleaned, knowledge_object_type)
    if input_hash in HASH_CACHE:
        return HASH_CACHE[input_hash]

    mapping: dict[str, str] = {}

    # 2. terminology YAML 高优先级 override
    terminology = _load_terminology()
    yaml_resolved, remaining = _apply_terminology(cleaned, terminology)
    mapping.update(yaml_resolved)

    if not remaining:
        HASH_CACHE[input_hash] = mapping
        return mapping

    # 3. Stage 1: embedding
    from packages.compiler.embedding_client import embed_batch
    embeddings = embed_batch(remaining)

    # 4. Stage 2: clustering by cosine
    from packages.compiler.clustering import cluster_by_cosine
    clusters = cluster_by_cosine(remaining, embeddings, threshold=0.78)

    # 5. Stage 3: per-cluster LLM refinement
    for cluster_names in clusters:
        if len(cluster_names) == 1:
            # Single name → mechanical slug
            n = cluster_names[0]
            ck = _slugify_part(n) or _hashed_slug(n)
            mapping[n] = f"{domain_id}:{equipment_class_id}:{_knowledge_type_prefix(knowledge_object_type)}:{ck}"
            _register([n], mapping[n])
        elif len(cluster_names) <= 15:
            # Cluster → LLM refine
            sub_groups = _llm_refine_cluster(
                cluster_names,
                domain_id=domain_id,
                equipment_class_id=equipment_class_id,
                knowledge_object_type=knowledge_object_type,
                backend_name=backend_name,
            )
            for sg in sub_groups:
                ck_full = f"{domain_id}:{equipment_class_id}:{_knowledge_type_prefix(knowledge_object_type)}:{sg['canonical_key']}"
                for n in sg["member_names"]:
                    mapping[n] = ck_full
                _register(sg["member_names"], ck_full)
        else:
            # Oversize cluster (rare): fallback split
            for n in cluster_names:
                ck = _slugify_part(n) or _hashed_slug(n)
                mapping[n] = f"{domain_id}:{equipment_class_id}:{_knowledge_type_prefix(knowledge_object_type)}:{ck}"
                _register([n], mapping[n])

    HASH_CACHE[input_hash] = mapping
    return mapping
```

### 5.2 新 helper `_llm_refine_cluster`

```python
def _llm_refine_cluster(
    cluster_names: list[str],
    *,
    domain_id: str,
    equipment_class_id: str,
    knowledge_object_type: str,
    backend_name: str | None = None,
) -> list[dict[str, Any]]:
    """Ask LLM whether cluster names are same concept or should split by facet.

    Returns list of sub-groups:
    [{"canonical_key": "...", "member_names": [...], "rationale": "..."}, ...]
    """
    backend = resolve_backend(backend_name=backend_name)
    if backend is None:
        # No LLM available → keep cluster as one group (trust embedding)
        suggested_ck = _slugify_part(cluster_names[0])
        return [{
            "canonical_key": suggested_ck,
            "member_names": cluster_names,
            "rationale": "No LLM backend; trusted embedding cluster",
        }]

    system = (
        f"You are normalizing {knowledge_object_type} names within a {equipment_class_id} domain. "
        f"Given a small set of candidate names that an embedding model judged similar, decide:"
        f"\n1. Which names refer to the EXACT same concept (same physical quantity, same facet)?"
        f"\n2. Which names are DIFFERENT facets of a related concept (e.g. setpoint vs limit vs alarm)?"
        f"\nReturn strict JSON: "
        f'{{"groups": [{{"canonical_key": "slug_name", "member_names": [...], "rationale": "..."}}]}}'
        f" — split into separate groups when facets differ."
    )
    user = json.dumps({"candidate_names": cluster_names}, ensure_ascii=False)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    try:
        payload = _request_json_completion(messages, backend)
        groups = payload.get("groups") or []
        # Validation: every name in cluster_names must appear in exactly one group
        covered = set()
        for g in groups:
            for n in g.get("member_names", []):
                covered.add(n)
        missing = [n for n in cluster_names if n not in covered]
        if missing:
            # LLM dropped names → put them in their own groups (mechanical)
            for n in missing:
                groups.append({
                    "canonical_key": _slugify_part(n) or _hashed_slug(n),
                    "member_names": [n],
                    "rationale": "LLM did not assign; mechanical fallback",
                })
        return groups
    except Exception:
        # LLM failure → trust embedding cluster as one group
        suggested_ck = _slugify_part(cluster_names[0])
        return [{
            "canonical_key": suggested_ck,
            "member_names": cluster_names,
            "rationale": "LLM refinement failed; trusted embedding cluster",
        }]
```

### 5.3 保留 E2/E3 防御性 sanity check 作 fallback

`_sanity_check_groups`（E2）和 merger 防御性 split（E3）**保留**，但不再是主路径 —— 只在 embedding 服务不可用且降级回旧 LLM grouping 时启用。

加一个 module-level switch：

```python
USE_EMBEDDING_FIRST = os.environ.get("KNOWFABRIC_USE_EMBEDDING_FIRST", "1") == "1"

def group_and_normalize(...):
    if USE_EMBEDDING_FIRST:
        return _group_via_embedding(...)
    else:
        return _group_via_batch_llm(...)  # 旧路径 + E2/E3 sanity
```

env var 默认开。Emergency fallback 用 `KNOWFABRIC_USE_EMBEDDING_FIRST=0`。

### 5.4 测试

`tests/test_canonical_key_embedding.py`：

- Mock `embed_batch` + `cluster_by_cosine` + `_llm_refine_cluster`
- 输入 ["External Chilled Water Setpoint", "Evaporator Leaving Water Temperature", "Safety Valve Pressure"]
- Mock embedding 使前两个 sim ≥ 0.78，第三个孤立
- Mock LLM 把前两个判同概念
- 断言 mapping 中前两个 → 同 canonical_key，第三个独立 key

### 5.5 Done means

- `pytest tests/test_canonical_key_embedding.py` 全过
- `KNOWFABRIC_USE_EMBEDDING_FIRST=1`（默认）下，跑测试 fixture 116 chiller names → 产出 ≤ 60 groups（合并发生），且其中至少 5 个 group 含 ≥ 2 names
- 没有 canonical_key 长度 ≤ 2 或纯数字（degenerate）

---

## 6. H3：chiller 域 corpus 重跑回测（半天）

### 6.1 前置

**强制 pg_dump**（docs/38 §8 治理纪律）：

```bash
pg_dump knowfabric > /tmp/h3_pre_rerun_$(date +%Y%m%dT%H%M%SZ).sql
```

### 6.2 操作

1. 清理现存 chiller 域 KO（让新 grouping 路径产生干净的结果）：

```sql
DELETE FROM knowledge_object_evidence
WHERE knowledge_object_id IN (
    SELECT knowledge_object_id FROM knowledge_object
    WHERE ontology_class_id = 'centrifugal_chiller'
);
DELETE FROM knowledge_object WHERE ontology_class_id = 'centrifugal_chiller';
```

2. 从历史 review-pack candidates JSONL 重新走 apply 路径：

```bash
python scripts/apply_review_packs_batch.py \
    --pack-paths <现有 chiller 域 packs> \
    --merger-backend mimo-compiler
# 默认 --use-merger 是 True（docs/37 §3 已切换）
# 默认 KNOWFABRIC_USE_EMBEDDING_FIRST=1
```

Carrier 19XR 的 candidates 已经在 [output/visual_evidence_batch/...](../output/visual_evidence_batch/) 里，**不要重抽**（doc 38 §11 第 8 条已约束）。

3. SQL 验证：

```sql
-- 总 KO 数
SELECT COUNT(*) FROM knowledge_object WHERE ontology_class_id = 'centrifugal_chiller';

-- 跨 publisher KO
SELECT canonical_key,
       jsonb_array_length(authority_summary_json->'layers') AS n_layers,
       (SELECT array_agg(DISTINCT layer->>'publisher')
        FROM jsonb_array_elements(authority_summary_json->'layers') layer
       ) AS publishers,
       consensus_state
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
  AND (SELECT COUNT(DISTINCT layer->>'publisher')
       FROM jsonb_array_elements(authority_summary_json->'layers') layer) >= 2;

-- consensus_state 分布
SELECT consensus_state, COUNT(*)
FROM knowledge_object
WHERE ontology_class_id = 'centrifugal_chiller'
GROUP BY consensus_state;
```

### 6.3 Done means（硬指标）

| 指标 | 目标 |
|------|------|
| **cross-publisher KOs**（publishers 数 ≥ 2 不同品牌）| **≥ 5 条** |
| 其中**跨语言**合并（EN + CN 至少一对，或 EN + CN + EN 三方）| **≥ 3 条** |
| 其中 Trane "Chilled Water Setpoint" + Carrier "Evaporator Leaving Water Temperature" 同 KO | **必须有** |
| 单 KO 的 authority_layers 数 | **≤ 8**（不要再回到 280-layer 怪物） |
| degenerate canonical_key (parameter:1 / 单字符)| **0** |
| consensus_state 分布种类 | **≥ 3 种**（含 agreed） |
| chiller 域总 KO 数 | **显著小于 129**（合并真发生） |

如果硬指标不达标，**dump grouping trace 让操盘手裁决**，不要再次给出"语义太难"诊断。

---

## 7. H4：更新 W3 D5 REPORT + 关闭文档（2 小时）

### 7.1 更新 [output/w3_multisource_baseline/REPORT.md](../output/w3_multisource_baseline/REPORT.md)

撤回之前所有"corpus gap"/"语义太难"诊断。写真数据：

- embedding-first 实施前后 cross-publisher KO 数对比
- 跨语言合并样本（如冷冻水设定 Trane EN ↔ Carrier EN ↔ McQuay CN）
- consensus_state 分布
- 总 KO 合并率

### 7.2 close docs/35 / 36 / 37 / 38

把 [docs/README.md](README.md) 这些条目加 "[CLOSED]" 标识，说明本轮工程链终结。

### 7.3 Done means

- W3 D5 REPORT 内容真数据，不再含 BLOCKED 字样
- docs/README.md 体现 doc 35-38 closed 状态

---

## 8. 验收（本轮 done）

完成下列 6 条本轮才算关闭：

1. H1：embedding_client + clustering 模块 + 单测全过
2. H2：group_and_normalize 走 embedding-first 路径，env var `KNOWFABRIC_USE_EMBEDDING_FIRST` 默认开
3. H3：chiller 域重跑后 SQL 验证满足全部硬指标（cross-publisher ≥ 5、跨语言 ≥ 3、含冷冻水概念合并）
4. H4：W3 D5 REPORT 真更新 + docs/README 关闭旧 docs
5. `pytest tests/` 全过；`bash scripts/check-all` 全过
6. pg_dump backup 存在（H3 前置）

---

## 9. 不做的事（防止散）

| 项目 | 为什么不做 |
|------|----------|
| 重新跑 Carrier 19XR 视觉抽取 | candidates JSONL 已经付 MiMo 配额产出，直接复用 |
| 删除 terminology YAML | 保留作高优先级 override，跟 embedding 协同 |
| 删除 E2/E3 防御性 sanity | 保留作 emergency fallback（`KNOWFABRIC_USE_EMBEDDING_FIRST=0`）|
| 加新 KO 类型 / 新 manual ingest | 先把 chiller 域 grouping 跑通 |
| 加新 health checks | 跟本文无关 |
| 改 v0.2 契约字段 | 不动 |
| 启动概念片 / 关系图实验 | 等本轮关闭 |
| 重构 scripts/ 大批量重命名 | 抽到 packages 的活由 future 任务管 |

---

## 10. 给 Codex 的执行约束

1. **`OMLX_API_KEY` 通过环境变量传入**，不允许写入代码或 commit 进仓。环境变量在 `.env.llm.local`（git ignored）配置。Codex 跑测试时如果发现 env 没设置，停下来问操盘手，**不要 hardcode key**

2. **threshold 0.78 是初始值**，跑出 H3 硬指标后**如有需要可调到 0.75-0.80 范围**，但调整必须写进 commit message 说明理由 + 跑回测的具体 cross-publisher 数变化

3. **embedding cache 写到 `/tmp/knowfabric_embedding_cache/`**，不入仓库。clear cache 用 `rm -rf` 即可

4. **H3 跑 chiller 域时，必须先 pg_dump**。这是 docs/38 §8 治理纪律，不能跳过。即使你认为 DB 当前状态不重要，也要 dump（避免再次出现像 docs/37 那种数据丢失）

5. **如果硬指标 H3 不达标**：
   - dump grouping trace 到 `output/diagnostic/<run_id>/embedding_first_trace.json`
   - 含：每个 cluster 的 names + 内部 cosine matrix + LLM 细化后的 sub-groups
   - **不要重写 cluster threshold 或 LLM prompt 几轮试错**，停下来问操盘手裁决

6. **任何 embedding 调用必须走 `packages/compiler/embedding_client.py` 的 `embed_one`/`embed_batch`**，禁止散在 scripts/ 里直接 HTTP

7. **保留 H1 之前的所有代码作 emergency fallback**：`KNOWFABRIC_USE_EMBEDDING_FIRST=0` 时回退到 E2/E3 sanity check 旧路径。删除旧代码等下一轮决定

8. **terminology YAML 仍然是高优先级 override**：embedding-first 流程要先查 YAML，再 embedding cluster。YAML 命中的 name 不走 embedding（节省调用）

9. **Codex 不许再以"corpus gap"/"语义太难"/"人工标注"为根本因停止工程修复**。这三种诊断都已经被 docs/36/37/38 否决。本轮如果 embedding-first 跑出来还不达标，唯一允许的回应是 dump trace + 等操盘手裁决

10. **R3/R4 代码（371b7fe）和 E1-E5（65e0482/720ee13/f70db05/eec8f2e/c200d1c）保留**，不要回滚或重写

---

## 11. 执行顺序

```
[确认 OMLX_API_KEY 在 env 已设, 跑 ollama 测试通]
  ↓
H1 (embedding_client + clustering 模块 + 单测)
  ↓
H2 (group_and_normalize 替换为 embedding-first)
  ↓
pg_dump backup
  ↓
H3 (chiller 域清理 + 重跑 apply + SQL 验证硬指标)
  ↓
H4 (REPORT 更新 + docs 关闭)
```

---

## CHANGELOG

- **2026-05-11**：初稿。基于 docs/38 跑后的 grouping_trace.json 诊断（LLM=mechanical 在 batch=30），引入 BGE-M3 跨语言 embedding clustering 作核心 grouping 策略。任务 H1-H4：embedding/clustering 模块 → group_and_normalize 替换 → chiller 域重跑验证 → REPORT 更新。BGE-M3-mlx-4bit 跨语言同概念 sim 0.80-0.98、不同概念 0.62-0.66，gap 充裕，阈值 0.78 安全。
