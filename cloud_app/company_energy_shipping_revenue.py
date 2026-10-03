"""Reviewed maritime revenue bases, bound to the actual issuer and annual filing.

Keep lease, freight, pool distributions and equity-method terminal income apart.
An undimensioned statement line keeps its original metric as its display key;
it is never presented as an XBRL dimension invented by the application.
"""
from decimal import Decimal

DOCUMENTS = {
    ('DHT',1331284):'https://www.sec.gov/Archives/edgar/data/1331284/000114036126010407/ef20059925_20f.htm',
    ('FRO',913290):'https://www.sec.gov/Archives/edgar/data/913290/000162828026021774/fro-20251231.htm',
    ('GLNG',1207179):'https://www.sec.gov/Archives/edgar/data/1207179/000162828026021198/glng-20251231.htm',
    ('FLNG',1772253):'https://www.sec.gov/Archives/edgar/data/1772253/000162828026012574/flng-20251231.htm',
    ('LPG',1596993):'https://www.sec.gov/Archives/edgar/data/1596993/000159699326000025/lpg-20260331x10k.htm',
    ('INSW',1679049):'https://www.sec.gov/Archives/edgar/data/1679049/000110465926020113/insw-20251231x10k.htm',
    ('NAT',1000177):'https://www.sec.gov/Archives/edgar/data/1000177/000114036126017809/ef20071320_20f.htm',
    ('NVGS',1581804):'https://www.sec.gov/Archives/edgar/data/1581804/000162828026017320/nvgs-20251231.htm',
    ('STNG',1483934):'https://www.sec.gov/Archives/edgar/data/1483934/000148393426000021/stng-20251231.htm',
    ('TEN',1166663):'https://www.sec.gov/Archives/edgar/data/1166663/000119312526144027/d49235d20f.htm',
    ('TK',911971):'https://www.sec.gov/Archives/edgar/data/911971/000091197126000015/tk-20251231.htm',
    ('TNK',1419945):'https://www.sec.gov/Archives/edgar/data/1419945/000141994526000007/tnk-20251231.htm',
    ('TORO',1941131):'https://www.sec.gov/Archives/edgar/data/1941131/000114036126014706/ef20060830_20f.htm',
    ('IMPP',1876581):'https://www.sec.gov/Archives/edgar/data/1876581/000119312526192203/d60380d20f.htm',
    ('PXS',1640043):'https://www.sec.gov/Archives/edgar/data/1640043/000149315226014641/form20-f.htm',
    ('KNOP',1564180):'https://www.sec.gov/Archives/edgar/data/1564180/000110465926044664/knop-20251231x20f.htm',
}
PERIODS = {key:('2025-01-01','2025-12-31') for key in DOCUMENTS}
PERIODS['LPG',1596993] = '2025-04-01','2026-03-31'
CONTRACT = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
CONTRACT_TAX = 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
LEASE = 'us-gaap:OperatingLeaseLeaseIncome'
PRODUCT = 'srt:ProductOrServiceAxis'
SEGMENT = 'us-gaap:StatementBusinessSegmentsAxis'
OPERATING = ('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember')
COORDINATES, LABELS = {}, {}


def _members(symbol,cik,axis,group,values,qualifiers=()):
    for member,label in values.items():
        pairs = [(axis,member),*qualifiers]
        COORDINATES[symbol,cik,frozenset(pairs)] = group,member
        LABELS[symbol,cik,member] = label


_members('DHT',1331284,'ifrs-full:ProductsAndServicesAxis','product',{
    'dht:TimeCharterRevenuesMember':'기간 용선 · 운송 수입',
    'dht:VoyageCharterRevenuesMember':'항해 용선 · 운송 수입'})
_members('FRO',913290,PRODUCT,'product',{
    'fro:VoyageCharterMember':'항해 용선 · 서비스 수입',
    'fro:TimeCharterMember':'기간 용선 · 서비스 수입',
    'fro:AdministrativeIncomeMember':'관리 서비스 수입'})
