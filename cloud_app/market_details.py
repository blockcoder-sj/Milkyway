"""Per-instrument atomic cache; HTTP readers never call external providers."""
import datetime as dt
import time
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime

from .bounded_io import read_bounded_json
from .market_catalog import BY_ID
from .market_detail_catalog import context_for
from .market_detail_feed import collect_detail, merge_news
from .market_service import _write_cache
from .provider_process import ProviderProcess

UTC=dt.timezone.utc
REFRESH_SECONDS=900
_provider=ProviderProcess(collect_detail)


class HistoryBar(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    date:dt.date
    open:float|None=Field(default=None,gt=0,le=1e16)
    high:float|None=Field(default=None,gt=0,le=1e16)
    low:float|None=Field(default=None,gt=0,le=1e16)
    close:float=Field(gt=0,le=1e16)
    volume:float|None=Field(default=None,ge=0,le=1e16)


class CompanyRow(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    symbol:str=Field(max_length=20)
    name:str=Field(max_length=120)
    market_cap:float|None=Field(default=None,gt=0,le=1e16)
    currency:str=Field(max_length=3)
    source:str=Field(max_length=80)
    url:str=Field(max_length=2000)
    displayed_share_pct:float|None=Field(default=None,ge=0,le=100)
    classification:dict|None=None
    directory_basis:str|None=Field(default=None,max_length=200)
    directory_group:str|None=Field(default=None,max_length=80)


class NewsRow(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title:str=Field(max_length=300)
    publisher:str=Field(max_length=80)
    url:str=Field(max_length=2000)
    published_at:AwareDatetime


class HistoryQuality(BaseModel):
    model_config=ConfigDict(extra='forbid')
    received:int=Field(ge=0,le=1200)
    outside_range:int=Field(ge=0,le=1200)
    invalid_close:int=Field(ge=0,le=1200)
    close_only:int=Field(ge=0,le=1200)
    duplicates:int=Field(ge=0,le=1200)
    accepted:int=Field(ge=0,le=1200)


TRow=TypeVar('TRow')


class DetailPart(BaseModel,Generic[TRow]):
    model_config=ConfigDict(extra='ignore')
    rows:list[TRow]=Field(default_factory=list,max_length=1100)
    fetched_at:AwareDatetime|None=None
    error:str|None=Field(default=None,max_length=300)
    source:str|None=Field(default=None,max_length=80)
    quality:HistoryQuality|None=None
    selection_version:int=Field(default=1,ge=1,le=10)


class DetailCache(BaseModel):
    model_config=ConfigDict(extra='ignore')
    history:DetailPart[HistoryBar]=Field(default_factory=DetailPart[HistoryBar])
    related_history:DetailPart[HistoryBar]=Field(default_factory=DetailPart[HistoryBar])
    companies:DetailPart[CompanyRow]=Field(default_factory=DetailPart[CompanyRow])
    news:DetailPart[NewsRow]=Field(default_factory=DetailPart[NewsRow])
    attempted_at:AwareDatetime|None=None


def cache_path(settings,identity):
    if identity not in BY_ID or BY_ID[identity].group == 'sectors' or not settings.personal_local_mode or settings.production:
        raise ValueError('Unknown personal market instrument')
    return settings.dataset_dir.parent/'market-details'/(identity+'.json')


def read_cache(settings,identity):
    try:
        value=read_bounded_json(cache_path(settings,identity),maximum_bytes=2*1024*1024)
        return DetailCache.model_validate(value)
    except (OSError,ValueError,TypeError):
        return DetailCache()


def refresh_detail(settings,identity):
    cache_path(settings, identity)  # Reject disabled sectors before any provider call.
    old=read_cache(settings,identity).model_dump(mode='json')
    try:
        result=_provider.run({'id':identity},{},deadline=time.monotonic()+60)
    except (RuntimeError,TimeoutError,ValueError,OSError):
        result={}
    for key in ('history','companies','news','related_history'):
        part=result.get(key,{})
        if 'rows' in part:
            if key == 'news':
                prior=old[key]['rows'] if old[key].get('selection_version',1)==part.get('selection_version',1) else []
                part['rows']=merge_news(prior+part['rows'],dt.datetime.now(UTC))
            old[key]=part
        else:
            old[key]['error']='원자료 수신·검증에 실패했습니다. 이전 자료가 있다면 유지합니다.'
    old['attempted_at']=dt.datetime.now(UTC).isoformat()
    parsed=DetailCache.model_validate(old)
    _write_cache(cache_path(settings,identity),parsed.model_dump(mode='json'))
    return parsed


def detail_snapshot(settings,identity,now=None):
    cache_path(settings, identity)
    instrument=BY_ID[identity]
    now=now or dt.datetime.now(UTC)
    cache=read_cache(settings,identity)
    result=cache.model_dump(mode='json')
    for key in ('history','companies','news','related_history'):
        part=getattr(cache,key)
        result[key]['stale']=bool(part.error) or part.fetched_at is None or part.fetched_at.tzinfo is None or not -120<=(now-part.fetched_at).total_seconds()<=REFRESH_SECONDS*2
    result['news']['rows']=merge_news(result['news']['rows'],now)
    from .market_detail_feed import years_ago
    earliest=years_ago(now).date().isoformat()
    for key in ('history','related_history'):
        result[key]['rows']=[row for row in result[key]['rows'] if earliest<=row['date']<=now.date().isoformat()]
    return {**result,'id':identity,'label':instrument.label,'symbol':instrument.symbol,'unit':instrument.unit,
            'group':instrument.group,'market':instrument.market,'context':context_for(identity),
            'refresh_seconds':REFRESH_SECONDS,'maximum_years':3}
