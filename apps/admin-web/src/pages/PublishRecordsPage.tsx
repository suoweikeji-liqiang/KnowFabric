import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAsyncResource } from "../hooks/useAsyncResource";
import { useNormalizedSelection } from "../hooks/useNormalizedSelection";
import { usePersistentPageState } from "../hooks/usePersistentPageState";
import { DataTable } from "../components/DataTable";
import { MasterDetailPage } from "../components/MasterDetailPage";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { Tabs } from "../components/Tabs";
import { domainLabels, releaseStatusLabels } from "../data/lookups";
import { getAdminDataSource } from "../services/adminDataSource";
import { runApplyReady } from "../services/adminMutations";
import { PublishRecord } from "../types";
import { formatCount } from "../utils/format";

function releaseTone(status: PublishRecord["status"]) {
  if (status === "success") return "success";
  if (status === "partial") return "warning";
  return "danger";
}

export function PublishRecordsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const dataSource = useMemo(() => getAdminDataSource(), []);
  const { data, loading, error, refresh } = useAsyncResource(
    () => dataSource.getPublishRecordsSnapshot(),
    [dataSource],
  );
  const allRecords = data?.records ?? [];
  const [state, , patchState] = usePersistentPageState("kf.page.publish-records", {
    domain: "all",
    status: "all",
    query: "",
    selectedId: allRecords[0]?.id ?? null,
    tab: "results",
  });
  const deferredQuery = useDeferredValue(state.query);
  const [actionState, setActionState] = useState<string>("");
  const [actionError, setActionError] = useState<string>("");

  const filtered = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();
    return allRecords.filter((record) => {
      const haystack = [record.id, record.workspace, record.operator, record.summary].join(" ").toLowerCase();
      return (
        (state.domain === "all" || record.domainId === state.domain) &&
        (state.status === "all" || record.status === state.status) &&
        (!normalizedQuery || haystack.includes(normalizedQuery))
      );
    });
  }, [allRecords, deferredQuery, state.domain, state.status]);

  useNormalizedSelection(filtered, state.selectedId, (record) => record.id, (selectedId) =>
    patchState({ selectedId }),
  );

  const selected = filtered.find((record) => record.id === state.selectedId) ?? null;
  const linkedPacks = data?.linkedPacksForRecord(selected) ?? [];
  const activeWorkspaceId = selected?.workspaceId ?? data?.workspaceId;

  useEffect(() => {
    const recordId = searchParams.get("record");
    if (!recordId) {
      return;
    }
    if (allRecords.some((item) => item.id === recordId) && state.selectedId !== recordId) {
      patchState({ selectedId: recordId });
    }
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("record");
    setSearchParams(nextParams, { replace: true });
  }, [allRecords, patchState, searchParams, setSearchParams, state.selectedId]);

  const leftPane = (
    <Panel title="发布批次" meta={`当前批次 ${formatCount(filtered.length)} 个`}>
      {loading && !data ? (
        <div className="empty-state">加载中...</div>
      ) : error ? (
        <div className="empty-state">加载失败：{error}</div>
      ) : (
        <DataTable
          columns={[
            { key: "id", label: "批次号", render: (row) => row.id },
            { key: "time", label: "时间", render: (row) => row.executedAt },
            {
              key: "status",
              label: "状态",
              render: (row) => <StatusBadge label={releaseStatusLabels[row.status]} tone={releaseTone(row.status)} />,
            },
            { key: "count", label: "成功/失败", render: (row) => `${row.successCount} / ${row.failureCount}` },
            { key: "workspace", label: "工作区", render: (row) => row.workspace },
          ]}
          rows={filtered}
          rowKey={(row) => row.id}
          selectedKey={state.selectedId}
          onSelect={(row) => patchState({ selectedId: row.id })}
          emptyState="当前筛选条件下没有发布记录。"
        />
      )}
    </Panel>
  );

  const rightPane = selected ? (
    <Panel
      title="发布详情"
      meta={`${selected.id} · ${selected.workspace}`}
      actions={
        <>
          <button
            className="ghost-button"
            onClick={async () => {
              const nextSnapshot = await refresh();
              if (selected?.id && nextSnapshot?.records.some((record) => record.id === selected.id)) {
                patchState({ selectedId: selected.id });
              } else if (nextSnapshot?.latestRecordId) {
                patchState({ selectedId: nextSnapshot.latestRecordId });
              }
            }}
            type="button"
          >
            刷新状态
          </button>
          <button
            className="primary-button"
            onClick={async () => {
              if (!activeWorkspaceId) {
                return;
              }
              try {
                setActionError("");
                setActionState("执行发布中...");
                const result = await runApplyReady(activeWorkspaceId);
                const nextSnapshot = await refresh();
                patchState({
                  selectedId: result.publish_record_id || nextSnapshot?.latestRecordId || state.selectedId,
                });
                setActionState(
                  (result.summary?.failed || 0) > 0 ? "发布完成，但存在失败项" : "发布完成",
                );
              } catch (caught) {
                setActionError(caught instanceof Error ? caught.message : String(caught));
                setActionState("");
              }
            }}
            type="button"
          >
            执行发布
          </button>
        </>
      }
    >
      <div className="detail-header">
        <div>
          <h2>{selected.summary}</h2>
          <p>
            {domainLabels[selected.domainId]} · {selected.executedAt} · 操作人 {selected.operator}
          </p>
          {actionState ? <p className="action-text">{actionState}</p> : null}
          {actionError ? <p className="action-text action-error">{actionError}</p> : null}
        </div>
        <StatusBadge label={releaseStatusLabels[selected.status]} tone={releaseTone(selected.status)} />
      </div>
      <Tabs
        activeTab={state.tab}
        onChange={(tab) => patchState({ tab })}
        tabs={[
          {
            id: "results",
            label: "发布结果",
            content: (
              <div className="detail-grid">
                <div>
                  <span>成功数</span>
                  <strong>{selected.successCount}</strong>
                </div>
                <div>
                  <span>失败数</span>
                  <strong>{selected.failureCount}</strong>
                </div>
                <div>
                  <span>领域</span>
                  <strong>{domainLabels[selected.domainId]}</strong>
                </div>
                <div>
                  <span>工作区</span>
                  <strong>{selected.workspace}</strong>
                </div>
                <div>
                  <span>记录类型</span>
                  <strong>{selected.recordMode === "apply_run" ? "实际发布批次" : "待发布快照"}</strong>
                </div>
              </div>
            ),
          },
          {
            id: "items",
            label: "对象清单",
            content: (
              <div className="stack-section">
                {selected.items.map((item) => (
                  <article key={`${item.packId || item.name}-${item.result}`} className="link-card">
                    <span>{item.type}</span>
                    <strong>{item.name}</strong>
                    <p className="panel-meta">{item.note}</p>
                    {item.docName ? <p className="panel-meta">文档：{item.docName}</p> : null}
                    {item.equipmentClassLabel ? <p className="panel-meta">设备类：{item.equipmentClassLabel}</p> : null}
                    <div className="detail-badges">
                      {item.knowledgeObjectId ? (
                        <button
                          className="ghost-button"
                          onClick={() => navigate(`/knowledge-assets?asset=${encodeURIComponent(item.knowledgeObjectId!)}`)}
                          type="button"
                        >
                          查看成果
                        </button>
                      ) : null}
                      {item.docId ? (
                        <button
                          className="ghost-button"
                          onClick={() => navigate(`/documents?doc=${encodeURIComponent(item.docId!)}`)}
                          type="button"
                        >
                          查看文档
                        </button>
                      ) : null}
                      {item.equipmentClassId ? (
                        <button
                          className="ghost-button"
                          onClick={() =>
                            navigate(
                              `/domain-assets?coverage=${encodeURIComponent(`${selected.domainId}__${item.equipmentClassId}`)}`,
                            )
                          }
                          type="button"
                        >
                          查看设备类
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            ),
          },
          {
            id: "errors",
            label: "错误信息",
            content: selected.errors.length ? (
              <div className="stack-section">
                {selected.errors.map((error) => (
                  <article key={error} className="note-card is-danger">
                    {error}
                  </article>
                ))}
                {selected.detailsText ? <article className="note-card">{selected.detailsText}</article> : null}
              </div>
            ) : (
              <div className="stack-section">
                {selected.detailsText ? <article className="note-card">{selected.detailsText}</article> : null}
                {!selected.detailsText ? <div className="empty-state">当前批次没有错误信息。</div> : null}
              </div>
            ),
          },
          {
            id: "packs",
            label: "关联审阅包",
            content: (
              <div className="stack-section">
                {linkedPacks.length ? (
                  linkedPacks.map((pack) => (
                    <article key={pack.id} className="link-card">
                      <span>{pack.id}</span>
                      <strong>{pack.name}</strong>
                      <div className="detail-badges">
                        <button
                          className="ghost-button"
                          onClick={() => navigate(`/review-center?pack=${encodeURIComponent(pack.id)}`)}
                          type="button"
                        >
                          查看审阅包
                        </button>
                        <button
                          className="ghost-button"
                          onClick={() =>
                            navigate(
                              `/domain-assets?coverage=${encodeURIComponent(`${pack.domainId}__${pack.equipmentClass}`)}`,
                            )
                          }
                          type="button"
                        >
                          查看设备类
                        </button>
                      </div>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">当前批次没有关联审阅包。</div>
                )}
              </div>
            ),
          },
        ]}
      />
    </Panel>
  ) : (
    <Panel title="发布详情" meta="未选择对象">
      <div className="empty-state">先从左侧选择一条发布记录。</div>
    </Panel>
  );

  return (
    <MasterDetailPage
      title="发布记录"
      split="minmax(430px, 44%) minmax(520px, 56%)"
      actions={
        <>
          <button className="secondary-button" onClick={() => void refresh()} type="button">
            刷新
          </button>
          <button
            className="secondary-button"
            onClick={() => {
              if (data?.latestRecordId) {
                patchState({ selectedId: data.latestRecordId });
              }
            }}
            type="button"
          >
            查看最新批次
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
            <option value="all">全部状态</option>
            <option value="success">成功</option>
            <option value="partial">部分失败</option>
            <option value="failed">失败</option>
          </select>
          <input
            placeholder="搜索批次、工作区、操作人"
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
