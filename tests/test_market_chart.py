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
const svg={innerHTML:'',addEventListener(){},setAttribute(key,value){this[key]=value;},getBoundingClientRect(){return {left:0,width:520,height:340}}},tooltip={};
const chart=api.create(svg,tooltip);
for(const style of ['line','candle'])for(const scale of ['linear','log']){
const result=chart.draw(rows,{start:'2026-09-01',end:'2026-09-30',interval:'day',style,scale,volume:true,ma20:true,ma60:true});
assert.equal(result.count,3);assert(!svg.innerHTML.includes('NaN'));assert(!svg.innerHTML.includes('Infinity'));assert(svg.innerHTML.includes('<text'));
}
assert.equal(svg.viewBox,'0 0 520 340');
const one=chart.draw([rows[0]],{start:'2026-09-01',end:'2026-09-30',interval:'day',style:'line'});
assert(svg.innerHTML.includes('<circle'));assert.equal(one.change,null);
const flat={...rows[0],open:100,high:100,low:100,close:100};
chart.draw([flat, {...flat,date:'2026-09-02'}],{start:'2026-09-01',end:'2026-09-30',interval:'day'});
assert(!svg.innerHTML.includes('NaN'));assert(!svg.innerHTML.includes('Infinity'));
const partial=api.validBars([{...rows[0],high:1},rows[1]]);
assert.equal(partial.length,2);assert.equal(partial[0].open,null);assert.equal(partial[0].close,105);
assert.equal(api.aggregate(partial,'week')[0].open,null);
assert.equal(api.aggregate(partial,'week')[0].close,110);
assert.equal(api.average(partial,2)[1],107.5);
chart.draw(partial,{start:'2026-09-01',end:'2026-09-30',interval:'day',style:'candle'});
assert(svg.innerHTML.includes('<circle'));assert(!svg.innerHTML.includes('NaN'));
assert.equal(chart.draw(rows,{start:'2026-01-01',end:'2026-01-02'}),null);
'''
        result=subprocess.run([shutil.which('node'),'-e',script,str(Path(__file__).resolve().parents[1]/'cloud_app/static/market-chart.js')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_calculation_explanations_escape_inputs_and_preserve_expansion(self):
        script=r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx=vm.createContext({window:{},Intl,Number});vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const api=ctx.window.MilkywayMarketMethods;
const html=api.quote({id:'<img>',source:'<script>',value:110,previous_close:100});
assert(html.includes('&lt;script&gt;'));assert(!html.includes('<script>'));assert(html.includes('110 ÷ 100'));
const missing=api.quote({id:'missing',value:100,previous_close:null});
assert(missing.includes('계산하지 않습니다'));assert(!missing.includes('NaN'));assert(!missing.includes('Infinity'));
assert(api.company({symbol:'AAA',market_cap:100},[{market_cap:100},{market_cap:300}]).includes('100 ÷ 400'));
assert(api.chart({quality:{received:4,outside_range:1,invalid_close:1,close_only:1,duplicates:0,accepted:2}}).includes('OHLC 불완전 1개'));
assert(api.chart({}).includes('다음 갱신'));
const details=[{dataset:{methodId:'kept'},open:false},{dataset:{methodId:'closed'},open:false}];
const target={innerHTML:'',querySelectorAll(selector){return selector.includes('[open]')?[{dataset:{methodId:'kept'}}]:details;}};
api.replace(target,'new content');assert.equal(target.innerHTML,'new content');assert.equal(details[0].open,true);assert.equal(details[1].open,false);
'''
        result=subprocess.run([shutil.which('node'),'-e',script,str(Path(__file__).resolve().parents[1]/'cloud_app/static/market-methods.js')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
