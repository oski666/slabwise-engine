"""Sales CSV for the automatic site build (GitHub Actions, D75): the committed base CSV (sales before Alt, built
from the raw archives with scripts/apify_to_csv.py) plus the Alt sales collected so far (data/raw/alt).

Usage: PYTHONPATH=. python scripts/build_sales.py data/raw/sales_base.csv data/raw/alt data/raw/sales_all.csv [data/raw/tcgcharts]
"""
import csv
import sys

from slabwise.sources.alt_merge import alt_rows
from slabwise.sources.tcgcharts_merge import tcgcharts_rows

base, alt_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
rows = list(csv.DictReader(open(base, newline="")))
got, why, _ = alt_rows(alt_dir, {r["item_id"] for r in rows if r["venue"] == "ebay"})
if len(sys.argv) > 4:                                 # D77: eBay sales read from tcgcharts
    tc, w2 = tcgcharts_rows(sys.argv[4], {r["item_id"] for r in rows + got if str(r["item_id"]).startswith("ebay:")},
                            [(r["card"], r["grade"], r["date"], r["price_usd"]) for r in rows + got if r["venue"] != "ebay"])
    got += tc
    why += w2
from slabwise.sources.auction_titles import refine_variant
n_amb = 0
for r in rows + got:                                  # D81: printings PSA keeps apart, also in sales collected before
    if r["card"] in ("base1-58/1st", "base1-58/shadowless", "base1-8/1st") and not r.get("excluded"):
        cid, bad = refine_variant(r["card"], r.get("title"))
        if bad:
            r["excluded"], n_amb = bad, n_amb + 1
        else:
            r["card"] = cid
why["variante ambigua"] += n_amb
import json
import os
_reg = os.path.join(os.path.dirname(os.path.abspath(base)), "eccezioni", "registro.json")   # D275: Oscar's decisions
if os.path.exists(_reg):
    reg = json.load(open(_reg))
    n_exc = 0
    for r in rows + got:
        d = reg.get(str(r["item_id"]))
        if d and d.get("stato") == "esclusa" and not r.get("excluded"):
            r["excluded"], n_exc = "esclusa da Oscar: " + (d.get("motivo") or "prezzo di un'altra stampa"), n_exc + 1
    why["eccezione confermata da Oscar"] += n_exc
if os.environ.get("SLABWISE_JA_MARKETS") == "1":     # D280: SNKRDUNK and Cardova, preview branch only
    from slabwise.sources.ja_markets import ja_market_rows
    _jr, _jw = ja_market_rows(os.path.dirname(os.path.abspath(base)), os.path.join("data", "fx_jpy.json"))
    got += _jr
    why += _jw
fields = ["item_id", "date", "card", "grade", "price_usd", "venue", "cert", "best_offer_hidden", "title", "excluded"]
with open(out, "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=fields)
    wr.writeheader()
    wr.writerows(rows + got)
print(f"{len(rows)} vendite di base + {len(got)} da Alt e tcgcharts -> {out}")
for k, v in why.most_common():
    print(f"  {k}: {v}")
