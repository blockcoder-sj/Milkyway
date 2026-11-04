/* Fresh operation state and the owner-run loopback process recovery control. */
(() => {
  const $ = (selector) => document.querySelector(selector);
  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  let hooks, current = null, selected = "", polling = false, recovering = false, control = null, lastChecked = 0;
  const personal = () => Boolean(hooks?.getState().config?.personal_local_mode);
  const date = (value) => value ? new Date(value).toLocaleString("ko-KR") : "아직 없음";

  function readSelection() {
    try { return localStorage.getItem("milkyway.personal.account") || ""; } catch { return ""; }
  }
  function remember(value) {
    selected = value;
    try { localStorage.setItem("milkyway.personal.account", value); } catch { /* Private browsing may disable persistence. */ }
  }
  function setText(selector, value) {
    const node = $(selector);
    if (node && node.textContent !== value) node.textContent = value;
  }
  function create() {
    if ($("#personalRuntimeControls")) return;
    const controls = document.createElement("div");
    controls.id = "personalRuntimeControls";
    controls.innerHTML = `<div class="runtime-state"><span id="runtimeStateDot" aria-hidden="true"></span><h4 id="runtimeTitle" aria-live="polite">자동매매 상태 확인 중</h4></div>
      <div class="runtime-actions"><label>운용할 계좌<select id="runtimeAccount" aria-label="복구·재개할 페이퍼 계좌"></select></label><button id="resumePersonal" class="primary" type="button">자동매매 복구·재개</button></div>
      <div id="runtimeChecks" class="runtime-checks"></div>
      <p id="runtimeProgress" class="runtime-progress" role="status"></p>
      <p id="runtimeLauncherHint" class="fineprint" hidden>시작·복구 실행기 연결이 없습니다. PC의 Milkyway 시작·복구 파일을 한 번 실행하면 이 버튼으로 프로세스 재시작까지 처리할 수 있습니다.</p>
      <p id="runtimeLastChecked" class="fineprint"></p>`;
    $("#operationMessage").before(controls);
    $("#operationPanel").removeAttribute("aria-live");
    $("#runtimeAccount").addEventListener("change", (event) => { remember(event.target.value); setText("#runtimeProgress", ""); poll(); });
    $("#resumePersonal").addEventListener("click", recover);
  }

  function view(data, networkOnline = true) {
    if (!networkOnline) return {title:"브라우저 네트워크 연결 끊김", message:"인터넷이 돌아오면 활성 계좌의 시세 조회를 자동으로 다시 시도합니다. 프로그램을 종료했다면 시작·복구를 실행해 주세요.", tone:"error"};
    return {title:data.title, message:data.message, tone:data.tone};
  }

  function render(data, observed = true) {
    create(); current = data;
    remember(data.account_id || "");
    if (observed) lastChecked = Date.now();
    const display = view(data, navigator.onLine !== false);
    setText("#runtimeTitle", display.title);
    setText("#operationMessage", display.message);
    $("#personalRuntimeControls").dataset.tone = display.tone;
    const badge = $("#workerStatus");
    badge.textContent = display.title;
    badge.className = `status-pill ${display.tone === "ok" || display.tone === "idle" ? "ok" : "warn"}`;
    const account = $("#runtimeAccount");
    const options = (data.accounts || []).map((row) => `<option value="${escape(row.id)}">${escape(row.name)}${row.expired ? " · 종료" : row.status === "paused" ? " · 일시정지" : row.status === "active" ? "" : " · 검토 필요"}</option>`).join("");
    if (account.innerHTML !== options) account.innerHTML = options;
    if (selected) account.value = selected;
    account.disabled = recovering || !data.accounts?.length;
    const choice = data.accounts?.find((row) => row.id === data.account_id);
    const worker = data.workers?.paper?.alive && data.workers?.data?.alive;
    const quote = !data.credential_saved ? "키 연결 필요" : data.state?.startsWith("quote_") || data.state === "no_quotes" ? "연결 확인 필요" : !data.market_open ? "장외 · 개장 후 확인" : data.quotes?.required ? `${data.quotes?.fresh || 0}/${data.quotes.required}종목 최신` : "계좌 재개 후 확인";
    const items = [["프로그램","응답 중"],["매매 프로세스",worker ? "실행 중" : "응답 없음"],["증권사 시세",quote],["페이퍼 계좌",choice?.expired ? "거래일 종료" : choice?.status === "active" ? "운용 허용" : choice?.status === "paused" ? "일시정지" : choice ? "검토 필요" : "선택 필요"]];
    const checks = items.map(([label,value]) => `<div><span>${label}</span><strong>${escape(value)}</strong></div>`).join("");
    if ($("#runtimeChecks").innerHTML !== checks) $("#runtimeChecks").innerHTML = checks;
    const facts = [["최근 프로세스 응답",date(data.workers?.paper?.observed_at)],["최근 증권사 시세",date(data.quotes?.last_received_at)],["최근 엔진 판단",date(data.last_execution_at)],["최근 가상 체결",date(data.last_fill_at)]];
    if (data.connection_probe) facts.unshift(["최근 API 연결 점검",`${data.connection_probe.state === "connected" ? "성공" : "확인 필요"} · ${date(data.connection_probe.checked_at)}`]);
    const session = choice?.session;
    if (session) facts.push(["이번 계좌 운용 종료",date(session.closes_at)]);
    const html = facts.map(([label,value]) => `<div class="operation-fact"><dt>${label}</dt><dd>${escape(value)}</dd></div>`).join("");
    if ($("#operationFacts").innerHTML !== html) $("#operationFacts").innerHTML = html;
    setText("#runtimeLastChecked", `상태 확인 ${date(data.checked_at)} · 연결 중에는 5초마다 확인`);
    if (!recovering) $("#resumePersonal").disabled = !data.accounts?.length;
  }

  function disconnected() {
    if (!personal()) return;
    create();
    const title = navigator.onLine === false ? "브라우저 네트워크 연결 끊김" : "프로그램 응답 확인 필요";
    setText("#runtimeTitle", title);
    setText("#operationMessage", "자동매매 상태를 확인할 수 없습니다. 복구·재개를 누르세요. 앱 자체를 닫았다면 PC의 Milkyway 시작·복구 파일을 실행해 주세요.");
    $("#personalRuntimeControls").dataset.tone = "error";
    if (!recovering) setText("#runtimeProgress", "");
    setText("#workerStatus", title);
    $("#workerStatus").className = "status-pill warn";
    setText("#runtimeLastChecked", lastChecked ? `마지막 정상 확인 ${date(lastChecked)} · 현재 상태 미확인` : "서버 상태를 확인하지 못했습니다.");
    // Old timestamps must never keep a disconnected screen looking healthy.
    $("#runtimeChecks").innerHTML = '<div><span>프로그램</span><strong>응답 미확인</strong></div><div><span>자동매매</span><strong>상태 미확인</strong></div>';
  }

  function renderUniverse(value) {
    let panel = $("#universePreparation");
    if (!panel) { panel=document.createElement("div"); panel.id="universePreparation"; panel.className="universe-preparation"; $("#operationFacts").after(panel); }
    panel.hidden = !value.state || value.state === "waiting";
    if (panel.hidden) return;
    const progress = `${Number(value.processed || 0).toLocaleString()}/${Number(value.total || 0).toLocaleString()}종목`;
    const error = {rate_limited:"요청 한도 · 잠시 뒤 자동 재시도",ip_not_allowed:"토스 허용 IP 확인 필요",authentication_failed:"토스 키 확인 필요",provider_unavailable:"자료 수신 대기 · 자동 재시도"}[value.error] || "";
    panel.innerHTML = `<strong>미국 전체 자동 선별 · ${value.state === "ready" ? "분석 준비 완료" : "자료 준비 중"}</strong><p>${escape(progress)} · 기준 일봉 ${escape(value.required_session || "확인 중")}${value.eligible != null ? ` · 조건 통과 ${Number(value.eligible).toLocaleString()}종목` : ""}${value.unavailable_history ? ` · 일봉 검증 불가 ${Number(value.unavailable_history).toLocaleString()}종목 제외` : ""}</p><small>토스 거래 가능 보통주·ADR·REIT · ETF·워런트 제외${error ? " · "+escape(error) : ""}</small>`;
  }

  async function poll() {
    if (!personal() || polling || !hooks.getState().me) return;
    polling = true;
    if (lastChecked && Date.now()-lastChecked > 15000) {
      setText("#runtimeTitle", "자동매매 상태 다시 확인 중");
      setText("#workerStatus", "상태 다시 확인 중");
      $("#personalRuntimeControls").dataset.tone = "warn";
    }
    try {
      const suffix = selected ? `?account_id=${encodeURIComponent(selected)}` : "";
      const requestedAccount = selected;
      let data = await request("/api/personal/operation" + suffix);
      if (control?.available) {
        try { data = processView(data, await controlRequest("/v1/services")); }
        catch {
          data = processView(data, {available:false});
          $("#runtimeLauncherHint").hidden = false;
        }
      }
      if (requestedAccount !== selected) return;
      render(data);
      try { renderUniverse(await request("/api/personal/universe")); } catch { /* Operation diagnostics remain available independently. */ }
    } catch (error) {
      try {
        if (error.status === 404 && selected) {
          remember(""); render(await request("/api/personal/operation"));
        } else if (error.status === 401 && hooks.getState().config.local_auto_login) {
          await ensureSession();
          render(await request("/api/personal/operation" + (selected ? `?account_id=${encodeURIComponent(selected)}` : "")));
        } else disconnected();
      } catch { disconnected(); }
    }
    finally { polling = false; }
  }

  async function loadControl() {
    control = await request("/api/personal/control");
    $("#runtimeLauncherHint").hidden = Boolean(control.available);
    return control.available;
  }

  function processView(data, monitor) {
    if (["paused","session_finished","review_required","account_required"].includes(data.state)) return data;
    if (!monitor.available) return {...data, state:"process_check_pending", title:"실행 프로세스 확인 필요", message:"프로그램은 응답하지만 PC 실행기에서 프로세스 상태를 확인하지 못했습니다. 복구·재개로 다시 점검해 주세요.", tone:"warn", ready_to_trade:false, ready_to_wait:false};
    const paper = monitor.services?.["paper-worker"] === "running", history = monitor.services?.["personal-data"] === "running";
    if (paper && history) return data;
    return {...data, state:"worker_offline", title:"자동매매 프로세스가 멈췄습니다", message:"PC에서 실행 프로세스 중지를 확인했습니다. 복구·재개를 누르면 기존 계좌를 이어서 시작합니다.", tone:"error", ready_to_trade:false, ready_to_wait:false,
      workers:{...data.workers,paper:{...data.workers?.paper,alive:paper && data.workers?.paper?.alive},data:{...data.workers?.data,alive:history && data.workers?.data?.alive}}};
  }

  async function request(path, options = {}, timeout = 5000) {
    const abort = new AbortController(), timer = setTimeout(() => abort.abort(), timeout);
    try { return await hooks.api(path, {...options, signal:abort.signal}); }
    finally { clearTimeout(timer); }
  }

  async function ensureSession() {
    const abort = new AbortController(), timer = setTimeout(() => abort.abort(), 5000);
    try { await hooks.ensureSession({signal:abort.signal}); }
    finally { clearTimeout(timer); }
  }

  async function refreshDashboard() {
    let timer;
    try { await Promise.race([hooks.refresh(), new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("전체 화면을 갱신 중입니다. 운용 상태는 계속 확인합니다.")), 10000); })]); }
    finally { clearTimeout(timer); }
  }

  async function controlRequest(path, body) {
    // The server returns only this fixed loopback address. Reject any altered URL.
    if (control?.url !== "http://127.0.0.1:19480" || !/^[a-f0-9]{64}$/.test(control.token || "")) throw new Error("시작·복구 실행기를 먼저 열어 주세요.");
    const abort = new AbortController(), timer = setTimeout(() => abort.abort(), 5000);
    try {
      const response = await fetch(control.url + path, {method:body === undefined ? "GET" : "POST", credentials:"omit", cache:"no-store", redirect:"error", signal:abort.signal,
        headers:{Authorization:`Bearer ${control.token}`, ...(body === undefined ? {} : {"Content-Type":"application/json"})},
        ...(body === undefined ? {} : {body:JSON.stringify(body)})});
      if (!response.ok) throw new Error("시작·복구 실행기 연결을 확인해 주세요.");
      return await response.json();
    } finally { clearTimeout(timer); }
  }

  async function recover() {
    if (recovering || !personal()) return;
    recovering = true; create();
    $("#resumePersonal").disabled = true; $("#runtimeAccount").disabled = true;
    setText("#resumePersonal", "복구 점검 중…");
    setText("#runtimeProgress", "프로세스와 기존 계좌를 점검합니다. 잔고와 기록은 그대로 유지합니다.");
    try {
      let helper = false;
      try { await loadControl(); } catch { /* Keep the paired capability if the app itself is down. */ }
      try { if (control?.available) { await controlRequest("/v1/status"); helper = true; } } catch { /* Account-only fallback remains safe and explicit. */ }
      if (helper) {
        let job = await controlRequest("/v1/recover", {account_id:selected || null});
        const deadline = Date.now() + 360000;
        while (job.busy) {
          setText("#runtimeProgress", job.message || "복구 점검 중입니다.");
          if (Date.now() >= deadline) throw new Error("복구 점검이 계속 진행 중입니다. 잠시 뒤 상태를 다시 확인해 주세요.");
          await new Promise((resolve) => setTimeout(resolve, 1000));
          job = await controlRequest("/v1/status");
        }
        if (["failed","blocked"].includes(job.state)) throw new Error(job.message);
        setText("#runtimeProgress", "복구 점검 완료. 현재 운용 상태를 확인해 주세요.");
      } else {
        $("#runtimeLauncherHint").hidden = false;
        // This endpoint only resumes the selected account; it cannot claim to
        // start a stopped host/Docker process without the owner-run launcher.
        await ensureSession();
        await request("/api/personal/resume", {method:"POST",body:JSON.stringify({account_id:selected || null})}, 30000);
        setText("#runtimeProgress", "계좌 재개를 요청했습니다. 프로세스가 멈췄다면 PC의 Milkyway 시작·복구 파일을 실행해 주세요.");
      }
      await ensureSession();
      await poll();
      await refreshDashboard();
    } catch (error) {
      setText("#runtimeProgress", error.message || "복구 상태를 확인해 주세요.");
      await poll();
    } finally {
      recovering = false;
      setText("#resumePersonal", "자동매매 복구·재개");
      $("#resumePersonal").disabled = !current?.accounts?.length;
      $("#runtimeAccount").disabled = !current?.accounts?.length;
    }
  }

  function onDashboard() {
    if (!personal()) return;
    create(); poll();
    if (!control?.available) loadControl().then(async (available) => {
      if (available) await controlRequest("/v1/status");
    }).catch(() => { $("#runtimeLauncherHint").hidden = false; });
  }
  function initialize(value) {
    hooks = value; selected = readSelection();
    setInterval(() => { if (personal() && !document.hidden) poll(); }, 5000);
    addEventListener("online", () => poll());
    addEventListener("offline", () => { if (current) render(current, false); else disconnected(); });
    addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
  }
  function selectAccount(id) { remember(id); poll(); }
  window.MilkywayRuntime = {initialize, onDashboard, poll, recover, disconnected, view, processView, selectAccount};
})();
