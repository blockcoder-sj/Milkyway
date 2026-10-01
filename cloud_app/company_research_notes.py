"""Small primary-source reading-note constructors; no network or model work."""


def source(label, url, date="열람 2026-10-01", level="primary"):
    return dict(label=label, url=url, as_of=date, level=level)


def profile(name, origin, business, revenue, products=(), customers="", inputs="", competition=""):
    fields = [("무엇을 하는 기업인가", business), ("매출이 생기는 구조", revenue),
              ("고객·판매 경로", customers), ("공급망·주요 투입 요소", inputs),
              ("경쟁의 범위", competition)]
    return dict(name=name, description=business, description_source=origin,
                brief=[dict(title=title, detail=detail, source=origin) for title, detail in fields if detail],
                products=[dict(title=title, detail=detail, source=origin) for title, detail in products],
                relations=[], sources=[origin])


def relation(name, symbol, kind, detail, origin, registry=None):
    return dict(name=name, symbol=symbol, registry_id=registry, kind=kind, detail=detail, source=origin)
