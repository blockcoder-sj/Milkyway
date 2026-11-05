/* Static structure only; all interactions belong to the controller. */
(() => {
  const $ = s => document.querySelector(s);
  function mount() {
    if ($("#researchPanel")) return;
    const panel = document.createElement("section");
    panel.id = "researchPanel"; panel.className = "panel research-panel hidden";
    panel.innerHTML = `<div class="section-head"><div><p class="eyebrow">AI RESEARCH</p><h3>대화로 만드는 나의 전략</h3></div><button id="researchRefresh" class="ghost compact" type="button">기록 새로고침</button></div>
      <p class="section-copy">가설을 편하게 이야기하고, 구체적인 규칙으로 발전시켜 보세요. 운용 설정은 옆에서 직접 조정할 수 있습니다.</p>
      <p id="researchConfig" class="fineprint"></p>
      <div class="research-toolbar"><label>이어갈 연구<select id="researchSessions"><option value="">새 연구를 만들어 주세요</option></select></label>
      <div class="research-session-actions"><button id="researchRename" class="ghost" type="button" disabled>이름 변경</button><button id="researchStart" class="ghost" type="button">새 대화 시작</button></div></div><details class="research-session-create"><summary>이름을 정해 대화 만들기</summary><form id="researchNew" class="stack"><label>연구 이름<input name="title" maxlength="100" required placeholder="예: 대형 기술주 추세 전략"></label><label>확인할 가설<textarea name="objective" maxlength="2000" rows="2" placeholder="대상 종목과 기대하는 효과"></textarea></label><button class="primary">연구 저장</button></form></details>
      <dialog id="researchRenameDialog" class="research-dialog" aria-labelledby="researchRenameTitle"><form id="researchRenameForm" class="stack"><h3 id="researchRenameTitle">대화 이름 변경</h3><label>대화 이름<input name="title" minlength="1" maxlength="100" required></label><p id="researchRenameError" class="error" role="alert"></p><div class="research-tune-actions"><button class="primary" type="submit">이름 저장</button><button id="researchRenameCancel" class="ghost" type="button">취소</button></div></form></dialog>
      <p id="researchError" class="error" role="alert"></p>
      <div id="researchRoom">
        <div class="research-columns"><div class="research-conversation"><header class="research-column-head"><h4>전략 파트너</h4><p class="fineprint">티커 지정 없이 미국 상장주식 전체에서 자동 선정합니다. 신호·진입·청산 규칙을 이야기해 주세요.</p></header><div id="researchTurns" class="research-turns" role="log" aria-live="polite" aria-label="전략 대화 기록"></div>
          <form id="researchMessage" class="stack"><label>전략 가설·수정 요청·결과 질문<textarea name="prompt" rows="4" maxlength="4000" required placeholder="예: 상승 추세인 주식 중 잠깐 눌린 종목을 사고 싶어. 어떤 조건부터 정하면 좋을까?"></textarea></label><button class="primary">전송 내용 확인</button><small>미리보기는 무료입니다. 다음 화면에서 1회 호출을 승인해야 AI에 전송됩니다.</small></form></div>
        <div class="research-inspector"><header class="research-column-head"><h4>운용 설정</h4><p class="fineprint">현재 저장한 전략의 비중·주기·손절을 조정하세요.</p></header>
          <p id="researchTuningEmpty" class="fineprint">대화에서 전략이 저장되면 비중·주기·손절·비용을 여기서 조정할 수 있습니다.</p>
          <form id="researchTuningForm" class="stack" hidden><strong id="researchTuneSummary"></strong><p id="researchTuneDescription" class="fineprint"></p><fieldset id="researchTuningFields"></fieldset><div class="research-tune-actions"><button id="researchTuneSave" class="primary" type="submit" disabled>새 버전으로 저장</button><button id="researchTuneReset" class="ghost" type="button" disabled>변경 취소</button></div><small>직접 조정은 AI 호출 없이 저장됩니다. 기존 페이퍼 계좌에는 자동 적용되지 않습니다.</small></form>
          <details><summary>전략 버전 · 코드 내려받기</summary><div id="researchVersions"></div></details><details><summary>후보 비교 실험</summary>
          <form id="researchExperiment" class="stack"><p class="fineprint">위에서 최대 4개 버전을 선택하세요. 각 기간은 최소 30일, 전체 370일 이내입니다. 일봉 준비가 완료되어야 실행할 수 있습니다.</p>
            <div class="manual-grid"><label>개발 시작일<input name="start_date" type="date" required></label><label>검증 시작일<input name="split_date" type="date" required></label><label>검증 종료일<input name="end_date" type="date" required></label><label>개발 순위 기준<select name="objective"><option value="sharpe">샤프 비율</option><option value="return_pct">수익률</option><option value="mdd_pct">최대 낙폭 최소화</option></select></label></div><button class="ghost">개발·검증 백테스트 실행</button></form></details>
        </div></div>
        <details class="research-workflow"><summary>검증 결과 · 페이퍼 트레이딩</summary><h4>실험 결과를 확인하고 대화로 개선</h4><p class="fineprint">개발 구간으로 후보를 고르고 검증 구간에서 확인합니다. 반복해서 확인한 검증 구간은 미사용 데이터가 아닙니다. 현재 선택 종목 기반의 탐색용 결과이며 생존편향이 있습니다. 수익을 보장하지 않습니다.</p><div id="researchExperiments" aria-live="polite"></div>
          <h4>선택한 버전으로 페이퍼 시작</h4><form id="researchDeploy" class="stack"><label>전략 버전<select name="strategy_id" required></select></label><label>계좌 이름<input name="name" minlength="2" maxlength="100" value="AI 연구 페이퍼" required></label><p class="fineprint">개발·검증 완료 및 검증 구간 거래 기록이 필요합니다. 계좌는 이 버전에 고정됩니다. 새 버전은 새 계좌에서 시작하세요.</p><button class="primary">페이퍼 계좌 생성·운용 시작</button></form><div id="researchPaper"></div></details><p class="fineprint">현재 실행 엔진은 미국 주식 일봉 기반 6종 신호 조합을 지원합니다. 다른 가설도 대화할 수 있지만, 지원되지 않는 주문·장중 조건은 구현 전까지 실행할 수 없습니다.</p>
      </div>`;
    $("#strategyLab").before(panel);
  }
  window.MilkywayResearchPanel = Object.freeze({mount});
})();
