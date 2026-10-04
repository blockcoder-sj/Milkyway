/* Real xyz geometry. Distances are exploration priorities, not financial impact estimates. */
(() => {
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const golden=Math.PI*(3-Math.sqrt(5));
  const hash=s=>{let h=2166136261;for(const c of String(s)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;};
  const revenueGroups={product:'제품·서비스',segment:'사업 부문',geography:'지역',end_market:'최종 시장',revenue_type:'매출 유형'};
  function measure(row){
    const share=!row.includes_intersegment&&!row.share_exclusion&&Number.isFinite(row.total)&&row.total>0&&Number.isFinite(row.value)&&row.value>=0&&row.value<=row.total?row.value/row.total*100:null;
    return {group:row.group,start:row.start,end:row.end,value:row.value,total:row.total,unit:row.unit,metric:row.metric,parent:row.parent,share_pct:share,exclusion:row.share_exclusion|| (row.includes_intersegment?'내부 거래 포함':share===null?'일치하는 분모 미확인':'')};
  }
  function measureText(m){return `${revenueGroups[m.group]||m.group} · ${m.start} ~ ${m.end} · ${Number(m.value).toLocaleString('ko-KR')} ${m.unit} · ${m.share_pct===null?'비중 미산출: '+m.exclusion:'같은 매출 지표 내 '+m.share_pct.toLocaleString('ko-KR',{maximumFractionDigits:2})+'%'} · 지표 ${m.metric}${m.parent?' · 상위 항목에 포함':''}`;}
  function weight(edge,basis='relations'){
    if(edge.kind==='revenue'){const m=edge.measure;return m?.group===basis&&edge.latest&&m.share_pct!==null?4+m.share_pct*.08:1.8;}
    const base={customer:3.5,supplier:3.5,subsidiary:3,parent:3,holding:2.8,owner:2.8,partner:3,competitor:2,transaction:1.7,business_scope:2.2,classification:.55,industry_process:.8,exposure:1.5}[edge.kind]||1;
    return base*(edge.analytical?.65:1)*(edge.citation?.level==='provider'?.85:1);
  }
  function rank(nodes,edges,focus,basis='relations'){
    const adj=new Map(nodes.map(n=>[n.id,new Map()]));
    for(const edge of edges){
      if(edge.source===edge.target||!adj.has(edge.source)||!adj.has(edge.target))continue;
      for(const[a,b]of[[edge.source,edge.target],[edge.target,edge.source]])adj.get(a).set(b,Math.max(weight(edge,basis),adj.get(a).get(b)||0));
    }
    const hops=new Map(),scores=new Map();
    if(adj.has(focus)){
      hops.set(focus,0);scores.set(focus,100);let frontier=[focus];
      for(let depth=1;depth<=3;depth++){
        const next=new Set();
        for(const a of frontier)for(const[b,w]of adj.get(a)){
          if(hops.has(b)&&hops.get(b)<depth)continue;
          const score=depth===1?w*20:(scores.get(a)||0)*w/3.5*.35;
          hops.set(b,depth);scores.set(b,Math.max(score,scores.get(b)||0));next.add(b);
        }frontier=[...next];
      }
    }
    return nodes.map(n=>({...n,hops:hops.get(n.id)??4,priority:scores.get(n.id)||0,degree:adj.get(n.id).size}))
      .sort((a,b)=>a.hops-b.hops||b.priority-a.priority||b.degree-a.degree||a.id.localeCompare(b.id));
  }
  const topics=[['원유',/원유|crude|upstream/i],['가스·LNG',/천연가스|\blng\b|natural gas|액화|\bngl\b/i],['정유·연료',/정유|refin|연료|fuel/i],['운송·저장',/운송|저장|파이프라인|midstream|pipeline|shipping|storage/i],['시추·서비스',/시추|유정|리그|drilling|fractur|oilfield/i],['전력',/발전|전력|electric|power/i],['석탄',/석탄|\bcoal\b/i],['우라늄',/우라늄|원자력|uranium|nuclear/i],['화학',/화학|chemical/i],['재생 에너지',/재생|바이오|renewable|biofuel/i]];
  function topic(n){const text=(n.name||'')+' '+(n.description||'');return topics.find(([,re])=>re.test(text))?.[0]||({issuer:'기업',company:'기업',product:'사업 요소',segment:'사업 부문',factor:'사업 요인',revenue:revenueGroups[n.measure?.group]||'매출 구성',group:'업종',sector:'섹터'}[n.kind]||'기타');}
  function layout(nodes,edges,focus,flat=false,basis='relations'){
    const ordered=rank(nodes,edges,focus,basis),groups=new Map(),out=[];
    for(const n of ordered){if(!groups.has(n.hops))groups.set(n.hops,[]);groups.get(n.hops).push(n);}
    // The selected neighbourhood does not expand when unrelated nodes are added.
    // Overlap is allowed; projection must never move planets into vacant slots.
    for(const[hop,group]of groups){
      if(hop===0){out.push({...group[0],x:0,y:0,z:0});continue;}
      const base=[0,65,210,410,700][hop],range=[0,60,70,120,0][hop],top=group[0].priority||1;
      for(let i=0;i<group.length;i++){
        const n=group[i],category=topic(n),known=topics.findIndex(([name])=>name===category);
        const angle=known>=0?known*Math.PI*2/topics.length+(hash(n.id)%1000/1000-.5)*.65:i*golden+(hash(n.id)%1000)/10000;
        const vertical=flat?0:known>=0?.55*Math.sin(known*golden)+(hash(n.id+'z')%1000/1000-.5)*.25:.65*Math.sin(angle*.7+.4),ring=Math.sqrt(1-vertical*vertical);
        const radius=base+range*(1-n.priority/top)+Math.sqrt(i)*[0,14,18,20,22][hop];
        out.push({...n,category,x:Math.cos(angle)*ring*radius,y:Math.sin(angle)*ring*radius,z:vertical*radius});
      }
    }return out;
  }
  function neighbourhood(ordered){return ordered.filter(n=>n.hops===0||n.hops===1).slice(0,9);}
  function project(n,camera,width,height){
    const cy=Math.cos(camera.yaw),sy=Math.sin(camera.yaw),cp=Math.cos(camera.pitch),sp=Math.sin(camera.pitch);
    const x=n.x*cy+n.z*sy,z=-n.x*sy+n.z*cy,y=n.y*cp-z*sp,depth=n.y*sp+z*cp;
    const perspective=clamp(camera.eye/(camera.eye+depth),.6,1.5),s=camera.scale*perspective;
    return {...n,sx:width/2+camera.panX+x*s,sy:height/2+camera.panY+y*s,depth};
  }
  function company(data,rows){
    const root=data.entity_key||'company-root',nodes=new Map([[root,{id:root,name:data.name,symbol:data.symbol,kind:'issuer'}]]);
    const edges=rows.map(row=>{
      const id=row.target_id||'reference:'+row.index;
      if(!nodes.has(id))nodes.set(id,{id,name:row.name,symbol:row.symbol,kind:'company',index:row.index,description:row.business?.detail||row.detail||''});
      let a=root,b=id;
      if(['supplier','parent','owner'].includes(row.kind))[a,b]=[b,a];
      return {id:'relation:'+row.index,source:a,target:b,kind:row.kind,index:row.index,citation:row.source,
        analytical:row.kind==='competitor'&&(row.detail||'').includes('공시 사업 범위를 대조한 비교 대상')};
    });
    const accepted=s=>{
      if(window.MilkywayCompanyResearchView)return window.MilkywayCompanyResearchView.accepted(s);
      try{const u=new URL(s?.url);return s?.level!=='encyclopedia'&&u.protocol==='https:'&&!u.username&&!u.password&&(!u.port||u.port==='443')&&!/(^|\.)(wikipedia|wikidata|wikimedia)\.org$/i.test(u.hostname.replace(/\.$/,''));}catch{return false;}
    };
    for(const field of ['products','segments','drivers','facts'])for(const [i,record]of (data[field]||[]).entries()){
      if(!accepted(record.source))continue;const id=root+':'+field+':'+i;
      const n={id,name:record.title,kind:field==='drivers'?'factor':field==='segments'?'segment':'product',description:record.detail||'',original:record.original||'',sources:[record.source],record};nodes.set(id,n);
      edges.push({id:'element:'+id,source:root,target:id,kind:field==='drivers'?'exposure':'business_scope',citation:record.source,analytical:field==='drivers',element:n});
    }
    const latest=new Map();for(const r of data.revenue_mix||[]){if(accepted(r.source))latest.set(r.group,[r.end,latest.get(r.group)||''].sort().at(-1));}
    for(const [i,record]of (data.revenue_mix||[]).entries()){
      if(!accepted(record.source))continue;const id=root+':revenue:'+i,m=measure(record),n={id,name:record.label,kind:'revenue',description:measureText(m),measure:m,latest:record.end===latest.get(record.group),sources:[record.source],record};nodes.set(id,n);
      edges.push({id:'element:'+id,source:root,target:id,kind:'revenue',citation:record.source,measure:m,latest:record.end===latest.get(record.group),element:n});
    }
    return {nodes:[...nodes.values()],edges,focus_id:root,rows,root_name:data.name,root_symbol:data.symbol,revenue_groups:[...latest.keys()]};
  }
  window.MilkywayConstellationMath=Object.freeze({clamp,hash,measure,measureText,revenueGroups,topic,weight,rank,layout,neighbourhood,project,company});
})();
