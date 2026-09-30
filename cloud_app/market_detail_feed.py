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
ENGLISH_NEWS_HOSTS = {'reuters.com','bloomberg.com','apnews.com','ft.com','wsj.com','cnbc.com','finance.yahoo.com','marketwatch.com','barrons.com','investors.com'}
KOREAN_NEWS_HOSTS = {'yna.co.kr','yonhapnewstv.co.kr','hankyung.com','mk.co.kr','reuters.com','kbs.co.kr','news.kbs.co.kr'}


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
            return read_requests_json(response,maximum_bytes=512*1024)
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
    bars=[]
    for index, stamp in enumerate(times):
        try:
            stamp=number(stamp)
            when=dt.datetime.fromtimestamp(stamp,UTC)
            if not years_ago(now)<=when<=now:
                continue
            values={name:number(columns[name][index])*instrument.multiplier for name in ('open','high','low','close')}
            if values['high']<max(values['open'],values['close'],values['low']) or values['low']>min(values['open'],values['close']):
                continue
            volume=columns.get('volume',[])
            volume=number(volume[index],positive=False) if index<len(volume) and volume[index] is not None else None
            if volume is not None and volume<0:
                volume=None
            bars.append({'date':when.astimezone(zone).date().isoformat(),**values,'volume':volume})
        except (ValueError,TypeError,IndexError,OverflowError,OSError):
            continue
    bars=list({bar['date']:bar for bar in bars}.values())
    bars.sort(key=lambda bar:bar['date'])
    if not bars:
        raise ValueError('No valid history')
    return {'rows':bars,'fetched_at':now.isoformat(),'source':'Yahoo Finance','error':None}


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
    if not isinstance(quotes,list) or len(quotes)>100:
        raise ValueError('Too many companies')
    rows=[]
    for row in quotes[:8]:
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
        payload=get_json('https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved',
            {'scrIds':'sec-ind_sec-largest-equities_'+context['sector_slug'],'count':8})
        return parse_us_companies(payload,now)
    if identity not in KR_COMPANIES:
        return {'rows':[],'fetched_at':now.isoformat(),'error':None}
    rows=[]
    for code,name in KR_COMPANIES[identity]:
        row={'symbol':code+'.KS','name':name,'market_cap':None,'currency':'KRW','source':'Npay 증권',
             'url':f'https://m.stock.naver.com/domestic/stock/{code}/total'}
        try:
            payload=get_json(f'https://m.stock.naver.com/api/stock/{code}/integration')
            if payload.get('itemCode')!=code:
                raise ValueError('Wrong company')
            infos=payload.get('totalInfos',[])
            if not isinstance(infos,list) or len(infos)>100:
                raise ValueError('Invalid company response')
            row['market_cap']=parse_kr_cap(next(item['value'] for item in infos if item.get('code')=='marketValue'))
        except Exception:
            pass
        rows.append(row)
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
            if when.tzinfo is None or not now-dt.timedelta(days=14)<=when<=now+dt.timedelta(minutes=5):
                continue
            rows.append({'title':title,'publisher':(src.text or host)[:80],'url':url,'published_at':when.isoformat()})
        except (ValueError,TypeError,AttributeError):
            continue
    return rows


def news(instrument):
    query=context_for(instrument.id)['news_query']; now=dt.datetime.now(UTC)
    korean=context_for(instrument.id).get('news_locale')=='ko'
    with FixedSession() as session:
        response=session.get('https://news.google.com/rss/search',params={
            'q':query+' when:14d','hl':'ko' if korean else 'en-US',
            'gl':'KR' if korean else 'US','ceid':'KR:ko' if korean else 'US:en'},
            headers={'User-Agent':'MilkywayPersonal/1.0'},timeout=(3,7),stream=True)
        try:
            response.raise_for_status()
            rows=parse_news_rss(read_requests_bytes(response,maximum_bytes=256*1024),now,
                                   KOREAN_NEWS_HOSTS if korean else ENGLISH_NEWS_HOSTS)
        finally:
            response.close()
    rows=list({row['url']:row for row in rows}.values()); rows.sort(key=lambda row:row['published_at'],reverse=True)
    return {'rows':rows[:8],'fetched_at':now.isoformat(),'source':'Google News · 지정 언론사','error':None}


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
