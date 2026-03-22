const state = {
  payload: null,
  activeView: "inbox",
  selectedDocumentId: null,
  activeWorkspaceId: null,
  reviewWorkspace: null,
  applyWorkspace: null,
  selectedPackFile: null,
  selectedCandidateIndex: 0,
  saving: false,
  applying: false,
  preparing: false,
  importing: false,
  processingDocId: null,
  notification: null,
  filters: {
    documents: { domain: "all", query: "" },
    review: { status: "all", query: "" },
    coverage: { domain: "all", status: "all" },
  },
};

const COMMAND_SHORTCUTS = [
  {
    label: "准备审阅包",
    command: "python3 scripts/prepare_review_pipeline_bundle.py <domain> review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id>",
    purpose: "从已有 Chunk 直接准备可审阅包。",
  },
  {
    label: "应用就绪审阅包",
    command: "python3 scripts/apply_ready_review_bundle.py review_bundle",
    purpose: "批量应用已完成审阅的审阅包。",
  },
  {
    label: "质量门检查",
    command: "bash scripts/check-all",
    purpose: "在结束会话前跑绑定质量门。",
  },
];

const DOMAIN_LABELS = {
  hvac: "暖通空调",
  drive: "变频驱动",
};

const KNOWLEDGE_OBJECT_LABELS = {
  application_guidance: "应用指导",
  commissioning_step: "调试步骤",
  diagnostic_step: "诊断步骤",
  fault_code: "故障代码",
  maintenance_procedure: "维护流程",
  parameter_spec: "参数规范",
  performance_spec: "性能规范",
  symptom: "症状",
  wiring_guidance: "接线指导",
};

const PRIORITY_RATIONALES = {
  motor_controller: "该设备类已在本体中定义，但当前策展覆盖仍为空白，内部控制柜排障链路因此缺了一块。",
  soft_starter: "软启动器已经有可用基线，下一步应补齐启动过程与接线指导，形成更完整的现场使用面。",
  frequency_converter: "变频转换器已有启动基线，下一步应补充接线、维护与应用指导，支撑现场部署工作。",
  air_cooled_modular_heat_pump: "这个设备类已经具备故障与维护基础，再补运行边界和症状覆盖，就能形成第一个内部可用的闭环排障切片。",
  ahu: "AHU 已有较好的权威型指导内容，但内部工程侧仍缺直接的参数查询与故障检索能力。",
  centrifugal_chiller: "离心式冷水机组是明确的品牌重点方向，比继续扩展仅用于演示的冷站指标更值得优先投入。",
};

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload.data;
}

async function loadWorkbench() {
  return fetchJson("/api/workbench");
}

async function loadReviewWorkspace() {
  const params = new URLSearchParams();
  if (state.activeWorkspaceId) {
    params.set("workspace_id", state.activeWorkspaceId);
  }
  return fetchJson(`/api/workbench/review-packs${params.toString() ? `?${params.toString()}` : ""}`);
}

async function loadReviewPack(packFile) {
  const params = new URLSearchParams();
  if (state.activeWorkspaceId) {
    params.set("workspace_id", state.activeWorkspaceId);
  }
  return fetchJson(`/api/workbench/review-packs/${encodeURIComponent(packFile)}${params.toString() ? `?${params.toString()}` : ""}`);
}

async function bootstrapReviewPack(packFile) {
  const params = new URLSearchParams();
  if (state.activeWorkspaceId) {
    params.set("workspace_id", state.activeWorkspaceId);
  }
  return fetchJson(`/api/workbench/review-packs/${encodeURIComponent(packFile)}/bootstrap${params.toString() ? `?${params.toString()}` : ""}`, {
    method: "POST",
  });
}

