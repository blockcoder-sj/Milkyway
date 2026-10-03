"""Exact annual coordinates for the reviewed specialist-service documents.

Do not combine regional parents with their children, product cross-tabs with
product totals, or external revenue with intersegment activity. The Forum
product table retains its actual signed elimination, never a computed plug.
"""
from decimal import Decimal

DOCUMENTS = {
    ('CLB', 1958086): 'https://www.sec.gov/Archives/edgar/data/1958086/000119312526118177/clb-20251231.htm',
    ('FET', 1401257): 'https://www.sec.gov/Archives/edgar/data/1401257/000140125726000015/fet-20251231.htm',
    ('NESR', 1698514): 'https://www.sec.gov/Archives/edgar/data/1698514/000149315226009139/form10-k.htm',
    ('OII', 73756): 'https://www.sec.gov/Archives/edgar/data/73756/000007375626000016/oii-20251231.htm',
    ('OIS', 1121484): 'https://www.sec.gov/Archives/edgar/data/1121484/000112148426000007/ois-20251231.htm',
}
PERIOD = ('2025-01-01', '2025-12-31')
CONTRACT = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
PRODUCT = 'srt:ProductOrServiceAxis'
SEGMENT = 'us-gaap:StatementBusinessSegmentsAxis'
GEO = 'srt:StatementGeographicalAxis'
OPERATING = ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember')
ELIMINATION = ('srt:ConsolidationItemsAxis', 'us-gaap:IntersegmentEliminationMember')
COORDINATES, LABELS = {}, {}


def _members(symbol, cik, axis, group, values, qualifiers=()):
    for member, label in values.items():
        COORDINATES[symbol, cik, frozenset([(axis, member), *qualifiers])] = group, member
        LABELS[symbol, cik, member] = label


_members('CLB', 1958086, SEGMENT, 'segment', {
    'clb:OperatingSegmentReservoirDescriptionMember': '저류층 분석 · 외부 매출',
    'clb:OperatingSegmentProductionEnhancementMember': '생산 개선 · 외부 매출'}, [OPERATING])
for _symbol, _cik in [('CLB', 1958086), ('OII', 73756), ('OIS', 1121484)]:
    _members(_symbol, _cik, PRODUCT, 'product', {
        'us-gaap:ServiceMember': '서비스', 'us-gaap:ProductMember': '제품'})
_members('CLB', 1958086, GEO, 'geography', {
    'country:US': '미국', 'us-gaap:NonUsMember': '미국 외'})

# The original table's external-revenue column uses this consolidation member.
_members('FET', 1401257, SEGMENT, 'segment', {
    'fet:DrillingAndCompletionsSegmentMember': '시추·완결 · 내부거래 제거 후',
    'fet:ArtificialLiftAndDownholeSegmentMember': '인공 채유·다운홀 · 외부 매출'},
    [('srt:ConsolidationItemsAxis', 'srt:ConsolidationEliminationsMember')])
_product_qualifiers = [OPERATING,
    ('us-gaap:ConcentrationRiskByTypeAxis', 'us-gaap:ProductConcentrationRiskMember'),
    ('us-gaap:ConcentrationRiskByBenchmarkAxis', 'us-gaap:SalesMember')]
_members('FET', 1401257, PRODUCT, 'product', {
    'fet:DrillingTechnologiesMember': '시추 기술', 'fet:SubseaTechnologiesMember': '해저 기술',
    'fet:StimulationandInterventionMember': '자극·유정 개입', 'fet:CoiledTubingMember': '코일튜빙',
    'fet:DownholeTechnologiesMember': '다운홀 기술', 'fet:ProductionEquipmentMember': '생산 장비',
    'fet:ValveSolutionsMember': '밸브'}, _product_qualifiers)
COORDINATES['FET', 1401257, frozenset([ELIMINATION, *_product_qualifiers[1:]])] = (
    'product', 'us-gaap:IntersegmentEliminationMember')
LABELS['FET', 1401257, 'us-gaap:IntersegmentEliminationMember'] = '내부거래 제거 · 원문 음수'
_members('FET', 1401257, GEO, 'geography', {
    'country:US': '미국', 'country:CA': '캐나다', 'us-gaap:MiddleEastMember': '중동',
    'fet:EuropeAndAfricaMember': '유럽·아프리카', 'srt:AsiaPacificMember': '아시아·태평양',
    'srt:LatinAmericaMember': '중남미'},
    [('us-gaap:ConcentrationRiskByTypeAxis', 'us-gaap:GeographicConcentrationRiskMember'),
     ('us-gaap:ConcentrationRiskByBenchmarkAxis', 'us-gaap:SalesMember')])
_members('NESR', 1698514, PRODUCT, 'product', {
    'NESR:ProductionServicesMember': '생산 서비스',
    'NESR:DrillingAndEvaluationServicesMember': '시추·평가 서비스'})
_members('NESR', 1698514, GEO, 'geography', {
    'NESR:MENAMember': '중동·북아프리카 MENA', 'NESR:RestOfWorldMember': '기타 지역'})
_members('OII', 73756, SEGMENT, 'segment', {
    'oii:SubseaRoboticsMember': '해저 로봇', 'oii:ManufacturedProductsMember': '제조 제품',
    'oii:OffshoreProjectsGroupMember': '해양 프로젝트',
    'oii:IntegrityManagementDigitalSolutionsMember': '건전성·디지털',
    'oii:AerospaceAndDefenseTechnologiesMember': '항공우주·방산 · 비에너지 포함'})
_members('OII', 73756, GEO, 'geography', {
    'country:US': '미국', 'country:GB': '영국', 'country:BR': '브라질', 'country:NO': '노르웨이',
    'srt:AfricaMember': '아프리카', 'srt:AsiaPacificMember': '아시아·태평양',
    'oii:OtherGeographicalMemberMember': '기타 지역'})
_ois_segments = {'ois:OffshoreManufacturedProductsMember': '해상 제조 제품',
    'ois:CompletionAndProductionServicesMember': '완결·생산 서비스',
    'ois:DownholeTechnologiesMember': '다운홀 기술'}
_members('OIS', 1121484, SEGMENT, 'segment', _ois_segments, [OPERATING])
_members('OIS', 1121484, SEGMENT, 'segment', _ois_segments)
_members('OIS', 1121484, GEO, 'geography', {
    'country:US': '미국', 'country:GB': '영국', 'country:SG': '싱가포르', 'ois:OtherMember': '기타 지역'})


def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == PERIOD
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def dimensions(pairs, symbol, cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol, cik, frozenset(pairs)))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if not reviewed(dict(start=start, end=end, source=origin), symbol, cik):
        return True
    return tag == ('us-gaap:Revenues' if symbol == 'OII' else CONTRACT)


def signed_value(tag, context, origin, symbol, cik):
    start, end, group, member = context
    return (symbol == 'FET' and cik == 1401257 and tag == CONTRACT
            and (group, member) == ('product', 'us-gaap:IntersegmentEliminationMember')
            and reviewed(dict(start=start, end=end, source=origin), symbol, cik))


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


def annotate(rows, symbol, cik):
    for row in rows:
        if reviewed(row, symbol, cik):
            row['label'] = LABELS.get((symbol, cik, row['member']), row['label'])
            row['parent'] = None
            if symbol == 'FET' and row['group'] == 'product':
                row['share_exclusion'] = '원문 제품 매출에 -502,000 USD 내부거래 제거를 포함합니다. 음수 조정을 제품 시장점유율로 표시하지 않습니다.'
                row['total'] = None
    return rows
