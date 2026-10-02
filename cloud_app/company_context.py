"""Reviewed business scope for graph neighbours, without provider or DB reads.

This is context about the company, never evidence of what it sold to a neighbour.
Resolve only exact catalog identities; a matching display name is insufficient.
"""
from copy import deepcopy
from functools import lru_cache
import re

from .company_provenance import forbidden
from .company_schemas import Fact


@lru_cache(maxsize=1024)
def _business(symbol, registry):
    from .company_catalog import editorial_for
    from .company_research_catalog import PRIVATE_COMPANIES

    value = (PRIVATE_COMPANIES.get(registry, {}) if registry
             else editorial_for(symbol) if symbol else {})
    detail, origin = value.get('description', ''), value.get('description_source')
    if not origin or forbidden(origin) or not re.search('[가-힣]', detail):
        return None
    return Fact(title='기업의 주요 사업', detail=detail[:600], source=origin).model_dump()


def business_context(symbol=None, registry=None):
    # Each response owns its values; callers cannot modify the shared catalogue.
    return deepcopy(_business(symbol, registry))
