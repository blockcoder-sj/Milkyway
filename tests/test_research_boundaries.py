"""Keep the research boundary explicit, and test its UI without a browser or API."""
import ast
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ResearchBoundaryTests(unittest.TestCase):
    def test_research_modules_do_not_import_the_composition_root(self):
        for path in (ROOT / "cloud_app").glob("research_*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, ("main", "cloud_app.main"), str(path))
                    if node.module in (None, "cloud_app"):
                        self.assertNotIn("main", [alias.name for alias in node.names], str(path))
                elif isinstance(node, ast.Import):
                    self.assertNotIn("cloud_app.main", [alias.name for alias in node.names], str(path))
        routes = (ROOT / "cloud_app/research_routes.py").read_text()
        for forbidden in ("from sqlalchemy", ".commit()", "invoke_approved(", "from .database"):
            self.assertNotIn(forbidden, routes)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for UI unit checks")
    def test_ui_escaping_approval_and_refresh_without_a_browser(self):
        script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const root=process.argv[1], elements=new Map(), handlers=new Map();
function element(key) {
 if(!elements.has(key)) elements.set(key, {innerHTML:'',textContent:'',value:'',hidden:false,disabled:false,
  elements:{strategy_id:{value:'',innerHTML:''},prompt:{value:'',focus(){}}},dataset:{},classList:{toggle(){}},
  removeAttribute(){},querySelectorAll(){return []},reset(){},
  addEventListener(event,handler){handlers.set(key+':'+event,handler)}});
 return elements.get(key);
}
const document={querySelector:element,querySelectorAll(){return []}},window={};
const context=vm.createContext({window,document,console,encodeURIComponent,crypto:{randomUUID(){return 'unit-request-0001'}}});
for(const file of ['format.js','research/api.js','research/view.js','research/tuning.js','research.js'])vm.runInContext(fs.readFileSync(root+'/'+file,'utf8'),context);
const payload='<img src=x onerror=alert(1)>', calls=[];
const room={id:'room',selected_strategy_id:'v1',turns:[{id:'turn',status:'awaiting_approval',prompt:payload,
 approval:{model:'gpt-5.4-mini',reasoning:'none',max_output_tokens:4000,input_characters:20,request:{input:payload},request_digest:'a'.repeat(64)},
 response:{reply:payload,limitations:[payload],next_steps:[]}}],
 versions:[{id:'v1',number:1,name:payload,spec:{description:payload},code_preview:payload}],
 experiments:[],paper:[]};
const view=window.MilkywayResearchView.create();view.render(room,false);
for(const id of ['#researchTurns','#researchVersions']) {
 assert(!element(id).innerHTML.includes('<img'),id);assert(element(id).innerHTML.includes('&lt;img'),id);
}
assert(element('#researchMessage button').disabled);
assert(element('#researchTurns').innerHTML.includes('data-research-action="approve"'));
const spec={symbols:['NVDA','MSFT'],factors:[{kind:'mean_reversion',lookback:20,weight:1},{kind:'rsi',lookback:14,weight:-0.5}],
 portfolio:{initial_cash:100000,max_positions:2,investment_fraction:0.7,max_position_fraction:0.4,
 rebalance_days:10,rebalance_weights:true,stop_loss_pct:-0.05,cost_per_side:0.003},
 filters:{min_price:5,min_average_volume:200000,history_days:60}};
const rules=window.MilkywayResearchView.executionRules(spec);
for(const text of ['100,000','70.00%','40.00%','10달력일','20거래일','수익률 낮은 순','RSI 낮은 순','200,000','평균 매입단가'])assert(rules.includes(text),text);
const allocation={...spec,symbols:['AAPL','MSFT','NVDA','AMD','AVGO'],portfolio:{...spec.portfolio,max_positions:5,investment_fraction:0.8,max_position_fraction:0.2}};
const allocationRules=window.MilkywayResearchView.executionRules(allocation);
assert(allocationRules.includes('전체 자산 기준 종목당 16.00% · 현금 20.00%'));
assert(allocationRules.includes('종목당 목표 상한 20.00%'));
assert(allocationRules.includes('휴장일에는 다음 거래 가능 시점'));
const cappedRules=window.MilkywayResearchView.executionRules({...allocation,portfolio:{...allocation.portfolio,max_position_fraction:0.1,rebalance_weights:false}});
assert(cappedRules.includes('전체 자산 기준 종목당 10.00% · 현금 50.00%'));
assert(cappedRules.includes('유지 종목의 수량 유지'));
assert(cappedRules.includes('비용 반영 전'));
assert(!window.MilkywayResearchView.executionRules({...allocation,symbols:[]}).includes('비중 계산 예시'));
room.turns[0].status='completed';room.turns[0].strategy_id='v1';room.turns[0].response.strategy={...spec,symbols:[payload]};
room.versions[0].spec=spec;view.invalidate();view.render(room,false);
assert(element('#researchTurns').innerHTML.includes('NVDA, MSFT'),'Execution rules come from the saved version');
assert(!element('#researchTurns').innerHTML.includes('대상 종목</th><td>&lt;img'),'Rejected response fields cannot replace the saved rules');
room.turns[0].status='awaiting_approval';view.invalidate();view.render(room,false);
const api=window.MilkywayResearchApi.create(async(path,options)=>{calls.push({path,options});return {}});
(async()=>{
 await api.prepare('room',{prompt:'test',request_id:'test-0001'});
 assert(!calls.some(c=>c.path.endsWith('/approve')));
 await api.approve('turn', 'a'.repeat(64));
 assert.equal(calls.length,2);assert.equal(calls[1].options.method,'POST');
 assert.equal(calls[1].options.body,JSON.stringify({approved:true,request_digest:'a'.repeat(64)}));
 calls.length=0;
 window.MilkywayResearchPanel={mount(){}};
 window.MilkywayPersonal={isPersonal(){return true}};
 const state={me:{id:'owner'},workspace:'strategy'};
 window.MilkywayResearch.initialize({getState:()=>state,refresh:async()=>{},toast(){},api:async(path,options)=>{
  calls.push({path,options});
  if(path.endsWith('/config'))return {model:'gpt-5.4-mini',reasoning:'none',configured:true};
  if(path.endsWith('/sessions'))return [{id:'room',title:payload}];
  return room;
 }});
 await window.MilkywayResearch.refresh();await window.MilkywayResearch.refresh();
 assert(calls.every(call=>!call.options),'Refresh must never spend or mutate');
 assert(!element('#researchSessions').innerHTML.includes('<img'));
 assert.equal(element('#researchDeploy').elements.strategy_id.value,'v1');
 room.turns[0].status='failed';room.turns[0].error='전략 검증 실패';
 room.turns[0].response.strategy=null;
 view.invalidate();view.render(room,false);
 assert(element('#researchTurns').innerHTML.includes('data-research-action="retry"'));
 assert(element('#researchTurns').innerHTML.includes('전략은 저장하지 않았습니다'));
 calls.length=0;
 const retryButton={dataset:{researchAction:'retry',id:'turn'}};
 handlers.get('#researchPanel:click')({target:{closest(){return retryButton}}});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(element('#researchMessage').elements.prompt.value,payload);
 assert.equal(calls.length,0,'Copying a failed hypothesis must make no API request');
 element('#researchMessage').elements.prompt.value='작성 중인 새 가설';
 handlers.get('#researchPanel:click')({target:{closest(){return retryButton}}});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(element('#researchMessage').elements.prompt.value,'작성 중인 새 가설');
 assert(calls.every(call=>!call.options),'Recovery may only refresh local saved state');
 assert(element('#researchError').textContent.includes('작성 중인'));
 console.log('research UI boundary checks passed');
})().catch(error=>{console.error(error);process.exitCode=1});
'''
        result = subprocess.run([shutil.which("node"), "-e", script, str(ROOT / "cloud_app/static")],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
