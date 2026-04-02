import { useDeferredValue, useMemo } from "react";

import { useAsyncResource } from "../hooks/useAsyncResource";
import { useNormalizedSelection } from "../hooks/useNormalizedSelection";
import { usePersistentPageState } from "../hooks/usePersistentPageState";
import { MasterDetailPage } from "../components/MasterDetailPage";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { Tabs } from "../components/Tabs";
import { coverageStatusLabels, domainLabels, knowledgeTypeLabels } from "../data/lookups";
import { getAdminDataSource } from "../services/adminDataSource";
import { EquipmentCoverage } from "../types";
import { formatCount, joinOrDash } from "../utils/format";

function tone(status: EquipmentCoverage["status"]) {
  if (status === "covered") return "success";
  if (status === "partial") return "cool";
  if (status === "thin") return "warning";
  return "danger";
}

export function DomainAssetsPage() {
  const dataSource = useMemo(() => getAdminDataSource(), []);
  const { data, loading, error, refresh } = useAsyncResource(
    () => dataSource.getDomainAssetsSnapshot(),
    [dataSource],
  );
  const allCoverage = data?.coverage ?? [];
  const [state, , patchState] = usePersistentPageState("kf.page.domain-assets", {
    domain: "all",
    status: "all",
    type: "all",
    query: "",
    selectedId: allCoverage[0]?.id ?? null,
    tab: "coverage",
  });
  const deferredQuery = useDeferredValue(state.query);

  const filtered = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();
    return allCoverage.filter((item) => {
      const haystack = [item.label, item.id].join(" ").toLowerCase();
      return (
        (state.domain === "all" || item.domainId === state.domain) &&
        (state.status === "all" || item.status === state.status) &&
        (state.type === "all" ||
          item.coveredTypes.includes(state.type as never) ||
          item.missingTypes.includes(state.type as never)) &&
        (!normalizedQuery || haystack.includes(normalizedQuery))
      );
    });
  }, [allCoverage, deferredQuery, state.domain, state.status, state.type]);

  useNormalizedSelection(filtered, state.selectedId, (item) => item.id, (selectedId) =>
    patchState({ selectedId }),
  );

  const selected = filtered.find((item) => item.id === state.selectedId) ?? null;
  const relatedDocs = data?.documentsForCoverage(selected) ?? [];
  const relatedAssets = data?.assetsForCoverage(selected) ?? [];

  const leftPane = (
    <Panel title="领域树" meta={`设备类 ${formatCount(filtered.length)} 个`}>
      {loading && !data ? (
        <div className="empty-state">加载中...</div>
      ) : error ? (
        <div className="empty-state">加载失败：{error}</div>
      ) : (
        <div className="tree-list">
          {["hvac", "drive"].map((groupId) => {
            const groupItems = filtered.filter((item) => item.domainId === groupId);
            if (!groupItems.length) return null;
            return (
              <div key={groupId} className="tree-group">
                <p className="tree-group-title">{domainLabels[groupId as "hvac" | "drive"]}</p>
                {groupItems.map((item) => (
                  <button
                    key={item.id}
                    className={`tree-item ${item.id === state.selectedId ? "is-active" : ""}`}
                    onClick={() => patchState({ selectedId: item.id })}
                    type="button"
                  >
                    <span>
                      <strong>{item.label}</strong>
                      <small>{item.id.replace("cov_", "")}</small>
                    </span>
                    <StatusBadge label={coverageStatusLabels[item.status]} tone={tone(item.status)} />
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </Panel>
  );

  const rightPane = selected ? (
    <Panel title="设备类详情" meta={`${selected.label} · ${selected.id}`}>
      <div className="detail-header">
        <div>
          <h2>{selected.label}</h2>
          <p>{selected.summary}</p>
        </div>
        <StatusBadge label={coverageStatusLabels[selected.status]} tone={tone(selected.status)} />
      </div>
      <Tabs
        activeTab={state.tab}
        onChange={(tab) => patchState({ tab })}
        tabs={[
          {
            id: "coverage",
            label: "覆盖概览",
            content: (
              <div className="detail-grid">
                <div>
                  <span>领域</span>
                  <strong>{domainLabels[selected.domainId]}</strong>
                </div>
                <div>
                  <span>成果数</span>
                  <strong>{selected.assetCount}</strong>
                </div>
                <div>
                  <span>文档数</span>
                  <strong>{selected.documentCount}</strong>
                </div>
                <div>
                  <span>更新时间</span>
                  <strong>{selected.updatedAt}</strong>
                </div>
                <div className="detail-grid-span">
                  <span>已覆盖</span>
                  <strong>{joinOrDash(selected.coveredTypes.map((item) => knowledgeTypeLabels[item]))}</strong>
                </div>
                <div className="detail-grid-span">
                  <span>缺失</span>
                  <strong>{joinOrDash(selected.missingTypes.map((item) => knowledgeTypeLabels[item]))}</strong>
                </div>
              </div>
            ),
          },
          {
            id: "assets",
            label: "成果列表",
            content: (
              <div className="stack-section">
                {relatedAssets.length ? (
                  relatedAssets.map((asset) => (
                    <article key={asset.id} className="link-card">
                      <span>{knowledgeTypeLabels[asset.type]}</span>
                      <strong>{asset.title}</strong>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">当前设备类还没有成果。</div>
                )}
              </div>
            ),
          },
          {
            id: "documents",
            label: "关联文档",
            content: (
              <div className="stack-section">
                {relatedDocs.length ? (
                  relatedDocs.map((doc) => (
                    <article key={doc.id} className="link-card">
                      <span>{doc.id}</span>
                      <strong>{doc.fileName}</strong>
                    </article>
                  ))
                ) : (
                  <div className="empty-state">当前设备类还没有关联文档。</div>
                )}
              </div>
            ),
          },
          {
            id: "gaps",
            label: "缺口说明",
            content: (
              <div className="stack-section">
                <article className="note-card">
                  优先从 {selected.missingTypes.length ? knowledgeTypeLabels[selected.missingTypes[0]] : "现有成果加固"} 入手，
                  保持证据链和设备类映射一致。
                </article>
              </div>
            ),
          },
        ]}
      />
    </Panel>
  ) : (
    <Panel title="设备类详情" meta="未选择对象">
      <div className="empty-state">先从左侧选择一个设备类。</div>
    </Panel>
  );

  return (
    <MasterDetailPage
      title="领域资产"
      split="minmax(340px, 38%) minmax(620px, 62%)"
      actions={
        <>
          <button className="secondary-button" onClick={() => void refresh()} type="button">
            刷新
          </button>
          <button className="secondary-button" type="button">
            导出覆盖清单
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
            <option value="all">全部覆盖状态</option>
            <option value="covered">已覆盖</option>
            <option value="partial">部分覆盖</option>
            <option value="thin">覆盖偏薄</option>
            <option value="missing">未覆盖</option>
          </select>
          <select value={state.type} onChange={(event) => patchState({ type: event.target.value })}>
            <option value="all">全部知识类型</option>
            {Object.entries(knowledgeTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <input
            placeholder="搜索设备类"
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
