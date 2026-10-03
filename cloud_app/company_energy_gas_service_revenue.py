"""Reviewed fuel, compression, power and gathering tables; no inferred totals."""
from decimal import Decimal
IDENTITIES={'CLNE': 1368265, 'FGPR': 922358, 'NFG': 70145, 'NGS': 1084991, 'SEI': 1697500, 'SMC': 2024218}
DOCUMENTS={('CLNE', 1368265): 'https://www.sec.gov/Archives/edgar/data/1368265/000110465926019215/clne-20251231x10k.htm', ('FGPR', 922358): 'https://www.sec.gov/Archives/edgar/data/922358/000110465926110592/fgp-20260731x10k.htm', ('NFG', 70145): 'https://www.sec.gov/Archives/edgar/data/70145/000007014525000039/nfg-20250930.htm', ('NGS', 1084991): 'https://www.sec.gov/Archives/edgar/data/1084991/000108499126000015/ngs-20251231.htm', ('SEI', 1697500): 'https://www.sec.gov/Archives/edgar/data/1697500/000162828026012501/sei-20251231.htm', ('SMC', 2024218): 'https://www.sec.gov/Archives/edgar/data/2024218/000202421826000017/smlp-20251231.htm'}
PERIODS={('CLNE', 1368265): ('2025-01-01', '2025-12-31'), ('FGPR', 922358): ('2025-08-01', '2026-07-31'), ('NFG', 70145): ('2024-10-01', '2025-09-30'), ('NGS', 1084991): ('2025-01-01', '2025-12-31'), ('SEI', 1697500): ('2025-01-01', '2025-12-31'), ('SMC', 2024218): ('2025-01-01', '2025-12-31')}
CONTRACT='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
PRODUCT='srt:ProductOrServiceAxis'
SEGMENT='us-gaap:StatementBusinessSegmentsAxis'
OPERATING=('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember')
COORDINATES,LABELS={},{}
def _members(symbol,axis,group,values,qualifiers=()):
    cik=IDENTITIES[symbol]
    for member,label in values.items():
        COORDINATES[symbol,cik,frozenset([(axis,member),*qualifiers])]=group,member
        LABELS[symbol,cik,member]=label
