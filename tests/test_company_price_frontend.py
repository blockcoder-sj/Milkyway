"""Executable price component checks with synthetic DOM and asynchronous replies."""
from pathlib import Path
import shutil
import subprocess
import unittest


class CompanyPriceFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is needed for frontend checks')
    def test_network_pages_and_live_prices_share_one_bounded_citation_registry(self):
        script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const elements=new Map();let poll,calls=0,reading,footerText='',page=1;
const el=id=>{if(!elements.has(id))elements.set(id,{innerHTML:'',addEventListener(){}});return elements.get(id);};
const ctx=vm.createContext({window:{MilkywayResearchView:{escape}},document:{hidden:false,querySelector:el},setInterval(fn){poll=fn;},URL,Intl,Date,encodeURIComponent});
for(const file of ['format.js','market-directory.js','company-research-view.js','company-price.js','company-network.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+file,'utf8'),ctx);
const key='c_'+'a'.repeat(32),via='c_'+'b'.repeat(32),leaf='c_'+'c'.repeat(32),state={workspace:'company',me:{id:'owner'}};
const origin={label:'Root filing',url:'https://www.sec.gov/report',level:'primary'};
const root={entity_key:key,symbol:'AAA',name:'Root',sources:[origin],relations:[{target_id:via,kind:'supplier',source:origin}]};
const quote={symbol:'AAA',value:100,currency:'USD',source:'Yahoo',source_url:'https://finance.yahoo.com/quote/AAA/',status:'closed',observed_at:'2026-10-02T00:00:00Z',fetched_at:'2026-10-02T00:00:01Z'};
reading=ctx.window.MilkywayCompanyResearchView.create(root);
const target={innerHTML:''},footer=next=>{if(next)reading=next;footerText=reading.footer();};
const prices=ctx.window.MilkywayCompanyPrice.create({api:async(_,options)=>{calls++;return options?{}:quote;},getState:()=>state,target,footer});
const network=ctx.window.MilkywayCompanyNetwork.create({getState:()=>state,footer,prepareReading:next=>prices.useReading(next),
 api:async()=>({root:{id:key,name:'Root'},via:{id:via,name:'Via'},direct:[],kind:'all',counts:{supplier:1},total:2,page,pages:2,
 rows:[{name:'Leaf',target_id:leaf,kind:'supplier',detail:'Recorded supply',source:{...origin,url:'https://issuer.example/claim-'+page},
 business:{detail:'한글 제품 정리',source:{...origin,url:'https://issuer.example/products-'+page}}}]})});
const tick=()=>new Promise(setImmediate);
(async()=>{
 prices.setContext(root,reading);await tick();network.setContext(root,reading);
 assert.equal(calls,2);assert(target.innerHTML.includes('data-company-citation="2"'));
 await network.open(via);
 assert.equal(calls,2);assert.equal(reading.count,4);
 assert(footerText.includes('id="company-source-2"><strong><a href="https://finance.yahoo.com/quote/AAA/"'));
 assert(target.innerHTML.includes('data-company-citation="2"'));assert(el('#companyNetwork').innerHTML.includes('data-company-citation="3"'));
 poll();await tick();assert.equal(calls,3);assert.equal(reading.count,4);assert(footerText.includes('claim-1'));
 page=2;await network.open(via,'all',2);
 assert.equal(calls,3);assert.equal(reading.count,4);assert(!footerText.includes('claim-1'));assert(footerText.includes('claim-2'));
 assert(target.innerHTML.includes('data-company-citation="2"'));assert(footerText.includes('id="company-source-2"><strong><a href="https://finance.yahoo.com/quote/AAA/"'));
 prices.clear();
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        root=Path(__file__).resolve().parents[1]/'cloud_app/static'
        result=subprocess.run([shutil.which('node'),'-e',script,str(root)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Node is needed for frontend checks')
    def test_numbers_sources_owner_navigation_visibility_and_failure(self):
        script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let poll,state={workspace:'company',me:{id:'first'}},calls=[],resolvers=[],delayed=false,failed=false,footers=0;
const ctx=vm.createContext({window:{MilkywayResearchView:{escape}},document:{hidden:false},
 setInterval(fn){poll=fn;},Date,Intl,Number,String,encodeURIComponent});
for(const file of ['format.js','company-price.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+file,'utf8'),ctx);
const view=ctx.window.MilkywayCompanyPrice;
const quote={symbol:'AAPL',value:1234.5,currency:'USD',change:10,change_pct:1,previous_close:1224.5,
 source:'<Provider>',source_url:'https://www.sec.gov/',status:'realtime',observed_at:'2026-10-02T14:00:00Z',fetched_at:'2026-10-02T14:00:01Z'};
const markup=view.html(quote);assert(markup.includes('1,234.50'));assert(markup.includes('+10.00'));
assert(markup.includes('실시간 체결'));assert(markup.includes('&lt;Provider&gt;'));assert(!markup.includes('<Provider>'));
assert(!markup.includes('href="https:'));assert(view.html({...quote,currency:'KRW',value:120000}).includes('120,000'));
assert(!view.html({...quote,value:null}).includes('0.00'));assert(view.html({...quote,status:'last_trade'}).includes('마지막 체결'));
const target={innerHTML:''},reading={registerPrice(){},cite:()=>'<a data-company-citation="1">[1]</a>'};
const api=async(path,options)=>{calls.push({path,options});if(failed)throw Error('<synthetic failure>');if(options)return {};
 if(delayed)return await new Promise(resolve=>resolvers.push(resolve));return quote;};
const control=view.create({api,getState:()=>state,target,footer:()=>footers++});
const tick=()=>new Promise(setImmediate),key='c_'+'a'.repeat(32),other='c_'+'b'.repeat(32);
(async()=>{
 control.setContext({entity_key:key,symbol:'AAPL'},reading);await tick();
 assert.equal(calls.length,2);assert.equal(calls[0].options.method,'POST');assert(calls[0].path.endsWith('/price-watch?symbol=AAPL'));
 assert(target.innerHTML.includes('1,234.50'));assert.equal(footers,1);
 ctx.document.hidden=true;poll();await tick();assert.equal(calls.length,2);ctx.document.hidden=false;
 state={...state,me:{id:'second'}};poll();await tick();assert.equal(calls.length,2);state={...state,me:{id:'first'}};
 failed=true;poll();await tick();assert(target.innerHTML.includes('이전 시세 · 갱신 실패'));failed=false;
 delayed=true;poll();await tick();assert.equal(resolvers.length,1);
 control.clear();control.setContext({entity_key:other,symbol:'AAPL'},reading);await tick();assert.equal(resolvers.length,2);
 resolvers[0]({...quote,value:9999});await tick();assert(!target.innerHTML.includes('9,999'));
 state={...state,workspace:'market'};resolvers[1](quote);await tick();assert(!target.innerHTML.includes('1,234.50'));
 state={...state,workspace:'company'};delayed=false;control.setContext({entity_key:key,symbol:null},reading);
 assert(target.innerHTML.includes('비상장'));const count=calls.length;poll();await tick();assert.equal(calls.length,count);
 control.setContext({entity_key:'../secret',symbol:'AAPL'},reading);await tick();assert.equal(calls.length,count);
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        root=Path(__file__).resolve().parents[1]/'cloud_app/static'
        result=subprocess.run([shutil.which('node'),'-e',script,str(root)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
