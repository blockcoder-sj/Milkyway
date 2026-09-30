/* Formula text mirrors the actual display transformations; no market interpretation. */
(() => {
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=value=>Number.isFinite(value)?String(value):'미수신';
  function help(id,paragraphs,label='계산 방법'){
    return `<details class="metric-method" data-method-id="${esc(id)}"><summary>${esc(label)}</summary>${paragraphs.map(p=>`<p>${esc(p)}</p>`).join('')}</details>`;
  }
  function replace(target,html){
    const open=new Set([...target.querySelectorAll('details[open][data-method-id]')].map(d=>d.dataset.methodId));
    target.innerHTML=html;
    for(const detail of target.querySelectorAll('details[data-method-id]'))detail.open=open.has(detail.dataset.methodId);
  }
  function quote(row){
    const available=Number.isFinite(row.value)&&Number.isFinite(row.previous_close)&&row.previous_close>0;
    return help('quote-'+row.id,[
      `현재값은 ${row.source||'시세 공급자'}가 제공한 값을 표시합니다. 지수의 구성 종목·가중치·제수로 앱에서 재산출한 값은 아닙니다. 상세 출처 모음의 산출기관 원문에서 지수 산식을 확인할 수 있습니다.`,
      `등락 = 현재값 − 전일 기준값. 등락률 = (현재값 ÷ 전일 기준값 − 1) × 100. ${available?`(${num(row.value)} ÷ ${num(row.previous_close)} − 1) × 100 = ${num((row.value/row.previous_close-1)*100)}%.`:'동일 공급자의 기준값이 없으면 계산하지 않습니다.'}`,
      `전일 기준값은 같은 공급자의 기준 종가를 사용합니다. 한국투자증권 업종 지수는 현재값에서 제공 등락폭을 빼서 복원합니다. 기준 시각: ${row.observed_at||'미수신'}.`,
      row.id==='jpykrw'?'100엔 환율은 Yahoo의 1엔당 원화 시세 × 100입니다. 현재값·기준값·가격 범위에 동일한 배율을 적용합니다.':'환율·선물·원자재도 공급자 시세와 표시 단위를 그대로 사용합니다.',
      '당일·52주 범위는 공급자의 고가·저가 항목입니다. 현재 화면의 차트 구간에서 다시 계산한 값이 아닙니다. 화면 숫자는 표시 자릿수로 반올림하며 계산에는 반올림 전 값을 사용합니다.'
    ]);
  }
  function metric(key,result,digits=2){
    const rows=result.rows;
    const scope=`${rows[0].date} ~ ${rows.at(-1).date}, 선택한 주기의 ${rows.length}개 봉. 화면은 소수 ${['high','low'].includes(key)?digits:2}자리까지 반올림합니다.`;
    const texts={
      change:[`기간 등락률 = (마지막 종가 ÷ 첫 종가 − 1) × 100. (${num(result.last_close)} ÷ ${num(result.first_close)} − 1) × 100.`, '봉이 하나이면 기간 등락률을 계산하지 않습니다. 배당·환전·거래비용은 포함하지 않습니다.'],
      high:['기간 최고 = 선택 구간에서 유효한 봉 고가의 최댓값. OHLC가 불완전한 봉은 이 계산에서 제외합니다.'],
      low:['기간 최저 = 선택 구간에서 유효한 봉 저가의 최솟값. OHLC가 불완전한 봉은 이 계산에서 제외합니다.'],
      drawdown:[`각 시점 낙폭 = (그 봉의 종가 ÷ 그 시점까지의 최고 종가 − 1) × 100. 이 값들의 최솟값입니다. 최저 낙폭의 입력값: (${num(result.drawdown_trough)} ÷ ${num(result.drawdown_peak)} − 1) × 100.`, '장중 저가를 사용하지 않으며, 봉이 하나이면 계산하지 않습니다. 주봉·월봉을 선택하면 그 주기의 종가로 계산합니다.']
    };
    return help('metric-'+key,[...texts[key],scope]);
  }
  function chart(part){
    const q=part.quality;
    return help('chart-method',[
      '일봉은 Yahoo가 제공한 시가·고가·저가·종가(OHLC)입니다. 배당 반영 조정종가로 대체하지 않습니다. 날짜는 거래소 시간대 기준입니다. 장중 마지막 봉은 아직 완료되지 않았을 수 있습니다.',
      '주봉은 월요일 시작 주, 월봉은 달력 월로 묶습니다. 시가=첫 일봉 시가, 고가=최댓값, 저가=최솟값, 종가=마지막 일봉 종가, 거래량=합계입니다. 봉의 마지막 거래일이 선택 기간에 속하면 표시하므로 첫 주·월봉은 시작일 전의 일봉을 포함할 수 있습니다. 종료일 이후의 자료는 사용하지 않아 마지막 주·월봉이 미완료일 수 있습니다.',
      '5·20·60·120봉 단순이동평균 = 해당 봉을 포함한 최근 N개 종가 합 ÷ N. 선택한 봉 주기에 따라 계산하며, 화면 시작일 이전에 수집한 봉도 사용합니다. N개가 없으면 값을 만들지 않고 미표시합니다. 최대 3년의 수집 범위가 계산 한계입니다.',
      '선은 수신한 종가 순서대로 연결합니다. 주말·휴장일을 포함해 값이 없는 날짜는 만들지 않습니다. 날짜 사이 간격은 거래 봉 간격이며 실제 달력 시간 간격과 다릅니다. 일반 눈금은 가격, 로그 눈금은 자연로그를 같은 간격으로 배치합니다.',
      'OHLC 범위가 맞지 않아도 양수인 유효 종가는 보존합니다. 이런 봉은 캔들 대신 보라색 점으로 표시합니다. 주·월 안에 불완전한 일봉이 있으면 해당 주·월도 종가만 표시합니다. 거래량이 하나라도 누락되면 그 집계 봉의 거래량은 표시하지 않습니다.',
      q?`최근 수집 응답: ${q.received}개, 수집 범위 밖 ${q.outside_range}개, 날짜·종가 검증 실패 ${q.invalid_close}개 제외, OHLC 불완전 ${q.close_only}개는 종가 보존, 날짜 중복 ${q.duplicates}개 제거, 최종 ${q.accepted}개. 이후 3년 범위가 지나면 화면에서 추가 제외됩니다.`:'이 캐시는 수집 품질 집계 전 자료입니다. 다음 갱신부터 원자료 검증 건수를 표시합니다.'
    ],'차트 계산 방법·원자료 검증');
  }
  function company(row,rows){
    const total=rows.reduce((sum,item)=>sum+(item.market_cap||0),0);
    return help('company-'+row.symbol,[
      `표시 기업 내 비중 = 기업 시가총액 ÷ 표에 표시한 기업 시가총액 합계 × 100. ${num(row.market_cap)} ÷ ${num(total)} × 100. 같은 통화의 표시 기업만 분모에 포함합니다. 하나라도 시총이 누락되면 비중 계산을 보류합니다.`,
      '시가총액은 공급자가 공표한 값입니다. 앱이 주가와 발행주식 수를 별도로 곱해 재계산하지 않습니다. Npay의 조·억 표기는 각각 10¹²·10⁸을 곱해 KRW로 변환합니다. 축약 시총과 비중은 화면에서 반올림합니다.',
      '이 표의 표본 내 시총 비중입니다. 제품·매출 시장점유율이나 공식 지수 구성 비중이 아닙니다.'
    ]);
  }
  window.MilkywayMarketMethods=Object.freeze({help,replace,quote,metric,chart,company});
})();
