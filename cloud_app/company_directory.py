"""Bounded local company-name index, independent from chart/news deserialization."""
from functools import lru_cache
from pathlib import Path
import re

from .bounded_io import read_bounded_json
from .market_catalog import BY_ID
from .market_details import cache_path, DetailPart, CompanyRow
from .sector_classifications import read_view


@lru_cache(maxsize=64)
def _received(location, mtime, size, inode):
    try:
        raw = read_bounded_json(Path(location), maximum_bytes=2 * 1024 * 1024)
        part = DetailPart[CompanyRow].model_validate(raw.get('companies', {}))
        return tuple((row.symbol, row.name) for row in part.rows
                     if re.fullmatch(r'[A-Z0-9][A-Z0-9.-]{0,19}', row.symbol))
    except (OSError, ValueError, TypeError, AttributeError):
        return ()


@lru_cache(maxsize=4)
def _index(files):
    result = {}
    for sector, location, mtime, size, inode in files:
        for symbol, name in _received(location, mtime, size, inode):
            result.setdefault(symbol, []).append((sector, name))
    return {symbol: tuple(rows) for symbol, rows in result.items()}


def lookup(settings, symbols, preferred_sector=None):
    """Exact disclosed tickers lead; unverified fallback keeps its original sector."""
    wanted = set(symbols)
    if not wanted:
        return {}
    found = {row.symbol: {'sector': row.sector, 'name': row.name}
             for row in read_view(settings).rows if row.symbol in wanted}
    from .company_catalog import EDITORIAL_DIRECTORY
    from .market_detail_catalog import KR_COMPANIES
    for sector, rows in KR_COMPANIES.items():
        for code, name in rows:
            symbol = code + '.KS'
            if symbol in wanted and symbol not in found:
                found[symbol] = {'sector': sector, 'name': name}
    for symbol, (sector, name) in EDITORIAL_DIRECTORY.items():
        if symbol in wanted and symbol not in found:
            found[symbol] = {'sector': sector, 'name': name}
    if wanted.issubset(found):
        return found
    files = []
    for sector, definition in sorted(BY_ID.items()):
        if definition.group != 'sectors':
            continue
        location = cache_path(settings, sector)
        try:
            stat = location.stat()
        except OSError:
            continue
        files.append((sector, str(location), stat.st_mtime_ns, stat.st_size, stat.st_ino))
    index = _index(tuple(files))
    for symbol in wanted - found.keys():
        rows = index.get(symbol, ())
        if rows:
            sector, name = next((row for row in rows if row[0] == preferred_sector), rows[0])
            found[symbol] = {'sector': sector, 'name': name}
    return found
