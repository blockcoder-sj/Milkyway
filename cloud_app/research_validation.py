"""Local response recovery; a recovered narrative can never contain a strategy."""
import json
import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ResearchNarrative(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    reply: str = Field(min_length=1, max_length=7000)
    limitations: list[Annotated[str, Field(min_length=1, max_length=1000)]] = Field(default_factory=list, max_length=10)
    next_steps: list[Annotated[str, Field(min_length=1, max_length=1000)]] = Field(default_factory=list, max_length=5)


def narrative_only(value):
    """Keep validated prose from a rejected draft, without coercion or execution."""
    if not isinstance(value, dict):
        return None
    try:
        narrative = ResearchNarrative.model_validate({
            key: value[key] for key in ('reply', 'limitations', 'next_steps') if key in value
        })
    except ValidationError:
        return None
    return {**narrative.model_dump(mode='json'), 'strategy': None}


def interrupted_narrative(text):
    """Only a complete first JSON reply string can survive a token interruption.

    No regex extraction of nested fields or repair of incomplete trading rules.
    Callers still return a failed turn and the original interruption diagnostic.
    """
    if not isinstance(text, str) or len(text) > 256 * 1024:
        return None
    match = re.match(r'\A\s*\{\s*"reply"\s*:\s*', text)
    if not match:
        return None
    try:
        value, _end = json.JSONDecoder().raw_decode(text, match.end())
    except (ValueError, RecursionError):
        return None
    return narrative_only({'reply': value})
