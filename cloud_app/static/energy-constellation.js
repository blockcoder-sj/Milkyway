/* Sector scene and source inspector. The endpoint reads local public research only. */
(() => {
  const esc=value=>window.MilkywayResearchView.escape(value);
  let hooks,scene,graph=null,serial=0,enabled=false,loading=false,selected=null,page=1,order=new Map();
  const $=id=>document.getElementById(id);
  const types={issuer:'조사 기업',company:'연결 기업',group:'사업 탐색 업종',product:'제품·설비·사업 과정',factor:'외부 요인',sector:'연구 범위',segment:'사업 부문',revenue:'매출 구성'};
  const kinds={customer:'공급·고객',supplier:'공급·고객',subsidiary:'모회사·자회사',parent:'모회사·자회사',holding:'소유·지분',owner:'소유·지분',partner:'협력',competitor:'경쟁',transaction:'사업 거래',business_scope:'사업 범위',classification:'편집 분류',industry_process:'산업 과정',exposure:'분석용 영향 경로',revenue:'공시 매출 구성'};
  function cite(source){
    try{const u=new URL(source.url);if(u.protocol!=='https:'||u.username||u.password)return '';return `<a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">${esc(source.label)} ↗</a><small>${esc(source.as_of||'문서 날짜 미제공')}</small>`;}catch{return '';}
  }
  function inspect(node,ranked=[]){
    if(!node||!graph)return;selected=node;page=1;order=new Map(ranked.map((n,i)=>[n.id,i]));drawInspector();
  }
  function drawInspector(){
    const node=selected;if(!node||!graph)return;
    const edges=graph.edges.filter(e=>e.source===node.id||e.target===node.id),byId=new Map(graph.nodes.map(n=>[n.id,n]));
    const otherId=e=>e.source===node.id?e.target:e.source;
    edges.sort((a,b)=>(order.get(otherId(a))??Infinity)-(order.get(otherId(b))??Infinity));
    const result=window.MilkywayPaging.slice(edges,page);page=result.page;
    const open=/^c_[a-f0-9]{32}$/.test(node.id)?`<p><a href="#company/${node.id}" data-company-id="${node.id}">기업 상세와 원문 보기 ↗</a></p>`:
      node.kind==='issuer'?`<p><a href="#company/${esc(node.sector)}/${esc(node.symbol)}" data-company-sector="${esc(node.sector)}" data-company-symbol="${esc(node.symbol)}">기업 상세와 원문 보기 ↗</a></p>`:'';
    $('energyCosmosFocus').innerHTML=`<small>${esc(types[node.kind])}${node.scope==='source_only'?' · 관계 출처만 확보':node.scope==='role_context'?' · 제한된 사업 문맥':''}</small><h4>${esc(node.name)}</h4><p>${esc(node.description||'별도 설명 미확보')}</p>${node.measure?`<p>${esc(window.MilkywayConstellationMath.measureText(node.measure))}</p>`:''}${node.original?`<details><summary>검색한 공시 원문 근거</summary><p lang="en">${esc(node.original)}</p></details>`:''}${(node.sources||[]).map(cite).join('')}${open}<p class="fineprint">직접 연결 ${edges.length}개 · 실선: 확인된 사업·거래 범위 · 점선: 분류·산업 구조·분석용 경로</p><div class="energy-cosmos-neighbours">${result.rows.map(e=>{
      const other=byId.get(e.source===node.id?e.target:e.source);
      return `<div><button type="button" class="ghost compact" data-cosmos-focus="${esc(other.id)}">${esc(other.name)} · ${esc(kinds[e.kind]||e.kind)}</button><p>${esc(e.detail)}</p>${e.measure?`<p>${esc(window.MilkywayConstellationMath.measureText(e.measure))}</p>`:''}${e.original?`<details><summary>검색한 공시 원문 근거</summary><p lang="en">${esc(e.original)}</p></details>`:''}${cite(e.citation)}${e.evidence_count>1?`<small>연결 출처 ${e.evidence_count}건 · 대표 근거 표시</small>`:''}</div>`;
    }).join('')}</div>${window.MilkywayPaging.controls(result,'data-cosmos-neighbours-page')}`;
  }
  async function load(force=false){
    if(!enabled||loading)return;
    if(graph&&!force){scene.set(graph);return;}
    const token=++serial,owner=hooks.getState().me?.id;loading=true;
    $('energyCosmosStatus').textContent='저장된 에너지 생태계 자료를 읽고 있습니다…';
    try{
      const result=await hooks.api('/api/energy-constellation');
      if(token!==serial||!enabled||owner!==hooks.getState().me?.id||hooks.getState().workspace!=='detail')return;
      graph=result;scene.set(graph);$('energyCosmosStatus').textContent=result.scope;
      $('energyCosmosMethod').textContent=result.method;
    }catch(error){if(token===serial&&enabled)$('energyCosmosStatus').textContent=error.message;}
    finally{if(token===serial)loading=false;}
  }
  function render(value){
    const next=Boolean(value);$('energyCosmosSection').hidden=!next;
    if(!next){enabled=false;serial++;loading=false;scene?.clear();return;}
    if(!enabled){enabled=true;load();}
  }
  function initialize(options){
    hooks=options;const section=document.createElement('section');section.id='energyCosmosSection';section.className='energy-cosmos-section';section.hidden=true;
    section.innerHTML='<div class="section-head"><div><p class="eyebrow">ENERGY CONSTELLATION</p><h3>에너지 생태계 우주 지도</h3></div><button id="energyCosmosRefresh" type="button" class="ghost compact">저장 자료 다시 읽기</button></div><p id="energyCosmosStatus" class="fineprint" role="status"></p><details class="energy-cosmos-method"><summary>거리·크기·출처를 읽는 기준</summary><p>선택한 요소를 중심에 두고 직접 연결을 먼저, 같은 단계에서는 공급·고객·소유·사업 관계를 분류 연결보다 가까이 배치합니다. 같은 관계의 원문을 여러 번 수집했다고 거리가 가까워지지 않습니다. 더 먼 단계는 바깥에 배치하며 확인되지 않은 직접 관계를 만들지 않습니다.</p><p id="energyCosmosMethod"></p><p>요소를 선택하면 주요 직접 연결을 최대 8개까지 모아 확대합니다. 전체 지도로 모든 요소를 다시 볼 수 있으며, 전체 화면의 천체 겹침은 허용합니다. 이름표는 읽을 수 있는 범위로 줄이며 검색으로 모든 등록 요소를 선택할 수 있습니다. 같은 사업 키워드를 가까이 모읍니다. 비중 기준을 선택하면 해당 구분의 최신 공시 매출 비중을 우선 배치합니다. 비중이 없는 관계·외부 요인의 영향 크기를 추정하지 않습니다. 원문 근거 검색과 정량 비중은 구별합니다. 매출 항목의 크기는 선택한 기준의 확인된 최신 매출 비중을 반영하고, 다른 천체는 선택 상태·확대·화면 밀도에 따른 표시 크기입니다.</p></details><div class="energy-cosmos-layout"><div id="energyCosmosGraph"></div><aside id="energyCosmosFocus" class="energy-cosmos-focus" aria-live="polite"></aside></div>';
    $('detailIndustrySection').before(section);
    scene=window.MilkywayConstellation.create($('energyCosmosGraph'),{select:inspect,evidenceSearch:q=>hooks.api('/api/energy-constellation/search?q='+encodeURIComponent(q)),edge:e=>{
      const a=graph.nodes.find(n=>n.id===e.source),b=graph.nodes.find(n=>n.id===e.target);
      $('energyCosmosFocus').innerHTML=`<small>${esc(e.analytical?'분석·분류 경로':'출처로 확인한 관계')}</small><h4>${esc(a.name)} → ${esc(b.name)}</h4><p>${esc(kinds[e.kind]||e.kind)}</p><p>${esc(e.detail)}</p>${e.measure?`<p>${esc(window.MilkywayConstellationMath.measureText(e.measure))}</p>`:''}${e.original?`<details><summary>검색한 공시 원문 근거</summary><p lang="en">${esc(e.original)}</p></details>`:''}${cite(e.citation)}<p class="fineprint">이 선의 정확한 근거입니다. 관계의 강도·거래액을 추정한 값은 아닙니다.</p><button type="button" class="ghost compact" data-cosmos-focus="${esc(b.id)}">${esc(b.name)} 중심으로</button>`;
    }});
    $('energyCosmosRefresh').addEventListener('click',()=>load(true));
    section.addEventListener('click',event=>{const focus=event.target.closest('[data-cosmos-focus]');if(focus){scene.focus(focus.dataset.cosmosFocus);return;}
      const target=event.target.closest('[data-cosmos-neighbours-page]');if(target&&!target.disabled){page=Number(target.dataset.cosmosNeighboursPage);drawInspector();}});
  }
  window.MilkywayEnergyConstellation=Object.freeze({initialize,render});
})();
