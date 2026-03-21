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
    label: "Prepare Review Bundle",
    command: "python3 scripts/prepare_review_pipeline_bundle.py <domain> review_bundle --doc-id <doc_id> --equipment-class-id <equipment_class_id>",
    purpose: "从已有 chunk 直接准备可审阅 bundle。",
  },
  {
    label: "Apply Ready Bundle",
    command: "python3 scripts/apply_ready_review_bundle.py review_bundle",
    purpose: "批量应用已完成审阅的 pack。",
  },
  {
    label: "Checks",
    command: "bash scripts/check-all",
    purpose: "在结束会话前跑绑定质量门。",
  },
];

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.detail || "Request failed");
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
    throw new Error(payload.detail || "Import failed");
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

function statusLabel(value) {
  const labels = {
    covered: "Covered",
    partial: "Partial",
    uncovered: "Uncovered",
    passed: "Passed",
    failed: "Failed",
    blocked_pending: "Pending",
    blocked_no_accepted: "No Accepted",
    review_complete: "Review Complete",
  };
  return labels[value] || value || "Unknown";
}

function joinInline(values) {
  if (!values || !values.length) {
    return "None";
  }
  return values.join(", ");
}

function codeBlock(value) {
  return `<code>${escapeHtml(value)}</code>`;
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
      <strong>${escapeHtml(state.notification.type.toUpperCase())}</strong>
      <span>${escapeHtml(state.notification.message)}</span>
    </div>
  `;
}

function renderSummaryStrip(summary) {
  const node = document.getElementById("summary-strip");
  const items = [
    ["Domains", summary.domain_count],
    ["Documents", summary.document_count],
    ["Fixtures", summary.fixture_count],
    ["Covered Classes", summary.covered_equipment_classes],
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
    { value: "", label: "Latest Workspace" },
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
          <span>${escapeHtml(item.source_domain)} · ${escapeHtml(joinInline(item.equipment_classes))}</span>
        </button>
      `,
    )
    .join("");
  const detail = selected
    ? `
      <article class="surface-card detail-card">
        <p class="surface-kicker">Selected Document</p>
        <h4>${escapeHtml(selected.file_name)}</h4>
        <div class="detail-grid">
          <div><span class="detail-label">Doc ID</span>${codeBlock(selected.doc_id)}</div>
          <div><span class="detail-label">Domain</span><p>${escapeHtml(selected.source_domain)}</p></div>
          <div><span class="detail-label">Equipment</span><p>${escapeHtml(joinInline(selected.equipment_classes))}</p></div>
          <div><span class="detail-label">Parse Status</span><p>${escapeHtml(selected.parse_status || "unknown")}</p></div>
          <div><span class="detail-label">Knowledge Types</span><p>${escapeHtml(joinInline(selected.knowledge_types))}</p></div>
          <div><span class="detail-label">Pages</span><p>${escapeHtml(selected.page_count || joinInline(selected.page_refs))}</p></div>
          <div><span class="detail-label">Chunks</span><p>${escapeHtml(selected.chunk_count ?? selected.entry_count ?? "-")}</p></div>
          <div><span class="detail-label">Fixtures</span><p>${escapeHtml(joinInline(selected.fixture_paths))}</p></div>
        </div>
        <div class="action-panel">
          <p class="action-title">Document Actions</p>
          ${
            selected.actionable
              ? `
                <div class="toolbar-actions">
                  <button id="parse-document-button" class="secondary-button" ${state.processingDocId === selected.doc_id ? "disabled" : ""}>Parse</button>
                  <button id="chunk-document-button" class="secondary-button" ${state.processingDocId === selected.doc_id || selected.parse_status !== "completed" ? "disabled" : ""}>Chunk</button>
                  <button id="prepare-bundle-button" class="primary-button" ${state.preparing || !selected.source_domain ? "disabled" : ""}>
                    ${state.preparing ? "Preparing..." : "Prepare Review"}
                  </button>
                </div>
                ${codeBlock(documentPrepareCommand(selected))}
              `
              : `<p class="surface-copy">Fixture samples are reference-only. Upload a real PDF to create an actionable document.</p>`
          }
        </div>
      </article>
    `
    : `
      <article class="surface-card empty-card">
        <p class="surface-kicker">Documents</p>
        <h4>No Actionable Documents Match Current Filters</h4>
        <p class="surface-copy">Connect a real database corpus or adjust the filters. Fixture samples remain visible as references below.</p>
      </article>
    `;
  const samples = (view.fixture_samples || [])
    .slice(0, 6)
    .map(
      (item) => `
        <div class="sample-row">
          <strong>${escapeHtml(item.file_name)}</strong>
          <span>${escapeHtml(item.source_domain)} · sample only · ${escapeHtml(joinInline(item.equipment_classes))}</span>
        </div>
      `,
    )
    .join("");
  return `
    <section class="split-grid review-grid">
      <article class="surface-card list-card">
        <p class="surface-kicker">Corpus</p>
        <h4>Real Documents</h4>
        <form id="document-import-form" class="editor-form compact-form">
          <label>
            <span class="detail-label">Import PDF</span>
            <input type="file" name="file" accept="application/pdf,.pdf" />
          </label>
          <label>
            <span class="detail-label">Domain</span>
            <select name="source_domain">
              <option value="">Unassigned</option>
              <option value="hvac">hvac</option>
              <option value="drive">drive</option>
            </select>
          </label>
          <div class="editor-actions">
            <button id="import-document-button" type="submit" class="primary-button" ${state.importing ? "disabled" : ""}>
              ${state.importing ? "Importing..." : "Import PDF"}
            </button>
          </div>
        </form>
        <p class="meta-note">${view.db_available ? "Database-backed corpus is available." : "Database unavailable. Showing fixture samples only."}</p>
        ${filterBar({
          searchId: "documents-query",
          searchValue: state.filters.documents.query,
          searchPlaceholder: "Search document, doc_id, equipment...",
          selectId: "documents-domain",
          selectValue: state.filters.documents.domain,
          selectOptions: [
            { value: "all", label: "All Domains" },
            ...[...new Set((view.documents || []).map((item) => item.source_domain).filter(Boolean))].sort().map((value) => ({ value, label: value })),
          ],
        })}
        <div class="list-column">${rows}</div>
        <div class="sample-panel">
          <p class="surface-kicker">Fixture Samples</p>
          <div class="list-column compact-list">${samples || "<span class=\"meta-note\">No fixture samples.</span>"}</div>
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
            <p class="task-domain">${escapeHtml(item.domain_id)}</p>
            <h4>${escapeHtml(item.equipment_class_id)}</h4>
            <p class="surface-copy">${escapeHtml(item.rationale)}</p>
          </div>
          <div class="task-row-side">
            <span class="task-label">Next Targets</span>
            <div class="tag-row">${item.target_knowledge_objects
              .map((value) => `<span class="tag">${escapeHtml(value)}</span>`)
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
        <p class="surface-kicker">Priority Queue</p>
        <h4>Highest-Leverage Work</h4>
        <div class="task-list">${cards}</div>
      </article>
      <article class="surface-card note-card">
        <p class="surface-kicker">Operator Rules</p>
        <h4>What We Optimize For</h4>
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
          <p class="surface-kicker">Review Packs</p>
          <h4>No Review Packs Found</h4>
          <p class="surface-copy">Set \`WORKBENCH_REVIEW_DIR\` or generate a bundle first, then return here to review and save pack files.</p>
          ${codeBlock(COMMAND_SHORTCUTS[0].command)}
        </article>
        <article class="surface-card">
          <p class="surface-kicker">Workflow</p>
          <h4>Review Path</h4>
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
        <p class="surface-kicker">Candidate Detail</p>
        <h4>${escapeHtml(selectedCandidate.canonical_key_candidate)}</h4>
        <div class="toolbar-row">
          <button id="bootstrap-pack-button" class="secondary-button">Bootstrap Current Pack</button>
          <span class="meta-note">${escapeHtml(selectedPack.pack_file)}</span>
        </div>
        <form id="review-form" class="editor-form">
          <label>
            <span class="detail-label">Review Decision</span>
            <select name="review_decision">
              ${["pending", "accepted", "rejected"]
                .map(
                  (value) => `<option value="${value}" ${value === (selectedCandidate.review_decision || "pending") ? "selected" : ""}>${value}</option>`,
                )
                .join("")}
            </select>
          </label>
          <label>
            <span class="detail-label">Title</span>
            <input name="title" value="${escapeHtml(selectedCandidate.curation?.title || "")}" />
          </label>
          <label>
            <span class="detail-label">Summary</span>
            <textarea name="summary" rows="4">${escapeHtml(selectedCandidate.curation?.summary || "")}</textarea>
          </label>
          <label>
            <span class="detail-label">Structured Payload</span>
            <textarea name="structured_payload" rows="8">${escapeHtml(JSON.stringify(selectedCandidate.curation?.structured_payload || {}, null, 2))}</textarea>
          </label>
          <label>
            <span class="detail-label">Applicability</span>
            <textarea name="applicability" rows="5">${escapeHtml(JSON.stringify(selectedCandidate.curation?.applicability || {}, null, 2))}</textarea>
          </label>
          <div class="editor-actions">
            <button type="submit" class="primary-button" ${state.saving ? "disabled" : ""}>${state.saving ? "Saving..." : "Save Candidate"}</button>
          </div>
        </form>
      </article>
      <article class="surface-card evidence-card">
        <p class="surface-kicker">Evidence</p>
        <h4>${escapeHtml(selectedCandidate.doc_name)}</h4>
        <div class="detail-grid">
          <div><span class="detail-label">Chunk</span>${codeBlock(selectedCandidate.chunk_id)}</div>
          <div><span class="detail-label">Page</span><p>${escapeHtml(selectedCandidate.page_no)}</p></div>
          <div><span class="detail-label">Type</span><p>${escapeHtml(selectedCandidate.knowledge_object_type)}</p></div>
          <div><span class="detail-label">Equipment</span><p>${escapeHtml(selectedCandidate.equipment_class_candidate?.equipment_class_id || "")}</p></div>
        </div>
        <div class="evidence-block">
          <span class="detail-label">Excerpt</span>
          <p>${escapeHtml(selectedCandidate.text_excerpt || "")}</p>
        </div>
        <div class="evidence-block">
          <span class="detail-label">Evidence Text</span>
          <pre>${escapeHtml(selectedCandidate.evidence_text || "")}</pre>
        </div>
      </article>
    `
    : `
      <article class="surface-card empty-card">
        <p class="surface-kicker">Candidate Detail</p>
        <h4>Select A Candidate</h4>
        <p class="surface-copy">Choose a candidate from the filtered pack list to start editing curation fields.</p>
      </article>
    `;
  return `
    <section class="review-shell">
      <article class="surface-card list-card">
        <p class="surface-kicker">Review Packs</p>
        <h4>Pack Directory</h4>
        <div class="meta-note">${escapeHtml(workspace.resolved_dir)}</div>
        ${filterBar({
          searchId: "review-query",
          searchValue: state.filters.review.query,
          searchPlaceholder: "Search pack, doc, equipment...",
          selectId: "review-status",
          selectValue: state.filters.review.status,
          selectOptions: [
            { value: "all", label: "All Statuses" },
            { value: "blocked_pending", label: "Pending" },
            { value: "blocked_no_accepted", label: "No Accepted" },
            { value: "review_complete", label: "Review Complete" },
          ],
          secondarySelectId: "review-workspace",
          secondarySelectValue: state.activeWorkspaceId || "",
          secondarySelectOptions: workspaceOptions(workspace.workspaces),
        })}
        <div class="list-column">${packRows}</div>
      </article>
      <article class="surface-card list-card">
        <p class="surface-kicker">Candidates</p>
        <h4>${escapeHtml(selectedPack?.doc_name || "No Pack Selected")}</h4>
        <div class="meta-note">${escapeHtml(selectedPack ? `${selectedPack.equipment_class_id} · ${statusLabel(selectedPack.status)}` : "Adjust filters to select a pack")}</div>
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
          <p class="surface-copy">Covered ${item.covered_equipment_classes}, Uncovered ${item.uncovered_equipment_classes}</p>
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
          <td colspan="5">No readiness data yet.</td>
        </tr>
      `;
  const latestApply = workspace?.latest_apply;
  const latestApplyCard = latestApply
    ? `
      <article class="surface-card">
        <p class="surface-kicker">Latest Apply</p>
        <h4>${escapeHtml(`Applied ${latestApply.summary?.applied ?? 0} · Failed ${latestApply.summary?.failed ?? 0}`)}</h4>
        <p class="surface-copy">Generated at ${escapeHtml(latestApply.generated_at || "-")}</p>
        ${
          latestApply.summary_text
            ? `<div class="evidence-block"><span class="detail-label">Summary Text</span><pre>${escapeHtml(latestApply.summary_text)}</pre></div>`
            : ""
        }
        ${
          latestApply.paths
            ? `<div class="detail-grid">
                <div><span class="detail-label">Apply Report</span>${codeBlock(latestApply.paths.apply_report || "-")}</div>
                <div><span class="detail-label">Stats</span>${codeBlock(latestApply.paths.stats || "-")}</div>
              </div>`
            : ""
        }
      </article>
    `
    : `
      <article class="surface-card">
        <p class="surface-kicker">Latest Apply</p>
        <h4>No Apply Run Yet</h4>
        <p class="surface-copy">Run apply-ready after at least one pack reaches ready status to populate stats and summary artifacts here.</p>
      </article>
    `;
  return `
    <section class="split-grid">
      <article class="surface-card">
        <p class="surface-kicker">Apply Rules</p>
        <h4>What Must Stay True</h4>
        <ul class="rule-list">${rules}</ul>
      </article>
      <div class="stack-grid">
        ${watch}
        <article class="surface-card table-card">
          <div class="toolbar-row">
            <div>
              <p class="surface-kicker">Readiness</p>
              <h4>Review Pack Status</h4>
            </div>
            <div class="toolbar-actions">
              <select id="apply-workspace" class="filter-select">
                ${workspaceOptions(workspace?.workspaces)
                  .map((item) => `<option value="${escapeHtml(item.value)}" ${item.value === (state.activeWorkspaceId || "") ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
                  .join("")}
              </select>
              <button id="refresh-apply-button" class="secondary-button">Refresh Readiness</button>
              <button id="run-apply-button" class="primary-button" ${state.applying || !workspace?.can_apply_bundle ? "disabled" : ""}>
                ${state.applying ? "Applying..." : "Run Apply-Ready"}
              </button>
            </div>
          </div>
          <div class="meta-note">${escapeHtml(workspace?.resolved_dir || "No review bundle configured")}</div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Pack</th>
                  <th>Equipment</th>
                  <th>Status</th>
                  <th>Accepted</th>
                  <th>Pending</th>
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
          <td>${escapeHtml(joinInline(item.covered_knowledge_objects))}</td>
          <td>${escapeHtml(joinInline(item.missing_knowledge_objects))}</td>
        </tr>
      `,
    )
    .join("");
  return `
    <article class="surface-card table-card">
      <p class="surface-kicker">${escapeHtml(domain.domain_id)}</p>
      <h4>${escapeHtml(domain.domain_name)}</h4>
      <p class="surface-copy">Supported: ${escapeHtml(joinInline(domain.supported_knowledge_objects))}</p>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Equipment</th>
              <th>Status</th>
              <th>Covered</th>
              <th>Missing</th>
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
          { value: "all", label: "All Domains" },
          ...view.domains.map((domain) => ({ value: domain.domain_id, label: domain.domain_name })),
        ],
        secondarySelectId: "coverage-status",
        secondarySelectValue: state.filters.coverage.status,
        secondarySelectOptions: [
          { value: "all", label: "All Statuses" },
          { value: "covered", label: "Covered" },
          { value: "partial", label: "Partial" },
          { value: "uncovered", label: "Uncovered" },
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
        <p class="surface-kicker">Demo Bundle</p>
        <h4>Bundle Not Found</h4>
        <p class="surface-copy">Run the evaluation flow first if you want this workbench to surface demo and handoff artifacts.</p>
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
        <p class="surface-kicker">Evaluation</p>
        <h4>${escapeHtml(scenario.title || "Current Demo Bundle")}</h4>
        <p class="surface-copy">${escapeHtml(scenario.subtitle || "Evidence-backed demo overview.")}</p>
        <div class="artifact-row">${links}</div>
      </article>
      <article class="surface-card">
        <p class="surface-kicker">Status</p>
        <h4>${escapeHtml(statusLabel(view.overall_status))}</h4>
        <p class="surface-copy">Generated at ${escapeHtml(view.generated_at || "-")}</p>
      </article>
    </section>
  `;
}

function renderView() {
  const views = state.payload.views;
  const viewMap = {
    inbox: {
      kicker: "Today",
      title: "Operator Inbox",
      description: "Start with the highest-leverage coverage gaps and keep the next action obvious.",
      body: inboxView(views.inbox),
      inspector: {
        title: "Work The Highest-Leverage Gap",
        summary: "Prefer equipment classes that can close a full review/apply loop instead of adding isolated facts.",
        list: views.inbox.rules,
        command: COMMAND_SHORTCUTS[0],
      },
    },
    documents: {
      kicker: "Intake",
      title: "Document Intake Surface",
      description: "Select a document, inspect its current semantic surface, and prepare the next review command without leaving the workbench.",
      body: documentListView(views.documents),
      inspector: {
        title: "Documents Should Lead To Action",
        summary: "A document panel should tell the operator what class it feeds and what command advances it into review.",
        list: [
          "Keep source file, domain, class, and pages visible together.",
          "Generate review commands from the selected doc, not from generic placeholders.",
          "Do not hide fixture paths from operators.",
        ],
        command: COMMAND_SHORTCUTS[0],
      },
    },
    review: {
      kicker: "Review",
      title: "Candidate Review Workspace",
      description: "Open local review packs, edit curation fields, save locally, and bootstrap draft fields when needed.",
      body: reviewWorkspaceView(views.review),
      inspector: {
        title: "Review And Save Locally",
        summary: "The first useful common path is local pack editing beside evidence, not a giant workflow engine.",
        list: [
          "Pack list stays visible while editing.",
          "Evidence stays adjacent to curation fields.",
          "Save writes back to the local review pack file.",
        ],
        command: COMMAND_SHORTCUTS[1],
      },
    },
    apply: {
      kicker: "Apply",
      title: "Readiness And Apply Control",
      description: "Use this surface to keep ready packs visible, blocked packs obvious, and apply actions deliberate.",
      body: applyView(views.apply),
      inspector: {
        title: "Apply Only What Is Ready",
        summary: "The workbench should make readiness visible before it makes apply easy, and show what happened after apply completes.",
        list: views.apply.rules,
        command: COMMAND_SHORTCUTS[1],
      },
    },
    coverage: {
      kicker: "Coverage",
      title: "Coverage Inventory",
      description: "Track which equipment classes are covered, partial, or still thin across the ontology-backed domains.",
      body: coverageView(views.coverage),
      inspector: {
        title: "Thin Coverage Should Be Obvious",
        summary: "Coverage views should surface missing knowledge types first so planning does not drift back into guesswork.",
        list: [
          "Show supported vs covered vs missing.",
          "Keep priority targets tied to ontology classes.",
          "Use domain inventory as the planning source of truth.",
        ],
        command: COMMAND_SHORTCUTS[2],
      },
    },
    demo: {
      kicker: "Demo",
      title: "Evaluation And Handoff",
      description: "Demo artifacts still matter, but they should sit beside the internal operator flow instead of replacing it.",
      body: demoView(views.demo),
      inspector: {
        title: "Demo Is A Surface, Not The Product",
        summary: "Use the bundle to verify delivery and explain progress, but keep internal workbench workflows primary.",
        list: [
          "Preserve evidence-backed outputs.",
          "Keep demo routes read-only.",
          "Do not let evaluation UI replace intake or review tooling.",
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
        notify("error", "Choose a PDF before importing");
        return;
      }
      state.importing = true;
      renderApp();
      try {
        const document = await importDocument(formData);
        state.payload = await loadWorkbench();
        state.selectedDocumentId = document.doc_id;
        notify("success", `Imported ${document.file_name}`);
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
        notify("success", `Parsed ${documentItem.file_name}`);
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
        notify("success", `Chunked ${documentItem.file_name}`);
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
        notify("success", `Prepared review bundle for ${documentItem.file_name}`);
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
        notify("success", `Bootstrapped ${state.selectedPackFile}`);
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
      notify("error", `JSON parse failed: ${error instanceof Error ? error.message : String(error)}`);
      return;
    }
    state.saving = true;
    renderApp();
    try {
      const saved = await saveReviewPack(state.selectedPackFile, pack);
      state.reviewWorkspace.packDetails[state.selectedPackFile] = saved;
      await refreshReviewWorkspace(state.selectedPackFile);
      await refreshApplyWorkspace();
      notify("success", `Saved ${candidate.canonical_key_candidate}`);
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
        notify("success", "Refreshed readiness status");
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
        notify("success", `Apply complete: ${result.summary.applied} applied, ${result.summary.failed} failed`);
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
    setText("app-subtitle", `Load failed: ${message}`);
    document.getElementById("view-body").innerHTML = `
      <article class="surface-card empty-card">
        <p class="surface-kicker">Load Error</p>
        <h4>Workbench Data Not Available</h4>
        <p class="surface-copy">${escapeHtml(message)}</p>
      </article>
    `;
  }
}

main();
