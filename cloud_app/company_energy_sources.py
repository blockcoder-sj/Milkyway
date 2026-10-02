"""Shared, local evidence metadata for reviewed Energy research modules."""
import json
from pathlib import Path

REPORTS = json.loads(Path(__file__).with_name('company_energy_reports.json').read_text())


def report(symbol, period='annual'):
    return {key: REPORTS[symbol][period][key] for key in ('label', 'url', 'as_of', 'level')}


def fact(title, detail, origin):
    return dict(title=title, detail=detail, source=origin)
