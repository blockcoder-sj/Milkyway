"""Editorial context and fixed source bindings for every display instrument."""
from .market_catalog import BY_ID

GICS = 'https://www.spglobal.com/spdji/en/landing/topic/gics/'
KRX = 'https://data.krx.co.kr/'
DART = 'https://dart.fss.or.kr/'
SEC = 'https://www.sec.gov/edgar/search/'
US_SECTORS = {
    'us_10': ('energy', 'Energy oil gas', '유가·가스 가격, 생산량, 정제마진, 설비투자'),
    'us_15': ('basic-materials', 'Materials chemicals mining', '원자재 가격, 재고, 중국 수요, 제조업 경기'),
    'us_20': ('industrials', 'Industrials aerospace manufacturing', '수주 잔고, 설비투자, 항공·물류 수요, 원가'),
    'us_25': ('consumer-cyclical', 'Consumer discretionary retail autos', '소비지출, 고용, 신용 비용, 자동차·유통 판매'),
    'us_30': ('consumer-defensive', 'Consumer staples food beverages', '판매량, 가격 인상, 원재료·물류 비용, 유통 채널'),
    'us_35': ('healthcare', 'Healthcare pharmaceutical biotech', '임상·인허가, 특허 만료, 보험 급여, 의료 수요'),
    'us_40': ('financial-services', 'Financial banks insurance', '금리 곡선, 대손 비용, 예대마진, 거래·보험 손익'),
    'us_45': ('technology', 'Technology semiconductors software', '반도체 수급, 클라우드·AI 투자, 소프트웨어 매출, 규제'),
    'us_50': ('communication-services', 'Communication services media telecom', '광고 지출, 가입자, 콘텐츠 비용, 플랫폼 규제'),
    'us_55': ('utilities', 'Utilities power electricity', '전력 수요, 요금 규제, 발전 비용, 자본 조달 비용'),
    'us_60': ('real-estate', 'Real estate REIT', '공실률, 임대료, 자본환원율, 차입 만기·금리'),
}
# Representative business examples, not a claim of current index membership/rank.
KR_COMPANIES = {
    'kr_13': [
        ('005930', '삼성전자'),
        ('000660', 'SK하이닉스'),
        ('006400', '삼성SDI'),
        ('066570', 'LG전자'),
        ('009150', '삼성전기'),
        ('011070', 'LG이노텍'),
        ('034220', 'LG디스플레이'),
        ('020150', '롯데에너지머티리얼즈'),
        ('103590', '일진전기'),
        ('010120', 'LS ELECTRIC'),
        ('267260', 'HD현대일렉트릭'),
        ('298040', '효성중공업'),
        ('000990', 'DB하이텍'),
        ('007660', '이수페타시스'),
        ('353200', '대덕전자'),
        ('007810', '코리아써키트'),
        ('008700', '아남전자'),
        ('005680', '삼영전자'),
        ('248070', '솔루엠'),
        ('272210', '한화시스템'),
    ],
    'kr_8': [
        ('051910', 'LG화학'),
        ('051900', 'LG생활건강'),
        ('090430', '아모레퍼시픽'),
        ('011170', '롯데케미칼'),
        ('009830', '한화솔루션'),
        ('010950', 'S-Oil'),
        ('011780', '금호석유화학'),
        ('004000', '롯데정밀화학'),
        ('120110', '코오롱인더'),
        ('003240', '태광산업'),
        ('004430', '송원산업'),
        ('006650', '대한유화'),
        ('002380', 'KCC'),
        ('008730', '율촌화학'),
        ('078520', '에이블씨엔씨'),
        ('161890', '한국콜마'),
        ('192820', '코스맥스'),
        ('003780', '진양산업'),
    ],
    'kr_15': [
        ('005380', '현대차'),
        ('000270', '기아'),
        ('012330', '현대모비스'),
        ('009540', 'HD한국조선해양'),
        ('329180', 'HD현대중공업'),
        ('010140', '삼성중공업'),
        ('042660', '한화오션'),
        ('012450', '한화에어로스페이스'),
        ('064350', '현대로템'),
        ('047810', '한국항공우주'),
        ('011210', '현대위아'),
        ('003620', 'KG모빌리티'),
        ('018880', '한온시스템'),
        ('009680', '모토닉'),
        ('003570', 'SNT다이내믹스'),
        ('064960', 'SNT모티브'),
        ('005850', '에스엘'),
        ('000430', '대원강업'),
    ],
    'kr_19': [
        ('003490', '대한항공'),
        ('011200', 'HMM'),
        ('086280', '현대글로비스'),
        ('000120', 'CJ대한통운'),
        ('020560', '아시아나항공'),
        ('180640', '한진칼'),
        ('002320', '한진'),
        ('028670', '팬오션'),
        ('044450', 'KSS해운'),
        ('005880', '대한해운'),
        ('089590', '제주항공'),
        ('272450', '진에어'),
        ('298690', '에어부산'),
        ('004360', '세방'),
    ],
    'kr_18': [
        ('000720', '현대건설'),
        ('028050', '삼성E&A'),
        ('047040', '대우건설'),
        ('006360', 'GS건설'),
        ('375500', 'DL이앤씨'),
        ('294870', 'HDC현대산업개발'),
        ('013580', '계룡건설'),
        ('009410', '태영건설'),
        ('005960', '동부건설'),
        ('002410', '범양건영'),
        ('000210', 'DL'),
        ('014790', 'HL D&I'),
        ('002780', '진흥기업'),
    ],
    'kr_21': [
        ('105560', 'KB금융'),
        ('055550', '신한지주'),
        ('086790', '하나금융지주'),
        ('316140', '우리금융지주'),
        ('024110', '기업은행'),
        ('138040', '메리츠금융지주'),
        ('138930', 'BNK금융지주'),
        ('139130', 'iM금융지주'),
        ('175330', 'JB금융지주'),
        ('323410', '카카오뱅크'),
        ('006800', '미래에셋증권'),
        ('016360', '삼성증권'),
        ('039490', '키움증권'),
        ('005940', 'NH투자증권'),
        ('032830', '삼성생명'),
        ('000810', '삼성화재'),
        ('005830', 'DB손해보험'),
        ('001450', '현대해상'),
        ('071050', '한국금융지주'),
        ('029780', '삼성카드'),
    ],
    'kr_24': [
        ('006800', '미래에셋증권'),
        ('016360', '삼성증권'),
        ('039490', '키움증권'),
        ('005940', 'NH투자증권'),
        ('003540', '대신증권'),
        ('030210', '다올투자증권'),
        ('001200', '유진투자증권'),
        ('003470', '유안타증권'),
        ('001720', '신영증권'),
        ('001510', 'SK증권'),
        ('001270', '부국증권'),
        ('001290', '상상인증권'),
        ('016610', 'DB증권'),
        ('001750', '한양증권'),
        ('001500', '현대차증권'),
    ],
    'kr_25': [
        ('032830', '삼성생명'),
        ('000810', '삼성화재'),
        ('005830', 'DB손해보험'),
        ('001450', '현대해상'),
        ('082640', '동양생명'),
        ('088350', '한화생명'),
        ('000370', '한화손해보험'),
        ('003690', '코리안리'),
        ('000400', '롯데손해보험'),
    ],
}
KR_TOPICS = {
    'kr_13': '반도체 전기전자', 'kr_8': '화학 화장품', 'kr_15': '자동차 조선',
    'kr_19': '해운 항공 물류', 'kr_18': '건설 수주', 'kr_21': '금융 은행',
    'kr_24': '증권 자본시장', 'kr_25': '보험 손해율',
}
INDEX_SOURCES = {
    'sp500': ('S&P DJI · S&P 500', 'https://www.spglobal.com/spdji/en/indices/equity/sp-500/', '미국 대형주를 유동주식 시가총액 가중 방식으로 반영하는 지수입니다.'),
    'dow': ('S&P DJI · Dow Jones', 'https://www.spglobal.com/spdji/en/indices/equity/dow-jones-industrial-average/', '주요 30개 기업을 주가 가중 방식으로 반영하는 지수입니다.'),
    'nasdaq': ('Nasdaq · Composite', 'https://indexes.nasdaq.com/Index/Overview/COMP', '나스닥 상장 종목을 폭넓게 포함하는 시가총액 가중 지수입니다.'),
    'nasdaq100': ('Nasdaq · Nasdaq-100', 'https://indexes.nasdaq.com/Index/Overview/NDX', '나스닥의 주요 비금융 기업을 수정 시가총액 가중 방식으로 반영합니다.'),
    'russell2000': ('FTSE Russell · US Indexes', 'https://www.lseg.com/en/ftse-russell/indices/russell-us', '미국 소형주를 시가총액 가중 방식으로 반영하는 지수입니다.'),
    'vix': ('Cboe · VIX', 'https://www.cboe.com/tradable_products/vix/', 'S&P 500 옵션에 반영된 향후 약 30일의 기대 변동성입니다. 주가 수익률이나 방향 예측값이 아닙니다.'),
}
FUTURE_SOURCES = {
    'sp500_future': ('CME · E-mini S&P 500','https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.html'),
    'nasdaq_future': ('CME · E-mini Nasdaq-100','https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.html'),
    'gold': ('COMEX · Gold','https://www.cmegroup.com/markets/metals/precious/gold.html'),
    'oil': ('NYMEX · WTI','https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html'),
}


