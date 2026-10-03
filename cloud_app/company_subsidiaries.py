"""Read exhibit rows without treating a second company as its jurisdiction."""
import re

PLACES = frozenset(value.lower() for value in (
    'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|'
    'Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|'
    'Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|'
    'New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|'
    'Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|'
    'Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia|'
    'United States|United States of America|USA|U.S.|Canada|Alberta|British Columbia|'
    'Manitoba|New Brunswick|Newfoundland and Labrador|Northwest Territories|Nova Scotia|'
    'Nunavut|Ontario|Prince Edward Island|Quebec|Québec|Saskatchewan|Yukon|'
    'England|Wales|England and Wales|Scotland|Northern Ireland|United Kingdom|UK|'
    'Ireland|Netherlands|France|Germany|Italy|Spain|Portugal|Belgium|Switzerland|'
    'Luxembourg|Austria|Sweden|Finland|Denmark|Norway|Poland|Czech Republic|Romania|'
    'Bulgaria|Hungary|Greece|Cyprus|Malta|Turkey|Israel|Russia|Ukraine|'
    'Bermuda|Cayman Islands|British Virgin Islands|Bahamas|Barbados|Curacao|Curaçao|'
    'Jersey|Guernsey|Isle of Man|Gibraltar|Mexico|Brazil|Argentina|Chile|Colombia|'
    'Peru|Ecuador|Venezuela|Guyana|Suriname|Uruguay|Bolivia|Panama|Costa Rica|'
    'Trinidad and Tobago|China|Hong Kong|Taiwan|Japan|Korea|South Korea|Republic of Korea|'
    'Singapore|Malaysia|Indonesia|Thailand|Philippines|Vietnam|Viet Nam|India|Pakistan|'
    'Australia|Western Australia|New Zealand|Saudi Arabia|United Arab Emirates|UAE|Abu Dhabi|Dubai|'
    'Qatar|Oman|Bahrain|Kuwait|Iraq|Egypt|Nigeria|Angola|South Africa|Mozambique|'
    'Gabon|Ghana|Kenya|Senegal|Algeria|Libya|Tunisia|Equatorial Guinea|Kazakhstan|Azerbaijan'
).split('|'))
LEGAL_FORM = re.compile(r'(.+?)\s+(?:limited liability company|corporation|limited partnership|'
                        r'limited liability partnership|company limited by shares)', re.I)
NAME_HEADER = re.compile(r'(?:name(?: of (?:subsidiary|company|entity))?|subsidiar(?:y|ies))', re.I)
PLACE_HEADER = re.compile(r'(?:jurisdiction|(?:state|country)(?: or (?:other )?jurisdiction)?)'
                         r'(?: of (?:incorporation|organization|formation))?', re.I)
ITEM_NUMBER = re.compile(r'(?:[ivxlcdm]+|[a-z]|\d{1,4})[.)]', re.I)
LEADING_ITEM = re.compile(r'^(?:(?:[ivxlcdm]+|[a-z]|\d{1,4})[.)]\s+)+')
CROSS_REFERENCE = re.compile(r'\s*\(see company\b[^)]*\)\s*$', re.I)


def normalized_name(value):
    """Remove exhibit list formatting, never a company's legal suffix."""
    value = value.strip()
    value = LEADING_ITEM.sub('', value, count=1)
    return CROSS_REFERENCE.sub('', value).strip()


def jurisdiction(value):
    value = value.strip()
    if value.lower() in PLACES:
        return value
    match = LEGAL_FORM.fullmatch(value)
    return match[1] if match and match[1].lower() in PLACES else None


def company_name(value):
    value = normalized_name(value)
    return (3 <= len(value) <= 160 and re.search(r'[A-Za-z]', value)
        and not ITEM_NUMBER.fullmatch(value)
        and not jurisdiction(value)
        and not re.search(r'\(REGISTRANT\)', value, re.I)
        and not re.search(r'(?:subsidiar|jurisdiction|\bname\b|exhibit|^state$|^December \d)', value, re.I))


