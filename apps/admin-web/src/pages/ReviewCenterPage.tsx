import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useAsyncResource } from "../hooks/useAsyncResource";
import { useNormalizedSelection } from "../hooks/useNormalizedSelection";
import { usePersistentPageState } from "../hooks/usePersistentPageState";
import { DataTable } from "../components/DataTable";
import { MasterDetailPage } from "../components/MasterDetailPage";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import { Tabs } from "../components/Tabs";
import { domainLabels, knowledgeTypeLabels, packStatusLabels, reviewStatusLabels } from "../data/lookups";
import { getAdminDataSource } from "../services/adminDataSource";
import {
  bootstrapReviewPack,
  fetchReviewPack,
  saveReviewPack,
} from "../services/adminMutations";
import { ReviewCandidate, ReviewPack } from "../types";
import { formatCount } from "../utils/format";

function packTone(status: ReviewPack["status"]) {
  if (status === "ready") return "success";
  if (status === "blocked") return "danger";
  return "pending";
}

function reviewTone(status: ReviewCandidate["status"]) {
  if (status === "accepted") return "success";
  if (status === "review_ready") return "cool";
  if (status === "rejected") return "danger";
  return "pending";
}

export function ReviewCenterPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const dataSource = useMemo(() => getAdminDataSource(), []);
  const { data, loading, error, refresh } = useAsyncResource(
    () => dataSource.getReviewCenterSnapshot(),
    [dataSource],
  );
  const allPacks = data?.packs ?? [];
  const allCandidates = data?.candidates ?? [];
  const [state, , patchState] = usePersistentPageState("kf.page.review-center", {
    workspace: "原型版",
    status: "all",
    domain: "all",
    query: "",
    selectedPackId: allPacks[0]?.id ?? null,
    selectedCandidateId: allCandidates[0]?.id ?? null,
    tab: "editor",
  });
  const deferredQuery = useDeferredValue(state.query);
  const [formState, setFormState] = useState({
    title: "",
    canonicalKey: "",
    summary: "",
    trustLevel: "L3",
    payload: "{}",
  });
  const [actionState, setActionState] = useState("");
  const [actionError, setActionError] = useState("");

  const filteredPacks = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();
    return allPacks.filter((pack) => {
      const haystack = [pack.name, pack.equipmentClass, pack.equipmentClassLabel || ""].join(" ").toLowerCase();
      return (
        (state.status === "all" || pack.status === state.status) &&
        (state.domain === "all" || pack.domainId === state.domain) &&
        (!normalizedQuery || haystack.includes(normalizedQuery))
      );
    });
  }, [allPacks, deferredQuery, state.domain, state.status]);

  useNormalizedSelection(filteredPacks, state.selectedPackId, (pack) => pack.id, (selectedPackId) =>
    patchState({ selectedPackId }),
  );

  const selectedPack = filteredPacks.find((pack) => pack.id === state.selectedPackId) ?? null;
  const candidates = data?.candidatesForPack(selectedPack) ?? [];

  useNormalizedSelection(candidates, state.selectedCandidateId, (candidate) => candidate.id, (selectedCandidateId) =>
    patchState({ selectedCandidateId }),
  );

  const selectedCandidate = candidates.find((candidate) => candidate.id === state.selectedCandidateId) ?? null;

  useEffect(() => {
    const pack = searchParams.get("pack");
    if (!pack) {
      return;
    }
    if (allPacks.some((item) => item.id === pack) && state.selectedPackId !== pack) {
      patchState({ selectedPackId: pack });
    }
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("pack");
    setSearchParams(nextParams, { replace: true });
  }, [allPacks, patchState, searchParams, setSearchParams, state.selectedPackId]);

  useEffect(() => {
    if (!selectedCandidate) {
      return;
    }
    setFormState({
      title: selectedCandidate.title,
      canonicalKey: selectedCandidate.canonicalKey,
      summary: selectedCandidate.summary,
      trustLevel: selectedCandidate.trustLevel,
      payload: selectedCandidate.payload,
    });
  }, [selectedCandidate]);

  useEffect(() => {
    if (!data?.workspaceId || state.workspace === data.workspaceId) {
      return;
    }
    patchState({ workspace: data.workspaceId });
  }, [data?.workspaceId, patchState, state.workspace]);

  const persistCandidate = async (reviewDecision: "pending" | "accepted" | "rejected") => {
    if (!selectedPack || !selectedCandidate) {
      return;
    }
    setActionError("");
    setActionState("保存中...");
    try {
      const pack = await fetchReviewPack(selectedPack.id, selectedPack.workspaceId);
      const candidateEntries = Array.isArray(pack.candidate_entries) ? pack.candidate_entries : [];
      const target = candidateEntries.find((item) => item.candidate_id === selectedCandidate.id);
      if (!target) {
        throw new Error("未找到当前候选项");
      }
      let structuredPayload: Record<string, unknown> = {};
      try {
        structuredPayload = JSON.parse(formState.payload || "{}");
      } catch (caught) {
        throw new Error(caught instanceof Error ? `结构化内容不是合法 JSON：${caught.message}` : "结构化内容不是合法 JSON");
      }
      target.review_decision = reviewDecision;
      target.canonical_key_candidate = formState.canonicalKey;
      target.curation = {
        ...(typeof target.curation === "object" && target.curation ? target.curation : {}),
        title: formState.title,
        summary: formState.summary,
        structured_payload: structuredPayload,
        applicability: {},
        trust_level: formState.trustLevel,
      };
      await saveReviewPack(selectedPack.id, pack, selectedPack.workspaceId);
      const nextSnapshot = await refresh();
      if (reviewDecision !== "pending" && nextSnapshot) {
        const refreshedPack = nextSnapshot.packs.find((item) => item.id === selectedPack.id) ?? selectedPack;
        const refreshedCandidates = nextSnapshot.candidatesForPack(refreshedPack);
        const nextPendingCandidateId = refreshedCandidates.find(
          (candidate) => candidate.id !== selectedCandidate.id && candidate.status === "pending",
        )?.id;
        if (nextPendingCandidateId) {
          patchState({ selectedCandidateId: nextPendingCandidateId });
        }
      }
      setActionState(reviewDecision === "accepted" ? "已接受并保存" : reviewDecision === "rejected" ? "已拒绝并保存" : "已保存为待定");
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : String(caught));
      setActionState("");
    }
  };

  const leftPane = (
    <div className="stack-panels">
      <Panel title="审阅包" meta={`工作区 ${data?.workspaceId ?? state.workspace}`} compact>
        {loading && !data ? (
          <div className="empty-state">加载中...</div>
        ) : error ? (
          <div className="empty-state">加载失败：{error}</div>
        ) : (
          <div className="tree-list">
            {filteredPacks.map((pack) => (
              <button
                key={pack.id}
                className={`tree-item ${pack.id === state.selectedPackId ? "is-active" : ""}`}
                onClick={() => patchState({ selectedPackId: pack.id })}
                type="button"
              >
                <span>
                  <strong>{pack.name}</strong>
                  <small>
                    {domainLabels[pack.domainId]} · {pack.equipmentClassLabel || pack.equipmentClass}
                    {pack.pendingCount !== undefined ? ` · 待处理 ${pack.pendingCount}` : ""}
                  </small>
                </span>
                <StatusBadge label={packStatusLabels[pack.status]} tone={packTone(pack.status)} />
              </button>
            ))}
          </div>
        )}
      </Panel>
      <Panel title="候选列表" meta={`当前候选 ${formatCount(candidates.length)} 条`}>
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
              { key: "type", label: "类型", render: (row) => knowledgeTypeLabels[row.type] },
              {
                key: "status",
                label: "状态",
                render: (row) => <StatusBadge label={reviewStatusLabels[row.status]} tone={reviewTone(row.status)} />,
              },
              { key: "page", label: "页码", render: (row) => row.pageNo },
              { key: "chunk", label: "Chunk", render: (row) => row.chunkId },
            ]}
            rows={candidates}
            rowKey={(row) => row.id}
            selectedKey={state.selectedCandidateId}
            onSelect={(row) => patchState({ selectedCandidateId: row.id })}
            emptyState="当前审阅包下没有候选项。"
          />
        )}
      </Panel>
    </div>
  );

  const rightPane = selectedCandidate ? (
    <Panel
      title="候选详情"
      meta={`${selectedCandidate.title} · ${selectedCandidate.canonicalKey}`}
      actions={
        <>
          <button className="secondary-button" onClick={() => void persistCandidate("pending")} type="button">
            标记待定
          </button>
          <button className="secondary-button" onClick={() => void persistCandidate("rejected")} type="button">
            拒绝
          </button>
          <button className="primary-button" onClick={() => void persistCandidate("accepted")} type="button">
            接受
          </button>
        </>
      }
    >
      <div className="detail-header">
        <div>
          <h2>{selectedCandidate.title}</h2>
          <p>{selectedCandidate.summary}</p>
          {actionState ? <p className="action-text">{actionState}</p> : null}
          {actionError ? <p className="action-text action-error">{actionError}</p> : null}
        </div>
        <StatusBadge label={reviewStatusLabels[selectedCandidate.status]} tone={reviewTone(selectedCandidate.status)} />
      </div>
      <Tabs
        activeTab={state.tab}
        onChange={(tab) => patchState({ tab })}
        tabs={[
          {
            id: "editor",
            label: "编辑",
            content: (
              <form className="editor-form">
                <label>
                  <span>标题</span>
                  <input
                    value={formState.title}
                    onChange={(event) => setFormState((current) => ({ ...current, title: event.target.value }))}
                  />
                </label>
                <label>
                  <span>标准键值</span>
                  <input
                    value={formState.canonicalKey}
                    onChange={(event) => setFormState((current) => ({ ...current, canonicalKey: event.target.value }))}
                  />
                </label>
                <label>
                  <span>摘要</span>
                  <textarea
                    rows={4}
                    value={formState.summary}
                    onChange={(event) => setFormState((current) => ({ ...current, summary: event.target.value }))}
                  />
                </label>
                <label>
                  <span>可信等级</span>
                  <input
                    value={formState.trustLevel}
                    onChange={(event) => setFormState((current) => ({ ...current, trustLevel: event.target.value }))}
                  />
                </label>
                <label>
                  <span>结构化内容</span>
                  <textarea
                    rows={8}
                    value={formState.payload}
                    onChange={(event) => setFormState((current) => ({ ...current, payload: event.target.value }))}
                  />
                </label>
              </form>
            ),
          },
          {
            id: "evidence",
            label: "证据",
            content: (
              <article className="evidence-card">
                <div className="evidence-meta">
                  <span>{selectedCandidate.sourceDocument}</span>
                  <span>第 {selectedCandidate.pageNo} 页</span>
                  <span>{selectedCandidate.chunkId}</span>
                </div>
                <p className="quote-line">{selectedCandidate.evidence.excerpt}</p>
                <pre>{selectedCandidate.evidence.evidenceText}</pre>
              </article>
            ),
          },
          {
            id: "payload",
            label: "结构化内容",
            content: (
              <div className="code-card">
                <pre>{selectedCandidate.payload}</pre>
              </div>
            ),
          },
          {
            id: "source",
            label: "来源关联",
            content: (
              <div className="stack-section">
                <article className="link-card">
                  <span>来源文档</span>
                  <strong>{selectedCandidate.sourceDocument}</strong>
                </article>
                <article className="link-card">
                  <span>所属审阅包</span>
                  <strong>{selectedPack?.name ?? "-"}</strong>
                </article>
              </div>
            ),
          },
        ]}
      />
    </Panel>
  ) : (
    <Panel title="候选详情" meta="未选择对象">
      <div className="empty-state">先选择一个审阅包和候选项。</div>
    </Panel>
  );

  return (
    <MasterDetailPage
      title="审阅中心"
      split="minmax(430px, 46%) minmax(520px, 54%)"
      actions={
        <>
          <button className="secondary-button" onClick={() => void refresh()} type="button">
            刷新
          </button>
          <button
            className="secondary-button"
            onClick={async () => {
              if (!selectedPack) {
                return;
              }
              try {
                setActionError("");
                setActionState("补全草稿中...");
                await bootstrapReviewPack(selectedPack.id, selectedPack.workspaceId);
                await refresh();
                setActionState("草稿补全完成");
              } catch (caught) {
                setActionError(caught instanceof Error ? caught.message : String(caught));
                setActionState("");
              }
            }}
            type="button"
          >
            补全草稿
          </button>
          <button className="primary-button" onClick={() => void persistCandidate("pending")} type="button">
            保存变更
          </button>
        </>
      }
      filters={
        <>
          <select value={data?.workspaceId ?? state.workspace} disabled>
            <option>{data?.workspaceId ?? state.workspace}</option>
          </select>
          <select value={state.domain} onChange={(event) => patchState({ domain: event.target.value })}>
            <option value="all">全部领域</option>
            <option value="hvac">暖通空调</option>
            <option value="drive">变频驱动</option>
          </select>
          <select value={state.status} onChange={(event) => patchState({ status: event.target.value })}>
            <option value="all">全部包状态</option>
            <option value="pending">待处理</option>
            <option value="ready">已就绪</option>
            <option value="blocked">被阻塞</option>
          </select>
          <input
            placeholder="搜索审阅包或设备类"
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
