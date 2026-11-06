/* Numeric presentation and grouped input parsing; never changes stored values. */
(() => {
  const formats = new Map();
  function number(value, digits = 2, minimum = 0) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    const key = `${digits}:${minimum}`;
    if (!formats.has(key)) formats.set(key, new Intl.NumberFormat('en-US', {
      useGrouping: true, maximumFractionDigits: digits, minimumFractionDigits: minimum,
    }));
    return formats.get(key).format(value);
  }
  function parse(value) {
    const text = String(value ?? '').trim();
    if (!/^[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)$/.test(text)) {
      throw new Error('숫자 형식을 확인하세요. 예: 100,000 또는 0.1');
    }
    const result = Number(text.replaceAll(',', ''));
    if (!Number.isFinite(result)) throw new Error('유효한 숫자를 입력하세요');
    return result;
  }
  const currency = new Intl.NumberFormat("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0});
  const timestamp = new Intl.DateTimeFormat("ko-KR", {month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"});
  function money(value) { return currency.format(value || 0); }
  function pct(value) { return `${Number(value || 0) >= 0 ? "+" : ""}${number(Number(value || 0), 2, 2)}%`; }
  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, character => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[character]));
  }
  function shortTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : timestamp.format(date);
  }
  window.MilkywayFormat = Object.freeze({number, parse, money, pct, escapeHtml, shortTime});
})();
