"""Bounded public history, company snapshots and attributed news for display."""
import datetime as dt
import email.utils
import math
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlsplit
from zoneinfo import ZoneInfo

from .bounded_io import read_requests_json, read_requests_bytes
from .market_broker_feed import FixedSession
from .market_catalog import BY_ID, Instrument
from .market_detail_catalog import context_for, KR_COMPANIES, RELATED_ETFS

UTC = dt.timezone.utc
ENGLISH_NEWS_HOSTS = {'reuters.com','bloomberg.com','apnews.com','ft.com','wsj.com','cnbc.com','finance.yahoo.com','marketwatch.com','barrons.com','investors.com','nytimes.com','bbc.com','bbc.co.uk','cnn.com','aljazeera.com','theguardian.com','economist.com','washingtonpost.com','abcnews.go.com','nbcnews.com','cbsnews.com','scmp.com','nikkei.com'}
KOREAN_NEWS_HOSTS = {'yna.co.kr','yonhapnewstv.co.kr','hankyung.com','mk.co.kr','reuters.com','kbs.co.kr','news.kbs.co.kr','newsis.com','news1.kr','chosun.com','donga.com','edaily.co.kr','sedaily.com','etnews.com','sbs.co.kr','imbc.com'}
NEWS_LIMIT = 400
NEWS_DAYS = 30
NEWS_SELECTION_VERSION = 3
COMPANY_PAGE_SIZE = 100
COMPANY_LIMIT = 1000


def number(value, *, positive=True):
    if isinstance(value,bool):
        raise ValueError('Boolean price')
    value=float(value)
    if not math.isfinite(value) or abs(value)>1e16 or (positive and value<=0):
        raise ValueError('Invalid number')
    return value


def years_ago(now):
    try:
        return now.replace(year=now.year-3)
    except ValueError:
        return now.replace(year=now.year-3,day=28)


def get_json(url, params=None):
    with FixedSession() as session:
        response=session.get(url,params=params,headers={'User-Agent':'MilkywayPersonal/1.0'},timeout=(3,7),stream=True)
        try:
            response.raise_for_status()
            return read_requests_json(response,maximum_bytes=1024*1024)
        finally:
            response.close()


def parse_history(payload, instrument, now):
    results=payload['chart']['result']
    if payload['chart'].get('error') or not isinstance(results,list) or len(results)!=1:
        raise ValueError('No history')
    row=results[0]; meta=row['meta']
    expected={'indices':'INDEX','sectors':'INDEX','fx':'CURRENCY','futures':'FUTURE','commodities':'FUTURE','etf':'ETF'}[instrument.group]
    if meta.get('symbol')!=instrument.symbol or meta.get('instrumentType')!=expected:
        raise ValueError('Wrong history instrument')
    zone=ZoneInfo(meta['exchangeTimezoneName'])
    times=row.get('timestamp',[])
    if len(times)>1200:
        raise ValueError('Too many bars')
    columns=row['indicators']['quote'][0]
    bars=[]; outside=0; rejected=0; close_only=0
    for index, stamp in enumerate(times):
        try:
            stamp=number(stamp)
            when=dt.datetime.fromtimestamp(stamp,UTC)
            if not years_ago(now)<=when<=now:
                outside+=1
                continue
            close=number(number(columns['close'][index])*instrument.multiplier)
            values={'open':None,'high':None,'low':None,'close':close}
            try:
                ohlc={name:number(number(columns[name][index])*instrument.multiplier) for name in ('open','high','low')}
                if ohlc['high']<max(ohlc['open'],close,ohlc['low']) or ohlc['low']>min(ohlc['open'],close):
                    raise ValueError('Inconsistent OHLC')
                values.update(ohlc)
            except (ValueError,TypeError,IndexError,KeyError):
                close_only+=1
            volume=columns.get('volume',[])
            try:
                volume=number(volume[index],positive=False) if index<len(volume) and volume[index] is not None else None
                if volume is not None and volume<0:volume=None
            except (ValueError,TypeError,IndexError):
                volume=None
            bars.append({'date':when.astimezone(zone).date().isoformat(),**values,'volume':volume})
        except (ValueError,TypeError,IndexError,KeyError,OverflowError,OSError):
            rejected+=1
    duplicate_count=len(bars)-len({bar['date'] for bar in bars})
    bars=list({bar['date']:bar for bar in bars}.values())
    bars.sort(key=lambda bar:bar['date'])
    if not bars:
        raise ValueError('No valid history')
    return {'rows':bars,'fetched_at':now.isoformat(),'source':'Yahoo Finance','error':None,
            'quality':{'received':len(times),'outside_range':outside,'invalid_close':rejected,
                       'close_only':close_only,'duplicates':duplicate_count,'accepted':len(bars)}}


