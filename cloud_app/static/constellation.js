/* Event-driven local Canvas scene with true xyz rotation, no external libraries. */
(() => {
  const G=window.MilkywayConstellationMath;
  const palette={sector:'#c5a3ff',issuer:'#bfa5ff',company:'#76c5df',group:'#e3b475',product:'#7bd2ae',factor:'#ed9ea7',segment:'#7bd2ae',revenue:'#f0ce82'};
  const labels={sector:'섹터',issuer:'조사 기업',company:'연결 기업',group:'업종',product:'사업 요소',factor:'사업·외부 요인',segment:'사업 부문',revenue:'매출 구성'};
  function create(target,hooks={}){
    const probe=document.createElement('canvas');
    if(!probe.getContext){return Object.freeze({set(value){target.innerHTML=value.rows?window.MilkywayCompanyRelations.draw(value.root_name,value.root_symbol,value.rows):'관계도를 지원하는 브라우저에서 확인하세요.';},clear(){target.innerHTML='';},highlight(){},focus(){}});}
    target.innerHTML='<div class="cosmos"><div class="cosmos-toolbar"><label>이름·종목 검색<input class="cosmos-search" type="search" placeholder="기업·제품·외부 요인" autocomplete="off"></label><div class="cosmos-matches"></div><label>공간<select class="cosmos-dimension"><option value="3d">3D 우주 지도</option><option value="2d">2D 펼치기</option></select></label><label>이름표<select class="cosmos-labels"><option value="key">주요 이름</option><option value="more">더 많이</option><option value="off">숨기기</option></select></label><label>비중 기준<select class="cosmos-basis"><option value="relations">사업 연결</option></select></label><button type="button" class="ghost compact cosmos-fit">전체 지도</button><button type="button" class="ghost compact cosmos-near">선택 주변</button><button type="button" class="ghost compact cosmos-in" aria-label="관계도 확대">＋</button><button type="button" class="ghost compact cosmos-out" aria-label="관계도 축소">−</button><button type="button" class="ghost compact cosmos-motion" aria-pressed="false">천천히 회전</button><button type="button" class="ghost compact cosmos-expand">크게 보기</button></div><div class="cosmos-viewport"><canvas class="cosmos-canvas" tabindex="0" role="img" aria-label="3차원 관계도. 방향키로 회전, Shift와 방향키로 대상 선택, Enter로 중심 이동, 더하기·빼기로 확대합니다."></canvas><div class="cosmos-legend"></div><button type="button" class="ghost compact cosmos-return" hidden>전체 지도로 돌아가기</button><p class="cosmos-hint">천체 클릭: 주요 연결 확대·근거 확인 · 전체 지도: 모든 요소 · 드래그: 회전 · Shift+드래그: 이동 · 휠/두 손가락: 확대</p><div class="cosmos-tooltip" hidden></div></div><p class="cosmos-status" role="status"></p></div>';
    const $=name=>target.querySelector('.cosmos-'+name),canvas=$('canvas'),ctx=canvas.getContext('2d');
    if(!ctx){target.textContent='이 브라우저에서 관계도 화면을 만들지 못했습니다. 아래 관계 목록에서 확인하세요.';return Object.freeze({set(){},clear(){},highlight(){},focus(){}});}
    const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
    const camera={yaw:0,pitch:0,zoom:1,panX:0,panY:0,eye:5000,scale:.2};
    let model=null,nodes=[],screen=[],focus=null,hover=null,frame=0,active=false,visible=true,auto=false,last=0,transition=null;
    let width=1,height=1,pointer=null,pinched=false,pinch=0,signature='',keyboard=0,selectedEdge=null;
    let lastFocus=null,view='all',nearby=new Set(),extent=160,fullExtent=160;
    const touches=new Map(),stars=Array.from({length:110},(_,i)=>({x:G.hash('sx'+i)%10000/10000,y:G.hash('sy'+i)%10000/10000,r:i%9===0?1:.55}));
    let evidenceSerial=0;
    if(hooks.evidenceSearch){
      const button=document.createElement('button');button.type='button';button.className='ghost compact';button.textContent='자료 근거 검색';
      $('search').parentElement.after(button);
      button.addEventListener('click',async()=>{
        const q=$('search').value.trim(),token=++evidenceSerial,owner=model;
        if(!q||!model)return;button.disabled=true;button.textContent='자료 근거 검색 중…';
        try{const result=await hooks.evidenceSearch(q);if(token!==evidenceSerial||!active||model!==owner||$('search').value.trim()!==q)return;
          $('matches').replaceChildren(...result.rows.map(hit=>{const item=document.createElement('button');item.type='button';item.className='ghost compact';item.textContent=hit.title+' · 근거 발췌: '+hit.excerpt;
            item.addEventListener('click',()=>{pick(hit.node_id);const edge=model.edges.find(e=>e.id===hit.edge_id);if(edge){selectedEdge=edge.id;hooks.edge?.(edge);}request();});return item;}));
          if(!result.rows.length){const empty=document.createElement('span');empty.textContent='이 키워드와 일치하는 자료 근거가 없습니다.';$('matches').replaceChildren(empty);}
        }catch(error){if(token===evidenceSerial&&active&&model===owner&&$('search').value.trim()===q){const message=document.createElement('span');message.textContent=error.message;$('matches').replaceChildren(message);}}
        finally{if(token===evidenceSerial){button.disabled=false;button.textContent='자료 근거 검색';}}
      });
    }
    function cancel(){if(frame)cancelAnimationFrame(frame);frame=0;last=0;}
    function request(){if(!frame&&active&&visible&&!document.hidden)frame=requestAnimationFrame(draw);}
    function fit(reset=false){
      if(reset){view='all';extent=fullExtent;camera.zoom=1;camera.panX=camera.panY=0;camera.yaw=camera.pitch=0;}
      camera.eye=fullExtent*6;
      camera.scale=Math.min(width,height)*.36/extent*camera.zoom;request();
    }
    function resize(){const r=canvas.getBoundingClientRect();if(r.width<1||r.height<1)return;
      width=r.width;height=r.height;const dpr=Math.min(1.5,window.devicePixelRatio||1);
      canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);fit();}
    function rebuild(id,animate=true,overview=false){
      if(!model)return;
      const next=G.layout(model.nodes,model.edges,id,$('dimension').value==='2d',$('basis').value);
      const before=new Map(nodes.map(n=>[n.id,n]));focus=id;hover=null;keyboard=0;selectedEdge=null;
      nodes=next;transition=animate&&before.size&&!reduced.matches?{start:performance.now(),from:before,to:next}:null;
      const neighbours=G.neighbourhood(next);nearby=new Set(neighbours.map(n=>n.id));
      fullExtent=Math.max(160,...next.map(n=>Math.hypot(n.x,n.y,n.z)));
      view=overview?'all':'focus';extent=overview?fullExtent:Math.max(100,...neighbours.map(n=>Math.hypot(n.x,n.y,n.z)))*1.15;
      canvas.setAttribute('aria-label',(model.nodes.find(n=>n.id===id)?.name||'관계도')+' 중심 · 방향키로 회전, Shift+방향키 대상 선택, Enter 중심 이동');
      camera.panX=camera.panY=0;camera.zoom=1;fit();hooks.select?.(model.nodes.find(n=>n.id===id),next);request();
    }
    function pick(id){if(model?.nodes.some(n=>n.id===id)){lastFocus=id;rebuild(id);$('search').value=model.nodes.find(n=>n.id===id).name;$('matches').replaceChildren();}}
    function color(node){return palette[node.kind]||palette.company;}
    function glow(p){const g=ctx.createRadialGradient(p.sx,p.sy,0,p.sx,p.sy,p.radius*4);g.addColorStop(0,color(p)+'50');g.addColorStop(1,color(p)+'00');ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.sx,p.sy,p.radius*4,0,Math.PI*2);ctx.fill();}
    function draw(now){
      frame=0;if(!active||!visible||document.hidden||!model||width<80||height<80)return;
      if((auto||transition)&&last&&now-last<80){request();return;}
      const started=performance.now(),delta=Math.min(40,last?now-last:16);last=now;
      if(auto&&!reduced.matches&&!pointer&&!transition)camera.yaw+=delta*.00003;
      let current=nodes;
      if(transition){const t=Math.min(1,(now-transition.start)/750),ease=1-(1-t)**3;
        current=transition.to.map(n=>{const a=transition.from.get(n.id)||n;return {...n,x:a.x+(n.x-a.x)*ease,y:a.y+(n.y-a.y)*ease,z:a.z+(n.z-a.z)*ease};});if(t===1)transition=null;
      }
      ctx.clearRect(0,0,width,height);
      for(const s of stars){ctx.fillStyle='#a591c555';ctx.beginPath();ctx.arc(s.x*width,s.y*height,s.r,0,Math.PI*2);ctx.fill();}
      $('return').hidden=view!=='focus';
      const focused=view==='focus',shown=focused?current.filter(n=>nearby.has(n.id)):current;
      const density=G.clamp(Math.sqrt(width*height/Math.max(1,nodes.length))*.12,.8,7);
      const magnify=focused?G.clamp(Math.sqrt(camera.zoom),.7,2):1;
      screen=shown.map(n=>({...G.project(n,$('dimension').value==='2d'?{...camera,yaw:0,pitch:0}:camera,width,height),radius:n.id===focus?(focused?28*magnify:18):focused?8*magnify:n.id===hover?7:n.hops===1&&nodes.length<500?Math.max(3.5,density):density}));
      const map=new Map(screen.map(n=>[n.id,n]));
      const center=map.get(focus);if(center){glow(center);ctx.strokeStyle='#b898e51d';ctx.setLineDash([2,9]);for(const r of [55,110,170]){ctx.beginPath();ctx.ellipse(center.sx,center.sy,r,r*.72,0,0,Math.PI*2);ctx.stroke();}ctx.setLineDash([]);}
      // Batch far lines to keep the full sector scene affordable while retaining
      // every edge. Direct connections stay readable when a planet is focused.
      const batches=new Map();
      for(const edge of model.edges){const a=map.get(edge.source),b=map.get(edge.target);if(!a||!b)continue;
        const hot=edge.source===focus||edge.target===focus||edge.source===hover||edge.target===hover;
        const key=(hot?'h':'b')+(edge.analytical?'a':'f');if(!batches.has(key))batches.set(key,[]);batches.get(key).push([edge,a,b]);}
      for(const[key,rows]of batches){ctx.strokeStyle=key.endsWith('a')?'#e7b377':'#ad94d8';ctx.globalAlpha=key[0]==='h'?.58:.075;ctx.lineWidth=key[0]==='h'?1.1:.5;ctx.setLineDash(key.endsWith('a')?[3,5]:[]);ctx.beginPath();
        for(const[,a,b]of rows){ctx.moveTo(a.sx,a.sy);ctx.lineTo(b.sx,b.sy);}ctx.stroke();}
      ctx.setLineDash([]);ctx.globalAlpha=1;
      ctx.strokeStyle='#e9dcff';ctx.lineWidth=1;ctx.beginPath();
      for(const edge of model.edges){if(edge.source!==focus&&edge.target!==focus)continue;
        if(!['customer','supplier','subsidiary','parent','holding','owner'].includes(edge.kind))continue;
        const a=map.get(edge.source),b=map.get(edge.target);if(!a||!b)continue;
        const d=Math.hypot(b.sx-a.sx,b.sy-a.sy);if(d<a.radius+b.radius+14)continue;
        const ux=(b.sx-a.sx)/d,uy=(b.sy-a.sy)/d,x=b.sx-ux*(b.radius+3),y=b.sy-uy*(b.radius+3);
        ctx.moveTo(x-ux*5-uy*3,y-uy*5+ux*3);ctx.lineTo(x,y);ctx.lineTo(x-ux*5+uy*3,y-uy*5-ux*3);
      }ctx.stroke();
      if(selectedEdge){const edge=model.edges.find(e=>e.id===selectedEdge),a=edge&&map.get(edge.source),b=edge&&map.get(edge.target);if(a&&b){ctx.strokeStyle='#fff1cf';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(a.sx,a.sy);ctx.lineTo(b.sx,b.sy);ctx.stroke();}}
      for(const p of [...screen].sort((a,b)=>b.depth-a.depth)){
        if(p.id===hover||p.id===focus||p.hops===1&&screen.length<100)glow(p);
        ctx.globalAlpha=p.hops<=1||p.id===hover?1:.75;ctx.fillStyle=color(p);
        if(p.kind==='revenue'&&p.latest&&p.measure?.group===$('basis').value&&p.measure.share_pct!==null){p.radius=Math.max(p.radius,3+Math.sqrt(p.measure.share_pct)*.8);}
        if(p.radius>=5){const planet=ctx.createRadialGradient(p.sx-p.radius*.35,p.sy-p.radius*.4,0,p.sx,p.sy,p.radius);planet.addColorStop(0,'#fff6ec');planet.addColorStop(.35,color(p));planet.addColorStop(1,'#302039');ctx.fillStyle=planet;}
        ctx.beginPath();ctx.arc(p.sx,p.sy,p.radius,0,Math.PI*2);ctx.fill();
        if(p.id===focus){ctx.strokeStyle='#e8daff';ctx.lineWidth=1;ctx.beginPath();ctx.arc(p.sx,p.sy,p.radius+6,0,Math.PI*2);ctx.stroke();}
      }ctx.globalAlpha=1;
      const boxes=[];let count=0;const cap=$('labels').value==='more'?90:30;
      if($('labels').value!=='off')for(const p of [...screen].sort((a,b)=>(a.id===hover?-1:b.id===hover?1:0)||(a.id===focus?-1:b.id===focus?1:0)||a.hops-b.hops||b.priority-a.priority)){
        if(count>=cap&&p.id!==hover&&p.id!==focus)continue;
        const title=p.name+(p.kind==='revenue'&&p.measure?.share_pct!==null?' · '+p.measure.share_pct.toLocaleString('ko-KR',{maximumFractionDigits:1})+'%':'');
        const text=Array.from(title).slice(0,34).join('')+(Array.from(title).length>34?'…':'');ctx.font=p.id===focus?'600 13px sans-serif':'11px sans-serif';
        const w=ctx.measureText(text).width+14,h=21,positions=[[p.sx-w/2,p.sy+p.radius+8]];
        if(focused)for(let level=0;level<5;level++){positions.push([p.sx-w/2,p.sy-p.radius-h-8-level*24],[p.sx+p.radius+10,p.sy-h/2+level*24],[p.sx-p.radius-w-10,p.sy-h/2-level*24],[p.sx-w/2,p.sy+p.radius+8+(level+1)*24]);}
        const slot=positions.find(([x,y])=>x>=3&&x+w<=width-3&&y>=38&&y+h<=height-40&&!boxes.some(b=>x<b.x+b.w+3&&x+w+3>b.x&&y<b.y+b.h+3&&y+h+3>b.y));if(!slot)continue;
        const [x,y]=slot;if(focused&&slot!==positions[0]){ctx.strokeStyle='#c2a5e077';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(p.sx,p.sy);ctx.lineTo(x+w/2,y+h/2);ctx.stroke();}
        boxes.push({x,y,w,h});ctx.fillStyle='#0b0914e8';ctx.fillRect(x,y,w,h);ctx.fillStyle='#ece3f7';ctx.textAlign='center';ctx.fillText(text,x+w/2,y+14);count++;
      }
      $('status').textContent=`${model.nodes.find(n=>n.id===focus)?.name||''} 중심 · ${focused?(nearby.size>1?'주요 직접 연결 '+(nearby.size-1)+'개 집중 보기':'확인된 직접 연결 없음'):'전체 보기'} · 전체 ${model.nodes.length.toLocaleString('ko-KR')}개 요소 / ${model.edges.length.toLocaleString('ko-KR')}개 연결`;
      canvas.dataset.nodeCount=String(nodes.length);canvas.dataset.shownNodeCount=String(screen.length);canvas.dataset.view=view;canvas.dataset.focusId=focus;canvas.dataset.renderMs=(performance.now()-started).toFixed(2);
      if(transition||auto&&!reduced.matches)request();
    }
    const coordinates=e=>{const r=canvas.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};};
    function hit(p){let best=null,distance=Infinity;for(const n of screen){const d=Math.hypot(n.sx-p.x,n.sy-p.y);if(d<n.radius+5&&(d<distance||d===distance&&n.depth<best.depth)){best=n;distance=d;}}return best;}
    function showHover(id){hover=id;const n=model?.nodes.find(n=>n.id===id),tooltip=$('tooltip');tooltip.hidden=!n;if(n){tooltip.textContent=n.name+' · '+(labels[n.kind]||'연결 기업')+' · '+G.topic(n)+(n.measure?' · '+G.measureText(n.measure):'');canvas.setAttribute('aria-label',tooltip.textContent+' · Enter로 중심 이동, 방향키 회전, Shift+방향키 대상 선택');}else if(model){canvas.setAttribute('aria-label',(model.nodes.find(n=>n.id===focus)?.name||'관계도')+' 중심 · 방향키로 회전, Shift+방향키 대상 선택, Enter 중심 이동');}request();}
    canvas.addEventListener('pointerdown',e=>{if(e.button!==0&&e.pointerType!=='touch')return;const p=coordinates(e);touches.set(e.pointerId,p);canvas.setPointerCapture(e.pointerId);pointer={id:e.pointerId,start:p,last:p,moved:false,pan:e.shiftKey||$('dimension').value==='2d'};
      if(touches.size===1)pinched=false;
      if(touches.size===2){const[a,b]=[...touches.values()];pinch=Math.hypot(a.x-b.x,a.y-b.y);pinched=true;}});
    canvas.addEventListener('pointermove',e=>{const p=coordinates(e);if(touches.has(e.pointerId))touches.set(e.pointerId,p);
      if(touches.size>=2){const[a,b]=[...touches.values()],d=Math.hypot(a.x-b.x,a.y-b.y);if(pinch)camera.zoom=G.clamp(camera.zoom*d/pinch,.4,20);pinch=d;fit();return;}
      if(pointer?.id===e.pointerId){const dx=p.x-pointer.last.x,dy=p.y-pointer.last.y;if(Math.hypot(p.x-pointer.start.x,p.y-pointer.start.y)>4)pointer.moved=true;
        if(pointer.moved){transition=null;if(pointer.pan){camera.panX+=dx;camera.panY+=dy;}else{camera.yaw+=dx*.006;camera.pitch=G.clamp(camera.pitch+dy*.006,-1.4,1.4);}pointer.last=p;request();}return;}
      const id=hit(p)?.id||null;if(id!==hover)showHover(id);
    });
    canvas.addEventListener('pointerup',e=>{const p=coordinates(e),moved=pointer?.moved;touches.delete(e.pointerId);
      if(!moved&&!pinched&&model){const n=hit(p);if(n)pick(n.id);else{
        const positions=new Map(screen.map(n=>[n.id,n]));let best=null,bestDistance=6;
        for(const edge of model.edges){if(edge.source!==focus&&edge.target!==focus)continue;const a=positions.get(edge.source),b=positions.get(edge.target);if(!a||!b)continue;
          const dx=b.sx-a.sx,dy=b.sy-a.sy,t=G.clamp(((p.x-a.sx)*dx+(p.y-a.sy)*dy)/(dx*dx+dy*dy||1),0,1),d=Math.hypot(p.x-a.sx-t*dx,p.y-a.sy-t*dy);if(d<bestDistance){best=edge;bestDistance=d;}}
        if(best){selectedEdge=best.id;hooks.edge?.(best);}
      }}pointer=null;if(!touches.size){pinched=false;pinch=0;}else{const[id,last]=[...touches][0];pointer={id,last,start:last,moved:true,pan:false};}request();
    });
    canvas.addEventListener('pointercancel',e=>{touches.delete(e.pointerId);pointer=null;pinch=0;pinched=true;});
    canvas.addEventListener('pointerleave',()=>showHover(null));
    function zoom(multiplier){camera.zoom=G.clamp(camera.zoom*multiplier,.4,20);fit();}
    canvas.addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY>0?.9:1.1);},{passive:false});
    canvas.addEventListener('keydown',e=>{
      if(e.key.startsWith('Arrow')){e.preventDefault();if(e.shiftKey){const choices=view==='focus'?nodes.filter(n=>nearby.has(n.id)):nodes;keyboard=(keyboard+(e.key==='ArrowLeft'||e.key==='ArrowUp'?-1:1)+choices.length)%Math.max(1,choices.length);showHover(choices[keyboard]?.id);}
        else{if(e.key==='ArrowLeft')camera.yaw-=.12;if(e.key==='ArrowRight')camera.yaw+=.12;if(e.key==='ArrowUp')camera.pitch=G.clamp(camera.pitch-.12,-1.4,1.4);if(e.key==='ArrowDown')camera.pitch=G.clamp(camera.pitch+.12,-1.4,1.4);}request();}
      else if(e.key==='Enter'&&hover){e.preventDefault();pick(hover);}else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1.2);}else if(e.key==='-'){e.preventDefault();zoom(.8);}else if(e.key==='Escape'&&model){e.preventDefault();rebuild(model.focus_id);$('search').value='';}
    });
    $('search').addEventListener('input',()=>{const q=$('search').value.trim().toLocaleLowerCase(),matches=q?(model?.nodes||[]).filter(n=>((n.name||'')+' '+(n.symbol||'')+' '+(n.description||'')+' '+(n.original||'')).toLocaleLowerCase().includes(q)).sort((a,b)=>Number(b.symbol?.toLocaleLowerCase()===q&&b.kind==='issuer')-Number(a.symbol?.toLocaleLowerCase()===q&&a.kind==='issuer')).slice(0,12):[];
      $('matches').replaceChildren(...matches.map(n=>{const button=document.createElement('button');button.type='button';button.className='ghost compact';button.textContent=n.name+' · '+(labels[n.kind]||'기업');button.addEventListener('click',()=>pick(n.id));return button;}));});
    $('search').addEventListener('keydown',e=>{if(e.key==='Enter'){$('matches').querySelector('button')?.click();}if(e.key==='Escape'){$('matches').replaceChildren();}});
    function overview(){if(!model)return;rebuild(model.focus_id,false,true);fit(true);$('search').value='';}
    $('fit').addEventListener('click',overview);$('return').addEventListener('click',overview);$('near').addEventListener('click',()=>pick(lastFocus||focus));$('basis').addEventListener('change',()=>rebuild(focus,false,view==='all')); $('in').addEventListener('click',()=>zoom(1.25));$('out').addEventListener('click',()=>zoom(.8));
    $('dimension').addEventListener('change',()=>{auto=false;motion();camera.yaw=camera.pitch=0;rebuild(focus,false,view==='all');});$('labels').addEventListener('change',request);
    function motion(){$('motion').setAttribute('aria-pressed',String(auto));$('motion').textContent=auto?'회전 멈춤':'천천히 회전';$('motion').disabled=reduced.matches||$('dimension').value==='2d';}
    $('motion').addEventListener('click',()=>{auto=!auto&&!reduced.matches;motion();request();});
    $('expand').addEventListener('click',()=>{const expanded=target.classList.toggle('cosmos-expanded');$('expand').textContent=expanded?'기본 크기':'크게 보기';resize();});
    const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(canvas);
    if(typeof IntersectionObserver!=='undefined')new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;if(visible){resize();request();}else cancel();}).observe(canvas);
    document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel();else request();});
    reduced.addEventListener('change',()=>{if(reduced.matches){auto=false;transition=null;motion();cancel();request();}});
    return Object.freeze({set(value){
      const next=JSON.stringify([value.focus_id,value.nodes.map(n=>[n.id,n.name,n.kind,n.index,n.measure,n.description,n.original]),value.edges.map(e=>[e.id,e.kind,e.measure,e.latest])]);
      model=value;active=true;
      if(next!==signature){signature=next;lastFocus=value.focus_id;
        const groups=value.revenue_groups||[...new Set(value.edges.filter(e=>e.kind==='revenue').map(e=>e.measure.group))];
        $('basis').replaceChildren(...['relations',...groups].map(g=>{const o=document.createElement('option');o.value=g;o.textContent=g==='relations'?'사업 연결':G.revenueGroups[g]+' 매출 비중';return o;}));$('basis').value=groups.includes('product')?'product':groups.includes('segment')?'segment':'relations';nodes=[];auto=false;motion();$('search').value='';$('matches').replaceChildren();
        const counts=new Map();for(const n of value.nodes)counts.set(n.kind,(counts.get(n.kind)||0)+1);
        $('legend').replaceChildren(...[...counts].map(([kind,count])=>{const span=document.createElement('span');span.className='cosmos-kind cosmos-'+kind;span.textContent=(labels[kind]||kind)+' '+count;return span;}));rebuild(value.focus_id,false,true);}
      resize();request();
    },clear(){active=false;auto=false;transition=null;model=null;nodes=[];screen=[];signature='';touches.clear();pointer=null;cancel();$('matches').replaceChildren();$('tooltip').hidden=true;ctx.clearRect(0,0,width,height);},
    focus:pick,highlight(index){const n=model?.nodes.find(n=>n.index===index);if(n)pick(n.id);}});
  }
  window.MilkywayConstellation=Object.freeze({create});
})();