_members('GLNG',1207179,PRODUCT,'product',{
    'glng:LiquefactionServicesRevenueMember':'액화 서비스',
    'glng:SalesTypeLeaseRevenueMember':'판매형 리스',
    'glng:VesselManagementFeesAndOtherRevenuesMember':'선박 관리·기타',
    'glng:TimeAndVoyageCharterRevenueMember':'기간·항해 용선'})
_members('GLNG',1207179,SEGMENT,'segment',{
    'glng:FLNGMember':'FLNG','us-gaap:CorporateAndOtherMember':'본사·기타'},[OPERATING])
_members('GLNG',1207179,'srt:StatementGeographicalAxis','geography',{
    'country:CM':'Cameroon · FLNG만',
    'glng:MauritaniaAndSenegalMember':'Mauritania·Senegal · FLNG만'},
    [('glng:VesselNameAxis','glng:FLNGHilliAndFLNGGimiMember')])
_members('INSW',1679049,PRODUCT,'product',{
    'insw:PoolRevenueLeasesMember':'상업 운항 풀 · 리스 포함',
    'insw:TimeAndBareboatCharterLeasesMember':'기간·나용선 · 리스 포함',
    'insw:VoyageCharterLeasesMember':'항해 용선 · 리스 포함'})
_members('INSW',1679049,SEGMENT,'segment',{
    'insw:InternationalCrudeTankersSegmentMember':'원유 운송',
    'insw:InternationalProductCarriersSegmentMember':'석유 제품 운송'})
_members('NAT',1000177,PRODUCT,'product',{
    'nat:SpotCharterMember':'현물 항해 용선','nat:TimeCharterMember':'기간 용선'})
_members('NVGS',1581804,PRODUCT,'product',{
    'nvgs:TimeChartersMember':'기간 용선 · 고객 계약',
    'nvgs:VoyageChartersMember':'항해 용선 · 고객 계약'})
_members('STNG',1483934,'ifrs-full:SegmentsAxis','segment',{
    'stng:HandymaxMember':'Handymax','stng:LR2Member':'LR2','stng:MRMember':'MR'},
    [('ifrs-full:SegmentConsolidationItemsAxis','ifrs-full:OperatingSegmentsMember')])
_members('TEN',1166663,'us-gaap:IncomeStatementLocationAxis','product',{
    'tnp:VoyageChartersAndContractsMember':'항해 용선·운송 계약'})
_members('TEN',1166663,'srt:StatementScenarioAxis','product',{
    'tnp:TimeBareboatAndPoolingCharterArrangementsMember':'기간·나용선·운항 풀'})
for _symbol,_cik,_prefix in [('TK',911971,'tk'),('TNK',1419945,'tnk')]:
    _members(_symbol,_cik,PRODUCT,'product',{
        _prefix+':VoyageChartersSuezmaxMember':'Suezmax · 항해 용선',
        _prefix+':VoyageChartersAframaxAndLR2Member':'Aframax·LR2 · 항해 용선',
        _prefix+':VoyageChartersVLCCMember':'VLCC · 항해 용선',
        _prefix+':TimeChartersSuezmaxMember':'Suezmax · 기간 용선',
        _prefix+':TimeChartersAframaxLR2Member':'Aframax·LR2 · 기간 용선',
        _prefix+':TimeCharterBunkerTankerMember':'연료 공급선 · 기간 용선',
        _prefix+':VesselOperationalAndMaintenanceServicesOtherRevenueMember':'선박 운항·정비',
        _prefix+':ShiptoshipsupportservicesOtherrevenueMember':'선박 간 화물 이송 지원',
        _prefix+':ManagementFeesAndOtherOtherRevenueMember':'관리·기타'})
    _members(_symbol,_cik,SEGMENT,'segment',{
        _prefix+':TankersMember':'유조선',_prefix+':MarineServicesAndOtherMember':'해상 서비스·기타'})
_members('TORO',1941131,SEGMENT,'segment',{
    'toro:EcoTankerSegmentMember':'Eco 탱커','toro:NonEcoTankerSegmentMember':'일반 탱커',
    'toro:LPGCarrierSegmentMember':'LPG 운송'},[OPERATING])
