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
  window.MilkywayFormat = Object.freeze({number, parse});
})();
