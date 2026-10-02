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
    'Australia|New Zealand|Saudi Arabia|United Arab Emirates|UAE|Abu Dhabi|Dubai|'
    'Qatar|Oman|Bahrain|Kuwait|Iraq|Egypt|Nigeria|Angola|South Africa|Mozambique|'
    'Gabon|Ghana|Kenya|Senegal|Algeria|Libya|Tunisia|Equatorial Guinea|Kazakhstan|Azerbaijan'
).split('|'))
LEGAL_FORM = re.compile(r'(.+?)\s+(?:limited liability company|corporation|limited partnership|'
                        r'limited liability partnership|company limited by shares)', re.I)
NAME_HEADER = re.compile(r'(?:name(?: of (?:subsidiary|company|entity))?|subsidiar(?:y|ies))', re.I)
PLACE_HEADER = re.compile(r'(?:jurisdiction(?: of (?:incorporation|organization|formation))?|'
                         r'(?:state|country)(?: of (?:incorporation|organization|formation))?)', re.I)


def jurisdiction(value):
    value = value.strip()
    if value.lower() in PLACES:
        return value
    match = LEGAL_FORM.fullmatch(value)
    return match[1] if match and match[1].lower() in PLACES else None


def company_name(value):
    return (3 <= len(value) <= 160 and re.search(r'[A-Za-z]', value)
        and not jurisdiction(value)
        and not re.search(r'(?:subsidiar|jurisdiction|\bname\b|exhibit|^state$|^December \d)', value, re.I))


def parse(soup, origin):
    if not re.search(r'subsidiar', soup.get_text(' ', strip=True)[:4000], re.I):
        raise ValueError('Not a subsidiary exhibit')
    result, seen = [], set()

    def add(name, place=None):
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
            names = [i for i,v in enumerate(values) if NAME_HEADER.fullmatch(v)]
            if names:
                columns = [(i, next((j for j in range(i+1, len(values))
                                     if PLACE_HEADER.fullmatch(values[j])), None)) for i in names]
                pending = []
                continue
            if columns:
                for i,j in columns:
                    if i < len(values):
                        add(values[i], jurisdiction(values[j]) if j is not None and j < len(values) else None)
                continue
            values = [v for v in values if v and v not in {'*', '—', '-', '•'}]
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
    """Discard old geographic phantoms and remove unsupported jurisdiction claims."""
    result = []
    prefix = '공시 자회사 명세서 · 설립·등록 관할: '
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('source'), dict):
            result.append(row)
            continue
        origin = row.get('source', {})
        legacy = (row.get('kind') == 'subsidiary' and origin.get('label', '').startswith('SEC · Exhibit 21')
                  and row.get('detail', '').startswith(prefix))
        if legacy and jurisdiction(row.get('name', '')):
            continue
        if legacy:
            place = row['detail'].removeprefix(prefix).split(' · ',1)[0]
            if not jurisdiction(place):
                row = {**row, 'detail': '공시 자회사 명세서에 기재된 기업명 · 기존 수집에서 관할을 확인하지 못했습니다. '
                    '지분율·거래 규모는 별도로 확인합니다.'}
        result.append(row)
    return result