async function saveReviewPack(packFile, payload) {
  const params = new URLSearchParams();
  if (state.activeWorkspaceId) {
    params.set("workspace_id", state.activeWorkspaceId);
  }
  return fetchJson(`/api/workbench/review-packs/${encodeURIComponent(packFile)}${params.toString() ? `?${params.toString()}` : ""}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, workspace_id: state.activeWorkspaceId }),
  });
}

async function loadApplyWorkspace() {
  const params = new URLSearchParams();
  if (state.activeWorkspaceId) {
    params.set("workspace_id", state.activeWorkspaceId);
  }
  return fetchJson(`/api/workbench/apply${params.toString() ? `?${params.toString()}` : ""}`);
}

async function prepareReviewBundle(payload) {
  return fetchJson("/api/workbench/review-bundle/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, workspace_id: state.activeWorkspaceId }),
  });
}

async function runApplyReady() {
  return fetchJson("/api/workbench/apply/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_id: state.activeWorkspaceId }),
  });
}

async function importDocument(formData) {
  const response = await fetch("/api/workbench/documents/import", {
    method: "POST",
    body: formData,
  });
  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.detail || "导入失败");
  }
  return payload.data;
}

async function parseDocument(docId) {
  return fetchJson(`/api/workbench/documents/${encodeURIComponent(docId)}/parse`, { method: "POST" });
}

async function chunkDocument(docId) {
  return fetchJson(`/api/workbench/documents/${encodeURIComponent(docId)}/chunk`, { method: "POST" });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function domainLabel(value) {
  return DOMAIN_LABELS[value] || value || "未指定";
}

function knowledgeLabel(value) {
  return KNOWLEDGE_OBJECT_LABELS[value] || value || "未指定";
}

function knowledgeInline(values) {
  if (!values || !values.length) {
    return "无";
  }
  return values.map((item) => knowledgeLabel(item)).join("、");
}

function priorityRationale(item) {
  return PRIORITY_RATIONALES[item.equipment_class_id] || item.rationale || "请补充该设备类的优先处理说明。";
}

function statusLabel(value) {
  const labels = {
    covered: "已覆盖",
    partial: "部分覆盖",
    uncovered: "未覆盖",
    passed: "通过",
    failed: "失败",
    success: "成功",
    error: "错误",
    ready: "已就绪",
    completed: "已完成",
    pending: "待处理",
    accepted: "已接受",
    rejected: "已拒绝",
    blocked_pending: "待审阅",
    blocked_no_accepted: "无已接受项",
    review_complete: "审阅完成",
  };
  return labels[value] || value || "未知";
}

function joinInline(values) {
  if (!values || !values.length) {
    return "无";
  }
  return values.join(", ");
}

function codeBlock(value) {
  return `<code class="block-code">${escapeHtml(value)}</code>`;
}

function notify(type, message) {
  state.notification = { type, message };
  renderNotification();
  window.clearTimeout(notify.timeoutId);
  notify.timeoutId = window.setTimeout(() => {
    state.notification = null;
    renderNotification();
  }, 3200);
}

function renderNotification() {
  const node = document.getElementById("toast-region");
  if (!state.notification) {
    node.innerHTML = "";
    return;
  }
  node.innerHTML = `
    <div class="toast toast-${escapeHtml(state.notification.type)}">
      <strong>${escapeHtml(statusLabel(state.notification.type))}</strong>
      <span>${escapeHtml(state.notification.message)}</span>
    </div>
  `;
}

function renderSummaryStrip(summary) {
  const node = document.getElementById("summary-strip");
  const items = [
    ["领域数量", summary.domain_count],
    ["文档数量", summary.document_count],
    ["已覆盖类", summary.covered_equipment_classes],
    ["重点缺口", summary.priority_target_count],
  ];
  node.innerHTML = items
    .map(
      ([label, value]) => `
        <article class="summary-pill">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `,
    )
    .join("");
}

function renderNavigation(navigation) {
  const node = document.getElementById("nav-list");
  node.innerHTML = navigation
    .map(
      (item) => `
        <button class="nav-item ${item.id === state.activeView ? "is-active" : ""}" data-view="${escapeHtml(item.id)}">
          <span class="nav-label">${escapeHtml(item.label)}</span>
          <span class="nav-description">${escapeHtml(item.description)}</span>
        </button>
      `,
    )
    .join("");
  node.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.activeView = button.dataset.view;
      if (state.activeView === "review" && !state.reviewWorkspace) {
        await refreshReviewWorkspace();
      }
      renderApp();
    });
  });
}

function filterBar({ searchId, searchValue, searchPlaceholder, selectId, selectValue, selectOptions, secondarySelectId, secondarySelectValue, secondarySelectOptions }) {
  const search = searchId
    ? `
      <input id="${escapeHtml(searchId)}" class="filter-input" value="${escapeHtml(searchValue)}" placeholder="${escapeHtml(searchPlaceholder)}" />
    `
    : "";
  const primary = selectId
    ? `
      <select id="${escapeHtml(selectId)}" class="filter-select">
        ${selectOptions
          .map((item) => `<option value="${escapeHtml(item.value)}" ${item.value === selectValue ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
          .join("")}
      </select>
    `
    : "";
  const secondary = secondarySelectId
    ? `
      <select id="${escapeHtml(secondarySelectId)}" class="filter-select">
        ${secondarySelectOptions
          .map((item) => `<option value="${escapeHtml(item.value)}" ${item.value === secondarySelectValue ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
          .join("")}
      </select>
    `
    : "";
  return `
    <div class="filter-bar">
      ${search}
      ${primary}
      ${secondary}
    </div>
  `;
}

function workspaceOptions(workspaceItems) {
  return [
    { value: "", label: "最新工作区" },
    ...(workspaceItems || []).map((item) => ({
      value: item.workspace_id,
      label: item.workspace_id,
    })),
  ];
}

function documentPrepareCommand(documentItem) {
  const domain = documentItem.source_domain;
  const equipment = documentItem.equipment_classes[0] || "<equipment_class_id>";
  return `python3 scripts/prepare_review_pipeline_bundle.py ${domain} review_bundle --doc-id ${documentItem.doc_id} --equipment-class-id ${equipment}`;
}

function filteredDocuments(view) {
  return (view.documents || []).filter((item) => {
    const domainOk = state.filters.documents.domain === "all" || item.source_domain === state.filters.documents.domain;
    const query = state.filters.documents.query.trim().toLowerCase();
    const haystack = [item.file_name, item.doc_id, item.source_domain, ...item.equipment_classes, ...item.knowledge_types]
      .join(" ")
      .toLowerCase();
    const queryOk = !query || haystack.includes(query);
    return domainOk && queryOk;
  });
}

function documentListView(view) {
  const documents = filteredDocuments(view);
  const selected = documents.find((item) => item.doc_id === state.selectedDocumentId) || documents[0] || null;
  if (selected) {
    state.selectedDocumentId = selected.doc_id;
  }
  const rows = documents
    .map(
      (item) => `
        <button class="list-row ${item.doc_id === state.selectedDocumentId ? "is-active" : ""}" data-doc-id="${escapeHtml(item.doc_id)}">
          <strong>${escapeHtml(item.file_name)}</strong>
          <span>${escapeHtml(domainLabel(item.source_domain))} · ${escapeHtml(joinInline(item.equipment_classes))}</span>
        </button>
      `,
    )
    .join("");
  const detail = selected
    ? `
      <article class="surface-card detail-card">
        <p class="surface-kicker">当前文档</p>
        <h4>${escapeHtml(selected.file_name)}</h4>
        <div class="detail-grid">
          <div><span class="detail-label">文档 ID</span>${codeBlock(selected.doc_id)}</div>
          <div><span class="detail-label">领域</span><p>${escapeHtml(domainLabel(selected.source_domain))}</p></div>
          <div><span class="detail-label">设备类</span><p>${escapeHtml(joinInline(selected.equipment_classes))}</p></div>
          <div><span class="detail-label">解析状态</span><p>${escapeHtml(statusLabel(selected.parse_status || "unknown"))}</p></div>
          <div><span class="detail-label">知识对象类型</span><p>${escapeHtml(knowledgeInline(selected.knowledge_types))}</p></div>
          <div><span class="detail-label">页数</span><p>${escapeHtml(selected.page_count || joinInline(selected.page_refs))}</p></div>
          <div><span class="detail-label">Chunk 数</span><p>${escapeHtml(selected.chunk_count ?? selected.entry_count ?? "-")}</p></div>
          <div><span class="detail-label">样例路径</span><p>${escapeHtml(joinInline(selected.fixture_paths))}</p></div>
        </div>
        <div class="action-panel">
          <p class="action-title">文档操作</p>
          ${
            selected.actionable
              ? `
                <div class="toolbar-actions">
                  <button id="parse-document-button" class="secondary-button" ${state.processingDocId === selected.doc_id ? "disabled" : ""}>解析文档</button>
                  <button id="chunk-document-button" class="secondary-button" ${state.processingDocId === selected.doc_id || selected.parse_status !== "completed" ? "disabled" : ""}>生成 Chunk</button>
                  <button id="prepare-bundle-button" class="primary-button" ${state.preparing || !selected.source_domain ? "disabled" : ""}>
                    ${state.preparing ? "准备中…" : "准备审阅包"}
                  </button>
                </div>
                ${codeBlock(documentPrepareCommand(selected))}
              `
              : `<p class="surface-copy">样例文档仅供参考。上传真实 PDF 后，才能生成可执行的文档对象。</p>`
          }
        </div>
      </article>
    `
    : `
      <article class="surface-card empty-card">
        <p class="surface-kicker">文档</p>
        <h4>当前筛选条件下没有可执行文档</h4>
        <p class="surface-copy">请连接真实数据库语料或调整筛选条件。下方仍保留样例文档供参考。</p>
      </article>
    `;
  const samples = (view.fixture_samples || [])
    .slice(0, 6)
    .map(
      (item) => `
        <div class="sample-row">
          <strong>${escapeHtml(item.file_name)}</strong>
          <span>${escapeHtml(domainLabel(item.source_domain))} · 仅样例 · ${escapeHtml(joinInline(item.equipment_classes))}</span>
        </div>
      `,
    )
    .join("");
  return `
    <section class="split-grid review-grid">
      <article class="surface-card list-card">
        <p class="surface-kicker">文档语料</p>
        <h4>实际文档</h4>
        <form id="document-import-form" class="editor-form compact-form">
          <label>
            <span class="detail-label">导入 PDF</span>
            <input type="file" name="file" accept="application/pdf,.pdf" />
          </label>
          <label>
            <span class="detail-label">领域</span>
            <select name="source_domain">
              <option value="">未指定</option>
              <option value="hvac">暖通空调</option>
              <option value="drive">变频驱动</option>
            </select>
          </label>
          <div class="editor-actions">
            <button id="import-document-button" type="submit" class="primary-button" ${state.importing ? "disabled" : ""}>
              ${state.importing ? "导入中…" : "导入 PDF"}
            </button>
          </div>
        </form>
        <p class="meta-note">${view.db_available ? "已连接数据库语料。" : "数据库不可用，仅展示样例文档。"}</p>
        ${filterBar({
          searchId: "documents-query",
          searchValue: state.filters.documents.query,
          searchPlaceholder: "搜索文档、doc_id、设备类…",
          selectId: "documents-domain",
          selectValue: state.filters.documents.domain,
          selectOptions: [
            { value: "all", label: "全部领域" },
            ...[...new Set((view.documents || []).map((item) => item.source_domain).filter(Boolean))].sort().map((value) => ({ value, label: domainLabel(value) })),
          ],
        })}
        <div class="list-column">${rows}</div>
        <div class="sample-panel">
          <p class="surface-kicker">样例文档</p>
          <div class="list-column compact-list">${samples || "<span class=\"meta-note\">暂无样例文档。</span>"}</div>
        </div>
      </article>
      ${detail}
    </section>
  `;
}

function inboxView(view) {
  const cards = view.cards
    .map(
      (item) => `
        <article class="task-row">
          <div class="task-row-main">
            <p class="task-domain">${escapeHtml(domainLabel(item.domain_id))}</p>
            <h4>${escapeHtml(item.equipment_class_id)}</h4>
            <p class="surface-copy">${escapeHtml(priorityRationale(item))}</p>
          </div>
          <div class="task-row-side">
            <span class="task-label">下一批知识对象</span>
            <div class="tag-row">${item.target_knowledge_objects
              .map((value) => `<span class="tag">${escapeHtml(knowledgeLabel(value))}</span>`)
              .join("")}</div>
          </div>
        </article>
      `,
    )
    .join("");
  const rules = view.rules.map((rule) => `<li>${escapeHtml(rule)}</li>`).join("");
  return `
    <section class="split-grid">
      <article class="surface-card">
        <p class="surface-kicker">优先队列</p>
        <h4>今日最高杠杆任务</h4>
        <div class="task-list">${cards}</div>
      </article>
      <article class="surface-card note-card">
        <p class="surface-kicker">操作规则</p>
        <h4>当前优化原则</h4>
        <ul class="rule-list">${rules}</ul>
      </article>
    </section>
  `;
}

function filteredPacks(workspace) {
  return workspace.packs.filter((item) => {
    const statusOk = state.filters.review.status === "all" || item.status === state.filters.review.status;
    const query = state.filters.review.query.trim().toLowerCase();
    const haystack = [item.doc_name, item.doc_id, item.equipment_class_id, item.domain_id, item.pack_file].join(" ").toLowerCase();
    const queryOk = !query || haystack.includes(query);
    return statusOk && queryOk;
  });
}

function reviewWorkspaceView(view) {
  const workspace = state.reviewWorkspace || view.workspace;
  if (!workspace || !workspace.available || !workspace.packs.length) {
    return `
      <section class="split-grid review-grid">
        <article class="surface-card empty-card">
          <p class="surface-kicker">审阅包</p>
          <h4>未找到审阅包</h4>
          <p class="surface-copy">请先设置 <code>WORKBENCH_REVIEW_DIR</code>，或先生成审阅包，再回到这里做本地审阅与保存。</p>
          ${codeBlock(COMMAND_SHORTCUTS[0].command)}
        </article>
        <article class="surface-card">
          <p class="surface-kicker">工作流</p>
          <h4>审阅路径</h4>
          <ol class="timeline-list">${view.workflow_steps
            .map(
              (step, index) => `
                <li class="timeline-item">
                  <span class="timeline-index">${index + 1}</span>
                  <p>${escapeHtml(step)}</p>
                </li>
              `,
            )
            .join("")}</ol>
        </article>
      </section>
    `;
  }
  const packs = filteredPacks(workspace);
  const selectedPack = packs.find((item) => item.pack_file === state.selectedPackFile) || packs[0] || null;
  if (selectedPack) {
    state.selectedPackFile = selectedPack.pack_file;
  }
  const packDetail = selectedPack ? workspace.packDetails?.[selectedPack.pack_file] || null : null;
  const selectedCandidate = packDetail?.candidate_entries?.[state.selectedCandidateIndex] || null;
  const packRows = packs
    .map(
      (item) => `
        <button class="list-row ${item.pack_file === state.selectedPackFile ? "is-active" : ""}" data-pack-file="${escapeHtml(item.pack_file)}">
          <strong>${escapeHtml(item.doc_name || item.pack_file)}</strong>
          <span>${escapeHtml(item.equipment_class_id)} · ${escapeHtml(statusLabel(item.status))}</span>
        </button>
      `,
    )
    .join("");
  const candidateRows = (packDetail?.candidate_entries || [])
    .map(
      (item, index) => `
        <button class="candidate-row ${index === state.selectedCandidateIndex ? "is-active" : ""}" data-candidate-index="${index}">
          <strong>${escapeHtml(item.canonical_key_candidate)}</strong>
          <span>${escapeHtml(item.knowledge_object_type)} · ${escapeHtml(item.review_decision || "pending")}</span>
        </button>
      `,
    )
    .join("");
  const detail = selectedCandidate
    ? `
      <article class="surface-card detail-card">
        <p class="surface-kicker">候选项详情</p>
        <h4>${escapeHtml(selectedCandidate.canonical_key_candidate)}</h4>
        <div class="toolbar-row">
          <button id="bootstrap-pack-button" class="secondary-button">补全当前审阅包草稿</button>
          <span class="meta-note">${escapeHtml(selectedPack.pack_file)}</span>
        </div>
        <form id="review-form" class="editor-form">
          <label>
            <span class="detail-label">审阅决定</span>
            <select name="review_decision">
              ${["pending", "accepted", "rejected"]
                .map(
                  (value) => `<option value="${value}" ${value === (selectedCandidate.review_decision || "pending") ? "selected" : ""}>${statusLabel(value)}</option>`,
                )
                .join("")}
            </select>
          </label>
          <label>
            <span class="detail-label">标题</span>
            <input name="title" value="${escapeHtml(selectedCandidate.curation?.title || "")}" />
          </label>
          <label>
            <span class="detail-label">摘要</span>
            <textarea name="summary" rows="4">${escapeHtml(selectedCandidate.curation?.summary || "")}</textarea>
          </label>
          <label>
            <span class="detail-label">结构化载荷</span>
            <textarea name="structured_payload" rows="8">${escapeHtml(JSON.stringify(selectedCandidate.curation?.structured_payload || {}, null, 2))}</textarea>
          </label>
          <label>
            <span class="detail-label">适用范围</span>
            <textarea name="applicability" rows="5">${escapeHtml(JSON.stringify(selectedCandidate.curation?.applicability || {}, null, 2))}</textarea>
          </label>
          <div class="editor-actions">
            <button type="submit" class="primary-button" ${state.saving ? "disabled" : ""}>${state.saving ? "保存中…" : "保存候选项"}</button>
          </div>
        </form>
      </article>
      <article class="surface-card evidence-card">
        <p class="surface-kicker">证据</p>
        <h4>${escapeHtml(selectedCandidate.doc_name)}</h4>
        <div class="detail-grid">
          <div><span class="detail-label">Chunk</span>${codeBlock(selectedCandidate.chunk_id)}</div>
          <div><span class="detail-label">页码</span><p>${escapeHtml(selectedCandidate.page_no)}</p></div>
          <div><span class="detail-label">类型</span><p>${escapeHtml(selectedCandidate.knowledge_object_type)}</p></div>
          <div><span class="detail-label">设备类</span><p>${escapeHtml(selectedCandidate.equipment_class_candidate?.equipment_class_id || "")}</p></div>
        </div>
        <div class="evidence-block">
          <span class="detail-label">摘录片段</span>
          <p>${escapeHtml(selectedCandidate.text_excerpt || "")}</p>
        </div>
        <div class="evidence-block">
          <span class="detail-label">证据原文</span>
          <pre>${escapeHtml(selectedCandidate.evidence_text || "")}</pre>
        </div>
      </article>
    `
    : `
      <article class="surface-card empty-card">
        <p class="surface-kicker">候选项详情</p>
        <h4>先选择一个候选项</h4>
        <p class="surface-copy">请先从候选项列表中选择一个条目，再开始编辑审阅字段。</p>
      </article>
    `;
  return `
    <section class="review-shell">
      <article class="surface-card list-card">
        <p class="surface-kicker">审阅包</p>
        <h4>审阅包目录</h4>
        <div class="meta-note">${escapeHtml(workspace.resolved_dir)}</div>
        ${filterBar({
          searchId: "review-query",
          searchValue: state.filters.review.query,
          searchPlaceholder: "搜索审阅包、文档、设备类…",
          selectId: "review-status",
          selectValue: state.filters.review.status,
          selectOptions: [
            { value: "all", label: "全部状态" },
            { value: "blocked_pending", label: "待审阅" },
            { value: "blocked_no_accepted", label: "无已接受项" },
            { value: "review_complete", label: "审阅完成" },
          ],
          secondarySelectId: "review-workspace",
          secondarySelectValue: state.activeWorkspaceId || "",
          secondarySelectOptions: workspaceOptions(workspace.workspaces),
        })}
        <div class="list-column">${packRows}</div>
      </article>
      <article class="surface-card list-card">
        <p class="surface-kicker">候选项</p>
        <h4>${escapeHtml(selectedPack?.doc_name || "尚未选择审阅包")}</h4>
        <div class="meta-note">${escapeHtml(selectedPack ? `${selectedPack.equipment_class_id} · ${statusLabel(selectedPack.status)}` : "请先调整筛选条件并选择一个审阅包")}</div>
        <div class="list-column">${candidateRows}</div>
      </article>
      <div class="stack-grid">${detail}</div>
    </section>
  `;
}

function applyView(view) {
  const workspace = state.applyWorkspace || view.workspace;
  const rules = view.rules.map((rule) => `<li>${escapeHtml(rule)}</li>`).join("");
  const watch = view.coverage_watch
    .map(
      (item) => `
        <article class="surface-card mini-stat-card">
          <p class="surface-kicker">${escapeHtml(item.domain_id)}</p>
          <h4>${escapeHtml(item.domain_name)}</h4>
          <p class="surface-copy">已覆盖 ${item.covered_equipment_classes}，未覆盖 ${item.uncovered_equipment_classes}</p>
        </article>
      `,
    )
    .join("");
  const readinessRows = workspace?.results?.length
    ? workspace.results
        .map(
          (item) => `
            <tr>
              <td><strong>${escapeHtml(item.doc_name || item.pack_file)}</strong><div class="table-subtle">${escapeHtml(item.pack_file)}</div></td>
              <td>${escapeHtml(item.equipment_class_id || "-")}</td>
              <td><span class="status-chip status-${escapeHtml(item.status === "ready" ? "covered" : "partial")}">${escapeHtml(statusLabel(item.status))}</span></td>
              <td>${escapeHtml(item.accepted_count ?? 0)}</td>
              <td>${escapeHtml(item.pending_count ?? 0)}</td>
            </tr>
          `,
        )
        .join("")
    : `
        <tr>
          <td colspan="5">暂无准备度数据。</td>
        </tr>
      `;
  const latestApply = workspace?.latest_apply;
  const latestApplyCard = latestApply
    ? `
      <article class="surface-card">
        <p class="surface-kicker">最近一次应用</p>
        <h4>${escapeHtml(`已应用 ${latestApply.summary?.applied ?? 0} · 失败 ${latestApply.summary?.failed ?? 0}`)}</h4>
        <p class="surface-copy">生成时间 ${escapeHtml(formatDateTime(latestApply.generated_at || "-"))}</p>
        ${
          latestApply.summary_text
            ? `<div class="evidence-block"><span class="detail-label">摘要文本</span><pre>${escapeHtml(latestApply.summary_text)}</pre></div>`
            : ""
        }
        ${
          latestApply.paths
            ? `<div class="detail-grid">
                <div><span class="detail-label">应用报告</span>${codeBlock(latestApply.paths.apply_report || "-")}</div>
                <div><span class="detail-label">统计</span>${codeBlock(latestApply.paths.stats || "-")}</div>
              </div>`
            : ""
        }
      </article>
    `
    : `
      <article class="surface-card">
        <p class="surface-kicker">最近一次应用</p>
        <h4>尚未执行应用</h4>
        <p class="surface-copy">至少有一个审阅包达到就绪状态后，再执行 apply-ready，这里才会出现统计与摘要产物。</p>
      </article>
    `;
  return `
    <section class="split-grid">
      <article class="surface-card">
        <p class="surface-kicker">应用规则</p>
        <h4>应用前必须成立</h4>
        <ul class="rule-list">${rules}</ul>
      </article>
      <div class="stack-grid">
        ${watch}
        <article class="surface-card table-card">
          <div class="toolbar-row">
            <div>
              <p class="surface-kicker">准备度</p>
              <h4>审阅包状态</h4>
            </div>
            <div class="toolbar-actions">
              <select id="apply-workspace" class="filter-select">
                ${workspaceOptions(workspace?.workspaces)
                  .map((item) => `<option value="${escapeHtml(item.value)}" ${item.value === (state.activeWorkspaceId || "") ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
                  .join("")}
              </select>
              <button id="refresh-apply-button" class="secondary-button">刷新准备度</button>
              <button id="run-apply-button" class="primary-button" ${state.applying || !workspace?.can_apply_bundle ? "disabled" : ""}>
                ${state.applying ? "应用中…" : "执行 Apply-Ready"}
              </button>
            </div>
          </div>
          <div class="meta-note">${escapeHtml(workspace?.resolved_dir || "尚未配置审阅包")}</div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>审阅包</th>
                  <th>设备类</th>
                  <th>状态</th>
                  <th>已接受</th>
                  <th>待处理</th>
                </tr>
              </thead>
              <tbody>${readinessRows}</tbody>
            </table>
          </div>
        </article>
        ${latestApplyCard}
      </div>
    </section>
  `;
}

function coverageDomainCard(domain) {
  const rows = domain.equipment_classes
    .map(
      (item) => `
        <tr>
          <td>
            <strong>${escapeHtml(item.label)}</strong>
            <div class="table-subtle">${escapeHtml(item.equipment_class_id)}</div>
          </td>
          <td><span class="status-chip status-${escapeHtml(item.coverage_status)}">${escapeHtml(statusLabel(item.coverage_status))}</span></td>
          <td>${escapeHtml(knowledgeInline(item.covered_knowledge_objects))}</td>
          <td>${escapeHtml(knowledgeInline(item.missing_knowledge_objects))}</td>
        </tr>
      `,
    )
    .join("");
  return `
    <article class="surface-card table-card">
      <p class="surface-kicker">${escapeHtml(domainLabel(domain.domain_id))}</p>
      <h4>${escapeHtml(domain.domain_name)}</h4>
      <p class="surface-copy">支持的知识对象：${escapeHtml(knowledgeInline(domain.supported_knowledge_objects))}</p>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>设备类</th>
              <th>状态</th>
              <th>已覆盖</th>
              <th>缺失</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </article>
  `;
}

function coverageView(view) {
  const filteredDomains = view.domains.filter((domain) => {
    const domainOk = state.filters.coverage.domain === "all" || domain.domain_id === state.filters.coverage.domain;
    return domainOk;
  });
  const cards = filteredDomains
    .map((domain) => {
      const filteredClasses = domain.equipment_classes.filter((item) => {
        const statusOk = state.filters.coverage.status === "all" || item.coverage_status === state.filters.coverage.status;
        return statusOk;
      });
      return coverageDomainCard({ ...domain, equipment_classes: filteredClasses });
    })
    .join("");
  return `
    <section class="stack-grid">
      ${filterBar({
        searchId: null,
        searchValue: "",
        searchPlaceholder: "",
        selectId: "coverage-domain",
        selectValue: state.filters.coverage.domain,
        selectOptions: [
          { value: "all", label: "全部领域" },
          ...view.domains.map((domain) => ({ value: domain.domain_id, label: domainLabel(domain.domain_id) })),
        ],
        secondarySelectId: "coverage-status",
        secondarySelectValue: state.filters.coverage.status,
        secondarySelectOptions: [
          { value: "all", label: "全部状态" },
          { value: "covered", label: "已覆盖" },
          { value: "partial", label: "部分覆盖" },
          { value: "uncovered", label: "未覆盖" },
        ],
      })}
      ${cards}
    </section>
  `;
}

function demoView(view) {
  if (!view.available) {
    return `
      <article class="surface-card empty-card">
        <p class="surface-kicker">演示包</p>
        <h4>未找到演示包</h4>
        <p class="surface-copy">如果希望这里展示演示与交付产物，请先执行评估流程。</p>
      </article>
    `;
  }
  const scenario = view.scenario || {};
  const links = Object.entries(view.paths || {})
    .filter(([, value]) => Boolean(value))
    .map(
      ([label, value]) => `<a class="artifact-link" href="${escapeHtml(value)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`,
    )
    .join("");
  return `
    <section class="split-grid">
      <article class="surface-card">
        <p class="surface-kicker">评估</p>
        <h4>${escapeHtml(scenario.title || "当前演示包")}</h4>
        <p class="surface-copy">${escapeHtml(scenario.subtitle || "基于证据链的演示概览。")}</p>
        <div class="artifact-row">${links}</div>
      </article>
      <article class="surface-card">
        <p class="surface-kicker">状态</p>
        <h4>${escapeHtml(statusLabel(view.overall_status))}</h4>
        <p class="surface-copy">生成时间 ${escapeHtml(formatDateTime(view.generated_at || "-"))}</p>
      </article>
    </section>
  `;
}

function renderView() {
  const views = state.payload.views;
  const viewMap = {
    inbox: {
      kicker: "今日优先级",
      title: "值班收件箱",
      description: "从最高杠杆的覆盖缺口开始，让下一步动作始终清楚可见。",
      body: inboxView(views.inbox),
      inspector: {
        title: "先补能闭环的缺口",
        summary: "优先处理能走通完整审阅到应用链路的设备类，而不是零散补点。",
        list: views.inbox.rules,
        command: COMMAND_SHORTCUTS[0],
      },
    },
    documents: {
      kicker: "文档录入",
      title: "文档录入工作面",
      description: "选中文档、查看当前语义状态，并直接准备下一步审阅命令。",
      body: documentListView(views.documents),
      inspector: {
        title: "文档必须通向动作",
        summary: "文档面板应该明确告诉操作者：它服务哪个设备类，以及下一条推进到审阅的命令是什么。",
        list: [
          "源文件、领域、设备类和页数要同时可见。",
          "审阅命令必须来自当前文档，而不是通用占位符。",
          "不要向操作者隐藏样例或样例路径。",
        ],
        command: COMMAND_SHORTCUTS[0],
      },
    },
    review: {
      kicker: "候选审阅",
      title: "候选项审阅工作面",
      description: "打开本地审阅包，编辑审阅字段，按需补全草稿并本地保存。",
      body: reviewWorkspaceView(views.review),
      inspector: {
        title: "先在本地完成审阅",
        summary: "最有价值的通用路径，是在证据旁直接编辑本地审阅包，而不是堆一个庞大的流程引擎。",
        list: [
          "编辑时审阅包列表必须始终可见。",
          "证据必须紧邻审阅字段展示。",
          "保存动作必须直接回写本地审阅包文件。",
        ],
        command: COMMAND_SHORTCUTS[1],
      },
    },
    apply: {
      kicker: "应用执行",
      title: "准备度与应用控制",
      description: "让已就绪审阅包清晰可见、阻塞原因明确、应用动作保持克制。",
      body: applyView(views.apply),
      inspector: {
        title: "只应用真正就绪的内容",
        summary: "工作台应该先把准备度讲清楚，再让 apply 变得容易，并在执行后交代清楚结果。",
        list: views.apply.rules,
        command: COMMAND_SHORTCUTS[1],
      },
    },
    coverage: {
      kicker: "覆盖盘点",
      title: "覆盖盘点",
      description: "跟踪各领域设备类的已覆盖、部分覆盖与薄弱空白。",
      body: coverageView(views.coverage),
      inspector: {
        title: "薄弱覆盖必须一眼可见",
        summary: "覆盖视图应该优先暴露缺失的知识对象类型，避免规划重新退回到拍脑袋。",
        list: [
          "同时展示支持项、已覆盖项和缺失项。",
          "重点目标必须绑定到本体设备类。",
          "以领域库存为规划真相源，而不是口头记忆。",
        ],
        command: COMMAND_SHORTCUTS[2],
      },
    },
    demo: {
      kicker: "演示交付",
      title: "评估与交付",
      description: "演示产物仍然重要，但它应该服务内部工作流，而不是替代它。",
      body: demoView(views.demo),
      inspector: {
        title: "演示只是一个工作面",
        summary: "用演示包验证交付和说明进展，但内部工作台流程必须始终是主线。",
        list: [
          "保留基于证据链的输出。",
          "演示路由应保持只读。",
          "不要让评估界面替代录入或审阅工具。",
        ],
        command: COMMAND_SHORTCUTS[2],
      },
    },
  };
  return viewMap[state.activeView];
}

function renderInspector(inspector) {
  setText("inspector-title", inspector.title);
  setText("inspector-summary", inspector.summary);
  document.getElementById("inspector-list").innerHTML = inspector.list
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  document.getElementById("inspector-command").innerHTML = `
    <p class="command-label">${escapeHtml(inspector.command.label)}</p>
    <code>${escapeHtml(inspector.command.command)}</code>
    <p class="command-copy">${escapeHtml(inspector.command.purpose)}</p>
  `;
}

async function refreshReviewWorkspace(selectedPackFile = state.selectedPackFile) {
  const workspace = await loadReviewWorkspace();
  state.reviewWorkspace = workspace;
  state.activeWorkspaceId = workspace.workspace_id || state.activeWorkspaceId;
  if (!workspace.available || !workspace.packs.length) {
    state.selectedPackFile = null;
    state.selectedCandidateIndex = 0;
    return;
  }
  const filtered = filteredPacks(workspace);
  const targetPack = selectedPackFile || filtered[0]?.pack_file || workspace.packs[0].pack_file;
  const packDetail = await loadReviewPack(targetPack);
  workspace.packDetails = { [targetPack]: packDetail };
  state.selectedPackFile = targetPack;
  state.selectedCandidateIndex = 0;
}

async function refreshApplyWorkspace() {
  state.applyWorkspace = await loadApplyWorkspace();
  state.activeWorkspaceId = state.applyWorkspace.workspace_id || state.activeWorkspaceId;
}

function attachDocumentHandlers() {
  const importForm = document.getElementById("document-import-form");
  if (importForm) {
    importForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(importForm);
      const file = formData.get("file");
      if (!(file instanceof File) || file.size === 0) {
        notify("error", "请先选择一个 PDF 再导入");
        return;
      }
      state.importing = true;
      renderApp();
      try {
        const document = await importDocument(formData);
        state.payload = await loadWorkbench();
        state.selectedDocumentId = document.doc_id;
        notify("success", `已导入 ${document.file_name}`);
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      } finally {
        state.importing = false;
        renderApp();
      }
    });
  }
  document.querySelectorAll("[data-doc-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedDocumentId = button.dataset.docId;
      renderApp();
    });
  });
  const queryInput = document.getElementById("documents-query");
  if (queryInput) {
    queryInput.addEventListener("input", () => {
      state.filters.documents.query = queryInput.value;
      renderApp();
    });
  }
  const domainSelect = document.getElementById("documents-domain");
  if (domainSelect) {
    domainSelect.addEventListener("change", () => {
      state.filters.documents.domain = domainSelect.value;
      renderApp();
    });
  }
  const parseButton = document.getElementById("parse-document-button");
  const documentItem = state.payload?.views?.documents?.documents?.find((item) => item.doc_id === state.selectedDocumentId);
  if (parseButton && documentItem?.actionable) {
    parseButton.addEventListener("click", async () => {
      state.processingDocId = documentItem.doc_id;
      renderApp();
      try {
        await parseDocument(documentItem.doc_id);
        state.payload = await loadWorkbench();
        notify("success", `已解析 ${documentItem.file_name}`);
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      } finally {
        state.processingDocId = null;
        renderApp();
      }
    });
  }
  const chunkButton = document.getElementById("chunk-document-button");
  if (chunkButton && documentItem?.actionable) {
    chunkButton.addEventListener("click", async () => {
      state.processingDocId = documentItem.doc_id;
      renderApp();
      try {
        await chunkDocument(documentItem.doc_id);
        state.payload = await loadWorkbench();
        notify("success", `已生成 Chunk：${documentItem.file_name}`);
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      } finally {
        state.processingDocId = null;
        renderApp();
      }
    });
  }
  const prepareButton = document.getElementById("prepare-bundle-button");
  if (prepareButton && documentItem) {
    prepareButton.addEventListener("click", async () => {
      state.preparing = true;
      renderApp();
      try {
        const result = await prepareReviewBundle({
          domain_id: documentItem.source_domain,
          doc_id: documentItem.doc_id,
          equipment_class_id: documentItem.equipment_classes[0] || null,
        });
        state.activeWorkspaceId = result.workspace_id || state.activeWorkspaceId;
        await refreshReviewWorkspace();
        await refreshApplyWorkspace();
        state.activeView = "review";
        notify("success", `已为 ${documentItem.file_name} 准备审阅包`);
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      } finally {
        state.preparing = false;
        renderApp();
      }
    });
  }
}

