"""Executable company view behavior using synthetic DOM/data, no provider calls."""
from pathlib import Path
import shutil
import subprocess
import unittest


class CompanyFrontendTests(unittest.TestCase):
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
assert.equal(view.lead(rows[5]).detail,'Laser <component> supplied');assert.equal(rows[5].evidence[0].detail,'Generic');
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
 if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',value:'all',disabled:false,
  classList:{add(){},remove(){}},querySelectorAll(){return[];},after(){},
  addEventListener(kind,fn){this[kind]=fn;},scrollIntoView(){}});
 return elements.get(id);
}
const panel={dataset:{},querySelectorAll(){return[];},addEventListener(kind,fn){panelHandlers[kind]=fn;}};
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state={workspace:'company',me:{id:'owner'},config:{personal_local_mode:true}},calls=[],resolveDelayed;
const src={label:'SEC <bad>',url:'https://www.sec.gov/',as_of:'2025-12-31',level:'primary'};
const result={symbol:'AAPL',name:'<script>Apple</script>',description:'description',sector:'us_45',sector_label:'Information Technology',
 entity_key:'c_'+'a'.repeat(32),collectable:true,
 quote:{market_cap:1000000,currency:'USD',displayed_share_pct:20,source:'Yahoo',url:'https://finance.yahoo.com/'},
 pending:false,stale:false,errors:[],fetched_at:'2026-10-01T00:00:00Z',sources:[src],
 related_directory:{MSFT:{sector:'us_45',name:'Microsoft'}},peers:[{symbol:'MSFT',name:'Microsoft',currency:'USD',market_cap:12,source:'Yahoo',url:'https://finance.yahoo.com/quote/MSFT/'}],financials:[],filings:[],facts:[],segments:[],drivers:[],market_shares:[],
 products:Array.from({length:12},(_,i)=>({title:`<img Product ${i}>`,detail:'safe',source:src})),
 relations:Array.from({length:12},(_,i)=>({name:`Company <${i}>`,target_id:'c_'+String(i+1).padStart(32,'0'),kind:i===0?'supplier':'subsidiary',symbol:i===0?'MSFT':null,detail:'Source-backed relation',source:src}))};
let delayed=false,response=result;
const ctx=vm.createContext({window:{MilkywayResearchView:{escape},getSelection:()=>null},
 document:{querySelector:el,createElement:()=>panel,addEventListener(kind,fn){documentHandlers[kind]=fn;}},
 history:{state:null,pushState(value){this.state=value;},back(){}},setInterval(){},Intl,Date,Number,Math,Map,Set,URL,encodeURIComponent});
for(const name of ['format.js','list-paging.js','market-directory.js','company-relations.js','company-page.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+name,'utf8'),ctx);
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
 assert(el('#companyGraph').innerHTML.includes('href="#company/'+result.relations[0].target_id));
 assert(el('#companyGraph').innerHTML.includes('role="link"'));assert(!el('#companyRelationList').innerHTML.includes('style='));
 assert(el('#companySources').innerHTML.includes('&lt;bad&gt;'));assert(el('#companySourceCount').textContent.includes('1개'));
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
 assert(el('#companyRelationList').innerHTML.includes('근거 2건'));assert(el('#companySourceCount').textContent.includes('2개'));
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


if __name__ == "__main__":
    unittest.main()
