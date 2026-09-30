/* Portfolio editing is local and creates a new immutable version, without AI. */
(() => {
  const $ = selector => document.querySelector(selector);
  const esc = value => window.MilkywayResearchView.escape(value);
  const names = {momentum:"모멘텀",mean_reversion:"평균 회귀",low_volatility:"낮은 변동성",moving_average:"이동평균",volume_momentum:"거래량 모멘텀",rsi:"RSI"};
  function create() {
    let version = null, dirty = false, requestId = null;
    const field = (name, label, value, min, max, step = "any") => `<label>${esc(label)}<input name="${name}" type="number" value="${esc(value)}" min="${min}" max="${max}" step="${step}" required></label>`;
    function render(room, busy) {
      const next = room?.versions.find(item => item.id === room.selected_strategy_id);
      const blocked = busy || Boolean(room?.turns.some(turn => ["awaiting_approval","running"].includes(turn.status)));
      $("#researchTuningFields").disabled = blocked;
      $("#researchTuneSave").disabled = blocked || !dirty;
      $("#researchTuneReset").disabled = blocked || !dirty;
      if (dirty) return;
      if (version?.id === next?.id && version) return;
      version = next?.spec?.portfolio ? next : null;
      $("#researchTuningForm").hidden = !version;
      $("#researchTuningEmpty").hidden = Boolean(version);
      if (!version) return;
      const spec = version.spec, p = spec.portfolio, f = spec.filters;
      $("#researchTuneSummary").textContent = `v${version.number} · ${spec.name} · ${spec.symbols.join(", ")}`;
      $("#researchTuneDescription").textContent = `현재 저장 규칙: 총 투자 ${(p.investment_fraction ?? 1)*100}%, 종목당 상한 ${(p.max_position_fraction ?? 1)*100}%, 최대 ${p.max_positions}종목, ${p.rebalance_days}달력일마다 재평가. 손절은 ${p.stop_loss_pct === null ? '사용 안 함' : '평균 매입단가 대비 '+Math.abs(p.stop_loss_pct*100)+'% 하락 기준'}입니다. 시세 공백·지연 시 손실이 더 커질 수 있습니다.`;
      $("#researchTuningFields").innerHTML = `<div class="manual-grid">
        ${field("initial_cash","시작 자금 (USD)",p.initial_cash,1000,10000000)}
        ${field("investment_pct","전체 투자 비중 (%)",(p.investment_fraction ?? 1)*100,5,100)}
        ${field("position_pct","종목당 비중 상한 (%)",(p.max_position_fraction ?? 1)*100,1,100)}
        ${field("max_positions","최대 보유 종목",p.max_positions,1,20,1)}
        ${field("rebalance_days","리밸런싱 간격 (달력일)",p.rebalance_days,1,30,1)}
        <label>리밸런싱 방식<select name="rebalance_weights"><option value="true" ${p.rebalance_weights ? "selected" : ""}>종목 교체 + 동일 비중 재조정</option><option value="false" ${!p.rebalance_weights ? "selected" : ""}>종목만 교체 · 기존 수량 유지</option></select></label>
        ${field("cost_pct","편도 거래 비용 (%)",p.cost_per_side*100,0,2)}
        <label>손절<select name="stop_enabled"><option value="true" ${p.stop_loss_pct !== null ? "selected" : ""}>사용</option><option value="false" ${p.stop_loss_pct === null ? "selected" : ""}>사용 안 함</option></select></label>
        ${field("stop_pct","손절 하락률 (%)",Math.abs(p.stop_loss_pct ?? -0.05)*100,0.5,50)}
      </div><p class="fineprint">투자 비중을 종목 수로 나눈 동일 비중에 종목당 상한을 적용합니다. 남는 금액은 현금입니다. 기존 수량 유지 모드에서는 보유 종목 비중을 줄이지 않습니다. 휴장일이 겹치면 다음 거래 가능 시점에 실행합니다.</p>
      <details><summary>신호·종목 필터 세부 조정</summary><div class="manual-grid">
        ${field("min_price","최소 주가 (USD)",f.min_price,1,1000)}
        ${field("min_average_volume","최소 평균 거래량",f.min_average_volume,0,1000000000)}
        ${field("history_days","필요 이력 (거래일)",f.history_days,20,252,1)}</div>
        ${spec.factors.map((factor,index) => `<h5>${esc(names[factor.kind] || factor.kind)}</h5><div class="manual-grid">${field(`lookback_${index}`,"관찰 기간 (거래일)",factor.lookback,2,252,1)}${field(`weight_${index}`,"신호 가중치",factor.weight,-5,5)}</div>`).join("")}</details>`;
    }
    function read() {
      if (!version) throw new Error("먼저 대화에서 전략 버전을 만들어 주세요");
      const values = new FormData($("#researchTuningForm"));
      const number = name => { const value = Number(values.get(name)); if (!Number.isFinite(value)) throw new Error("조정할 숫자를 확인하세요"); return value; };
      requestId ||= crypto.randomUUID();
      return {id:version.id, body:{request_id:requestId,
        portfolio:{initial_cash:number("initial_cash"),investment_fraction:number("investment_pct")/100,
          max_position_fraction:number("position_pct")/100,max_positions:number("max_positions"),
          rebalance_days:number("rebalance_days"),rebalance_weights:values.get("rebalance_weights")==="true",
          cost_per_side:number("cost_pct")/100,stop_loss_pct:values.get("stop_enabled")==="true" ? -number("stop_pct")/100 : null},
        filters:{min_price:number("min_price"),min_average_volume:number("min_average_volume"),history_days:number("history_days")},
        factors:version.spec.factors.map((factor,index) => ({...factor,lookback:number(`lookback_${index}`),weight:number(`weight_${index}`)}))}};
    }
    return Object.freeze({render,read,isDirty:()=>dirty,
      markDirty(){ dirty=true; requestId=null; $("#researchTuneSave").disabled=false; $("#researchTuneReset").disabled=false; },
      reset(){ dirty=false; version=null; requestId=null; },
      requireSaved(){ if(dirty) throw new Error("조정 중인 설정을 새 버전으로 저장하거나 변경 취소한 뒤 진행해 주세요"); }});
  }
  window.MilkywayResearchTuning = Object.freeze({create});
})();
