/* Persistent personal research. API spending happens only on the approval button. */
(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const post = (body) => ({method: "POST", body: JSON.stringify(body)});
  const status = {awaiting_approval:"승인 대기", running:"실행 중", completed:"완료", cancelled:"취소", expired:"승인 만료", failed:"실패", queued:"대기"};
  let hooks, room, busy = false, loading = false, owner = null, rendered = "", messageId = null, experimentId = null, deployId = null;
  const base = () => `/api/research/sessions/${encodeURIComponent(room.id)}`;
  const metric = (m, key, suffix = "") => Number.isFinite(m?.[key]) ? `${m[key].toFixed(2)}${suffix}` : "—";
  function error(e) { $("#researchError").textContent = e.message; }
  function setup() {
    if ($("#researchPanel")) return;
    const panel = document.createElement("section");
    panel.id = "researchPanel"; panel.className = "panel research-panel hidden";
    panel.innerHTML = `<div class="section-head"><div><p class="eyebrow">AI RESEARCH</p><h3>가설에서 페이퍼 트레이딩까지</h3></div><button id="researchRefresh" class="ghost compact" type="button">기록 새로고침</button></div>
      <p class="section-copy">가설 대화 → 전략 버전 → 기간별 비교 → 개선 → 선택한 버전으로 페이퍼 운용</p>
      <p id="researchConfig" class="fineprint"></p>
      <div class="research-toolbar"><label>이어갈 연구<select id="researchSessions"><option value="">새 연구를 만들어 주세요</option></select></label>
      <details><summary>새 연구 만들기</summary><form id="researchNew" class="stack"><label>연구 이름<input name="title" maxlength="100" required placeholder="예: 대형 기술주 추세 전략"></label><label>확인할 가설<textarea name="objective" maxlength="2000" rows="2" placeholder="대상 종목과 기대하는 효과"></textarea></label><button class="primary">연구 저장</button></form></details></div>
      <p id="researchError" class="error" role="alert"></p>
      <div id="researchRoom" hidden>
        <div class="research-columns"><div><h4>1. 가설과 개선 대화</h4><div id="researchTurns" class="research-turns" aria-live="polite"></div>
          <form id="researchMessage" class="stack"><label>전략 가설·수정 요청·결과 질문<textarea name="prompt" rows="4" maxlength="4000" required placeholder="예: AAPL, MSFT, NVDA 중 20일 모멘텀이 높은 2개를 매수하고, 5일마다 리밸런싱해줘"></textarea></label><button class="primary">요청 미리보기 만들기</button><small>미리보기는 무료입니다. 다음 화면에서 1회 호출을 승인해야 AI에 전송됩니다.</small></form></div>
        <div><h4>2. 저장된 전략 버전</h4><div id="researchVersions"></div><h4>3. 후보 비교</h4>
          <form id="researchExperiment" class="stack"><p class="fineprint">위에서 최대 4개 버전을 선택하세요. 각 기간은 최소 30일, 전체 370일 이내입니다. 일봉 준비가 완료되어야 실행할 수 있습니다.</p>
            <div class="manual-grid"><label>개발 시작일<input name="start_date" type="date" required></label><label>검증 시작일<input name="split_date" type="date" required></label><label>검증 종료일<input name="end_date" type="date" required></label><label>개발 순위 기준<select name="objective"><option value="sharpe">샤프 비율</option><option value="return_pct">수익률</option><option value="mdd_pct">최대 낙폭 최소화</option></select></label></div><button class="ghost">개발·검증 백테스트 실행</button></form>
        </div></div>
        <h4>4. 실험 결과를 확인하고 대화로 개선</h4><p class="fineprint">개발 구간으로 후보를 고르고 검증 구간에서 확인합니다. 반복해서 확인한 검증 구간은 미사용 데이터가 아닙니다. 현재 선택 종목 기반의 탐색용 결과이며 생존편향이 있습니다. 수익을 보장하지 않습니다.</p><div id="researchExperiments" aria-live="polite"></div>
          <h4>5. 선택한 버전으로 페이퍼 시작</h4><form id="researchDeploy" class="stack"><label>전략 버전<select name="strategy_id" required></select></label><label>계좌 이름<input name="name" minlength="2" maxlength="100" value="AI 연구 페이퍼" required></label><p class="fineprint">개발·검증 완료 및 검증 구간 거래 기록이 필요합니다. 계좌는 이 버전에 고정됩니다. 새 버전은 새 계좌에서 시작하세요.</p><button class="primary">페이퍼 계좌 생성·운용 시작</button></form><div id="researchPaper"></div>
      </div>`;
    $("#strategyLab").before(panel);
    $("#researchRefresh").addEventListener("click", () => refresh());
    $("#researchSessions").addEventListener("change", () => act(async () => {room = await hooks.api(`/api/research/sessions/${encodeURIComponent($("#researchSessions").value)}`); rendered=""; messageId=experimentId=deployId=null; $("#researchMessage").reset(); renderRoom();}));
    $("#researchNew").addEventListener("submit", e => {e.preventDefault(); act(async () => {room=await hooks.api("/api/research/sessions",post(Object.fromEntries(new FormData(e.target)))); e.target.reset(); rendered=""; await refreshList(); renderRoom();});});
    $("#researchMessage").addEventListener("submit", e => {e.preventDefault(); act(async () => {messageId ||= crypto.randomUUID(); await hooks.api(`${base()}/messages`,post({prompt:e.target.prompt.value,request_id:messageId})); messageId=null; e.target.reset(); await reload();});});
    $("#researchExperiment").addEventListener("submit", e => {e.preventDefault(); const values=Object.fromEntries(new FormData(e.target)); act(async () => {const ids=[...document.querySelectorAll('[data-candidate]:checked')].map(x=>x.value); if (!ids.length || ids.length>4) throw new Error("1~4개 버전을 선택해 주세요"); experimentId ||= crypto.randomUUID(); await hooks.api(`${base()}/experiments`,post({...values,strategy_ids:ids,request_id:experimentId})); experimentId=null; await reload(); hooks.toast("백테스트 큐에 추가했습니다");});});
    $("#researchDeploy").addEventListener("submit", e => {e.preventDefault(); const values=Object.fromEntries(new FormData(e.target)); act(async () => {deployId ||= crypto.randomUUID(); await hooks.api(`${base()}/deploy`,post({...values,request_id:deployId})); deployId=null; await reload(); await hooks.refresh(); hooks.toast("페이퍼 계좌를 만들었습니다. 아래 계좌 상태를 확인하세요");});});
    panel.addEventListener("click", e => {const b=e.target.closest("[data-research-action]"); if (!b) return; act(async () => {
      const {researchAction:action,id}=b.dataset;
      if (action==="history") {await hooks.openAccountHistory(id); return;}
      if (action==="select") {await hooks.api(`${base()}/select/${encodeURIComponent(id)}`,post({}));}
      else {const turn=room.turns.find(t=>t.id===id); if (!turn) return; await hooks.api(`/api/research/turns/${encodeURIComponent(id)}/${action}`,post(action==="approve"?{approved:true,request_digest:turn.approval.request_digest}:{}));}
      await reload(); await hooks.refresh();
    });});
  }
  function renderRoom() {
    $("#researchRoom").hidden = !room;
    if (!room) return;
    const snapshot=JSON.stringify(room);
    if (snapshot===rendered) return;
    rendered=snapshot;
    const selected=[...document.querySelectorAll('[data-candidate]:checked')].map(x=>x.value);
    const deployment=$("#researchDeploy").strategy_id.value;
    $("#researchTurns").innerHTML = room.turns.length ? room.turns.map(t=>`<article class="research-turn"><strong>나 · ${esc(status[t.status]||t.status)}</strong><p>${esc(t.prompt)}</p>${t.response?`<strong>AI</strong><p>${esc(t.response.reply)}</p><ul>${[...(t.response.limitations||[]),...(t.response.next_steps||[])].map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:""}${t.error?`<p class="error">${esc(t.error)}</p>`:""}${t.usage?`<small>사용 토큰: 입력 ${esc(t.usage.input_tokens??"—")} / 출력 ${esc(t.usage.output_tokens??"—")}</small>`:""}${t.status==="running"?"<p>응답을 기다리고 있습니다. 연결이 끊겨도 자동으로 재호출하지 않습니다.</p>":""}${t.status==="awaiting_approval"?`<div class="research-approval"><strong>이 요청의 API 사용 승인</strong><p>${esc(t.approval.model)} · 추론 ${esc(t.approval.reasoning)}<br>최대 1회 호출 · 출력 최대 ${esc(t.approval.max_output_tokens)}토큰<br>전송 자료 ${esc(t.approval.input_characters)}자 · 승인 유효 시간 15분</p><p>가설, 최근 대화, 선택 전략과 실험·페이퍼 기록이 OpenAI에 전송됩니다. 실제 사용량에 따라 요금이 부과됩니다.</p><details><summary>전송 내용 전체 보기</summary><pre>${esc(JSON.stringify(t.approval.request,null,2))}</pre></details><button class="primary" data-research-action="approve" data-id="${esc(t.id)}">이번 요청 1회 유료 호출 승인</button> <button class="ghost" data-research-action="cancel" data-id="${esc(t.id)}">취소</button></div>`:""}</article>`).join("") : '<p class="fineprint">종목과 가설을 입력하면 대화를 시작할 수 있습니다.</p>';
    const blocked=room.turns.some(t=>["awaiting_approval","running"].includes(t.status));
    $("#researchMessage button").disabled = blocked||busy;
    $("#researchVersions").innerHTML = room.versions.length ? room.versions.map(v=>`<article class="research-version"><label><input type="checkbox" data-candidate value="${esc(v.id)}" ${selected.includes(v.id)?"checked":""}> v${v.number} · ${esc(v.name)}</label><small>${v.id===room.selected_strategy_id?"현재 대화의 기준 버전":""}</small><div><button class="ghost compact" data-research-action="select" data-id="${esc(v.id)}" ${blocked?"disabled":""}>대화 기준으로 선택</button> <a href="${base()}/export/${encodeURIComponent(v.id)}" download>Python 코드</a></div><details><summary>규칙·코드 확인</summary><pre>${esc(v.code_preview)}\n\n${esc(JSON.stringify(v.spec,null,2))}</pre></details></article>`).join("") : '<p class="fineprint">AI가 전략을 제안하면 검증된 버전이 저장됩니다.</p>';
    const deploy=$("#researchDeploy").strategy_id;
    deploy.innerHTML=room.versions.map(v=>`<option value="${esc(v.id)}">v${v.number} · ${esc(v.name)}</option>`).join("");
    deploy.value=room.versions.some(v=>v.id===deployment)?deployment:room.selected_strategy_id||"";
    $("#researchDeploy button").disabled = !room.versions.length||busy;
    $("#researchPaper").innerHTML=room.paper.map(a=>`<p>페이퍼 · ${esc(a.status)} · 최근 평가액 ${metric(a,"last_equity")} USD <button class="ghost compact" data-research-action="history" data-id="${esc(a.account_id)}">체결 기록</button></p>`).join("");
    $("#researchExperiments").innerHTML=room.experiments.map(x=>`<article class="research-comparison"><strong>${esc(x.start_date)} ~ ${esc(x.end_date)} · ${esc(status[x.status]||x.status)}</strong><p>검증 시작: ${esc(x.split_date)} · 개발 순위 기준: ${esc(x.objective)}</p><div class="research-table"><table><thead><tr><th>버전 / 구간</th><th>상태</th><th>수익률</th><th>샤프</th><th>최대 낙폭</th><th>거래 수</th></tr></thead><tbody>${x.candidates.flatMap(c=>["development","validation"].map(segment=>{const run=c[segment]||{}; const v=room.versions.find(v=>v.id===c.strategy_id); return `<tr><td>v${v?.number??"?"} ${c.strategy_id===x.development_leader?"· 개발 1위":""} / ${segment==="development"?"개발":"검증"}</td><td>${esc(status[run.status]||run.status)}${run.error?`<small>${esc(run.error)}</small>`:""}</td><td>${metric(run.metrics,"return_pct","%")}</td><td>${metric(run.metrics,"sharpe")}</td><td>${metric(run.metrics,"mdd_pct","%")}</td><td>${esc(run.metrics?.trade_count??"—")}</td></tr>`;})).join("")}</tbody></table></div></article>`).join("")||'<p class="fineprint">아직 비교 실험이 없습니다.</p>';
  }
  async function reload() { if(room) {room=await hooks.api(base());renderRoom();} }
  async function refreshList() {
    const rows=await hooks.api("/api/research/sessions");
    $("#researchSessions").innerHTML=rows.length?rows.map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join(""):'<option value="">새 연구를 만들어 주세요</option>';
    if (room) $("#researchSessions").value=room.id;
    else if(rows.length) room=await hooks.api(`/api/research/sessions/${encodeURIComponent(rows[0].id)}`);
  }
  async function act(fn) {
    if (busy) return;
    busy=true; $("#researchError").textContent="";
    const controls=[...$("#researchPanel").querySelectorAll("button,select")];
    const disabled=controls.map(b=>b.disabled); controls.forEach(b=>b.disabled=true);
    try {await fn();} catch(e) {error(e); try{await reload();}catch{} }
    finally {busy=false;controls.forEach((b,i)=>b.disabled=disabled[i]); rendered="";renderRoom();}
  }
  async function refresh() {
    setup();
    const state=hooks.getState(), personal=window.MilkywayPersonal.isPersonal();
    $("#researchPanel").classList.toggle("hidden", !personal||state.workspace!=="strategy");
    if(!personal) {$("#researchPanel").removeAttribute("data-workspace-page");return;}
    $("#researchPanel").dataset.workspacePage="strategy";
    if(!state.me||busy||loading) return;
    loading=true;
    try {
      if(owner!==state.me.id){owner=state.me.id;room=null;rendered="";messageId=experimentId=deployId=null;}
      const config=await hooks.api("/api/research/config");
      $("#researchConfig").textContent=`${config.model||"gpt-5.4-mini"} · 추론 ${config.reasoning||"none"} · ${config.configured?"키 설정됨 (실제 호출 미확인)":"Milkyway/.env에 OPENAI_API_KEY를 입력하고 앱을 재시작하세요"} · 호출마다 별도 승인. 자동매매 실행에는 AI 호출료가 들지 않습니다.`;
      await refreshList(); await reload();renderRoom();
    }catch(e){error(e);}finally{loading=false;}
  }
  window.MilkywayResearch={initialize(options){hooks=options;setup();},refresh};
})();
