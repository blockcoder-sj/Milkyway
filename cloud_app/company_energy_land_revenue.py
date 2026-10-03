"""Reviewed land/mineral revenue coordinates, scoped to an actual filing and FY.

Royalty operators are not necessarily product purchasers. Keep royalties, leases,
derivative gains and equity-method income on their original accounting bases.
Non-inline trust statement tables are separately transcribed in land_tables.
"""
from decimal import Decimal

DOCUMENTS = {
 ('BSM',1621434):'https://www.sec.gov/Archives/edgar/data/1621434/000162143426000018/bsm-20251231.htm',
 ('DMLP',1172358):'https://www.sec.gov/Archives/edgar/data/1172358/000143774926005376/dmlp20251231_10k.htm',
 ('KRP',1657788):'https://www.sec.gov/Archives/edgar/data/1657788/000110465926020477/krp-20251231x10k.htm',
 ('NRP',1171486):'https://www.sec.gov/Archives/edgar/data/1171486/000143774926006147/nrp20251231_10k.htm',
 ('TPL',1811074):'https://www.sec.gov/Archives/edgar/data/1811074/000181107426000018/tpl-20251231.htm',
 ('VNOM',2074176):'https://www.sec.gov/Archives/edgar/data/2074176/000207417626000010/vnom-20251231.htm',
 ('CKX',352955):'https://www.sec.gov/Archives/edgar/data/352955/000143774926010434/ckx20251231_10k.htm',
 ('MNR',1980088):'https://www.sec.gov/Archives/edgar/data/1980088/000162828026017249/mnr-20251231.htm',
 ('MXC',66418):'https://www.sec.gov/Archives/edgar/data/66418/000149315226030386/form10-k.htm',
 ('LB',1995807):'https://www.sec.gov/Archives/edgar/data/1995807/000119312526072404/lb-20251231.htm',
 ('PNRG',56868):'https://www.sec.gov/Archives/edgar/data/56868/000143774926012531/pnrg20251231_10k.htm',
}
PERIODS = {key:('2025-01-01','2025-12-31') for key in DOCUMENTS}
PERIODS['MXC',66418] = '2025-04-01','2026-03-31'
CONTRACT = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
CONTRACT_TAX = 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
LEASE = 'us-gaap:OperatingLeaseLeaseIncome'
PRODUCT = 'srt:ProductOrServiceAxis'
SEGMENT = 'us-gaap:StatementBusinessSegmentsAxis'
OPERATING = ('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember')
NRP_SEGMENT = 'nrp:RevenuesExcludingGainOnSaleOfAsset'
COORDINATES, LABELS = {}, {}


def _members(symbol,cik,axis,group,values,qualifiers=()):
    for member,label in values.items():
        COORDINATES[symbol,cik,frozenset([(axis,member),*qualifiers])] = group,member
        LABELS[symbol,cik,member] = label


_members('BSM',1621434,PRODUCT,'product',{
 'srt:OilReservesMember':'원유·콘덴세이트',
 'srt:NaturalGasReservesMember':'천연가스·NGL',
 'us-gaap:RealEstateMember':'임대 보너스·기타'})
_members('DMLP',1172358,PRODUCT,'product',{
 'dmlp:RoyaltiesMember':'광물·로열티 권리 수입',
 'dmlp:NetProfitInterestsMember':'순이익 권리 NPI',
 'dmlp:LeaseBonusMember':'임대 보너스','dmlp:OtherRevenueMember':'기타'})
_members('KRP',1657788,PRODUCT,'product',{
 'us-gaap:OilAndCondensateMember':'원유·콘덴세이트',
 'us-gaap:NaturalGasMidstreamMember':'천연가스 · 원문 제품 표',
 'krp:NGLRevenueMember':'NGL',
 'krp:LeaseBonusAndOtherIncomeMember':'임대 보너스·기타'})
_members('NRP',1171486,PRODUCT,'product',{
 'nrp:RoyaltyAndOtherMineralRightsMember':'로열티·기타 광물권',
 'nrp:TransportationAndProcessingServicesMember':'운송·처리 · 리스 포함'},
 [(SEGMENT,'nrp:MineralRightsSegmentMember')])
