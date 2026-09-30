/* Detail navigation, escaped sources, and cached data presentation. */
(() => {
  const $=selector=>document.querySelector(selector);
  const esc=value=>window.MilkywayResearchView.escape(value);
  const fmt=value=>Number.isFinite(value)?new Intl.NumberFormat('ko-KR',{maximumFractionDigits:2}).format(value):'—';
  const cap=value=>Number.isFinite(value)?new Intl.NumberFormat('ko-KR',{notation:'compact',maximumFractionDigits:2}).format(value):'—';
  const time=value=>value?new Date(value).toLocaleString('ko-KR'):'수신 대기';
  const date=value=>value.toISOString().slice(0,10);
  const safeUrl=value=>{try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:null;}catch{return null;}};
  const link=(label,url)=>safeUrl(url)?`<a href="${esc(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:esc(label);
  let hooks,identity=null,data=null,chart,loading=null,epoch=0,signature='';
  function mount(){
    const panel=document.createElement('section');panel.id='marketDetail';panel.className='panel market-detail-page hidden';panel.dataset.workspacePage='detail';
    panel.innerHTML=`<button id="detailBack" class="ghost compact">← 시장으로</button><div class="detail-heading"><div><p id="detailCategory" class="eyebrow"></p><h2 id="detailTitle">시장 상세</h2><p id="detailIntro"></p></div><div id="detailQuote"></div></div><div id="detailFacts" class="detail-metrics"></div><p id="detailError" class="error" role="alert"></p>
      <nav class="detail-jumps" aria-label="상세 정보 목차"><a href="#detailChartSection">차트</a><a href="#detailCompaniesSection">기업·비중</a><a href="#detailNewsSection">뉴스·관찰점</a><a href="#detailSourcesSection">출처 모음</a></nav>
      <section id="detailChartSection"><h3>가격 흐름 · 최대 3년</h3><div id="detailChartControls" class="detail-chart-controls">
        <label>차트 자료<select id="detailSeries"><option value="history">표시 지수·시세</option></select></label><label>기간<select id="detailPeriod"><option value="1">1개월</option><option value="3">3개월</option><option value="6">6개월</option><option value="12" selected>1년</option><option value="36">3년</option><option value="custom">직접 지정</option></select></label>
        <label>시작일<input id="detailStart" type="date"></label><label>종료일<input id="detailEnd" type="date"></label>
        <label>봉 주기<select id="detailInterval"><option value="day">일봉</option><option value="week">주봉</option><option value="month">월봉</option></select></label>
        <label>표시<select id="detailStyle"><option value="line">선</option><option value="candle">캔들</option></select></label>
        <label>눈금<select id="detailScale"><option value="linear">일반</option><option value="log">로그</option></select></label>
        <label class="detail-check"><input id="detailMA20" type="checkbox">20봉 이동평균</label><label class="detail-check"><input id="detailMA60" type="checkbox">60봉 이동평균</label><label class="detail-check"><input id="detailVolume" type="checkbox">거래량</label>
      </div><p id="detailChartStatus" class="fineprint"></p><div id="detailMetrics" class="detail-metrics"></div><svg id="detailChart" viewBox="0 0 960 400" role="img" aria-label="선택 기간의 가격 차트"></svg><p id="detailChartTooltip" class="fineprint"></p><p class="fineprint">기간 등락은 첫 봉 종가 대비 마지막 봉 종가입니다. 배당·환전·거래비용은 포함하지 않습니다. 이동평균은 선택한 봉 주기와 기간 안에서 계산하며, 장중 마지막 봉은 미완료일 수 있습니다.</p><details><summary>최근 봉의 수치 보기</summary><div id="detailPriceTable" class="research-table"></div></details></section>
      <section id="detailCompaniesSection"><h3 id="detailCompaniesTitle">주요 기업과 비중</h3><p id="detailCompanyNote" class="fineprint"></p><div id="detailCompanies"></div><div id="detailMarketShare"></div></section>
      <section id="detailNewsSection"><h3>뉴스와 관찰할 지표</h3><div id="detailWatchpoints" class="detail-watchpoints"></div><p class="fineprint">관찰점은 일반적인 분석 항목입니다. 아래 보도는 출처를 제한해 최신순으로 모으며, 중요도나 주가 영향이 검증된 순위는 아닙니다. 보도 내용은 원문에서 확인하세요.</p><div id="detailNews"></div></section>
      <section id="detailSourcesSection"><h3>출처 모음</h3><p class="fineprint">시세·기업·뉴스는 수집 시점, 사업 점유율은 발표 기준일을 따릅니다. 원자료를 확인하고 수치의 범위를 비교하세요.</p><div id="detailSources"></div></section>`;
    $('#market').after(panel);
    chart=window.MilkywayMarketChart.create($('#detailChart'),$('#detailChartTooltip'));
    $('#detailBack').addEventListener('click',()=>{identity=null;++epoch;hooks.openWorkspace('market');});
    $('#detailSeries').addEventListener('change',()=>{range();draw();});
    $('#detailPeriod').addEventListener('change',()=>{range();draw();});
    for(const id of ['detailStart','detailEnd'])$('#'+id).addEventListener('change',()=>{$('#detailPeriod').value='custom';draw();});
    for(const id of ['detailInterval','detailStyle','detailScale','detailMA20','detailMA60','detailVolume'])$('#'+id).addEventListener('change',draw);
    panel.querySelectorAll('.detail-jumps a').forEach(anchor=>anchor.addEventListener('click',event=>{event.preventDefault();$(anchor.getAttribute('href')).scrollIntoView({behavior:'smooth'});}));
    document.addEventListener('click',event=>{const anchor=event.target.closest('a[data-market-detail]');if(!anchor||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();open(anchor.dataset.marketDetail);});
    addEventListener('popstate',()=>{const match=location.hash.match(/^#detail\/([a-z0-9_]+)$/);if(match)open(match[1],false);else if(identity){identity=null;++epoch;hooks.openWorkspace(location.hash==='#strategy'?'strategy':'market',false);}});
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
    const start=$('#detailStart').value,end=$('#detailEnd').value;
    if(!start||!end||start>end||start<$('#detailStart').min||end>$('#detailEnd').max){$('#detailChartStatus').textContent='사용 가능한 3년 이내의 시작·종료일을 확인하세요.';chart.draw([],{start,end});$('#detailMetrics').innerHTML='';$('#detailPriceTable').innerHTML='';return;}
    const part=historyPart(),related=$('#detailSeries').value==='related_history',subject=related?data.context.related_chart.label:data.label;
    $('#detailChartStatus').textContent=`${subject} · ${related?data.context.related_chart.unit:data.unit} · Yahoo Finance · 수집 ${time(part.fetched_at)} · ${part.stale?'갱신 지연 또는 수신 대기':'15분마다 갱신'}${part.error?' · '+part.error:''}${related?' · '+data.context.related_chart.note:''}${part.rows.length<2?' · 원자료가 부족해 장기 흐름을 표시할 수 없습니다.':''}`;
    const result=chart.draw(part.rows,{start,end,interval:$('#detailInterval').value,style:$('#detailStyle').value,scale:$('#detailScale').value,ma20:$('#detailMA20').checked,ma60:$('#detailMA60').checked,volume:$('#detailVolume').checked});
    $('#detailMetrics').innerHTML=result?[['기간 등락',fmt(result.change)+'%'],['기간 최고',fmt(result.high)],['기간 최저',fmt(result.low)],['종가 최대 낙폭',fmt(result.drawdown)+'%']].map(([label,value])=>`<div><small>${label}</small><strong>${value}</strong></div>`).join(''):'';
    $('#detailPriceTable').innerHTML=result?`<table><thead><tr><th>날짜</th><th>시가</th><th>고가</th><th>저가</th><th>종가</th><th>거래량</th></tr></thead><tbody>${result.rows.slice(-10).reverse().map(row=>`<tr><td>${row.date}</td>${['open','high','low','close','volume'].map(key=>`<td>${fmt(row[key])}</td>`).join('')}</tr>`).join('')}</tbody></table>`:'';
  }
  function quote(overview){
    const row=overview?.items.find(item=>item.id===identity);
    if(!row)return;
    $('#detailQuote').innerHTML=`<strong>${fmt(row.value)} <small>${esc(row.unit)}</small></strong><span>${fmt(row.change_pct)}% <small>전일 대비</small></span><small>${esc(row.source)} · ${row.is_realtime?'실시간 수신':esc(row.status==='stale'?'갱신 지연':'기준 시각 확인')}</small><small>기준 ${esc(time(row.observed_at))}</small>`;
  }
  function render(){
    const context=data.context, companies=data.companies.rows.slice(0,8),news=data.news.rows.slice(0,8);
    $('#detailCategory').textContent=({indices:'MARKET INDEX',sectors:'SECTOR RESEARCH',fx:'CURRENCIES',futures:'FUTURES',commodities:'COMMODITIES'})[data.group]||'MARKET';
    $('#detailTitle').textContent=data.label;$('#detailIntro').textContent=context.intro;
    $('#detailFacts').innerHTML=context.facts.map(fact=>`<div><small>${esc(fact.label)}</small><p>${esc(fact.value)}</p></div>`).join('');
    const series=$('#detailSeries'),previous=series.value,initialized=series.dataset.identity===identity;
    series.innerHTML=`<option value="history">${esc(data.label)} · ${data.history.rows.length}개 일봉</option>`+(context.related_chart?`<option value="related_history">관련 ETF · ${esc(context.related_chart.label)}</option>`:'');
    series.value=initialized?previous:(data.history.rows.length<2&&data.related_history?.rows.length?'related_history':'history');series.dataset.identity=identity;
    quote(hooks.getState().dashboard?.market_overview);
    $('#detailCompaniesTitle').textContent=data.group==='sectors'?'주요 기업과 비중':data.group==='fx'?'통화정책 원문':data.group==='indices'?'구성·산출 원문':'계약 명세와 거래소';
    $('#detailCompanyNote').textContent=(context.companies_note||'이 항목의 공식 구성·관련 정보는 아래 산출기관 원문에서 확인할 수 있습니다.')+(companies.length?` 수집 ${time(data.companies.fetched_at)}${data.companies.stale?' · 갱신 지연':''}`:'');
    $('#detailCompanies').innerHTML=companies.length?`<p class="fineprint">비중 = 이 표의 기업 시총 ÷ 표시 기업 시총 합계. 제품·매출 시장점유율이나 공식 지수 비중과는 다릅니다.</p><div class="research-table"><table><thead><tr><th>기업</th><th>시가총액</th><th>표시 기업 내 비중</th><th>출처</th></tr></thead><tbody>${companies.map(row=>`<tr><td>${esc(row.name)}<small>${esc(row.symbol)}</small></td><td>${cap(row.market_cap)} ${esc(row.currency)}</td><td>${fmt(row.displayed_share_pct)}%${Number.isFinite(row.displayed_share_pct)?`<div class="detail-share-bar"><i style="width:${Math.min(100,Math.max(0,row.displayed_share_pct))}%"></i></div>`:''}</td><td>${link(row.source,row.url)}</td></tr>`).join('')}</tbody></table></div>`:data.group==='sectors'?'<p class="fineprint">기업 수치 수신 대기 · 출처 모음에서 원자료를 확인하세요.</p>':context.sources.filter(row=>row.kind!=='시세').map(row=>`<p>${link(row.label,row.url)}</p>`).join('');
    const shares=context.market_share||[];
    $('#detailMarketShare').innerHTML=shares.length?shares.map(share=>`<article class="detail-share-fact"><h4>${esc(share.title)}</h4><p>${esc(share.period)} · 발표 ${esc(share.published_at)} · 확인 ${esc(share.checked_at)}</p><p>${esc(share.scope)}</p><div class="detail-watchpoints">${share.values.map(row=>`<span>${esc(row.name)} <strong>${fmt(row.value)}%</strong></span>`).join('')}</div>${link(share.provider+' 원자료',share.url)}</article>`).join(''):data.group==='sectors'?'<p class="fineprint">사업별 실제 시장점유율은 비교 범위·기준일을 확인한 자료가 있을 때만 제공합니다. 현재 이 업종의 검증된 수치는 등록되지 않았습니다.</p>':'';
    $('#detailWatchpoints').innerHTML=context.watchpoints.map(value=>`<span>${esc(value)}</span>`).join('');
    $('#detailNews').innerHTML=`<p class="fineprint">수집 ${esc(time(data.news.fetched_at))} · 최근 14일 · ${esc(data.news.source||'Google News · 지정 언론사')}${data.news.stale?' · 갱신 지연':''}</p>`+(news.length?news.map(item=>`<article class="detail-news-item">${link(item.title,item.url)}<small>${esc(item.publisher)} · ${esc(time(item.published_at))}</small></article>`).join(''):'<p class="fineprint">현재 출처·기간 조건을 충족하는 관련 보도가 없습니다.</p>');
    const sources=[...context.sources,...companies.map(row=>({label:row.name+' · '+row.source,url:row.url,kind:'기업'})),...shares.map(row=>({label:row.provider+' · '+row.title,url:row.url,kind:'시장점유율'})),...news.map(row=>({label:row.publisher+' · '+row.title,url:row.url,kind:'보도'}))];
    const unique=[...new Map(sources.map(row=>[row.url,row])).values()];
    $('#detailSources').innerHTML=unique.map(row=>`<p><small>${esc(row.kind)}</small> ${link(row.label,row.url)}</p>`).join('');
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
  async function open(id,push=true){
    if(!/^[a-z0-9_]{1,30}$/.test(id)||!hooks.getState().config.personal_local_mode)return;
    identity=id;data=null;signature='';++epoch;hooks.openWorkspace('detail',false);
    if(push)history.pushState(null,'','#detail/'+id);
    $('#detailTitle').textContent='상세 정보를 불러오고 있습니다';$('#detailError').textContent='';
    for(const selector of ['#detailFacts','#detailCategory','#detailCompanyNote','#detailChartStatus','#detailChartTooltip','#detailWatchpoints','#detailQuote','#detailIntro','#detailCompanies','#detailMarketShare','#detailNews','#detailSources','#detailMetrics','#detailPriceTable','#detailChart'])$(selector).innerHTML='';
    $('#detailPeriod').value='12';$('#detailSeries').dataset.identity='';
    await refresh();
  }
  window.MilkywayMarketDetail=Object.freeze({initialize(options){hooks=options;mount();setInterval(()=>{if(!document.hidden)refresh();},15000);},open,quote});
})();
