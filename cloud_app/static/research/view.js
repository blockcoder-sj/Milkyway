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
    ? `${window.MilkywayFormat.number(values[key],2,2)}${suffix}` : "—";
  const empty = text => `<p class="fineprint">${escape(text)}</p>`;
  const factorNames = Object.freeze({
    momentum:["모멘텀","수익률 높은 순","수익률 낮은 순"],
    mean_reversion:["평균 회귀","수익률 낮은 순","수익률 높은 순"],
    low_volatility:["낮은 변동성","변동성 낮은 순","변동성 높은 순"],
    moving_average:["이동평균 괴리","평균 대비 가격 높은 순","평균 대비 가격 낮은 순"],
    volume_momentum:["거래량 모멘텀","평균 대비 거래량 높은 순","평균 대비 거래량 낮은 순"],
    rsi:["RSI","RSI 높은 순","RSI 낮은 순"],
  });
  function executionRules(spec) {
    if (!spec?.portfolio || !spec?.filters || !Array.isArray(spec.factors) || !Array.isArray(spec.symbols)) return "";
    const p = spec.portfolio, f = spec.filters;
    const number = (value, decimals=0) => window.MilkywayFormat.number(value,decimals,decimals);
    const percent = value => `${number(value*100,2)}%`;
    const rows = [
      ["대상 종목", spec.symbols.join(", ")],
      ["초기 자금", `${number(p.initial_cash,2)} USD`],
      ["보유·배분", `전체 자산 기준 · 최대 ${number(p.max_positions)}종목 · 전체 투자 목표 ${percent(p.investment_fraction)} · 종목당 목표 상한 ${percent(p.max_position_fraction)} · 남는 자금은 현금`],
      ["리밸런싱", `${number(p.rebalance_days)}달력일 간격 · ${p.rebalance_weights ? "동일 목표 비중으로 재조정" : "교체 종목만 거래 · 유지 종목의 수량 유지"} · 휴장일에는 다음 거래 가능 시점에 실행`],
      ["손절", p.stop_loss_pct===null ? "사용 안 함" : `현재 평균 매입단가 대비 ${percent(Math.abs(p.stop_loss_pct))} 하락 기준`],
      ["거래 비용", `매수·매도 각각 ${percent(p.cost_per_side)}`],
      ["종목 필터", `가격 ${number(f.min_price,2)} USD 이상 · ${number(f.history_days)}거래일 이력 · 해당 기간 평균 거래량 ${number(f.min_average_volume)}주 이상`],
    ];
    const count = Math.min(p.max_positions, spec.symbols.length);
    if (count > 0 && Number.isFinite(p.investment_fraction) && Number.isFinite(p.max_position_fraction)) {
      const target = Math.min(p.investment_fraction / count, p.max_position_fraction);
      rows.splice(3, 0, ["비중 계산 예시", `${number(count)}종목이 모두 편입되면 전체 자산 기준 종목당 ${percent(target)} · 현금 ${percent(Math.max(0,1-count*target))} (비용 반영 전). 실제 비중은 체결 비용·가격 변동 및 기존 수량 유지 여부에 따라 달라집니다.`]);
    }
    const factors = spec.factors.map(factor => {
      const labels = factorNames[factor.kind] || [factor.kind,"높은 순","낮은 순"];
      return `<li>${escape(labels[0])} · ${escape(number(factor.lookback))}거래일 · 가중치 ${escape(number(factor.weight,2))} · ${escape(factor.weight===0 ? "점수에 반영 안 함" : labels[factor.weight>0 ? 1 : 2])}</li>`;
    }).join("");
    return `<details class="research-rules"><summary>실제 저장된 실행 규칙</summary><p>저장한 전략 데이터에서 표시합니다. 각 지표의 종목 간 순위에 가중치를 곱해 합산하고 높은 점수부터 선택합니다.</p><ul>${factors}</ul><div class="research-table"><table><tbody>${rows.map(([label,value])=>`<tr><th scope="row">${escape(label)}</th><td>${escape(value)}</td></tr>`).join("")}</tbody></table></div></details>`;
  }

  function approval(turn) {
    if (turn.status !== "awaiting_approval") return "";
    const value = turn.approval;
    return `<div class="research-approval">
      <strong>이 요청의 API 사용 승인</strong>
      <p>${escape(value.model)} · 추론 ${escape(value.reasoning)}<br>
        최대 1회 호출 · 출력 최대 ${window.MilkywayFormat.number(value.max_output_tokens,0)}토큰<br>
        전송 자료 ${window.MilkywayFormat.number(value.input_characters,0)}자 · 승인 유효 시간 15분</p>
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
  function renderTurn(turn, savedVersions) {
    const usage = turn.usage
      ? `<small>사용 토큰: 입력 ${window.MilkywayFormat.number(turn.usage.input_tokens,0)} / 출력 ${window.MilkywayFormat.number(turn.usage.output_tokens,0)}</small>` : "";
    const running = turn.status === "running"
      ? "<p>응답을 기다리고 있습니다. 연결이 끊겨도 자동으로 재호출하지 않습니다.</p>" : "";
    return `<article class="research-turn"><div class="research-user"><strong>나 · ${status(turn.status)}</strong>
      <p>${escape(turn.prompt)}</p></div><div class="research-assistant">${turn.error&&turn.response?'<small>확인된 대화 내용 · 이 응답의 전략은 저장하지 않았습니다</small>':''}${responseBody(turn)}
      ${turn.error ? `<p class="error">${escape(turn.error)}</p>` : ""}
      ${turn.diagnostic?`<details><summary>오류 상세</summary><p>분류: ${escape(turn.diagnostic.code)}${turn.diagnostic.http_status?' · HTTP '+escape(turn.diagnostic.http_status):''}${Number.isFinite(turn.diagnostic.elapsed_ms)?' · '+window.MilkywayFormat.number(turn.diagnostic.elapsed_ms/1000)+'초':''}</p>${turn.diagnostic.request_id?`<p>OpenAI 요청 ID: ${escape(turn.diagnostic.request_id)}</p>`:''}</details>`:''}
      ${turn.status==='completed' && turn.strategy_id ? executionRules(savedVersions.get(turn.strategy_id)?.spec) : ""}
      ${usage}${running}${approval(turn)}${turn.status==='failed'?`<button class="ghost compact" data-research-action="retry" data-id="${escape(turn.id)}">가설 다시 가져오기</button><small>가설을 입력 칸에 복사합니다. 다시 전송하면 새 미리보기와 별도 승인이 필요합니다.</small>`:''}</div></article>`;
  }
  function renderVersion(version, room, selected, blocked) {
    const exportPath = `${window.MilkywayResearchApi.sessionPath(room.id)}/export/${encodeURIComponent(version.id)}`;
    return `<article class="research-version">
      <label><input type="checkbox" data-candidate value="${escape(version.id)}" ${selected.includes(version.id) ? "checked" : ""}>
        v${escape(version.number)} · ${escape(version.name)}</label>
      <small>${version.id === room.selected_strategy_id ? "현재 대화의 기준 버전" : ""}</small>
      <div><button class="ghost compact" data-research-action="select" data-id="${escape(version.id)}" ${blocked ? "disabled" : ""}>대화 기준으로 선택</button>
        <a href="${exportPath}" download>Python 코드</a></div>
      ${executionRules(version.spec)}<details><summary>규칙·코드 확인</summary><pre>${escape(version.code_preview)}\n\n${escape(JSON.stringify(version.spec, null, 2))}</pre></details>
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
      <td>${metric(run.metrics, "mdd_pct", "%")}</td><td>${window.MilkywayFormat.number(run.metrics?.trade_count,0)}</td>
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
      $("#researchRoom").hidden = false;
      room ||= {id:"",selected_strategy_id:null,turns:[],versions:[],experiments:[],paper:[]};
      const snapshot = JSON.stringify([room,busy]);
      if (snapshot === rendered) return;
      rendered = snapshot;
      const selected = [...document.querySelectorAll("[data-candidate]:checked")].map(input => input.value);
      const deploy = $("#researchDeploy").elements.strategy_id;
      const previousDeployment = deploy.value;
      const blocked = room.turns.some(turn => ["awaiting_approval", "running"].includes(turn.status));
      const savedVersions = new Map(room.versions.map(version=>[version.id,version]));
      $("#researchTurns").innerHTML = room.turns.length ? room.turns.map(turn=>renderTurn(turn,savedVersions)).join("")
        : empty("어떤 투자 아이디어를 실험해 보고 싶으세요? 아직 종목이나 규칙을 정하지 않았다면, 기대하는 효과부터 이야기해 주세요.");
      $("#researchMessage button").disabled = blocked || busy;
      $("#researchVersions").innerHTML = room.versions.length
        ? room.versions.map(version => renderVersion(version, room, selected, blocked || busy)).join("")
        : empty("AI가 전략을 제안하면 실행 형식에 맞는 버전이 저장됩니다. 성과 검증은 별도로 진행하세요.");
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
  window.MilkywayResearchView = Object.freeze({create, escape, executionRules});
})();
