/* Coordinates the personal research view and transport. No provider calls on refresh. */
(() => {
  const $ = selector => document.querySelector(selector);
  const esc = value => window.MilkywayResearchView.escape(value);
  let hooks, api, view, tuning, room = null, owner = null;
  let busy = false, loading = false, epoch = 0, startingNew = false;
  let messageId = null, experimentId = null, deployId = null;

  function render() { view.render(room, busy); tuning.render(room, busy); $("#researchSessions").value = room?.id || ""; $("#researchRename").disabled = !room || busy; }
  function error(e) { $("#researchError").textContent = e.message; }
  function resetRequests() { messageId = experimentId = deployId = null; }
  function sessionOptions(rows) {
    $("#researchSessions").innerHTML = rows.length
      ? rows.map(r => `<option value="${esc(r.id)}">${esc(r.title)}</option>`).join("")
      : '';
    $("#researchSessions").innerHTML = '<option value="">새 대화</option>' + $("#researchSessions").innerHTML;
    $("#researchSessions").value = room?.id || "";
  }
  async function reload() {
    if (!room) return;
    const id = room.id, actor = owner;
    const result = await api.session(id);
    if (room?.id === id && hooks.getState().me?.id === actor) {
      room = result;
      render();
    }
  }
  async function act(action) {
    if (busy) return;
    busy = true;
    ++epoch; // Any older background response must not overwrite this action.
    $("#researchError").textContent = "";
    const controls = [...$("#researchPanel").querySelectorAll("button,select")];
    const disabled = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    $("#researchTuningFields").disabled = true;
    try { await action(); }
    catch (e) {
      error(e);
      try { await reload(); } catch { /* Retain the original actionable error. */ }
    } finally {
      busy = false;
      controls.forEach((control, i) => { control.disabled = disabled[i]; });
      view.invalidate();
      render();
    }
  }
  function bindForms() {
    let renameId = null;
    $('#researchRename').addEventListener('click', () => {
      if (!room || busy) return;
      renameId = room.id;
      $('#researchRenameForm').elements.title.value = room.title;
      $('#researchRenameError').textContent = '';
      $('#researchRenameDialog').showModal();
      $('#researchRenameForm').elements.title.focus();
    });
    $('#researchRenameCancel').addEventListener('click', () => $('#researchRenameDialog').close());
    $('#researchRenameForm').addEventListener('submit', async event => {
      event.preventDefault();
      const title = event.target.elements.title.value.trim(), actor = owner;
      if (!title) { $('#researchRenameError').textContent = '대화 이름을 입력해 주세요'; return; }
      const button = event.target.querySelector('button[type=submit]');
      button.disabled = true;
      try {
        const renamed = await api.rename(renameId, title);
        if (owner !== actor || room?.id !== renamed.id) return;
        room.title = renamed.title;
        sessionOptions(await api.sessions());
        $('#researchRenameDialog').close();
        hooks.toast('대화 이름을 변경했습니다');
      } catch (e) { $('#researchRenameError').textContent = e.message; }
      finally { button.disabled = false; }
    });
    $("#researchStart").addEventListener("click", () => act(async () => {
      tuning.requireSaved();
      startingNew = true; room = null; tuning.reset(); resetRequests();
      $("#researchMessage").reset(); $("#researchSessions").value = "";
      view.invalidate(); render();
    }));
    $("#researchTuningForm").addEventListener("input", () => tuning.markDirty());
    $("#researchTuneReset").addEventListener("click", () => { tuning.reset(); render(); });
    $("#researchTuningForm").addEventListener("submit", event => {
      event.preventDefault();
      let adjustment;
      try { adjustment = tuning.read(); } catch (e) { error(e); return; }
      act(async () => {
        room = await api.adjust(room.id, adjustment.id, adjustment.body);
        tuning.reset(); view.invalidate(); render();
        await hooks.refresh(); hooks.toast("운용 설정을 새 전략 버전으로 저장했습니다. AI 호출은 없습니다.");
      });
    });
    $("#researchRefresh").addEventListener("click", refresh);
    $("#researchSessions").addEventListener("change", event => {
      const id = event.target.value;
      act(async () => {
        tuning.requireSaved();
        room = id ? await api.session(id) : null;
        startingNew = !id;
        tuning.reset();
        resetRequests();
        $("#researchMessage").reset();
        view.invalidate();
        render();
      });
    });
    $("#researchNew").addEventListener("submit", event => {
      event.preventDefault();
      const body = Object.fromEntries(new FormData(event.target));
      act(async () => {
        tuning.requireSaved();
        room = await api.createSession(body);
        startingNew = false;
        tuning.reset();
        resetRequests();
        event.target.reset();
        $("#researchMessage").reset();
        sessionOptions(await api.sessions());
        view.invalidate();
        render();
      });
    });
    $("#researchMessage").addEventListener("submit", event => {
      event.preventDefault();
      const prompt = event.target.elements.prompt.value;
      act(async () => {
        tuning.requireSaved();
        if (!room) {
          room = await api.createSession({title:prompt.trim().slice(0,60) || "새 전략 대화",objective:""});
          startingNew = false;
          sessionOptions(await api.sessions());
        }
        messageId ||= crypto.randomUUID();
        await api.prepare(room.id, {prompt, request_id: messageId});
        messageId = null;
        event.target.reset();
        await reload();
      });
    });
    $("#researchExperiment").addEventListener("submit", event => {
      event.preventDefault();
      // Capture before act() disables controls: FormData omits disabled selects.
      const body = Object.fromEntries(new FormData(event.target));
      const ids = [...document.querySelectorAll("[data-candidate]:checked")].map(input => input.value);
      act(async () => {
        if (!ids.length || ids.length > 4) throw new Error("1~4개 버전을 선택해 주세요");
        experimentId ||= crypto.randomUUID();
        await api.compare(room.id, {...body, strategy_ids: ids, request_id: experimentId});
        experimentId = null;
        await reload();
        hooks.toast("백테스트 큐에 추가했습니다");
      });
    });
    $("#researchDeploy").addEventListener("submit", event => {
      event.preventDefault();
      const body = Object.fromEntries(new FormData(event.target));
      act(async () => {
        deployId ||= crypto.randomUUID();
        await api.deploy(room.id, {...body, request_id: deployId});
        deployId = null;
        await reload();
        await hooks.refresh();
        hooks.toast("페이퍼 계좌를 만들었습니다. 아래 계좌 상태를 확인하세요");
      });
    });
    $("#researchPanel").addEventListener("click", event => {
      const button = event.target.closest("[data-research-action]");
      if (button) act(() => handleAction(button.dataset.researchAction, button.dataset.id));
    });
  }
  async function handleAction(action, id) {
    if (action === "history") return hooks.openAccountHistory(id);
    if (action === "select") { tuning.requireSaved(); await api.select(room.id, id); tuning.reset(); }
    else {
      const turn = room.turns.find(item => item.id === id);
      if (!turn) return;
      if (action === 'retry') {
        if (turn.status !== 'failed') return;
        const input=$('#researchMessage').elements.prompt;
        if (input.value.trim()&&input.value!==turn.prompt) throw new Error('작성 중인 가설을 먼저 저장하거나 비워 주세요');
        input.value=turn.prompt;input.focus();
        hooks.toast('가설을 가져왔습니다. 무료 미리보기 후 별도로 승인해 주세요.');return;
      }
      if (action === "approve") {
        const digest=turn.approval.request_digest;
        turn.status="running";view.invalidate();render();
        $("#researchTurns").setAttribute("aria-busy","true");
        try { await api.approve(id,digest); }
        finally { $("#researchTurns").setAttribute("aria-busy","false"); }
      }
      else if (action === "cancel") await api.cancel(id);
      else return;
    }
    await reload();
    await hooks.refresh();
  }
  async function refresh() {
    const state = hooks.getState(), personal = window.MilkywayPersonal.isPersonal();
    $("#researchPanel").classList.toggle("hidden", !personal || state.workspace !== "strategy");
    if (!personal) {
      $("#researchPanel").removeAttribute("data-workspace-page");
      return;
    }
    $("#researchPanel").dataset.workspacePage = "strategy";
    if (!state.me || busy || loading) return;
    if (owner !== state.me.id) {
      owner = state.me.id;
      room = null;
      resetRequests();
      tuning.reset();
      startingNew = false;
      view.invalidate();
      render();
    }
    loading = true;
    const token = ++epoch, actor = owner;
    try {
      const config = await api.configuration();
      const rows = await api.sessions();
      const id = room?.id || (!startingNew && rows[0]?.id);
      const nextRoom = id ? await api.session(id) : null;
      if (token !== epoch || busy || hooks.getState().me?.id !== actor) return;
      room = nextRoom;
      sessionOptions(rows);
      $("#researchConfig").textContent = `${config.model || "gpt-5.4-mini"} · 추론 ${config.reasoning || "none"} · ${config.configured ? "키 설정됨" : "Milkyway/.env에 OPENAI_API_KEY를 입력하고 앱을 재시작하세요"} · 호출마다 별도 승인. 자동매매 실행에는 AI 호출료가 들지 않습니다.`;
      render();
    } catch (e) {
      if (token === epoch) error(e);
    } finally { loading = false; }
  }
  window.MilkywayResearch = Object.freeze({
    initialize(options) {
      hooks = options;
      api = window.MilkywayResearchApi.create(hooks.api);
      view = window.MilkywayResearchView.create();
      window.MilkywayResearchPanel.mount();
      tuning = window.MilkywayResearchTuning.create();
      bindForms();
    },
    refresh,
  });
})();
