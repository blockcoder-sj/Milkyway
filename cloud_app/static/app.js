const state = {config: {}, refreshPromise: null, lastRefresh: null, csrf: "", me: null, dashboard: null, aiConnection: null, marketDataConnection: null, strategies: [], backtests: [], backtestOffset: 0, backtestPage: [], marketCountry: "us", sectorCountry: "us", workspace: "market", stream: null, preferences: window.MilkywayProfile.loadPreferences()};
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const money = (value) => new Intl.NumberFormat("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0}).format(value || 0);
const number = (value) => window.MilkywayFormat.number(value);
const pct = (value) => `${Number(value || 0) >= 0 ? "+" : ""}${window.MilkywayFormat.number(Number(value || 0), 2, 2)}%`;

const MARKET_SELECTION = {
  us: {
    label: "미국",
    indices: new Set(["sp500", "dow", "nasdaq"]),
    futures: new Set(["nasdaq_future"]),
  },
  kr: {
    label: "한국",
    indices: new Set(["kospi", "kosdaq"]),
    futures: new Set(["kospi200_future"]),
  },
};
const SECTOR_SELECTION = {
  us: {
    title: "US Equity Sectors",
    empty: "섹터 맵 또는 완료 가격 데이터가 준비되지 않았습니다.",
    method: "미국 유니버스의 최근 두 완료 세션을 비교한 자체 10개 섹터 동일가중 평균입니다. 공식 GICS 섹터지수는 아닙니다.",
  },
  kr: {
    title: "한국 주식 업종 흐름",
    empty: "한국 종목별 시세와 거래소 업종 분류가 아직 연결되지 않았습니다.",
    method: "한국 탭은 종목별 완료 가격과 KRX 기준 업종 매핑이 연결되면 동일한 방식으로 계산합니다.",
  },
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[character]));
}

function shortTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("ko-KR", {month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"}).format(date);
}

function toast(message, error = false) {
  const element = $("#toast");
  element.textContent = message;
  element.style.borderColor = error ? "#7f3c3c" : "#725ca5";
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 3200);
}

async function api(path, options = {}) {
  const headers = {"Content-Type": "application/json", ...(options.headers || {})};
  if (state.csrf && options.method && options.method !== "GET") headers["X-CSRF-Token"] = state.csrf;
  let response;
  try { response = await fetch(path, {credentials: "same-origin", ...options, headers}); }
  catch { throw new Error("서버에 연결할 수 없습니다. Docker가 실행 중인지 확인해 주세요. 저장 요청 중이었다면 새로고침 후 기록을 먼저 확인하고 재시도하세요."); }
  if (response.status === 204) return null;
  let body = {};
  try { body = await response.json(); } catch { throw new Error("서버 응답을 읽지 못했습니다. 실행한 요청은 자동으로 다시 보내지 않습니다. 기록을 새로고침해 상태를 확인하세요."); }
  if (!response.ok) {
    if (response.status === 401) throw new Error(state.config.local_auto_login
      ? "로컬 세션이 만료되었습니다. 새로고침하면 자동으로 다시 연결됩니다. 저장된 기록은 유지됩니다."
      : "로그인이 만료되었습니다. 다시 로그인해 주세요. 저장된 기록은 유지됩니다.");
    if (response.status === 429) throw new Error(typeof body.detail === "string" ? body.detail : "요청 한도에 도달했습니다. 잠시 기다린 뒤 다시 시도해 주세요.");
    const detail = Array.isArray(body.detail) ? body.detail.map((item) => `${(item.loc || []).filter((value) => value !== "body").join(".")}: ${item.msg}`).join("\n") : body.detail;
    throw new Error(typeof detail === "string" ? detail : `요청을 처리하지 못했습니다 (HTTP ${response.status}). 사용설명서의 문제 해결을 확인하세요.`);
  }
  return body;
}

function authTab(name) {
  $$('[data-auth-tab]').forEach((button) => button.classList.toggle("active", button.dataset.authTab === name));
  $("#loginForm").classList.toggle("hidden", name !== "login");
  $("#registerForm").classList.toggle("hidden", name !== "register");
  $("#authError").textContent = "";
}

function formObject(form) { return Object.fromEntries(new FormData(form).entries()); }

function sourceLabel(row) {
  if (row.status === "live") return window.MilkywayPersonal.isPersonal() ? "최근 수신" : "실시간";
  if (row.status === "completed_close") return "완료 종가";
  if (row.status === "stale") return "갱신 지연";
  return "연결 대기";
}

function renderMarketRows(target, rows) {
  const element = $(target);
  element.innerHTML = rows.map((row) => `
    <div class="market-card">
      <div class="market-card-top"><span class="market-label">${escapeHtml(row.label)}</span><i class="feed-dot ${row.status === "live" ? "live" : row.status === "stale" ? "stale" : ""}"></i></div>
      <strong class="market-value ${row.value == null ? "missing" : ""}">${number(row.value)}</strong>
      <div class="market-source"><span>${escapeHtml(sourceLabel(row))}${row.source ? ` · ${escapeHtml(row.source)}` : ""}</span><time>${shortTime(row.observed_at)}</time></div>
    </div>`).join("");
}

