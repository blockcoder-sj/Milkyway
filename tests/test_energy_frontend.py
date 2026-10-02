"""Dependency-free checks for the energy guide browser renderer."""
from pathlib import Path
import shutil
import subprocess
import unittest


class EnergyFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required for frontend checks')
    def test_frontend_escapes_preserves_noop_and_navigates_to_folded_sources(self):
        script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let writes=0,html='',handler;
const panel={hidden:false,querySelectorAll:()=>[],addEventListener:(type,fn)=>handler=fn,
 get innerHTML(){return html;},set innerHTML(value){html=value;writes++;}};
const disclosure={open:false};let scrolled=0;
const source={closest:()=>disclosure,scrollIntoView:()=>scrolled++};
const jump={hidden:false};
const document={getElementById:id=>({detailIndustrySection:panel,detailIndustryJump:jump,'energy-source-gics':source})[id]};
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context=vm.createContext({document,window:{MilkywayResearchView:{escape}},Set,JSON});
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),context);
const view=context.window.MilkywayEnergyGuide;
const data={title:'<img src=x>',scope:'Scope',checked_at:'2026-10-02',classification_note:'Classification',
 industries:[{code:'10101010',name:'Drilling',label:'시추',body:'Test',source_ids:['gics','bad" onclick="alert(1)']}],
 sections:[{id:'chains',title:'Flow',intro:'Structural only',entries:[{title:'<script>',body:'<svg onload=x>',
 source_ids:['gics'],steps:['<img>','Other'],formula:'<b>',caveat:'<i>'}]}]};
view.initialize();view.render(data);
assert.equal(panel.hidden,false);assert.equal(jump.hidden,false);
assert(html.includes('&lt;img'));assert(!html.includes('<img'));assert(!html.includes('<script>'));
assert(!html.includes('onclick'));assert(html.includes('<ol'));assert(!html.includes('href="https:'));
assert(html.includes('energy-source-gics'));const count=writes;view.render(data);assert.equal(writes,count);
let prevented=0;
const anchor={getAttribute:()=> '#energy-source-gics',hasAttribute:()=>true};
const event={target:{closest:()=>anchor},button:0,preventDefault:()=>prevented++};
handler(event);assert.equal(disclosure.open,true);assert.equal(scrolled,1);assert.equal(prevented,1);
handler({...event,ctrlKey:true});assert.equal(scrolled,1);
view.render(null);assert.equal(panel.hidden,true);assert.equal(jump.hidden,true);assert.equal(html,'');
view.render(data);assert(html.includes('Flow'));
"""
        file = Path(__file__).resolve().parents[1]/'cloud_app/static/energy-guide.js'
        result = subprocess.run([shutil.which('node'), '-e', script, str(file)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
