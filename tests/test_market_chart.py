from pathlib import Path
import shutil
import subprocess
import unittest


class MarketChartTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_aggregation_metrics_and_bounded_chart_drawing(self):
        script=r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx=vm.createContext({window:{},Intl,Date,Number});vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const api=ctx.window.MilkywayMarketChart;
const rows=[{date:'2026-09-01',open:100,high:110,low:90,close:105,volume:10},{date:'2026-09-02',open:105,high:120,low:100,close:110,volume:20},{date:'2026-09-08',open:110,high:115,low:80,close:90,volume:30}];
assert.equal(api.aggregate(rows,'week').length,2);const monthly=api.aggregate(rows,'month')[0];
assert.equal(monthly.open,100);assert.equal(monthly.high,120);assert.equal(monthly.low,80);assert.equal(monthly.close,90);assert.equal(monthly.volume,60);
assert(Math.abs(api.metrics(rows).change-(90/105-1)*100)<1e-10);
assert(Math.abs(api.metrics(rows).drawdown-(90/110-1)*100)<1e-10);
assert.equal(api.average(rows,2)[0],null);assert.equal(api.average(rows,2)[1],107.5);
assert.equal(api.validBars([...rows,null,{...rows[0],date:'2026-99-01'},{...rows[0],date:'2026-02-30'},{...rows[0],date:'<script>',close:NaN}]).length,3);
const svg={innerHTML:'',addEventListener(){},getBoundingClientRect(){return {left:0,width:960}}},tooltip={};
const chart=api.create(svg,tooltip);
for(const style of ['line','candle'])for(const scale of ['linear','log']){
const result=chart.draw(rows,{start:'2026-09-01',end:'2026-09-30',interval:'day',style,scale,volume:true,ma20:true,ma60:true});
assert.equal(result.count,3);assert(!svg.innerHTML.includes('NaN'));assert(!svg.innerHTML.includes('Infinity'));assert(svg.innerHTML.includes('<text'));
}
assert.equal(chart.draw(rows,{start:'2026-01-01',end:'2026-01-02'}),null);
'''
        result=subprocess.run([shutil.which('node'),'-e',script,str(Path(__file__).resolve().parents[1]/'cloud_app/static/market-chart.js')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