# Separate price series: these ETFs have a different investment universe/weighting
# from the displayed sector index. Never splice or relabel them as that index.
RELATED_ETFS = {
    **dict(zip(US_SECTORS, [(symbol, 'Select Sector SPDR '+symbol) for symbol in
        ('XLE','XLB','XLI','XLY','XLP','XLV','XLF','XLK','XLC','XLU','XLRE')])),
    'kospi200':('069500.KS','KODEX 200'),
    'kr_13':('091160.KS','KODEX 반도체'), 'kr_8':('117460.KS','KODEX 에너지화학'),
    'kr_15':('091180.KS','KODEX 자동차'), 'kr_19':('140710.KS','KODEX 운송'),
    'kr_18':('117700.KS','KODEX 건설'), 'kr_21':('091170.KS','KODEX 은행'),
    'kr_24':('102970.KS','KODEX 증권'), 'kr_25':('140700.KS','KODEX 보험'),
}
NEWS_QUERIES = {
    'sp500':'"S&P 500"', 'dow':'"Dow Jones"', 'nasdaq':'"Nasdaq Composite"',
    'nasdaq100':'"Nasdaq 100"', 'russell2000':'"Russell 2000"', 'vix':'"VIX" volatility',
    'usdkrw':'원달러 환율', 'jpykrw':'엔화 환율', 'eurkrw':'유로 환율',
    'usdjpy':'yen dollar', 'eurusd':'euro dollar', 'gold':'gold price', 'oil':'WTI oil price',
    'sp500_future':'"S&P 500" futures', 'nasdaq_future':'"Nasdaq" futures',
}
SECTOR_NEWS_QUERIES = {
    'us_10':'oil OR gas OR "energy stocks"',
    'us_15':'mining OR chemicals OR "materials stocks"',
    'us_20':'manufacturing OR aerospace OR "industrial stocks"',
    'us_25':'retail OR automakers OR "consumer discretionary"',
    'us_30':'"food companies" OR "beverage companies" OR "consumer staples"',
    'us_35':'pharmaceutical OR biotech OR "healthcare stocks"',
    'us_40':'"bank stocks" OR insurers OR "financial services"',
    'us_45':'semiconductor OR software OR "technology stocks" OR Nvidia OR Apple OR Microsoft',
    'us_50':'telecom OR "media companies" OR "social media"',
    'us_55':'"electric utilities" OR "power companies" OR "utility stocks"',
    'us_60':'REIT OR "commercial real estate" OR "property companies"',
}
INDEX_METHODS = {
    'sp500':'유동주식 시가총액 가중 · 미국 대형주', 'dow':'주가 가중 · 주요 30개 기업',
    'nasdaq':'시가총액 가중 · 나스닥 상장 종목', 'nasdaq100':'수정 시가총액 가중 · 주요 비금융 기업',
    'russell2000':'시가총액 가중 · 미국 소형주', 'vix':'S&P 500 옵션에서 산출한 약 30일 기대 변동성',
    'kospi':'시가총액 가중 · 유가증권시장', 'kosdaq':'시가총액 가중 · 코스닥시장',
    'kospi200':'유동주식 시가총액 가중 · 대표 200종목',
}

