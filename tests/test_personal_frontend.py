"""Local UI contract and executable JavaScript behavior, without a browser."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "cloud_app" / "static"


class PersonalFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed for UI checks")
    def test_delete_confirmation_errors_and_refresh_do_not_send_duplicate_requests(self):
        script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(process.argv[1]+'/app.js','utf8');
const code=source.slice(source.indexOf('async function deleteResource('),source.indexOf('async function toggleAccount('));
let confirmed=false, personal=true, requests=[], messages=[], refreshes=0, fail=false, refreshed=false;
const history={open:true,dataset:{accountId:'a/one'},close(){this.open=false}};
const state={dashboard:{accounts:[{id:'a/one',name:'Synthetic account'}]},strategies:[{id:'s',name:'Strategy'}],refreshPromise:null,backtestOffset:50,backtestPage:[{}]};
const context=vm.createContext({state,window:{confirm:()=>confirmed,MilkywayPersonal:{isPersonal:()=>personal}},
 $:()=>history,toast:(...args)=>messages.push(args),encodeURIComponent,
 api:async(path,options)=>{requests.push({path,options});if(fail)throw new Error('연결된 계좌를 먼저 삭제하세요')},
 refresh:async()=>{assert(refreshed);refreshes++},console});
vm.runInContext(code,context);
const button={disabled:false};
(async()=>{
 await context.deleteResource('account','a/one',button);assert.equal(requests.length,0);
 confirmed=true;personal=false;
 await context.deleteResource('account','a/one',button);assert.equal(requests.length,0);personal=true;
 let completeOld;state.refreshPromise=new Promise(resolve=>{completeOld=()=>{refreshed=true;state.refreshPromise=null;resolve()}});
 const deleting=context.deleteResource('account','a/one',button);
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(requests.length,1);assert(button.disabled);assert.equal(refreshes,0);
 await context.deleteResource('account','a/one',button);assert.equal(requests.length,1);
 completeOld();await deleting;
 assert.equal(requests[0].path,'/api/accounts/a%2Fone');assert.equal(requests[0].options.method,'DELETE');
 assert.deepEqual(JSON.parse(requests[0].options.body),{confirm:true});assert.equal(refreshes,1);
 assert.equal(history.open,false);assert(!button.disabled);assert.equal(state.backtestOffset,0);
 fail=true;await context.deleteResource('strategy','s',button);
 assert.equal(requests.length,2);assert(!button.disabled);assert(messages.at(-1)[0].includes('연결된 계좌'));assert.equal(messages.at(-1)[1],true);
})().catch(error=>{console.error(error);process.exitCode=1});
'''
        result = subprocess.run(["node", "-e", script, str(STATIC)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_standalone_manual_builder_is_removed_but_research_tuning_remains(self):
        personal = (STATIC / "personal.js").read_text()
        for removed in ("manualStrategyForm", "manualSymbols", "manualFactors", "직접 규칙 입력", "function saveStrategy"):
            self.assertNotIn(removed, personal)
        panel = (STATIC / "research/panel.js").read_text()
        self.assertIn("미국 상장주식 전체에서 자동 선정", panel)
        self.assertIn("researchTuningForm", panel)
        self.assertIn(".personal-mode #strategyBuilder{display:none}", (STATIC / "styles.css").read_text())

    @unittest.skipUnless(shutil.which("node"), "Node is needed for UI checks")
    def test_one_session_account_shows_schedule_and_disables_resume_after_expiry(self):
        script = r'''
const assert = require("node:assert/strict"), fs = require("node:fs"), vm = require("node:vm");
const source = fs.readFileSync(process.argv[1] + "/app.js", "utf8");
const part = source.slice(source.indexOf("function accountCards("), source.indexOf("async function toggleAccount("));
const element = {}, count = {};
const ctx = vm.createContext({$: id => id === "#accountCards" ? element : count, $$: () => [],
  window:{MilkywayPersonal:{isPersonal:()=>true}},
  shortTime:()=>"now", money: x => String(x), pct: x => String(x), number: x => String(x), escapeHtml: x => String(x).replaceAll("<", "&lt;")});
vm.runInContext(part, ctx);
const row = {id:"a", name:"one day", status:"active", positions:[], equity:100000, initial_cash:100000, cash:100000, return_pct:0,
  paper_session:{session_date:"2026-10-02", closes_at:"2026-10-02T20:00:00Z", expired:false}};
ctx.rows = [row]; vm.runInContext("accountCards(rows)", ctx);
assert.match(element.innerHTML, /미국 거래일 2026-10-02/);
assert.match(element.innerHTML, /자동 중지/);
assert.match(element.innerHTML, /account-toggle/);
assert.match(element.innerHTML, /account-delete/);
row.automatic_selection={universe_count:6500,evaluated_count:6200,excluded:{history:300},fresh:true,created_at:"2026-11-05",weights:{AAA:.4}};
vm.runInContext("accountCards(rows)",ctx);
assert.match(element.innerHTML,/AAA 40/);

row.status="paused"; row.paper_session.expired=true;
row.paper_session.summary={fill_count:0,last_known_equity:100000};
vm.runInContext("accountCards(rows)", ctx);
assert.doesNotMatch(element.innerHTML, /account-toggle/);
assert.match(element.innerHTML, /지정 거래일 종료/);
assert.match(element.innerHTML, /체결 0건/);
assert.match(element.innerHTML, /공식 종가 미확인/);
row.paper_session=null; vm.runInContext("accountCards(rows)", ctx);
assert.match(element.innerHTML, /재개/);
'''
        result = subprocess.run([shutil.which("node"), "-e", script, str(STATIC)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for UI checks")
    def test_local_entry_uses_only_local_session_endpoint(self):
        script = r'''
const assert = require("node:assert/strict"), fs = require("node:fs"), vm = require("node:vm");
const source = fs.readFileSync(process.argv[1] + "/app.js", "utf8");
const start = source.indexOf("async function initializeApp()");
const bootstrap = source.slice(start, source.indexOf("\nstartMarketBackdrop();", start));
const elements = new Map(), calls = [];
let config = {personal_local_mode:true, local_auto_login:true}, entered;
function element(id) {
 if (!elements.has(id)) elements.set(id, {textContent:"", value:"", firstChild:{textContent:""},
   classList:{toggle(name, value){this[name] = value;}}, closest(){return this;}});
 return elements.get(id);
}
const ctx = vm.createContext({state:{}, $:element, api:async(path, options)=>{
 calls.push({path,options});
 if(path === "/api/config") return config;
 return {id:"owner", csrf:"synthetic-csrf"};
}, enterApp:async(me)=>{entered=me;}});
vm.runInContext(bootstrap, ctx);
(async()=>{
 await vm.runInContext("initializeApp()", ctx);
 assert.deepEqual(calls.map(c=>c.path), ["/api/config","/api/auth/local"]);
 assert.equal(calls[1].options.method,"POST");
 assert.equal(calls[1].options.headers["X-Milkyway-Local"],"1");
 assert.equal(entered.id,"owner");
 assert.equal(element("#profileMenu [data-profile-menu-action=logout]").classList.hidden,true);
 calls.length=0;config={personal_local_mode:false,local_auto_login:false};
 await vm.runInContext("initializeApp()", ctx);
 assert.deepEqual(calls.map(c=>c.path), ["/api/config","/api/auth/me"]);
 assert.equal(element("#profileMenu [data-profile-menu-action=logout]").classList.hidden,false);
})().catch(error=>{console.error(error);process.exitCode=1});
'''
        result = subprocess.run([shutil.which("node"), "-e", script, str(STATIC)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_credentials_are_confined_to_the_local_module(self):
        html = (STATIC / "index.html").read_text()
        profile = (STATIC / "profile.js").read_text()
        personal = (STATIC / "personal.js").read_text()
        self.assertNotIn('name="api_key"', html)
        self.assertNotIn('name="api_secret"', html)
        self.assertNotIn("api_key", profile)
        self.assertNotIn("localStorage", personal)
        self.assertNotIn("sessionStorage", personal)
        self.assertIn('!isPersonal() || connection.management !== "member"', personal)
        self.assertIn('form.elements.api_secret.value = ""', personal)
        self.assertIn('form.elements.api_key.value = ""', personal)
        self.assertIn('personal_use_only', personal)

    def test_beginner_actions_and_history_exports_are_present(self):
        html = (STATIC / "index.html").read_text()
        app = (STATIC / "app.js").read_text()
        personal = (STATIC / "personal.js").read_text()
        for expected in ('id="operationMessage"', 'id="connectionError"', 'id="accountHistoryDialog"'):
            self.assertIn(expected, html)
        self.assertNotIn('manualStrategyForm', personal)
        self.assertIn('account-delete', app)
        self.assertIn('strategy-delete', app)
        self.assertIn('/export?kind=fills', app)
        self.assertIn('/export?kind=equity', app)
        self.assertIn('/api/backtests?limit=50&offset=', app)
        self.assertNotIn('WORKER ONLINE', app)
        self.assertIn('execution_detail', app)

    @unittest.skipUnless(shutil.which("node"), "Node is optional; run on host for executable JS checks")
    def test_javascript_behavior_without_a_browser(self):
        script = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const root = process.argv[1];
const elements = new Map();
function element(selector) {
  if (!elements.has(selector)) elements.set(selector, {
    innerHTML: "", textContent: "", className: "", disabled: false, open: false, style: {}, dataset: {},
    classList: {toggle() {}, add() {}, remove() {}, contains() {return false;}},
    addEventListener() {}, setAttribute() {}, showModal() {this.open = true;},
    querySelectorAll() {return [];},
    insertAdjacentHTML(position, html) {this.innerHTML += html;},
  });
  return elements.get(selector);
}
let calls = [];
let response = {};
const context = vm.createContext({
  console, Intl, Date, Math, Number, String, Set, Map, URL, setTimeout: () => 0,
  document: {querySelector: element, querySelectorAll: () => []},
  window: {MilkywayProfile: {loadPreferences: () => ({default_market: "us"})}},
  fetch: async (path, options) => {calls.push([path, options]); return {status: 200, ok: true, json: async () => response};},
});
vm.runInContext(fs.readFileSync(root + "/format.js", "utf8"), context);
vm.runInContext(fs.readFileSync(root + "/personal.js", "utf8"), context);
vm.runInContext(fs.readFileSync(root + "/market-methods.js", "utf8"), context);
vm.runInContext(fs.readFileSync(root + "/market.js", "utf8"), context);
let app = fs.readFileSync(root + "/app.js", "utf8").split("\n$$('[data-auth-tab]').forEach")[0];
vm.runInContext(app, context);
vm.runInContext('window.MilkywayPersonal.initialize({getState: () => state});', context);
// A multi-tenant cloud page never creates a local credential form.
assert.equal(vm.runInContext('window.MilkywayPersonal.renderConnection({management:"member"})', context), false);
assert.equal(elements.size, 0);
vm.runInContext('state.config = {personal_local_mode:true};', context);
assert.equal(vm.runInContext('window.MilkywayPersonal.renderConnection({management:"credential_broker"})', context), false);
assert.equal(elements.size, 0);
vm.runInContext('state.dashboard = {accounts:[{id:"account-one", name:"내 계좌"}]};', context);
vm.runInContext('marketCards({us:[{label:"<script>bad</script>", value:10, status:"live", source:"kis", observed_at:"2026-09-25T15:00:00Z", is_realtime:true}]});', context);
assert.match(element("#watchlistCards").innerHTML, /&lt;script&gt;/);
assert.doesNotMatch(element("#watchlistCards").innerHTML, /<script>/);
assert.match(element("#watchlistUpdated").textContent, /1\/1/);
Object.assign(element("#backtestForm"), {strategy_id: {}, bias_mode: {querySelector: () => ({})}, start_date: {}, end_date: {}});
vm.runInContext('state.strategies = [{id:"strategy-one",spec:{filters:{history_days:60},factors:[{lookback:20}]}}]; state.dashboard.data = {first_completed_session:"2023-09-01",last_completed_session:"2026-09-25"}; openBacktest("strategy-one");', context);
const start = new Date(element("#backtestForm").start_date.value);
const end = new Date(element("#backtestForm").end_date.value);
assert.equal(element("#backtestForm").bias_mode.value, "exploratory");
assert.ok((end - start) / 86400000 <= 370, "the default backtest window must fit the API limit");
response = {equity:[{at:"2026-09-25T14:00:00Z", value:100},{at:"2026-09-25T14:05:00Z", value:110}], fills:[{ticker:"<img src=x>", side:"BUY", shares:1, price:10, fee:0.03, reason:"test", executed_at:"2026-09-25T14:00:00Z"}]};
(async () => {
 await vm.runInContext('openAccountHistory("account-one")', context);
 assert.match(element("#accountHistoryBody").innerHTML, /export\?kind=fills/);
 assert.match(element("#accountHistoryBody").innerHTML, /export\?kind=equity/);
 assert.match(element("#accountHistoryBody").innerHTML, /&lt;img src=x&gt;/);
 assert.doesNotMatch(element("#accountHistoryBody").innerHTML, /<img src=x>/);
 assert.equal(calls.at(-1)[0], "/api/accounts/account-one/history");
 response = [{id:"old", strategy_name:"old strategy", status:"completed", progress:100, start_date:"2026-01-01", end_date:"2026-03-01"}];
 vm.runInContext('state.backtests = [{id:"new",strategy_name:"new strategy",status:"failed",progress:0}];', context);
 await vm.runInContext('loadBacktestPage(50)', context);
 assert.equal(calls.at(-1)[0], "/api/backtests?limit=50&offset=50");
 assert.match(element("#backtestList").innerHTML, /old strategy/);
 assert.doesNotMatch(element("#backtestList").innerHTML, /new strategy/);
 assert.equal(vm.runInContext('state.backtests[0].id',context), "new");
})().catch(error => {console.error(error); process.exitCode = 1;});
'''
        completed = subprocess.run([shutil.which("node"), "-e", script, str(STATIC)], capture_output=True, text=True, timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
