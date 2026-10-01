/* Pure, deterministic relationship selection and SVG layout. No AI or provider I/O. */
(() => {
  const kinds = Object.freeze({
    supplier: '공급사', customer: '고객사', partner: '협력사', competitor: '경쟁사',
    parent: '모회사', subsidiary: '자회사', owner: '소유·지분 관계', holding: '보유·지분 기업',
  });
  const colors = Object.freeze({
    supplier: '#e9be77', customer: '#85b9ed', partner: '#7dcfb5', competitor: '#e99099',
    parent: '#b69aef', subsidiary: '#b69aef', owner: '#9298a9', holding: '#9298a9',
  });
  const operating = new Set(['supplier', 'customer', 'partner', 'competitor']);
  const order = Object.keys(kinds);
  const sourceRank = {primary: 0, provider: 1};
  const esc = value => window.MilkywayResearchView.escape(value);
  const evidence = edge => edge.evidence?.length ? edge.evidence : [edge];
  const statementDate = item => /^\d{4}-\d{2}-\d{2}$/.test(item.source?.as_of || '') ? item.source.as_of : '';
  function lead(edge) {
    return [...evidence(edge)].sort((a, b) =>
      (sourceRank[a.source?.level] ?? 3) - (sourceRank[b.source?.level] ?? 3)
      || statementDate(b).localeCompare(statementDate(a)))[0];
  }
  function select(rows, filter) {
    const score = edge => (operating.has(edge.kind) ? 0 : 100)
      + (sourceRank[lead(edge).source?.level] ?? 3) * 10 + order.indexOf(edge.kind);
    return rows.map((edge, index) => ({...edge, index})).filter(edge =>
      filter === 'all' || (filter === 'business' ? !['owner', 'holding'].includes(edge.kind) : edge.kind === filter)
    ).sort((a, b) => score(a) - score(b) || a.name.localeCompare(b.name, 'ko') || a.index - b.index);
  }
  function lines(value, width, maximum = 2) {
    let chars = Array.from(String(value || '').replace(/\s+/g, ' ').trim());
    return Array.from({length: maximum}, (_, index) => {
      let length = Math.min(width, chars.length);
      if (chars.length > width && index < maximum - 1) {
        const space = chars.slice(0, width + 1).lastIndexOf(' ');
        if (space >= Math.floor(width / 3)) length = space;
      }
      const text = chars.slice(0, length).join('');
      chars = chars.slice(length);
      while (chars[0] === ' ') chars.shift();
      return text + (index === maximum - 1 && chars.length ? '…' : '');
    });
  }
  function draw(name, symbol, rows) {
    if (!rows.length) return '';
    const rowCount = Math.ceil(rows.length / 2), height = Math.max(360, rowCount * 140 + 100), centerY = height / 2;
    const firstY = (height - (rowCount - 1) * 140) / 2;
    const points = rows.map((edge, index) => ({...edge,
      x: index % 2 ? 850 : 150, y: firstY + Math.floor(index / 2) * 140}));
    const connectors = points.map(point => {
      const left = point.x < 500, fromX = left ? 405 : 595, toX = left ? 280 : 720;
      const incoming = ['supplier', 'parent', 'owner'].includes(point.kind);
      const outgoing = ['customer', 'subsidiary', 'holding'].includes(point.kind);
      const marker = incoming ? 'marker-start' : outgoing ? 'marker-end' : '';
      return `<path d="M ${fromX} ${centerY} C ${left ? 340 : 660} ${centerY}, ${left ? 340 : 660} ${point.y}, ${toX} ${point.y}" stroke="${colors[point.kind]}" class="company-graph-edge"${marker ? ` ${marker}="url(#company-arrow-${incoming ? 'start' : 'end'})"` : ''}/>`;
    }).join('');
    const nodes = points.map(point => {
      const item = lead(point), title = lines(point.name, 24);
      const detail = lines(item.detail || '사업 역할 설명 미등록', 27);
      const origin = {primary: '기업·공시 원문', provider: '정보 제공사·조사'}[item.source?.level] || '출처 확인';
      const valid = /^c_[a-f0-9]{32}$/.test(point.target_id || '');
      const open = valid ? `<a role="link" tabindex="0" href="#company/${point.target_id}" data-company-id="${point.target_id}" aria-label="${esc(point.name + ' 기업 상세 · ' + kinds[point.kind])}" class="company-graph-node">` : '<g>';
      return `${open}<title>${esc(point.name + ' · ' + kinds[point.kind] + '\n' + (item.detail || '') + '\n' + origin)}</title><rect x="${point.x - 130}" y="${point.y - 61}" width="260" height="122" rx="12" fill="#14111d" stroke="${colors[point.kind]}"/><text x="${point.x}" y="${point.y - 42}" text-anchor="middle" fill="${colors[point.kind]}" class="graph-kind">${esc(kinds[point.kind])}</text>${title.map((text, index) => `<text x="${point.x}" y="${point.y - 21 + index * 16}" text-anchor="middle" class="graph-name">${esc(text)}</text>`).join('')}${detail.map((text, index) => `<text x="${point.x}" y="${point.y + 16 + index * 14}" text-anchor="middle" class="graph-role">${esc(text)}</text>`).join('')}<text x="${point.x}" y="${point.y + 49}" text-anchor="middle" class="graph-evidence">${esc(origin)} · 근거 ${evidence(point).length}건</text>${valid ? '</a>' : '</g>'}`;
    }).join('');
    return `<svg class="company-graph" viewBox="0 0 1000 ${height}" role="group" aria-label="${esc(name)} 기업 관계도"><defs><marker id="company-arrow-end" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 Z" fill="#c4b4db"/></marker><marker id="company-arrow-start" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 Z" fill="#c4b4db"/></marker></defs>${connectors}<rect x="405" y="${centerY - 46}" width="190" height="92" rx="16" class="company-graph-center"/>${lines(name, 16).map((text, index) => `<text x="500" y="${centerY - 13 + index * 18}" text-anchor="middle" class="graph-center-title">${esc(text)}</text>`).join('')}<text x="500" y="${centerY + 29}" text-anchor="middle" class="graph-center-symbol">${esc(symbol || '기업 관계 자료')}</text>${nodes}</svg>`;
  }
  window.MilkywayCompanyRelations = Object.freeze({kinds, evidence, lead, select, draw});
})();
