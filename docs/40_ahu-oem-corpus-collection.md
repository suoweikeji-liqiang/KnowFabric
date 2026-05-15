# 40 AHU OEM Corpus Collection (standalone task)

- Date: 2026-05-15
- Status: handoff to Codex, independent of chiller compile pipeline
- Predecessor: docs/34–39 (chiller domain compile/merger track)
- Postcondition: ahu domain has multi-publisher OEM corpus ready for extraction in a later round

---

## 1 背景

chiller 域 cross-publisher merge 已经跑通（centrifugal_chiller cross_pub ≈ 20–22，oracle PASS）。但是 ahu domain 现在的 KO 全部来自 ASHRAE G36 这一份系统级控制序列标准，**单 publisher，cross_pub = 0**。

根本原因不是 merger / clustering / extraction 不行——是 corpus 里**根本没有 AHU OEM 手册**。chiller 域全部 OEM 手册都是 Carrier 19XR / York YK / McQuay WMC / Trane CVHE / Gree 离心机，没有一份是 AHU 产品线。

本任务目的：**补全 ahu domain 的 OEM 手册原始语料**，让后续 extraction 跑出来时 cross-publisher merger 有真实的多 publisher 数据可以合并。

## 2 范围

### In scope
- 下载 ≥ 16 份 AHU OEM 手册 / Engineering Guide / Product Catalog（覆盖 ≥ 6 个 vendor）
- 落地到 `storage/authority_sources/hvac/oem/ahu/<vendor>/`
- 探测每份 PDF 的 `page_count` 和 `text_quality`（已有脚本 `scripts/inspect_document_text_quality.py`）
- 输出 `storage/authority_sources/hvac/oem/ahu/manifest.csv`

### Out of scope
- ❌ 不做 extraction / KO 写入（这是 PP 或后续轮次的事，不在本任务）
- ❌ 不动 ahu domain ontology schema
- ❌ 不修 chiller 域已有 KO 或 review pack
- ❌ 不下载 VRF / RTU / Fan Coil / Air Cooled Chiller 资料（focused AHU only）
- ❌ 不下载 marketing brochure / sales sheet（要的是技术 IOM、Engineering Guide、Product Data with technical tables）

## 3 厂家清单与 product family（验证为真）

下面的厂家入口和产品系列名是**已知存在**的。Codex 不要按下面的 URL 字面 hit，要进入 vendor literature 主站搜对应 product family，因为厂家网站经常改版，硬编码 URL 容易死。

### Tier 1：国外，公开下载，难度低

| Vendor | Literature 入口 | 已知 product family | 期望 doc 类型 | 目标份数 |
| --- | --- | --- | --- | --- |
| Carrier | carrier.com → Commercial → Air Handling Units | 39M, 39MN/MW, 39L/LB, 39CC, 39CQ | Product Data + IOM | 3 |
| Trane | trane.com → Commercial → Air Handlers → Literature | M-Series Climate Changer, T-Series, Performance Climate Changer (CSAA) | Catalog + IOM | 2–3 |
| Daikin Applied | daikinapplied.com → Products → Air Handlers | Vision (built-up), Skyline (indoor commercial), Maverick II (modular) | Catalog + IOM + Application Guide | 2–3 |
| Johnson Controls / York | johnsoncontrols.com → Document Library | Solution XT, Solution Plus, LD Custom | Engineering Guide + IOM | 2 |

### Tier 2：国内，可能要邮箱注册

| Vendor | Literature 入口 | 已知 product family | 目标份数 |
| --- | --- | --- | --- |
| 格力商用 | gree.com → 商用空调 → 组合式 / 模块化 → 资料下载 | 组合式空调机组、模块化空调机组、立柜式 | 2 |
| 美的中央空调 | midea.com → 商用 → 产品资料 → 空气处理机 | MDA 组合式、MEX 模块式 | 2 |
| 麦克维尔（中国） | daikinapplied.com.cn 或 mcquay-china.com | ZG / ZA 组合式空调箱 | 2 |
| 天加 Tica | tica.com.cn → 产品中心 → 空调机组 | 组合式空调机组、净化空调机组 | 2 |

### Tier 3：可选（时间宽松再做）
- Greenheck（DA、RV 系列）
- 申菱 Shenling（机房空调，shenglinairconditioner.com）
- 海尔商用 AHU
- 顿汉布什 Dunham-Bush AHU CHG/GHG

## 4 采集流程

每个 vendor 走这个循环：

1. **进入** vendor literature 主页（上表 Literature 入口）
2. **搜索** product family 名（上表 product family 列）
3. **筛选** doc 类型，优先级：IOM > Engineering Guide > Product Data Catalog > Application Guide
4. **下载** PDF
5. **重命名**，规则：`<vendor>_<model>_<doctype>[_<year>].pdf`
   - 例: `carrier_39M_IOM.pdf`、`trane_PerformanceClimateChanger_catalog_2022.pdf`、`gree_GHZ_modular_AHU_manual.pdf`
