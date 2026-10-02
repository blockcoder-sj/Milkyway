/* Cached primary company research. Public collection is queued separately from AI. */
(() => {
  const $=s=>document.querySelector(s),esc=v=>window.MilkywayResearchView.escape(v),fmt=(v,d=2)=>window.MilkywayFormat.number(v,d);
  const relationView=window.MilkywayCompanyRelations,kinds=relationView.kinds;
  const level={primary:'공시·기업 원문',provider:'정보 제공사·공개 조사'};
  let reading=null,revenueGroup=null,network=null,prices=null;
  let hooks,sector=null,symbol=null,entityKey=null,loadPath=null,data=null,epoch=0,loading=null,signature='',relationPage=1,productPage=1,peerPage=1,selected=null;
  const validKey=value=>/^c_[a-f0-9]{32}$/.test(value||'');
  const companyLink=(edge,label=edge.name)=>validKey(edge.target_id)?`<a class="company-open" data-company-id="${esc(edge.target_id)}" href="#company/${edge.target_id}">${esc(label)}</a>`:'';
  const source=row=>reading?.cite(row)||'';
  const fact=row=>reading.fact(row);
  function mount(){
    const panel=document.createElement('section');panel.id='companyPage';panel.className='panel company-page hidden';panel.dataset.workspacePage='company';
    panel.innerHTML=`<div class="section-head"><button id="companyBack" class="ghost compact">← 이전 화면</button><button id="companyCollect" class="ghost compact">기업 자료 새로 수집</button></div><div class="company-heading"><div><p class="eyebrow">COMPANY RESEARCH</p><h2 id="companyTitle">기업 상세</h2><p id="companyIntro"></p><div id="companyIntroSource"></div></div><div id="companyQuote"></div></div><p id="companyStatus" class="fineprint" role="status"></p><p id="companyError" class="error" role="alert"></p>
      <nav class="detail-jumps" aria-label="기업 상세 목차"><a href="#companyBriefSection">기업 핵심 정리</a><a href="#companySegmentsSection">매출 구성</a><a href="#companyRelationsSection">기업 관계도</a><a href="#companyProductsSection">제품·서비스</a><a href="#companyDriversSection">실적 관련 요인</a><a href="#companyFinancialsSection">공시·재무</a><a href="#companySourcesSection">출처</a></nav>
      <section id="companyBriefSection"><h3>기업 핵심 정리</h3><div id="companyBrief" class="company-brief-grid"></div></section>
      <section id="companySegmentsSection"><div class="section-head"><h3>사업·매출 구성</h3><label>매출 구분<select id="companyRevenueGroup"></select></label></div><div id="companyRevenue"></div><div id="companySegments" class="company-fact-grid"></div><details class="company-appendix"><summary>사업 구성·산업 분류 원자료</summary><div id="companySegmentOriginals" class="company-fact-grid"></div><div id="companyFacts" class="company-fact-grid"></div></details><h3>제품 시장점유율</h3><div id="companyMarketShares" class="company-fact-grid"></div></section>
      <section id="companyRelationsSection"><div class="section-head"><h3>기업 관계도</h3><label>관계 종류<select id="companyRelationFilter"><option value="business">사업 관계 우선</option><option value="all">소유·지분 포함 전체</option>${Object.entries(kinds).map(([key,name])=>`<option value="${key}">${name}</option>`).join('')}</select></label></div><p class="fineprint">기업을 누르면 상세 페이지로 이동합니다. 화살표는 공급사 → 현재 기업 → 고객사 또는 모회사 → 자회사 방향입니다. 연결선은 지분율·거래액·관계의 강도를 뜻하지 않습니다.</p><details class="company-graph-method"><summary>표시 순서·자료 범위·수집 방법</summary><p>공급·고객·협력·경쟁 관계를 먼저 표시합니다. 각 종류 안에서는 기업·공시 원문, 정보 제공사 순이며 같은 출처 등급은 진술의 기준일을 사용합니다. 사업 규모나 투자 중요도 점수가 아닙니다. 발표된 계획과 현재 이행을 구분하며, 공개되지 않은 상대 회사는 추정하지 않습니다.</p><div id="companyReportAnalysis"></div></details><p id="companyRelationSummary" class="fineprint"></p><div class="company-graph-layout"><div id="companyGraph" tabindex="0" role="region" aria-label="기업 관계도 · 좁은 화면에서 좌우 스크롤"></div><aside id="companyRelationFocus" class="company-fact" aria-live="polite"></aside></div><div id="companyRelationList"></div><div id="companyRelationPages"></div></section>
      <section id="companyProductsSection"><h3>제품·서비스</h3><div id="companyProducts" class="company-fact-grid"></div><div id="companyProductPages"></div><details class="company-appendix"><summary>제품·서비스 공시 발췌</summary><div id="companyProductOriginals" class="company-fact-grid"></div></details></section>
      <section id="companyDriversSection"><h3>실적에 관련된 요인</h3><p class="fineprint">원자료에 제시된 사업 조건·투입 요소를 정리합니다.</p><div id="companyDrivers" class="company-fact-grid"></div><details class="company-appendix"><summary>사업 조건·위험 요인 공시 발췌</summary><div id="companyDriverOriginals" class="company-fact-grid"></div></details></section>
      <section id="companyPeersSection"><h3>동일 섹터 기업 탐색</h3><p class="fineprint">시가총액순으로 수집된 동일 분류 기업 최대 80개입니다. 동일 섹터 분류만으로 직접 경쟁 관계를 뜻하지 않습니다. 전체 기업은 섹터 목록에서 볼 수 있습니다.</p><div id="companyPeers"></div><div id="companyPeerPages"></div></section>
      <section id="companyFinancialsSection"><h3>공시·재무 원자료</h3><p class="fineprint">재무 수치는 공시에 보고된 값이며 앱에서 재계산하지 않습니다. 매출·이익은 표에 표시한 연간 기간, 자산·부채·자본은 기말 기준입니다. 최신 분기 수치 또는 예상치와 혼동하지 마세요.</p><div id="companyFinancials"></div><div id="companyFilings"></div></section>
      <section id="companySourcesSection"><details id="companySourceDetails" class="detail-sources-toggle"><summary id="companySourceCount">출처 모음</summary><p class="fineprint">기업·공시 원문과 정보 제공사·공개 조사를 모았습니다. 본문의 번호를 누르면 해당 출처로 이동합니다. 기업 발표는 해당 기업의 진술이며 독립적인 계약 이행 검증을 뜻하지 않습니다.</p><div id="companySources"></div></details></section>`;
    $('#marketDetail').after(panel);
    const pricePanel=document.createElement('div');pricePanel.id='companyLivePrice';
    $('#companyQuote').before(pricePanel);
    prices=window.MilkywayCompanyPrice.create({api:(...args)=>hooks.api(...args),getState:()=>hooks.getState(),target:pricePanel,footer});
    const networkSection=document.createElement('section');networkSection.className='company-network-section';
    networkSection.innerHTML='<h3>업계 연결 탐색</h3><div id="companyNetwork" aria-live="polite"></div>';
    $('#companyRelationsSection').append(networkSection);
    network=window.MilkywayCompanyNetwork.create({api:(...args)=>hooks.api(...args),getState:()=>hooks.getState(),footer,prepareReading:next=>prices.useReading(next)});
    $('#companyBack').addEventListener('click',()=>{if(history.state?.parentCompany){history.back();return;}const target=sector;leave();if(target)window.MilkywayMarketDetail.open(target);else hooks.openWorkspace('market');});
    $('#companyCollect').addEventListener('click',collect);
    $('#companyRelationFilter').addEventListener('change',()=>{relationPage=1;selected=null;relations();});
    $('#companyRevenueGroup').addEventListener('change',()=>{revenueGroup=$('#companyRevenueGroup').value;$('#companyRevenue').innerHTML=reading.revenue(revenueGroup);});
    panel.querySelectorAll('.detail-jumps a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();$(a.getAttribute('href')).scrollIntoView({behavior:'smooth'});}));
    panel.addEventListener('click',event=>{
      const citation=event.target.closest('[data-company-citation]');if(citation){event.preventDefault();$('#companySourceDetails').open=true;$('#company-source-'+citation.dataset.companyCitation)?.scrollIntoView({behavior:'smooth',block:'center'});return;}
      const via=event.target.closest('[data-network-via]');if(via){network.open(via.dataset.networkVia);return;}
      const networkPage=event.target.closest('[data-network-page]');if(networkPage&&!networkPage.disabled){network.page(Number(networkPage.dataset.networkPage));return;}
      const relation=event.target.closest('[data-relation-index]');if(relation){selected=Number(relation.dataset.relationIndex);focus();return;}
      const page=event.target.closest('[data-relation-page]');if(page){relationPage=Number(page.dataset.relationPage);selected=null;relations();return;}
      const product=event.target.closest('[data-product-page]');if(product){productPage=Number(product.dataset.productPage);products();}
      const peer=event.target.closest('[data-peer-page]');if(peer){peerPage=Number(peer.dataset.peerPage);peers();}
    });
    panel.addEventListener('keydown',event=>{const relation=event.target.closest('[data-relation-index]');if(relation&&(event.key==='Enter'||event.key===' ')){event.preventDefault();selected=Number(relation.dataset.relationIndex);focus();}});
    document.addEventListener('click',event=>{
      if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.altKey||event.shiftKey)return;
      const entity=event.target.closest('[data-company-id]');if(entity){if(validKey(entity.dataset.companyId)){event.preventDefault();openEntity(entity.dataset.companyId);}return;}
      const target=event.target.closest('[data-company-symbol][data-company-sector]');if(!target)return;
      if(event.target.closest('a,button,input,select,textarea,details')&&event.target.closest('a,button')!==target)return;
      const selection=window.getSelection();if(selection&&!selection.isCollapsed&&target.contains(selection.anchorNode))return;
      event.preventDefault();open(target.dataset.companySector,target.dataset.companySymbol);
    });
  }
  function footer(nextReading){if(nextReading)reading=nextReading;if(reading){$('#companySourceCount').textContent=`출처 모음 · ${fmt(reading.count,0)}개`;$('#companySources').innerHTML=reading.footer();}}
  function focus(){
    const edge=data?.relations[selected];
    if(!edge){$('#companyRelationFocus').innerHTML='<h4>관계 확인</h4><p>관계도나 아래 목록에서 기업을 선택하세요.</p>';return;}
    const evidence=edge.evidence?.length?edge.evidence:[edge];
    $('#companyRelationFocus').innerHTML=`<small>${esc(kinds[edge.kind])} · 근거 ${fmt(evidence.length,0)}건</small><h4>${esc(edge.name)}</h4>${reading.business(edge)}<strong>확인된 관계</strong>${evidence.map(item=>`<div class="company-relation-evidence"><p>${esc(item.detail||'등록된 관계의 세부 조건은 원문을 확인하세요.')} ${source(item.source)}</p>${item.reverse?`<p class="company-reverse-note">${esc(item.reported_by)} 자료에 기록된 관계를 반대 방향에서 표시합니다. 설명과 출처는 원래 진술의 내용입니다.</p>`:''}${reading.original(item.original)}</div>`).join('')}<p>${companyLink(edge,edge.name+' 기업 상세')}</p>${['supplier','customer','partner','competitor'].includes(edge.kind)?`<button class="ghost compact" data-network-via="${esc(edge.target_id)}">업계 연결</button>`:''}`;
  }
  function relations(){
    if(!data)return;
    const filter=$('#companyRelationFilter').value,rows=relationView.select(data.relations,filter),result=window.MilkywayPaging.slice(rows,relationPage);
    relationPage=result.page;
    $('#companyRelationSummary').textContent=`${filter==='business'?'사업 관계':filter==='all'?'전체 관계':kinds[filter]} ${fmt(rows.length,0)}개 · 현재 페이지 ${fmt(result.rows.length,0)}개 · 자료에 등록된 기업만 표시`;
    for(const option of $('#companyRelationFilter').options){if(kinds[option.value])option.textContent=`${kinds[option.value]} (${fmt(relationView.select(data.relations,option.value).length,0)})`;}
    $('#companyGraph').innerHTML=relationView.draw(data.name,data.symbol,result.rows)||'<p class="fineprint company-graph-empty">이 조건에서 출처를 확인한 사업 관계가 아직 등록되지 않았습니다. 관계 종류를 바꾸거나 기업 공시·자료 수집 상태를 확인하세요.</p>';
    $('#companyRelationList').innerHTML=result.rows.map(edge=>{const item=relationView.lead(edge);return `<div class="company-relation-row"><span class="relation-kind relation-${esc(edge.kind)}">${esc(kinds[edge.kind])}</span><div class="company-relation-business"><strong>${companyLink(edge)}</strong>${reading.business(edge)}<p><span class="fineprint">관계 근거</span> ${esc(item.detail||'사업 역할 설명 미등록')}</p></div><small>${esc(item.source.as_of||'기준일 미제공')} · ${esc(level[item.source.level])}${item.reverse?' · 역방향 표시':''}${edge.evidence?.length>1?' · 근거 '+fmt(edge.evidence.length,0)+'건':''}</small><button class="ghost compact" type="button" data-relation-index="${edge.index}" aria-label="${esc(edge.name)} 관계·출처">관계·출처</button>${['supplier','customer','partner','competitor'].includes(edge.kind)?`<button class="ghost compact" data-network-via="${esc(edge.target_id)}" aria-label="${esc(edge.name)} 업계 연결">업계 연결</button>`:''}</div>`;}).join('');
    $('#companyRelationPages').innerHTML=window.MilkywayPaging.controls(result,'data-relation-page');
    selected??=result.rows[0]?.index;focus();
  }
  function products(){const result=window.MilkywayPaging.slice(data.products.filter(row=>!row.original),productPage);productPage=result.page;$('#companyProducts').innerHTML=result.rows.length?result.rows.map(fact).join(''):'<p class="fineprint">검토된 제품·서비스 정리 수신 대기</p>';$('#companyProductPages').innerHTML=window.MilkywayPaging.controls(result,'data-product-page');$('#companyProductOriginals').innerHTML=data.products.filter(row=>row.original).map(fact).join('')||'<p class="fineprint">확보한 발췌 없음</p>';}
  function peers(){
    const result=window.MilkywayPaging.slice(data.peers||[],peerPage);peerPage=result.page;
    $('#companyPeers').innerHTML=result.rows.length?`<div class="research-table"><table><thead><tr><th>기업</th><th>종목</th><th>시가총액</th><th>근거</th></tr></thead><tbody>${result.rows.map(row=>`<tr class="company-directory-row" data-company-sector="${esc(sector)}" data-company-symbol="${esc(row.symbol)}"><td><a data-company-sector="${esc(sector)}" data-company-symbol="${esc(row.symbol)}" href="#company/${encodeURIComponent(sector)}/${encodeURIComponent(row.symbol)}">${esc(row.name)}</a></td><td>${esc(row.symbol)}</td><td>${fmt(row.market_cap,0)} ${esc(row.currency)}</td><td>${source(reading.quoteSource(row,data.quote_basis?.fetched_at))}</td></tr>`).join('')}</tbody></table></div>`:'<p class="fineprint">동일 섹터 기업 시세 자료 수신 대기</p>';
    $('#companyPeerPages').innerHTML=window.MilkywayPaging.controls(result,'data-peer-page');
  }
  function render(){
    reading=window.MilkywayCompanyResearchView.create(data);
    $('#companyTitle').textContent=data.name;$('#companyIntro').textContent=data.description||'이 기업의 공시·제품·사업 구성과 연결 관계를 출처별로 확인하세요.';$('#companyIntroSource').innerHTML=source(data.description_source);
    const basis=data.quote_basis||{},date=basis.fetched_at?new Date(basis.fetched_at).toLocaleString('ko-KR'):'수신 전';
    $('#companyQuote').innerHTML=`<strong>${esc(data.symbol||'종목 미등록')}</strong><span>${esc(data.sector_label)}</span>${data.quote.market_cap!=null?`<small>시가총액 ${fmt(data.quote.market_cap,0)} ${esc(data.quote.currency)} ${source(reading.quoteSource(data.quote,basis.fetched_at))}</small>${Number.isFinite(data.quote.displayed_share_pct)?`<small>수집 기업 내 비중 ${fmt(data.quote.displayed_share_pct)}%</small>`:''}`:'<small>등록된 시가총액·지수 비중 자료 없음</small>'}${basis.count?`<details class="company-quote-method"><summary>시총·비중 산출</summary><p>시총은 제공사 보고값입니다. 비중 = 기업 시총 ÷ 수신한 동일 통화 ${fmt(basis.count,0)}개 기업의 시총 합계(${fmt(basis.market_cap_sum,0)} ${esc(data.quote.currency)}) × 100. 페이지를 바꿔도 분모는 같습니다. 시총 미수신 기업이 있으면 비중을 계산하지 않습니다.</p><p>수집 ${esc(date)} · 제품 시장점유율·공식 지수 비중과 다릅니다.</p></details>`:''}`;
    $('#companyStatus').textContent=`${data.pending?'기업 자료 수집 중 · 이 화면에서 결과를 확인할 수 있습니다':data.fetched_at?'자료 수집 '+new Date(data.fetched_at).toLocaleString('ko-KR'):'공식 관계 자료로 등록된 항목'}${data.collectable===false?' · 등록된 공식 자료 범위 제공':data.stale?' · 일부 자료 확인 필요':''}`;
    $('#companyCollect').disabled=Boolean(data.pending)||data.collectable===false;
    $('#companyError').textContent=(data.errors||[]).join(' / ');
    $('#companyReportAnalysis').innerHTML=data.report_analysis?fact(data.report_analysis):'<p class="fineprint">공시 본문 분석 자료 수신 전입니다. 기업 자료를 수집하면 공시에서 확인한 사업 관계와 원문을 추가합니다. 빈 관계 분류는 해당 관계가 없다는 뜻이 아닙니다.</p>';
    products();relations();peers();
    $('#companyBrief').innerHTML=reading.essentials();
    revenueGroup=reading.groups.includes(revenueGroup)?revenueGroup:reading.groups[0]||'product';
    $('#companyRevenueGroup').innerHTML=reading.groups.map(key=>`<option value="${key}">${esc(window.MilkywayCompanyResearchView.groups[key])}</option>`).join('')||'<option value="product">수치 확인 대기</option>';
    $('#companyRevenueGroup').value=revenueGroup;$('#companyRevenueGroup').disabled=!reading.groups.length;
    $('#companyRevenue').innerHTML=reading.revenue(revenueGroup);
    for(const [id,key,message] of [['companySegments','segments',''],['companyFacts','facts','등록·산업 분류 수신 대기'],['companyDrivers','drivers','검토된 관련 요인 수신 대기'],['companyMarketShares','market_shares','조사 범위·기간이 확인된 제품별 시장점유율 미확보. 시총 비중은 시장점유율로 사용하지 않습니다.']]){
      const rows=(data[key]||[]).filter(row=>key==='facts'||!row.original);$('#'+id).innerHTML=rows.length?rows.map(fact).join(''):`<p class="fineprint">${message}</p>`;
    }
    for(const [id,key] of [['companySegmentOriginals','segments'],['companyDriverOriginals','drivers']])$('#'+id).innerHTML=(data[key]||[]).filter(row=>row.original).map(fact).join('')||'<p class="fineprint">확보한 발췌 없음</p>';
    $('#companyFinancials').innerHTML=data.financials.length?`<div class="research-table"><table><thead><tr><th>공시 항목</th><th>보고값</th><th>보고 기간·기말</th><th>원자료</th></tr></thead><tbody>${data.financials.map(row=>`<tr><td>${esc(row.label)}</td><td>${fmt(row.value,0)} ${esc(row.unit)}</td><td>${esc(row.period)}</td><td>${source(row.source)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="fineprint">현재 확인된 공시 재무 수치가 없습니다. 아래 기업 공시 원문을 확인하세요.</p>';
    $('#companyFilings').innerHTML=data.filings.length?`<p class="fineprint">확보한 공시 ${fmt(data.filings.length,0)}건 · 원문 링크와 기준일은 하단 출처 모음에서 확인할 수 있습니다.</p>`:'';
    network.setContext(data,reading);prices.setContext(data,reading);footer();
  }
  async function refresh(){
    if(!loadPath||loading===epoch||hooks.getState().workspace!=='company')return;
    const token=epoch,actor=hooks.getState().me?.id;loading=token;
    try{
      const next=await hooks.api(loadPath);
      if(token!==epoch||actor!==hooks.getState().me?.id||hooks.getState().workspace!=='company')return;
      const nextSignature=JSON.stringify(next),previousSelection=data?.relations[selected];
      if(previousSelection){const index=next.relations.findIndex(row=>row.target_id===previousSelection.target_id&&row.kind===previousSelection.kind);selected=index<0?null:index;}
      data=next;entityKey=next.entity_key;if(next.sector)sector=next.sector;
      if(nextSignature!==signature){signature=nextSignature;render();}
    }catch(e){if(token===epoch)$('#companyError').textContent=e.message;}
    finally{if(loading===token)loading=null;}
  }
  async function collect(){
    if(!loadPath||data?.pending||data?.collectable===false)return;
    const token=epoch;$('#companyCollect').disabled=true;
    try{await hooks.api(loadPath+'/refresh',{method:'POST'});if(token===epoch){signature='';await refresh();}}
    catch(e){if(token===epoch)$('#companyError').textContent=e.message;}
    finally{if(token===epoch)$('#companyCollect').disabled=Boolean(data?.pending)||data?.collectable===false;}
  }
  async function present(path,hash,nextSector,nextSymbol,key,push){
    const parentCompany=entityKey,origin=nextSector||sector||history.state?.companyOrigin||null;
    sector=origin;symbol=nextSymbol;entityKey=key;loadPath=path;data=null;signature='';
    network.reset();prices.clear();++epoch;relationPage=productPage=peerPage=1;selected=null;reading=null;revenueGroup=null;$('#companyRelationFilter').value='business';$('#companySourceDetails').open=false;
    hooks.openWorkspace('company',false);
    if(push)history.pushState({companyOrigin:origin,parentCompany},'',hash);
    $('#companyTitle').textContent='기업 자료를 불러오고 있습니다';$('#companyError').textContent='';
    $('#companyStatus').textContent='';$('#companyCollect').disabled=true;
    for(const id of ['companyIntro','companyIntroSource','companyQuote','companyBrief','companyRevenue','companyGraph','companyRelationFocus','companyRelationList','companyRelationPages','companyRelationSummary','companyReportAnalysis','companyProducts','companyProductPages','companyProductOriginals','companySegments','companySegmentOriginals','companyDriverOriginals','companyFacts','companyMarketShares','companyDrivers','companyPeers','companyPeerPages','companyFinancials','companyFilings','companySources'])$('#'+id).innerHTML='';
    const token=epoch;await refresh();
    if(token===epoch&&hooks.getState().workspace==='company'&&data?.stale&&!data.pending&&data.collectable!==false)await collect();
  }
  async function open(nextSector,nextSymbol,push=true){
    if(!/^[a-z0-9_]{1,30}$/.test(nextSector)||!/^[A-Z0-9][A-Z0-9.-]{0,19}$/.test(nextSymbol)||!hooks.getState().config.personal_local_mode)return;
    return present(`/api/company-details/${encodeURIComponent(nextSector)}/${encodeURIComponent(nextSymbol)}`,`#company/${encodeURIComponent(nextSector)}/${encodeURIComponent(nextSymbol)}`,nextSector,nextSymbol,null,push);
  }
  async function openEntity(key,push=true){
    if(!validKey(key)||!hooks.getState().config.personal_local_mode)return;
    return present('/api/company-entities/'+key,'#company/'+key,null,null,key,push);
  }
  function leave(){network.reset();prices.clear();sector=symbol=entityKey=loadPath=null;++epoch;}
  window.MilkywayCompany=Object.freeze({initialize(options){hooks=options;mount();setInterval(()=>{if(!document.hidden)refresh();},5000);},open,openEntity,leave});
})();
