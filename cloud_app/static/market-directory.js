/* Company directory, monthly news and attributed source lists. Read-only rendering. */
(() => {
  const $=s=>document.querySelector(s),esc=v=>window.MilkywayResearchView.escape(v),fmt=(v,d=2)=>window.MilkywayFormat.number(v,d);
  const time=v=>v?new Date(v).toLocaleString('ko-KR'):'수신 대기';
  const safeUrl=v=>{try{const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password&&(!u.port||u.port==='443')?u.href:null;}catch{return null;}};
  const link=(label,url)=>safeUrl(url)?`<a href="${esc(safeUrl(url))}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:esc(label);
  let data=null,companyPage=1,newsPage=1,query='';
  function companyRows(){return data.companies.rows.filter(row=>`${row.name} ${row.symbol}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));}
  function companies(){
    const all=data.companies.rows,result=window.MilkywayPaging.slice(companyRows(),companyPage);companyPage=result.page;
    $('#detailCompanyCount').textContent=`수집 ${fmt(all.length,0)}개 · 검색 ${fmt(result.total,0)}개 · ${result.page}/${result.pages}페이지`;
    $('#detailCompanyRows').innerHTML=result.rows.length?`<div class="research-table"><table><thead><tr><th>기업</th><th>시가총액</th><th>수집 기업 내 비중</th><th>분류 확인</th></tr></thead><tbody>${result.rows.map(row=>`<tr class="company-table-row" data-company-symbol="${esc(row.symbol)}" data-company-sector="${esc(data.id)}"><td><a class="company-open" data-company-symbol="${esc(row.symbol)}" data-company-sector="${esc(data.id)}" href="#company/${encodeURIComponent(data.id)}/${encodeURIComponent(row.symbol)}">${esc(row.name)}</a><small>${esc(row.symbol)}</small></td><td>${fmt(row.market_cap,0)} ${esc(row.currency)}</td><td>${fmt(row.displayed_share_pct)}${Number.isFinite(row.displayed_share_pct)?'%':''}${window.MilkywayMarketMethods.company(row,all)}${Number.isFinite(row.displayed_share_pct)?`<div class="detail-share-bar"><i style="width:${Math.min(100,Math.max(0,row.displayed_share_pct))}%"></i></div>`:''}</td><td>${row.classification?`<span>공식 구성 공시 대조</span><small>${esc(row.classification.source.as_of)} · ${esc(row.classification.basis)}</small>`:data.id.startsWith('us_')?'<span>공식 분류 미확인</span><small>Yahoo 분류 · 별도 확인 필요</small>':'<span>KOSPI 업종 예시</span>'}</td></tr>`).join('')}</tbody></table></div>`:'<p class="fineprint">검색 조건에 맞는 기업이 없습니다.</p>';
    $('#detailCompanyPages').innerHTML=window.MilkywayPaging.controls(result,'data-company-page');
  }
  function news(){
    const result=window.MilkywayPaging.slice(data.news.rows,newsPage);newsPage=result.page;
    $('#detailNews').innerHTML=`<p class="fineprint">수집 ${esc(time(data.news.fetched_at))} · 최근 30일 · ${fmt(result.total,0)}건 · ${esc(data.news.source||'Google News · 지정 언론사')}${data.news.stale?' · 갱신 지연':''}</p>`+(result.rows.length?result.rows.map(item=>`<article class="detail-news-item">${link(item.title,item.url)}<small>${esc(item.publisher)} · ${esc(time(item.published_at))}</small></article>`).join(''):'<p class="fineprint">현재 출처·기간 조건을 충족하는 관련 보도가 없습니다.</p>')+window.MilkywayPaging.controls(result,'data-news-page');
  }
  function sources(){
    const context=data.context,all=[...context.sources,...data.companies.rows.map(row=>({label:row.name+' · '+row.source,url:row.url,kind:'기업'})),...data.companies.rows.filter(row=>row.classification).map(row=>({label:row.classification.source.label,url:row.classification.source.url,kind:'분류 · '+row.classification.source.as_of})),...(context.market_share||[]).map(row=>({label:row.provider+' · '+row.title,url:row.url,kind:'시장점유율'})),...data.news.rows.map(row=>({label:row.publisher+' · '+row.title,url:row.url,kind:'보도'}))];
    const guideSources=Object.entries(data.industry_guide?.sources||{}).map(([id,row])=>({...row,id:/^[a-z][a-z0-9-]{0,30}$/.test(id)?'energy-source-'+id:null}));
    const unique=[...new Map([...all,...guideSources].map(row=>[row.url,row])).values()];
    $('#detailSourceCount').textContent=`출처 모음 · ${fmt(unique.length,0)}개`;
    $('#detailSources').innerHTML=unique.map(row=>`<p${row.id?` id="${esc(row.id)}"`:''}><small>${esc(row.kind)}</small> ${link(row.label,row.url)}</p>`).join('');
  }
  function render(next){
    if(data?.id!==next.id){companyPage=newsPage=1;query='';}data=next;
    const all=data.companies.rows;
    $('#detailCompanies').innerHTML=all.length?`<p class="fineprint">비중 = 기업 시총 ÷ 현재 수집한 ${fmt(all.length,0)}개 기업 시총 합계. 페이지·검색을 바꿔도 분모는 같습니다. 제품·매출 시장점유율이나 공식 지수 비중과는 다릅니다.</p><div class="company-list-tools"><input id="detailCompanySearch" type="search" placeholder="기업명 또는 종목 코드 검색" aria-label="섹터 기업 검색" value="${esc(query)}"><span id="detailCompanyCount"></span></div><div id="detailCompanyRows"></div><div id="detailCompanyPages"></div>`:data.group==='sectors'?'<p class="fineprint">기업 수치 수신 대기 · 출처 모음에서 원자료를 확인하세요.</p>':data.context.sources.filter(row=>row.kind!=='시세').map(row=>`<p>${link(row.label,row.url)}</p>`).join('');
    const audit=data.companies.classification_audit;
    if(audit){const note=document.createElement('p');note.className='fineprint';note.textContent=`분류 대조: 기존 ${fmt(audit.checked,0)}개 확인 · 공시 대조 ${fmt(audit.matched,0)}개 · 미확인 ${fmt(audit.unverified,0)}개 · 다른 섹터로 정정 ${fmt(audit.moved.length,0)}개${audit.stale?' · 분류 공시 갱신 필요':''}${audit.omitted?' · 표시 상한 초과 '+fmt(audit.omitted,0)+'개':''}. ${audit.method}`;$('#detailCompanies').prepend(note);}
    if(all.length)companies();news();sources();
  }
  function initialize(){
    $('#detailCompanies').addEventListener('input',event=>{if(event.target.id==='detailCompanySearch'){query=event.target.value;companyPage=1;companies();}});
    $('#detailCompanies').addEventListener('click',event=>{const b=event.target.closest('[data-company-page]');if(b){companyPage=Number(b.dataset.companyPage);companies();}});
    $('#detailNews').addEventListener('click',event=>{const b=event.target.closest('[data-news-page]');if(b){newsPage=Number(b.dataset.newsPage);news();$('#detailNewsSection').scrollIntoView({behavior:'smooth',block:'start'});}});
  }
  window.MilkywayMarketDirectory=Object.freeze({initialize,render,link});
})();
