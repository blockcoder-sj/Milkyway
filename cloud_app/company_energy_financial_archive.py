"""Bounded original-filing financial receipts, independent of business coverage.

The local archive records reported values, not an assessment that a company has
been fully researched. Historical entity scopes stay visible beside the table.
"""
import datetime as dt
import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from .bounded_io import read_bounded_json
from .company_annual_financials import METRICS
from .company_annual_coordinates import metric_allowed
from .company_annual_attachments import same_annual_accession
from .company_financial_coordinates import coordinate
from .company_revenue import source_cik
from .company_schemas import Fact, Financial, Source
from .energy_issuers import issuer


class Receipt(Source):
    as_of: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    # Receipt metadata is small. The separately reviewed BP annual original is
    # 29.3 MB; this does not enlarge the app's network collection or JSON limits.
    bytes: int = Field(gt=0, le=48 * 1024 * 1024)
    blocks: int = Field(ge=0, le=100000)
    collected_at: AwareDatetime


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cik: str = Field(pattern=r'^[1-9][0-9]{0,9}$')
    annual: Receipt
    parent_annual: Receipt | None = None
    annual_period_end: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    financials: list[Financial] = Field(max_length=9)
    financial_context: list[Fact] = Field(default_factory=list, max_length=8)

    @model_validator(mode='after')
    def original_coordinates(self):
        source = self.annual.model_dump()
        if source_cik(source) != int(self.cik) or self.annual.level != 'primary':
            raise ValueError('Financial receipt issuer mismatch')
        if self.parent_annual is not None:
            parent = self.parent_annual.model_dump()
            if (not same_annual_accession(source, parent, self.cik)
                    or self.annual_period_end is None
                    or dt.date.fromisoformat(self.annual_period_end) > dt.date.fromisoformat(parent['as_of'])):
                raise ValueError('Financial exhibit parent mismatch')
        elif self.annual_period_end is not None:
            raise ValueError('Exhibit period requires original parent evidence')
        allowed = {tag: instant for _, tags, instant in METRICS for tag in tags}
        seen = set()
        filed = dt.date.fromisoformat(self.annual.as_of)
        for row in self.financials:
            metric = row.source.label.removeprefix('SEC 연차 원문 XBRL · ')
            coordinate = (metric, row.unit, row.period)
            if (metric not in allowed or coordinate in seen
                    or row.source.url.split('#')[0] != self.annual.url
                    or row.source.as_of != self.annual.as_of
                    or row.source.level != 'primary'
                    or not re.fullmatch(r'[A-Z]{3}', row.unit)):
                raise ValueError('Invalid original financial coordinate')
            dates = [dt.date.fromisoformat(value) for value in row.period.split(' ~ ')]
            if (len(dates) not in (1, 2) or dates[-1] > filed
                    or not metric_allowed(metric, source, self.cik, dates[-1])
                    or (self.parent_annual is not None and dates[-1].isoformat() != self.annual_period_end)
                    or (len(dates) == 1) != allowed[metric]
                    or (len(dates) == 2 and not 300 <= (dates[1] - dates[0]).days <= 400)):
                raise ValueError('Invalid original financial period')
            seen.add(coordinate)
        for row in self.financial_context:
            if row.source.level != 'primary':
                raise ValueError('Financial scope requires a primary source')
        return self


# Exact continuity of the old operating issuer into the new July 2026 holdco.
# This is a historical annual receipt, never a new holdco's own annual filing.
HISTORICAL = {
    'XOM': ('34088', 'https://www.sec.gov/Archives/edgar/data/34088/'
            '000003408826000045/xom-20251231.htm'),
}


def validate_archive(value):
    if not isinstance(value, dict) or len(value) > 500:
        raise ValueError('Invalid financial archive')
    result = {}
    for symbol, raw in value.items():
        entry = issuer(symbol)
        record = Record.model_validate(raw)
        historic = HISTORICAL.get(symbol)
        if (not entry or (record.cik != entry.cik
                and (record.cik, record.annual.url) != historic)):
            raise ValueError('Unverified financial archive issuer')
        if historic and record.cik != entry.cik and not record.financial_context:
            raise ValueError('Historical annual scope is missing')
        result[symbol] = record.model_dump(mode='json')
    return result


@lru_cache(maxsize=1)
def archive():
    return validate_archive(read_bounded_json(
        Path(__file__).with_name('company_energy_financials.json'),
        maximum_bytes=2 * 1024 * 1024))


def symbols():
    return frozenset(archive())


def editorial(symbol):
    value = archive().get(symbol)
    if not value:
        return {}
    origin = {key: value['annual'][key] for key in ('label', 'url', 'as_of', 'level')}
    origins = [origin]
    if value.get('parent_annual'):
        origins.append({key:value['parent_annual'][key] for key in ('label','url','as_of','level')})
    return deepcopy(dict(financials=value['financials'],
        financial_context=value['financial_context'], filings=origins, sources=origins))
