"""Reviewed Canadian annual coordinates; royalties and internal sales stay visible."""

COORDINATES = {}
LABELS = {}
DOCUMENTS = {
    ('SU',311337):'https://www.sec.gov/Archives/edgar/data/311337/000110465926020411/su-20251231xex99d2.htm',
    ('CNQ',1017413):'https://www.sec.gov/Archives/edgar/data/1017413/000101741326000018/cnq-20251231.htm',
    ('IMO',49938):'https://www.sec.gov/Archives/edgar/data/49938/000004993826000009/imo-20251231.htm',
    ('CVE',1475260):'https://www.sec.gov/Archives/edgar/data/1475260/000147526026000008/cve-20251231.htm',
    ('OBE',1334388):'https://www.sec.gov/Archives/edgar/data/1334388/000119312526058652/obe-ex99_3.htm',
    ('BTE',1279495):'https://www.sec.gov/Archives/edgar/data/1279495/000127949526000007/bte-20251231_d2.htm',
    ('VET',1293135):'https://www.sec.gov/Archives/edgar/data/1293135/000110465926023553/vet-20251231xex99d3.htm',
    ('PDS',1013605):'https://www.sec.gov/Archives/edgar/data/1013605/000101360526000014/pds-ex99_3.htm',
}


def _add(symbol,cik,pairs,group,member,label):
    COORDINATES[symbol,cik,frozenset(pairs)] = group,member
    LABELS[symbol,cik,member] = label


QUALIFIER = ('ifrs-full:SegmentConsolidationItemsAxis','ifrs-full:OperatingSegmentsMember')
for (symbol,cik),members in {
    ('SU',311337):{'su:OilSandsSegmentMember':'오일샌드 · 채굴·열회수·개질',
                  'su:ExplorationAndProductionSegmentMember':'탐사·생산 · 해상 등',
                  'su:RefiningAndMarketingSegmentMember':'정유·판매'},
    ('CNQ',1017413):{'cnq:NorthAmericaExplorationAndProductionSegmentMember':'북미 탐사·생산',
                    'cnq:NorthSeaExplorationAndProductionSegmentMember':'북해 탐사·생산',
                    'cnq:OffshoreAfricaExplorationAndProductionSegmentMember':'아프리카 해상 탐사·생산',
                    'cnq:OilSandsMiningAndUpgradingSegmentMember':'오일샌드 채굴·개질',
                    'cnq:MidstreamAndRefiningSegmentMember':'중류·정유'},
}.items():
    for member,label in members.items():
        _add(symbol,cik,[QUALIFIER,('ifrs-full:SegmentsAxis',member)],'segment',member,label)
_add('CNQ',1017413,[('ifrs-full:SegmentConsolidationItemsAxis','cnq:EliminationOfIntersegmentAmountsAndOtherMember')],
     'segment','cnq:EliminationOfIntersegmentAmountsAndOtherMember','내부 거래 제거·기타 영업 · 순액')

for member,label in {'imo:UpstreamMember':'상류 · 생산','imo:DownstreamMember':'하류 · 정유·판매',
                     'imo:ChemicalMember':'화학'}.items():
    _add('IMO',49938,[('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember'),
                     ('us-gaap:StatementBusinessSegmentsAxis',member)],'segment',member,label)
_add('IMO',49938,[('srt:ConsolidationItemsAxis','us-gaap:CorporateNonSegmentMember')],
     'segment','us-gaap:CorporateNonSegmentMember','본사·기타')

for parent,members in {
    'cve:UpstreamMember':{'cve:OilSandsSegmentMember':'오일샌드','cve:ConventionalSegmentMember':'일반 육상 원유·가스',
                          'cve:OffshoreMember':'해상 생산'},
    'cve:DownstreamMember':{'cve:CanadianRefiningMember':'캐나다 정유·개질','cve:USRefiningMember':'미국 정유'},
}.items():
    for member,label in members.items():
        _add('CVE',1475260,[('srt:ProductOrServiceAxis',parent),('ifrs-full:SegmentsAxis',member)],
             'segment',member,label)
    LABELS['CVE',1475260,parent] = '상류 사업 소계' if parent=='cve:UpstreamMember' else '하류 사업 소계'

# Suncor product sales remain qualified by their actual producing segment.
for segment,products in {
    'su:OilSandsSegmentMember':{'su:ScoAndDieselMember':'오일샌드 · 합성원유·디젤','su:BitumenMember':'오일샌드 · 비투멘'},
    # The issuer's visible table says crude oil and NGL despite this XML name.
    'su:ExplorationAndProductionSegmentMember':{'su:NaturalGasMember':'탐사·생산 · 원유·NGL'},
    'su:RefiningAndMarketingSegmentMember':{'su:GasolineMember':'정유·판매 · 휘발유','su:DistillateMember':'정유·판매 · 중간유분',
                                           'su:OtherProductAndServicesMember':'정유·판매 · 기타 제품·서비스'},
}.items():
    for product,label in products.items():
        _add('SU',311337,[QUALIFIER,('ifrs-full:SegmentsAxis',segment),('ifrs-full:ProductsAndServicesAxis',product)],
             'product',segment+'/'+product,label)

for member,label in {'srt:NorthAmericaMember':'북미','su:OtherForeignCountriesOtherThanThoseInNorthAmericaMember':'북미 외'}.items():
    _add('SU',311337,[('ifrs-full:GeographicalAreasAxis',member)],'geography',member,label)
for member,label in {'country:CA':'캐나다','country:US':'미국','country:CN':'중국'}.items():
    _add('CVE',1475260,[('ifrs-full:GeographicalAreasAxis',member)],'geography',member,label)
