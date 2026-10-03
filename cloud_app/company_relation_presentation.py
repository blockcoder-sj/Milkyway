"""Order evidence by its stated date, then the current reviewed wording.

Historical claims stay visible. Fetch time is not a document's effective date;
names alone never identify a reviewed owner or counterpart.
"""
from datetime import date
from functools import lru_cache


@lru_cache(maxsize=1)
def reviewed_claims():
    # Deferred to avoid a catalogue import cycle during profile construction.
    from .company_research_catalog import PUBLIC_COMPANIES, PRIVATE_COMPANIES, RELATIONS

    result = {}
    profiles = [('ticker', key, value, RELATIONS.get(key, []))
                for key, value in PUBLIC_COMPANIES.items()]
    profiles += [('registry', key, value, []) for key, value in PRIVATE_COMPANIES.items()]
    for namespace, owner, profile, extra in profiles:
        claims = result.setdefault((namespace, owner), set())
        for edge in profile.get('relations', []) + extra:
            source = edge['source']
            for field, target_namespace in (('symbol', 'ticker'), ('registry_id', 'registry'),
                                            ('entity_id', 'wikidata')):
                if edge.get(field):
                    claims.add((target_namespace, edge[field], edge['kind'], edge.get('detail', ''),
                                source['url'], source.get('as_of'), source['level']))
    return result


def evidence_order(row, aliases_by_id):
    as_of = row['as_of']
    try:
        # Collection labels such as '열람 2026-10-01' are not filing dates.
        stated_date = date.fromisoformat(as_of).toordinal() if isinstance(as_of, str) and len(as_of) == 10 else 0
    except ValueError:
        stated_date = 0
    claims = reviewed_claims()
    reviewed = any(
        (target['namespace'], target['value'], row['kind'], row['detail'],
         row['url'], as_of, row['level']) in claims.get((owner['namespace'], owner['value']), ())
        for owner in aliases_by_id[row['owner_id']]
        for target in aliases_by_id[row['object_id']]
    )
    business = row['kind'] in ('supplier', 'customer', 'partner', 'competitor')
    level = {'primary': 0, 'provider': 1, 'encyclopedia': 2}.get(row['level'], 3)
    return (0 if business else 1, level, -stated_date, 0 if reviewed else 1)
