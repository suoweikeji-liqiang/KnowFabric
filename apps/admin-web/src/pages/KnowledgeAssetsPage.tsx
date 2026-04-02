import { useDeferredValue, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { MasterDetailPage } from "../components/MasterDetailPage";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { Tabs } from "../components/Tabs";
import { domainLabels, knowledgeTypeLabels, publishStatusLabels, reviewStatusLabels } from "../data/lookups";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { useNormalizedSelection } from "../hooks/useNormalizedSelection";
import { usePersistentPageState } from "../hooks/usePersistentPageState";
import { getAdminDataSource } from "../services/adminDataSource";
import { KnowledgeAsset } from "../types";
import { downloadJsonFile } from "../utils/download";
import { formatCount, joinOrDash } from "../utils/format";

function publishTone(status: KnowledgeAsset["publishStatus"]) {
  if (status === "published") return "success";
  if (status === "reviewed") return "cool";
  if (status === "archived") return "neutral";
  return "warning";
}

function reviewTone(status: KnowledgeAsset["reviewStatus"]) {
  if (status === "accepted") return "success";
  if (status === "review_ready") return "cool";
  if (status === "rejected") return "danger";
  return "pending";
}

export function KnowledgeAssetsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const dataSource = useMemo(() => getAdminDataSource(), []);
  const { data, loading, error, refresh } = useAsyncResource(
    () => dataSource.getKnowledgeAssetsSnapshot(),
    [dataSource],
  );
  const allAssets = data?.assets ?? [];
  const [state, , patchState] = usePersistentPageState("kf.page.knowledge-assets", {
    domain: "all",
    type: "all",
    review: "all",
    publish: "all",
    source: "all",
    query: "",
    selectedId: allAssets[0]?.id ?? null,
    tab: "overview",
  });
  const deferredQuery = useDeferredValue(state.query);

  const filtered = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();
    return allAssets.filter((asset) => {
      const searchText = [
        asset.title,
        asset.canonicalKey,
        asset.equipmentClass,
        asset.equipmentClassLabel || "",
        asset.sourceDocument,
      ]
        .join(" ")
        .toLowerCase();
      return (
        (state.domain === "all" || asset.domainId === state.domain) &&
        (state.type === "all" || asset.type === state.type) &&
        (state.review === "all" || asset.reviewStatus === state.review) &&
        (state.publish === "all" || asset.publishStatus === state.publish) &&
        (state.source === "all" || asset.sourceDocument === state.source) &&
        (!normalizedQuery || searchText.includes(normalizedQuery))
      );
    });
  }, [allAssets, deferredQuery, state.domain, state.publish, state.review, state.source, state.type]);

  useNormalizedSelection(filtered, state.selectedId, (asset) => asset.id, (selectedId) =>
    patchState({ selectedId }),
  );

  const selected = filtered.find((asset) => asset.id === state.selectedId) ?? null;
  const relatedDocuments = data?.relatedDocumentsForAsset(selected) ?? [];
  const primaryRelatedDocument = relatedDocuments[0] ?? null;

  useEffect(() => {
    const assetId = searchParams.get("asset");
    if (!assetId) {
      return;
    }
    if (allAssets.some((item) => item.id === assetId) && state.selectedId !== assetId) {
      patchState({ selectedId: assetId });
    }
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("asset");
    setSearchParams(nextParams, { replace: true });
  }, [allAssets, patchState, searchParams, setSearchParams, state.selectedId]);

  const leftPane = (
    <Panel title="成果列表" meta={`当前结果 ${formatCount(filtered.length)} 条`}>
      {loading && !data ? (
        <div className="empty-state">加载中...</div>
      ) : error ? (
        <div className="empty-state">加载失败：{error}</div>
      ) : (
        <DataTable
          columns={[
            {
              key: "title",
              label: "标题",
              render: (row) => (
                <div className="cell-stack">
                  <strong>{row.title}</strong>
                  <span>{row.canonicalKey}</span>
                </div>
              ),
            },
            {
              key: "equipment",
              label: "设备类",
              render: (row) => row.equipmentClassLabel || row.equipmentClass,
            },
            {
              key: "type",
              label: "类型",
              render: (row) => knowledgeTypeLabels[row.type],
            },
            {
              key: "status",
              label: "状态",
              render: (row) => (
                <div className="cell-stack">
                  <StatusBadge label={reviewStatusLabels[row.reviewStatus]} tone={reviewTone(row.reviewStatus)} />
                  <StatusBadge label={publishStatusLabels[row.publishStatus]} tone={publishTone(row.publishStatus)} />
                </div>
              ),
            },
            {
              key: "source",
              label: "来源",
              render: (row) => row.sourceDocument,
            },
          ]}
          rows={filtered}
          rowKey={(row) => row.id}
          selectedKey={state.selectedId}
          onSelect={(row) => patchState({ selectedId: row.id })}
          emptyState="当前筛选条件下没有知识成果。"
        />
      )}
    </Panel>
  );

  const rightPane = selected ? (
    <Panel
      title="成果详情"
      meta={`${selected.title} · ${selected.canonicalKey}`}
      actions={
        <>
          <button
            className="ghost-button"
            onClick={() => {
              if (primaryRelatedDocument) {
                navigate(`/documents?doc=${encodeURIComponent(primaryRelatedDocument.id)}`);
              }
            }}
            type="button"
          >
            查看来源文档
          </button>
          <button
            className="ghost-button"
            onClick={() => navigate(`/domain-assets?coverage=${encodeURIComponent(`${selected.domainId}__${selected.equipmentClass}`)}`)}
            type="button"
          >
            查看所属设备类
          </button>
        </>
      }
    >
      <div className="detail-header">
        <div>
          <h2>{selected.title}</h2>
          <p>{selected.summary}</p>
        </div>
        <div className="detail-badges">
          <StatusBadge label={reviewStatusLabels[selected.reviewStatus]} tone={reviewTone(selected.reviewStatus)} />
          <StatusBadge label={publishStatusLabels[selected.publishStatus]} tone={publishTone(selected.publishStatus)} />
        </div>
      </div>
      <Tabs
        activeTab={state.tab}
        onChange={(tab) => patchState({ tab })}
        tabs={[
          {
            id: "overview",
            label: "概览",
            content: (
              <div className="detail-grid">
                <div>
                  <span>领域</span>
                  <strong>{domainLabels[selected.domainId]}</strong>
                </div>
                <div>
                  <span>设备类</span>
                  <strong>{selected.equipmentClassLabel || selected.equipmentClass}</strong>
                </div>
                <div>
                  <span>知识类型</span>
                  <strong>{knowledgeTypeLabels[selected.type]}</strong>
                </div>
                <div>
                  <span>可信等级</span>
                  <strong>{selected.trustLevel}</strong>
                </div>
                <div className="detail-grid-span">
                  <span>适用范围</span>
                  <strong>{joinOrDash(selected.applicability)}</strong>
                </div>
              </div>
            ),
          },
          {
            id: "evidence",
            label: "证据",
            content: (
              <div className="stack-section">
                {selected.evidence.map((item) => (
                  <article key={item.chunkId} className="evidence-card">
                    <div className="evidence-meta">
                      <span>{item.documentName}</span>
                      <span>第 {item.pageNo} 页</span>
                      <span>{item.chunkId}</span>
                    </div>
                    <p className="quote-line">{item.excerpt}</p>
                    <pre>{item.evidenceText}</pre>
                  </article>
                ))}
              </div>
            ),
          },
          {
            id: "payload",
            label: "结构化内容",
            content: (
              <div className="code-card">
                <pre>{selected.payload}</pre>
              </div>
            ),
          },
          {
            id: "related",
            label: "来源与关联",
            content: (
              <div className="stack-section">
                <article className="link-card">
                  <span>来源文档</span>
                  <strong>{joinOrDash(relatedDocuments.map((item) => item.fileName))}</strong>
                </article>
                <article className="link-card">
                  <span>关联成果</span>
                  <strong>{joinOrDash(selected.relatedAssets)}</strong>
                </article>
              </div>
            ),
          },
        ]}
      />
    </Panel>
  ) : (
    <Panel title="成果详情" meta="未选择对象">
      <div className="empty-state">先从左侧选择一条成果。</div>
    </Panel>
  );

  return (
    <MasterDetailPage
      title="知识成果"
      split="minmax(420px, 46%) minmax(520px, 54%)"
      actions={
        <>
          <button className="secondary-button" onClick={() => void refresh()} type="button">
            刷新
          </button>
          <button
            className="primary-button"
            onClick={() => {
              if (!selected) {
                return;
              }
              let payload: unknown;
              try {
                payload = JSON.parse(selected.payload || "{}");
              } catch {
                payload = selected.payload;
              }
              downloadJsonFile(`${selected.canonicalKey || selected.id}.json`, {
                id: selected.id,
                title: selected.title,
                canonicalKey: selected.canonicalKey,
                domainId: selected.domainId,
                equipmentClass: selected.equipmentClass,
                type: selected.type,
                summary: selected.summary,
                trustLevel: selected.trustLevel,
                applicability: selected.applicability,
                payload,
                evidence: selected.evidence,
              });
            }}
            type="button"
          >
            导出结果
          </button>
        </>
      }
      filters={
        <>
          <select value={state.domain} onChange={(event) => patchState({ domain: event.target.value })}>
            <option value="all">全部领域</option>
            <option value="hvac">暖通空调</option>
            <option value="drive">变频驱动</option>
          </select>
          <select value={state.type} onChange={(event) => patchState({ type: event.target.value })}>
            <option value="all">全部知识类型</option>
            {Object.entries(knowledgeTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <select value={state.review} onChange={(event) => patchState({ review: event.target.value })}>
            <option value="all">全部审阅状态</option>
            <option value="pending">待审阅</option>
            <option value="accepted">已接受</option>
            <option value="review_ready">可复核</option>
          </select>
          <select value={state.publish} onChange={(event) => patchState({ publish: event.target.value })}>
            <option value="all">全部发布状态</option>
            <option value="draft">草稿</option>
            <option value="reviewed">已审阅</option>
            <option value="published">已发布</option>
          </select>
          <select value={state.source} onChange={(event) => patchState({ source: event.target.value })}>
            <option value="all">全部来源文档</option>
            {[...new Set(allAssets.map((asset) => asset.sourceDocument))].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <input
            placeholder="搜索标题、键值、设备类"
            type="search"
            value={state.query}
            onChange={(event) => patchState({ query: event.target.value })}
          />
        </>
      }
      leftPane={leftPane}
      rightPane={rightPane}
    />
  );
}
