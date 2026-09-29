/* Static structure only; all interactions belong to the controller. */
(() => {
  const $ = s => document.querySelector(s);
  function mount() {
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
  }
  window.MilkywayResearchPanel = Object.freeze({mount});
})();