def history(instrument):
    now=dt.datetime.now(UTC)
    payload=get_json('https://query1.finance.yahoo.com/v8/finance/chart/'+quote(instrument.symbol,safe=''),
                     {'period1':int(years_ago(now).timestamp()),'period2':int(now.timestamp()),'interval':'1d'})
    return parse_history(payload,instrument,now)


def parse_us_companies(payload, now):
    results=payload['finance']['result']
    if not isinstance(results,list) or len(results)!=1:
        raise ValueError('No company screen')
    quotes=results[0]['quotes']
    if not isinstance(quotes,list) or len(quotes)>COMPANY_LIMIT:
        raise ValueError('Too many companies')
    rows=[]
    for row in quotes:
        try:
            symbol=row['symbol']
            if not isinstance(symbol,str) or not re.fullmatch(r'[A-Z0-9.^=-]{1,20}',symbol) or row.get('currency')!='USD':
                continue
            rows.append({'symbol':symbol,'name':str(row.get('shortName') or row.get('longName') or symbol)[:120],
                'market_cap':number(row['marketCap']),'currency':'USD',
                'source':'Yahoo Finance','url':'https://finance.yahoo.com/quote/'+quote(symbol,safe='')+'/'})
        except (ValueError,KeyError,TypeError):
            continue
    if not rows:
        raise ValueError('No valid companies')
    return company_snapshot(rows,now)


def company_snapshot(rows,now):
    rows=list({row['symbol']:row for row in rows}.values())
    total=sum(row['market_cap'] for row in rows if row.get('market_cap') is not None)
    complete=bool(rows) and all(row.get('market_cap') is not None for row in rows)
    for row in rows:
        row['displayed_share_pct']=row['market_cap']/total*100 if complete and total>0 else None
    return {'rows':rows,'fetched_at':now.isoformat(),'error':None if complete else '일부 기업의 시총 미수신 · 비중 계산 보류'}


def parse_kr_cap(value):
    found=re.fullmatch(r'(?:(\d[\d,]*)조\s*)?(?:(\d[\d,]*)억)?',value.strip())
    if not found or not any(found.groups()):
        raise ValueError('Unknown Korean cap unit')
    return number(int((found[1] or '0').replace(',',''))*1e12+int((found[2] or '0').replace(',',''))*1e8)


