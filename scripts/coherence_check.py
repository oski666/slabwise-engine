"""Coherence checks on the site's data (D211): every number the pages put side by side must agree with the others.

Usage: PYTHONPATH=. python scripts/coherence_check.py prototype/data/real.json [report.json]
Prints one line per check with the number of cases and the first examples, and writes the report (default
results/coherence.json). Exit code 0 always: the site is not held back, the report is read after each build.
Checks:
  C1 band: lo <= value <= hi for every grade with a value
  C2 sales: sales in 90 days <= all sales of the grade
  C3 population: PSA 10 population <= PSA total; sum of PSA 7-10 populations <= PSA total
  C4 Gem Rate: PSA 10 / total from our populations against GemRate's own counts (within 5 points, when both exist)
  C5 tap: new PSA 10 in 30 days <= PSA 10 population (GemRate); the tap's card exists
  C6 era: the era written on the card is the era of its id (slabwise.series.series_of)
  C7 grade ladder: a higher grade worth less than the grade below, both with own sales and not in review
  C8 changes: no 30/90-day change shown on a grade in review, stale or without own sales
  C9 hidden gem: only on a PSA 10 with >= 3 sales in 13 weeks, not in review, x < 0.5
  C10 stories: the change written in a story equals the change on the card's page
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from slabwise.series import series_of  # noqa: E402

D = json.load(open(sys.argv[1]))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "coherence.json")
C = D["cards"]
by_id = {c["id"]: c for c in C}
tap = D.get("tap") or {}
rep = {}


def add(key, case):
    rep.setdefault(key, []).append(case)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


own = lambda g: g.get("sales_all") and not g.get("off") and not g.get("stale")  # noqa: E731
for c in C:
    G = {g["grade"]: g for g in c["grades"]}
    for g in c["grades"]:
        if g.get("value") and g.get("lo") and g.get("hi") and not (g["lo"] <= g["value"] <= g["hi"]):
            add("C1", (c["id"], g["grade"], g["lo"], g["value"], g["hi"]))
        if (g.get("sales90") or 0) > (g.get("sales_all") or 0):
            add("C2", (c["id"], g["grade"], g["sales90"], g["sales_all"]))
        if not own(g) and (g.get("ch30") is not None or g.get("ch90") is not None) and (g.get("off") or g.get("stale") or not g.get("sales_all")):
            add("C8", (c["id"], g["grade"]))
    tot = num(c.get("psa_total"))
    pops = {k: num(G[k].get("pop")) for k in G}
    if tot:
        if (pops.get(10) or 0) > tot:
            add("C3", (c["id"], "PSA 10 > total", pops.get(10), tot))
        if sum(v or 0 for v in pops.values()) > tot * 1.001:
            add("C3", (c["id"], "PSA 7-10 > total", sum(v or 0 for v in pops.values()), tot))
    t = tap.get(c["id"])
    if t and tot and pops.get(10) and t.get("total") and t.get("psa10") is not None:
        ours, theirs = pops[10] / tot, t["psa10"] / t["total"]
        if abs(ours - theirs) > 0.05:
            add("C4", (c["id"], c["name"], round(ours * 100, 1), round(theirs * 100, 1)))
    if t and t.get("new10") is not None and t.get("psa10") is not None and t["new10"] > t["psa10"]:
        add("C5", (c["id"], t["new10"], t["psa10"]))
    if c.get("series") != series_of(c["id"].split("/")[0]):
        add("C6", (c["id"], c.get("set"), c.get("series"), series_of(c["id"].split("/")[0])))
    for hi_, lo_ in ((10, 9), (9, 8), (8, 7)):
        a, b = G.get(hi_), G.get(lo_)
        if a and b and own(a) and own(b) and (a.get("sales90") or 0) >= 3 and (b.get("sales90") or 0) >= 3 and a["value"] < b["value"]:
            add("C7", (c["id"], c["name"], f"PSA {hi_} {round(a['value'])} < PSA {lo_} {round(b['value'])}"))
    r = c.get("rarity_price")
    if r and r.get("gem"):
        g10 = G.get(10)
        if not (g10 and (g10.get("sales90") or 0) >= 3 and not g10.get("off") and r["x"] < 0.5):
            add("C9", (c["id"],))
for k in tap:
    if k not in by_id and not any(k.startswith(x + "/") for x in by_id):
        add("C5", (k, "not a card of the site"))
for s in ((D.get("pulse") or {}).get("stories") or []):
    c = by_id.get(s.get("id") or s.get("card"))
    if c and s.get("grade") is not None and s.get("change") is not None:
        g = next((g for g in c["grades"] if g["grade"] == s["grade"]), None)
        shown = g and (g.get("ch30") if s.get("kind") in ("up", "down", "rise", "fall") else None)
        if shown is not None and abs(shown - s["change"]) > 0.005:
            add("C10", (c["id"], s["grade"], s["change"], shown))

summary = {k: dict(n=len(v), examples=v[:12]) for k, v in sorted(rep.items())}
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
json.dump(dict(asof=D.get("asof"), cards=len(C), checks=summary), open(out, "w"), indent=1, ensure_ascii=False)
for k in [f"C{i}" for i in range(1, 11)]:
    v = rep.get(k, [])
    print(f"{k}: {len(v)}" + (f"  es. {v[:4]}" if v else ""))