_members('CLNE',PRODUCT,'product',{'clne:VolumeRelatedProductRevenueMember':'연료·환경 크레딧 · 평가 조정 후 순매출','clne:StationConstructionSalesMember':'충전소 건설','clne:VolumeRelatedOperationsAndMaintenanceServiceRevenueMember':'운영·정비 서비스','clne:OtherServiceRevenueSourceMember':'기타 서비스'})
_members('CLNE',PRODUCT,'revenue_type',{'us-gaap:ProductMember':'제품 순매출','us-gaap:ServiceMember':'서비스'})
_members('CLNE',SEGMENT,'segment',{'clne:SingleReportableSegmentMember':'연료·충전·서비스 단일 보고 부문'})
_members('CLNE','srt:StatementGeographicalAxis','geography',{'country:US':'미국','country:CA':'캐나다'})
_members('FGPR',PRODUCT,'product',{'us-gaap:RetailMember':'소매 프로판','fgp:WholesaleSalesToResellersMember':'재판매상 도매','fgp:OtherGasSalesMember':'기타 가스 판매','us-gaap:ProductAndServiceOtherMember':'기타 제품·서비스'})
_members('FGPR',SEGMENT,'segment',{'fgp:PropaneOperationAndRelatedEquipmentSalesSegmentMember':'프로판·관련 장비 단일 부문'})
_members('NFG',SEGMENT,'segment',{'nfg:IntegratedUpstreamAndGatheringAndOtherMember':'통합 생산·집하·기타 · 외부','nfg:PipelineAndStorageMember':'파이프라인·저장 · 외부','nfg:TotalUtilityMember':'규제 가스 공급 · 외부'})
_members('NFG',PRODUCT,'product',{'nfg:NaturalGasCommercialSalesMember':'상업용 가스 공급','nfg:NaturalGasIndustrialSalesMember':'산업용 가스 공급','nfg:NaturalGasProcessingMember':'가스 처리','nfg:NaturalGasResidentialSalesMember':'가정용 가스 공급','nfg:ProductionofCrudeOilMember':'원유 생산','us-gaap:NaturalGasMidstreamMember':'가스 집하','us-gaap:NaturalGasProductionMember':'가스 생산','us-gaap:NaturalGasStorageMember':'가스 저장','us-gaap:OilAndGasServiceMember':'가스 운송 서비스','us-gaap:ProductAndServiceOtherMember':'기타 계약 매출'})
_members('NGS',PRODUCT,'product',{'ngs:OtherPartsRebuildsMember':'부품 판매','ngs:CompressorRelatedMember':'압축기·재제작 판매','ngs:AftermarketServicesMember':'고객 장비 사후 서비스'})
_members('SEI',SEGMENT,'segment',{'sei:SolarisPowerSolutionsMember':'Power Solutions · 반올림','sei:SolarisLogisticsSolutionsMember':'Logistics Solutions · 반올림'},[OPERATING])
for _segment,_member,_label in [('sei:SolarisPowerSolutionsMember','sei:LeasingRevenueMember','발전 장비 임대 · 반올림'),('sei:SolarisPowerSolutionsMember','us-gaap:ServiceMember','발전 서비스 · 반올림'),('sei:SolarisLogisticsSolutionsMember','us-gaap:ServiceMember','유전 물류 서비스 · 반올림')]:
    _key=_segment+'/'+_member
    COORDINATES['SEI',1697500,frozenset([(PRODUCT,_member),(SEGMENT,_segment)])]='product',_key
    LABELS['SEI',1697500,_key]=_label
_members('SEI','us-gaap:RelatedPartyTransactionsByRelatedPartyAxis','revenue_type',{'us-gaap:NonrelatedPartyMember':'서비스 · 손익계산서 정확값'})
_members('SMC',PRODUCT,'product',{'us-gaap:NaturalGasGatheringTransportationMarketingAndProcessingMember':'집하·처리 수수료','us-gaap:OilAndCondensateMember':'천연가스·NGL·콘덴세이트 판매','us-gaap:ProductAndServiceOtherMember':'기타 제품·서비스'})
_members('SMC',SEGMENT,'segment',{'smlp:RockiesSegmentMember':'Rockies','smlp:PermianBasinSegmentMember':'Permian · 연결 매출','smlp:MidConBarnettShaleSegmentMember':'Mid-Con·Barnett','smlp:PiceanceBasinSegmentMember':'Piceance'},[OPERATING])
STATEMENT_LINES={'NGS':(('us-gaap:RentalIncomeNonoperating','product','압축기 임대'),),'SEI':(('us-gaap:OperatingLeaseLeaseIncome','revenue_type','임대 · 손익계산서 정확값'),)}
EXTRA_METRICS={s:tuple(tag for tag,_,_ in lines) for s,lines in STATEMENT_LINES.items()}
for _s,_lines in STATEMENT_LINES.items():
    for _tag,_group,_label in _lines:LABELS[_s,IDENTITIES[_s],_tag]=_label

def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == PERIODS.get((symbol,cik))
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def dimensions(pairs, symbol, cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol, cik, frozenset(pairs)))


def metric_allowed(tag,group,start,end,origin,symbol,cik):
    if not reviewed(dict(start=start,end=end,source=origin),symbol,cik):return True
    if symbol=='NFG' and group=='segment':return tag=='us-gaap:Revenues'
    if symbol=='SEI':return tag in ((CONTRACT,'us-gaap:OperatingLeaseLeaseIncome') if group=='revenue_type' else ('us-gaap:Revenues',))
    if symbol=='NGS':return tag in (CONTRACT,'us-gaap:RentalIncomeNonoperating')
    return tag==CONTRACT

