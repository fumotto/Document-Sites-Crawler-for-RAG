"use strict";

// PyWebViewは `window.pywebview` をDOM読み込み後、非同期に注入する。
// 公式に推奨される待機方法は `pywebviewready` イベントの購読である。
function onPywebviewReady(callback) {
  if (window.pywebview) {
    callback();
  } else {
    window.addEventListener("pywebviewready", callback);
  }
}

const POLL_INTERVAL_MS = 1500; // 5.3節: 1〜2秒間隔でポーリング

let pollTimer = null;
let lastLogIndex = -1;

function showScreen(id) {
  ["screen-input", "screen-running", "screen-completed", "screen-error"].forEach((screenId) => {
    document.getElementById(screenId).hidden = screenId !== id;
  });

  const startButton = document.getElementById("btn-start");
  if (startButton) {
    startButton.disabled = id !== "screen-input";
  }
}

function collectFormData() {
  return {
    urls_text: document.getElementById("urls_text").value,
    mode: document.querySelector('input[name="mode"]:checked').value,
    word_limit: Number(document.getElementById("word_limit").value),
    request_delay: Number(document.getElementById("request_delay").value),
    include: document.getElementById("include").value,
    exclude: document.getElementById("exclude").value,
    max_pages: Number(document.getElementById("max_pages").value),
    timeout_seconds: Number(document.getElementById("timeout_seconds").value),
    log_level: document.getElementById("log_level").value,
  };
}

function applySettingsToForm(settings) {
  if (!settings) return;
  document.getElementById("urls_text").value = settings.urls_text || "";
  const modeRadio = document.querySelector(`input[name="mode"][value="${settings.mode}"]`);
  if (modeRadio) modeRadio.checked = true;
  document.getElementById("word_limit").value = settings.word_limit ?? 450000;
  document.getElementById("request_delay").value = settings.request_delay ?? 0.5;
  document.getElementById("include").value = settings.include || "";
  document.getElementById("exclude").value = settings.exclude || "";
  document.getElementById("max_pages").value = settings.max_pages ?? 1000;
  document.getElementById("timeout_seconds").value = settings.timeout_seconds ?? 30;
  document.getElementById("log_level").value = settings.log_level || "INFO";
}

function appendLogLines(panelEl, lines) {
  if (!lines || lines.length === 0) return;
  const atBottom = panelEl.scrollTop + panelEl.clientHeight >= panelEl.scrollHeight - 4;
  panelEl.textContent += (panelEl.textContent ? "\n" : "") + lines.join("\n");
  if (atBottom) {
    panelEl.scrollTop = panelEl.scrollHeight;
  }
}

function renderResultSummary(results) {
  const container = document.getElementById("result-summary");
  container.innerHTML = "";
  (results || []).forEach((r) => {
    const card = document.createElement("div");
    card.className = "site-summary-card" + (r.has_fatal_error ? " fatal" : "");

    const title = document.createElement("h3");
    title.textContent = r.site_identifier;
    card.appendChild(title);

    const status = document.createElement("div");
    status.className = r.has_fatal_error ? "status-fatal" : "status-ok";
    status.textContent = r.has_fatal_error
      ? "処理に失敗しました"
      : `完了: ${r.total_pages_included}ページ / 重複除外 ${r.duplicate_excluded_count}件 / ` +
        `チャンク ${r.chunk_file_count}件`;
    card.appendChild(status);

    if (r.warnings && r.warnings.length > 0) {
      const ul = document.createElement("ul");
      r.warnings.forEach((w) => {
        const li = document.createElement("li");
        li.textContent = w;
        ul.appendChild(li);
      });
      card.appendChild(ul);
    }

    container.appendChild(card);
  });
}

function startPolling() {
  lastLogIndex = -1;
  document.getElementById("log-panel").textContent = "";
  stopPolling();
  pollTimer = setInterval(pollStatus, POLL_INTERVAL_MS);
  pollStatus(); // 即時に1回実行し、体感の待ち時間を減らす
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollStatus() {
  try {
    const status = await window.pywebview.api.get_status(lastLogIndex);
    lastLogIndex = status.last_index;

    appendLogLines(document.getElementById("log-panel"), status.log_lines);

    document.getElementById("progress-text").textContent =
      `サイト処理中: ${status.sites_done} / ${status.sites_total}`;

    if (status.state === "completed") {
      stopPolling();
      appendLogLines(document.getElementById("log-panel-completed"), []); // 初期化目的
      document.getElementById("log-panel-completed").textContent =
        document.getElementById("log-panel").textContent;
      renderResultSummary(status.result_summary);
      showScreen("screen-completed");
      await open_explorer();
    } else if (status.state === "failed") {
      stopPolling();
      document.getElementById("error-message").textContent =
        status.error_message || "不明なエラーが発生しました。";
      showScreen("screen-error");
    }
  } catch (err) {
    // ポーリング自体の失敗はログにのみ残し、UIは次回ポーリングを待つ
    console.error("get_status failed:", err);
  }
}

function validateForm(formData) {
  const urls = formData.urls_text
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  if (urls.length === 0) {
    return "対象URLを1つ以上入力してください。";
  }
  for (const u of urls) {
    if (!u.startsWith("http://") && !u.startsWith("https://")) {
      return `URLの形式が不正です: ${u}`;
    }
  }
  return null;
}
function open_explorer() {
    window.pywebview.api.open_output_directory();
}
async function onStartClicked() {
  const formData = collectFormData();
  const validationError = validateForm(formData);
  const errorEl = document.getElementById("input-error");

  if (validationError) {
    errorEl.textContent = validationError;
    errorEl.hidden = false;
    return;
  }
  errorEl.hidden = true;

  const startButton = document.getElementById("btn-start");
  startButton.disabled = true;

  try {
    const response = await window.pywebview.api.start_execution(formData);
    if (response.status === "started") {
      showScreen("screen-running");
      startPolling();
    } else if (response.status === "already_running") {
      errorEl.textContent = "既に実行中です。";
      errorEl.hidden = false;
      showScreen("screen-input");
    }
  } catch (err) {
    errorEl.textContent = "実行開始に失敗しました。";
    errorEl.hidden = false;
    showScreen("screen-input");
  }
}

function init() {
  onPywebviewReady(async () => {
    try {
      const info = await window.pywebview.api.get_app_info();
      document.getElementById("app-title").textContent = info.app_name;
      document.getElementById("app-version").textContent = "v" + info.version;
    } catch (err) {
      console.error("get_app_info failed:", err);
    }

    try {
      const settings = await window.pywebview.api.load_settings();
      applySettingsToForm(settings);
    } catch (err) {
      console.error("load_settings failed:", err);
    }
  });

  document.getElementById("btn-start").addEventListener("click", onStartClicked);

  document.getElementById("btn-restart").addEventListener("click", () => {
    showScreen("screen-input");
  });

  document.getElementById("btn-back-from-error").addEventListener("click", () => {
    showScreen("screen-input");
  });

  document.getElementById("btn-open-log").addEventListener("click", async () => {
    try {
      await window.pywebview.api.open_log_folder();
    } catch (err) {
      console.error("open_log_folder failed:", err);
    }
  });

  showScreen("screen-input");
}

document.addEventListener("DOMContentLoaded", init);
