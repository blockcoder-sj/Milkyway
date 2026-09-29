/* Escaped presentation only. Rendering never sends network requests. */
(() => {
  const $ = selector => document.querySelector(selector);
  const escape = value => String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]));
  const labels = Object.freeze({
    awaiting_approval: "승인 대기", running: "실행 중", completed: "완료",
    cancelled: "취소", expired: "승인 만료", failed: "실패", queued: "대기",
  });
  const status = value => escape(labels[value] || value);
  const metric = (values, key, suffix = "") => Number.isFinite(values?.[key])
    ? `${values[key].toFixed(2)}${suffix}` : "—";
  const empty = text => `<p class="fineprint">${escape(text)}</p>`;

  function approval(turn) {
    if (turn.status !== "awaiting_approval") return "";
    const value = turn.approval;
    return `<div class="research-approval">
      <strong>이 요청의 API 사용 승인</strong>
      <p>${escape(value.model)} · 추론 ${escape(value.reasoning)}<br>
        최대 1회 호출 · 출력 최대 ${escape(value.max_output_tokens)}토큰<br>
        전송 자료 ${escape(value.input_characters)}자 · 승인 유효 시간 15분</p>
      <p>가설, 최근 대화, 선택 전략과 실험·페이퍼 기록이 OpenAI에 전송됩니다. 실제 사용량에 따라 요금이 부과됩니다.</p>
      <details><summary>전송 내용 전체 보기</summary><pre>${escape(JSON.stringify(value.request, null, 2))}</pre></details>
      <button class="primary" data-research-action="approve" data-id="${escape(turn.id)}">이번 요청 1회 유료 호출 승인</button>
      <button class="ghost" data-research-action="cancel" data-id="${escape(turn.id)}">취소</button>
    </div>`;
  }
  function responseBody(turn) {
    if (!turn.response) return "";
    const points = [...(turn.response.limitations || []), ...(turn.response.next_steps || [])];
    return `<strong>AI</strong><p>${escape(turn.response.reply)}</p>
      <ul>${points.map(value => `<li>${escape(value)}</li>`).join("")}</ul>`;
  }
  function renderTurn(turn) {
    const usage = turn.usage
      ? `<small>사용 토큰: 입력 ${escape(turn.usage.input_tokens ?? "—")} / 출력 ${escape(turn.usage.output_tokens ?? "—")}</small>` : "";
    const running = turn.status === "running"
      ? "<p>응답을 기다리고 있습니다. 연결이 끊겨도 자동으로 재호출하지 않습니다.</p>" : "";
    return `<article class="research-turn"><strong>나 · ${status(turn.status)}</strong>
      <p>${escape(turn.prompt)}</p>${responseBody(turn)}
      ${turn.error ? `<p class="error">${escape(turn.error)}</p>` : ""}
      ${usage}${running}${approval(turn)}</article>`;
  }
  function renderVersion(version, room, selected, blocked) {
    const exportPath = `${window.MilkywayResearchApi.sessionPath(room.id)}/export/${encodeURIComponent(version.id)}`;
    return `<article class="research-version">
      <label><input type="checkbox" data-candidate value="${escape(version.id)}" ${selected.includes(version.id) ? "checked" : ""}>
        v${escape(version.number)} · ${escape(version.name)}</label>
      <small>${version.id === room.selected_strategy_id ? "현재 대화의 기준 버전" : ""}</small>
      <div><button class="ghost compact" data-research-action="select" data-id="${escape(version.id)}" ${blocked ? "disabled" : ""}>대화 기준으로 선택</button>
        <a href="${exportPath}" download>Python 코드</a></div>
      <details><summary>규칙·코드 확인</summary><pre>${escape(version.code_preview)}\n\n${escape(JSON.stringify(version.spec, null, 2))}</pre></details>
    </article>`;
  }
  function comparisonRow(candidate, segment, experiment, room) {
    const run = candidate[segment] || {};
    const version = room.versions.find(item => item.id === candidate.strategy_id);
    const leader = candidate.strategy_id === experiment.development_leader ? "· 개발 1위" : "";
    return `<tr>
      <td>v${escape(version?.number ?? "?")} ${leader} / ${segment === "development" ? "개발" : "검증"}</td>
      <td>${status(run.status)}${run.error ? `<small>${escape(run.error)}</small>` : ""}</td>
      <td>${metric(run.metrics, "return_pct", "%")}</td><td>${metric(run.metrics, "sharpe")}</td>
      <td>${metric(run.metrics, "mdd_pct", "%")}</td><td>${escape(run.metrics?.trade_count ?? "—")}</td>
    </tr>`;
  }
  function comparison(experiment, room) {
    const rows = experiment.candidates.flatMap(candidate => ["development", "validation"].map(
      segment => comparisonRow(candidate, segment, experiment, room))).join("");
    return `<article class="research-comparison">
      <strong>${escape(experiment.start_date)} ~ ${escape(experiment.end_date)} · ${status(experiment.status)}</strong>
      <p>검증 시작: ${escape(experiment.split_date)} · 개발 순위 기준: ${escape(experiment.objective)}</p>
      <div class="research-table"><table><thead><tr><th>버전 / 구간</th><th>상태</th><th>수익률</th>
        <th>샤프</th><th>최대 낙폭</th><th>거래 수</th></tr></thead><tbody>${rows}</tbody></table></div>
    </article>`;
  }
  function paper(account) {
    return `<p>페이퍼 · ${status(account.status)} · 최근 평가액 ${metric(account, "last_equity")} USD
      <button class="ghost compact" data-research-action="history" data-id="${escape(account.account_id)}">체결 기록</button></p>`;
  }
  function create() {
    let rendered = "";
    function render(room, busy) {
      $("#researchRoom").hidden = !room;
      if (!room) return;
      const snapshot = JSON.stringify(room);
      if (snapshot === rendered) return;
      rendered = snapshot;
      const selected = [...document.querySelectorAll("[data-candidate]:checked")].map(input => input.value);
      const deploy = $("#researchDeploy").elements.strategy_id;
      const previousDeployment = deploy.value;
      const blocked = room.turns.some(turn => ["awaiting_approval", "running"].includes(turn.status));
      $("#researchTurns").innerHTML = room.turns.length ? room.turns.map(renderTurn).join("")
        : empty("종목과 가설을 입력하면 대화를 시작할 수 있습니다.");
      $("#researchMessage button").disabled = blocked || busy;
      $("#researchVersions").innerHTML = room.versions.length
        ? room.versions.map(version => renderVersion(version, room, selected, blocked)).join("")
        : empty("AI가 전략을 제안하면 검증된 버전이 저장됩니다.");
      deploy.innerHTML = room.versions.map(version =>
        `<option value="${escape(version.id)}">v${escape(version.number)} · ${escape(version.name)}</option>`).join("");
      deploy.value = room.versions.some(version => version.id === previousDeployment)
        ? previousDeployment : room.selected_strategy_id || "";
      $("#researchDeploy button").disabled = !room.versions.length || busy;
      $("#researchPaper").innerHTML = room.paper.map(paper).join("");
      $("#researchExperiments").innerHTML = room.experiments.length
        ? room.experiments.map(experiment => comparison(experiment, room)).join("")
        : empty("아직 비교 실험이 없습니다.");
    }
    return Object.freeze({render, invalidate() { rendered = ""; }});
  }
  window.MilkywayResearchView = Object.freeze({create, escape});
})();
