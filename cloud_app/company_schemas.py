"""Explicit display-only company knowledge contracts."""
from typing import Literal
from urllib.parse import urlsplit
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=160)
    url: str = Field(max_length=2000)
    as_of: str | None = Field(default=None, max_length=40)
    level: Literal["primary", "provider", "encyclopedia"] = "primary"

    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        ):
            raise ValueError("Unsafe source URL")
        return value


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    detail: str = Field(default="", max_length=1500)
    original: str = Field(default="", max_length=1500)
    source: Source


class Relation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=160)
    kind: Literal[
        "subsidiary",
        "parent",
        "owner",
        "holding",
        "partner",
        "supplier",
        "customer",
        "competitor",
    ]
    detail: str = Field(default="", max_length=700)
    original: str = Field(default="", max_length=1500)
    symbol: str | None = Field(default=None, max_length=20)
    entity_id: str | None = Field(default=None, pattern=r"^Q\d{1,12}$")
    registry_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    source: Source


class Financial(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    label: str = Field(max_length=80)
    value: float = Field(ge=-1e16, le=1e16)
    unit: str = Field(max_length=12)
    period: str = Field(max_length=80)
    source: Source


class RevenueLine(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    group: Literal['product', 'segment', 'geography', 'revenue_type', 'end_market']
    member: str = Field(min_length=1, max_length=190)
    label: str = Field(min_length=1, max_length=160)
    value: float = Field(ge=0, le=1e16)
    unit: str = Field(pattern=r'^[A-Z]{3}$')
    start: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    end: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    total: float | None = Field(default=None, gt=0, le=1e16)
    metric: str = Field(min_length=1, max_length=120)
    parent: str | None = Field(default=None, max_length=190)
    includes_intersegment: bool = False
    share_exclusion: str | None = Field(default=None, max_length=400)
    source: Source

    @model_validator(mode='after')
    def valid_period(self):
        import datetime as dt
        first, last = dt.date.fromisoformat(self.start), dt.date.fromisoformat(self.end)
        if not 300 <= (last - first).days <= 400 or (self.total is not None and self.value > self.total):
            raise ValueError('Invalid annual revenue slice')
        return self


class CompanyKnowledge(BaseModel):
    model_config = ConfigDict(extra="forbid", revalidate_instances="always")
    symbol: str | None = Field(default=None, pattern=r"^[A-Z0-9][A-Z0-9.-]{0,19}$")
    entity_id: str | None = Field(default=None, pattern=r"^Q\d{1,12}$")
    registry_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    name: str = Field(max_length=120)
    description: str = Field(default="", max_length=1500)
    description_source: Source | None = None
    facts: list[Fact] = Field(default_factory=list, max_length=30)
    brief: list[Fact] = Field(default_factory=list, max_length=8)
    revenue_mix: list[RevenueLine] = Field(default_factory=list, max_length=80)
    collector_version: int = Field(default=0, ge=0, le=100)
    products: list[Fact] = Field(default_factory=list, max_length=60)
    segments: list[Fact] = Field(default_factory=list, max_length=30)
    market_shares: list[Fact] = Field(default_factory=list, max_length=30)
    drivers: list[Fact] = Field(default_factory=list, max_length=30)
    relations: list[Relation] = Field(default_factory=list, max_length=100)
    financials: list[Financial] = Field(default_factory=list, max_length=30)
    filings: list[Source] = Field(default_factory=list, max_length=12)
    sources: list[Source] = Field(default_factory=list, max_length=200)
    report_analysis: Fact | None = None
    unavailable_sources: list[Literal[
        "wikidata", "sec", "sec_financials", "sec_report", "sec_subsidiaries", "wise"
    ]] = Field(default_factory=list, max_length=6)
    fetched_at: AwareDatetime | None = None
    attempted_at: AwareDatetime | None = None
    errors: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode='before')
    @classmethod
    def accepted_provenance(cls, value):
        from .company_provenance import clean
        return clean(value)