_members('NRP',1171486,SEGMENT,'segment',{
 'nrp:MineralRightsSegmentMember':'광물권 · 처분손익 제외',
 'nrp:SodaAshSegmentMember':'소다회 · 지분법 판매액 제외'},[OPERATING])
_members('TPL',1811074,PRODUCT,'product',{
 'tpl:OilAndGasRoyaltiesMember':'석유·가스 로열티',
 'tpl:WaterSalesAndRoyaltiesMember':'용수 판매·로열티',
 'tpl:ProducedWaterRoyaltiesMember':'생산수 로열티',
 'tpl:EasementandSundryMember':'통행·사용권·기타 토지 수입',
 'tpl:LandSalesMember':'토지 매각'})
_members('TPL',1811074,SEGMENT,'segment',{
 'tpl:LandAndResourceManagementSegmentMember':'토지·자원 관리',
 'tpl:WaterServiceandOperationsSegmentMember':'용수 서비스·운영'},[OPERATING])
_members('VNOM',2074176,PRODUCT,'product',{
 'vnom:OilIncomeMember':'원유 로열티','vnom:NaturalGasIncomeMember':'천연가스 로열티',
 'vnom:NaturalGasLiquidsIncomeMember':'NGL 로열티'})
_members('VNOM',2074176,'us-gaap:SubsegmentsAxis','revenue_type',{
 'vnom:DiamondbackOperatedPropertiesMember':'Diamondback 운영 자산 · 로열티만',
 'vnom:ThirdPartyOperatedPropertiesMember':'제3자 운영 자산 · 로열티만'})
_members('CKX',352955,PRODUCT,'product',{
 'us-gaap:OilAndGasMember':'석유·가스 로열티','us-gaap:TimberMember':'목재',
 'ckx:SurfaceLeasesUnrelatedPartiesMember':'제3자 토지 임대'})
_members('CKX',352955,SEGMENT,'segment',{
 'ckx:OilAndGasSegmentMember':'석유·가스','ckx:TimberSegmentMember':'목재',
 'ckx:SurfaceSegmentMember':'지표 토지 임대'},[OPERATING])
_members('MNR',1980088,PRODUCT,'product',{
 'mnr:OilGasAndNaturalGasLiquidsNetMember':'석유·가스·NGL · 생산 후 비용 차감',
 'mnr:OilAndNaturalGasDerivativesGainLossMember':'파생상품 손익',
 'us-gaap:NaturalGasMidstreamMember':'가스 집하·처리',
 'us-gaap:ProductMember':'외부 조달 상품 판매'})
_members('MNR',1980088,SEGMENT,'segment',{'mnr:ReportableSegmentMember':'단일 보고 사업'})
_members('MXC',66418,PRODUCT,'product',{
 'MXC:OilSalesMember':'원유','MXC:NaturalGasSalesMember':'천연가스','MXC:OtherMember':'기타'})
for _member,_label in {
 'lb:SurfaceUseRoyaltiesMember':'지표 사용 로열티',
 'lb:EasementsAndOtherSurfaceRelatedRevenuesMember':'통행·사용권·기타 토지 수입',
 'lb:ResourceSalesMember':'용수 등 자원 판매',
 'lb:ResourceRoyaltiesMember':'용수·모래 등 자원 로열티',
}.items():
    for _party,_suffix in [('us-gaap:RelatedPartyMember','특수관계자'),
                           ('us-gaap:NonrelatedPartyMember','제3자')]:
        _key = _member+'/'+_party
        COORDINATES['LB',1995807,frozenset([(PRODUCT,_member),
            ('us-gaap:RelatedPartyTransactionsByRelatedPartyAxis',_party)])] = 'product',_key
        LABELS['LB',1995807,_key] = _label+' · '+_suffix
_members('LB',1995807,PRODUCT,'product',{
 'lb:OilAndGasRoyaltiesMember':'석유·가스 로열티',
 'us-gaap:ProductAndServiceOtherMember':'기타'})
_members('PNRG',56868,PRODUCT,'product',{
 'pnrg:OilSalesMember':'원유','us-gaap:NaturalGasProductionMember':'천연가스',
 'pnrg:NaturalGasLiquidMember':'NGL','us-gaap:OilAndGasServiceMember':'유전 서비스'})
