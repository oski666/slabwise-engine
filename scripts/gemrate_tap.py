"""The "tap" (D189, D190): how many new PSA copies of a card arrive, against how many the market absorbs.

Usage: PYTHONPATH=. python scripts/gemrate_tap.py data/raw/gemrate/sets.json data/raw/sales_all.csv [out.json]

Input: the GemRate set pages read from Oscar's browser (scripts/browser/gemrate_sets.js), one entry per catalogue set
with the rows whose card number matches ours. A row is matched to a catalogue card by number and name; the printing
("parallel") must be the base one ("Base", "Holo" or empty) for our base cards, "1st Edition" / "Shadowless" for the
edition pages (D141).
For each card: weekly new gradings (all grades) from the 52-week cumulative trend; the last 13 weeks against the 39
before; new PSA 10 in the last two periods GemRate reports; PSA sales of the card per week in our data (last 13
weeks); the ratio new gradings / sales ("tap ratio": above 1, more copies arrive than change hands).
Main measure (D190): new PSA 10 in the last 30 days (GemRate) against PSA 10 sold in 30 days in our data; above 1.5
"aperto", 0.67-1.5 "equilibrio", below 0.67 "chiuso". Writes one entry per card. Nothing here enters the prices.
"""
import json
import re
import sys

import numpy as np
import pandas as pd

src, sales_path = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else "data/raw/gemrate/tap.json"
sets = json.load(open(src))
sales = pd.read_csv(sales_path, low_memory=False)
sales = sales[sales["excluded"].isna()]
sales["date"] = pd.to_datetime(sales["date"], utc=True, format="mixed")
t1 = sales["date"].max()
recent = sales[sales["date"] > t1 - pd.Timedelta(weeks=13)]
per_card = recent.groupby("card").size()
per_card10 = recent[recent["grade"] == 10].groupby("card").size()


def norm_no(s):
    s = str(s or "").upper()
    s = re.sub(r"^0+(?=\d)", "", s)
    return re.sub(r"^([A-Z]+)0+(\d)", r"\1\2", s)


def simple(s):
    return re.sub(r"[^a-z]", "", str(s).lower().replace("holo", ""))


# D211: a GemRate row whose total of PSA gradings is not within half and double the PSA total we already hold for the card
# (tcgcharts) is another printing or another card under the same number: it is dropped (e.g. Pikachu Base Set 58: 23
# against 19,499).
import os
_TC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "tcgcharts", "cards.json")
TC_TOTAL = {k: (v or {}).get("psa_population") for k, v in json.load(open(_TC)).items()} if os.path.exists(_TC) else {}
BASE_PAR = {"", "base", "holo", "none", "unlimited"}
# D207: for modern cards GemRate writes the rarity in "parallel" (there is no other printing of the card): these labels are
# the base printing too. Any other label (1st Edition, Shadowless, Trainer Deck, Cracked Ice, Russian...) stays a variant.
RARITY_PAR = {"special illustration rare", "illustration rare", "secret", "hyper rare", "mega hyper rare", "ultra rare",
              "black white rare", "gold star", "pokemon x van gogh",
              "special art rare", "art rare", "bw rare", "mega attack rare", "mega ultra rare"}   # D261: Japanese rarity names
res = {}
for s in sets.values() if isinstance(sets, dict) else sets:
    for cid, name, no in s["cards"]:
        for edition, par_ok in ((None, BASE_PAR | RARITY_PAR), ("/1st", {"1st edition"}), ("/shadowless", {"shadowless"})):
            rows = [r for r in s["rows"] if norm_no(r["card_number"]) == norm_no(no)
                    and (r.get("parallel") or "").strip().lower() in par_ok
                    and simple(name.split(" ")[0]) in simple(r.get("name"))]
            if len(rows) > 1:                                  # D222: our cards are never the reverse foil (D150 excludes it)
                rows = [r for r in rows if "reverse" not in str(r.get("name")).lower()]
            if len(rows) != 1:
                continue
            r = rows[0]
            _tot = TC_TOTAL.get(cid + (edition or ""))
            if _tot and r.get("card_total_grades") and not 0.5 <= float(r["card_total_grades"]) / _tot <= 2:
                continue
            tr = np.array(r.get("grading_trend") or [], dtype=float)
            if len(tr) < 14:
                continue
            wk = np.diff(tr)
            last13, before = wk[-13:].mean(), (wk[:-13].mean() if len(wk) > 13 else np.nan)
            key = cid + (edition or "")
            sold = int(per_card.get(key, 0))
            sold10_30 = float(per_card10.get(key, 0)) / 13 * 30 / 7          # D190: PSA 10 sold in 30 days, from the last 13 weeks
            new10_30 = r.get("c10_diff_p1")                                    # new PSA 10 in the last 30 days (GemRate)
            ratio10 = round(new10_30 / sold10_30, 2) if new10_30 is not None and sold10_30 > 0 else None
            state = None if ratio10 is None else "aperto" if ratio10 > 1.5 else "chiuso" if ratio10 < 0.67 else "equilibrio"
            res[key] = dict(new10_30=new10_30, sold10_30=round(sold10_30, 1), tap10=ratio10, tap_state=state,
                            new_all_30=r.get("ct_diff_p1"), gemrate=r["gemrate_id"], set_name=s["set_name"], year=s["year"], parallel=r.get("parallel"),
                            total=int(r["card_total_grades"]), psa10=int(r["g10"] or 0), psa9=int(r["g9"] or 0), psa8=int(r.get("g8") or 0), psa7=int(r.get("g7") or 0),
                            gem_rate=r.get("card_gem_rate"), new_week_13=round(float(last13), 1),
                            new_week_before=round(float(before), 1) if before == before else None,
                            new_psa10_p1=r.get("c10_diff_p1"), new_psa10_p2=r.get("c10_diff_p2"),
                            sold_week_13=round(sold / 13, 1),
                            tap_ratio=round(float(last13) / (sold / 13), 2) if sold else None,
                            trend=[int(x) for x in tr], updated=r.get("last_updated"))
json.dump(res, open(out, "w"), indent=0)
print(len(res), "carte con il rubinetto ->", out)
