/* Industry notes are independent of company trades and quote calculations. */
(() => {
  const esc=value=>window.MilkywayResearchView.escape(value);
  let signature='';
  const refs=ids=>(ids||[]).filter(id=>/^[a-z][a-z0-9-]{0,30}$/.test(id)).map(id=>`<a class="energy-reference" href="#energy-source-${id}" data-energy-source="${id}">출처</a>`).join(' ');
  function entry(item,index,section){
    const id=`energy-${section}-${index}`;
    return `<details class="energy-topic" id="${esc(id)}"><summary>${esc(item.title)}</summary><div><p>${esc(item.body)}</p>${item.steps?.length?`<ol class="energy-flow" aria-label="산업의 처리 순서">${item.steps.map(step=>`<li>${esc(step)}</li>`).join('')}</ol>`:''}${item.formula?`<p class="energy-formula">${esc(item.formula)}</p>`:''}${item.caveat?`<p class="fineprint">${esc(item.caveat)}</p>`:''}<p class="energy-references">${refs(item.source_ids)}</p></div></details>`;
  }
  function render(guide){
    const panel=document.getElementById('detailIndustrySection'),jump=document.getElementById('detailIndustryJump');
    panel.hidden=!guide;jump.hidden=!guide;
    if(!guide){panel.innerHTML='';signature='';return;}
    const next=JSON.stringify(guide);
    if(next===signature)return;
    const expanded=new Set([...panel.querySelectorAll('details[open]')].map(node=>node.id));
    signature=next;
    panel.innerHTML=`<header class="energy-guide-heading"><div><p class="eyebrow">INDUSTRY GUIDE</p><h3>${esc(guide.title)}</h3></div><span class="fineprint">자료 확인 ${esc(guide.checked_at)}</span></header><p>${esc(guide.scope)}</p><nav class="energy-guide-nav" aria-label="산업 구조 목차"><a href="#energy-industries">세부 업종</a>${guide.sections.map(section=>`<a href="#energy-section-${esc(section.id)}">${esc(section.title)}</a>`).join('')}</nav><section id="energy-industries"><h4>세부 업종 · GICS</h4><p class="fineprint">${esc(guide.classification_note)}</p><div class="energy-industries">${guide.industries.map(row=>`<article><small>${esc(row.code)}</small><h5>${esc(row.name)}</h5><strong>${esc(row.label)}</strong><p>${esc(row.body)}</p>${refs(row.source_ids)}</article>`).join('')}</div></section>${guide.sections.map(section=>`<section id="energy-section-${esc(section.id)}"><h4>${esc(section.title)}</h4><p class="fineprint">${esc(section.intro)}</p>${section.entries.map((item,index)=>entry(item,index,section.id)).join('')}</section>`).join('')}`;
    for(const node of panel.querySelectorAll('details'))if(expanded.has(node.id))node.open=true;
  }
  function initialize(){
    document.getElementById('detailIndustrySection').addEventListener('click',event=>{
      const anchor=event.target.closest('a[href^="#"]');
      if(!anchor||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
      const target=document.getElementById(anchor.getAttribute('href').slice(1));
      if(!target)return;
      event.preventDefault();
      const disclosure=anchor.hasAttribute('data-energy-source')?target.closest('details'):null;
      if(disclosure)disclosure.open=true;
      target.scrollIntoView({behavior:'smooth',block:'start'});
    });
  }
  window.MilkywayEnergyGuide=Object.freeze({initialize,render});
})();
