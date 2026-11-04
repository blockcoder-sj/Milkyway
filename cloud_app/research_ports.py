"""Application capabilities injected into research; no hidden main.py imports."""

from dataclasses import dataclass
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any
from sqlalchemy.orm import Session
from .config import Settings
from .database import PaperAccount, Strategy, User
from .strategies import StrategySpec


@dataclass(frozen=True)
class ResearchServices:
    get_settings: Callable[[], Settings]
    rate_limit: Callable[[str, int, int], Any]
    strategy_creation: Callable[[Session, User, StrategySpec, str], AbstractContextManager[Strategy]]
    account_creation: Callable[[str, str, User, Session, int | None], AbstractContextManager[PaperAccount]]
    strategy_payload: Callable[[Strategy], dict]
    account_snapshot: Callable[[Session, PaperAccount], dict]
    owned_strategy: Callable[[Session, User, str], Strategy]
