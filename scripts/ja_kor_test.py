"""Protocol §50 (D239): short Korean tags on the Japanese path. Usage: PYTHONPATH=. python scripts/ja_kor_test.py <slabwise-data dir> <out.json>"""
import gzip, json, sys, random
from slabwise.sources import auction_titles as at
pd = sys.argv[1]
titles = {s.get("title") or "" for s in json.load(gzip.open(pd + "/data/raw/tcgcharts/history.json.gz", "rt"))} | {s.get("title") or "" for s in json.load(open(pd + "/data/raw/tcgcharts/sales.json"))}
titles = sorted(t for t in titles if t)
res = {}
for flag in (False, True):
    at.JA_EXCLUDE = at.ja_exclude(at.NEW_JA_BOX, flag)
    res[flag] = {t: at.match_title(t)[0] for t in titles}
moved = [(t, res[False][t], res[True][t]) for t in titles if res[False][t] and res[True][t] and res[True][t] != res[False][t]]
lost = [(t, res[False][t]) for t in titles if res[False][t] and not res[True][t]]
out = dict(titles=len(titles), K1_moved=len(moved), lost=len(lost), K1=not moved, lost_items=lost if len(lost) <= 40 else random.Random(42).sample(lost, 40))
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print({k: v for k, v in out.items() if k != "lost_items"})
for t, k in out["lost_items"]: print(k, "|", t[:115])
