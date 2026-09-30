/* Shared, bounded pagination for collected companies and articles. */
(() => {
  function slice(rows, page=1, size=8) {
    const total=rows.length,pages=Math.max(1,Math.ceil(total/size));
    page=Math.max(1,Math.min(pages,Number.isInteger(page)?page:1));
    return {rows:rows.slice((page-1)*size,page*size),page,pages,total};
  }
  function controls(result, attribute) {
    if(result.pages<2)return '';
    if(!/^data-[a-z-]+$/.test(attribute))throw new Error('Invalid pagination attribute');
    const button=(page,label,current=false)=>`<button type="button" class="ghost compact" ${attribute}="${page}" ${current?'aria-current="page"':''} aria-label="${label} 페이지">${label}</button>`;
    const numbers=[...new Set([1,result.pages,...Array.from({length:5},(_,i)=>result.page+i-2).filter(n=>n>=1&&n<=result.pages)])].sort((a,b)=>a-b);
    let last=0;
    return `<nav class="detail-pagination" aria-label="페이지 이동">${result.page>1?button(result.page-1,'이전'):''}${numbers.map(n=>{const gap=last&&n-last>1?'<span aria-hidden="true">…</span>':'';last=n;return gap+button(n,n,n===result.page);}).join('')}${result.page<result.pages?button(result.page+1,'다음'):''}</nav>`;
  }
  window.MilkywayPaging=Object.freeze({slice,controls});
})();