def canonical(rows, symbol, cik):
    allowed = {(group, member) for (issuer, identity, _), (group, member) in COORDINATES.items()
               if (issuer, identity) == (symbol, cik)}
    allowed.update((group,tag) for tag,group,_ in STATEMENT_LINES.get(symbol,()))
    selected = [row for row in rows if not reviewed(row, symbol, cik) or (
        row['unit'] == 'USD' and (row['group'], row['member']) in allowed
        and metric_allowed(row['metric'], row['group'], row['start'], row['end'], row['source'], symbol, cik))]
    values = {}
    for row in selected:
        if reviewed(row, symbol, cik):
            key = tuple(row[k] for k in ('group', 'member', 'start', 'end', 'unit', 'metric'))
            values.setdefault(key, set()).add(Decimal(str(row['value'])))
    kept, seen = [], set()
    for row in selected:
        if reviewed(row, symbol, cik):
            key = tuple(row[k] for k in ('group', 'member', 'start', 'end', 'unit', 'metric'))
            if key in seen or len(values[key]) != 1:
                continue
            seen.add(key)
        kept.append(row)
    return kept


def presentation_group(row, symbol, cik):
    if reviewed(row, symbol, cik):
        groups = {group for (issuer, identity, _), (group, member) in COORDINATES.items()
                  if (issuer, identity, member) == (symbol, cik, row['member'])}
        groups.update(group for tag,group,_ in STATEMENT_LINES.get(symbol,()) if tag==row['member'])
        if len(groups) == 1:
            return groups.pop()
    return row['group']


def extra_metrics(origin,symbol,cik,period_end):
    return EXTRA_METRICS.get(symbol,()) if (period_end is not None and origin['url'].split('#')[0]==DOCUMENTS.get((symbol,cik)) and period_end.isoformat()==PERIODS.get((symbol,cik),(None,None))[1]) else ()

def statement_rows(rows,clean,anchors,origin,symbol,cik,period_end):
    if not extra_metrics(origin,symbol,cik,period_end):return rows
    start,end=PERIODS[symbol,cik]
    for tag,group,label in STATEMENT_LINES.get(symbol,()):
        key=tag,'USD',start,end,None,''
        if key in clean:
            rows.append(dict(group=group,member=tag,label=label,value=float(clean[key]),unit='USD',start=start,end=end,total=None,metric=tag,parent=None,includes_intersegment=False,source={**origin,'url':origin['url']+('#'+anchors[key] if key in anchors else '')}))
    return rows

def signed_value(tag,context,origin,symbol,cik):return False

def annotate(rows,symbol,cik):
    for row in rows:
        if not reviewed(row,symbol,cik):continue
        row['label']=LABELS.get((symbol,cik,row['member']),row['label'])
        row['parent']=None
        if symbol=='SEI':
            row['share_exclusion']=('부문·제품 주석은 백만 USD 반올림 표이며 손익계산서 서비스/임대 분류와도 차이가 있습니다. 정확한 전체매출 622,205,000의 비중으로 계산하지 않습니다.' if row['group']!='revenue_type' else '서로 다른 계약 서비스/임대 회계 지표의 정확값입니다. 두 항목 합계는 622,205,000 USD이며 단일 지표 구성비로 계산하지 않습니다.')
            row['total']=None
        if symbol=='NGS':
            row['share_exclusion']='임대 수입과 고객 계약 매출을 합친 원문 표입니다. 2025 합계172,315,000 USD이며 서로 다른 회계 지표에 동일 분모 비중을 붙이지 않습니다.'
            row['total']=None
        if symbol=='NFG' and row['group']=='product':
            row['share_exclusion']='고객 계약 매출 2,219,117,000 USD의 구분입니다. 파생상품·대체 요금 수익 등이 포함된 연결 매출2,277,541,000 전체의 비중과 다릅니다.'
            row['total']=None
    return rows
