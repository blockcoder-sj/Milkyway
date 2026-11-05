"""Validated HTTP inputs for personal research."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .strategies import PortfolioSpec, FilterSpec, FactorSpec


class SessionBody(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    objective: str = Field(default="", max_length=2000)


class MessageBody(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    request_id: str = Field(pattern="^[a-zA-Z0-9_-]{8,64}$")


class RenameSessionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=100)


class ApprovalBody(BaseModel):
    request_digest: str = Field(pattern="^[a-f0-9]{64}$")
    approved: Literal[True]


class AdjustmentBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(pattern="^[a-zA-Z0-9_-]{8,64}$")
    universe: Literal["selected", "us_all"] | None = None
    symbols: list[str] | None = Field(default=None, max_length=20)
    portfolio: PortfolioSpec
    filters: FilterSpec
    factors: list[FactorSpec] = Field(min_length=1, max_length=5)
