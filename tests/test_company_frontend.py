"""Executable company view behavior using synthetic DOM/data, no provider calls."""
from pathlib import Path
import shutil
import subprocess
import unittest


class CompanyFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed for frontend checks")
    def test_korean_brief_revenue_originals_and_bottom_only_sources(self):
        script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ctx=vm.createContext({window:{MilkywayResearchView:{escape}},Intl,Number,String,Set,Map,URL,encodeURIComponent});
for(const name of ['format.js','market-directory.js','company-research-view.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+name,'utf8'),ctx);
const view=ctx.window.MilkywayCompanyResearchView;
const src={label:'SEC <report>',url:'https://www.sec.gov/report.htm#part1',level:'primary',as_of:'2026-02-25'};
const rejected={label:'Rejected',url:'https://en.wikipedia.org/wiki/X',level:'primary'};
const base={group:'product',member:'nvda:DataCenterMember',label:'데이터센터',value:150000000,unit:'USD',start:'2025-01-27',end:'2026-01-25',total:200000000,metric:'us-gaap:Revenues',source:src};
const data={brief:[{title:'매출 구조',detail:'기기·서비스 판매',source:src}],sources:[src,rejected],products:[
 {title:'공시 발췌',detail:'',original:'<img src=x> Untranslated source',source:{...src,url:'https://www.sec.gov/report.htm#part2'}},
 {title:'Bad',detail:'Rejected content',source:rejected}],revenue_mix:[base,{...base,member:'nvda:ComputeMember',label:'컴퓨팅',value:100000000,parent:base.member},
 {...base,member:'x:OtherMember',label:'기타',value:1,total:null},{...base,group:'geography',member:'country:US',label:'미국'}]};
const reading=view.create(data),brief=reading.essentials(),original=reading.fact(data.products[0]),revenue=reading.revenue('product'),footer=reading.footer();
assert.equal(reading.count,1);assert(brief.includes('기기·서비스 판매'));assert(!brief.includes('href="https:'));
assert(brief.includes('data-company-citation="1"'));assert(!brief.includes('target="_blank"'));
assert(original.includes('<details class="company-original">'));assert(!original.includes('<details class="company-original" open'));
assert(original.includes('&lt;img'));assert(!original.includes('<img'));assert(!original.includes('href="https:'));
assert.equal(reading.fact(data.products[1]),'');assert(!footer.includes('wikipedia'));assert(footer.includes('report.htm#part2'));
assert(footer.includes('이 자료의 근거 위치'));
assert(footer.includes('SEC &lt;report&gt;'));assert(footer.includes('https://translate.google.com/'));assert(footer.includes('선택한 공개 발췌문만'));
assert(revenue.includes('150,000,000 USD'));assert(revenue.includes('75%'));assert(revenue.includes('company-revenue-child'));
assert(revenue.includes('분모 미확인'));assert(revenue.includes('다시 합산하지 않습니다'));assert(!revenue.includes('미국'));
assert.equal(reading.groups.length,2);assert(!revenue.includes('href="https:'));
const tiny=view.create({revenue_mix:[{...base,value:5000000,total:132699000000}]}).revenue('product');
assert(tiny.includes('0.01% 미만'));assert(!tiny.includes('>0%</'));
const zero=view.create({revenue_mix:[{...base,value:0}]}).revenue('product');
assert(zero.includes('>0%</'));assert(!zero.includes('0.01% 미만'));
assert.equal(view.accepted({url:'javascript:alert(1)',level:'primary'}),false);
assert.equal(view.accepted({url:'https://user:pass@www.sec.gov/',level:'primary'}),false);
assert.equal(view.accepted({url:'https://www.sec.gov/',level:'encyclopedia'}),false);
assert.equal(view.accepted({url:'https://x.wikidata.org/wiki/X',level:'primary'}),false);
assert(view.create({}).essentials().includes('아직 검토되지 않았습니다'));
const single=view.create({brief:[{title:'매출이 생기는 구조',detail:'단일 보고 부문 · 개별 구성비 미공개 <script>',source:src}]}).revenue('product');
assert(single.includes('단일 보고 부문'));assert(single.includes('data-company-citation="1"'));
assert(single.includes('&lt;script&gt;'));assert(!single.includes('<script>'));assert(!single.includes('수치를 확인하지 못했습니다'));
assert(view.create({brief:[{title:'매출이 생기는 구조',detail:'Bad',source:rejected}]}).revenue('product').includes('확인하지 못했습니다'));
assert(view.create({...data,brief:[{title:'매출이 생기는 구조',detail:'Other note',source:src}]}).revenue('segment').includes('확인하지 못했습니다'));
const internal=view.create({revenue_mix:[{...base,group:'segment',includes_intersegment:true}]}).revenue('segment');
const adjusted=view.create({revenue_mix:[{...base,group:'segment',share_exclusion:'음수 조정 <script>excluded</script>'}]}).revenue('segment');
assert(adjusted.includes('150,000,000 USD'));assert(adjusted.includes('조정 포함 · 산출 제외'));
assert(adjusted.includes('&lt;script&gt;'));assert(!adjusted.includes('<script>'));assert(!adjusted.includes('75%'));
assert(internal.includes('내부 거래 포함'));assert(!internal.includes('75%'));assert(internal.includes('150,000,000 USD'));
const periods=view.create({revenue_mix:[base,{...base,start:'2024-01-27',end:'2025-01-25'},
 {...base,unit:'KRW'},{...base,source:{...src,url:'https://www.sec.gov/another.htm'}},
 {...base,metric:'us-gaap:SalesRevenueNet'}]}).revenue('product');
assert.equal((periods.match(/<table>/g)||[]).length,5);
const market=view.create({revenue_mix:[{...base,group:'end_market'}]});
assert.equal(market.groups[0],'end_market');assert(market.revenue('end_market').includes('고객 산업별'));
const edge={name:'공급 업체',source:src,business:{detail:'<script>장비 제조</script>',source:{...src,url:'https://issuer.example.test/products'}}};
const contextual=view.create({relations:[edge]});
assert.equal(contextual.count,2);assert(contextual.business(edge).includes('기업 사업'));
assert(contextual.business(edge).includes('&lt;script&gt;'));assert(!contextual.business(edge).includes('<script>'));
assert(contextual.business(edge).includes('data-company-citation="1"'));assert(!contextual.business(edge).includes('href="https:'));
assert.equal(contextual.business({...edge,business:{detail:'Bad',source:rejected}}),'');
const network=view.create({});network.registerNetwork({rows:[edge]});
assert.equal(network.count,2);assert(network.business(edge).includes('data-company-citation='));
const scopeData={financial_context:[{title:'연결 범위',detail:'지배기업 변경 <script>',source:src}]};
const scope=view.create(scopeData);
assert.equal(scope.count,1);assert(scope.footer().includes('연결 범위'));
assert(scope.fact(scopeData.financial_context[0]).includes('data-company-citation="1"'));
assert(scope.fact(scopeData.financial_context[0]).includes('&lt;script&gt;'));
assert(!scope.fact(scopeData.financial_context[0]).includes('<script>'));
assert.equal(view.create({financial_context:[{...scopeData.financial_context[0],source:rejected}]}).count,0);
"""
        root = Path(__file__).resolve().parents[1] / 'cloud_app/static'
        result = subprocess.run([shutil.which('node'), '-e', script, str(root)],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for frontend checks")
    def test_business_relation_priority_roles_directions_and_safe_links(self):
        script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ctx=vm.createContext({window:{MilkywayResearchView:{escape}},Set,Object,Array,String});
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const view=ctx.window.MilkywayCompanyRelations,primary={level:'primary'},wiki={level:'encyclopedia'};
const edge=(kind,index,source=wiki)=>({kind,name:'Company '+index,target_id:'c_'+String(index).padStart(32,'0'),source,detail:'Source detail'});
const rows=[edge('owner',1),edge('holding',2),edge('subsidiary',3),edge('supplier',4),
 edge('customer',5,primary),{...edge('supplier',6),evidence:[{source:wiki,detail:'Generic'},
 {source:primary,detail:'Laser <component> supplied',reverse:true,reported_by:'Source company'}]}];
const selected=view.select(rows,'business');
assert.equal(selected.length,4);assert(!selected.some(row=>['owner','holding'].includes(row.kind)));
assert.equal(selected[0].target_id,rows[5].target_id);assert.equal(selected[1].kind,'customer');
assert.equal(view.select(rows,'all').length,6);assert.equal(view.select(rows,'owner')[0].index,0);
const identified={...edge('subsidiary',9,primary),name:'Z Operating subsidiary',business:{detail:'검토된 윤활유 사업',source:primary}};
const shell={...edge('subsidiary',8,primary),name:'123 Legal entity'};
const ranked=view.select([shell,identified,edge('supplier',7,primary)],'business');
assert.equal(ranked[0].kind,'supplier');assert.equal(ranked[1].name,identified.name);
assert.equal(ranked[2].name,shell.name);assert.equal(view.select([shell,identified],'subsidiary')[0].name,identified.name);
assert.equal(view.lead(rows[5]).detail,'Laser <component> supplied');assert.equal(rows[5].evidence[0].detail,'Generic');
assert.equal(view.lead({evidence:[{detail:'Old',source:{level:'primary',as_of:'2025-01-26'}},
 {detail:'Current',source:{level:'primary',as_of:'2026-02-25'}},
 {detail:'Later retrieval',source:{level:'primary',as_of:'열람 2026-10-01'}}]}).detail,'Current');
let svg=view.draw('<Apple>', 'AAPL', selected);
assert(svg.includes('Laser &lt;component&gt; supplied'));assert(!svg.includes('Laser <component>'));
assert(svg.includes('marker-start="url(#company-arrow-start)"'));assert(svg.includes('marker-end="url(#company-arrow-end)"'));
assert(svg.includes('id="company-arrow-start" viewBox="0 0 10 10" refX="9"'));
assert(svg.includes('근거 2건'));assert(svg.includes('href="#company/'+rows[5].target_id));
assert(!svg.includes('#company/'+rows[0].target_id));assert(svg.includes('&lt;Apple&gt;'));
svg=view.draw('Root','AAA',[{...rows[5],target_id:'javascript:alert(1)'}]);
assert(!svg.includes('javascript:'));assert(!svg.includes('role="link"'));
assert.equal(view.draw('Root','AAA',[]),'');
svg=view.draw('Corning Incorporated','GLW',[rows[5]]);
assert(svg.includes('class="graph-center-title">Corning</text>'));
assert(svg.includes('class="graph-center-title">Incorporated</text>'));
svg=view.draw('Root','AAA',Array.from({length:8},(_,i)=>edge('supplier',i+10,primary)));
assert(svg.includes('viewBox="0 0 1000 660"'));assert.equal((svg.match(/class="company-graph-node"/g)||[]).length,8);
"""
        path = (
            Path(__file__).resolve().parents[1]
            / "cloud_app/static/company-relations.js"
        )
        result = subprocess.run(
            [shutil.which("node"), "-e", script, str(path)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for frontend checks")
    def test_reload_keeps_canonical_address_and_parent_history(self):
        script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[1],'utf8'),key='c_'+'a'.repeat(32),calls=[];
const context=vm.createContext({state:{me:{id:'user'},config:{},preferences:{default_market:'us'},stream:true},
 location:{hash:'#company/'+key},profileController:{render(){}},
 api:async(path)=>path==='/api/config'?{personal_local_mode:true}:{id:'user',csrf:'synthetic'},
 $:()=>({classList:{add(){},remove(){}}}),applyMarketPreference(){},refresh:async()=>{},
 openWorkspace(workspace,updateHash){calls.push({workspace,updateHash});if(updateHash)context.location.hash='#'+workspace;},
 window:{MilkywayCompany:{openEntity:async(id,push)=>calls.push({id,push})}}});
const dashboard=source.slice(source.indexOf('async function showDashboard('),source.indexOf('\nfunction accountCards('));
const enter=source.slice(source.indexOf('async function enterApp('),source.indexOf('\nfunction openBacktest('));
vm.runInContext(dashboard+'\n'+enter,context);
(async()=>{await vm.runInContext('enterApp()',context);assert.equal(context.location.hash,'#company/'+key);
assert.equal(calls[0].updateHash,false);assert.equal(calls[1].id,key);assert.equal(calls[1].push,false);})()
.catch(e=>{console.error(e);process.exitCode=1;});
"""
        path = Path(__file__).resolve().parents[1] / "cloud_app/static/app.js"
        result = subprocess.run(
            [shutil.which("node"), "-e", script, str(path)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for frontend checks")
    def test_escaping_pagination_filters_and_stale_navigation(self):
        script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const elements=new Map(),documentHandlers={},panelHandlers={};
function el(id){
 if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',value:'all',disabled:false,options:[{value:'supplier',textContent:''}],
  classList:{add(){},remove(){}},querySelectorAll(){return[];},after(){},before(){},append(){},
  addEventListener(kind,fn){this[kind]=fn;},scrollIntoView(){}});
 return elements.get(id);
}
const panel={dataset:{},querySelectorAll(){return[];},addEventListener(kind,fn){panelHandlers[kind]=fn;}};
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state={workspace:'company',me:{id:'owner'},config:{personal_local_mode:true}},calls=[],resolveDelayed,poll;
const src={label:'SEC <bad>',url:'https://www.sec.gov/',as_of:'2025-12-31',level:'primary'};
const result={symbol:'AAPL',name:'<script>Apple</script>',description:'description',sector:'us_45',sector_label:'Information Technology',
 entity_key:'c_'+'a'.repeat(32),collectable:true,
 quote:{market_cap:1000000,currency:'USD',displayed_share_pct:20,source:'Yahoo',url:'https://finance.yahoo.com/'},
 pending:false,stale:false,errors:[],fetched_at:'2026-10-01T00:00:00Z',sources:[src],report_analysis:{title:'공시 본문',detail:'<script>unsafe</script>',source:src},
 related_directory:{MSFT:{sector:'us_45',name:'Microsoft'}},peers:[{symbol:'MSFT',name:'Microsoft',currency:'USD',market_cap:12,source:'Yahoo',url:'https://finance.yahoo.com/quote/MSFT/'}],financials:[],filings:[],facts:[],segments:[],drivers:[],market_shares:[],
 products:Array.from({length:12},(_,i)=>({title:`<img Product ${i}>`,detail:'safe',source:src})),
 relations:Array.from({length:12},(_,i)=>({name:`Company <${i}>`,target_id:'c_'+String(i+1).padStart(32,'0'),kind:i===0?'supplier':'subsidiary',symbol:i===0?'MSFT':null,detail:'Source-backed relation',source:src}))};
let delayed=false,response=result;
result.relations[0].business={title:'기업 사업',detail:'<script>검사 장비</script>',source:src};
const ctx=vm.createContext({window:{MilkywayResearchView:{escape},MilkywayCompanyPrice:{create:()=>({setContext(){},clear(){}})},getSelection:()=>null},
 document:{querySelector:el,createElement:()=>panel,addEventListener(kind,fn){documentHandlers[kind]=fn;}},
 history:{state:null,pushState(value){this.state=value;},back(){}},setInterval(fn){poll=fn;},Intl,Date,Number,Math,Map,Set,URL,encodeURIComponent});
for(const name of ['format.js','list-paging.js','market-directory.js','company-research-view.js','company-relations.js','company-network.js','company-page.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+name,'utf8'),ctx);
ctx.window.MilkywayCompany.initialize({getState:()=>state,openWorkspace:workspace=>{state.workspace=workspace;},
 api:async(path,options)=>{calls.push({path,options});if(delayed)return await new Promise(resolve=>{resolveDelayed=resolve});return response;}});
function click(attribute,value){panelHandlers.click({target:{closest(selector){return selector==='['+attribute+']'?{dataset:{[attribute.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]:String(value)}}:null;}}});}
(async()=>{
 await ctx.window.MilkywayCompany.open('us_45','AAPL');
 assert.equal(calls.length,1);assert(!calls[0].options);
 assert(el('#companyQuote').innerHTML.includes('1,000,000'));
 assert(el('#companyGraph').innerHTML.includes('&lt;script&gt;'));assert(!el('#companyGraph').innerHTML.includes('<script>'));
 assert(el('#companyProducts').innerHTML.includes('&lt;img'));assert(!el('#companyProducts').innerHTML.includes('<img'));
 assert(!el('#companyProducts').innerHTML.includes('Product 8'));assert.equal(el('#companyRelationFilter').value,'business');
 click('data-product-page',2);assert(el('#companyProducts').innerHTML.includes('Product 8'));assert(!el('#companyProducts').innerHTML.includes('Product 0'));
 click('data-relation-page',2);assert(el('#companyRelationSummary').textContent.includes('현재 페이지 4개'));
 el('#companyRelationFilter').value='supplier';el('#companyRelationFilter').change();
 assert(el('#companyRelationFocus').innerHTML.includes(result.relations[0].target_id));assert(!el('#companyRelationList').innerHTML.includes('&lt;1&gt;'));
 assert(el('#companyRelationFocus').innerHTML.includes('기업 사업'));assert(el('#companyRelationList').innerHTML.includes('&lt;script&gt;검사 장비'));
 assert(!el('#companyRelationFocus').innerHTML.includes('<script>'));assert(!el('#companyRelationList').innerHTML.includes('<script>'));
 response={...result,relations:[...result.relations.slice(1),result.relations[0]]};poll();await new Promise(setImmediate);
 assert(el('#companyRelationFocus').innerHTML.includes(result.relations[0].target_id));assert(!el('#companyRelationFocus').innerHTML.includes(result.relations[1].target_id));
 response=result;poll();await new Promise(setImmediate);
 assert(el('#companyGraph').innerHTML.includes('href="#company/'+result.relations[0].target_id));
 assert(el('#companyGraph').innerHTML.includes('role="link"'));assert(!el('#companyRelationList').innerHTML.includes('style='));
 assert(el('#companySources').innerHTML.includes('&lt;bad&gt;'));assert(el('#companySourceCount').textContent.includes('3개'));
 assert(el('#companyReportAnalysis').innerHTML.includes('&lt;script&gt;'));assert(!el('#companyReportAnalysis').innerHTML.includes('<script>'));
 assert(el('#companyRelationFilter').options[0].textContent.includes('1'));
 calls=[];await ctx.window.MilkywayCompany.openEntity(result.relations[0].target_id);
 assert.equal(calls[0].path,'/api/company-entities/'+result.relations[0].target_id);
 assert.equal(ctx.history.state.parentCompany,result.entity_key);
 ctx.window.MilkywayCompany.leave();await ctx.window.MilkywayCompany.openEntity(result.entity_key);
 assert(el('#companyPeers').innerHTML.includes('#company/us_45/MSFT'));assert(!el('#companyPeers').innerHTML.includes('#company/null/'));
 calls=[];await ctx.window.MilkywayCompany.openEntity('../env');assert.equal(calls.length,0);
 const privateKey='c_'+'b'.repeat(32);
 response={...result,entity_key:privateKey,symbol:null,sector:null,sector_label:'기업 관계 자료',collectable:false,stale:true,
   quote:{market_cap:null,currency:'',displayed_share_pct:null,source:'',url:''},quote_basis:{},
   relations:[{...result.relations[0],target_id:result.entity_key,kind:'parent',reverse:true,reported_by:'Apple <raw>',
     evidence:[{detail:'First <claim>',source:src,reverse:true,reported_by:'Apple <raw>'},
       {detail:'Second <claim>',source:{...src,label:'Second <report>',url:'https://www.sec.gov/other'},reverse:false}]}]};
 calls=[];
 documentHandlers.click({button:0,preventDefault(){},target:{closest(selector){return selector==='[data-company-id]'?{dataset:{companyId:privateKey}}:null;}}});
 await new Promise(setImmediate);
 assert.equal(calls.length,1);assert.equal(calls[0].path,'/api/company-entities/'+privateKey);
 assert(el('#companyCollect').disabled);assert(el('#companyQuote').innerHTML.includes('종목 미등록'));
 assert(!el('#companyQuote').innerHTML.includes('1,000,000'));
 assert(el('#companyRelationFocus').innerHTML.includes('Apple &lt;raw&gt;'));assert(el('#companyRelationFocus').innerHTML.includes('반대 방향'));
 assert(el('#companyRelationFocus').innerHTML.includes('First &lt;claim&gt;'));assert(el('#companyRelationFocus').innerHTML.includes('Second &lt;claim&gt;'));
 assert(el('#companyRelationList').innerHTML.includes('근거 2건'));assert(el('#companySourceCount').textContent.includes('3개'));
 assert(el('#companySources').innerHTML.includes('Second &lt;report&gt;'));
 response=result;
 calls=[];delayed=true;const opening=ctx.window.MilkywayCompany.open('us_45','AAPL');
 ctx.window.MilkywayCompany.leave();state.workspace='market';resolveDelayed({...result,stale:true});await opening;
 assert.equal(calls.length,1);assert(!calls.some(row=>row.options?.method==='POST'));
 calls=[];await ctx.window.MilkywayCompany.open('../env','AAPL');assert.equal(calls.length,0);
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        root = Path(__file__).resolve().parents[1] / "cloud_app/static"
        result = subprocess.run(
            [shutil.which("node"), "-e", script, str(root)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Node is needed for frontend checks')
    def test_two_hop_network_bottom_sources_and_stale_owner_boundaries(self):
        script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const els=new Map(),el=id=>{if(!els.has(id))els.set(id,{innerHTML:'',value:'all',addEventListener(kind,fn){this[kind]=fn;}});return els.get(id);};
const ctx=vm.createContext({window:{MilkywayResearchView:{escape}},document:{querySelector:el},Map,Set,Intl,URL,Number,String,Object,Array,encodeURIComponent});
for(const file of ['format.js','market-directory.js','company-research-view.js','company-network.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+file,'utf8'),ctx);
const key='c_'+'a'.repeat(32),via='c_'+'b'.repeat(32),leaf='c_'+'c'.repeat(32);
const src={label:'Visible source',url:'https://www.sec.gov/a.htm',level:'primary',as_of:'2026-01-01'};
const extra={...src,label:'Extra source',url:'https://www.sec.gov/b.htm'};
const root={entity_key:key,name:'Root',sources:[src],relations:[]};
const node=(id,name)=>({id,name,symbol:null,brief:[{title:'사업',detail:'반도체 제조 사업',source:src}]});
const edge={name:'<img Leaf>',target_id:leaf,kind:'supplier',detail:'확인된 공급',source:extra,evidence_total:1,
 evidence:[{detail:'<script>Claim',original:'A public original',source:extra,reverse:true,reported_by:'Issuer <raw>'}]};
const payload={root:node(key,'Root'),via:node(via,'Middle'),direct:[edge],rows:[edge],page:1,pages:2,total:9,kind:'all',counts:{supplier:9}};
let state={me:{id:'owner'},workspace:'company'},calls=[],footer,lastReading,delayed=false,finish;
const network=ctx.window.MilkywayCompanyNetwork.create({getState:()=>state,footer:reading=>{lastReading=reading;footer=reading.footer();},
 api:async(path)=>{calls.push(path);return delayed?await new Promise(resolve=>{finish=resolve}):payload;}});
(async()=>{
 network.setContext(root,ctx.window.MilkywayCompanyResearchView.create(root));assert.equal(calls.length,0);
 await network.open(via);assert.equal(calls.length,1);assert(calls[0].includes('/network?via='+via));
 const html=el('#companyNetwork').innerHTML;
 assert(html.includes('href="#company/'+leaf));assert(html.includes('&lt;img'));assert(!html.includes('<img'));
 assert(html.includes('&lt;script&gt;Claim'));assert(html.includes('Issuer &lt;raw&gt;'));assert(!html.includes('href="https:'));
 assert(html.includes('직접 거래'));assert(html.includes('1 / 2'));assert(html.includes('<details class="company-original">'));
 assert.equal(lastReading.count,2);assert(footer.includes('Extra source'));assert(footer.includes('https://www.sec.gov/b.htm'));
 calls=[];await network.open('../env');await network.open(via,'owner');await network.open(via,'all',51);assert.equal(calls.length,0);
 network.page(2);await new Promise(setImmediate);assert(calls[0].endsWith('page=2'));
 // A late response from the previous owner cannot replace the current panel.
 delayed=true;const pending=network.open(via);state.me.id='another';const before=el('#companyNetwork').innerHTML;
 finish({...payload,via:node(via,'STALE OWNER')});await pending;assert.equal(el('#companyNetwork').innerHTML,before);
 state.me.id='owner';const pending2=network.open(via);network.reset();finish({...payload,via:node(via,'STALE NAVIGATION')});await pending2;
 assert(!el('#companyNetwork').innerHTML.includes('STALE'));
 delayed=false;network.setContext(root,ctx.window.MilkywayCompanyResearchView.create(root));
 await network.open(via);await network.open(via);assert.equal(lastReading.count,2);
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        root=Path(__file__).resolve().parents[1]/'cloud_app/static'
        result=subprocess.run([shutil.which('node'),'-e',script,str(root)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)



if __name__ == "__main__":
    unittest.main()
