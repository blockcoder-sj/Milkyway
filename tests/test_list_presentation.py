"""Shared formatting, input round trips and stable bounded page selection."""
from pathlib import Path
import shutil,subprocess,unittest

class ListPresentationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_grouped_input_and_pagination_boundaries(self):
        script=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');const ctx=vm.createContext({window:{},Intl});
for(const file of ['format.js','list-paging.js'])vm.runInContext(fs.readFileSync(process.argv[1]+'/'+file,'utf8'),ctx);
const f=ctx.window.MilkywayFormat,p=ctx.window.MilkywayPaging;
assert.equal(f.escapeHtml(`<a x="'">&`), '&lt;a x=&quot;&#39;&quot;&gt;&amp;');
assert.equal(f.escapeHtml(null), '');assert.equal(f.money(1234.5), '$1,235');
assert.equal(f.pct(-1.2), '-1.20%');assert.equal(f.pct(0), '+0.00%');
assert.equal(f.shortTime(null), '—');assert.equal(f.shortTime('invalid'), '—');
assert.notEqual(f.shortTime('2026-11-05T16:00:00Z'), '—');

assert.equal(f.number(1234567.89), '1,234,567.89');assert.equal(f.parse(f.number(1234567.89)),1234567.89);
assert.equal(f.parse('-1,234.5'),-1234.5);assert.equal(f.parse('.5'),.5);assert.equal(f.number(null),'—');
for(const value of ['1,00','1,234,56','','NaN','Infinity','123<script>','1e999'])assert.throws(()=>f.parse(value));
const rows=Array.from({length:35},(_,i)=>i);assert.equal(p.slice(rows,2).rows.join(','),'8,9,10,11,12,13,14,15');
assert.equal(p.slice(rows,99).page,5);assert.equal(p.slice([],99).page,1);assert.equal(p.slice(rows,0).page,1);
assert(!p.controls(p.slice(rows,5),'data-news-page').includes('data-news-page="6"'));
assert(p.controls(p.slice(rows,3),'data-news-page').includes('aria-current="page"'));
assert.throws(()=>p.controls(p.slice(rows,2),'onclick=evil'));
'''
        result=subprocess.run([shutil.which('node'),'-e',script,str(Path(__file__).resolve().parents[1]/'cloud_app/static')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
