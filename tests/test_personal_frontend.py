"""Local UI contract and executable JavaScript behavior, without a browser."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "cloud_app" / "static"


class PersonalFrontendTests(unittest.TestCase):
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
        self.assertIn('hooks.api("/api/strategies"', personal)
        self.assertIn('factors: selectedFactors', personal)
        self.assertIn('spec.symbols = symbols', personal)
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
    innerHTML: "", textContent: "", className: "", disabled: false, open: false, style: {},
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
