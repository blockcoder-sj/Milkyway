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

  function create({getUser, getPreferences, getAiConnection, onAiLoad, onAiSave, onAiDisconnect, onSave, onLogout, onError}) {
    let activeTrigger = null;

    function selectedProvider(connection, providerId) {
      return connection.providers?.find((provider) => provider.id === providerId) || connection.providers?.[0];
    }

    function updateModelOptions(connection, providerId, preferredModel = "") {
      const provider = selectedProvider(connection, providerId);
      const datalist = $("#aiModelOptions");
      datalist.innerHTML = (provider?.model_examples || []).map((model) => `<option value="${model}"></option>`).join("");
      const modelInput = $("#aiModel");
      modelInput.value = preferredModel || provider?.default_model || "";
      modelInput.readOnly = provider?.id === "local";
    }

    function updateKeyHelp(connection, providerId) {
      const provider = selectedProvider(connection, providerId);
      const sameProvider = connection.connected && connection.provider === providerId;
      const requiresKey = provider?.requires_api_key !== false;
      const keyInput = $("#aiApiKey");
      $("#aiApiKeyField").classList.toggle("hidden", !requiresKey);
      keyInput.disabled = !requiresKey;
      keyInput.required = requiresKey && !sameProvider;
      keyInput.placeholder = sameProvider ? `${connection.key_hint} · 비워 두면 기존 키 유지` : "API 키 입력";
      if (!requiresKey) {
        $("#aiKeyHelp").textContent = !provider?.available
          ? provider?.disabled_reason || "로컬 AI 서버 설정이 필요합니다."
          : provider?.ready
            ? "API 키 없이 Milkyway 서버의 공용 로컬 모델을 사용합니다."
            : "로컬 AI 모델을 내려받거나 시작하는 중입니다. 준비 후 자동으로 연결됩니다.";
      } else {
        $("#aiKeyHelp").textContent = sameProvider
          ? `현재 ${connection.key_hint} 키가 저장되어 있습니다. 새 키를 입력하면 교체됩니다.`
          : "처음 연결하거나 공급자를 바꿀 때 API 키를 입력해야 합니다.";
      }
      $("#aiBillingNote").textContent = requiresKey
        ? "API 사용료와 한도는 선택한 공급자의 본인 계정에 적용됩니다."
        : "로컬 AI는 별도 API 사용료가 없으며 서버 자원을 함께 사용합니다.";
    }

    function renderAiConnection() {
      const connection = getAiConnection?.() || {connected: false, providers: []};
      const providerSelect = $("#aiProvider");
      providerSelect.innerHTML = (connection.providers || []).map((provider) => {
        const suffix = !provider.available ? " · 서버 설정 필요" : provider.ready ? "" : " · 모델 준비 중";
        return `<option value="${provider.id}" ${provider.available ? "" : "disabled"}>${provider.label}${suffix}</option>`;
      }).join("");
      const providerId = connection.provider || connection.providers?.[0]?.id || "";
      providerSelect.value = providerId;
      updateModelOptions(connection, providerId, connection.model || "");
      updateKeyHelp(connection, providerId);
      $("#aiApiKey").value = "";
      const status = $("#aiConnectionStatus");
      const selected = selectedProvider(connection, providerId);
      status.textContent = connection.connected
        ? "연결됨"
        : connection.configured && selected?.available
          ? "모델 준비 중"
          : connection.configured ? "서버 설정 필요" : "연결 필요";
      status.className = `status-pill ${connection.connected ? "ok" : "warn"}`;
      $("#aiDisconnectBtn").classList.toggle("hidden", !connection.configured);
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
      if (tab === "settings" && !(getAiConnection?.()?.providers || []).length) {
        Promise.resolve(onAiLoad()).then(render).catch(onError);
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
      $("#aiProvider").addEventListener("change", (event) => {
        const connection = getAiConnection?.() || {connected: false, providers: []};
        updateModelOptions(connection, event.target.value);
        updateKeyHelp(connection, event.target.value);
      });
      $("#aiConnectionForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = $("#aiConnectionSaveBtn");
        const original = button.textContent;
        button.disabled = true;
        button.textContent = "저장 중…";
        try {
          const values = Object.fromEntries(new FormData(event.target).entries());
          if (!values.api_key) delete values.api_key;
          await onAiSave(values);
          renderAiConnection();
        } catch (error) {
          onError(error);
        } finally {
          button.disabled = false;
          button.textContent = original;
        }
      });
      $("#aiDisconnectBtn").addEventListener("click", async () => {
        if (!window.confirm("저장된 AI 연결을 해제할까요?")) return;
        try {
          await onAiDisconnect();
          renderAiConnection();
        } catch (error) {
          onError(error);
        }
      });
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
