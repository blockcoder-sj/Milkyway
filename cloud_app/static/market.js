/* Display-only market views. No API calls, strategy changes, or credential access. */
(() => {
  const $ = (selector) => document.querySelector(selector);
  const escape = window.MilkywayFormat.escapeHtml;
  const finite = value => typeof value === "number" && Number.isFinite(value);
  const number = (value, digits = 2) => finite(value) ? new Intl.NumberFormat("ko-KR", {maximumFractionDigits:digits}).format(value) : "—";
  const change = value => finite(value) ? `${value > 0 ? "+" : ""}${number(value)}%` : "—";
  const direction = value => !finite(value) || value === 0 ? "neutral" : value > 0 ? "positive" : "negative";
  const statuses = {realtime:"실시간 수신",polled:"증권사 현재값 · 15초 조회",reference:"증권사 참고 환율 · 1분 갱신",awaiting_source:"첫 수신 대기",unavailable:"수신 실패",stale:"갱신 지연 · 이전 값",delayed:"참고 시세 · 지연 가능",completed_close:"최근 종가 · 기준 시각 확인"};
  function time(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString("ko-KR", {month:"numeric",day:"numeric",hour:"2-digit",minute:"2-digit"});
  }
  function sparkline(values) {
    const points = (Array.isArray(values) ? values : []).slice(-400), valid=points.filter(finite);
    if (valid.length < 2) return '<div class="market-chart-empty">장중 차트 준비 중</div>';
    const low = Math.min(...valid), high=Math.max(...valid), span=high-low || Math.max(Math.abs(low)*0.0001,0.01);
    let connected=false;
    const path=points.map((value,index)=>{
      if(!finite(value)){connected=false;return '';}
      const command=connected?'L':'M';connected=true;
      return `${command}${(index/(points.length-1)*300).toFixed(2)},${(78-(value-low)/span*66).toFixed(2)}`;
    }).join(' ');
    return `<svg class="market-spark" viewBox="0 0 300 90" preserveAspectRatio="none" role="img" aria-label="최근 세션 장중 흐름 · 가격 범위에 맞춘 눈금"><path class="spark-grid" d="M0 12H300 M0 45H300 M0 78H300"/><path class="spark-line" d="${path}"/></svg>`;
  }
  function card(row, sector = false) {
    const stale = row.status === "stale" || row.status === "unavailable";
    const format = value => number(value, row.group === "fx" && row.unit === "USD" ? 4 : row.group === "fx" && row.unit === "JPY" ? 3 : 2);
    const label = sector ? escape(row.label) : `<a class="market-detail-link" data-market-detail="${escape(row.id)}" href="#detail/${encodeURIComponent(row.id)}">${escape(row.label)}</a>`;
    const chart = sector ? `<div class="market-chart-summary">${sparkline(row.sparkline)}</div>` : `<a class="market-chart-link" data-market-detail="${escape(row.id)}" data-chart-expand href="#detail/${encodeURIComponent(row.id)}" aria-label="${escape(row.label)} 차트 크게 보기">${sparkline(row.sparkline)}</a>`;
    return `<article class="market-card ${sector ? "sector-index-card sector-summary-card" : ""} ${stale ? "market-stale" : ""}" ${sector ? 'aria-disabled="true"' : `data-market-card="${escape(row.id)}"`}>
      <div class="market-card-top"><strong>${label}</strong><small>${escape(row.unit)}</small></div>
      <div class="market-price-line"><span class="market-value">${format(row.value)}</span><b class="market-change ${direction(row.change_pct)}">${change(row.change_pct)}</b></div>
      <div class="market-delta">전일 대비 ${finite(row.change) && row.change > 0 ? "+" : ""}${format(row.change)} ${escape(row.unit === "%" ? "%p" : row.unit)}</div>
      ${chart}
      ${stale?'<small class="market-stale-note">갱신 확인 필요</small>':''}</article>`;
  }
  const renderedCards = new WeakMap();
  function renderCards(selector, rows, sector = false) {
    const target = $(selector);
    const signature = JSON.stringify(rows);
    if (renderedCards.get(target) === signature) return;
    window.MilkywayMarketMethods.replace(target,rows.map(row => card(row, sector)).join(""));
    renderedCards.set(target, signature);
  }
  function renderMarket(overview, country) {
    const rows = overview?.items || [];
    $("#marketCards").classList.remove("empty-state");
    renderCards("#marketCards", rows.filter(row => row.group === "indices" && row.market === country));
    renderCards("#marketFx", rows.filter(row => row.group === "fx"));
    renderCards("#marketFutures", rows.filter(row => ["futures","commodities"].includes(row.group)));
    $("#leadingIndicatorLabel").textContent = "해외 선물·원자재";
    $("#marketUpdated").textContent = `${overview?.available_count || 0}/${overview?.total_count || rows.length}개 수신 · 최근 수집 ${time(overview?.attempted_at)}`;
    $("#marketFeedNote").textContent = overview?.note || "시장 데이터 수집을 기다리고 있습니다.";
  }
  function renderSectors(overview, country, sort = "desc") {
    const rows = (overview?.items || []).filter(row => row.group === "sectors" && row.market === country);
    rows.sort((a,b) => {
      if (sort === "name") return String(a.label).localeCompare(String(b.label), "ko");
      if (!finite(a.change_pct)) return finite(b.change_pct) ? 1 : 0;
      if (!finite(b.change_pct)) return -1;
      return (sort === "asc" ? 1 : -1) * (a.change_pct - b.change_pct);
    });
    $("#sectorHeatmapTitle").textContent = country === "kr" ? "한국 주요 업종 지수" : "미국 S&P 500 · 11개 섹터";
    $("#heatmapMeta").textContent = `${rows.filter(row => finite(row.value)).length}/${rows.length}개 수신 · 등락 요약`;
    $("#heatmapMethod").textContent = country === "kr"
      ? "증권사 우선으로 조회하고 Yahoo Finance로 보완하는 코스피 주요 8개 업종 지수입니다. 전체 업종 목록이 아니며 금융업과 증권·보험의 구성 범위는 겹칩니다. 기준 시각과 지연 여부를 확인하세요."
      : "Yahoo Finance가 제공하는 S&P 500의 GICS 11개 섹터 지수입니다. 지수값과 공급자 전일 기준값으로 등락률을 계산합니다. 기준 시각과 지연 여부를 확인하세요.";
    $("#sectorHeatmap").className = "sector-index-grid";
    renderCards("#sectorHeatmap", rows, true);
  }
  const detailAvailable = (id) => !/^(us_|kr_)/.test(String(id));
  window.MilkywayMarket = {renderMarket, renderSectors, detailAvailable};
})();
