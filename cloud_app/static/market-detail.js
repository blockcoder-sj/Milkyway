/* Detail navigation, escaped sources, and cached data presentation. */
(() => {
  const $=selector=>document.querySelector(selector);
  const methods=window.MilkywayMarketMethods;
  const movingAverages=window.MilkywayMarketChart.MOVING_AVERAGES;
  const esc=value=>window.MilkywayResearchView.escape(value);
  const fmt=(value,digits=2)=>Number.isFinite(value)?new Intl.NumberFormat('ko-KR',{maximumFractionDigits:digits}).format(value):'—';
  const cap=value=>fmt(value,0);
  const time=value=>value?new Date(value).toLocaleString('ko-KR'):'수신 대기';
  const date=value=>value.toISOString().slice(0,10);
  const safeUrl=value=>{try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;}catch{return null;}};
  const link=(label,url)=>safeUrl(url)?`<a href="${esc(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:esc(label);
  let hooks,identity=null,data=null,chart,loading=null,epoch=0,signature='';
  function mount(){
    const panel=document.createElement('section');panel.id='marketDetail';panel.className='panel market-detail-page hidden';panel.dataset.workspacePage='detail';
    panel.innerHTML=`<button id="detailBack" class="ghost compact">← 시장으로</button><div class="detail-heading"><div><p id="detailCategory" class="eyebrow"></p><h2 id="detailTitle">시장 상세</h2><p id="detailIntro"></p></div><div id="detailQuote"></div></div><div id="detailFacts" class="detail-metrics"></div><p id="detailError" class="error" role="alert"></p>
      <nav class="detail-jumps" aria-label="상세 정보 목차"><a href="#detailChartSection">차트</a><a id="detailCosmosJump" href="#energyCosmosSection" hidden>우주 관계도</a><a id="detailIndustryJump" href="#detailIndustrySection" hidden>산업 구조</a><a id="detailCompaniesJump" href="#detailCompaniesSection">구성·산출</a><a href="#detailNewsSection">뉴스</a><a href="#detailSourcesSection">출처 모음</a></nav>
      <section id="detailChartSection"><div class="detail-chart-heading"><h3>가격 차트</h3><button id="detailExpand" class="ghost compact">크게 보기 ↗</button></div><div id="detailChartHome"><div id="detailChartView" class="market-terminal">
        <div class="terminal-toolbar"><div id="detailPeriodButtons" class="chart-periods" role="group" aria-label="차트 기간">${[['1','1개월'],['3','3개월'],['6','6개월'],['12','1년'],['36','3년']].map(([value,label])=>`<button type="button" data-chart-period="${value}" aria-pressed="${value==='3'}">${label}</button>`).join('')}</div><label class="chart-interval">봉 주기<select id="detailInterval"><option value="day">일봉</option><option value="week">주봉</option><option value="month">월봉</option></select></label></div>
        <div class="terminal-series"><label>차트 자료<select id="detailSeries"><option value="history">표시 지수·시세</option></select></label><details id="detailChartSettings"><summary>설정</summary><div id="detailChartControls" class="detail-chart-controls">
          <label>기간<select id="detailPeriod"><option value="1">1개월</option><option value="3" selected>3개월</option><option value="6">6개월</option><option value="12">1년</option><option value="36">3년</option><option value="custom">직접 지정</option></select></label>
          <label>시작일<input id="detailStart" type="date"></label><label>종료일<input id="detailEnd" type="date"></label>
          <label>표시<select id="detailStyle"><option value="candle" selected>캔들</option><option value="line">선</option></select></label>
          <label>눈금<select id="detailScale"><option value="linear">일반</option><option value="log">로그</option></select></label>
          ${movingAverages.map(ma=>`<label class="detail-check"><input id="detailMA${ma.period}" type="checkbox" checked>${ma.period}봉 이동평균</label>`).join('')}<label class="detail-check"><input id="detailVolume" type="checkbox">거래량</label>
        </div></details></div>
        <div id="detailChartTooltip" class="chart-readout" aria-live="off"></div><div id="detailChartLegend" class="chart-ma-legend" aria-label="이동평균"></div>
        <svg id="detailChart" role="button" tabindex="0" aria-haspopup="dialog" aria-label="가격 차트 크게 보기"></svg>
        <div class="chart-footer"><span id="detailChartRange"></span><span>Yahoo Finance · 일봉 기준</span></div><p id="detailChartWarning" class="chart-data-note"></p><details class="chart-source"><summary>데이터 기준·출처</summary><p id="detailChartStatus"></p></details>
      </div></div><div id="detailMetrics" class="detail-metrics"></div><div id="detailChartMethod"></div><details><summary>최근 봉의 수치 보기</summary><div id="detailPriceTable" class="research-table"></div></details></section>
      <dialog id="detailChartDialog" aria-labelledby="detailDialogTitle"><header class="detail-dialog-heading"><h3 id="detailDialogTitle">가격 차트</h3><button id="detailCollapse" class="ghost compact" autofocus>닫기 · Esc</button></header><div id="detailChartDialogSlot"></div></dialog>
      <section id="detailIndustrySection" hidden></section>
      <section id="detailCompaniesSection"><h3 id="detailCompaniesTitle">주요 기업과 비중</h3><p id="detailCompanyNote" class="fineprint"></p><div id="detailCompanies"></div><div id="detailMarketShare"></div></section>
      <section id="detailNewsSection"><h3>관련 뉴스</h3><p class="fineprint">제목의 관련 키워드 조건을 통과한 지정 언론사의 최근 30일 보도를 최신 순으로 표시합니다. 한 페이지에 8건씩 제공하며 뒤로 갈수록 이전 보도가 나옵니다. 기사 제목과 원문 링크를 모으며, 검색에 잡히지 않거나 제목 조건에 맞지 않는 보도는 포함되지 않을 수 있습니다.</p><div id="detailNews"></div></section>
      <section id="detailSourcesSection"><details class="detail-sources-toggle"><summary id="detailSourceCount">출처 모음</summary><p class="fineprint">시세·기업·뉴스는 수집 시점, 사업 점유율은 발표 기준일을 따릅니다. 원자료를 확인하고 수치의 범위를 비교하세요.</p><div id="detailSources"></div></details></section>`;
    $('#market').after(panel);
    window.MilkywayMarketDirectory.initialize();
    chart=window.MilkywayMarketChart.create($('#detailChart'),$('#detailChartTooltip'),$('#detailChartLegend'));
    $('#detailBack').addEventListener('click',()=>{closeChart();identity=null;++epoch;hooks.openWorkspace('market');});
    $('#detailSeries').addEventListener('change',()=>{range();draw();});
    $('#detailPeriod').addEventListener('change',()=>{range();draw();});
    for(const id of ['detailStart','detailEnd'])$('#'+id).addEventListener('change',()=>{$('#detailPeriod').value='custom';draw();});
    $('#detailPeriodButtons').addEventListener('click',event=>{const button=event.target.closest('[data-chart-period]');if(!button)return;$('#detailPeriod').value=button.dataset.chartPeriod;range();draw();});
    for(const id of ['detailInterval','detailStyle','detailScale',...movingAverages.map(ma=>'detailMA'+ma.period),'detailVolume'])$('#'+id).addEventListener('change',draw);
    panel.querySelectorAll('.detail-jumps a').forEach(anchor=>anchor.addEventListener('click',event=>{event.preventDefault();$(anchor.getAttribute('href')).scrollIntoView({behavior:'smooth'});}));
    document.addEventListener('click',event=>{
      if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
      const anchor=event.target.closest('a[data-market-detail]');
      if(anchor){event.preventDefault();open(anchor.dataset.marketDetail,true,anchor.hasAttribute('data-chart-expand'));return;}
      const card=event.target.closest('[data-market-card]');
      // Keep disclosures, source links and text selection usable inside the card.
      if(!card||event.target.closest('a,button,input,select,textarea,label,details,[contenteditable]'))return;
      const selection=window.getSelection();
      if(selection&&!selection.isCollapsed&&card.contains(selection.anchorNode))return;
      event.preventDefault();open(card.dataset.marketCard);
    });

    $('#detailExpand').addEventListener('click',expandChart);
    $('#detailChart').addEventListener('click',expandChart);
    $('#detailChart').addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();expandChart();}});
    $('#detailCollapse').addEventListener('click',closeChart);
    $('#detailChartDialog').addEventListener('close',restoreChart);
    $('#detailChartDialog').addEventListener('click',event=>{if(event.target===$('#detailChartDialog'))closeChart();});
    let resizeFrame;
    new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(hooks.getState().workspace==='detail')draw();});}).observe($('#detailChart'));

  }
  let settingsOpen=true,chartFocus=null;
  function expandChart(){
    const dialog=$('#detailChartDialog');if(dialog.open||!data)return;
    chartFocus=document.activeElement;settingsOpen=$('#detailChartSettings').open;
    $('#detailChartSettings').open=false;
    $('#detailDialogTitle').textContent=$('#detailTitle').textContent+' · 확대 차트';
    $('#detailChartDialogSlot').append($('#detailChartView'));
    $('#detailChart').setAttribute('role','img');$('#detailChart').setAttribute('tabindex','-1');
    $('#detailChart').setAttribute('aria-label','선택 기간의 확대 가격 차트');
    dialog.showModal();document.body.classList.add('chart-dialog-open');requestAnimationFrame(draw);
  }
  function closeChart(){if($('#detailChartDialog').open)$('#detailChartDialog').close();}
  function restoreChart(){
    $('#detailChartHome').append($('#detailChartView'));$('#detailChartSettings').open=settingsOpen;
    $('#detailChart').setAttribute('role','button');$('#detailChart').setAttribute('tabindex','0');
    $('#detailChart').setAttribute('aria-label','가격 차트 크게 보기');
    document.body.classList.remove('chart-dialog-open');
    if(chartFocus?.isConnected)chartFocus.focus({preventScroll:true});requestAnimationFrame(draw);
  }
  function historyPart(){return data?.[$('#detailSeries').value]||data?.history;}
  function range(){
    if(!data)return;
    const rows=window.MilkywayMarketChart.validBars(historyPart().rows),last=rows.at(-1)?.date||date(new Date());
    const today=new Date(),minimum=new Date();minimum.setUTCFullYear(minimum.getUTCFullYear()-3);
    const earliest=rows[0]?.date||date(minimum);
    for(const id of ['detailStart','detailEnd']){$('#'+id).min=earliest;$('#'+id).max=date(today);}
    if($('#detailPeriod').value==='custom')return;
    const start=new Date(last+'T00:00:00Z');start.setUTCMonth(start.getUTCMonth()-Number($('#detailPeriod').value));
    $('#detailStart').value=date(start)<earliest?earliest:date(start);$('#detailEnd').value=last;
  }
  function draw(){
    if(!data)return;
    for(const button of $('#detailPeriodButtons').querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.chartPeriod===$('#detailPeriod').value));
    const start=$('#detailStart').value,end=$('#detailEnd').value;
    if(!start||!end||start>end||start<$('#detailStart').min||end>$('#detailEnd').max){$('#detailChartLegend').textContent='';$('#detailChartRange').textContent='';$('#detailChartWarning').textContent='사용 가능한 3년 이내의 시작·종료일을 확인하세요.';chart.draw([],{start,end});$('#detailMetrics').innerHTML='';$('#detailPriceTable').innerHTML='';$('#detailChartMethod').innerHTML='';return;}
    const part=historyPart(),related=$('#detailSeries').value==='related_history',subject=related?data.context.related_chart.label:data.label;
    $('#detailChartStatus').textContent=`${subject} · ${related?data.context.related_chart.unit:data.unit} · Yahoo Finance · 수집 ${time(part.fetched_at)} · ${part.stale?'갱신 지연 또는 수신 대기':'15분마다 갱신'}${part.error?' · '+part.error:''}${related?' · '+data.context.related_chart.note:''}${part.rows.length<2?' · 원자료가 부족해 장기 흐름을 표시할 수 없습니다.':''}`;
    const digits=data.group==='fx'?(data.unit==='USD'?4:data.unit==='JPY'?3:2):2;
    const result=chart.draw(part.rows,{start,end,digits,interval:$('#detailInterval').value,style:$('#detailStyle').value,scale:$('#detailScale').value,...Object.fromEntries(movingAverages.map(ma=>['ma'+ma.period,$('#detailMA'+ma.period).checked])),volume:$('#detailVolume').checked});
    const incomplete=result?.rows.filter(row=>row.open===null).length||0;
    $('#detailChartRange').textContent=result?`${result.rows[0].date} — ${result.rows.at(-1).date} · ${result.count}개 봉`:'';
    const unavailable=result?.averages.filter(ma=>!ma.values.some(Number.isFinite)).map(ma=>'MA '+ma.period)||[];
    $('#detailChartWarning').textContent=[
      related?'관련 ETF 가격 · 원래 지수와 구성·가중 방식이 다름':'',
      incomplete?`시가·고가·저가 불완전 ${incomplete}개 · 캔들 대신 종가 점 표시`:'',
      result?.count===1?'수신 자료 1개 · 기간 등락 계산 불가':'',
      unavailable.length?`${unavailable.join(' · ')}: 계산에 필요한 이전 봉 부족`:'',
      part.stale?'갱신 지연 · 데이터 기준·출처 확인':''
    ].filter(Boolean).join(' / ');
    methods.replace($('#detailMetrics'),result?[['change','기간 등락',fmt(result.change)+'%'],['high','기간 최고',fmt(result.high,digits)],['low','기간 최저',fmt(result.low,digits)],['drawdown','종가 최대 낙폭',fmt(result.drawdown)+'%']].map(([key,label,value])=>`<div><small>${label}</small><strong>${value}</strong>${methods.metric(key,result,digits)}</div>`).join(''):'');
    methods.replace($('#detailChartMethod'),methods.chart(part));
    $('#detailPriceTable').innerHTML=result?`<table><thead><tr><th>날짜</th><th>시가</th><th>고가</th><th>저가</th><th>종가</th><th>거래량</th></tr></thead><tbody>${result.rows.slice(-10).reverse().map(row=>`<tr><td>${row.date}</td>${['open','high','low','close','volume'].map(key=>`<td>${fmt(row[key],key==='volume'?0:digits)}</td>`).join('')}</tr>`).join('')}</tbody></table>`:'';
  }
  function quote(overview){
    const row=overview?.items.find(item=>item.id===identity);
    if(!row)return;
    const digits=row.group==='fx'?(row.unit==='USD'?4:row.unit==='JPY'?3:2):2;
    methods.replace($('#detailQuote'),`<strong>${fmt(row.value,digits)} <small>${esc(row.unit)}</small></strong><span>${fmt(row.change_pct)}% <small>전일 대비</small></span><small>${esc(row.source)} · ${row.is_realtime?'실시간 수신':esc(row.status==='stale'?'갱신 지연':'기준 시각 확인')}</small><small>기준 ${esc(time(row.observed_at))}</small>${row.fallback_reason?`<small>${esc(row.fallback_reason)}</small>`:''}${row.error?`<small class="error">${esc(row.error)}</small>`:''}<details class="market-detail"><summary>지표 정보</summary><dl><dt>전일 기준값</dt><dd>${fmt(row.previous_close,digits)}</dd><dt>당일 범위</dt><dd>${fmt(row.day_low,digits)} ~ ${fmt(row.day_high,digits)}</dd><dt>52주 범위</dt><dd>${fmt(row.year_low,digits)} ~ ${fmt(row.year_high,digits)}</dd></dl><p>수집 ${esc(time(row.fetched_at))}</p></details>${methods.quote(row)}`);
  }
  function render(){
    const context=data.context, companies=data.companies.rows;
    $('#detailCategory').textContent=({indices:'MARKET INDEX',sectors:'SECTOR RESEARCH',fx:'CURRENCIES',futures:'FUTURES',commodities:'COMMODITIES'})[data.group]||'MARKET';
    $('#detailTitle').textContent=data.label;$('#detailIntro').textContent=context.intro;
    $('#detailCompaniesJump').textContent=data.group==='sectors'?'기업·비중':'구성·산출';
    $('#detailFacts').innerHTML=context.facts.map(fact=>`<div><small>${esc(fact.label)}</small><p>${esc(fact.value)}</p></div>`).join('');
    const series=$('#detailSeries'),previous=series.value,initialized=series.dataset.identity===identity;
    series.innerHTML=`<option value="history">${esc(data.label)} · ${data.history.rows.length}개 일봉</option>`+(context.related_chart?`<option value="related_history">관련 ETF · ${esc(context.related_chart.label)}</option>`:'');
    series.value=initialized?previous:(data.history.rows.length<2&&data.related_history?.rows.length?'related_history':'history');series.dataset.identity=identity;
    quote(hooks.getState().dashboard?.market_overview);
    $('#detailCompaniesTitle').textContent=data.group==='sectors'?'섹터 기업 백과':data.group==='fx'?'통화정책 원문':data.group==='indices'?'구성·산출 원문':'계약 명세와 거래소';
    $('#detailCompanyNote').textContent=(context.companies_note||'이 항목의 공식 구성·관련 정보는 아래 산출기관 원문에서 확인할 수 있습니다.')+(companies.length?` 수집 ${time(data.companies.fetched_at)}${data.companies.stale?' · 갱신 지연':''}`:'');
    window.MilkywayMarketDirectory.render(data);
    $("#detailCosmosJump").hidden=!data.industry_guide;
    const shares=context.market_share||[];
    $('#detailMarketShare').innerHTML=shares.length?shares.map(share=>`<article class="detail-share-fact"><h4>${esc(share.title)}</h4><p>${esc(share.period)} · 발표 ${esc(share.published_at)} · 확인 ${esc(share.checked_at)}</p><p>${esc(share.scope)}</p><div class="detail-watchpoints">${share.values.map(row=>`<span>${esc(row.name)} <strong>${fmt(row.value)}%</strong></span>`).join('')}</div>${methods.help('published-share',['발표기관이 공표한 비율을 그대로 옮긴 값입니다. 앱에서 재계산하지 않습니다.','파운드리 사업 매출을 기준으로 한 점유율입니다. 개별 매출 원자료와 전체 분모는 앱에 저장되어 있지 않아 여기서 수치를 재현할 수 없습니다. 발표기관 원문의 조사 범위·산식을 확인하세요.'])}${link(share.provider+' 원자료',share.url)}</article>`).join(''):data.group==='sectors'?'<p class="fineprint">사업별 실제 시장점유율은 비교 범위·기준일을 확인한 자료가 있을 때만 제공합니다. 현재 이 업종의 검증된 수치는 등록되지 않았습니다.</p>':'';
    range();draw();
  }
  async function refresh(){
    if(loading===epoch||!identity||hooks.getState().workspace!=='detail')return;
    const current=identity,token=epoch,owner=hooks.getState().me?.id;loading=token;
    try{
      const next=await hooks.api('/api/market-details/'+encodeURIComponent(current));
      if(token!==epoch||current!==identity||owner!==hooks.getState().me?.id)return;
      const snapshot=JSON.stringify(next);data=next;
      $('#detailError').textContent='';
      if(snapshot!==signature){signature=snapshot;render();}
    }catch(error){if(token===epoch)$('#detailError').textContent=error.message;}
    finally{if(loading===token)loading=null;}
  }
  async function open(id,push=true,expanded=false){
    if(!/^[a-z0-9_]{1,30}$/.test(id)||!hooks.getState().config.personal_local_mode)return;
    if (!window.MilkywayMarket.detailAvailable(id)) {
      hooks.openWorkspace('market',false); history.replaceState(null,'','#market'); return;
    }
    closeChart();identity=id;data=null;signature='';++epoch;hooks.openWorkspace('detail',false);

    if(push)history.pushState(null,'','#detail/'+id);
    $('#detailTitle').textContent='상세 정보를 불러오고 있습니다';$('#detailError').textContent='';
    for(const selector of ['#detailFacts','#detailCategory','#detailCompanyNote','#detailChartStatus','#detailChartTooltip','#detailChartMethod','#detailChartLegend','#detailChartWarning','#detailChartRange','#detailQuote','#detailIntro','#detailCompanies','#detailMarketShare','#detailNews','#detailSources','#detailMetrics','#detailPriceTable','#detailChart'])$(selector).innerHTML='';
    $('#detailPeriod').value='3';$('#detailSeries').dataset.identity='';
    await refresh();if(expanded&&identity===id)expandChart();
  }
  window.MilkywayMarketDetail=Object.freeze({leave(){closeChart();identity=null;++epoch;},initialize(options){hooks=options;mount();setInterval(()=>{if(!document.hidden)refresh();},15000);},open,quote});
})();
