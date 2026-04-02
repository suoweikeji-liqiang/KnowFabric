import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { MasterDetailPage } from "../components/MasterDetailPage";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { Tabs } from "../components/Tabs";
import { useAsyncResource } from "../hooks/useAsyncResource";
import { useNormalizedSelection } from "../hooks/useNormalizedSelection";
import { usePersistentPageState } from "../hooks/usePersistentPageState";
import { documentStatusLabels, domainLabels, sourceTypeLabels } from "../data/lookups";
import { getAdminDataSource } from "../services/adminDataSource";
import { chunkDocument, parseDocument, prepareReviewBundle } from "../services/adminMutations";
import { DocumentRecord } from "../types";
import { formatCount, joinOrDash } from "../utils/format";

function statusTone(status: DocumentRecord["status"]) {
  if (status === "chunked") return "success";
  if (status === "parsed") return "cool";
  if (status === "failed") return "danger";
  return "warning";
}

export function DocumentsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const dataSource = useMemo(() => getAdminDataSource(), []);
  const { data, loading, error, refresh } = useAsyncResource(
    () => dataSource.getDocumentsSnapshot(),
    [dataSource],
  );
  const allDocuments = data?.documents ?? [];
  const [state, , patchState] = usePersistentPageState("kf.page.documents", {
    domain: "all",
    status: "all",
    sourceType: "all",
    query: "",
    selectedId: allDocuments[0]?.id ?? null,
    tab: "overview",
  });
  const deferredQuery = useDeferredValue(state.query);
  const [actionState, setActionState] = useState<string>("");
  const [actionError, setActionError] = useState<string>("");

  const filtered = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();
    return allDocuments.filter((record) => {
      const haystack = [
        record.fileName,
        record.id,
        ...record.equipmentClasses,
        ...(record.equipmentClassLabels || []),
      ]
        .join(" ")
        .toLowerCase();
      return (
        (state.domain === "all" || record.domainId === state.domain) &&
        (state.status === "all" || record.status === state.status) &&
        (state.sourceType === "all" || record.sourceType === state.sourceType) &&
        (!normalizedQuery || haystack.includes(normalizedQuery))
      );
    });
  }, [allDocuments, deferredQuery, state.domain, state.sourceType, state.status]);

  useNormalizedSelection(filtered, state.selectedId, (record) => record.id, (selectedId) =>
    patchState({ selectedId }),
  );

  const selected = filtered.find((record) => record.id === state.selectedId) ?? null;
  const linkedAssets = data?.linkedAssetsForDocument(selected) ?? [];
  const preferredPrepareTarget = selected?.prepareTargets?.[0] ?? null;

  useEffect(() => {
    const docId = searchParams.get("doc");
    if (!docId) {
      return;
    }
    if (allDocuments.some((item) => item.id === docId) && state.selectedId !== docId) {
      patchState({ selectedId: docId });
    }
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("doc");
    setSearchParams(nextParams, { replace: true });
  }, [allDocuments, patchState, searchParams, setSearchParams, state.selectedId]);

  const leftPane = (
    <Panel title="文档列表" meta={`当前文档 ${formatCount(filtered.length)} 份`}>
      {loading && !data ? (
        <div className="empty-state">加载中...</div>
      ) : error ? (
        <div className="empty-state">加载失败：{error}</div>
      ) : (
        <DataTable
          columns={[
            {
              key: "file",
              label: "文档",
              render: (row) => (
                <div className="cell-stack">
                  <strong>{row.fileName}</strong>
                  <span>{row.id}</span>
                </div>
              ),
            },
            { key: "domain", label: "领域", render: (row) => domainLabels[row.domainId] },
            {
              key: "status",
              label: "状态",
              render: (row) => <StatusBadge label={documentStatusLabels[row.status]} tone={statusTone(row.status)} />,
            },
            { key: "pages", label: "页/Chunk", render: (row) => `${row.pageCount} / ${row.chunkCount}` },
            { key: "source", label: "来源", render: (row) => sourceTypeLabels[row.sourceType] },
          ]}
          rows={filtered}
          rowKey={(row) => row.id}
          selectedKey={state.selectedId}
          onSelect={(row) => patchState({ selectedId: row.id })}
          emptyState="当前筛选条件下没有文档。"
        />
      )}
    </Panel>
  );

  const rightPane = selected ? (
    <Panel
      title="文档详情"
      meta={`${selected.fileName} · ${selected.id}`}
      actions={
        <>
          <button
            className="ghost-button"
            onClick={async () => {
              try {
                setActionError("");
                setActionState("解析中...");
                await parseDocument(selected.id);
                await refresh();
                setActionState("解析完成");
              } catch (caught) {
                setActionError(caught instanceof Error ? caught.message : String(caught));
                setActionState("");
              }
            }}
            type="button"
          >
            解析文档
          </button>
          <button
            className="ghost-button"
            onClick={async () => {
              try {
                setActionError("");
                setActionState("切块中...");
                await chunkDocument(selected.id);
                await refresh();
                setActionState("切块完成");
              } catch (caught) {
                setActionError(caught instanceof Error ? caught.message : String(caught));
                setActionState("");
              }
            }}
            type="button"
          >
            生成 Chunk
          </button>
          <button
            className="primary-button"
            onClick={async () => {
              try {
                setActionError("");
                setActionState("准备候选中...");
                const result = await prepareReviewBundle({
                  domain_id: selected.domainId,
                  doc_id: selected.id,
                  equipment_class_id: preferredPrepareTarget?.equipmentClassId ?? null,
                });
                setActionState("已生成审阅包");
                const packFile = result.review_workspace?.packs?.[0]?.pack_file;
                navigate(packFile ? `/review-center?pack=${encodeURIComponent(packFile)}` : "/review-center");
              } catch (caught) {
                setActionError(caught instanceof Error ? caught.message : String(caught));
                setActionState("");
              }
            }}
            type="button"
          >
            准备候选
          </button>
        </>
      }
    >
      <div className="detail-header">
        <div>
          <h2>{selected.fileName}</h2>
          <p>{selected.stageSummary}</p>
          {actionState ? <p className="action-text">{actionState}</p> : null}
          {actionError ? <p className="action-text action-error">{actionError}</p> : null}
        </div>
        <StatusBadge label={documentStatusLabels[selected.status]} tone={statusTone(selected.status)} />
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
                  <strong>{joinOrDash(selected.equipmentClassLabels || selected.equipmentClasses)}</strong>
                </div>
                <div>
                  <span>页数</span>
                  <strong>{selected.pageCount}</strong>
                </div>
                <div>
                  <span>切块数量</span>
                  <strong>{selected.chunkCount}</strong>
                </div>
                <div className="detail-grid-span">
                  <span>候选目标</span>
                  <strong>
                    {selected.prepareTargets?.length
                      ? selected.prepareTargets
                          .map((item) => `${item.equipmentClassLabel} (${item.anchorCount})`)
                          .join("，")
                      : "未解析出明确设备类目标"}
                  </strong>
                </div>
                <div className="detail-grid-span">
                  <span>处理链</span>
                  <strong>{joinOrDash(selected.stageTimeline)}</strong>
                </div>
              </div>
            ),
          },
          {
            id: "pages",
            label: "页面",
            content: (
              <div className="stack-section">
                {selected.pageNotes.map((note) => (
                  <article key={note} className="note-card">
                    {note}
                  </article>
                ))}
              </div>
            ),
          },
          {
            id: "chunks",
            label: "切块",
            content: (
              <div className="stack-section">
                {selected.chunkHighlights.length ? (
                  selected.chunkHighlights.map((chunkId) => (
                    <article key={chunkId} className="link-card">
                      <span>重点切块</span>
                      <strong>{chunkId}</strong>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">当前没有可展示的切块高亮。</div>
                )}
              </div>
            ),
          },
          {
            id: "assets",
            label: "关联成果",
            content: (
              <div className="stack-section">
                {linkedAssets.length ? (
                  linkedAssets.map((asset) => (
                    <article key={asset.id} className="link-card">
                      <span>{asset.canonicalKey}</span>
                      <strong>{asset.title}</strong>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">当前文档还没有关联成果。</div>
                )}
              </div>
            ),
          },
        ]}
      />
    </Panel>
  ) : (
    <Panel title="文档详情" meta="未选择对象">
      <div className="empty-state">先从左侧选择一份文档。</div>
    </Panel>
  );

  return (
    <MasterDetailPage
      title="文档管理"
      split="minmax(400px, 42%) minmax(540px, 58%)"
      actions={
        <>
          <button className="secondary-button" onClick={() => void refresh()} type="button">
            刷新
          </button>
          <button className="secondary-button" type="button">
            导入文档
          </button>
          <button className="primary-button" type="button">
            批量准备候选
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
          <select value={state.status} onChange={(event) => patchState({ status: event.target.value })}>
            <option value="all">全部处理状态</option>
            <option value="imported">已导入</option>
            <option value="parsed">已解析</option>
            <option value="chunked">已切块</option>
            <option value="failed">失败</option>
          </select>
          <select value={state.sourceType} onChange={(event) => patchState({ sourceType: event.target.value })}>
            <option value="all">全部来源</option>
            <option value="manual">内部手册</option>
            <option value="vendor">厂商资料</option>
            <option value="authority">权威资料</option>
          </select>
          <input
            placeholder="搜索文档名、doc_id、设备类"
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
