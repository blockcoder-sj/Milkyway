/* Real xyz geometry. Distances are exploration priorities, not financial impact estimates. */
(() => {
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const golden=Math.PI*(3-Math.sqrt(5));
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
    const ordered=rank(nodes,edges,focus),groups=new Map(),out=[];
    for(const n of ordered){if(!groups.has(n.hops))groups.set(n.hops,[]);groups.get(n.hops).push(n);}
    // The selected neighbourhood does not expand when unrelated nodes are added.
    // Overlap is allowed; projection must never move planets into vacant slots.
    for(const[hop,group]of groups){
      if(hop===0){out.push({...group[0],x:0,y:0,z:0});continue;}
      const base=[0,65,210,410,700][hop],range=[0,60,70,120,0][hop],top=group[0].priority||1;
      for(let i=0;i<group.length;i++){
        const n=group[i],angle=i*golden+(hash(n.id)%1000)/10000;
        const vertical=flat?0:.65*Math.sin(angle*.7+.4),ring=Math.sqrt(1-vertical*vertical);
        const radius=base+range*(1-n.priority/top)+Math.sqrt(i)*[0,14,18,20,22][hop];
        out.push({...n,x:Math.cos(angle)*ring*radius,y:Math.sin(angle)*ring*radius,z:vertical*radius});
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
      if(!nodes.has(id))nodes.set(id,{id,name:row.name,symbol:row.symbol,kind:'company',index:row.index});
      let a=root,b=id;
      if(['supplier','parent','owner'].includes(row.kind))[a,b]=[b,a];
      return {id:'relation:'+row.index,source:a,target:b,kind:row.kind,index:row.index,citation:row.source,
        analytical:row.kind==='competitor'&&(row.detail||'').includes('공시 사업 범위를 대조한 비교 대상')};
    });
    return {nodes:[...nodes.values()],edges,focus_id:root,rows,root_name:data.name,root_symbol:data.symbol};
  }
  window.MilkywayConstellationMath=Object.freeze({clamp,hash,weight,rank,layout,neighbourhood,project,company});
})();
