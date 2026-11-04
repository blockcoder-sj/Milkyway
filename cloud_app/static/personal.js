/* Personal workstation controls. Credential inputs are created only in local mode. */
(() => {
  const $ = (selector) => document.querySelector(selector);
  const escape = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[char]));
  let hooks;
  let connectionBusy = false;
  const isPersonal = () => Boolean(hooks?.getState().config?.personal_local_mode || hooks?.getState().dashboard?.personal_local_mode);
  const isDemo = () => Boolean(hooks?.getState().config?.local_demo_data || hooks?.getState().dashboard?.local_demo_data);

  function renderBuilder() {
    const aiAvailable = !isPersonal() && Boolean(hooks.getState().dashboard?.ai_enabled);
    $("#strategyBuilder").classList.toggle("hidden", !aiAvailable);
    $("#aiForm").classList.toggle("hidden", !aiAvailable);
    $("#aiConnectBtn").classList.toggle("hidden", isPersonal());
    $("#aiForm").previousElementSibling.classList.toggle("hidden", !aiAvailable);
    $("#aiForm").previousElementSibling.previousElementSibling.classList.toggle("hidden", !aiAvailable);
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
      if (window.MilkywayRuntime) {
        window.MilkywayRuntime.onDashboard(dashboard);
        renderBuilder();
        return;
      }
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
    $("#operationFacts").innerHTML = facts.map(([label, value]) => `<div class="operation-fact"><dt>${escape(label)}</dt><dd>${escape(value)}</dd></div>`).join("");
    $("#openQuoteSettings").classList.toggle("hidden", !isPersonal() && dashboard.market_data_connection?.usage_scope !== "personal_paper_only");
    renderBuilder();
  }

  function initialize(value) { hooks = value; }
  window.MilkywayPersonal = {initialize, isPersonal, isDemo, renderStatus, renderConnection};
})();
