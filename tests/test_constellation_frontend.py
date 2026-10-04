"""Actual geometry and event-driven canvas lifecycle, without browser libraries."""
from pathlib import Path
import shutil
import subprocess
import unittest


@unittest.skipUnless(shutil.which('node'), 'Node required for browser modules')
class ConstellationFrontendTests(unittest.TestCase):
    def node(self, script):
        result = subprocess.run([shutil.which('node'), '-e', script,
            str(Path(__file__).resolve().parents[1]/'cloud_app/static')],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_full_graph_ranking_and_dense_nonoverlap_in_three_dimensions_and_projection(self):
        self.node(r"""
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const window={};vm.runInNewContext(fs.readFileSync(process.argv[1]+'/constellation-math.js','utf8'),{window});
const G=window.MilkywayConstellationMath,ns=['a','b','c','d'].map(id=>({id,name:id}));
const es=[{source:'a',target:'b',kind:'customer'},{source:'a',target:'c',kind:'classification',analytical:true},{source:'b',target:'d',kind:'partner'}];
let xyz=G.layout(ns,es,'a'),byId=new Map(xyz.map(n=>[n.id,n]));
assert.equal(byId.get('a').x,0);assert(Math.hypot(byId.get('b').x,byId.get('b').y,byId.get('b').z)<Math.hypot(byId.get('c').x,byId.get('c').y,byId.get('c').z));
assert.equal(G.rank(ns,es,'a')[1].id,'b');assert.equal(G.rank(ns,[...es,...es], 'a')[1].priority,G.rank(ns,es,'a')[1].priority);
xyz=G.layout(ns,es,'b');assert.equal(xyz[0].id,'b');assert.equal(xyz[0].z,0);
function noOverlap(points,space){
 const bins=new Map(),cell=space==='world'?24:8;
 for(const p of points){const x=space==='world'?p.x:p.sx,y=space==='world'?p.y:p.sy,z=space==='world'?p.z:0,r=space==='world'?12:p.radius;
 const reach=space==='world'?1:Math.ceil((r+18)/cell);
 for(let a=-reach;a<=reach;a++)for(let b=-reach;b<=reach;b++)for(let c=space==='world'?-1:0;c<=(space==='world'?1:0);c++)for(const q of bins.get([Math.floor(x/cell)+a,Math.floor(y/cell)+b,Math.floor(z/cell)+c].join(','))||[]){assert(Math.hypot(x-q.x,y-q.y,z-q.z)>=r+q.r-1e-6);}
 const k=[Math.floor(x/cell),Math.floor(y/cell),Math.floor(z/cell)].join(',');if(!bins.has(k))bins.set(k,[]);bins.get(k).push({x,y,z,r});
 }
}
for(const flat of [false,true]){
 const n=3200,nodes=Array.from({length:n},(_,i)=>({id:String(i),name:String(i)})),edges=nodes.slice(1).map(p=>({source:'0',target:p.id,kind:'customer'}));
 const world=G.layout(nodes,edges,'0',flat);noOverlap(world,'world');assert(flat?world.every(n=>n.z===0):world.some(n=>n.z!==0));
 const max=Math.max(...world.map(n=>Math.hypot(n.x,n.y,n.z)));
 for(const [w,h] of [[800,560],[340,480]]){const radius=Math.max(.8,Math.sqrt(w*h/n)*.12),camera={yaw:flat?0:.7,pitch:flat?0:.3,eye:max*6,scale:Math.min(w,h)*.39/max,panX:0,panY:0};
 const screen=G.separate(world.map(p=>({...G.project(p,camera,w,h),radius:p.id==='0'?18:radius})),w,h);assert.equal(screen.length,n);noOverlap(screen,'screen');assert(screen.every(p=>p.sx>=p.radius&&p.sx<=w-p.radius&&p.sy>=p.radius&&p.sy<=h-p.radius));}
}
const rows=Array.from({length:25},(_,i)=>({target_id:'c'+i,name:'N'+i,index:i,kind:'supplier'}));assert.equal(G.company({name:'Root'},rows).nodes.length,26);
""")

    def test_scene_idle_visibility_search_recenter_keyboard_and_teardown(self):
        self.node(r"""
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const els=new Map(),listeners={},raf=new Map();let serial=0,clock=0,intersection,selected;
const paint=new Proxy({measureText:t=>({width:t.length*6}),createRadialGradient:()=>({addColorStop(){}})},{get:(t,k)=>t[k]||(()=>{})});
function el(key){if(!els.has(key))els.set(key,{value:key==='dimension'?'3d':'key',dataset:{},hidden:false,children:[],textContent:'',getContext:()=>paint,getBoundingClientRect:()=>({width:800,height:560,left:0,top:0}),setPointerCapture(){},setAttribute(k,v){this[k]=v;},replaceChildren(...v){this.children=v;},addEventListener(k,f){this[k]=f;},querySelector(){return this.children[0];}});return els.get(key);}
const target={querySelector:k=>el(k.slice(8)),classList:{toggle:()=>true},innerHTML:''};
const document={hidden:false,createElement:()=>el('new'+serial++),addEventListener:(k,f)=>listeners[k]=f};
const window={devicePixelRatio:1,matchMedia:()=>({matches:false,addEventListener(){}})};
const context=vm.createContext({window,document,performance:{now:()=>clock},requestAnimationFrame:f=>{const id=++serial;raf.set(id,f);return id;},cancelAnimationFrame:id=>raf.delete(id),ResizeObserver:class{observe(){}},IntersectionObserver:class{constructor(f){intersection=f;}observe(){}},URL,Map,Set,Math,Number,Intl,JSON});
for(const file of ['constellation-math.js','constellation.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+file,'utf8'),context);
const scene=window.MilkywayConstellation.create(target,{select:n=>selected=n});
el('dimension').change();assert.equal(raf.size,0);
const graph={focus_id:'root',nodes:[{id:'root',name:'Root',kind:'sector'},{id:'x',name:'<img unsafe>',symbol:'XOM',kind:'issuer'},{id:'y',name:'Other',kind:'factor'}],edges:[{id:'edge',source:'root',target:'x',kind:'customer'}]};
function flush(){clock+=1000;const jobs=[...raf.values()];raf.clear();for(const f of jobs)f(clock);}
scene.set(graph);flush();assert.equal(el('canvas').dataset.nodeCount,'3');assert.equal(raf.size,0);assert.equal(selected.id,'root');
el('search').value='xom';el('search').input();assert.equal(el('matches').children[0].textContent,'<img unsafe> · 조사 기업');el('matches').children[0].click();flush();assert.equal(el('canvas').dataset.focusId,'x');assert.equal(raf.size,0);
scene.set(graph);flush();assert.equal(el('canvas').dataset.focusId,'x');
el('motion').click();flush();assert.equal(raf.size,1);intersection([{isIntersecting:false}]);assert.equal(raf.size,0);intersection([{isIntersecting:true}]);flush();assert.equal(raf.size,1);
document.hidden=true;listeners.visibilitychange();assert.equal(raf.size,0);document.hidden=false;listeners.visibilitychange();flush();assert.equal(raf.size,1);
el('motion').click();flush();assert.equal(raf.size,0);
el('canvas').keydown({key:'Escape',preventDefault(){}});flush();assert.equal(selected.id,'root');
scene.clear();assert.equal(raf.size,0);scene.set(graph);flush();assert.equal(el('canvas').dataset.nodeCount,'3');
""")

    def test_sector_sources_paging_exact_edge_and_stale_owner_response(self):
        self.node(r"""
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const els=new Map();function el(id){if(!els.has(id))els.set(id,{innerHTML:'',textContent:'',hidden:false,before(){},addEventListener(k,f){this[k]=f;}});return els.get(id);}
let handlers,sceneHooks,sets=0,calls=0,finish,delayed=false,state={workspace:'detail',me:{id:'owner'}};
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const source={label:'<img source>',url:'https://www.sec.gov/test',as_of:'2026-10-04'};
const root={id:'energy',kind:'sector',name:'<script>root',description:'<img detail>',sources:[source,{...source,url:'javascript:bad'}]};
const graph={focus_id:'energy',scope:'Scope',method:'Method',nodes:[root,...Array.from({length:12},(_,i)=>({id:'n'+i,kind:'company',name:'Company '+i}))],edges:Array.from({length:12},(_,i)=>({id:'e'+i,source:'energy',target:'n'+i,kind:'customer',detail:'<img claim '+i+'>',citation:source}))};
const scene={set:g=>{sets++;sceneHooks.select(g.nodes[0]);},clear(){},focus:id=>sceneHooks.select(graph.nodes.find(n=>n.id===id))};
const window={MilkywayResearchView:{escape},MilkywayConstellation:{create:(target,h)=>{sceneHooks=h;return scene;}}};
const document={getElementById:el,createElement:()=>({set id(v){els.set(v,this);},addEventListener:(k,f)=>handlers=f})};
const ctx=vm.createContext({window,document,URL,Map,Set,Number});
for(const file of ['list-paging.js','energy-constellation.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+file,'utf8'),ctx);
const view=window.MilkywayEnergyConstellation;
view.initialize({getState:()=>state,api:async()=>{calls++;return delayed?await new Promise(r=>finish=r):graph;}});
function click(attribute,value){handlers({target:{closest:s=>s==='['+attribute+']'?{dataset:{[attribute.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]:value}}:null}});}
(async()=>{view.render(true);await new Promise(setImmediate);assert.equal(calls,1);let html=el('energyCosmosFocus').innerHTML;
assert(html.includes('&lt;script&gt;'));assert(!html.includes('<script>'));assert(!html.includes('javascript:'));assert(html.includes('data-cosmos-neighbours-page'));
assert(!html.includes('Company 8'));click('data-cosmos-neighbours-page','2');assert(el('energyCosmosFocus').innerHTML.includes('Company 8'));
sceneHooks.edge(graph.edges[8]);assert(el('energyCosmosFocus').innerHTML.includes('&lt;img claim 8&gt;'));assert(!el('energyCosmosFocus').innerHTML.includes('claim 0'));
view.render(false);view.render(true);assert.equal(calls,1);
delayed=true;el('energyCosmosRefresh').click();view.render(false);state.me={id:'different'};const before=sets;finish(graph);await new Promise(setImmediate);assert.equal(sets,before);
})().catch(e=>{console.error(e);process.exitCode=1;});
""")
