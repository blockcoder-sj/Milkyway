"""Exact annual tables for eight issuers with different entity/accounting scopes."""
from decimal import Decimal

IDENTITIES = {'APC':2080921,'BDCO':793306,'IEP':813762,'INVX':1042893,
              'NUAI':2028336,'RSRV':83350,'SUNC':2089661,'TBN':1997652}
DOCUMENTS = {}
PERIODS = {}
COORDINATES, LABELS = {}, {}
CONTRACT = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
INCLUDING = 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
REVENUES = 'us-gaap:Revenues'
PRODUCT = 'srt:ProductOrServiceAxis'
SEGMENT = 'us-gaap:StatementBusinessSegmentsAxis'
GEO = 'srt:StatementGeographicalAxis'
MANUAL_APC = {
 'reported:Fuel':('product','제3자 연료',3203273000),
 'reported:RelatedFuel':('product','관계사 연료',2302547000),
 'reported:Other':('product','기타 순매출',63063000),
 'reported:RelatedOther':('product','관계사 기타 순매출',12381000),
 'reported:Wholesale':('segment','wholesale · 외부',2753108000),
 'reported:Fleet':('segment','fleet fueling · 외부',483779000),
 'reported:GPMP':('segment','GPMP · 외부',2306808000),
 'reported:AllOther':('segment','All Other · 외부',37569000),
}

# Metadata comes from the hash-verified original receipt, not from a ticker guess.
from .company_energy_sources import REPORTS
for _s,_c in IDENTITIES.items():
    DOCUMENTS[_s,_c] = REPORTS[_s]['annual']['url']
    PERIODS[_s,_c] = ('2025-07-01','2026-06-30') if _s=='TBN' else ('2025-01-01','2025-12-31')

def _members(symbol,axis,group,mapping,qualifiers=()):
    cik=IDENTITIES[symbol]
    for member,label in mapping.items():
        COORDINATES[symbol,cik,frozenset([(axis,member),*qualifiers])]=group,member
        LABELS[symbol,cik,member]=label

_members('BDCO',SEGMENT,'segment',{'bdco:RefineryOperationsMember':'정제 · 외부 매출','bdco:TollingAndTerminalingMember':'tolling·저장 · 외부 매출'})
_members('IEP',SEGMENT,'segment',{'iep:InvestmentSegmentMember':'투자 · 순손익 포함','iep:EnergySegmentMember':'에너지','iep:AutomotiveSegmentMember':'자동차','iep:FoodPackagingSegmentMember':'식품 포장','iep:RealEstateSegmentMember':'부동산','iep:HomeFashionSegmentMember':'홈 패션','iep:PharmaSegmentMember':'제약','iep:HoldingCompanyMember':'holding·기타'})
_members('INVX',PRODUCT,'product',{'us-gaap:ProductMember':'제품','us-gaap:ServiceMember':'서비스','invx:LeasingMember':'임대'})
_members('INVX',GEO,'segment',{'invx:USAndCanadianMarketsNAMMember':'미국·Canada 시장','invx:InternationalAndOffshoreMember':'국제·해양 시장'})
_members('INVX',GEO,'geography',{'country:US':'미국 육상','invx:UnitedStatesOffshoreMember':'미국 해양','country:CA':'캐나다','country:SA':'사우디아라비아','country:BR':'브라질','country:MX':'멕시코','country:AR':'아르헨티나','invx:OtherMEAPMember':'기타 중동·유럽·아시아태평양','invx:EastAndCentralAfricaMember':'동·중부 아프리카','srt:LatinAmericaMember':'기타 중남미'})
_members('NUAI',PRODUCT,'product',{'nehc:NaturalGasNetMember':'천연가스 · 집하·처리비 차감 후','srt:NaturalGasLiquidsReservesMember':'NGL'})
_members('RSRV',PRODUCT,'product',{'us-gaap:OilAndCondensateMember':'원유·콘덴세이트','us-gaap:NaturalGasProductionMember':'천연가스','rsrv:MiscellaneousOilAndGasSalesMember':'기타 원유·가스 판매','rsrv:LeaseBonusesAndOtherMember':'광물권 lease bonus·기타'})
_members('SUNC',PRODUCT,'revenue_type',{'sunc:SalesRevenueMember':'연료·상품 판매','sunc:ServiceRevenueMember':'서비스','sunc:LeaseRevenueMember':'임대'})
_members('SUNC',GEO,'geography',{'country:US':'미국','country:CA':'캐나다','sunc:ForeignMember':'미국·캐나다 외'})
_members('SUNC',SEGMENT,'segment',{'sunc:FuelDistributionMember':'연료 유통 · 외부','sunc:PipelineSystemsMember':'파이프라인 · 외부','sunc:TerminalsMember':'터미널 · 외부','sunc:RefineryMember':'정유 · 외부'},[('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember'),('us-gaap:RelatedPartyTransactionsByRelatedPartyAxis','sunc:ExternalRevenueMember')])
_members('SUNC',PRODUCT,'product',{'srt:FuelMember':'연료 판매','sunc:NonFuelMember':'비연료 판매','sunc:LeaseIncomeMember':'임대','sunc:PipelineThroughputMember':'파이프라인 서비스','sunc:TerminalThroughputMember':'터미널 서비스','sunc:RefineryMember':'정유 서비스','sunc:OtherMember':'기타'},[('us-gaap:TransactionTypeAxis','sunc:ExternalRevenueMember')])