async function attachReviewHandlers() {
  document.querySelectorAll("[data-pack-file]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedPackFile = button.dataset.packFile;
      state.selectedCandidateIndex = 0;
      await refreshReviewWorkspace(state.selectedPackFile);
      renderApp();
    });
  });
  const reviewQuery = document.getElementById("review-query");
  if (reviewQuery) {
    reviewQuery.addEventListener("input", async () => {
      state.filters.review.query = reviewQuery.value;
      await refreshReviewWorkspace();
      renderApp();
    });
  }
  const reviewStatus = document.getElementById("review-status");
  if (reviewStatus) {
    reviewStatus.addEventListener("change", async () => {
      state.filters.review.status = reviewStatus.value;
      await refreshReviewWorkspace();
      renderApp();
    });
  }
  const reviewWorkspace = document.getElementById("review-workspace");
  if (reviewWorkspace) {
    reviewWorkspace.addEventListener("change", async () => {
      state.activeWorkspaceId = reviewWorkspace.value || null;
      state.selectedPackFile = null;
      await refreshReviewWorkspace();
      await refreshApplyWorkspace();
      renderApp();
    });
  }
  document.querySelectorAll("[data-candidate-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCandidateIndex = Number(button.dataset.candidateIndex || "0");
      renderApp();
    });
  });
  const bootstrapButton = document.getElementById("bootstrap-pack-button");
  if (bootstrapButton && state.selectedPackFile) {
    bootstrapButton.addEventListener("click", async () => {
      try {
        await bootstrapReviewPack(state.selectedPackFile);
        await refreshReviewWorkspace(state.selectedPackFile);
        await refreshApplyWorkspace();
        notify("success", `已补全草稿：${state.selectedPackFile}`);
        renderApp();
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      }
    });
  }
  const form = document.getElementById("review-form");
  if (!form || !state.reviewWorkspace?.packDetails?.[state.selectedPackFile]) {
    return;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const pack = structuredClone(state.reviewWorkspace.packDetails[state.selectedPackFile]);
    const candidate = pack.candidate_entries[state.selectedCandidateIndex];
    const formData = new FormData(form);
    candidate.review_decision = formData.get("review_decision");
    candidate.curation = candidate.curation || {};
    candidate.curation.title = formData.get("title") || "";
    candidate.curation.summary = formData.get("summary") || "";
    try {
      candidate.curation.structured_payload = JSON.parse(formData.get("structured_payload") || "{}");
      candidate.curation.applicability = JSON.parse(formData.get("applicability") || "{}");
    } catch (error) {
      notify("error", `JSON 解析失败：${error instanceof Error ? error.message : String(error)}`);
      return;
    }
    state.saving = true;
    renderApp();
    try {
      const saved = await saveReviewPack(state.selectedPackFile, pack);
      state.reviewWorkspace.packDetails[state.selectedPackFile] = saved;
      await refreshReviewWorkspace(state.selectedPackFile);
      await refreshApplyWorkspace();
      notify("success", `已保存 ${candidate.canonical_key_candidate}`);
    } catch (error) {
      notify("error", error instanceof Error ? error.message : String(error));
    } finally {
      state.saving = false;
      renderApp();
    }
  });
}

