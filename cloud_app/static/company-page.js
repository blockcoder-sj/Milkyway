/* Cached company encyclopedia. Public-data collection is queued separately from AI. */
(() => {
  const $=s=>document.querySelector(s),esc=v=>window.MilkywayResearchView.escape(v),fmt=(v,d=2)=>window.MilkywayFormat.number(v,d);
  const link=(label,url)=>window.MilkywayMarketDirectory.link(label,url);
  const kinds={subsidiary:'자회사',parent:'모회사',owner:'소유·지분 관계',holding:'보유·지분 기업',partner:'협력사',supplier:'공급사',customer:'고객사',competitor:'경쟁사'};
  const colors={subsidiary:'#b69aef',parent:'#b69aef',owner:'#9298a9',holding:'#9298a9',partner:'#7dcfb5',supplier:'#e9be77',customer:'#85b9ed',competitor:'#e99099'};
  const level={primary:'공시·기업 원문',provider:'정보 제공사',encyclopedia:'공개 백과 · 원자료 확인'};
  let hooks,sector=null,symbol=null,entityKey=null,loadPath=null,data=null,epoch=0,loading=null,signature='',relationPage=1,productPage=1,peerPage=1,selected=null;
  const validKey=value=>/^c_[a-f0-9]{32}$/.test(value||'');
  const companyLink=(edge,label=edge.name)=>validKey(edge.target_id)?`<a class="company-open" data-company-id="${esc(edge.target_id)}" href="#company/${edge.target_id}">${esc(label)}</a>`:'';
  function source(row){return row?`<small class="company-citation">${link(row.label,row.url)}${row.as_of?' · 기준 '+esc(row.as_of):''} · ${esc(level[row.level]||'출처')}</small>`:'';}
  function fact(row){return `<article class="company-fact"><h4>${esc(row.title)}</h4>${row.detail?`<p>${esc(row.detail)}</p>`:''}${source(row.source)}</article>`;}
  function mount(){
    const panel=document.createElement('section');panel.id='companyPage';panel.className='panel company-page hidden';panel.dataset.workspacePage='company';
    panel.innerHTML=`<div class="section-head"><button id="companyBack" class="ghost compact">← 이전 화면</button><button id="companyCollect" class="ghost compact">기업 자료 새로 수집</button></div><div class="company-heading"><div><p class="eyebrow">COMPANY ENCYCLOPEDIA</p><h2 id="companyTitle">기업 상세</h2><p id="companyIntro"></p><div id="companyIntroSource"></div></div><div id="companyQuote"></div></div><p id="companyStatus" class="fineprint" role="status"></p><p id="companyError" class="error" role="alert"></p>
      <nav class="detail-jumps" aria-label="기업 상세 목차"><a href="#companyRelationsSection">기업 관계도</a><a href="#companyProductsSection">제품·서비스</a><a href="#companySegmentsSection">사업 구성</a><a href="#companyDriversSection">실적 관련 요인</a><a href="#companyFinancialsSection">공시·재무</a><a href="#companySourcesSection">출처</a></nav>
      <section id="companyRelationsSection"><div class="section-head"><h3>기업 관계도</h3><label>관계 종류<select id="companyRelationFilter"><option value="all">전체 관계</option>${Object.entries(kinds).map(([key,name])=>`<option value="${key}">${name}</option>`).join('')}</select></label></div><p class="fineprint">관계도의 기업을 누르면 해당 상세 페이지로 이동합니다. 아래 목록의 ‘관계·출처’에서 연결 근거를 확인할 수 있습니다. 연결선은 지분율·거래액·관계의 강도를 뜻하지 않으며 기준일이 다른 진술이 함께 표시될 수 있습니다.</p><div class="company-graph-layout"><div id="companyGraph"></div><aside id="companyRelationFocus" class="company-fact" aria-live="polite"></aside></div><div id="companyRelationList"></div><div id="companyRelationPages"></div></section>
      <section id="companyProductsSection"><h3>제품·서비스</h3><div id="companyProducts" class="company-fact-grid"></div><div id="companyProductPages"></div></section>
      <section id="companySegmentsSection"><h3>사업·매출 구성</h3><div id="companySegments" class="company-fact-grid"></div><h3>기업 기본 정보</h3><div id="companyFacts" class="company-fact-grid"></div><h3>제품 시장점유율</h3><div id="companyMarketShares" class="company-fact-grid"></div></section>
      <section id="companyDriversSection"><h3>실적에 관련된 요인</h3><p class="fineprint">원자료에 제시된 사업 조건·투입 요소를 정리합니다. 수익률 전망이나 수치의 좋고 나쁨을 평가하지 않습니다.</p><div id="companyDrivers" class="company-fact-grid"></div></section>
      <section id="companyPeersSection"><h3>동일 섹터 기업 탐색</h3><p class="fineprint">시가총액순으로 수집된 동일 분류 기업 최대 80개입니다. 동일 섹터 분류만으로 직접 경쟁 관계를 뜻하지 않습니다. 전체 기업은 섹터 목록에서 볼 수 있습니다.</p><div id="companyPeers"></div><div id="companyPeerPages"></div></section>
      <section id="companyFinancialsSection"><h3>공시·재무 원자료</h3><p class="fineprint">재무 수치는 공시에 보고된 값이며 앱에서 재계산하지 않습니다. 매출·이익은 표에 표시한 연간 기간, 자산·부채·자본은 기말 기준입니다. 최신 분기 수치 또는 예상치와 혼동하지 마세요.</p><div id="companyFinancials"></div><div id="companyFilings"></div></section>
      <section id="companySourcesSection"><details class="detail-sources-toggle"><summary id="companySourceCount">출처 모음</summary><p class="fineprint">공시·기업 발표, 정보 제공사, 공개 백과를 구분합니다. 각 항목의 출처와 기준일을 확인할 수 있습니다. 등록되지 않은 관계나 수치는 추정하지 않습니다.</p><div id="companySources"></div></details></section>`;
    $('#marketDetail').after(panel);
    $('#companyBack').addEventListener('click',()=>{if(history.state?.parentCompany){history.back();return;}const target=sector;leave();if(target)window.MilkywayMarketDetail.open(target);else hooks.openWorkspace('market');});
    $('#companyCollect').addEventListener('click',collect);
    $('#companyRelationFilter').addEventListener('change',()=>{relationPage=1;selected=null;relations();});
    panel.querySelectorAll('.detail-jumps a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();$(a.getAttribute('href')).scrollIntoView({behavior:'smooth'});}));
    panel.addEventListener('click',event=>{
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
  function focus(){
    const edge=data?.relations[selected];
    if(!edge){$('#companyRelationFocus').innerHTML='<h4>관계 확인</h4><p>관계도나 아래 목록에서 기업을 선택하세요.</p>';return;}
    const evidence=edge.evidence?.length?edge.evidence:[edge];
    $('#companyRelationFocus').innerHTML=`<small>${esc(kinds[edge.kind])} · 근거 ${fmt(evidence.length,0)}건</small><h4>${esc(edge.name)}</h4>${evidence.map(item=>`<div class="company-relation-evidence"><p>${esc(item.detail||'등록된 관계의 세부 조건은 원문을 확인하세요.')}</p>${item.reverse?`<p class="company-reverse-note">${esc(item.reported_by)} 자료에 기록된 관계를 반대 방향에서 표시합니다. 설명과 출처는 원래 진술의 내용입니다.</p>`:''}${source(item.source)}</div>`).join('')}<p>${companyLink(edge,edge.name+' 기업 상세')}</p>${edge.entity_id?`<p>${link('공개 백과 기업 항목','https://www.wikidata.org/wiki/'+edge.entity_id)}</p>`:''}`;
  }
  function relations(){
    if(!data)return;
    const filter=$('#companyRelationFilter').value,rows=data.relations.map((edge,index)=>({...edge,index})).filter(edge=>filter==='all'||edge.kind===filter),result=window.MilkywayPaging.slice(rows,relationPage);
    relationPage=result.page;
    const points=result.rows.map((edge,index)=>{
      const angle=-Math.PI/2+index*2*Math.PI/Math.max(result.rows.length,1);
      return {...edge,x:450+Math.cos(angle)*305,y:210+Math.sin(angle)*155};
    });
    const text=name=>{const chars=Array.from(name);return [chars.slice(0,20).join(''),chars.slice(20,40).join('')+(chars.length>40?'…':'')];};
    $('#companyGraph').innerHTML=points.length?`<svg class="company-graph" viewBox="0 0 900 420" role="group" aria-label="${esc(data.name)} 기업 관계도">${points.map(p=>`<line x1="450" y1="210" x2="${p.x.toFixed(2)}" y2="${p.y.toFixed(2)}" stroke="${colors[p.kind]}" stroke-opacity=".45"/>`).join('')}<rect x="345" y="173" width="210" height="74" rx="16" class="company-graph-center"/><text x="450" y="204" text-anchor="middle" class="graph-center-title">${esc(text(data.name)[0])}</text><text x="450" y="226" text-anchor="middle" class="graph-center-symbol">${esc(data.symbol||'관계 자료')}</text>${points.map(p=>{const lines=text(p.name);return `<a role="link" tabindex="0" href="#company/${esc(p.target_id)}" data-company-id="${esc(p.target_id)}" aria-label="${esc(p.name+' 기업 상세 · '+kinds[p.kind])}" class="company-graph-node"><title>${esc(p.name)}</title><rect x="${(p.x-105).toFixed(2)}" y="${(p.y-36).toFixed(2)}" width="210" height="72" rx="12" fill="#14111d" stroke="${colors[p.kind]}"/><text x="${p.x.toFixed(2)}" y="${(p.y-14).toFixed(2)}" text-anchor="middle" fill="${colors[p.kind]}" class="graph-kind">${esc(kinds[p.kind])}</text><text x="${p.x.toFixed(2)}" y="${(p.y+6).toFixed(2)}" text-anchor="middle" class="graph-name">${esc(lines[0])}</text>${lines[1]?`<text x="${p.x.toFixed(2)}" y="${(p.y+23).toFixed(2)}" text-anchor="middle" class="graph-name">${esc(lines[1])}</text>`:''}</a>`;}).join('')}</svg>`:'<p class="fineprint company-graph-empty">출처를 확인한 관계가 이 조건에 등록되지 않았습니다. 자료 수집 상태와 기업 공시 원문을 확인하세요.</p>';
    $('#companyRelationList').innerHTML=result.rows.map(edge=>`<div class="company-relation-row"><span class="relation-kind relation-${esc(edge.kind)}">${esc(kinds[edge.kind])}</span><strong>${companyLink(edge)}</strong><small>${esc(edge.source.as_of||'기준일 미제공')} · ${esc(level[edge.source.level])}${edge.reverse?' · 역방향 표시':''}${edge.evidence?.length>1?' · 근거 '+fmt(edge.evidence.length,0)+'건':''}</small><button class="ghost compact" type="button" data-relation-index="${edge.index}" aria-label="${esc(edge.name)} 관계·출처">관계·출처</button></div>`).join('');
    $('#companyRelationPages').innerHTML=window.MilkywayPaging.controls(result,'data-relation-page');
    selected??=result.rows[0]?.index;focus();
  }
  function products(){const result=window.MilkywayPaging.slice(data.products,productPage);productPage=result.page;$('#companyProducts').innerHTML=result.rows.length?result.rows.map(fact).join(''):'<p class="fineprint">제품·서비스의 확인된 설명이 아직 등록되지 않았습니다. 기업 공시·원문을 확인하세요.</p>';$('#companyProductPages').innerHTML=window.MilkywayPaging.controls(result,'data-product-page');}
  function peers(){
    const result=window.MilkywayPaging.slice(data.peers||[],peerPage);peerPage=result.page;
    $('#companyPeers').innerHTML=result.rows.length?`<div class="research-table"><table><thead><tr><th>기업</th><th>종목</th><th>시가총액</th><th>원자료</th></tr></thead><tbody>${result.rows.map(row=>`<tr class="company-directory-row" data-company-sector="${esc(sector)}" data-company-symbol="${esc(row.symbol)}"><td><a data-company-sector="${esc(sector)}" data-company-symbol="${esc(row.symbol)}" href="#company/${encodeURIComponent(sector)}/${encodeURIComponent(row.symbol)}">${esc(row.name)}</a></td><td>${esc(row.symbol)}</td><td>${fmt(row.market_cap,0)} ${esc(row.currency)}</td><td>${link(row.source,row.url)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="fineprint">동일 섹터 기업 시세 자료 수신 대기</p>';
    $('#companyPeerPages').innerHTML=window.MilkywayPaging.controls(result,'data-peer-page');
  }
  function render(){
    $('#companyTitle').textContent=data.name;$('#companyIntro').textContent=data.description||'이 기업의 공시·제품·사업 구성과 연결 관계를 출처별로 확인하세요.';$('#companyIntroSource').innerHTML=source(data.description_source);
    const basis=data.quote_basis||{},date=basis.fetched_at?new Date(basis.fetched_at).toLocaleString('ko-KR'):'수신 전';
    $('#companyQuote').innerHTML=`<strong>${esc(data.symbol||'종목 미등록')}</strong><span>${esc(data.sector_label)}</span>${data.quote.market_cap!=null?`<small>시가총액 ${fmt(data.quote.market_cap,0)} ${esc(data.quote.currency)}</small><small>수집 기업 내 비중 ${fmt(data.quote.displayed_share_pct)}%</small>`:'<small>등록된 시가총액·지수 비중 자료 없음</small>'}${data.quote.url?link(data.quote.source,data.quote.url):''}${basis.count?`<details class="company-quote-method"><summary>시총·비중 산출</summary><p>시총은 제공사 보고값입니다. 비중 = 기업 시총 ÷ 수신한 동일 통화 ${fmt(basis.count,0)}개 기업의 시총 합계(${fmt(basis.market_cap_sum,0)} ${esc(data.quote.currency)}) × 100. 페이지를 바꿔도 분모는 같습니다. 시총 미수신 기업이 있으면 비중을 계산하지 않습니다.</p><p>수집 ${esc(date)} · 제품 시장점유율·공식 지수 비중과 다릅니다.</p></details>`:''}`;
    $('#companyStatus').textContent=`${data.pending?'기업 자료 수집 중 · 이 화면에서 결과를 확인할 수 있습니다':data.fetched_at?'자료 수집 '+new Date(data.fetched_at).toLocaleString('ko-KR'):'원문 관계 자료로 등록된 항목'}${data.collectable===false?' · 공개 기업 식별자 미확인 · 원문 자료만 제공':data.stale?' · 일부 자료 확인 필요':''}`;
    $('#companyCollect').disabled=Boolean(data.pending)||data.collectable===false;
    $('#companyError').textContent=(data.errors||[]).join(' / ');
    products();relations();peers();
    for(const [id,key,message] of [['companySegments','segments','공시 사업 구성 또는 제공사 매출 구성 자료가 아직 등록되지 않았습니다.'],['companyFacts','facts','기업 개요 원자료 수신 대기'],['companyDrivers','drivers','이 기업의 원자료로 확인한 관련 요인이 아직 등록되지 않았습니다.'],['companyMarketShares','market_shares','조사 범위·기간을 확인한 제품별 시장점유율 자료가 아직 등록되지 않았습니다. 시총 비중을 시장점유율로 사용하지 않습니다.']])$('#'+id).innerHTML=data[key]?.length?data[key].map(fact).join(''):`<p class="fineprint">${message}</p>`;
    $('#companyFinancials').innerHTML=data.financials.length?`<div class="research-table"><table><thead><tr><th>공시 항목</th><th>보고값</th><th>보고 기간·기말</th><th>원자료</th></tr></thead><tbody>${data.financials.map(row=>`<tr><td>${esc(row.label)}</td><td>${fmt(row.value,0)} ${esc(row.unit)}</td><td>${esc(row.period)}</td><td>${source(row.source)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="fineprint">현재 확인된 공시 재무 수치가 없습니다. 아래 기업 공시 원문을 확인하세요.</p>';
    $('#companyFilings').innerHTML=data.filings.map(row=>`<p>${source(row)}</p>`).join('');
    const sources=[...data.sources,...(data.description_source?[data.description_source]:[]),...['products','segments','market_shares','facts','drivers','financials'].flatMap(key=>(data[key]||[]).map(row=>row.source)),...data.relations.flatMap(edge=>(edge.evidence?.length?edge.evidence:[edge]).map(item=>item.source)),...data.filings];
    const unique=[...new Map(sources.map(row=>[row.url+'|'+(row.as_of||''),row])).values()];$('#companySourceCount').textContent=`출처 모음 · ${fmt(unique.length,0)}개`;$('#companySources').innerHTML=unique.map(row=>`<p>${source(row)}</p>`).join('');
  }
  async function refresh(){
    if(!loadPath||loading===epoch||hooks.getState().workspace!=='company')return;
    const token=epoch,actor=hooks.getState().me?.id;loading=token;
    try{
      const next=await hooks.api(loadPath);
      if(token!==epoch||actor!==hooks.getState().me?.id||hooks.getState().workspace!=='company')return;
      const nextSignature=JSON.stringify(next);data=next;entityKey=next.entity_key;
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
    ++epoch;relationPage=productPage=peerPage=1;selected=null;$('#companyRelationFilter').value='all';
    hooks.openWorkspace('company',false);
    if(push)history.pushState({companyOrigin:origin,parentCompany},'',hash);
    $('#companyTitle').textContent='기업 자료를 불러오고 있습니다';$('#companyError').textContent='';
    $('#companyStatus').textContent='';$('#companyCollect').disabled=true;
    for(const id of ['companyIntro','companyIntroSource','companyQuote','companyGraph','companyRelationFocus','companyRelationList','companyRelationPages','companyProducts','companyProductPages','companySegments','companyFacts','companyMarketShares','companyDrivers','companyPeers','companyPeerPages','companyFinancials','companyFilings','companySources'])$('#'+id).innerHTML='';
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
  function leave(){sector=symbol=entityKey=loadPath=null;++epoch;}
  window.MilkywayCompany=Object.freeze({initialize(options){hooks=options;mount();setInterval(()=>{if(!document.hidden)refresh();},5000);},open,openEntity,leave});
})();