def source(label, url, kind):
    return {'label':label,'url':url,'kind':kind}


def context_for(identity):
    instrument = BY_ID[identity]
    sources = [source('Yahoo Finance · 시세와 과거 차트',instrument.source_url,'시세')]
    result = {'intro':instrument.description,'watchpoints':[], 'sources':sources,
              'news_query':instrument.label, 'companies_note':'', 'market_share':[]}
    if identity in US_SECTORS:
        slug, query, points = US_SECTORS[identity]
        result.update(news_query=query, watchpoints=points.split(', '), sector_slug=slug,
            companies_note='기업별로 공식 운용사 구성·섹터 공시와 대조합니다. 확인된 불일치는 해당 섹터로 이동하고 공시에 있는 기업을 보완합니다. 미확인 기업은 Yahoo 분류로 표시합니다. S&P 500 구성 종목 전체·공식 지수 비중·GICS 전체 원장 직접 검증과 구분합니다.')
        sources.extend([source('S&P DJI · GICS 분류',GICS,'분류'),
            source('Yahoo Finance · 섹터 기업 목록',f'https://finance.yahoo.com/sectors/{slug}/','기업'),
            source('SEC EDGAR · 기업 공시',SEC,'공시')])
    elif identity in KR_COMPANIES:
        result.update(news_query=KR_TOPICS[identity], watchpoints=['분기 실적과 매출 구성','신규 수주·판매량','원가와 금리·환율','정책·규제 변화'],
            companies_note='업종 이해를 위한 대표 기업 예시입니다. 시총 순위나 현재 지수 편입 전체 목록이 아닙니다.')
        sources.extend([source('KRX · 지수·업종 원자료',KRX,'지수'),source('DART · 사업보고서·분기 공시',DART,'공시')])
    elif identity in INDEX_SOURCES:
        label,url,intro=INDEX_SOURCES[identity]
        result.update(intro=intro,watchpoints=['공식 구성 종목·산출 방법','대형 종목 집중도','업종별 기여와 시장 폭','정기 구성 변경'])
        sources.append(source(label,url,'산출기관'))
    elif identity in {'kospi','kosdaq','kospi200'}:
        result.update(watchpoints=['지수 산출 방식과 편입 종목','업종별 시총 집중도','외국인·기관 수급','정기 편입 변경'])
        sources.extend([source('KRX · 지수·구성 정보',KRX,'산출기관'),source('DART · 기업 공시',DART,'공시')])
    elif instrument.group == 'fx':
        result.update(intro=instrument.description+' 기준의 참고 환율입니다. 실제 환전 매수·매도 환율과 차이가 있습니다.',
            watchpoints=['두 통화의 정책금리 차이','물가·고용·성장 지표','중앙은행 발표','무역·자본 흐름'],news_query=instrument.symbol+' exchange rate')
        sources.extend([source('한국은행 · 통화정책', 'https://www.bok.or.kr/','중앙은행'),
            source('Federal Reserve · 정책 발표','https://www.federalreserve.gov/newsevents/pressreleases.htm','중앙은행'),
            source('ECB · 통화정책','https://www.ecb.europa.eu/mopo/html/index.en.html','중앙은행'),
            source('Bank of Japan · 통화정책','https://www.boj.or.jp/en/mopo/','중앙은행')])
    elif identity in FUTURE_SOURCES:
        label,url=FUTURE_SOURCES[identity]
        result.update(watchpoints=['계약 명세·거래 시간','만기와 최근월 교체','현물 대비 가격 차이','거래량과 경제지표'],
                      intro=instrument.description+'입니다. 최근월 교체로 장기 차트에 단절이 생길 수 있으며, 실제 선물 보유 수익률과 다릅니다.')
        sources.append(source(label,url,'거래소'))
    if instrument.market=='kr' or identity in {'usdkrw','jpykrw','eurkrw'}:
        result['news_locale']='ko'
    if identity in KR_TOPICS:
        result['news_query']=' OR '.join(KR_TOPICS[identity].split())
    if identity in NEWS_QUERIES:
        result['news_query']=NEWS_QUERIES[identity]
    if identity in US_SECTORS:
        result['news_query']=SECTOR_NEWS_QUERIES[identity]
    result['facts']=[{'label':'표시 단위','value':instrument.unit},
        {'label':'식별 기호','value':instrument.symbol},
        {'label':'과거 시세','value':'최대 3년 · 제공되는 구간만 표시'}]
    if identity in INDEX_METHODS:
        result['facts'].insert(0,{'label':'산출 방식·범위','value':INDEX_METHODS[identity]})
    if identity=='vix':
        result['watchpoints']=['옵션에 반영된 기대 변동성','만기별 변동성 차이','주가와의 동반 움직임','VIX 지수와 선물의 가격 차이']
    if identity in RELATED_ETFS:
        symbol,label=RELATED_ETFS[identity]
        url='https://finance.yahoo.com/quote/'+symbol+'/'
        issuer=('https://www.ssga.com/mainfund/'+symbol if instrument.market=='us' else
                'https://www.samsungfund.com/etf/search.do?searchText='+symbol[:6])
        result['related_chart']={'symbol':symbol,'label':label,'unit':'USD' if instrument.market=='us' else 'KRW',
            'note':'관련 ETF의 가격 흐름입니다. 표시 지수와 편입 범위·가중 방식이 다르며, 지수 가격이나 총수익률이 아닙니다.', 'url':url}
        sources.extend([source(label+' · 과거 시세',url,'관련 ETF'),source(label+' · 운용사',issuer,'상품 원문')])
    if identity in {'us_45','kr_13'}:
        result['market_share'] = [{'title':'글로벌 파운드리 매출 점유율', 'period':'2026년 2분기',
            'published_at':'2026-09-09','checked_at':'2026-09-30','provider':'TrendForce',
            'url':'https://www.trendforce.com/presscenter/news/20260909-13225.html',
            'scope':'파운드리 사업 매출 기준. 정보기술 전체·반도체 전체 점유율이 아닙니다. 발표 자료를 수동 확인한 값입니다.',
            'values':[{'name':'TSMC','value':72.5},{'name':'Samsung Foundry','value':5.9},{'name':'SMIC','value':5.4},{'name':'UMC','value':3.9},{'name':'GlobalFoundries','value':3.2}]}]
    return result