async function attachApplyHandlers() {
  const workspaceSelect = document.getElementById("apply-workspace");
  if (workspaceSelect) {
    workspaceSelect.addEventListener("change", async () => {
      state.activeWorkspaceId = workspaceSelect.value || null;
      await refreshApplyWorkspace();
      await refreshReviewWorkspace();
      renderApp();
    });
  }
  const refreshButton = document.getElementById("refresh-apply-button");
  if (refreshButton) {
    refreshButton.addEventListener("click", async () => {
      try {
        await refreshApplyWorkspace();
        notify("success", "已刷新准备度状态");
        renderApp();
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      }
    });
  }
  const applyButton = document.getElementById("run-apply-button");
  if (applyButton) {
    applyButton.addEventListener("click", async () => {
      state.applying = true;
      renderApp();
      try {
        const result = await runApplyReady();
        await refreshApplyWorkspace();
        await refreshReviewWorkspace(state.selectedPackFile);
        notify("success", `应用完成：${result.summary.applied} 个成功，${result.summary.failed} 个失败`);
      } catch (error) {
        notify("error", error instanceof Error ? error.message : String(error));
      } finally {
        state.applying = false;
        renderApp();
      }
    });
  }
}

function attachCoverageHandlers() {
  const domainSelect = document.getElementById("coverage-domain");
  if (domainSelect) {
    domainSelect.addEventListener("change", () => {
      state.filters.coverage.domain = domainSelect.value;
      renderApp();
    });
  }
  const statusSelect = document.getElementById("coverage-status");
  if (statusSelect) {
    statusSelect.addEventListener("change", () => {
      state.filters.coverage.status = statusSelect.value;
      renderApp();
    });
  }
}