_members('TORO',1941131,PRODUCT,'product',{
    'toro:TimeCharterMember':'기간 용선 · 리스',
    'toro:PoolAgreementsMember':'운항 풀 · 리스'})
_members('IMPP',1876581,PRODUCT,'product',{
    'impp:TimeCharterRevenuesMember':'기간 용선 · 부분 구성',
    'impp:VoyageCharterRevenuesMember':'항해 용선 · 부분 구성'})
_members('PXS',1640043,PRODUCT,'product',{
    'PXS:SpotVoyageChartersMember':'현물 항해 용선','PXS:TimeChartersMember':'기간 용선'})
_members('PXS',1640043,SEGMENT,'segment',{
    'PXS:TankerVesselsMember':'석유 제품 탱커','PXS:DryBulkVesselsMember':'건화물 운송'},
    [('us-gaap:SubsegmentsConsolidationItemsAxis','us-gaap:ReportableSubsegmentsMember')])
_members('KNOP',1564180,PRODUCT,'product',{
    'knop:TimeCharterRevenuesMember':'기간 용선','knop:BareboatRevenuesMember':'나용선'})

# Exact statement metrics, not a global acceptance of issuer extension tags.
EXTRA_METRICS = {
    'DHT':('dht:ShippingRevenue','ifrs-full:OtherRevenue'),
    'FRO':('ifrs-full:RevenueFromRenderingOfServices','ifrs-full:OtherRevenue'),
    'LPG':('lpg:NetPoolRevenuesRelatedPartyIncome','us-gaap:RevenueNotFromContractWithCustomerOther'),
    'NVGS':(LEASE,),
    'TEN':('us-gaap:RevenueNotFromContractWithCustomer','tnp:OperatingLeaseLeaseIncome1'),
    'TORO':(LEASE,),
    'KNOP':('knop:OtherRevenues',),
}
STATEMENT_LINES = {
    'DHT':(('ifrs-full:OtherRevenue','revenue_type','기타 수입 · 운송 외'),),
    'FRO':(('ifrs-full:OtherRevenue','revenue_type','기타 수입 · 서비스 외'),),
    'FLNG':((CONTRACT,'segment','LNG 선박 용선 · 단일 보고 사업'),),
    'LPG':(('lpg:NetPoolRevenuesRelatedPartyIncome','product','Helios 운항 풀 · 순수입'),
           ('us-gaap:RevenueNotFromContractWithCustomerOther','product','기타 수입')),
    'NVGS':((LEASE,'product','운영 리스 · 운항 풀'),),
    'KNOP':(('knop:OtherRevenues','product','기타 · 항해 수입 포함'),),
}
for (_symbol,_cik) in DOCUMENTS:
    for _metric,_group,_label in STATEMENT_LINES.get(_symbol,()):
        LABELS[_symbol,_cik,_metric] = _label


def reviewed(row,symbol,cik):
    return ((row['start'],row['end']) == PERIODS.get((symbol,cik))
        and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol,cik)))


def extra_metrics(origin,symbol,cik,period_end):
    return (EXTRA_METRICS.get(symbol,())
        if (origin['url'].split('#')[0] == DOCUMENTS.get((symbol,cik))
            and period_end is not None
            and period_end.isoformat() == PERIODS.get((symbol,cik),(None,None))[1]) else ())


def dimensions(pairs,symbol,cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol,cik,frozenset(pairs)))


def metric_allowed(tag,group,start,end,origin,symbol,cik):
    if not reviewed(dict(start=start,end=end,source=origin),symbol,cik):
        return True
    expected = {
        'DHT':('dht:ShippingRevenue',),
        'FRO':('ifrs-full:RevenueFromRenderingOfServices',),
        'GLNG':(CONTRACT,), 'FLNG':(CONTRACT,),
        'INSW':('us-gaap:Revenues',) if group=='product' else (CONTRACT,),
        'NAT':(CONTRACT,), 'NVGS':(CONTRACT_TAX,),
        'STNG':('ifrs-full:Revenue',),
        'TEN':EXTRA_METRICS['TEN'], 'TK':(CONTRACT,), 'TNK':(CONTRACT,),
        'TORO':(LEASE,) if group=='product' else ('us-gaap:Revenues',),
        'IMPP':(CONTRACT_TAX,),
        'PXS':(CONTRACT_TAX,) if group=='product' else ('us-gaap:Revenues',),
        'KNOP':(CONTRACT,),
    }.get(symbol,())
    return tag in expected