6. **落地**：`storage/authority_sources/hvac/oem/ahu/<vendor>/<filename>.pdf`
7. **探测元数据**：
   ```bash
   python scripts/inspect_document_text_quality.py <pdf_path>
   ```
   记录 `page_count`、`text_quality`（text / scanned / mixed）

## 5 Manifest 输出

`storage/authority_sources/hvac/oem/ahu/manifest.csv`：

```csv
vendor,model,doctype,language,file_path,page_count,text_quality,sha256,download_url,downloaded_at,notes
carrier,39M,IOM,en,storage/authority_sources/hvac/oem/ahu/carrier/carrier_39M_IOM.pdf,52,text,abc123...,https://...,2026-05-15,
gree,GHZ_modular,manual,zh,storage/authority_sources/hvac/oem/ahu/gree/gree_GHZ_modular_AHU_manual.pdf,180,text,def456...,https://...,2026-05-15,
trane,PerformanceClimateChanger,catalog,en,storage/authority_sources/hvac/oem/ahu/trane/...,240,text,...,2026-05-15,page_count>200_needs_section_aware
...
```

字段说明：
- `language`: `en` / `zh`（必须二选一，跨语言比例后面要看）
- `page_count`: 实际探测值，不是估计
- `text_quality`: `text` / `scanned` / `mixed`，由 `inspect_document_text_quality.py` 给出
- `sha256`: 文件实际 hash，用于去重
- `notes`: 自动标记 `page_count>200_needs_section_aware` 或 `text_quality=scanned_needs_visual_track`

## 6 验收标准

任务完成的硬指标：

- [ ] 总 PDF ≥ 16
- [ ] 覆盖 vendor ≥ 6（Tier 1 + Tier 2 凑齐 6 家最低要求）
- [ ] 每家 vendor ≥ 2 份 doc
- [ ] EN doc ≥ 30%，CN doc ≥ 30%（cross-language merge 后续测试要这个比例）
- [ ] `manifest.csv` 字段全部填齐，`page_count` 和 `text_quality` 经过实际探测（不是估计）
- [ ] `sha256` 去重，无重复文件
- [ ] `vendor_unreachable.csv` 记录所有抓失败的尝试（URL、错误码、时间），不要 fabricate

## 7 已知陷阱与对策

| 陷阱 | 对策 |
| --- | --- |
| Cloudflare / robots.txt 拦 curl | 用 `User-Agent: curl/8.4.0`（chiller 域已验证可用） |
| 厂家网站改版，老 URL 404 | **不要硬编码 URL**，从 vendor literature 主入口搜 product family 名 |
| 国内厂家要邮箱注册 | 用项目专用邮箱（操作员另发）；若注册门槛过高，跳过并记 `vendor_unreachable.csv` |
| 同一 PDF 镜像多份 | sha256 去重，保留命名最规范的一份 |
| Marketing brochure 没有技术参数 | 看目录里有没有 "Specifications / Performance Data / Dimensional Data / Control Sequence" 章节，没有就不要 |
| PDF 超大（300+ 页）下载慢 | 不要因为大就跳过；这正是 NN section-aware 要的素材 |
| PDF 是扫描件 | 不要跳过，标记 `text_quality=scanned`，后续走 visual track（FF 阶段已有能力） |

## 8 绝对不要做的事

- ❌ 不要 fabricate 不存在的 PDF URL（找不到就记 `vendor_unreachable.csv`）
- ❌ 不要因为"为了凑数量"下载 marketing PDF
- ❌ 不要为了让 cross_pub 数字好看而下载同一 vendor 的多个版本的同一份文档（去重 sha256 会查出来）
- ❌ 不要触发 chiller 域已有的 review pack / KO / merger pipeline
- ❌ 不要修改 ahu domain 的 ontology_class_v2 / brick_facet_map / 任何 schema 文件
- ❌ 不要在 task 完成报告里写"已下载 N 份" 但 manifest.csv 没对应行——一切以 manifest.csv 为准

## 9 交付物

1. `storage/authority_sources/hvac/oem/ahu/<vendor>/*.pdf` — 实际 PDF 文件
2. `storage/authority_sources/hvac/oem/ahu/manifest.csv` — 完整 manifest
3. `storage/authority_sources/hvac/oem/ahu/vendor_unreachable.csv` — 失败记录（若有）
4. `output/diagnostic/<timestamp>_ahu_corpus_collection/REPORT.md` — 简短跑批报告：每个 vendor 下了几份、language 分布、page_count 分布、scanned 比例

## 10 后续衔接

本任务**不触发** extraction。完成后下一轮（PP 或独立轮次）会：

1. 用 `scripts/import_documents.py` 把 `storage/authority_sources/hvac/oem/ahu/` 导入 document 表，domain=hvac，预计 routing 到 `ahu` ontology_class（部分可能路由到 `air_handler`、`fan_coil_unit` 子类，正常）
2. 跑 doc-level extraction（或 section-aware for 大文件）
3. 跑 review pack apply + merger
4. 验证 ahu domain cross_pub 从 0 上升到 ≥ 3

那是后话。本任务**只采集，不抽取**。
