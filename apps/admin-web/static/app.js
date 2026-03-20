async function loadBundle() {
  const response = await fetch("/api/demo-bundle");
  const payload = await response.json();
  if (!response.ok || !payload.success) {
    throw new Error(payload.detail || "无法加载 demo bundle");
  }
  return payload.data;
}

function statusText(status) {
  return status === "passed" ? "通过" : status === "failed" ? "失败" : "待执行";
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function wireArtifacts(paths) {
  document.getElementById("cover-link").href = paths.cover_note || "#";
  document.getElementById("brief-link").href = paths.brief || "#";
  document.getElementById("manifest-link").href = paths.manifest || "#";
  document.getElementById("log-link").href = paths.api_log || "#";
}

function renderHighlight(highlight) {
  const template = document.getElementById("highlight-template");
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector(".highlight-surface").textContent = highlight.surface.toUpperCase();
  node.querySelector(".highlight-type").textContent = highlight.query_type;
  node.querySelector(".highlight-title").textContent = highlight.title || "未命名知识项";
  node.querySelector(".highlight-summary").textContent = highlight.summary || "暂无摘要";
  return node;
}

function renderPlantCard(card) {
  const template = document.getElementById("primary-card-template");
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector(".plant-role").textContent = card.role;
  node.querySelector(".plant-title").textContent = card.label;
  node.querySelector(".plant-focus").textContent = card.focus;
  node.querySelector(".plant-count").textContent = `${card.query_count} 条知识亮点`;
  const container = node.querySelector(".plant-highlights");
  card.highlights.forEach((highlight) => {
    container.appendChild(renderHighlight(highlight));
  });
  return node;
}

function renderMiniCard(kicker, title, summary) {
  const template = document.getElementById("mini-card-template");
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector(".mini-kicker").textContent = kicker;
  node.querySelector(".mini-title").textContent = title;
  node.querySelector(".mini-summary").textContent = summary;
  return node;
}

function renderScenarioMeta(scenario) {
  const stepTemplate = document.getElementById("step-template");
  const stepList = document.getElementById("demo-steps");
  stepList.innerHTML = "";
  scenario.demo_steps.forEach((step, index) => {
    const node = stepTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".step-index").textContent = String(index + 1);
    node.querySelector(".step-text").textContent = step;
    stepList.appendChild(node);
  });

  const questionTemplate = document.getElementById("question-template");
  const questionList = document.getElementById("customer-questions");
  questionList.innerHTML = "";
  scenario.customer_questions.forEach((question) => {
    const node = questionTemplate.content.firstElementChild.cloneNode(true);
    node.textContent = question;
    questionList.appendChild(node);
  });
}

function renderScenario(bundle) {
  const scenario = bundle.scenario;
  setText("scenario-title", scenario.title);
  setText("scenario-subtitle", scenario.subtitle);
  renderScenarioMeta(scenario);

  const coldPlantGrid = document.getElementById("cold-plant-grid");
  coldPlantGrid.innerHTML = "";
  scenario.primary_cards.forEach((card) => {
    coldPlantGrid.appendChild(renderPlantCard(card));
  });

  const downstreamGrid = document.getElementById("downstream-grid");
  downstreamGrid.innerHTML = "";
  scenario.downstream_cards.forEach((card) => {
    downstreamGrid.appendChild(
      renderMiniCard(card.role, card.label, card.highlights[0]?.summary || card.focus),
    );
  });

  const extensionGrid = document.getElementById("extension-grid");
  extensionGrid.innerHTML = "";
  scenario.extension_domains.forEach((domain) => {
    extensionGrid.appendChild(
      renderMiniCard("扩展域", domain.label, `${domain.summary} 当前包含 ${domain.query_count} 条演示查询。`),
    );
  });
}

function renderBundle(bundle) {
  const statusPill = document.getElementById("status-pill");
  statusPill.textContent = `总体状态 ${statusText(bundle.statuses.overall)}`;
  statusPill.dataset.status = bundle.statuses.overall;
  setText("semantic-count", `${bundle.counts.semantic_checks_passed ?? "-"} 项`);
  setText("mcp-count", `${bundle.counts.mcp_checks_passed ?? "-"} 项`);
  setText("api-count", `${bundle.counts.api_checks_passed ?? "-"} 项`);
  setText("generated-at", bundle.generated_at || "-");
  wireArtifacts(bundle.paths);
  setText("cover-note", bundle.cover_note_text || "暂无交付说明");
  setText("brief-preview", bundle.brief_text || "暂无中文简报");
  renderScenario(bundle);
}

async function main() {
  try {
    const bundle = await loadBundle();
    renderBundle(bundle);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    document.getElementById("cover-note").textContent = `加载失败：${message}`;
    document.getElementById("brief-preview").textContent = "请先运行 scripts/run_chinese_demo_shell.py 或 scripts/run_live_demo_evaluation.py 生成 demo bundle。";
    document.getElementById("status-pill").textContent = "加载失败";
  }
}

main();