def reviewed(row,symbol,cik):
    return ((row['start'],row['end'])==PERIODS.get((symbol,cik))
            and row['source']['url'].split('#')[0]==DOCUMENTS.get((symbol,cik)))

def dimensions(pairs,symbol,cik):
    return None if len(set(pairs))!=len(pairs) else COORDINATES.get((symbol,cik,frozenset(pairs)))

def metric_allowed(tag,group,start,end,origin,symbol,cik):
    if not reviewed(dict(start=start,end=end,source=origin),symbol,cik):return True
    if symbol=='APC':return tag=='reported:CombinedRevenue'
    if symbol in ('IEP','SUNC'):return tag==REVENUES
    if symbol=='NUAI':return tag==INCLUDING
    if symbol=='RSRV':return tag in (INCLUDING,'us-gaap:RegulatedOperatingRevenueGas')
    return tag==CONTRACT

def canonical(rows,symbol,cik):
    allowed={(g,m) for (s,c,_),(g,m) in COORDINATES.items() if (s,c)==(symbol,cik)}
    if (symbol,cik)==('APC',2080921):
        allowed.update((group,member) for member,(group,_,_) in MANUAL_APC.items())
    selected=[r for r in rows if not reviewed(r,symbol,cik) or (
        r['unit']=='USD' and (r['group'],r['member']) in allowed
        and metric_allowed(r['metric'],r['group'],r['start'],r['end'],r['source'],symbol,cik))]
    values={}
    for r in selected:
        if reviewed(r,symbol,cik):
            key=tuple(r[k] for k in ('group','member','start','end','unit','metric'))
            values.setdefault(key,set()).add(Decimal(str(r['value'])))
    kept,seen=[],set()
    for r in selected:
        if reviewed(r,symbol,cik):
            key=tuple(r[k] for k in ('group','member','start','end','unit','metric'))
            if key in seen or len(values[key])!=1:continue
            seen.add(key)
        kept.append(r)
    return kept

def presentation_group(row,symbol,cik):
    if reviewed(row,symbol,cik):
        groups={g for (s,c,_),(g,m) in COORDINATES.items() if (s,c,m)==(symbol,cik,row['member'])}
        if len(groups)==1:return groups.pop()
    return row['group']

def extra_metrics(origin,symbol,cik,period_end):
    if (symbol=='RSRV' and cik==83350 and period_end is not None
        and period_end.isoformat()=='2025-12-31' and origin['url'].split('#')[0]==DOCUMENTS.get((symbol,cik))):
        return ('us-gaap:RegulatedOperatingRevenueGas',)
    return ()

def statement_rows(rows,clean,anchors,origin,symbol,cik,period_end):
    if not extra_metrics(origin,symbol,cik,period_end):return rows
    tag='us-gaap:RegulatedOperatingRevenueGas'
    key=tag,'USD','2025-01-01','2025-12-31','product','rsrv:LeaseBonusesAndOtherMember'
    if key in clean:
        rows.append(dict(group='product',member=key[-1],label='광물권 lease bonus·기타',
            value=float(clean[key]),unit='USD',start=key[2],end=key[3],total=None,metric=tag,
            parent=None,includes_intersegment=False,
            source={**origin,'url':origin['url']+('#'+anchors[key] if key in anchors else '')}))
    return rows

def annotate(rows,symbol,cik):
    for row in rows:
        if not reviewed(row,symbol,cik):continue
        row['label']=LABELS.get((symbol,cik,row['member']),row['label'])
        row['parent']=None
        if symbol=='RSRV':
            row['total']=None
            row['share_exclusion']='상품 계약 매출16,699,954 USD와 lease bonus·기타741,207 USD는 서로 다른 원문 회계 지표입니다. 연결17,441,161 USD의 단일 지표 구성비로 계산하지 않습니다.'
        if symbol=='IEP':
            row['total']=None
            row['share_exclusion']='7개 보고 부문과 holding의 전체 매출9,658백만 USD입니다. 투자 순손익과 영업 매출이 함께 있어 순수 상품 매출 시장비중으로 계산하지 않습니다.'
    return rows