async function attachViewHandlers() {
  if (state.activeView === "documents") {
    attachDocumentHandlers();
  }
  if (state.activeView === "review") {
    await attachReviewHandlers();
  }
  if (state.activeView === "apply") {
    await attachApplyHandlers();
  }
  if (state.activeView === "coverage") {
    attachCoverageHandlers();
  }
}

function renderApp() {
  renderNavigation(state.payload.navigation);
  renderSummaryStrip(state.payload.summary);
  renderNotification();
  setText("app-title", state.payload.title);
  setText("app-subtitle", state.payload.subtitle);
  const current = renderView();
  setText("view-kicker", current.kicker);
  setText("view-title", current.title);
  setText("view-description", current.description);
  document.getElementById("view-body").innerHTML = current.body;
  renderInspector(current.inspector);
  attachViewHandlers();
}

async function main() {
  try {
    state.payload = await loadWorkbench();
    state.selectedDocumentId = state.payload.views.documents.documents[0]?.doc_id || null;
    await refreshReviewWorkspace();
    await refreshApplyWorkspace();
    renderApp();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setText("app-subtitle", `加载失败：${message}`);
    document.getElementById("view-body").innerHTML = `
      <article class="surface-card empty-card">
        <p class="surface-kicker">加载失败</p>
        <h4>工作台数据暂不可用</h4>
        <p class="surface-copy">${escapeHtml(message)}</p>
      </article>
    `;
  }
}

main();