def statement_rows(rows,clean,anchors,origin,symbol,cik,period_end):
    """Project only actually reported, identity-checked statement facts.

    clean already rejects typed, foreign-CIK, invalid-unit and conflicting facts.
    A missing component is never inferred from the difference of two totals.
    """
    period = PERIODS.get((symbol,cik))
    if (period is None or origin['url'].split('#')[0] != DOCUMENTS[symbol,cik]
            or period_end is None or period_end.isoformat()!=period[1]):
        return rows
    start,end = period
    for metric,group,label in STATEMENT_LINES.get(symbol,()):
        key = metric,'USD',start,end,None,''
        value = clean.get(key)
        if value is None:
            continue
        rows.append(dict(group=group,member=metric,label=label,value=float(value),
            unit='USD',start=start,end=end,total=None,metric=metric,parent=None,
            includes_intersegment=False,
            source={**origin,'url':origin['url']+('#'+anchors[key] if key in anchors else '')}))
    # TEN's two classes use different original accounting metrics. Retain both
    # only when the actual statement total proves their reconciliation.
    if symbol=='TEN':
        components = [
            ('us-gaap:RevenueNotFromContractWithCustomer','tnp:VoyageChartersAndContractsMember'),
            ('tnp:OperatingLeaseLeaseIncome1','tnp:TimeBareboatAndPoolingCharterArrangementsMember')]
        keys = [(tag,'USD',start,end,'product',member) for tag,member in components]
        total = clean.get(('us-gaap:Revenues','USD',start,end,None,''))
        if total is not None and all(key in clean for key in keys) and sum(clean[key] for key in keys)==total:
            rows = [row for row in rows if row['group']!='product']
            for key in keys:
                rows.append(dict(group='product',member=key[5],label=LABELS[symbol,cik,key[5]],
                    value=float(clean[key]),unit='USD',start=start,end=end,total=None,metric=key[0],
                    parent=None,includes_intersegment=False,
                    source={**origin,'url':origin['url']+('#'+anchors[key] if key in anchors else '')}))
        else:
            rows = [row for row in rows if row['group']!='product']
    return rows


def presentation_group(row,symbol,cik):
    if reviewed(row,symbol,cik):
        found = {group for (issuer,identity,_),(group,member) in COORDINATES.items()
                 if (issuer,identity,member)==(symbol,cik,row['member'])}
        found.update(group for metric,group,_ in STATEMENT_LINES.get(symbol,()) if metric==row['member'])
        if len(found)==1:
            return found.pop()
    return row['group']


def canonical(rows,symbol,cik):
    allowed = {(group,member) for (issuer,identity,_),(group,member) in COORDINATES.items()
               if (issuer,identity)==(symbol,cik)}
    allowed.update((group,metric) for metric,group,_ in STATEMENT_LINES.get(symbol,()))
    selected = []
    for row in rows:
        if reviewed(row,symbol,cik):
            statement = any((row['metric'],row['group'],row['member'])==(metric,group,metric)
                            for metric,group,_ in STATEMENT_LINES.get(symbol,()))
            if (row['unit']!='USD' or (row['group'],row['member']) not in allowed or (not statement and
                    not metric_allowed(row['metric'],row['group'],row['start'],row['end'],row['source'],symbol,cik))):
                continue
            if symbol=='TEN' and row['group']=='product' and (row['member'],row['metric']) not in {
                    ('tnp:VoyageChartersAndContractsMember','us-gaap:RevenueNotFromContractWithCustomer'),
                    ('tnp:TimeBareboatAndPoolingCharterArrangementsMember','tnp:OperatingLeaseLeaseIncome1')}:
                continue
        selected.append(row)
    values = {}
    for row in selected:
        if reviewed(row,symbol,cik):
            key = tuple(row[k] for k in ('group','member','start','end','unit','metric'))
            values.setdefault(key,set()).add(Decimal(str(row['value'])))
    result,seen = [],set()
    for row in selected:
        if reviewed(row,symbol,cik):
            key = tuple(row[k] for k in ('group','member','start','end','unit','metric'))
            if key in seen or len(values[key])!=1:
                continue
            seen.add(key)
        result.append(row)
    if symbol=='TEN':
        product = [row for row in result if reviewed(row,symbol,cik) and row['group']=='product']
        if len(product)!=2:
            result = [row for row in result if not (reviewed(row,symbol,cik) and row['group']=='product')]
    return result