function marketCards(groups) {
  if (window.MilkywayPersonal.isPersonal()) {
    window.MilkywayMarket.renderMarket(state.dashboard?.market_overview, state.marketCountry);
    const rows = groups?.us || state.dashboard?.market || [];
    renderMarketRows("#watchlistCards", rows);
    $("#watchlistCards").classList.toggle("empty-state", !rows.length);
    if (!rows.length) $("#watchlistCards").textContent = "증권사 연결·활성 페이퍼 계좌·미국 정규장이 준비되면 내 전략 종목의 시세가 표시됩니다.";
    $("#watchlistUpdated").textContent = `미국 주식 · ${rows.filter((row) => row.is_realtime).length}/${rows.length}종목 최근 수신`;
    return;
  }
  const selected = MARKET_SELECTION[state.marketCountry] || MARKET_SELECTION.us;
  const indices = (groups?.indices || []).filter((row) => selected.indices.has(row.id));
  const futures = (groups?.futures || []).filter((row) => selected.futures.has(row.id));
  renderMarketRows("#marketCards", indices);
  renderMarketRows("#marketFutures", futures);
  const observed = [...indices, ...futures].filter((row) => row.observed_at).sort((a, b) => new Date(b.observed_at) - new Date(a.observed_at));
  const liveCount = [...indices, ...futures].filter((row) => row.is_realtime).length;
  $("#marketUpdated").textContent = observed.length ? `${selected.label} · ${liveCount}개 실시간 · 최근 ${shortTime(observed[0].observed_at)}` : `${selected.label} 시세 공급자 연결 대기`;
  $("#leadingIndicatorLabel").textContent = `${selected.label} 선행 지표`;
}