STATEMENT_LINES = {
 'BSM':(('us-gaap:GainLossOnDerivativeInstrumentsNetPretax','파생상품 순손익'),),
 'KRP':(('us-gaap:UnrealizedGainLossOnCommodityContracts','파생상품 순손익 · 원문 손익표'),),
 'PNRG':(('us-gaap:OtherIncome','기타 수입'),
         ('us-gaap:GainLossOnSaleOfPropertyPlantEquipment','자산 처분 순이익')),
}
EXTRA_METRICS = {'CKX':(LEASE,), 'NRP':(NRP_SEGMENT,),
                 **{symbol:tuple(tag for tag,_ in entries) for symbol,entries in STATEMENT_LINES.items()}}
for (_symbol,_cik) in DOCUMENTS:
    for _tag,_label in STATEMENT_LINES.get(_symbol,()):
        LABELS[_symbol,_cik,_tag]=_label


def reviewed(row,symbol,cik):
    return ((row['start'],row['end']) == PERIODS.get((symbol,cik))
        and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol,cik)))


def extra_metrics(origin,symbol,cik,period_end):
    return (EXTRA_METRICS.get(symbol,()) if
        origin['url'].split('#')[0] == DOCUMENTS.get((symbol,cik))
        and period_end is not None
        and period_end.isoformat() == PERIODS.get((symbol,cik),(None,None))[1] else ())


def dimensions(pairs,symbol,cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol,cik,frozenset(pairs)))


def metric_allowed(tag,group,start,end,origin,symbol,cik):
    if not reviewed(dict(start=start,end=end,source=origin),symbol,cik):
        return True
    if group=='revenue_type' and symbol in STATEMENT_LINES:
        return tag in EXTRA_METRICS[symbol]
    expected = {'DMLP':CONTRACT_TAX,'PNRG':CONTRACT_TAX,'MNR':'us-gaap:Revenues',
                'NRP':NRP_SEGMENT if group=='segment' else 'us-gaap:Revenues'}.get(symbol,CONTRACT)
    return tag in ((CONTRACT,LEASE) if symbol=='CKX' and group=='product' else (expected,))


def canonical(rows,symbol,cik):
    allowed = {(group,member) for (issuer,identity,_),(group,member) in COORDINATES.items()
               if (issuer,identity)==(symbol,cik)}
    allowed.update(('revenue_type',tag) for tag,_ in STATEMENT_LINES.get(symbol,()))
    selected=[]
    for row in rows:
        if reviewed(row,symbol,cik) and (row['unit']!='USD' or (row['group'],row['member']) not in allowed
                or not metric_allowed(row['metric'],row['group'],row['start'],row['end'],row['source'],symbol,cik)):
            continue
        selected.append(row)
    values={}
    for row in selected:
        if reviewed(row,symbol,cik):
            key=tuple(row[k] for k in ('group','member','start','end','unit','metric'))
            values.setdefault(key,set()).add(Decimal(str(row['value'])))
    kept,seen=[],set()
    for row in selected:
        if reviewed(row,symbol,cik):
            key=tuple(row[k] for k in ('group','member','start','end','unit','metric'))
            if key in seen or len(values[key])!=1:
                continue
            seen.add(key)
        kept.append(row)
    return kept


def presentation_group(row,symbol,cik):
    if reviewed(row,symbol,cik):
        groups={group for (issuer,identity,_),(group,member) in COORDINATES.items()
                if (issuer,identity,member)==(symbol,cik,row['member'])}
        groups.update('revenue_type' for tag,_ in STATEMENT_LINES.get(symbol,()) if row['member']==tag)
        if len(groups)==1:
            return groups.pop()
    return row['group']


