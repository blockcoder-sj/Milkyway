(() => {
  const DEFAULT_PREFERENCES = Object.freeze({default_market: "us"});
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  function loadPreferences() {
    try {
      const saved = JSON.parse(localStorage.getItem("milkyway_preferences") || "{}");
      return {
        default_market: ["us", "kr"].includes(saved.default_market) ? saved.default_market : DEFAULT_PREFERENCES.default_market,
      };
    } catch {
      return {...DEFAULT_PREFERENCES};
    }
  }

  function create({getUser, getPreferences, getAiConnection, getMarketDataConnection, onAiLoad, onMarketDataLoad, onSave, onLogout, onError}) {
    let activeTrigger = null;

    function renderAiConnection() {
      const connection = getAiConnection?.() || {connected: false, providers: []};
      if (window.MilkywayPersonal?.isPersonal()) {
        $("#aiConnectionSettings").classList.remove("hidden");
        $("#aiConnectionSettings h4").textContent = "내 AI 연구 설정";
        $("#aiConnectionStatus").textContent = connection.configured ? "키 설정됨 · 호출 미확인" : "키 입력 필요";
        $("#aiConnectionSummary").textContent = `Milkyway/.env의 OPENAI_API_KEY에 키를 입력하고 앱을 재시작하세요. 모델 ${connection.model || "gpt-5.4-mini"}, 추론 ${connection.reasoning || "none"}. 연구 대화에서 요청마다 승인한 경우에만 호출합니다.`;
        $("#aiConnectionSettings .settings-billing-note").textContent = "자동매매는 저장된 규칙으로 실행되며 AI를 자동 호출하지 않습니다.";
        return;
      }
      const status = $("#aiConnectionStatus");
      status.textContent = connection.connected ? "사용 가능" : "운영자 설정 필요";
      status.className = `status-pill ${connection.connected ? "ok" : "warn"}`;
      const provider = connection.provider || "공용 AI";
      const model = connection.model ? ` · ${connection.model}` : "";
      $("#aiConnectionSummary").textContent = connection.connected
        ? `${provider}${model}을(를) 서버 공용 설정으로 사용합니다. 회원 브라우저는 API 키를 받거나 전송하지 않습니다.`
        : "동아리 공용 AI가 아직 준비되지 않았습니다. 운영자가 broker 서버에서 공급자·모델·키를 설정해야 합니다.";
    }

    function renderMarketDataConnection() {
      const connection = getMarketDataConnection?.() || {connected: false, providers: []};
      if (window.MilkywayPersonal?.renderConnection(connection)) return;
      const status = $("#marketDataConnectionStatus");
      let manage = $("#marketDataManageLink");
      if (!manage) {
        manage = document.createElement("a");
        manage.id = "marketDataManageLink";
        manage.textContent = "개인 증권사 API 연결·관리";
        manage.rel = "noreferrer noopener";
        $("#marketDataConnectionSummary").after(manage);
      }
      manage.hidden = true;
      if (connection.usage_scope === "personal_paper_only") {
        status.textContent = connection.connected ? "개인 API 연결됨" : "개인 API 연결 필요";
        status.className = `status-pill ${connection.connected ? "ok" : "warn"}`;
        $("#marketDataConnectionSummary").textContent = connection.connected
          ? `${connection.provider} · ${connection.environment}. 본인의 페이퍼 계좌에 사용합니다.`
          : "개인 증권사 API를 연결하면 본인의 전략으로 페이퍼 트레이딩을 시작할 수 있습니다.";
        if (connection.management === "credential_broker" && connection.management_url) {
          const url = new URL(connection.management_url);
          if (url.protocol === "https:") {
            manage.href = url.href;
            manage.hidden = false;
          }
        }
        return;
      }
      status.textContent = connection.connected ? "공용 피드 설정됨" : "운영자 설정 필요";
      status.className = `status-pill ${connection.connected ? "ok" : "warn"}`;
      const environment = connection.environment ? ` · ${connection.environment}` : "";
      const transport = connection.transport === "rest_polling" ? "REST 주기 조회" : "데이터셋";
      $("#marketDataConnectionSummary").textContent = connection.connected
        ? `${connection.provider || "공용 시세"}${environment} · ${transport}. 증권사 키는 broker 서버에만 있고 페이퍼 엔진에는 정규화된 시세만 전달됩니다.`
        : "공용 시세가 아직 준비되지 않았습니다. 운영자가 공급자 권한을 확인한 뒤 broker 서버에서 활성화해야 합니다.";
    }

    function render() {
      const user = getUser();
      if (!user) return;
      const initial = (user.display_name || user.email || "M").trim().charAt(0).toUpperCase();
      $$('[data-profile-avatar]').forEach((element) => { element.textContent = initial; });
      $$('[data-profile-name]').forEach((element) => { element.textContent = user.display_name; });
      $$('[data-profile-email]').forEach((element) => { element.textContent = user.email; });
      const form = $("#profileSettingsForm");
      const preferences = getPreferences();
      form.default_market.value = preferences.default_market;
      renderAiConnection();
      renderMarketDataConnection();
    }

    function showTab(name) {
      $$('[data-profile-tab]').forEach((button) => button.classList.toggle("active", button.dataset.profileTab === name));
      $$('[data-profile-panel]').forEach((panel) => panel.classList.toggle("hidden", panel.dataset.profilePanel !== name));
      $("#profileDialogTitle").textContent = name === "settings" ? "설정" : "내 프로필";
    }

    function closeMenu() {
      $("#profileMenu").classList.add("hidden");
      $$('[data-open-profile]').forEach((button) => button.setAttribute("aria-expanded", "false"));
      activeTrigger = null;
    }

    function openMenu(trigger) {
      render();
      const menu = $("#profileMenu");
      if (activeTrigger === trigger && !menu.classList.contains("hidden")) {
        closeMenu();
        return;
      }
      closeMenu();
      activeTrigger = trigger;
      trigger.setAttribute("aria-expanded", "true");
      menu.classList.remove("hidden");
      const rect = trigger.getBoundingClientRect();
      const left = Math.max(12, Math.min(rect.right - menu.offsetWidth, window.innerWidth - menu.offsetWidth - 12));
      const top = Math.min(rect.bottom + 10, window.innerHeight - menu.offsetHeight - 12);
      menu.style.left = `${left}px`;
      menu.style.top = `${Math.max(12, top)}px`;
      menu.querySelector('[role="menuitem"]')?.focus();
    }

    function openDialog(tab = "info", targetId = null) {
      closeMenu();
      render();
      showTab(tab);
      const dialog = $("#profileDialog");
      if (!dialog.open) dialog.showModal();
      if (targetId) requestAnimationFrame(() => $("#" + targetId)?.focus({preventScroll: true}));
      if (tab === "settings") {
        const loads = [];
        if (!(getAiConnection?.()?.providers || []).length) loads.push(onAiLoad());
        if (!(getMarketDataConnection?.()?.providers || []).length) loads.push(onMarketDataLoad());
        if (loads.length) Promise.all(loads).then(render).catch(onError);
      }
    }

    function handleMenuAction(action) {
      if (action === "profile") openDialog("info");
      if (action === "settings") openDialog("settings");
      if (action === "logout") {
        closeMenu();
        onLogout();
      }
    }

    function bind() {
      $$('[data-open-profile]').forEach((button) => button.addEventListener("click", (event) => {
        event.stopPropagation();
        openMenu(button);
      }));
      $$('[data-profile-menu-action]').forEach((button) => button.addEventListener("click", () => handleMenuAction(button.dataset.profileMenuAction)));
      $$('[data-profile-tab]').forEach((button) => button.addEventListener("click", () => showTab(button.dataset.profileTab)));
      $("#profileSettingsForm").addEventListener("submit", (event) => {
        event.preventDefault();
        const preferences = Object.fromEntries(new FormData(event.target).entries());
        localStorage.setItem("milkyway_preferences", JSON.stringify(preferences));
        $("#profileDialog").close();
        onSave(preferences);
      });
      document.addEventListener("click", (event) => {
        if (!$("#profileMenu").contains(event.target)) closeMenu();
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeMenu();
      });
      window.addEventListener("resize", closeMenu, {passive: true});
      window.addEventListener("scroll", closeMenu, {passive: true, capture: true});
    }

    return {bind, render, openSettings: (targetId = null) => openDialog("settings", targetId)};
  }

  window.MilkywayProfile = {create, loadPreferences};
})();