def parse(soup, origin):
    if not re.search(r'subsidiar', soup.get_text(' ', strip=True)[:4000], re.I):
        raise ValueError('Not a subsidiary exhibit')
    result, seen = [], set()

    def add(name, place=None):
        name = normalized_name(name)
        if not company_name(name) or name in seen or len(result) >= 80:
            return None
        seen.add(name)
        row = dict(name=name, kind='subsidiary', symbol=None,
            detail='공시 자회사 명세서 · ' + ('설립·등록 관할: ' + place if place else '원문에 기재된 기업명 · 관할 미확인')
                + ' · 지분율·현재 거래 규모는 별도로 확인합니다.', source=origin)
        result.append(row)
        return row

    for table in soup.find_all('table', limit=200):
        columns, pending = [], []
        for tr in table.find_all('tr', limit=2000):
            if len(result) >= 80:
                return result
            cells = tr.find_all(['td', 'th'], recursive=False)
            values = [re.sub(r'\s+', ' ', c.get_text(' ', strip=True)).strip() for c in cells]
            # SEC's indented lists use different numbers of td cells per row.
            # Match physical column ranges, rather than a td's ordinal index.
            positions, offset = [], 0
            for cell,value in zip(cells,values):
                span = cell.get('colspan', '1')
                width = min(int(span), 256) if re.fullmatch(r'[0-9]{1,3}', str(span)) else 1
                width = max(width, 1)
                positions.append((value, offset, offset + width))
                offset += width
            names = [i for i,(v,_,_) in enumerate(positions) if NAME_HEADER.fullmatch(v)]
            if names:
                columns = [(positions[i][1:], next((positions[j][1:] for j in range(i+1, len(values))
                                     if PLACE_HEADER.fullmatch(values[j])), None)) for i in names]
                pending = []
                continue
            if columns:
                for name_range,place_range in columns:
                    def within(bounds):
                        return [v for v,start,end in positions
                                if bounds and start < bounds[1] and end > bounds[0]
                                and v and not ITEM_NUMBER.fullmatch(v)]
                    name = ' '.join(within(name_range))
                    place = next((p for v in within(place_range) if (p := jurisdiction(v))), None)
                    add(name, place)
                continue
            values = [v for v in values if v and v not in {'*', '—', '-', '•'}
                      and not ITEM_NUMBER.fullmatch(v)]
            places = [jurisdiction(v) for v in values]
            # Flotek's two parallel name columns have legal-form/state rows below.
            if values and all(places):
                if len(pending) == len(values):
                    for row,place in zip(pending,places):
                        if row:
                            row['detail'] = ('공시 자회사 명세서 · 설립·등록 관할: ' + place
                                + ' · 지분율·현재 거래 규모는 별도로 확인합니다.')
                pending = []
                continue
            if len(values) >= 2 and company_name(values[0]) and any(places[1:]):
                add(values[0], next(p for p in places[1:] if p))
                pending = []
            elif values and all(company_name(v) and re.search(r'\b(?:LLC|Inc\.?|Ltd\.?|Limited|Corp\.?|S\.A\.)$',v,re.I) for v in values):
                pending = [add(v) for v in values]
            else:
                pending = []
    return result


def repair_legacy(rows):
    """Repair only generated exhibit rows; keep independently reviewed claims."""
    result = []
    prefix = '공시 자회사 명세서 · 설립·등록 관할: '
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('source'), dict):
            result.append(row)
            continue
        origin = row.get('source', {})
        generated = (row.get('kind') == 'subsidiary' and origin.get('label', '').startswith('SEC · Exhibit 21')
                     and row.get('detail', '').startswith('공시 자회사 명세서'))
        if generated:
            name = normalized_name(row.get('name', ''))
            if not name or ITEM_NUMBER.fullmatch(name) or jurisdiction(name) or re.search(r'\(REGISTRANT\)', name, re.I):
                continue
            if name != row['name']:
                row = {**row, 'name': name}
        if generated and row.get('detail', '').startswith(prefix):
            place = row['detail'].removeprefix(prefix).split(' · ',1)[0]
            if not jurisdiction(place):
                row = {**row, 'detail': '공시 자회사 명세서에 기재된 기업명 · 기존 수집에서 관할을 확인하지 못했습니다. '
                    '지분율·거래 규모는 별도로 확인합니다.'}
        result.append(row)
    return result


def replaced_by_reviewed(row, reviewed):
    """Replace a generic cache entry only in the same verified exhibit/entity."""
    origin = row.get('source', {})
    if (row.get('kind') != 'subsidiary'
            or not origin.get('label', '').startswith('SEC · Exhibit 21')
            or not row.get('detail', '').startswith('공시 자회사 명세서')):
        return False
    identity = row.get('registry_id') or row.get('symbol') or row.get('name')
    document = origin.get('url', '').split('#')[0]
    return any(item.get('kind') == 'subsidiary'
               and (item.get('registry_id') or item.get('symbol') or item.get('name')) == identity
               and item.get('source', {}).get('url', '').split('#')[0] == document
               and item.get('source', {}).get('as_of') == origin.get('as_of')
               for item in reviewed)
