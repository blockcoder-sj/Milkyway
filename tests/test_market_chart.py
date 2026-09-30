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
const ctx=vm.createContext({window:{},Intl,Number});vm.runInContext(fs.readFileSync(require('node:path').join(require('node:path').dirname(process.argv[1]),'format.js'),'utf8'),ctx);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
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

    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_default_candles_four_averages_warmup_and_crosshair(self):
        script=r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx=vm.createContext({window:{},Intl,Date,Number});vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
const api=ctx.window.MilkywayMarketChart;
assert.equal(api.DEFAULTS.style,'candle');assert.equal(api.DEFAULTS.volume,false);
assert.deepEqual(Array.from(api.MOVING_AVERAGES,ma=>ma.period),[5,20,60,120]);
for(const ma of api.MOVING_AVERAGES)assert.equal(api.DEFAULTS['ma'+ma.period],true);
const rows=Array.from({length:160},(_,i)=>({date:new Date(Date.UTC(2026,0,1+i)).toISOString().slice(0,10),open:100+i,high:102+i,low:99+i,close:101+i,volume:100+i}));
const handlers={},cursor={innerHTML:'',setAttribute(key,value){this[key]=value;}};
const svg={innerHTML:'',addEventListener(name,fn){handlers[name]=fn;},setAttribute(){},querySelector(){return cursor;},getBoundingClientRect(){return{left:0,top:0,width:700,height:400};}};
const tooltip={},legend={},chart=api.create(svg,tooltip,legend),options={start:rows[130].date,end:rows[149].date};
const result=chart.draw(rows,options);assert.equal(result.count,20);
assert.equal((svg.innerHTML.match(/data-candle/g)||[]).length,20);
assert.equal((svg.innerHTML.match(/data-ma=/g)||[]).length,4);assert(!svg.innerHTML.includes('data-volume'));
for(const ma of result.averages){
 const expected=rows.slice(130-ma.period+1,131).reduce((sum,row)=>sum+row.close,0)/ma.period;
 assert.equal(ma.values[0],expected);assert.equal(ma.values.length,20);
}
// The previous 120 values must participate in the y-axis rather than get clipped.
for(const match of svg.innerHTML.matchAll(/<polyline[^>]+points="([^"]+)"/g))for(const point of match[1].split(' ')){
 const y=Number(point.split(',')[1]);assert(y>=20&&y<=364);
}
assert(tooltip.innerHTML.includes(rows[149].date));assert(legend.innerHTML.includes('MA 120'));
assert(!legend.innerHTML.includes('style='));
const css=fs.readFileSync(require('node:path').join(require('node:path').dirname(process.argv[1]),'market-chart.css'),'utf8');
for(const ma of api.MOVING_AVERAGES)assert(css.includes('.market-ma[data-ma=\"'+ma.period+'\"]{color:'+ma.color+'}'));
handlers.pointermove({clientX:14+(610-14)/20*.5,clientY:150});
assert.equal(cursor.visibility,'visible');assert(cursor.innerHTML.includes(rows[130].date));assert(tooltip.innerHTML.includes(rows[130].date));
handlers.pointerleave();assert.equal(cursor.visibility,'hidden');assert(tooltip.innerHTML.includes(rows[149].date));
const changed=rows.map((row,i)=>i>149?{...row,close:100000,high:100001}:row);
assert.equal(chart.draw(changed,options).averages[3].values[19],result.averages[3].values[19]);
chart.draw(rows,{...options,ma5:false,ma20:false,ma60:false,ma120:false});assert.equal((svg.innerHTML.match(/data-ma=/g)||[]).length,0);
const short=chart.draw(rows.slice(0,4),{start:rows[0].date,end:rows[3].date});assert(short.averages.every(ma=>ma.values.every(v=>v===null)));
assert(!svg.innerHTML.includes('NaN'));assert(!svg.innerHTML.includes('Infinity'));
'''
        result=subprocess.run([shutil.which('node'),'-e',script,str(Path(__file__).resolve().parents[1]/'cloud_app/static/market-chart.js')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
