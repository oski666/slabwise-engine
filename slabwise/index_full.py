"""D149 (protocol §29), D228: the site's indices from the run with the long history.

Keeps each series from its first basket of at least 5 items (15 for the general index); every index
that already exists on 2024-01-01 is 100 on its first week of 2024, a later one is 100 at its start.
"""
MIN_BASKET = {"era": 5, "set": 5, "generale": 15}
COMMON = "2024-01-01"


def trim(ix, kind):
    if not ix:
        return None
    start = next((d for d, n in (ix.get("sizes") or []) if n >= MIN_BASKET[kind]), None)
    if not start:
        return None
    pts = [p for p in ix["points"] if p[0] >= start]
    if len(pts) <= 26:
        return None
    b = next((p for p in pts if p[0] >= COMMON), None) if start <= COMMON else pts[0]
    return dict(ix, start=start, base=b[0], points=[[d, round(v * 100 / b[1], 2)] for d, v in pts])


def extract(hist):
    """hist: a dict with indexes, index_all, index_sets, asof, index_base (the real.json of the history run)."""
    res = dict(indexes={k: v for k, v in ((k, trim(v, "era")) for k, v in (hist.get("indexes") or {}).items()) if v},
               index_all=trim(hist.get("index_all"), "generale"),
               index_sets={k: v for k, v in ((k, trim(v, "set")) for k, v in (hist.get("index_sets") or {}).items()) if v},
               asof=hist.get("asof"))
    res["index_base"] = next((v["base"] for v in res["indexes"].values() if v["start"] <= COMMON), hist.get("index_base"))
    return res
