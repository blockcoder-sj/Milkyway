"""Manually checked non-inline trust tables; these are not fabricated XBRL facts.

Amounts, labels and table anchors were read from the archived original 10-Ks.
Keep cash/distributable-income accounting separate from corporate GAAP earnings.
"""
from .company_energy_sources import report

TRUSTS = ('CRT','NRT','PBT','SBR')
PERIODS = {symbol:('2025-01-01','2025-12-31') for symbol in TRUSTS}
PERIODS['NRT'] = '2024-11-01','2025-10-31'


def table_source(symbol,anchor,label):
    origin=report(symbol)
    return {**origin,'label':'SEC 연차 원문 표 · '+label,'url':origin['url']+'#'+anchor}


def _financials(symbol,balance,income,rows):
    first,last=PERIODS[symbol]
    return [dict(label=label,value=value,unit='USD',
        period=last if point else first+' ~ '+last,
        source=table_source(symbol,balance if point else income,original))
        for label,value,point,original in rows]


FINANCIALS = {
 'CRT':_financials('CRT','stmt_of_assets_liabilities_and_trust_co','statements_of_distributable_income',[
  ('순이익 권리 수입 · NPI',5738240,False,'Net profits income'),
  ('수입 합계 · 이자 포함',5787922,False,'Total income'),
  ('관리비',847078,False,'Administration expense'),
  ('분배 가능 수입',4490844,False,'Distributable income'),
  ('현금·단기 투자',2133676,True,'Cash and short-term investments'),
  ('자산 총계 · 신탁 장부',4296650,True,'Total assets'),
  ('신탁 원본 · 장부금액',2158420,True,'Trust corpus')]),
 'NRT':_financials('NRT','za5f095eaf64240c3aba6560641c403db','zb51f4ce6a8874cecb4b66a599292fae3',[
  ('로열티 수취액',8650094,False,'Royalties received'),
  ('수입 합계 · 이자 포함',8734568,False,'Total income'),
  ('순이익 · 신탁 기준',7938920,False,'Net income'),
  ('현금·현금성 자산',4785156,True,'Cash and cash equivalents'),
  ('자산 총계 · 신탁 장부',4785157,True,'Total assets'),
  ('미지급 분배금',2849083,True,'Distributions payable'),
  ('미분배 수익 잔액',1936073,True,'Undistributed earnings')]),
 'PBT':_financials('PBT','statements_of_assets_liabilities_and','statements_of_distributable_income',[
  ('로열티 수입 · 합의금 포함',16055300,False,'Royalty income'),
  ('수입 합계 · 이자 포함',16128061,False,'Total income'),
  ('관리비',1827899,False,'General and administrative'),
  ('분배 가능 수입',14300162,False,'Distributable income'),
  ('현금·단기 투자',1715167,True,'Cash and short-term investments'),
  ('자산 총계 · 신탁 장부',1877733,True,'Total assets'),
  ('부채 총계 · 준비금 포함',1715167,True,'Total liabilities')]),
 'SBR':_financials('SBR','statements_of_assets_liabilities_and_tru','statements_of_distributable_income',[
  ('로열티 수입',77061857,False,'Royalty income'),
  ('수입 합계 · 이자 포함',77533692,False,'Total income'),
  ('관리비',4090067,False,'General and administrative expenses'),
  ('분배 가능 수입',73443625,False,'Distributable income'),
  ('현금·단기 투자',7574257,True,'Cash and short-term investments'),
  ('자산 총계 · 신탁 장부',7643865,True,'Total assets'),
  ('부채 총계',796286,True,'Total liabilities')]),
}


def _revenue(symbol,group,member,label,value,anchor,metric,explanation):
    first,last=PERIODS[symbol]
    return dict(group=group,member='table:'+member,label=label,value=value,unit='USD',
        start=first,end=last,total=None,metric='table:'+metric,parent=None,
        includes_intersegment=False,share_exclusion=explanation,
        source=table_source(symbol,anchor,'로열티·권리 수입 · 수동 대조'))


REVENUE = {
 'CRT':[_revenue('CRT','product','net_profit_income','순이익 권리 수입 · NPI',5738240,
  'statements_of_distributable_income','net_profit_income',
  '원문 비인라인 표에서 대조한 신탁 수입입니다. 기초 유정의 총판매 14,589,185 USD나 배분 전 생산량과 같지 않습니다. 이자 49,682·관리비·준비금은 따로 확인합니다.')],
 'PBT':[_revenue('PBT','product','royalty_income','로열티 수입 · 합의금 포함',16055300,
  'statements_of_distributable_income','royalty_income',
  '원문 비인라인 표를 대조했습니다. Texas Royalties 11,555,301 USD·합의금 수령 4,500,000의 합계는 손익 표 로열티 16,055,300과 1 USD 차이가 있습니다. 차이를 보정하지 않으며 Waddell 운영 수입 0과 합의금은 다릅니다.')],
 'SBR':[_revenue('SBR','product','royalty_income','로열티 수입',77061857,
  'statements_of_distributable_income','royalty_income',
  '원문 비인라인 표를 대조한 로열티 수입입니다. 이자 471,835 USD·관리비 4,090,067·분배 가능 수입 73,443,625와 실제 지급액 75,291,967은 다른 항목입니다.')],
 'NRT':[],
}
for _group,_values in [
 ('product',[('gas','가스',8146320),('sulfur','황',428513),('oil','원유',75071)]),
 ('geography',[('western_oldenburg','Western Oldenburg',6686731),
               ('eastern_oldenburg','Eastern Oldenburg',1963173),('non_oldenburg','Oldenburg 외',0)]),
 ('revenue_type',[('mobil_erdgas','Mobil Erdgas 약정',5836999),('beb','BEB · OEG 약정',2812905)])]:
    for _member,_label,_value in _values:
        REVENUE['NRT'].append(_revenue('NRT',_group,_member,_label,_value,
            'z72410ae4bcc047fba4fc2616e2724258','royalty_income',
            'FY2025는 2024-11-01~2025-10-31입니다. 사업 표의 제품·지역·운영사별 합계는 각각 8,649,904 USD로 수입 표 수취액 8,650,094보다 190 작습니다. 공시 표의 차이를 임의 조정하거나 100% 구성비로 표시하지 않습니다.'))
