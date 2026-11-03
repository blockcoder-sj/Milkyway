"""Executable recovery UI behavior without real network or brokerage requests."""
from pathlib import Path
import shutil
import subprocess
import unittest


class RuntimeFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_disconnect_reconnect_and_one_click_resume_preserve_the_selected_account(self):
        script = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[1],'utf8');
const nodes=new Map(), timers=new Map();let timerId=0,offline=false,resumes=0,sessionChecks=0,fetches=0;
function node(){return {innerHTML:'',textContent:'',hidden:false,disabled:false,value:'',dataset:{},className:'',classList:{add(){},remove(){},toggle(){}},addEventListener(){},removeAttribute(){}};}
const ids=['personalRuntimeControls','runtimeAccount','runtimeTitle','runtimeStateDot','operationMessage','operationPanel','runtimeChecks','runtimeProgress','runtimeLauncherHint','runtimeLastChecked','operationFacts','workerStatus','resumePersonal'];
for(const id of ids)nodes.set('#'+id,node());
const account='a'.repeat(32), state={config:{personal_local_mode:true},me:{id:'owner'}};
const data={checked_at:new Date().toISOString(),account_id:account,account_name:'kept',accounts:[{id:account,name:'<img onerror=bad>',status:'active',expired:false}],state:'running',title:'자동매매 정상',message:'전략 조건 관찰',tone:'ok',market_open:true,credential_saved:true,workers:{paper:{alive:true},data:{alive:true}},quotes:{fresh:2,required:2}};
const calls=[];
const ctx=vm.createContext({window:{},document:{querySelector:s=>nodes.get(s),hidden:false},navigator:{onLine:true},localStorage:{getItem:()=>account,setItem(){}},AbortController,Date,console,
setInterval(){},setTimeout(fn,ms){const id=++timerId;timers.set(id,{fn,ms});return id;},clearTimeout(id){timers.delete(id);},addEventListener(){},fetch(){fetches++;throw Error('no real network');}});
vm.runInContext(source,ctx);
const runtime=ctx.window.MilkywayRuntime;
const hooks={getState:()=>state,ensureSession:async()=>{sessionChecks++;},refresh:async()=>{},api:async(path,options={})=>{
calls.push([path,options.body]);
if(path==='/api/personal/control')return {available:false,url:'http://127.0.0.1:19480'};
if(path==='/api/personal/resume'){resumes++;return {resumed:true};}
if(offline)throw Error('offline');
return data;}};
(async()=>{
runtime.initialize(hooks);await runtime.poll();
assert.equal(nodes.get('#runtimeTitle').textContent,'자동매매 정상');
assert.match(nodes.get('#runtimeAccount').innerHTML,/&lt;img/);
nodes.get('#runtimeProgress').textContent='old completion';offline=true;await runtime.poll();assert.notEqual(nodes.get('#runtimeTitle').textContent,'자동매매 정상');assert.match(nodes.get('#runtimeChecks').innerHTML,/미확인/);assert.equal(nodes.get('#runtimeProgress').textContent,'');
offline=false;await runtime.poll();assert.equal(nodes.get('#runtimeTitle').textContent,'자동매매 정상');
assert.notEqual(runtime.view(data,false).tone,'ok');
assert.equal(runtime.processView(data,{available:true,services:{'paper-worker':'exited','personal-data':'running'}}).state,'worker_offline');
assert.equal(runtime.processView(data,{available:false}).ready_to_trade,false);
await runtime.recover();assert.equal(resumes,1);assert.ok(sessionChecks>=1);
const resume=calls.find(([path])=>path==='/api/personal/resume');assert.equal(JSON.parse(resume[1]).account_id,account);
assert.ok(calls.every(([path])=>path!='/api/accounts'));assert.equal(fetches,0);assert.equal(nodes.get('#resumePersonal').disabled,false);
let release;hooks.api=async(path,options={})=>{if(path==='/api/personal/control')return {available:false};if(path==='/api/personal/resume'){resumes++;await new Promise(r=>release=r);return {};}return data;};
const first=runtime.recover();for(let i=0;i<12;i++)await Promise.resolve();const second=runtime.recover();
assert.equal(resumes,2);release();await Promise.all([first,second]);assert.equal(resumes,2);
hooks.api=async(path)=>path==='/api/personal/control'?{available:true,url:'https://evil.example',token:'a'.repeat(64)}:data;
await runtime.recover();assert.equal(fetches,0);
await runtime.poll();assert.equal(nodes.get('#runtimeTitle').textContent,'실행 프로세스 확인 필요');
assert.notEqual(nodes.get('#personalRuntimeControls').dataset.tone,'ok');
console.log('disconnect/reconnect, selected-only resume, duplicate click and fixed loopback controls passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        path=Path(__file__).resolve().parents[1]/"cloud_app/static/personal-runtime.js"
        result=subprocess.run([shutil.which("node"),"-e",script,str(path)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
