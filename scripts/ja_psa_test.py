"""Protocol §62 (D278): PSA label set names for Japanese cards. Reads every distinct title (tcgcharts sales, long
history, Cardova auctions built as titles) with the rule off and on, in two processes, and compares.

  read TITLES_JSON OUT_JSON          (run with SLABWISE_JA_PSA=0 and =1)
  titles TCGCHARTS_DIR CARDOVA_GZ OUT_JSON
  compare OFF_JSON ON_JSON RESULT_JSON
"""
import gzip
import json
import os
import random
import sys


def titles(tc_dir, cardova, out):
    t = set()
    for s in json.load(open(os.path.join(tc_dir, "sales.json"))):
        t.add(s.get("title") or "")
    h = os.path.join(tc_dir, "history.json.gz")
    if os.path.exists(h):
        for s in json.load(gzip.open(h, "rt")):
            t.add(s.get("title") or "")
    n_tc = len(t)
    if os.path.exists(cardova):
        for r in json.load(gzip.open(cardova, "rt"))["rows"]:
            try:
                g = int(float(r["grade"]))
            except (TypeError, ValueError):
                continue
            t.add(f"{r['year']} Pokemon {r['variety']} {r['card_number']} {r['player']} {r.get('attribute') or ''} PSA {g}")
    t.discard("")
    json.dump(sorted(t), open(out, "w"))
    print(f"§62: {n_tc} titoli tcgcharts, {len(t)} in tutto")


def read(src, out):
    from slabwise.sources.auction_titles import match_title
    res = {}
    for x in json.load(open(src)):
        c, _ = match_title(x)
        res[x] = c
    json.dump(res, open(out, "w"))


def compare(off, on, result):
    a, b = json.load(open(off)), json.load(open(on))
    changed = [(t, a[t], b[t]) for t in a if a[t] and b.get(t) and a[t] != b[t]]
    lost = [(t, a[t]) for t in a if a[t] and not b.get(t)]
    new = [(t, b[t]) for t in b if b[t] and not a.get(t)]
    random.seed(62)
    res = dict(titles=len(a), P1_changed=len(changed), P1_examples=changed[:20], P2_lost=len(lost), P2_examples=lost[:20],
               new=len(new), new_by_card=dict(sorted(((c, sum(1 for _, x in new if x == c)) for c in {x for _, x in new}),
                                                     key=lambda kv: -kv[1])),
               P3_sample=random.sample(new, min(40, len(new))))
    json.dump(res, open(result, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k in ("titles", "P1_changed", "P2_lost", "new")}))


if __name__ == "__main__":
    {"titles": titles, "read": read, "compare": compare}[sys.argv[1]](*sys.argv[2:])
