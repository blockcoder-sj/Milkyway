/* Cached trade prices; owner/navigation guards. Provider credentials stay server-side. */
(() => {
  const esc = value => window.MilkywayResearchView.escape(value);
  const fmt = (value, digits = 2) => window.MilkywayFormat.number(value, digits, digits);
  const labels = {realtime:'실시간 체결', polled:'현재가 · 15초 조회', reference:'참고 시세',
    last_trade:'마지막 체결', delayed:'참고 시세 · 지연 가능', closed:'장 종료 기준', stale:'이전 시세 · 갱신 실패'};
  const valid = value => /^c_[a-f0-9]{32}$/.test(value || '');
  function html(price, cite = () => '') {
    if (!Number.isFinite(price?.value) || price.value <= 0) return `<p class="fineprint">${esc(price?.note || '현재 주가 수신 대기')}</p>`;
    const digits = price.currency === 'KRW' ? 0 : 2;
    const positive = price.change > 0, negative = price.change < 0;
    const source = {label:price.source+' · 기업 현재가', url:price.source_url, level:'provider'};
    const baseline = price.comparison_source_url ? {label:price.comparison_source, url:price.comparison_source_url, level:'provider'} : null;
    const when = price.observed_at ? new Date(price.observed_at).toLocaleString('ko-KR') : '체결 시각 미제공';
    return `<div class="company-current-price"><small>현재 주가 · ${esc(price.currency)}</small><strong>${fmt(price.value,digits)}</strong>
      ${Number.isFinite(price.change_pct) ? `<span class="${positive?'up':negative?'down':'flat'}">${positive?'+':''}${fmt(price.change,digits)} (${positive?'+':''}${fmt(price.change_pct)}%)</span>` : '<span class="fineprint">전일 비교 기준값 미수신</span>'}
      <small>${esc(labels[price.status] || '참고 시세')} · ${esc(price.source)} ${cite(source)}</small><small>시세 기준 ${esc(when)}</small>
      <details class="company-price-method"><summary>주가·등락 표시 방법</summary><p>시세 기준 시각은 공급자가 제공한 체결·가격 시각입니다. 수신 시각과 다릅니다. 화면은 2초마다 캐시를 확인합니다. 토스증권 체결 스트림을 우선하고 초기·미수신 시 REST 현재가로 보완합니다. 무료 참고 시세는 1분마다 수집합니다.</p>
      ${price.previous_close ? `<p>등락 = 현재가 ${fmt(price.value,digits)} − 전일 종가 ${fmt(price.previous_close,digits)}. 등락률 = 등락 ÷ 전일 종가 × 100. 전일 종가 출처: ${esc(price.comparison_source || price.source)} ${cite(baseline || source)}. 다른 제공사의 전일 종가는 같은 현지 거래일일 때만 함께 사용합니다.</p>` : '<p>확인된 전일 종가가 없어 등락을 계산하지 않았습니다.</p>'}
      <p>최근 수신 ${esc(new Date(price.fetched_at).toLocaleString('ko-KR'))}${price.delay_minutes != null ? ' · 공급자 보고 지연 '+fmt(price.delay_minutes,0)+'분' : ''}.</p></details></div>`;
  }
  function create({api,getState,target,footer}) {
    let context = null, reading = null, epoch = 0, pending = null, watchAt = 0, latest = null;
    function clear() {context=null;reading=null;latest=null;++epoch;target.innerHTML='';}
    function useReading(nextReading) {
      reading=nextReading;
      if(latest&&reading){reading.registerPrice(latest);target.innerHTML=html(latest,reading.cite);}
    }
    function setContext(data,nextReading) {
      reading=nextReading;
      if (!valid(data.entity_key) || !data.symbol) {clear();target.innerHTML='<p class="fineprint">시세 종목 미연결 기업·기관</p>';return;}
      const key=data.entity_key+'|'+data.symbol+'|'+getState().me?.id;
      if (context?.key!==key) {context={key,entity:data.entity_key,symbol:data.symbol,actor:getState().me?.id};++epoch;watchAt=0;latest=null;target.innerHTML='<p class="fineprint">현재 주가 수신 대기</p>';}
      if(latest){reading.registerPrice(latest);target.innerHTML=html(latest,reading.cite);}
      refresh();
    }
    async function refresh() {
      if (!context || pending===epoch || getState().workspace!=='company' || getState().me?.id!==context.actor || document.hidden) return;
      const token=epoch, current=context;
      const active=()=>token===epoch&&context===current&&getState().workspace==='company'&&getState().me?.id===current.actor;
      pending=token;
      try {
        const base='/api/company-entities/'+current.entity;
        const query='?symbol='+encodeURIComponent(current.symbol);
        if(Date.now()>=watchAt){watchAt=Date.now()+30000;await api(base+'/price-watch'+query,{method:'POST'});if(!active())return;}
        const result=await api(base+'/price'+query);
        if(!active()||result.symbol!==current.symbol)return;
        latest=result;reading.registerPrice(result);target.innerHTML=html(result,reading.cite);footer();
      } catch (error) {if(active()){if(latest){latest={...latest,status:'stale'};target.innerHTML=html(latest,reading.cite);}else target.innerHTML=`<p class="fineprint">${esc(error.message)}</p>`;}}
      finally {if(pending===token)pending=null;}
    }
    setInterval(refresh,2000);
    return Object.freeze({setContext,useReading,clear,refresh});
  }
  window.MilkywayCompanyPrice=Object.freeze({create,html});
})();
