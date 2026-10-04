/* Real xyz geometry. Distances are exploration priorities, not financial impact estimates. */
(() => {
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const golden=Math.PI*(3-Math.sqrt(5));
  const vacancyCache=new Map();
  const hash=s=>{let h=2166136261;for(const c of String(s)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;};
  function weight(edge){
    const base={customer:3.5,supplier:3.5,subsidiary:3,parent:3,holding:2.8,owner:2.8,partner:3,competitor:2,transaction:1.7,business_scope:2.2,classification:.55,industry_process:.8,exposure:1.5}[edge.kind]||1;
    return base*(edge.analytical?.65:1)*(edge.citation?.level==='provider'?.85:1);
  }
  function rank(nodes,edges,focus){
    const adj=new Map(nodes.map(n=>[n.id,new Map()]));
    for(const edge of edges){
      if(edge.source===edge.target||!adj.has(edge.source)||!adj.has(edge.target))continue;
      for(const[a,b]of[[edge.source,edge.target],[edge.target,edge.source]])adj.get(a).set(b,Math.max(weight(edge),adj.get(a).get(b)||0));
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
  function layout(nodes,edges,focus,flat=false){
    const ordered=rank(nodes,edges,focus),groups=new Map(),bins=new Map(),out=[];
    for(const n of ordered){if(!groups.has(n.hops))groups.set(n.hops,[]);groups.get(n.hops).push(n);}
    const outer=Math.max(900,Math.sqrt(nodes.length)*32);
    function blocked(p){
      const cell=24,x=Math.floor(p.x/cell),y=Math.floor(p.y/cell),z=Math.floor(p.z/cell);
      for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(let dz=-1;dz<=1;dz++){
        for(const q of bins.get(`${x+dx},${y+dy},${z+dz}`)||[])if(Math.hypot(p.x-q.x,p.y-q.y,p.z-q.z)<24)return true;
      }return false;
    }
    for(const[hop,group]of groups){
      if(hop===0){out.push({...group[0],x:0,y:0,z:0});continue;}
      const base=outer*[0,.23,.44,.64,.8][hop],range=outer*[0,.14,.15,.14,.2][hop],top=group[0].priority||1;
      for(let i=0;i<group.length;i++){
        const n=group[i],angle=i*golden+(hash(n.id)%1000)/10000;
        const vertical=flat?0:.8*(1-2*(i+.5)/group.length),ring=Math.sqrt(1-vertical*vertical);
        let radius=base+range*(n.priority?1-n.priority/top:i/Math.max(1,group.length-1));
        let p;
        do{p={...n,x:Math.cos(angle)*ring*radius,y:Math.sin(angle)*ring*radius,z:vertical*radius};radius+=25;}while(blocked(p));
        out.push(p);const key=[p.x,p.y,p.z].map(v=>Math.floor(v/24)).join(',');if(!bins.has(key))bins.set(key,[]);bins.get(key).push(p);
      }
    }return out;
  }
  function project(n,camera,width,height){
    const cy=Math.cos(camera.yaw),sy=Math.sin(camera.yaw),cp=Math.cos(camera.pitch),sp=Math.sin(camera.pitch);
    const x=n.x*cy+n.z*sy,z=-n.x*sy+n.z*cy,y=n.y*cp-z*sp,depth=n.y*sp+z*cp;
    const perspective=clamp(camera.eye/(camera.eye+depth),.6,1.5),s=camera.scale*perspective;
    return {...n,sx:width/2+camera.panX+x*s,sy:height/2+camera.panY+y*s,depth};
  }
  function separate(points,width,height,attempt=0){
    const out=[],bins=new Map(),large=[],cell=8;
    const small=Math.max(1,...points.filter(p=>p.radius<=5).map(p=>p.radius));
    const step=Math.max(2,Math.min(...points.filter(p=>p.radius<=5).map(p=>p.radius),small)*2+1.6);
    const cols=Math.max(1,Math.floor((width-8)/step)),rows=Math.max(1,Math.floor((height-8)/step));
    // Vacancies expand around the focused planet instead of accumulating in
    // rows at the viewport edge. A small deterministic jitter avoids a grid.
    const cacheKey=cols+':'+rows;
    if(!vacancyCache.has(cacheKey)){
      if(vacancyCache.size>=4)vacancyCache.delete(vacancyCache.keys().next().value);
      vacancyCache.set(cacheKey,Array.from({length:cols*rows},(_,i)=>({a:i%cols,b:Math.floor(i/cols)}))
        .sort((a,b)=>((a.a-cols/2)**2+(a.b-rows/2)**2)-((b.a-cols/2)**2+(b.b-rows/2)**2)));
    }
    const slots=vacancyCache.get(cacheKey);
    let cursor=0;
    const key=(x,y)=>x+y*100000;
    function blocked(x,y,r){
      for(const q of large)if(Math.hypot(x-q.sx,y-q.sy)<r+q.radius+1.5)return true;
      const a=Math.floor(x/cell),b=Math.floor(y/cell),reach=Math.ceil((r+small+1.5)/cell);
      for(let dx=-reach;dx<=reach;dx++)for(let dy=-reach;dy<=reach;dy++)for(const q of bins.get(key(a+dx,b+dy))||[]){
        if((x-q.sx)**2+(y-q.sy)**2<(r+q.radius+1.5)**2)return true;
      }return false;
    }
    const candidate=(a,b,r)=>{const jitter=(Math.imul(a+17,73856093)^Math.imul(b+31,19349663))>>>0,x=4+(a+.5+(jitter%100/100-.5)*.25)*step,y=4+(b+.5+((jitter>>>8)%100/100-.5)*.25)*step;
      return a>=0&&a<cols&&b>=0&&b<rows&&x>=r+3&&x<=width-r-3&&y>=r+3&&y<=height-r-3&&!blocked(x,y,r)?[x,y]:null;};
    for(const p of points){
      let x=p.sx,y=p.sy;
      if(blocked(x,y,p.radius)){
        let slot=null;const a=Math.round((x-4)/step-.5),b=Math.round((y-4)/step-.5);
        for(let ring=0;ring<3&&!slot;ring++)for(let dx=-ring;dx<=ring&&!slot;dx++)for(const dy of ring===0?[0]:[-ring,ring]){slot=candidate(a+dx,b+dy,p.radius);if(slot)break;}
        for(let ring=1;ring<3&&!slot;ring++)for(let dy=-ring+1;dy<ring&&!slot;dy++)for(const dx of [-ring,ring]){slot=candidate(a+dx,b+dy,p.radius);if(slot)break;}
        while(!slot&&cursor<slots.length){const s=slots[cursor++];slot=candidate(s.a,s.b,p.radius);}
        if(!slot){
          if(attempt>=10)throw new Error('Relation viewport is too small');
          return separate(points.map(n=>({...n,radius:n.radius>5?n.radius:n.radius*.8})),width,height,attempt+1);
        }
        [x,y]=slot;
      }
      const mark={...p,sx:x,sy:y};out.push(mark);
      if(p.radius>5)large.push(mark);else{const k=key(Math.floor(x/cell),Math.floor(y/cell));if(!bins.has(k))bins.set(k,[]);bins.get(k).push(mark);}
    }return out;
  }
  function company(data,rows){
    const root=data.entity_key||'company-root',nodes=new Map([[root,{id:root,name:data.name,symbol:data.symbol,kind:'issuer'}]]);
    const edges=rows.map(row=>{
      const id=row.target_id||'reference:'+row.index;
      if(!nodes.has(id))nodes.set(id,{id,name:row.name,symbol:row.symbol,kind:'company',index:row.index});
      let a=root,b=id;
      if(['supplier','parent','owner'].includes(row.kind))[a,b]=[b,a];
      return {id:'relation:'+row.index,source:a,target:b,kind:row.kind,index:row.index,citation:row.source,
        analytical:row.kind==='competitor'&&(row.detail||'').includes('공시 사업 범위를 대조한 비교 대상')};
    });
    return {nodes:[...nodes.values()],edges,focus_id:root,rows,root_name:data.name,root_symbol:data.symbol};
  }
  window.MilkywayConstellationMath=Object.freeze({clamp,hash,weight,rank,layout,project,separate,company});
})();
