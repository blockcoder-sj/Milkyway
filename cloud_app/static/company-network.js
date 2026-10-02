/* Explicit two-hop exploration of locally stored business evidence. */
(() => {
  const esc=value=>window.MilkywayResearchView.escape(value);
  const kinds={supplier:'공급사',customer:'고객사',partner:'협력사',competitor:'경쟁사'};
  const valid=value=>/^c_[a-f0-9]{32}$/.test(value||'');
  const link=(key,name)=>valid(key)?`<a data-company-id="${key}" href="#company/${key}">${esc(name)}</a>`:esc(name);
  function create(hooks) {
    const $=selector=>document.querySelector(selector);
    let root=null,reading=null,value=null,serial=0;
    function message(text) { $('#companyNetwork').innerHTML=`<p class="fineprint">${esc(text)}</p>`; }
    function setContext(data,nextReading) {
      if(root?.entity_key!==data.entity_key) {serial++;value=null;}
      if(value&&!(data.relations||[]).some(edge=>edge.target_id===value.via.id&&kinds[edge.kind])) {serial++;value=null;}
      root=data;reading=nextReading;
      if(value)draw();else message('관계 목록의 업계 연결을 선택하면 연결 기업의 사업 관계를 8개씩 표시합니다.');
    }
    function reset(){serial++;root=null;reading=null;value=null;message('관계 목록에서 업계 연결을 선택하세요.');}
    function node(row) {return `<article class="company-network-company"><h4>${link(row.id,row.name)}</h4><small>${esc(row.symbol||'별도 등록 기업')}</small>${(row.brief||[]).map(fact=>`<p>${esc(fact.detail)} ${reading.cite(fact.source)}</p>`).join('')}</article>`;}
    function claims(edge) {
      const rows=edge.evidence?.length?edge.evidence:[edge];
      return rows.map(row=>`<div class="company-network-claim"><p>${esc(row.detail)} ${reading.cite(row.source)}</p><small>${esc(row.source?.as_of||'기준일 미제공')}${row.reverse?' · '+esc(row.reported_by)+' 자료의 역방향 표시':''}</small>${reading.original(row.original)}</div>`).join('')+
        (edge.evidence_total>rows.length?`<small>이 연결의 근거 ${edge.evidence_total}개 중 ${rows.length}개 표시 · 기업 상세에서 전체 확인</small>`:'');
    }
    function draw() {
      if(!value||!reading)return;
      // Only the visible path contributes extra sources; browsing many pages
      // must not accumulate thousands of hidden excerpts in the DOM.
      reading=window.MilkywayCompanyResearchView.create(root);
      // Prices and this path must cite the same visible source registry.
      // Bind the cached price before appending this page's network sources.
      hooks.prepareReading?.(reading);
      reading.registerNetwork(value);
      $('#companyNetwork').innerHTML=`<div class="section-head"><p class="fineprint">${esc(value.root.name)} → ${esc(value.via.name)} → 연결 기업 · 단계별 확인 자료</p><label>연결 기업의 관계<select id="companyNetworkKind"><option value="all">사업 관계 전체</option>${Object.entries(kinds).map(([key,label])=>`<option value="${key}"${value.kind===key?' selected':''}>${label} (${value.counts[key]||0})</option>`).join('')}</select></label><button class="ghost compact" data-network-page="${value.page}">연결 새로 읽기</button></div><div class="company-network-path"><div>${node(value.root)}${value.direct.map(edge=>`<div class="company-network-direct"><strong>${esc(kinds[edge.kind])}</strong>${claims(edge)}</div>`).join('')}</div><div>${node(value.via)}<p class="fineprint">오른쪽 관계의 기준 기업</p></div><div class="company-network-neighbours">${value.rows.map(edge=>`<article class="company-network-company"><span class="relation-kind relation-${esc(edge.kind)}">${esc(kinds[edge.kind])}</span><h4>${link(edge.target_id,edge.name)}</h4>${reading.business(edge)}<strong>확인된 관계</strong>${claims(edge)}</article>`).join('')||'<p class="fineprint">이 분류에서 추가로 확인된 사업 관계가 없습니다. 공개되지 않은 관계는 추정하지 않습니다.</p>'}</div></div><p class="fineprint">두 연결이 있다는 사실만 표시합니다. 첫 기업과 마지막 기업의 직접 거래·계약·거래액을 뜻하지 않습니다.</p><div class="list-paging"><button class="ghost compact" data-network-page="${value.page-1}" ${value.page<=1?'disabled':''}>이전</button><span>${value.page} / ${value.pages} 페이지 · ${value.total}개</span><button class="ghost compact" data-network-page="${value.page+1}" ${value.page>=value.pages?'disabled':''}>다음</button></div>`;
      $('#companyNetworkKind').addEventListener('change',()=>open(value.via.id,$('#companyNetworkKind').value,1));
      hooks.footer(reading);
    }
    async function open(via,kind='all',page=1) {
      if(!valid(root?.entity_key)||!valid(via)||!['all',...Object.keys(kinds)].includes(kind)||!Number.isInteger(page)||page<1||page>50)return;
      const token=++serial,owner=hooks.getState().me?.id,key=root.entity_key;
      message('확인된 업계 연결을 읽는 중입니다…');
      try {
        const result=await hooks.api(`/api/company-entities/${key}/network?via=${via}&kind=${kind}&page=${page}`);
        if(token!==serial||owner!==hooks.getState().me?.id||hooks.getState().workspace!=='company'||root?.entity_key!==key)return;
        value=result;draw();
      } catch(error) {if(token===serial&&owner===hooks.getState().me?.id&&hooks.getState().workspace==='company')message(error.message||'업계 연결을 읽지 못했습니다. 다시 선택하세요.');}
    }
    function page(number) {if(value)open(value.via.id,value.kind,number);}
    return Object.freeze({setContext,reset,open,page});
  }
  window.MilkywayCompanyNetwork=Object.freeze({create});
})();
