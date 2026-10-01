/* Essential reading, annual revenue and bottom-only citations. No network calls. */
(() => {
  const esc = value => window.MilkywayResearchView.escape(value);
  const fmt = (value, digits = 0) => window.MilkywayFormat.number(value, digits);
  const groups = Object.freeze({product: '제품·서비스', segment: '보고 사업 부문', geography: '지역', revenue_type: '제품 매출·서비스 매출 구분'});
  const levels = {primary: '공시·기업 원문', provider: '정보 제공사·공개 조사'};
  const metrics = Object.freeze({'us-gaap:Revenues': '매출', 'us-gaap:SalesRevenueNet': '순매출',
    'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax': '계약 고객 매출(부과세 제외)', 'ifrs-full:Revenue': 'IFRS 매출'});
  function accepted(source) {
    try {
      const url = new URL(source?.url);
      return source?.level !== 'encyclopedia' && url.protocol === 'https:'
        && !url.username && !url.password && (!url.port || url.port === '443')
        && !/(^|\.)(wikipedia|wikidata|wikimedia)\.org$/i.test(url.hostname.replace(/\.$/, ''));
    } catch { return false; }
  }
  function identity(source) {
    const url = new URL(source.url); url.hash = '';
    return url.href + '|' + (source.as_of || '');
  }
  const quoteSource = (row, date) => row?.url ? {label: row.source || '시세 제공사',
    url: row.url, as_of: date || null, level: 'provider'} : null;
  function create(data) {
    const sources = new Map(), excerpts = new Map();
    function add(source, title) {
      if (!accepted(source)) return;
      const key = identity(source);
      if (!sources.has(key)) sources.set(key, {...source, url: source.url.split('#')[0], number: sources.size + 1, locations: new Map()});
      if (new URL(source.url).hash) sources.get(key).locations.set(source.url, title || source.label);
    }
    for (const row of data.brief || []) add(row.source, row.title);
    for (const source of [...(data.sources || []), ...(data.filings || []), data.description_source,
      data.report_analysis?.source, quoteSource(data.quote, data.quote_basis?.fetched_at),
      ...(data.peers || []).map(row => quoteSource(row, data.quote_basis?.fetched_at))]) add(source);
    for (const key of ['brief', 'products', 'segments', 'facts', 'drivers', 'market_shares', 'financials', 'revenue_mix']) {
      for (const row of data[key] || []) {
        add(row.source, row.title || row.label);
        if (row.original && accepted(row.source)) excerpts.set(row.title + '|' + row.original,
          {title: row.title, text: row.original, source: row.source});
      }
    }
    for (const edge of data.relations || []) {
      for (const row of edge.evidence?.length ? edge.evidence : [edge]) {
        add(row.source, edge.name + ' · 관계 근거');
        if (row.original && accepted(row.source)) excerpts.set(edge.name + '|' + row.original,
          {title: edge.name + ' · 관계 원문', text: row.original, source: row.source});
      }
    }
    function cite(source) {
      if (!accepted(source)) return '';
      const row = sources.get(identity(source));
      return row ? `<a class="company-citation-ref" data-company-citation="${row.number}" href="#company-source-${row.number}" aria-label="출처 ${row.number} 보기">[${row.number}]</a>` : '';
    }
    function original(text, title = '영문 원문 확인') {
      return text ? `<details class="company-original"><summary>${esc(title)}</summary><p lang="en">${esc(text)}</p><small>한글 핵심 정리와 구분한 공시 발췌입니다. 하단 출처에서 무료 번역으로 읽을 수 있습니다.</small></details>` : '';
    }
    function fact(row) {
      if (!accepted(row.source)) return '';
      return `<article class="company-fact"><h4>${esc(row.title)} ${cite(row.source)}</h4>${row.detail ? `<p>${esc(row.detail)}</p>` : ''}${original(row.original)}</article>`;
    }
    function essentials() {
      const cards = (data.brief || []).filter(row => row.detail && accepted(row.source));
      return cards.length ? cards.map(fact).join('')
        : '<article class="company-fact"><h4>핵심 정리 확인 대기</h4><p>이 기업의 한글 사업 요약은 아직 검토되지 않았습니다. 아래에 확보한 매출 구성과 공시 자료만 표시합니다.</p></article>';
    }
    function revenue(group) {
      const rows = (data.revenue_mix || []).filter(row => row.group === group && accepted(row.source));
      if (!rows.length) return '<p class="fineprint">동일 공시의 연간 매출 구성 수치를 확인하지 못했습니다. 임의 비중은 계산하지 않습니다.</p>';
      const sorted = rows.filter(row => !row.parent).sort((a, b) => b.value - a.value)
        .flatMap(row => [row, ...rows.filter(child => child.parent === row.member).sort((a, b) => b.value - a.value)]);
      sorted.push(...rows.filter(row => row.parent && !rows.some(parent => parent.member === row.parent)));
      const first = rows[0];
      return `<p class="company-revenue-period">연간 ${esc(first.start)} ~ ${esc(first.end)} · ${esc(first.unit)} · 지표: ${esc(metrics[first.metric] || first.metric)}</p>
        <div class="research-table"><table><thead><tr><th>${esc(groups[group])}</th><th>매출</th><th>같은 매출 지표 내 비중</th><th>근거</th></tr></thead><tbody>${sorted.map(row => {
          const share = Number.isFinite(row.total) && row.total > 0 && row.value <= row.total ? row.value / row.total * 100 : null;
          return `<tr${row.parent ? ' class="company-revenue-child"' : ''}><td>${row.parent ? '<span aria-label="상위 항목에 포함">↳ </span>' : ''}${esc(row.label)}</td><td>${fmt(row.value)} ${esc(row.unit)}</td><td>${share === null ? '분모 미확인' : fmt(share, 2) + '%'}</td><td>${cite(row.source)}</td></tr>`;
        }).join('')}</tbody></table></div>
        <details class="company-revenue-method"><summary>매출 구성 계산 방법·포함 관계</summary><p>비중 = 해당 항목 매출 ÷ 같은 공시·매출 지표·기간·통화의 연결 매출 × 100. 분모가 정확히 일치할 때만 계산합니다. 지표에 따라 금융업의 전체 수익 등과 범위가 다를 수 있습니다. 시장점유율이나 이익 비중이 아닙니다. 제품·사업 부문·지역은 서로 다른 구분이며 더하지 않습니다. ↳ 행은 상위 항목에 포함되므로 다시 합산하지 않습니다. 다른 항목도 중복될 수 있어 화면 전체의 합계를 만들지 않습니다.</p><dl>${rows.map(row => `<dt>${esc(row.label)}</dt><dd>공시 식별자 ${esc(row.member)} · 지표 ${esc(row.metric)}${row.total ? ' · 비중 분모 ' + fmt(row.total) + ' ' + esc(row.unit) : ' · 일치하는 분모 미확인'} ${cite(row.source)}</dd>`).join('')}</dl></details>`;
    }
    function footer() {
      const external = (label, url) => window.MilkywayMarketDirectory.link(label, url);
      const rows = [...sources.values()];
      return `<ol class="company-source-list">${rows.map(row => `<li id="company-source-${row.number}"><strong>${external(row.label, row.url)}</strong><small>${esc(levels[row.level] || '출처')} · ${esc(row.as_of ? '자료 기준 ' + row.as_of : '원자료 기준일 미제공')}</small><small>${esc(new URL(row.url).hostname)}</small>${row.locations.size ? `<details class="company-source-locations"><summary>이 자료의 근거 위치 · ${fmt(row.locations.size)}개</summary><ul>${[...row.locations].map(([url, title]) => `<li>${external(title, url)}</li>`).join('')}</ul></details>` : ''}</li>`).join('')}</ol>
        ${excerpts.size ? `<details class="company-translations"><summary>영문 발췌 한글로 읽기 · 무료 외부 번역</summary><p class="fineprint">선택한 공개 발췌문만 Google 번역 새 창으로 보냅니다. 자동 호출은 없으며 기계 번역은 검토된 한글 요약과 다릅니다.</p><ul>${[...excerpts.values()].map(row => `<li>${external(row.title, 'https://translate.google.com/?sl=en&tl=ko&op=translate&text=' + encodeURIComponent(row.text))} ${cite(row.source)}</li>`).join('')}</ul></details>` : ''}`;
    }
    return Object.freeze({cite, fact, original, essentials, revenue, footer, count: sources.size,
      groups: Object.keys(groups).filter(key => (data.revenue_mix || []).some(row => row.group === key)), quoteSource});
  }
  window.MilkywayCompanyResearchView = Object.freeze({create, accepted, groups});
})();
