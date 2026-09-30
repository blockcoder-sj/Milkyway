"""Executable market rendering checks without a browser or external feeds."""
from pathlib import Path
import shutil
import subprocess
import unittest


class MarketFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed for UI checks")
    def test_country_currency_sorting_missing_values_and_escaping(self):
        script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const elements=new Map();
function element(id){
 if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',className:'',classList:{remove(){}}});
 return elements.get(id);
}
const ctx=vm.createContext({window:{},document:{querySelector:element},Intl,Date,Number});
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const row={id:'one',label:'<img src=x onerror=alert(1)>',symbol:'^GSPC',group:'indices',market:'us',
 unit:'pt',description:'<script>bad</script>',value:100,previous_close:100,change:0,change_pct:0,
 status:'delayed',observed_at:'2026-09-30T00:00:00Z',fetched_at:'2026-09-30T00:01:00Z',sparkline:[100,101,100],
 source_url:'javascript:alert(1)'};
const items=[row,{...row,id:'kr',label:'KOSPI',market:'kr'},
 {...row,id:'fx',label:'EUR/USD',group:'fx',market:'global',unit:'USD',value:1.1327,change:-0.0012},
 {...row,id:'top',label:'Top Sector',group:'sectors',change_pct:3},
 {...row,id:'bottom',label:'Bottom Sector',group:'sectors',change_pct:-2},
 {...row,id:'missing',label:'Missing Sector',group:'sectors',value:null,change_pct:null,status:'unavailable'},
 {...row,id:'krsector',label:'Korean Sector',market:'kr',group:'sectors'}];
const overview={items,available_count:6,total_count:7,note:'display feed'};
ctx.window.MilkywayMarket.renderMarket(overview,'us');
let html=element('#marketCards').innerHTML;
assert(html.includes('&lt;img'));assert(!html.includes('<img'));assert(!html.includes('<script>'));
assert(!html.includes('javascript:'));assert(html.includes('0%'));assert(!html.includes('KOSPI'));
assert(element('#marketFx').innerHTML.includes('EUR/USD'));
assert(element('#marketFx').innerHTML.includes('1.1327'));
assert(element('#marketFx').innerHTML.includes('-0.0012 USD'));
ctx.window.MilkywayMarket.renderMarket(overview,'kr');
assert(element('#marketCards').innerHTML.includes('KOSPI'));
ctx.window.MilkywayMarket.renderSectors(overview,'us','desc');
html=element('#sectorHeatmap').innerHTML;
assert(html.indexOf('Top Sector')<html.indexOf('Bottom Sector'));
assert(html.indexOf('Bottom Sector')<html.indexOf('Missing Sector'));
assert(!html.includes('Korean Sector'));assert(!html.includes('NaN'));assert(!html.includes('Infinity'));
assert(html.includes('수신 실패'));
ctx.window.MilkywayMarket.renderSectors(overview,'us','asc');
html=element('#sectorHeatmap').innerHTML;
assert(html.indexOf('Bottom Sector')<html.indexOf('Top Sector'));
ctx.window.MilkywayMarket.renderSectors(overview,'kr','name');
assert(element('#sectorHeatmap').innerHTML.includes('Korean Sector'));
assert(!element('#sectorHeatmap').innerHTML.includes('Top Sector'));
assert(element('#heatmapMethod').textContent.includes('8개'));
'''
        source = Path(__file__).resolve().parents[1] / "cloud_app/static/market.js"
        result = subprocess.run([shutil.which("node"), "-e", script, str(source)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
