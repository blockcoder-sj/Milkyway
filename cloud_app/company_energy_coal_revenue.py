"""Reviewed coal tables: external CNR revenue and signed mining reconciliations."""
from decimal import Decimal
IDENTITIES = {'ARLP':1086600,'BTU':1064728,'CNR':1710366,'NC':789933}
DOCUMENTS = {
('ARLP',1086600):'https://www.sec.gov/Archives/edgar/data/1086600/000110465926020468/arlp-20251231x10k.htm',
('BTU',1064728):'https://www.sec.gov/Archives/edgar/data/1064728/000106472826000006/btu-20251231.htm',
('CNR',1710366):'https://www.sec.gov/Archives/edgar/data/1710366/000171036626000007/cnr-20251231.htm',
('NC',789933):'https://www.sec.gov/Archives/edgar/data/789933/000078993326000070/nacco-20251231.htm'}
PERIOD=('2025-01-01','2025-12-31')
CONTRACT='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
PRODUCT='srt:ProductOrServiceAxis'
SEGMENT='us-gaap:StatementBusinessSegmentsAxis'
OPERATING=('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember')
COORDINATES, LABELS = {}, {}
def _members(symbol,axis,group,values,qualifiers=()):
    cik=IDENTITIES[symbol]
    for member,label in values.items():
        COORDINATES[symbol,cik,frozenset([(axis,member),*qualifiers])]=group,member
        LABELS[symbol,cik,member]=label
_members('ARLP',PRODUCT,'product',{'arlp:CoalProductsAndServicesRevenueMember':'석탄 제품·서비스','us-gaap:RoyaltyMember':'원유·가스 로열티','us-gaap:ShippingAndHandlingMember':'운송·취급','us-gaap:ProductAndServiceOtherMember':'기타 제품·서비스'})
_members('ARLP',SEGMENT,'segment',{'arlp:IllinoisBasinSegmentMember':'Illinois Basin','arlp:AppalachiaSegmentMember':'Appalachia','arlp:RoyaltiesOilAndGasSegmentMember':'원유·가스 로열티','arlp:RoyaltiesCoalSegmentMember':'석탄 로열티'},[OPERATING])
_members('ARLP','srt:ConsolidationItemsAxis','segment',{'us-gaap:CorporateNonSegmentMember':'본사·기타 · 내부거래 제거 포함'})
_members('BTU',PRODUCT,'product',{'btu:MetallurgicalCoalMember':'제철용 석탄','btu:ThermalCoalMember':'발전용 석탄','us-gaap:ProductAndServiceOtherMember':'기타 제품·서비스'})
_members('BTU',SEGMENT,'segment',{'btu:OtherUSThermalMiningMember':'기타 미국 발전용 석탄','btu:PowderRiverBasinMiningMember':'Powder River Basin','btu:SeaborneMetallurgicalMiningMember':'해상 제철용 석탄','btu:SeaborneThermalMiningMember':'해상 발전용 석탄','us-gaap:CorporateAndOtherMember':'본사·기타'})
_members('CNR',PRODUCT,'product',{'cnr:PowerGenerationMember':'발전용 석탄','cnr:IndustrialMember':'산업용 석탄','cnr:MetallurgicalMember':'제철용 석탄','cnr:TerminalRevenueMember':'제3자 터미널 서비스','cnr:OtherRevenueMember':'기타 매출'})
_members('CNR',SEGMENT,'segment',{'cnr:HighCVThermalMember':'고열량 발전용 석탄 · 외부','cnr:MetallurgicalSegmentMember':'제철용 석탄 · 외부','cnr:PRBMember':'Powder River Basin · 외부','cnr:CoreMarineTerminalMember':'Core Marine Terminal · 제3자'})
_members('CNR','srt:ConsolidationItemsAxis','segment',{'cnr:CorporateAndReconcilingItemsMember':'휴지·기타 · 본사 조정'})
_members('NC',SEGMENT,'segment',{'nacco:UtilityCoalMiningMember':'Utility Coal Mining','nacco:ContractMiningMember':'Contract Mining','nacco:MineralsAndRoyaltiesMember':'Minerals and Royalties'},[OPERATING])
_members('NC','srt:ConsolidationItemsAxis','segment',{'us-gaap:CorporateNonSegmentMember':'본사·기타','srt:ConsolidationEliminationsMember':'연결 내부거래 제거'})

def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == PERIOD
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def dimensions(pairs, symbol, cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol, cik, frozenset(pairs)))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if not reviewed(dict(start=start, end=end, source=origin), symbol, cik):
        return True
    return tag == ('us-gaap:Revenues' if symbol == 'BTU' else CONTRACT)


def canonical(rows, symbol, cik):
    allowed = {(group, member) for (issuer, identity, _), (group, member) in COORDINATES.items()
               if (issuer, identity) == (symbol, cik)}
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
        if len(groups) == 1:
            return groups.pop()
    return row['group']


def signed_value(tag, context, origin, symbol, cik):
    start,end,group,member=context
    return (tag==CONTRACT and group=='segment' and (symbol,member) in {
        ('ARLP','us-gaap:CorporateNonSegmentMember'),('NC','srt:ConsolidationEliminationsMember')}
        and reviewed(dict(start=start,end=end,source=origin),symbol,cik))

def annotate(rows,symbol,cik):
    for row in rows:
        if reviewed(row,symbol,cik):
            row['label']=LABELS.get((symbol,cik,row['member']),row['label'])
            row['parent']=None
            if symbol in {'ARLP','NC'} and row['group']=='segment':
                row['share_exclusion']='부문 매출과 음수 본사·내부거래 조정을 함께 보존한 표입니다. 조정 전 매출을 연결 구성비로 사용하지 않습니다.'
                row['includes_intersegment'],row['total']=True,None
    return rows