def companies(identity):
    now=dt.datetime.now(UTC); context=context_for(identity)
    if context.get('sector_slug'):
        params={'scrIds':'sec-ind_sec-largest-equities_'+context['sector_slug'],'count':COMPANY_PAGE_SIZE}
        first=get_json('https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved',params)
        initial=parse_us_companies(first,now)
        screen=first['finance']['result'][0]
        total=screen.get('total',len(initial['rows']))
        if isinstance(total,bool) or not isinstance(total,int) or total<0:raise ValueError('Invalid screen total')
        def page(offset):
            payload=get_json('https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved',{**params,'start':offset})
            if payload['finance']['result'][0].get('start')!=offset:raise ValueError('Screen offset mismatch')
            return parse_us_companies(payload,now)['rows']
        rows=initial['rows'];failed=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in [pool.submit(page,n) for n in range(COMPANY_PAGE_SIZE,min(total,COMPANY_LIMIT),COMPANY_PAGE_SIZE)]:
                try:rows.extend(future.result())
                except Exception:failed=True
        result=company_snapshot(rows,now)
        if failed:result['error']='일부 기업 페이지 수신 실패 · 수신한 기업 기준 비중'
        elif total>COMPANY_LIMIT:result['error']='기업 목록은 시가총액 상위 1,000개까지 수집합니다'
        return result
    if identity not in KR_COMPANIES:
        return {'rows':[],'fetched_at':now.isoformat(),'error':None}
    def korean_company(pair):
        code,name=pair
        row={'symbol':code+'.KS','name':name,'market_cap':None,'currency':'KRW','source':'Npay 증권',
             'url':f'https://m.stock.naver.com/domestic/stock/{code}/total'}
        try:
            payload=get_json(f'https://m.stock.naver.com/api/stock/{code}/integration')
            if payload.get('itemCode')!=code:raise ValueError('Wrong company')
            infos=payload.get('totalInfos',[])
            if not isinstance(infos,list) or len(infos)>100:raise ValueError('Invalid company response')
            row['market_cap']=parse_kr_cap(next(item['value'] for item in infos if item.get('code')=='marketValue'))
            row['name']=str(payload.get('stockName') or name)[:120]
        except Exception:pass
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(korean_company,KR_COMPANIES[identity]))
    return company_snapshot(rows,now)


def safe_news_url(url):
    if not isinstance(url,str) or len(url)>2000:
        return False
    try:
        parsed=urlsplit(url)
        return parsed.scheme=='https' and parsed.hostname in {'finance.yahoo.com','news.google.com'} and not parsed.username and not parsed.password and parsed.port in (None,443)
    except ValueError:
        return False


def parse_news_rss(raw,now,allowed_hosts=KOREAN_NEWS_HOSTS):
    if len(raw)>256*1024 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Unsafe news XML')
    root=ET.fromstring(raw)
    rows=[]
    for item in root.findall('./channel/item')[:100]:
        try:
            src=item.find('source')
            if src is None:
                continue
            host=urlsplit(src.attrib.get('url','')).hostname or ''
            if not any(host==domain or host.endswith('.'+domain) for domain in allowed_hosts):
                continue
            when=email.utils.parsedate_to_datetime(item.findtext('pubDate'))
            title=item.findtext('title'); url=item.findtext('link')
            if not isinstance(title,str) or not 1<=len(title)<=300 or not safe_news_url(url):
                continue
            if when.tzinfo is None or not now-dt.timedelta(days=NEWS_DAYS)<=when<=now+dt.timedelta(minutes=5):
                continue
            rows.append({'title':title,'publisher':(src.text or host)[:80],'url':url,'published_at':when.astimezone(UTC).isoformat()})
        except (ValueError,TypeError,AttributeError):
            continue
    return rows


def merge_news(rows, now):
    """A bounded, deduplicated rolling month, sorted by timestamp rather than page."""
    valid=[row for row in rows if now-dt.timedelta(days=NEWS_DAYS)<=dt.datetime.fromisoformat(row['published_at'].replace('Z','+00:00'))<=now+dt.timedelta(minutes=5)]
    unique=list({row['url']:row for row in valid}.values())
    unique.sort(key=lambda row:(dt.datetime.fromisoformat(row['published_at'].replace('Z','+00:00')),row['url']),reverse=True)
    return unique[:NEWS_LIMIT]


