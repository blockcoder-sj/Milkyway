"""Executable company view behavior using synthetic DOM/data, no provider calls."""
from pathlib import Path
import shutil
import subprocess
import unittest


class CompanyFrontendTests(unittest.TestCase):
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
 quote:{market_cap:1000000,currency:'USD',displayed_share_pct:20,source:'Yahoo',url:'https://finance.yahoo.com/'},
 pending:false,stale:false,errors:[],fetched_at:'2026-10-01T00:00:00Z',sources:[src],
 related_directory:{MSFT:{sector:'us_45',name:'Microsoft'}},financials:[],filings:[],facts:[],segments:[],drivers:[],market_shares:[],
 products:Array.from({length:12},(_,i)=>({title:`<img Product ${i}>`,detail:'safe',source:src})),
 relations:Array.from({length:12},(_,i)=>({name:`Company <${i}>`,kind:i===0?'supplier':'subsidiary',symbol:i===0?'MSFT':null,detail:'Source-backed relation',source:src}))};
let delayed=false;
const ctx=vm.createContext({window:{MilkywayResearchView:{escape},getSelection:()=>null},
 document:{querySelector:el,createElement:()=>panel,addEventListener(kind,fn){documentHandlers[kind]=fn;}},
 history:{pushState(){}},setInterval(){},Intl,Date,Number,Math,Map,Set,URL,encodeURIComponent});
for(const name of ['format.js','list-paging.js','market-directory.js','company-page.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+name,'utf8'),ctx);
ctx.window.MilkywayCompany.initialize({getState:()=>state,openWorkspace:workspace=>{state.workspace=workspace;},
 api:async(path,options)=>{calls.push({path,options});if(delayed)return await new Promise(resolve=>{resolveDelayed=resolve});return result;}});
function click(attribute,value){panelHandlers.click({target:{closest(selector){return selector==='['+attribute+']'?{dataset:{[attribute.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]:String(value)}}:null;}}});}
(async()=>{
 await ctx.window.MilkywayCompany.open('us_45','AAPL');
 assert.equal(calls.length,1);assert(!calls[0].options);
 assert(el('#companyQuote').innerHTML.includes('1,000,000'));
 assert(el('#companyGraph').innerHTML.includes('&lt;script&gt;'));assert(!el('#companyGraph').innerHTML.includes('<script>'));
 assert(el('#companyProducts').innerHTML.includes('&lt;img'));assert(!el('#companyProducts').innerHTML.includes('<img'));
 assert(!el('#companyProducts').innerHTML.includes('Product 8'));assert(!el('#companyRelationList').innerHTML.includes('&lt;8&gt;'));
 click('data-product-page',2);assert(el('#companyProducts').innerHTML.includes('Product 8'));assert(!el('#companyProducts').innerHTML.includes('Product 0'));
 click('data-relation-page',2);assert(el('#companyRelationList').innerHTML.includes('&lt;8&gt;'));
 el('#companyRelationFilter').value='supplier';el('#companyRelationFilter').change();
 assert(el('#companyRelationFocus').innerHTML.includes('MSFT'));assert(!el('#companyRelationList').innerHTML.includes('&lt;1&gt;'));
 assert(el('#companySources').innerHTML.includes('&lt;bad&gt;'));assert(el('#companySourceCount').textContent.includes('1개'));
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
