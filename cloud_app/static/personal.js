/* Personal workstation controls. Credential inputs are created only in local mode. */
(() => {
  const $ = (selector) => document.querySelector(selector);
  const escape = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[char]));
  const factors = {momentum: "모멘텀 (최근 상승)", mean_reversion: "평균회귀 (최근 하락)", low_volatility: "저변동성", moving_average: "이동평균 추세", volume_momentum: "거래량 모멘텀", rsi: "RSI (상대강도)"};
  let hooks;
  let connectionBusy = false;
  const isPersonal = () => Boolean(hooks?.getState().config?.personal_local_mode || hooks?.getState().dashboard?.personal_local_mode);
  const isDemo = () => Boolean(hooks?.getState().config?.local_demo_data || hooks?.getState().dashboard?.local_demo_data);

  function numberField(name, label, value, min, max, step = 1) {
    return `<label>${label}<input name="${name}" type="number" value="${value}" min="${min}" max="${max}" step="${step}" required></label>`;
  }
  function addFactor(kind = "momentum", lookback = 20, weight = 1) {
    const container = $("#manualFactors");
    if (container.children.length >= 5) return;
    const row = document.createElement("div");
    row.className = "manual-factor";
    row.innerHTML = `<label>선정 기준<select data-factor-kind>${Object.entries(factors).map(([value, text]) => `<option value="${value}">${text}</option>`).join("")}</select></label><label>관찰 거래일<input data-factor-lookback type="number" min="2" max="252" value="${lookback}" required></label><label>가중치<input data-factor-weight type="number" min="-5" max="5" step="0.1" value="${weight}" required></label><button type="button" class="ghost compact" aria-label="선정 기준 삭제">삭제</button>`;
    row.querySelector("select").value = kind;
    row.querySelector("button").addEventListener("click", () => {
      if (container.children.length === 1) { hooks.toast("선정 기준은 하나 이상 필요합니다", true); return; }
      row.remove();
      $("#addManualFactor").disabled = false;
    });
    container.append(row);
    $("#addManualFactor").disabled = container.children.length >= 5;
  }

  function renderBuilder() {
    if ($("#manualStrategyForm")) {
      $("#manualSymbolsLabel").classList.toggle("hidden", !isPersonal());
      $("#manualSymbols").required = isPersonal();
    } else {
      const section = document.createElement("section");
      section.id = "manualBuilder";
      section.innerHTML = `<details><summary>직접 규칙 입력 (선택)</summary><div class="section-head"><div><p class="eyebrow">MY STRATEGY</p><h3>내 규칙으로 전략 만들기</h3></div></div>
        <p class="section-copy">AI 키 없이 직접 설정합니다. 점수가 높은 종목을 선정하고, 완료된 전일 데이터로 판단합니다.</p>
        <form id="manualStrategyForm" class="stack">
          <label>전략 이름<input name="name" minlength="2" maxlength="100" value="나의 20일 모멘텀" required></label>
          <label id="manualSymbolsLabel">미국 주식 종목 코드 (1~20개)<input id="manualSymbols" name="symbols" maxlength="240" placeholder="예: AAPL, MSFT, NVDA" value="AAPL, MSFT, NVDA" autocapitalize="characters" spellcheck="false"><small>쉼표 또는 공백으로 구분합니다. 이 종목들 안에서만 매매 후보를 고릅니다.</small></label>
          <div id="manualFactors" class="stack"></div><button id="addManualFactor" class="ghost" type="button">선정 기준 추가 (최대 5개)</button>
          <p class="fineprint">양수 가중치는 해당 기준을 선호하고 음수는 반대로 적용합니다. 0은 사용하지 않습니다.</p>
          <div class="manual-grid">${numberField("initial_cash", "초기 가상자금 (USD)", 100000, 1000, 10000000)}${numberField("max_positions", "최대 보유 종목 수", 3, 1, 50)}${numberField("rebalance_days", "리밸런싱 간격 (달력일)", 1, 1, 30)}${numberField("stop_loss", "손절 기준 (%)", -5, -50, -0.5, 0.5)}</div>
          <details><summary>필터·거래비용 설정</summary><div class="manual-grid">${numberField("min_price", "최소 주가 (USD)", 5, 1, 1000, 0.01)}${numberField("min_average_volume", "최소 일평균 거래량", 200000, 0, 1000000000)}${numberField("history_days", "최소 가격 이력 (거래일)", 60, 20, 252)}${numberField("cost_pct", "편도 가상 거래비용 (%)", 0.3, 0, 2, 0.01)}</div><label class="consent-row"><input name="no_stop" type="checkbox">손절 사용 안 함</label></details>
          <label>설명 (선택)<textarea name="description" maxlength="1000" rows="2" placeholder="이 전략으로 확인하고 싶은 가설"></textarea></label>
          <p id="manualStrategyError" class="error" role="alert"></p><button class="primary" type="submit">전략 저장</button>
        </form></details><hr class="builder-divider">`;
      $("#strategyBuilder").prepend(section);
      $("#addManualFactor").addEventListener("click", () => addFactor());
      addFactor();
      $("#manualStrategyForm").addEventListener("submit", saveStrategy);
      $("#manualSymbolsLabel").classList.toggle("hidden", !isPersonal());
      $("#manualSymbols").required = isPersonal();
    }
    const aiAvailable = !isPersonal() && Boolean(hooks.getState().dashboard?.ai_enabled);
    $("#aiForm").classList.toggle("hidden", !aiAvailable);
    $("#aiConnectBtn").classList.toggle("hidden", isPersonal());
    $("#aiForm").previousElementSibling.classList.toggle("hidden", !aiAvailable);
    $("#aiForm").previousElementSibling.previousElementSibling.classList.toggle("hidden", !aiAvailable);
  }

  async function saveStrategy(event) {
    event.preventDefault();
    const form = event.target;
    const value = Object.fromEntries(new FormData(form));
    const error = $("#manualStrategyError");
    const button = form.querySelector("button[type=submit]");
    error.textContent = "";
    const selectedFactors = [...$("#manualFactors").children].map((row) => ({kind: row.querySelector("[data-factor-kind]").value, lookback: Number(row.querySelector("[data-factor-lookback]").value), weight: Number(row.querySelector("[data-factor-weight]").value)}));
    const symbols = [...new Set(value.symbols.toUpperCase().split(/[\s,]+/).filter(Boolean))];
    if (isPersonal() && (symbols.length < 1 || symbols.length > 20 || symbols.some((symbol) => !/^[A-Z][A-Z0-9.-]{0,14}$/.test(symbol)))) { error.textContent = "미국 주식 종목 코드를 1~20개 입력해 주세요. 예: AAPL, MSFT"; return; }
    if (isPersonal() && Number(value.max_positions) > symbols.length) { error.textContent = "최대 보유 종목 수를 입력한 종목 수 이하로 설정해 주세요."; return; }
    if (!selectedFactors.some((factor) => factor.weight !== 0)) { error.textContent = "하나 이상의 선정 기준 가중치를 0이 아닌 값으로 설정해 주세요."; return; }
    const spec = {schema_version: 1, name: value.name.trim(), description: value.description.trim(), factors: selectedFactors,
      filters: {min_price: Number(value.min_price), min_average_volume: Number(value.min_average_volume), history_days: Number(value.history_days)},
      portfolio: {initial_cash: Number(value.initial_cash), max_positions: Number(value.max_positions), rebalance_days: Number(value.rebalance_days), cost_per_side: Number(value.cost_pct) / 100, stop_loss_pct: value.no_stop ? null : Number(value.stop_loss) / 100}};
    if (isPersonal()) spec.symbols = symbols;
    button.disabled = true;
    button.textContent = "전략 저장 중…";
    try {
      await hooks.api("/api/strategies", {method: "POST", body: JSON.stringify({spec, original_prompt: ""})});
      hooks.toast("전략을 저장했습니다. 아래 내 전략에서 백테스트 또는 페이퍼 계좌를 시작하세요.");
      await hooks.refresh();
      $("#strategyList").scrollIntoView({behavior: "smooth", block: "center"});
    } catch (failure) { error.textContent = failure.message; }
    finally { button.disabled = false; button.textContent = "전략 저장"; }
  }

  function renderConnection(connection) {
    // A cloud response cannot opt into same-origin credential collection.
    if (!isPersonal() || connection.management !== "member") return false;
    const block = $("#marketDataConnectionSettings");
    block.querySelector("h4").textContent = "내 증권사 시세 연결";
    block.querySelector(".eyebrow").textContent = "PERSONAL QUOTE API";
    block.querySelector(".settings-billing-note").textContent = "이 PC의 서버가 키를 암호화해 보관합니다. 현재가 조회에만 사용하며 증권사 주문은 보내지 않습니다. 과거 일봉은 Yahoo에서 별도로 받습니다. 키와 백업은 공유하지 마세요.";
    $("#marketDataConnectionSummary").textContent = connection.connected
      ? `${connection.provider?.toUpperCase()} · ${connection.environment} · 인증 확인됨. 장중 최신 시세 수신 여부는 운용 상태에서 따로 확인하세요.`
      : "증권사에서 발급받은 본인 키를 연결하세요. KIS 또는 토스증권의 미국 주식 시세를 사용합니다.";
    $("#marketDataConnectionStatus").textContent = connection.connected ? "인증 확인됨" : "연결 필요";
    $("#marketDataConnectionStatus").className = `status-pill ${connection.connected ? "ok" : "warn"}`;
    if ($("#marketDataManageLink")) $("#marketDataManageLink").hidden = true;
    if (!$("#personalCredentialForm")) {
      const form = document.createElement("form");
      form.id = "personalCredentialForm";
      form.className = "stack market-data-connection-form";
      form.autocomplete = "off";
      form.innerHTML = `<label>증권사<select name="provider"><option value="kis">한국투자증권 KIS</option><option value="toss">토스증권</option></select></label>
        <label>발급받은 키의 환경<select name="environment"></select></label>
        <p id="personalProviderHelp" class="fineprint"></p>
        <label><span id="personalKeyLabel">App Key</span><input name="api_key" type="password" minlength="20" maxlength="512" autocomplete="new-password" spellcheck="false" required></label>
        <label><span id="personalSecretLabel">App Secret</span><input name="api_secret" type="password" minlength="20" maxlength="512" autocomplete="new-password" spellcheck="false" required></label>
        <label class="consent-row"><input name="personal_use_only" type="checkbox" required>본인의 개인 페이퍼 트레이딩 시세 조회에만 사용합니다.</label>
        <div class="settings-actions"><button class="primary" type="submit">인증 확인 후 저장</button><button id="disconnectPersonalQuote" class="ghost" type="button">연결 해제</button></div>
        <p id="personalCredentialError" class="error" role="alert"></p>`;
      block.append(form);
      form.elements.provider.value = connection.provider || "kis";
      updateCredentialProvider(connection.environment);
      form.elements.provider.addEventListener("change", () => {
        form.elements.api_key.value = "";
        form.elements.api_secret.value = "";
        updateCredentialProvider();
      });
      form.addEventListener("submit", saveConnection);
      $("#disconnectPersonalQuote").addEventListener("click", disconnectConnection);
      $("#profileDialog").addEventListener("close", () => {
        form.elements.api_key.value = "";
        form.elements.api_secret.value = "";
      });
    }
    $("#disconnectPersonalQuote").disabled = connectionBusy || !connection.connected;
    return true;
  }

  function updateCredentialProvider(environment) {
    const form = $("#personalCredentialForm");
    const toss = form.elements.provider.value === "toss";
    form.elements.environment.innerHTML = toss
      ? '<option value="live">실시간 시세 (내부 가상 체결)</option>'
      : '<option value="real">실전투자 키 · 시세 조회만</option><option value="paper">모의투자 키 · 시세 조회만</option>';
    if ([...form.elements.environment.options].some((option) => option.value === environment)) form.elements.environment.value = environment;
    $("#personalKeyLabel").textContent = toss ? "Client ID" : "App Key";
    $("#personalSecretLabel").textContent = toss ? "Client Secret" : "App Secret";
    $("#personalProviderHelp").innerHTML = toss
      ? '<a href="https://corp.tossinvest.com/ko/open-api" target="_blank" rel="noopener noreferrer">토스증권 Open API 안내</a> · WTS에서 발급한 키와 이 PC가 사용하는 공인 IP 허용 등록이 필요합니다. IP가 바뀌면 재등록하세요.'
      : '<a href="https://apiportal.koreainvestment.com/" target="_blank" rel="noopener noreferrer">한국투자증권 개발자센터</a> · 키를 발급받은 환경을 선택하세요. 내부 페이퍼 계좌이므로 실전 키를 선택해도 실제 주문은 없습니다. 미국 주식 시세 이용 권한을 확인하세요.';
  }

  function connectionControls(disabled) {
    connectionBusy = disabled;
    $("#personalCredentialForm").querySelectorAll("button, input, select").forEach((element) => { element.disabled = disabled; });
  }
  async function saveConnection(event) {
    event.preventDefault();
    const form = event.target;
    const payload = Object.fromEntries(new FormData(form));
    payload.personal_use_only = form.elements.personal_use_only.checked;
    $("#personalCredentialError").textContent = "증권사 인증을 확인하고 있습니다. 잠시 기다려 주세요.";
    connectionControls(true);
    try {
      const connection = await hooks.api("/api/me/market-data-connection", {method: "PUT", body: JSON.stringify(payload)});
      hooks.getState().marketDataConnection = connection;
      $("#personalCredentialError").textContent = "저장했습니다. 시세 수집은 활성 페이퍼 계좌와 미국 정규장이 열렸을 때 진행합니다.";
      await hooks.refresh();
    } catch (failure) { $("#personalCredentialError").textContent = failure.message; }
    finally {
      form.elements.api_key.value = "";
      form.elements.api_secret.value = "";
      payload.api_key = "";
      payload.api_secret = "";
      connectionControls(false);
      renderConnection(hooks.getState().marketDataConnection || {});
    }
  }
  async function disconnectConnection() {
    if (!window.confirm("증권사 연결을 해제하면 새 시세 수신과 가상 체결이 중단됩니다. 기존 기록은 보존됩니다. 해제할까요?")) return;
    connectionControls(true);
    try {
      await hooks.api("/api/me/market-data-connection", {method: "DELETE"});
      $("#personalCredentialError").textContent = "연결을 해제했습니다. 기록은 삭제하지 않았습니다.";
      await hooks.refresh();
    } catch (failure) { $("#personalCredentialError").textContent = failure.message; }
    finally { connectionControls(false); renderConnection(hooks.getState().marketDataConnection || {}); }
  }

  function renderStatus(dashboard) {
    document.body.classList.toggle("personal-mode", isPersonal());
    if (isPersonal()) {
      $("#market .section-head h3").textContent = "주요 지수·환율";
    }
    const operational = dashboard.operational || {};
    const worker = dashboard.worker || {};
    const workerAt = new Date(worker.observed_at).getTime();
    const fresh = typeof worker.alive === "boolean" ? worker.alive : Boolean(worker.observed_at) && Number.isFinite(workerAt) && Date.now() - workerAt < 120000;
    const status = $("#workerStatus");
    status.textContent = fresh ? "운용 프로세스 응답" : "운용 프로세스 확인 필요";
    status.className = `status-pill ${fresh ? "ok" : "warn"}`;
    const message = operational.message || (!fresh ? "페이퍼 운용 프로세스가 응답하지 않습니다. Docker 실행 상태와 사용설명서의 문제 해결을 확인하세요." : isDemo() ? "설치 연습용 합성 데이터입니다. 실제 증권사 시세가 아닙니다." : "운용 프로세스가 응답했습니다. 계좌 상태와 최신 시세 수신을 확인하세요.");
    $("#operationMessage").textContent = message;
    const data = dashboard.personal_data || {};
    const facts = [
      ["실행 모드", isPersonal() ? "개인 PC · 미국 주식 · 가상 체결" : isDemo() ? "합성 데이터 설치 연습" : "동아리 서버"],
      ["증권사 인증", dashboard.market_data_connection?.connected ? `${dashboard.market_data_connection.provider} · 확인됨` : "연결 전"],
      ["운용 프로세스", fresh ? `최근 응답 ${new Date(workerAt).toLocaleString("ko-KR")}` : "응답 지연 / 미실행"],
      ["정규장", typeof operational.market_open === "boolean" ? operational.market_open ? "열림" : "장외 또는 휴장 · 신규 체결 대기" : "미국 동부시간 09:30~16:00, 거래일 기준"],
      ["최근 시세", operational.last_quote_at ? new Date(operational.last_quote_at).toLocaleString("ko-KR") : "수신 기록 없음"],
    ];
    if (isPersonal()) facts.push(["과거 일봉", data.message || data.status || "전략 저장 후 자동 준비"], ["수신 방식", `REST 주기 조회 · ${Number(hooks.getState().config?.quote_interval_seconds || 15)}초 주기 · 종목별 수신 간격·공급자 지연은 다를 수 있음`]);
    const backup = dashboard.workers?.backup;
    if (isPersonal() && backup) facts.push(["백업", `${backup.alive ? "프로세스 응답" : "프로세스 응답 없음 · 확인 필요"} · ${backup.detail || "시작 대기"}`]);
    $("#operationFacts").innerHTML = facts.map(([label, value]) => `<dt>${escape(label)}</dt><dd>${escape(value)}</dd>`).join("");
    $("#openQuoteSettings").classList.toggle("hidden", !isPersonal() && dashboard.market_data_connection?.usage_scope !== "personal_paper_only");
    renderBuilder();
  }

  function initialize(value) { hooks = value; }
  window.MilkywayPersonal = {initialize, isPersonal, isDemo, renderStatus, renderConnection};
})();
