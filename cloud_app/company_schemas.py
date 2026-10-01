"""Explicit display-only company knowledge contracts."""
from typing import Literal
from urllib.parse import urlsplit
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


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
    symbol: str | None = Field(default=None, max_length=20)
    entity_id: str | None = Field(default=None, pattern=r"^Q\d{1,12}$")
    source: Source


class Financial(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    label: str = Field(max_length=80)
    value: float = Field(ge=-1e16, le=1e16)
    unit: str = Field(max_length=12)
    period: str = Field(max_length=80)
    source: Source


class CompanyKnowledge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str | None = Field(default=None, pattern=r"^[A-Z0-9][A-Z0-9.-]{0,19}$")
    entity_id: str | None = Field(default=None, pattern=r"^Q\d{1,12}$")
    name: str = Field(max_length=120)
    description: str = Field(default="", max_length=1500)
    description_source: Source | None = None
    facts: list[Fact] = Field(default_factory=list, max_length=30)
    products: list[Fact] = Field(default_factory=list, max_length=60)
    segments: list[Fact] = Field(default_factory=list, max_length=30)
    market_shares: list[Fact] = Field(default_factory=list, max_length=30)
    drivers: list[Fact] = Field(default_factory=list, max_length=30)
    relations: list[Relation] = Field(default_factory=list, max_length=100)
    financials: list[Financial] = Field(default_factory=list, max_length=30)
    filings: list[Source] = Field(default_factory=list, max_length=12)
    sources: list[Source] = Field(default_factory=list, max_length=200)
    fetched_at: AwareDatetime | None = None
    attempted_at: AwareDatetime | None = None
    errors: list[str] = Field(default_factory=list, max_length=12)