for member,label in {'obe:CrudeOilFuelMember':'원유','obe:NaturalGasLiquidMember':'NGL',
                     'srt:NaturalGasReservesMember':'천연가스'}.items():
    _add('OBE',1334388,[('ifrs-full:ProductsAndServicesAxis',member)],'product',member,label)

# Baytex's SegmentsAxis is a product table within continuing Canadian operations.
# Discontinued U.S. sales and anonymous concentration-risk coordinates are omitted.
for member,label in {'bte:LightOilandCondensateMember':'경질유·콘덴세이트','bte:HeavyOilPropertiesMember':'중질유',
                     'bte:NGLMember':'NGL','bte:NaturalGasMember':'천연가스'}.items():
    _add('BTE',1279495,[('ifrs-full:SegmentsAxis',member),('ifrs-full:GeographicalAreasAxis','country:CA')],
         'product',member,label)
_add('BTE',1279495,[('ifrs-full:GeographicalAreasAxis','country:CA')],'geography','country:CA','캐나다 · 계속사업')

for member,label in {'country:CA':'캐나다','country:FR':'프랑스','country:NL':'네덜란드','country:DE':'독일',
                     'country:IE':'아일랜드','country:AU':'호주','vet:CentralAndEasternEuropeMember':'중·동부 유럽'}.items():
    _add('VET',1293135,[('ifrs-full:GeographicalAreasAxis',member),('ifrs-full:SegmentsAxis','ifrs-full:ReportableSegmentsMember')],
         'geography',member,label)
_add('VET',1293135,[('ifrs-full:SegmentConsolidationItemsAxis','ifrs-full:UnallocatedAmountsMember'),
                  ('ifrs-full:SegmentsAxis','ifrs-full:ReportableSegmentsMember')],
     'geography','ifrs-full:UnallocatedAmountsMember','기업 공통·지역 미배분 매출')

for member,label in {'pds:ContractDrillingServicesSegmentMember':'계약 시추','pds:CompletionAndProductionServicesSegmentMember':'완결·생산 서비스'}.items():
    _add('PDS',1013605,[('pds:SegmentConsolidationAxis',member)],'segment',member,label)
for member,label in {'country:CA':'캐나다','country:US':'미국','pds:InternationalSegmentMember':'미국·캐나다 외'}.items():
    _add('PDS',1013605,[('ifrs-full:GeographicalAreasAxis',member)],'geography',member,label)
for member,label in {'pds:DayRateOrHourlyServicesMember':'일당·시간당 서비스',
                     'pds:ShortfallPaymentsOrIdleButContractedMember':'계약 부족분·대기 보상',
                     'pds:OtherServicesMember':'기타 서비스'}.items():
    _add('PDS',1013605,[('ifrs-full:ProductsAndServicesAxis',member)],'product',member,label)


def dimensions(pairs,symbol,cik):
    if len(set(pairs)) != len(pairs):
        return None
    return COORDINATES.get((symbol,cik,frozenset(pairs)))


def reviewed(row,symbol,cik):
    return (row['start']=='2025-01-01' and row['end']=='2025-12-31'
            and row['source']['url'].split('#')[0]==DOCUMENTS.get((symbol,cik)))


def annotate(rows,symbol,cik):
    explanations = {
        'SU':'부문·제품 매출은 내부 거래를 포함합니다. 부문 합계 60,504,000,000 CAD에서 내부 거래 8,127,000,000 CAD를 제거한 고객 계약 총매출은 52,377,000,000 CAD입니다. 여기서 로열티 3,469,000,000 CAD를 차감하며 기타소득 402,000,000 CAD는 별도입니다.',
        'CNQ':'부문 거래를 포함한 다섯 영업 부문의 로열티 차감 후 매출 합계는 37,686,000,000 CAD입니다. 내부 거래 제거·기타 영업 순액 +1,076,000,000 CAD를 합쳐 연결 매출 38,762,000,000 CAD가 됩니다. 기타 영업을 전부 음수 내부 거래로 취급하지 않습니다.',
        'IMO':'부문·본사 수익 합계 69,482,000,000 CAD에서 내부 거래 22,404,000,000 CAD를 제거한 매출·기타소득 합계는 47,078,000,000 CAD입니다. 매출 46,918,000,000 CAD와 기타소득 160,000,000 CAD의 합계이며 부과세 포함 고객 계약 매출 38,678,000,000 CAD는 별도입니다.',
        'CVE':'부문 매출 합계 58,637,000,000 CAD에서 본사·내부 거래 제거 8,941,000,000 CAD를 차감하면 연결 매출 49,696,000,000 CAD입니다. 상·하류 소계와 개별 부문을 합쳐 중복 계산하지 않습니다.',
        'PDS':'두 부문 매출 합계 1,854,854,000 CAD에서 내부 거래 11,150,000 CAD를 차감하면 연결 매출 1,843,704,000 CAD입니다. 제품별 서비스·지역 표는 이 제거 후 연결 기준입니다.',
    }
    for row in rows:
        if not reviewed(row,symbol,cik):
            continue
        if ((symbol in {'SU','CVE'} and row['group'] in {'segment','product'})
                or (symbol in {'CNQ','IMO','PDS'} and row['group']=='segment')):
            row['includes_intersegment'],row['total'] = True,None
            row['share_exclusion'] = explanations[symbol]
        # OBE products, BTE continuing sales and VET countries already have an
        # exact same-metric denominator. Their accounting notes live beside the
        # financial table, without suppressing valid sales composition ratios.
    return rows


def presentation_group(row,symbol,cik):
    if reviewed(row,symbol,cik):
        for (issuer,identity,_),(group,member) in COORDINATES.items():
            if (issuer,identity,member)==(symbol,cik,row['member']):
                return group
    return row['group']
