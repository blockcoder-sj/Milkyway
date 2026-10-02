"""Executable directory paging/filtering and escaped provenance rendering."""
from pathlib import Path
import shutil
import subprocess
import unittest


class EnergyDirectoryFrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required for frontend checks')
    def test_research_groups_page_and_escape_without_changing_classification(self):
        script = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements=new Map(),handlers={};
function element(id){if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',prepend(){},
 addEventListener:(kind,fn)=>handlers[id+'|'+kind]=fn});return elements.get(id);}
const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context=vm.createContext({window:{MilkywayResearchView:{escape},MilkywayMarketMethods:{company:()=>''}},
 document:{querySelector:element,createElement:()=>({})},Intl,Date,URL,Number,Set,Map});
for(const name of ['format.js','list-paging.js','market-directory.js'])
 vm.runInContext(fs.readFileSync(process.argv[1]+'/'+name,'utf8'),context);
const rows=Array.from({length:10},(_,i)=>({symbol:'TEST'+i,name:'Company '+i,market_cap:null,currency:'USD',
 source:'SEC',url:'https://www.sec.gov/report/'+i,displayed_share_pct:null,
 directory_basis:'발행기업 조사 · GICS 미확인',directory_group:i===9?'<svg onload=x>':'압축·분산 발전'}));
const payload={id:'us_10',group:'sectors',context:{sources:[]},companies:{rows},news:{rows:[]},
 issuer_directory:{research_issuers:187,checked_at:'2026-10-03',method:'Collection is not completion',
 identity_source:{label:'Identity',url:'https://www.sec.gov/files/company_tickers_exchange.json'}}};
const view=context.window.MilkywayMarketDirectory;view.initialize();view.render(payload);
assert(element('#detailCompanyRows').innerHTML.includes('Company 0'));
assert(!element('#detailCompanyRows').innerHTML.includes('Company 8'));
assert(element('#detailCompanies').innerHTML.includes('사업별 탐색'));
assert(element('#detailCompanies').innerHTML.includes('&lt;svg'));assert(!element('#detailCompanies').innerHTML.includes('<svg'));
assert(element('#detailCompanyRows').innerHTML.includes('GICS 미확인'));
assert(!element('#detailCompanyRows').innerHTML.includes('공식 구성 공시 대조'));
handlers['#detailCompanies|click']({target:{closest:()=>({dataset:{companyPage:'2'}})}});
assert(element('#detailCompanyRows').innerHTML.includes('Company 9'));assert(!element('#detailCompanyRows').innerHTML.includes('<svg'));
handlers['#detailCompanies|change']({target:{id:'detailCompanyGroup',value:'압축·분산 발전'}});
assert(element('#detailCompanyRows').innerHTML.includes('Company 0'));
handlers['#detailCompanies|input']({target:{id:'detailCompanySearch',value:'TEST8'}});
assert(element('#detailCompanyRows').innerHTML.includes('Company 8'));assert(!element('#detailCompanyRows').innerHTML.includes('Company 0'));
assert(element('#detailSources').innerHTML.includes('company_tickers_exchange.json'));
'''
        directory = Path(__file__).resolve().parents[1]/'cloud_app/static'
        result = subprocess.run([shutil.which('node'), '-e', script, str(directory)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