def news_title_matches(title,query,identity):
    """A headline scope check; indexed article-body matches alone are insufficient."""
    extras={
        'us_45':['tech','AI','OpenAI','Anthropic','chip','chips','cloud','GPU','Micron','HPE','quantum'],
        'us_10':['energy','petroleum','OPEC','refinery','Exxon','Chevron'],
        'us_15':['metals','copper','steel','lithium','aluminium','Linde'],
        'us_20':['industrial','logistics','airlines','Boeing','Caterpillar'],
        'us_25':['automotive','Tesla','Amazon','Ford','retailer'],
        'us_30':['food','beverage','Walmart','Costco','Coca-Cola','Pepsi'],
        'us_35':['healthcare','medical','FDA','Moderna','Pfizer','Eli Lilly'],
        'us_40':['bank','insurance','JPMorgan','Goldman Sachs','Morgan Stanley'],
        'us_50':['telecom','media','Netflix','Alphabet','Meta','Disney'],
        'us_55':['utilities','electricity','Duke Energy','NextEra'],
        'us_60':['real estate','property','Prologis','REITs'],
    }
    clauses=re.split(r'\s+OR\s+',query)
    terms=[(re.findall(r'"([^"]+)"',clause) or [clause.strip().split()[0]])[0] for clause in clauses]
    for term in terms+extras.get(identity,[]):
        if term.isascii():
            parts=re.findall(r'[A-Za-z0-9]+',term)
            pattern=r'(?<![A-Za-z0-9])'+r'[^A-Za-z0-9]*'.join(map(re.escape,parts))+r'(?![A-Za-z0-9])'
            if parts and re.search(pattern,title,re.IGNORECASE):return True
        elif re.sub(r'\W','',term.casefold()) in re.sub(r'\W','',title.casefold()):return True
    return False


def news(instrument):
    context=context_for(instrument.id); now=dt.datetime.now(UTC)
    korean=context.get('news_locale')=='ko'
    hosts=KOREAN_NEWS_HOSTS if korean else ENGLISH_NEWS_HOSTS
    groups=[sorted(hosts)[start:start+6] for start in range(0,len(hosts),6)]
    def window(index,publishers):
        sites=' OR '.join('site:'+host for host in publishers)
        start=(now-dt.timedelta(days=min(NEWS_DAYS,(index+1)*8))).date()
        end=(now-dt.timedelta(days=index*8)).date()+dt.timedelta(days=1)
        with FixedSession() as session:
            response=session.get('https://news.google.com/rss/search',params={
                'q':'('+context['news_query']+') ('+sites+') after:'+start.isoformat()+' before:'+end.isoformat(),
                'hl':'ko' if korean else 'en-US','gl':'KR' if korean else 'US','ceid':'KR:ko' if korean else 'US:en'},
                headers={'User-Agent':'MilkywayPersonal/1.0'},timeout=(3,7),stream=True)
            try:
                response.raise_for_status()
                return parse_news_rss(read_requests_bytes(response,maximum_bytes=256*1024),now,hosts)
            finally:
                response.close()
    rows=[]; failures=0
    # Keep publisher expressions small: oversized Google queries can return a
    # generic publisher feed. Time windows preserve older indexed headlines.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(window,index,publishers) for index in range(4) for publishers in groups]
        for future in futures:
            try: rows.extend(future.result())
            except Exception: failures+=1
    if failures==len(futures): raise ValueError('No news window received')
    return {'rows':merge_news([row for row in rows if news_title_matches(row['title'],context['news_query'],instrument.id)],now),'fetched_at':now.isoformat(),'source':'Google News · 지정 언론사 · 제목 키워드',
            'selection_version':NEWS_SELECTION_VERSION,
            'error':'일부 기간·언론사의 뉴스 수집 실패 · 수신된 기사만 표시' if failures else None}


def related_history(instrument):
    if instrument.id not in RELATED_ETFS:
        return {'rows':[],'error':None}
    symbol,label=RELATED_ETFS[instrument.id]
    return history(Instrument(instrument.id,label,symbol,instrument.market,'etf',label))


def collect_detail(payload,_configuration):
    instrument=BY_ID[payload['id']]
    def safely(kind):
        try:
            return {'history':lambda:history(instrument),'companies':lambda:companies(instrument.id),'news':lambda:news(instrument),'related_history':lambda:related_history(instrument)}[kind]()
        except Exception:
            return {'error':'원자료 수신·검증에 실패했습니다'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(zip(('history','companies','news','related_history'),pool.map(safely,('history','companies','news','related_history'))))