def statement_rows(rows,clean,anchors,origin,symbol,cik,period_end):
    period=PERIODS.get((symbol,cik))
    if (period is None or period_end is None or period_end.isoformat()!=period[1]
            or origin['url'].split('#')[0]!=DOCUMENTS[symbol,cik]):
        return rows
    start,end=period
    for tag,label in STATEMENT_LINES.get(symbol,()):
        key=tag,'USD',start,end,None,''
        value=clean.get(key)
        if value is not None:
            rows.append(dict(group='revenue_type',member=tag,label=label,value=float(value),unit='USD',
                start=start,end=end,total=None,metric=tag,parent=None,includes_intersegment=False,
                source={**origin,'url':origin['url']+('#'+anchors[key] if key in anchors else '')}))
    # CKX reports one lease component under a different original metric.
    # The parser's single-metric view would otherwise omit that actual row.
    if (symbol,cik)!=('CKX',352955):
        return rows
    start,end=PERIODS[symbol,cik]
    member='ckx:SurfaceLeasesUnrelatedPartiesMember'
    key=LEASE,'USD',start,end,'product',member
    value=clean.get(key)
    if value is not None:
        rows.append(dict(group='product',member=member,label=LABELS[symbol,cik,member],
            value=float(value),unit='USD',start=start,end=end,total=None,metric=LEASE,
            parent=None,includes_intersegment=False,
            source={**origin,'url':origin['url']+('#'+anchors[key] if key in anchors else '')}))
    return rows


EXPLANATIONS = {
 'BSM':'고객 계약 422,328,000 USD 구성입니다. 연결 수입 469,919,000에는 파생상품 순이익 47,591,000이 포함되므로 전체 수입 구성비가 아닙니다.',
 'DMLP':'로열티 상위 항목 127,823,000 USD와 그 안의 원유 114,116,000·가스 13,707,000을 중복 합산하지 않습니다. NPI·임대 보너스·기타 포함 합계는 152,832,000입니다.',
 'KRP':'상품·임대/기타 합계 321,739,000 USD입니다. 연결 333,830,000에 포함된 파생상품 순이익 12,091,000은 원유·가스 판매가 아닙니다.',
 'NRP':'광물권·물류 매출 202,340,000 USD입니다. 운송·처리 11,295,000에는 리스 수입이 포함됩니다. 순수입 207,282,000의 자산 처분·지분법 수익이나 Sisecam Wyoming 자체 판매 529,382,000을 더하지 않습니다.',
 'VNOM':'제품별·운영사별 표는 같은 로열티 1,346,000,000 USD를 각각 나눈 것입니다. 연결 수입 1,395,000,000에는 임대 보너스 48,000,000·기타 1,000,000도 포함됩니다.',
 'CKX':'로열티 415,469 USD·목재 94,825·임대 328,249 합계는 838,543입니다. 제품 표의 고객 계약/리스 태그를 보존합니다. 토지 처분 이익은 이 매출 구성과 다릅니다.',
 'MNR':'순상품 판매 1,037,650,000 USD·파생상품 81,289,000·중류 27,561,000·외부 상품 28,890,000의 합계입니다. 총상품 판매 1,040,852,000과 그 제품별 내역을 다시 더하지 않습니다. 차액 3,202,000은 공시된 생산 후 비용입니다.',
 'MXC':'FY2026는 2025-04-01~2026-03-31입니다. 제품 3개 합계 6,561,324 USD와 사무실 전대 수입을 구분합니다.',
 'LB':'제품×특수관계자 여부의 두 축을 모두 보존합니다. 10개 실제 항목의 합계는 199,093,000 USD입니다. 별도 관련자 약정 표 소계 55,899,000을 다시 더하지 않습니다.',
 'PNRG':'제품·서비스 185,909,000 USD와 실제 별도 태그의 기타 수입 1,536,000·자산 처분 순이익 1,607,000이 연결 수입 189,052,000을 구성합니다. 처분이익을 원유·가스 판매에 합치지 않습니다.',
}


def annotate(rows,symbol,cik):
    for row in rows:
        if not reviewed(row,symbol,cik):
            continue
        row['label']=LABELS.get((symbol,cik,row['member']),row['label'])
        row['parent']=None
        if symbol in EXPLANATIONS:
            row['share_exclusion']=EXPLANATIONS[symbol]
        if symbol in {'BSM','KRP','NRP','VNOM','PNRG'} or (symbol=='CKX' and row['group']=='product'):
            row['total']=None
    return rows