function selectMarketCountry(country) {
  if (!MARKET_SELECTION[country]) return;
  state.marketCountry = country;
  $$('[data-market-country]').forEach((button) => {
    const active = button.dataset.marketCountry === country;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  marketCards(state.dashboard?.market_groups || {});
}

function selectSectorCountry(country) {
  if (!SECTOR_SELECTION[country]) return;
  state.sectorCountry = country;
  $$('[data-sector-country]').forEach((button) => {
    const active = button.dataset.sectorCountry === country;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  const heatmaps = state.dashboard?.sector_heatmaps || {us: state.dashboard?.sector_heatmap};
  renderHeatmap(heatmaps?.[country] || {status: "awaiting_market_data", cells: []});
}

function openWorkspace(workspace, updateHash = true) {
  if (!["market", "strategy", "detail", "company"].includes(workspace)) return;
  if (workspace !== "detail") window.MilkywayMarketDetail?.leave();
  if (workspace !== "company") window.MilkywayCompany?.leave();
  state.workspace = workspace;
  $$('[data-workspace-page]').forEach((section) => section.classList.toggle("hidden", section.dataset.workspacePage !== workspace));
  $$('[data-open-workspace]').forEach((link) => {
    const active = link.dataset.openWorkspace === workspace || (["detail","company"].includes(workspace) && link.dataset.openWorkspace === "market");
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current");
  });
  if (updateHash) history.replaceState(null, "", `#${workspace}`);
  window.scrollTo({top: 0, behavior: "smooth"});
}

function showAuth() {
  $("#landingView").classList.add("hidden");
  $("#authView").classList.remove("hidden");
  authTab("login");
  history.replaceState(null, "", "#login");
  window.scrollTo({top: 0, behavior: "smooth"});
  setTimeout(() => $("#loginForm input[name=email]").focus(), 220);
}

function showLanding() {
  if (state.stream) {
    state.stream.close();
    state.stream = null;
  }
  $("#authView").classList.add("hidden");
  $("#appView").classList.add("hidden");
  $("#landingView").classList.remove("hidden");
  $("#landingAction").textContent = "시작하기";
  $$('[data-authenticated-only]').forEach((element) => element.classList.toggle("hidden", !state.me));
  history.replaceState(null, "", "#landing");
  document.documentElement.classList.add("scroll-instant");
  window.scrollTo(0, 0);
  requestAnimationFrame(() => document.documentElement.classList.remove("scroll-instant"));
}

function applyMarketPreference(country) {
  const selected = MARKET_SELECTION[country] && SECTOR_SELECTION[country] ? country : "us";
  state.marketCountry = selected;
  state.sectorCountry = selected;
  if (state.dashboard) {
    selectMarketCountry(selected);
    selectSectorCountry(selected);
  }
}

async function showDashboard(workspace = "market", updateHash = true) {
  if (!state.me) { showAuth(); return; }
  applyMarketPreference(state.preferences.default_market);
  $("#landingView").classList.add("hidden");
  $("#authView").classList.add("hidden");
  $("#appView").classList.remove("hidden");
  await refresh();
  applyMarketPreference(state.preferences.default_market);
  openWorkspace(["market", "strategy"].includes(workspace) ? workspace : "market", updateHash);
  if (!state.stream) {
    state.stream = new EventSource("/api/stream");
    state.stream.addEventListener("heartbeat", () => refresh().catch(showRefreshError));
    state.stream.addEventListener("error", () => { $("#connectionError").textContent = "상태 연결을 다시 시도하고 있습니다. 30초마다 서버 상태를 별도로 확인합니다."; });
  }
}

function accountCards(rows) {
  $("#accountCount").textContent = `${rows.length}개 계좌`;
  const element = $("#accountCards");
  if (!rows.length) {
    element.className = "account-grid empty-state";
    element.textContent = "아직 계좌가 없습니다. 전략을 만든 뒤 페이퍼 계좌를 시작하세요.";
    return;
  }
  element.className = "account-grid";
  element.innerHTML = rows.map((account) => {
    const run = account.paper_session;
    const finished = run && (run.expired || run.completed_at);
    const label = finished ? "지정 거래일 종료" : account.status === "active" ? "운용 허용 · 상태 확인 필요" : ["review_required", "configuration_required"].includes(account.status) ? "전략·보유 종목 검토 필요" : "일시정지";
    const control = finished ? '<span class="status-pill">종료</span>' : ["review_required", "configuration_required"].includes(account.status)
      ? '<span class="status-pill warn">REVIEW</span>'
      : `<button class="ghost compact account-toggle" data-id="${escapeHtml(account.id)}" data-status="${account.status === "active" ? "paused" : "active"}">${account.status === "active" ? "정지" : "재개"}</button>`;
    const selection = account.automatic_selection;
    const coverage = selection ? `<p class="fineprint">전체 ${Number(selection.universe_count).toLocaleString()}종목 · 평가 가능 ${Number(selection.evaluated_count).toLocaleString()} · 제외 ${Object.values(selection.excluded || {}).reduce((a,b)=>a+Number(b),0).toLocaleString()} · ${selection.fresh ? "최신 탐색" : "탐색 갱신 대기"} ${shortTime(selection.created_at)} · 목표 ${Object.entries(selection.weights || {}).map(([ticker,weight])=>`${escapeHtml(ticker)} ${pct(weight)}`).join(", ")}</p>` : "";
    const positions = account.positions.map((position) => `<span class="chip">${escapeHtml(position.ticker)} ${pct(position.pnl_pct)}</span>`).join("") || `<span class="chip">${finished ? "보유 종목 없음" : "첫 리밸런싱 대기"}</span>`;
    const schedule = run ? `<p class="fineprint">미국 거래일 ${escapeHtml(run.session_date)} · 자동 중지 ${escapeHtml(new Date(run.closes_at).toLocaleString("ko-KR"))}${run.summary ? `<br>체결 ${number(run.summary.fill_count, 0)}건 · 종료 시 마지막 확인 평가액 ${money(run.summary.last_known_equity)} (공식 종가 미확인)` : ""}</p>` : "";
    return `<div class="account"><div class="account-top"><div><h4>${escapeHtml(account.name)}</h4><span class="muted">${label}</span></div>${control}</div><div class="metric">${money(account.equity)}</div><div class="${account.return_pct >= 0 ? "positive-text" : "negative-text"}">${pct(account.return_pct)}</div><div class="positions">${positions}</div>${coverage}${schedule}<p class="fineprint">현금 ${money(account.cash)} · 최근 리밸런싱 ${escapeHtml(account.last_rebalanced_on || "대기")}<br>${escapeHtml(account.execution_detail || "평가액은 마지막 수신 가격 기준입니다.")}</p><button class="ghost compact account-history-open" data-id="${escapeHtml(account.id)}">체결·자산 기록 보기</button></div>`;
  }).join("");
  $$('.account-toggle').forEach((button) => button.addEventListener("click", () => toggleAccount(button.dataset.id, button.dataset.status)));
  $$('.account-history-open').forEach((button) => button.addEventListener("click", () => openAccountHistory(button.dataset.id)));
}

async function toggleAccount(id, status) {
  try {
    await api(`/api/accounts/${id}`, {method: "PATCH", body: JSON.stringify({status})});
    toast(status === "active" ? "계좌 운용을 재개했습니다" : "계좌를 일시정지했습니다");
    await refresh();
  } catch (error) { toast(error.message, true); }
}

async function openAccountHistory(id) {
  const account = state.dashboard.accounts.find((row) => row.id === id);
  const dialog = $("#accountHistoryDialog");
  $("#accountHistoryTitle").textContent = `${account?.name || "계좌"} · 체결·자산 기록`;
  $("#accountHistoryBody").textContent = "최근 기록을 불러오고 있습니다…";
  if (!dialog.open) dialog.showModal();
  try {
    const history = await api(`/api/accounts/${encodeURIComponent(id)}/history`);
    const points = history.equity || [];
    const fills = history.fills || [];
    const encodedId = encodeURIComponent(id);
    $("#accountHistoryBody").innerHTML = `<div class="history-actions"><a class="ghost compact" href="/api/accounts/${encodedId}/export?kind=fills" download>전체 체결 CSV 저장</a><a class="ghost compact" href="/api/accounts/${encodedId}/export?kind=equity" download>전체 자산 CSV 저장</a></div>
      <h4>최근 자산 추이</h4>${points.length > 1 ? equityChart(points, "페이퍼 계좌 자산 곡선") : '<p class="fineprint">자산 기록은 시세 평가 후 쌓입니다. 아직 그래프를 그릴 기록이 충분하지 않습니다.</p>'}
      <p class="fineprint">${points.length ? `${shortTime(points[0].at)} ~ ${shortTime(points.at(-1).at)} · 최근 ${points.length.toLocaleString()}개 관측` : "아직 자산 관측 기록이 없습니다."}</p>
      <h4>최근 가상 체결 (${fills.length.toLocaleString()}건)</h4>
      ${fills.length ? `<div class="history-table-wrap"><table class="history-table"><thead><tr><th>체결 시각</th><th>종목</th><th>매매</th><th>수량</th><th>가격 (USD)</th><th>비용 (USD)</th><th>사유</th></tr></thead><tbody>${fills.map((fill) => `<tr><td>${shortTime(fill.executed_at)}</td><td>${escapeHtml(fill.ticker)}</td><td>${escapeHtml(fill.side)}</td><td>${number(fill.shares)}</td><td>${number(fill.price)}</td><td>${number(fill.fee)}</td><td>${escapeHtml(fill.reason)}</td></tr>`).join("")}</tbody></table></div>` : '<p class="fineprint">아직 체결이 없습니다. 활성 계좌, 최신 일봉·시세, 미국 정규장 및 리밸런싱 시각을 운용 상태에서 확인하세요.</p>'}`;
  } catch (error) { $("#accountHistoryBody").textContent = error.message; }
}

function dataFacts(data) {
  if (window.MilkywayPersonal.isPersonal()) {
    const personal = state.dashboard.personal_data || {};
    $("#dataFacts").innerHTML = `<dt>선정 범위</dt><dd>전략별 전체 미국 자동 선정 또는 직접 지정</dd><dt>일봉 출처</dt><dd>Yahoo · 자동 준비·갱신</dd><dt>준비 상태</dt><dd>${escapeHtml(personal.message || personal.status || "전략 저장 후 준비")}</dd><dt>완료 세션</dt><dd>${escapeHtml(personal.last_completed_session || data.last_completed_session || "준비 중")}</dd><dt>성과 판정</dt><dd>탐색용 · 생존편향 있음</dd>`;
    return;
  }
  const lag = Number(data.trading_session_lag || 0);
  const freshnessLabel = lag ? `${lag}세션 지연` : "최신 완료 세션";
  $("#dataFacts").innerHTML = `
    <dt>완료 세션</dt><dd class="${lag ? "data-stale" : "data-fresh"}">${escapeHtml(data.last_completed_session)} · ${freshnessLabel}</dd>
    <dt>기대 완료 세션</dt><dd>${escapeHtml(data.expected_latest_completed_session)}</dd>
    <dt>검증 종목</dt><dd>${Number(data.symbol_count).toLocaleString()}개</dd>
    <dt>첫 인증 스냅샷</dt><dd>${escapeHtml(data.first_certified_snapshot)}</dd>
    <dt>첫 정식 체결일</dt><dd>${escapeHtml(data.first_certified_execution_date)}</dd>
    <dt>전방 데이터 게이트</dt><dd class="${data.forward_data_gate_ready ? "data-fresh" : "data-stale"}">${data.forward_data_gate_ready ? "정상" : `차단 (${Number(data.strategy_candidate_data_blockers)})`}</dd>
    <dt>데이터 지문</dt><dd>${escapeHtml(data.fingerprint)}</dd>`;
}

function renderStrategies() {
  const element = $("#strategyList");
  if (!state.strategies.length) {
    element.className = "strategy-list empty-state";
    element.textContent = "저장된 전략이 없습니다.";
    return;
  }
  element.className = "strategy-list";
  element.innerHTML = state.strategies.map((strategy) => `
    <div class="strategy">
      <div class="strategy-head"><div><h4>${escapeHtml(strategy.name)}</h4><p>${escapeHtml(strategy.description)}</p></div></div>
      <p>${strategy.spec.universe === "us_all" ? "미국 상장주식 전체 · 최신 시세로 자동 선정·배분" : escapeHtml((strategy.spec.symbols || []).join(", "))}</p><div class="factor-row">${strategy.spec.factors.map((factor) => `<span class="badge">${escapeHtml(factor.kind)} ${Number(factor.lookback)}d × ${Number(factor.weight)}</span>`).join("")}<span class="badge amber">${Number(strategy.spec.portfolio.max_positions)}종목 · ${Number(strategy.spec.portfolio.rebalance_days)}일</span></div>
      <details class="code-preview"><summary>저장된 전략 규격 보기</summary><pre>${escapeHtml(strategy.code_preview)}</pre></details>
      <div class="strategy-actions"><button class="ghost run-backtest" data-id="${escapeHtml(strategy.id)}">백테스트</button><button class="ghost new-account" data-id="${escapeHtml(strategy.id)}">페이퍼 계좌</button></div>
    </div>`).join("");
  $$('.run-backtest').forEach((button) => button.addEventListener("click", () => openBacktest(button.dataset.id)));
  $$('.new-account').forEach((button) => button.addEventListener("click", () => openAccount(button.dataset.id)));
}

function chartGeometry(points, width = 620, height = 200) {
  if (!points || points.length < 2) return null;
  const values = points.map((point) => Number(point.value)).filter(Number.isFinite);
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const coordinates = values.map((value, index) => ({x: index / (values.length - 1) * width, y: height - 8 - (value - min) / range * (height - 24)}));
  const line = coordinates.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
  return {line, area: `${line} L${width},${height} L0,${height} Z`, min, max};
}

function equityChart(points, label = "백테스트 자산 곡선") {
  const geometry = chartGeometry(points);
  if (!geometry) return "";
  return `<svg class="equity-chart" viewBox="0 0 620 200" preserveAspectRatio="none" role="img" aria-label="${escapeHtml(label)}">
    <defs><linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c4a7ff" stop-opacity=".32"/><stop offset="1" stop-color="#c4a7ff" stop-opacity="0"/></linearGradient></defs>
    <line class="grid-line" x1="0" y1="50" x2="620" y2="50"/><line class="grid-line" x1="0" y1="100" x2="620" y2="100"/><line class="grid-line" x1="0" y1="150" x2="620" y2="150"/>
    <path class="area" d="${geometry.area}"/><path class="line" d="${geometry.line}"/>
  </svg>`;
}

function featuredBacktest() {
  const element = $("#featuredBacktest");
  const job = state.backtests.find((item) => item.status === "completed" && item.result?.metrics);
  if (!job) {
    const active = state.backtests.find((item) => ["queued", "running"].includes(item.status));
    element.className = "featured-empty";
    element.innerHTML = active
      ? `<div class="empty-visual"><span></span><span></span><span></span><span></span></div><strong>백테스트 실행 중 · ${Number(active.progress)}%</strong><p>${escapeHtml(active.strategy_name)} 결과가 준비되면 자동으로 표시됩니다.</p>`
      : '<div class="empty-visual"><span></span><span></span><span></span><span></span></div><strong>아직 완료된 백테스트가 없습니다</strong><p>전략을 만든 뒤 백테스트를 실행하면 성과 곡선과 핵심 지표가 이곳에 표시됩니다.</p>';
    return;
  }
  const metrics = job.result.metrics;
  const points = job.result.equity_curve || [];
  const firstDate = points[0]?.date || job.start_date;
  const lastDate = points.at(-1)?.date || job.end_date;
  element.className = "featured-result";
  element.innerHTML = `
    <div class="featured-title"><div><h4>${escapeHtml(job.strategy_name)}</h4><p>${escapeHtml(job.start_date)} → ${escapeHtml(job.end_date)} · ${escapeHtml(job.bias_mode)}</p></div><span class="status-pill ${job.result.certification_eligible ? "ok" : "warn"}">${job.result.certification_eligible ? "PIT CERTIFIED" : "EXPLORATORY"}</span></div>
    <div class="result-grid"><div class="mini-metric"><span>RETURN</span><strong class="${metrics.return_pct >= 0 ? "positive-text" : "negative-text"}">${pct(metrics.return_pct)}</strong></div><div class="mini-metric"><span>SHARPE</span><strong>${Number(metrics.sharpe).toFixed(2)}</strong></div><div class="mini-metric"><span>MAX DRAWDOWN</span><strong class="negative-text">${pct(metrics.mdd_pct)}</strong></div><div class="mini-metric"><span>TRADES</span><strong>${Number(metrics.trade_count).toLocaleString()}</strong></div></div>
    <div class="equity-chart-wrap"><div class="chart-head"><span>${escapeHtml(firstDate)}</span><span>ENDING ${money(metrics.ending_equity)}</span><span>${escapeHtml(lastDate)}</span></div>${equityChart(points)}${job.result.caveat ? `<p class="result-caveat">${escapeHtml(job.result.caveat)}</p>` : ""}</div>`;
}

function sparkline(points) {
  const geometry = chartGeometry(points, 300, 70);
  return geometry ? `<svg class="sparkline" viewBox="0 0 300 70" preserveAspectRatio="none"><path d="${geometry.line}" fill="none" stroke="#c4a7ff" stroke-width="2"/></svg>` : "";
}

function renderBacktests() {
  const element = $("#backtestList");
  if (!state.backtests.length) {
    element.className = "backtest-list empty-state";
    element.textContent = "실행 기록이 없습니다.";
    featuredBacktest();
    return;
  }
  element.className = "backtest-list";
  const page = state.backtestOffset ? state.backtestPage : state.backtests;
  element.innerHTML = page.map((job) => {
    const result = job.result;
    const metrics = result?.metrics;
    return `<div class="backtest"><div class="backtest-head"><div><h4>${escapeHtml(job.strategy_name)}</h4><p>${escapeHtml(job.start_date)} → ${escapeHtml(job.end_date)} · ${escapeHtml(job.bias_mode)}</p></div><span class="status-pill ${job.status === "completed" ? "ok" : job.status === "failed" ? "warn" : ""}">${escapeHtml(job.status)} ${Number(job.progress)}%</span></div>${result?.caveat ? `<p class="notice">${escapeHtml(result.caveat)}</p>` : ""}${metrics ? `<div class="result-grid"><div class="mini-metric"><span>RETURN</span><strong>${pct(metrics.return_pct)}</strong></div><div class="mini-metric"><span>SHARPE</span><strong>${Number(metrics.sharpe).toFixed(2)}</strong></div><div class="mini-metric"><span>MDD</span><strong>${pct(metrics.mdd_pct)}</strong></div><div class="mini-metric"><span>TRADES</span><strong>${Number(metrics.trade_count)}</strong></div></div>${sparkline(result.equity_curve)}` : ""}${job.error ? `<p class="error">${escapeHtml(job.error)}</p>` : ""}</div>`;
  }).join("");
  element.insertAdjacentHTML("beforeend", `<div class="history-actions"><button id="newerBacktests" class="ghost" type="button" ${state.backtestOffset ? "" : "disabled"}>새로운 기록</button><span class="fineprint">${state.backtestOffset + 1}~${state.backtestOffset + page.length}번째</span><button id="olderBacktests" class="ghost" type="button" ${page.length < 50 ? "disabled" : ""}>이전 기록</button></div>`);
  $("#newerBacktests").addEventListener("click", () => loadBacktestPage(Math.max(0, state.backtestOffset - 50)));
  $("#olderBacktests").addEventListener("click", () => loadBacktestPage(state.backtestOffset + 50));
  featuredBacktest();
}

async function loadBacktestPage(offset) {
  $("#olderBacktests").disabled = true;
  $("#newerBacktests").disabled = true;
  try {
    const page = await api(`/api/backtests?limit=50&offset=${offset}`);
    if (!page.length && offset) { toast("이전 기록이 더 없습니다"); return; }
    state.backtestOffset = offset;
    state.backtestPage = page;
  } catch (error) { toast(error.message, true); }
  finally { renderBacktests(); }
}

function renderHeatmap(data) {
  if (window.MilkywayPersonal.isPersonal()) {
    window.MilkywayMarket.renderSectors(state.dashboard?.market_overview, state.sectorCountry, $("#sectorSort").value);
    return;
  }
  const element = $("#sectorHeatmap");
  const selected = SECTOR_SELECTION[state.sectorCountry] || SECTOR_SELECTION.us;
  $("#sectorHeatmapTitle").textContent = selected.title;
  $("#heatmapMethod").textContent = selected.method;
  $("#heatmapMeta").textContent = data.status === "ready" ? `${data.as_of} · EQUAL-WEIGHT · ${Number(data.coverage_pct).toFixed(1)}%` : `${state.sectorCountry === "us" ? "미국" : "한국"} 섹터 데이터 연결 필요`;
  if (!data.cells?.length) {
    element.className = "heatmap empty-state";
    element.textContent = selected.empty;
    return;
  }
  element.className = "heatmap";
  element.innerHTML = data.cells.map((cell) => {
    const value = Number(cell.return_pct);
    const strength = Math.min(.78, .18 + Math.abs(value) / 5 * .6).toFixed(2);
    const direction = value > .03 ? "positive" : value < -.03 ? "negative" : "neutral";
    return `<div class="heat-cell ${direction}" style="--strength:${strength}"><strong>${escapeHtml(cell.label)}</strong><b>${pct(value)}</b><small>${Number(cell.symbol_count)}종목 · 상승 ${Number(cell.advancers_pct).toFixed(0)}%</small></div>`;
  }).join("");
}

function renderNews(data) {
  const element = $("#newsList");
  $("#newsMeta").textContent = data.status === "ready" ? `${data.provider} · ${shortTime(data.observed_at)}` : "뉴스 공급자 연결 대기";
  if (!data.items?.length) {
    element.className = "news-list feed-empty empty-state";
    element.innerHTML = "<div><strong>아직 연결된 뉴스 피드가 없습니다</strong><p>라이선스가 확인된 뉴스 공급자를 연결하면 서버가 한 번 수집하고 모든 동아리 회원에게 공유합니다.</p></div>";
    return;
  }
  element.className = "news-list";
  element.innerHTML = data.items.slice(0, 7).map((item, index) => `<a class="news-item" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer"><span class="news-index">${String(index + 1).padStart(2, "0")}</span><div><h4>${escapeHtml(item.title)}</h4><p>${escapeHtml(item.source)} · ${shortTime(item.published_at)}</p></div><span class="news-arrow">↗</span></a>`).join("");
}

async function loadDashboard() {
  const [dashboard, strategies, backtests] = await Promise.all([api("/api/dashboard"), api("/api/strategies"), api("/api/backtests")]);
  state.dashboard = dashboard;
  state.aiConnection = dashboard.ai_connection;
  state.marketDataConnection = dashboard.market_data_connection;
  state.strategies = strategies;
  state.backtests = backtests;
  marketCards(dashboard.market_groups);
  renderHeatmap(dashboard.sector_heatmaps?.[state.sectorCountry] || dashboard.sector_heatmap);
  renderNews(dashboard.news);
  accountCards(dashboard.accounts);
  dataFacts(dashboard.data);
  renderStrategies();
  renderBacktests();

  window.MilkywayPersonal.renderStatus(dashboard);
  $("#connectionError").textContent = "";
  state.lastRefresh = Date.now();
  $("#aiConnectBtn").classList.toggle("connected", dashboard.ai_enabled);
  $("#aiConnectBtn").setAttribute("aria-label", dashboard.ai_enabled ? "AI 연결 설정 열기, 연결됨" : "AI 연결 설정 열기");
  profileController.render();
  await window.MilkywayResearch.refresh();

}

function showRefreshError(error) {
  $("#connectionError").textContent = error.message + (state.lastRefresh ? ` 마지막 정상 조회: ${new Date(state.lastRefresh).toLocaleString("ko-KR")}. 화면의 값이 최신이 아닐 수 있습니다.` : "");
  $("#workerStatus").textContent = "서버 연결 확인 필요";
  $("#workerStatus").className = "status-pill warn";
}

function refresh() {
  if (state.refreshPromise) return state.refreshPromise;
  state.refreshPromise = loadDashboard().finally(() => { state.refreshPromise = null; });
  return state.refreshPromise;
}

async function enterApp(me = null) {
  state.config = await api("/api/config");
  state.me = me || await api("/api/auth/me");
  state.csrf = state.me.csrf;
  profileController.render();
  const detail = location.hash.match(/^#detail\/([a-z0-9_]+)$/);
  const company = location.hash.match(/^#company\/([a-z0-9_]+)\/([A-Z0-9.-]+)$/);
  const entity = location.hash.match(/^#company\/(c_[a-f0-9]{32})$/);
  const requested = location.hash === "#market" ? "market" : location.hash === "#strategy" ? "strategy" : null;
  await showDashboard(requested || "market", !detail && !company && !entity);
  if (detail && state.config.personal_local_mode) await window.MilkywayMarketDetail.open(detail[1],false);
  if (company && state.config.personal_local_mode) await window.MilkywayCompany.open(company[1],company[2],false);
  if (entity && state.config.personal_local_mode) await window.MilkywayCompany.openEntity(entity[1],false);
}

function openBacktest(id) {
  const form = $("#backtestForm");
  form.strategy_id.value = id;
  const data = state.dashboard.data;
  const hasStrict = !window.MilkywayPersonal.isPersonal() && !window.MilkywayPersonal.isDemo() && data.forward_data_gate_ready && data.first_certified_execution_date <= data.last_completed_session;
  form.bias_mode.querySelector('option[value="strict"]').disabled = !hasStrict;
  form.bias_mode.value = hasStrict ? "strict" : "exploratory";
  const today = new Date().toISOString().slice(0, 10);
  const fallbackStart = `${new Date().getFullYear()}-01-02`;
  const strategy = state.strategies.find((row) => row.id === id);
  const warmupDays = Math.max(strategy?.spec?.filters?.history_days || 60, ...((strategy?.spec?.factors || []).map((factor) => factor.lookback + 1)));
  const firstDate = new Date(`${data.first_completed_session || fallbackStart}T00:00:00Z`);
  firstDate.setUTCDate(firstDate.getUTCDate() + Math.ceil(warmupDays * 7 / 5) + 10);
  const earliestWindow = new Date(`${data.last_completed_session || today}T00:00:00Z`);
  earliestWindow.setUTCDate(earliestWindow.getUTCDate() - 365);
  const exploratoryStart = new Date(Math.max(firstDate.getTime(), earliestWindow.getTime())).toISOString().slice(0, 10);
  form.start_date.value = hasStrict ? data.first_certified_execution_date : exploratoryStart < (data.last_completed_session || today) ? exploratoryStart : data.first_completed_session || fallbackStart;
  form.end_date.value = data.last_completed_session || today;
  if (!hasStrict) toast("정식 PIT 체결 구간이 아직 준비되지 않아 탐색용 모드로 열었습니다");
  $("#backtestDialog").showModal();
}

function openAccount(id) {
  $("#accountForm").strategy_id.value = id;
  $("#accountForm").elements.session_date.value = "";
  $("#paperSessionField").classList.toggle("hidden", !state.config?.personal_local_mode);
  $("#accountDialog").showModal();
}

function startMarketBackdrop() {
  const canvas = $("#marketBackdrop");
  const context = canvas.getContext("2d");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let width = innerWidth;
  let height = innerHeight;
  let stars = [];
  let dust = [];
  let lastFrame = -Infinity;

  function makeStar() {
    return {
      x: Math.random(),
      y: Math.random(),
      size: .35 + Math.random() * 1.25,
      alpha: .15 + Math.random() * .52,
      phase: Math.random() * Math.PI * 2,
      drift: .001 + Math.random() * .003,
    };
  }

  function makeDust() {
    const averaged = (Math.random() + Math.random() + Math.random()) / 3;
    return {
      progress: Math.random() * 1.24 - .12,
      offset: (averaged - .5) * 2,
      size: .35 + Math.random() * 1.8,
      alpha: .08 + Math.random() * .46,
      phase: Math.random() * Math.PI * 2,
      speed: .45 + Math.random() * .75,
      white: Math.random() > .76,
    };
  }

  function resize() {
    width = innerWidth;
    height = innerHeight;
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const pixels = width * height;
    stars = Array.from({length: Math.max(90, Math.min(230, Math.floor(pixels / 7200)))}, makeStar);
    dust = Array.from({length: Math.max(180, Math.min(520, Math.floor(pixels / 3100)))}, makeDust);
  }

  function draw(now = 0) {
    if (document.hidden) {
      lastFrame = now;
      if (!reduced) requestAnimationFrame(draw);
      return;
    }
    if (!reduced && now - lastFrame < 42) {
      requestAnimationFrame(draw);
      return;
    }
    lastFrame = now;
    context.clearRect(0, 0, width, height);
    context.save();
    context.globalCompositeOperation = "screen";

    stars.forEach((star) => {
      const x = (star.x * (width + 24) + now * star.drift) % (width + 24) - 12;
      const twinkle = .7 + Math.sin(now * .0012 + star.phase) * .3;
      context.fillStyle = `rgba(224,211,255,${star.alpha * twinkle})`;
      context.beginPath();
      context.arc(x, star.y * height, star.size, 0, Math.PI * 2);
      context.fill();
    });

    const wave = Math.sin(now * .00013) * height * .025;
    const ribbonLayers = [
      {lineWidth: Math.max(140, height * .22), color: "rgba(91,51,171,.055)", blur: 58},
      {lineWidth: Math.max(68, height * .11), color: "rgba(153,105,255,.075)", blur: 34},
      {lineWidth: Math.max(18, height * .032), color: "rgba(220,202,255,.09)", blur: 18},
    ];
    ribbonLayers.forEach((layer, index) => {
      context.beginPath();
      context.moveTo(-width * .12, height * .86 + wave * (index + 1));
      context.bezierCurveTo(
        width * .24, height * .30 - wave,
        width * .66, height * .72 + wave,
        width * 1.12, height * .17 - wave * .5,
      );
      context.lineCap = "round";
      context.lineWidth = layer.lineWidth;
      context.strokeStyle = layer.color;
      context.shadowBlur = layer.blur;
      context.shadowColor = "rgba(174,132,255,.34)";
      context.stroke();
    });
    context.shadowBlur = 0;

    dust.forEach((particle) => {
      const travel = (particle.progress + now * .000006 * particle.speed + .12) % 1.24 - .12;
      const x = travel * width;
      const center = height * (.79 - travel * .53) + Math.sin(travel * Math.PI * 2.4 + now * .00015) * height * .045;
      const spread = Math.max(0, 1 - Math.abs(particle.offset));
      const y = center + particle.offset * height * .22;
      const edgeFade = Math.max(0, Math.sin(((travel + .12) / 1.24) * Math.PI));
      const twinkle = .72 + Math.sin(now * .0015 + particle.phase) * .28;
      const alpha = particle.alpha * spread * edgeFade * twinkle;
      context.fillStyle = particle.white
        ? `rgba(255,255,255,${alpha})`
        : `rgba(196,167,255,${alpha})`;
      context.beginPath();
      context.arc(x, y, particle.size * (.55 + spread), 0, Math.PI * 2);
      context.fill();
    });
    context.restore();
    if (!reduced) requestAnimationFrame(draw);
  }
  resize();
  addEventListener("resize", resize, {passive: true});
  if (reduced) draw(); else requestAnimationFrame(draw);
}

$$('[data-auth-tab]').forEach((button) => button.addEventListener("click", () => authTab(button.dataset.authTab)));
$$('[data-show-landing]').forEach((button) => button.addEventListener("click", (event) => { event.preventDefault(); showLanding(); }));
$$('[data-open-dashboard]').forEach((button) => button.addEventListener("click", () => showDashboard(button.dataset.openDashboard).catch((error) => toast(error.message, true))));
$$('[data-prompt]').forEach((button) => button.addEventListener("click", () => { $("#strategyPrompt").value = button.dataset.prompt; $("#strategyPrompt").focus(); }));
$$('[data-market-country]').forEach((button) => button.addEventListener("click", () => selectMarketCountry(button.dataset.marketCountry)));
$$('[data-sector-country]').forEach((button) => button.addEventListener("click", () => selectSectorCountry(button.dataset.sectorCountry)));
$("#sectorSort").addEventListener("change", () => selectSectorCountry(state.sectorCountry));
$$('[data-open-workspace]').forEach((link) => link.addEventListener("click", (event) => { event.preventDefault(); openWorkspace(link.dataset.openWorkspace); }));
$$('[data-close]').forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));

$("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { const data = await api("/api/auth/login", {method: "POST", body: JSON.stringify(formObject(event.target))}); state.csrf = data.csrf; await enterApp(); }
  catch (error) { $("#authError").textContent = error.message; }
});

$("#registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { const data = await api("/api/auth/register", {method: "POST", body: JSON.stringify(formObject(event.target))}); state.csrf = data.csrf; await enterApp(); }
  catch (error) { $("#authError").textContent = error.message; }
});

$("#landingAction").addEventListener("click", () => {
  if (!state.me && state.config.local_auto_login) { initializeApp().catch(showStartupError); return; }
  if (!state.me) { showAuth(); return; }
  showDashboard("market").catch(showRefreshError);
});

const profileController = window.MilkywayProfile.create({
  getUser: () => state.me,
  getPreferences: () => state.preferences,
  getAiConnection: () => state.aiConnection,
  getMarketDataConnection: () => state.marketDataConnection,
  onAiLoad: async () => {
    state.aiConnection = await api("/api/me/ai-connection");
    return state.aiConnection;
  },
  onMarketDataLoad: async () => {
    state.marketDataConnection = await api("/api/me/market-data-connection");
    return state.marketDataConnection;
  },
  onSave: (preferences) => {
    state.preferences = preferences;
    applyMarketPreference(preferences.default_market);
    toast("개인 설정을 저장했습니다");
  },
  onLogout: async () => { try { await api("/api/auth/logout", {method: "POST"}); } finally { location.reload(); } },
  onError: (error) => toast(error.message || "요청을 처리하지 못했습니다", true),
});
profileController.bind();
window.MilkywayPersonal.initialize({api, refresh, toast, getState: () => state});
window.MilkywayMarketDetail.initialize({api, openWorkspace, getState: () => state});
window.MilkywayCompany.initialize({api, openWorkspace, getState: () => state});
addEventListener("popstate", () => {
  const detail=location.hash.match(/^#detail\/([a-z0-9_]+)$/);
  const company=location.hash.match(/^#company\/([a-z0-9_]+)\/([A-Z0-9.-]+)$/);
  const entity=location.hash.match(/^#company\/(c_[a-f0-9]{32})$/);
  if(detail) window.MilkywayMarketDetail.open(detail[1],false);
  else if(company) window.MilkywayCompany.open(company[1],company[2],false);
  else if(entity) window.MilkywayCompany.openEntity(entity[1],false);
  else openWorkspace(location.hash==="#strategy"?"strategy":"market",false);
});
window.MilkywayResearch.initialize({api, refresh, toast, getState: () => state, openAccountHistory});
$("#openQuoteSettings").addEventListener("click", () => profileController.openSettings("marketDataConnectionSettings"));

$("#aiConnectBtn").addEventListener("click", () => profileController.openSettings("aiConnectionSettings"));

$("#aiForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.dashboard && !state.dashboard.ai_enabled) { toast("동아리 공용 AI가 아직 준비되지 않았습니다", true); profileController.openSettings("aiConnectionSettings"); return; }
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  button.querySelector("span").textContent = "AI 생성 중…";
  try { await api("/api/strategies/generate", {method: "POST", body: JSON.stringify(formObject(event.target))}); event.target.reset(); toast("전략을 검증하고 저장했습니다"); await refresh(); }
  catch (error) { toast(error.message, true); }
  finally { button.disabled = false; button.querySelector("span").textContent = "전략 생성 및 검증"; }
});

$("#backtestForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  try { await api("/api/backtests", {method: "POST", body: JSON.stringify(formObject(event.target))}); $("#backtestDialog").close(); toast("백테스트를 작업 큐에 추가했습니다"); await refresh(); }
  catch (error) { toast(error.message, true); }
  finally { button.disabled = false; }
});

$("#accountForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.target.querySelector("button[type=submit]");
  button.disabled = true;
  const body = formObject(event.target);
  if (!body.session_date) delete body.session_date;
  try { await api("/api/accounts", {method: "POST", body: JSON.stringify(body)}); $("#accountDialog").close(); toast("페이퍼 계좌를 만들었습니다"); await refresh(); }
  catch (error) { toast(error.message, true); }
  finally { button.disabled = false; }
});

$("#refreshBtn").addEventListener("click", () => refresh().catch((error) => toast(error.message, true)));

setInterval(() => {
  if (state.me && !$("#appView").classList.contains("hidden")) refresh().catch(showRefreshError);
}, 30000);

let marketPolling = false;
setInterval(async () => {
  if (marketPolling || !state.me || !state.dashboard || !state.config.personal_local_mode ||
      !["market", "detail"].includes(state.workspace) || document.hidden || $("#appView").classList.contains("hidden")) return;
  marketPolling = true;
  const owner = state.me.id;
  try {
    const overview = await api("/api/market-overview");
    if (state.me?.id === owner && state.dashboard) {
      state.dashboard.market_overview = overview;
      window.MilkywayMarketDetail.quote(overview);
      window.MilkywayMarket.renderMarket(overview, state.marketCountry);
      window.MilkywayMarket.renderSectors(overview, state.sectorCountry, $("#sectorSort").value);
    }
  } catch { /* The last timestamp and age remain visible; normal refresh shows errors. */ }
  finally { marketPolling = false; }
}, 2000);

async function initializeApp() {
  const config = await api("/api/config");
  state.config = config;
  $("#profileMenu [data-profile-menu-action=logout]").classList.toggle("hidden", Boolean(config.local_auto_login));
  if (config.personal_local_mode || config.local_demo_data) {
    const label = $("#registerForm input[name=invite_code]").closest("label");
    label.firstChild.textContent = "로컬 설치 코드 (기본값: local-club)";
    $("#registerForm input[name=invite_code]").value = "local-club";
    $("#about .about-intro > p").textContent = "내 PC에서 규칙으로 전략을 만들고, 백테스트와 페이퍼 트레이딩을 진행합니다. 실제 증권사 주문은 보내지 않습니다.";
    $("#profileMenu [data-profile-menu-action=settings] small").textContent = "AI 연구 · 증권사 시세 연결";
  }
  const me = config.local_auto_login
    ? await api("/api/auth/local", {method: "POST", headers: {"X-Milkyway-Local": "1"}, body: "{}"})
    : await api("/api/auth/me");
  await enterApp(me);
}

function showStartupError(error) {
  if (state.me) showRefreshError(error);
  else if (state.config.local_auto_login) toast(error.message, true);
  else if (location.hash === "#login") showAuth();
}

startMarketBackdrop();
initializeApp().catch(showStartupError);