def annotate(rows,symbol,cik):
    explanations = {
        'DHT':'기간·항해 용선 합계는 운송 수입 497,197,000 USD입니다. 기타 수입 1,203,000을 포함한 연결 498,400,000과 다른 분모입니다.',
        'FRO':'용선·관리 서비스 1,965,104,000 USD와 기타 수입 6,069,000을 구분합니다. 연결 수입은 1,971,173,000이며 같은 서비스에 포함된 리스·비리스 부분을 다시 더하지 않습니다.',
        'FLNG':'원문 단일 LNG 용선 사업의 실제 수입입니다. 표시 키는 원래 매출 태그이며 공시에 없는 사업 부문 식별자를 만든 값이 아닙니다. EUA 거래 수입은 이미 포함됩니다.',
        'LPG':'FY2026는 2025-04-01~2026-03-31입니다. Helios 풀 순수입 474,888,842 USD와 기타 6,622,400의 합계는 481,511,242입니다. 서로 다른 실제 태그를 보존하며 풀의 최종 고객 총운임과는 다릅니다.',
        'GLNG':'FLNG 지역 표 366,724,000 USD는 Hilli·Gimi만 포함합니다. 연결 393,522,000의 지역별 구성비나 생산 LNG의 판매액이 아닙니다.',
        'NVGS':'고객 계약 538,457,000 USD와 운영 리스 48,504,000의 합계는 586,961,000입니다. 서로 다른 태그를 그대로 보존하며 지분법 수출 터미널 전체 수입 97,859,000은 연결에 더하지 않습니다.',
        'TEN':'항해·운송 계약 136,701,000 USD와 기간·나용선·풀 661,988,000의 합계는 798,689,000입니다. 원문의 서로 다른 태그를 보존하며 전대 리스 소계 29,273,000을 다시 더하지 않습니다.',
        'TORO':'연결 수입 21,081,840 USD는 리스 수입으로 구성됩니다. 고객 계약 태그의 0은 전체 수입 0이 아닙니다. 처분·분할한 선박의 중단 사업은 제외합니다.',
        'IMPP':'기간·항해 두 계약 항목의 합계 154,775,747 USD는 전체 161,004,306보다 6,228,559 작습니다. 미태그 부분을 차액으로 만들어 넣거나 100% 구성비로 표시하지 않습니다.',
        'KNOP':'기간 용선 359,094,000 USD·나용선 2,091,000·기타 3,258,000의 합계는 364,443,000입니다. 기타에 포함된 항해 466,000과 기간·나용선 상위 소계를 다시 더하지 않습니다. 서로 다른 태그를 보존합니다.',
    }
    for row in rows:
        if not reviewed(row,symbol,cik):
            continue
        omit = (symbol in {'NVGS','LPG','TEN','KNOP','IMPP'} or
                (symbol in {'DHT','FRO'} and row['group']=='revenue_type') or
                (symbol=='GLNG' and row['group']=='geography') or
                (symbol=='TORO' and row['group']=='product'))
        if symbol in explanations and (symbol!='GLNG' or row['group']=='geography'):
            row['share_exclusion'] = explanations[symbol]
        if omit:
            row['total'] = None
        row['parent'] = None
    return rows
