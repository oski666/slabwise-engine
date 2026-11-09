"""Real data for the site (P14): the LVM run on the real sales CSV, in the same shape as demo.json.

Usage: PYTHONPATH=. python prototype/build_real_data.py data/raw/sales_all.csv data/raw/era_map.json
Output: prototype/data/real.json (git-ignored: built from collected sales).
Only catalogue cards (base printing) with at least MIN_SALES real sales are shown. Populations
and listings are not collected yet: those fields are null / empty and the site says so.
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from slabwise.calibrate import calibrate_clean  # noqa: E402
from slabwise.identity import identity_layer  # noqa: E402
from slabwise.backtest import TIERS, tier_of  # noqa: E402
from slabwise.index import EraIndex  # noqa: E402
from slabwise.model import LatentValueModel  # noqa: E402
from slabwise.schema import GRADES  # noqa: E402
from slabwise.sources.csv_sales import era_of, load_sales_csv  # noqa: E402

MIN_SALES = 5
Z = 1.2816
path, era_path = sys.argv[1], sys.argv[2]
catalog = json.load(open(os.path.join(HERE, "data", "cards.json")))
catalog_ja = json.load(open(os.path.join(HERE, "data", "cards_ja.json")))      # Japanese printings (D28)
catalog += catalog_ja
thumbs = json.load(open(os.path.join(HERE, "data", "images.json")))
hires = json.load(open(os.path.join(HERE, "data", "hires.json")))
from slabwise.series import ERAS, SERIES, JA_SERIES, series_of, is_promo  # noqa: E402,F401  (D121, D154)

raw = pd.read_csv(path)
t0 = pd.to_datetime(raw["date"], utc=True, format="mixed").min().normalize()
sales, cards = load_sales_csv(path)
era_map = json.load(open(era_path))
eras = sorted(set(era_map.values()) | {era_of(c, era_map) for c in cards})   # eras known only by prefix too (D117)
era = np.array([eras.index(era_of(c, era_map)) for c in cards])
clean, removed = identity_layer(sales, None, verify_certs=False)
W = int(clean["week"].max()) + 1
train = max(26, W // 3)
params, _, _ = calibrate_clean(clean, len(cards), era, len(eras), train, trend=False)   # adopted method: v1.2 until D33 is decided
_v = os.environ.get("SLABWISE_LADDER", "")             # test switch for v1.14 (protocol §20): "steps" or "pops"
params.step_prior = params.step_prior or _v in ("steps", "pops")
params.pop_steps = params.pop_steps or _v == "pops"
params.card_drift = params.card_drift or os.environ.get("SLABWISE_CARD_DRIFT") == "1"   # protocol §36 arm B (D204); off on the site
params.grade_jump = os.environ.get("SLABWISE_GRADE_JUMP", "1") == "1"   # v1.20 (D210): jumps of a single grade; "0" = v1.15 (tests)
params.grade_jump_recent = os.environ.get("SLABWISE_GRADE_JUMP_RECENT", "0") == "1"   # D220 (protocol §40): arm D/E
if os.environ.get("SLABWISE_STEP_T"):                  # D220 (protocol §40): arm E, steps with 2 degrees of freedom
    params.step_t = float(os.environ["SLABWISE_STEP_T"])
REVIEW_RECENT = os.environ.get("SLABWISE_REVIEW_RECENT", "1") == "1"   # v1.20 (D210): review against the recent sales of E2r; "0" = D98 on 13 weeks
lvm = LatentValueModel(len(cards), era, len(eras), params)
lvm.set_parents([cards.index(c.split("/")[0]) if "/" in c and c.split("/")[0] in cards else -1 for c in cards])   # variants (v1.13/v1.15 switches)
_tc_cards = os.path.join(HERE, "..", "data", "raw", "tcgcharts", "cards.json")
if params.pop_steps and os.path.exists(_tc_cards):      # v1.14 (D101): PSA populations from tcgcharts, base printings only
    _tc = json.load(open(_tc_cards))
    lvm.set_pops([[float((_tc.get(c, {}).get("pop") or {}).get(str(g)) or np.nan) for g in (10, 9, 8, 7)] for c in cards])
groups = {w: g for w, g in clean.groupby("week")}
est = np.full((W, len(cards), 4), np.nan)
sd = np.full((W, len(cards), 4), np.nan)
# published index (v1.4, D39), grouped by series since D121: the algorithm is the same, the groups are the ones on the page
# D142: Japanese printings have an index of their own; the English indices hold English cards only
# D154: five eras of the market; promo sets stay out of the era and general indices
ix_group = lambda c: "Giappone" if c.startswith("ja:") else (None if is_promo(c) else series_of(c.split("/")[0]))  # noqa: E731
series_names = sorted({ix_group(c) for c in cards} - {None})
ser_id = np.array([series_names.index(ix_group(c)) if ix_group(c) else -1 for c in cards])
_jera = sorted({series_of(c) for c in cards if c.startswith("ja:")})
_eq = np.array([_jera.index(series_of(c)) if c.startswith("ja:") else 100 + int(ser_id[i]) for i, c in enumerate(cards)])   # D252: Japanese eras
eidx = EraIndex(ser_id, len(series_names), k=int(os.environ.get("SLABWISE_IX_K", "20")), quota=_eq)   # §31 (D169): 20 items per era; §53 (D252):
# inside "Giappone" equal seats per Japanese era; an English era is a single sub-group, so its basket is the same as without quota
# D136: the general index (whole catalogue, 30 items) and set indices (sets with at least 8 catalogue cards)
_qg = np.array([-1 if c.startswith("ja:") or is_promo(c) else series_names.index(ix_group(c)) for c in cards])   # D250: the era of each item
aidx = EraIndex(np.where(_qg >= 0, 0, -1), 1, k=int(os.environ.get("SLABWISE_IX_KALL", "60")), quota=_qg)   # D169: 60 items; D250: 12 per era
SET_MIN = 8
_set_of = lambda c: c.split("/")[0].rsplit("-", 1)[0]
_base_cards = [c for c in cards if "/" not in c and not c.startswith("ja:")]
set_names = sorted({_set_of(c) for c in _base_cards if sum(_set_of(x) == _set_of(c) for x in _base_cards) >= SET_MIN})
sidx = EraIndex(np.array([set_names.index(_set_of(c)) if not c.startswith("ja:") and _set_of(c) in set_names else -1 for c in cards]), len(set_names))
# D244: replay from a saved state. The weekly loop only depends on the sales of the weeks it has seen, the catalogue,
# the parameters and the code; a state saved after week w is reused when all of those are unchanged up to w, and the
# run continues from w + 1. Same arithmetic in the same order, so the result is the full run's, bit for bit.
import hashlib, pickle, glob  # noqa: E401,E402
QTEST = os.environ.get("SLABWISE_IX_QUOTA_TEST") == "1"  # protocol §51 (D245): a general index with seats per era, alongside
CKPT = None if QTEST else os.environ.get("SLABWISE_CKPT")   # folder of saved states (the build keeps it in the Actions cache)
JTEST = os.environ.get("SLABWISE_IX_JA_TEST") == "1"   # protocol §53 (D251): the Japanese index with seats per era
if JTEST:
    CKPT = None
    _jnames = sorted({series_of(c) for c in cards if c.startswith("ja:")})
    _jq = np.array([_jnames.index(series_of(c)) if c.startswith("ja:") else -1 for c in cards])
    jqidx = EraIndex(np.where(_jq >= 0, 0, -1), 1, k=20, quota=_jq)
    jmidx = EraIndex(_jq, len(_jnames), k=20)
if QTEST:                                               # §51/§52: A is now the general of D169 (most traded), Q the one in use (D250)
    qidx = EraIndex(np.where(_qg >= 0, 0, -1), 1, k=60)
_code = b"".join(open(os.path.join(HERE, "..", f), "rb").read() for f in
                 ("slabwise/model.py", "slabwise/index.py", "slabwise/stats.py", "prototype/build_real_data.py") if os.path.exists(os.path.join(HERE, "..", f)))
_static = hashlib.sha256(repr((np.__version__, pd.__version__, sys.version, cards, eras, era.tolist(), str(t0), repr(params), series_names, set_names, ser_id.tolist(),
                               os.environ.get("SLABWISE_IX_K", "20"), os.environ.get("SLABWISE_IX_KALL", "60"))).encode() + _code).hexdigest()
_chain, _h = [], hashlib.sha256(_static.encode())
for w in range(W):
    g_ = groups.get(w)
    _h.update(b"|" + (pd.util.hash_pandas_object(g_, index=False).values.tobytes() + str(list(g_.columns)).encode() if g_ is not None else b"-"))
    _chain.append(_h.hexdigest())
w0 = 0
if CKPT:
    os.makedirs(CKPT, exist_ok=True)
    best = None
    for f in glob.glob(os.path.join(CKPT, "state_*.pkl")):
        try:
            head = json.load(open(f[:-4] + ".json"))
            if head["w"] < W and head["chain"] == _chain[head["w"]] and (best is None or head["w"] > best[0]):
                best = (head["w"], f)
        except Exception:
            pass
    if best:
        try:
            with open(best[1], "rb") as fh:
                lvm_, eidx_, aidx_, sidx_, e_, s_ = pickle.load(fh)
            lvm, eidx, aidx, sidx = lvm_, eidx_, aidx_, sidx_
            est[:best[0] + 1], sd[:best[0] + 1] = e_, s_
            w0 = best[0] + 1
        except Exception as ex:                         # an unreadable state never stops the build: full run
            print("D244: stato illeggibile, calcolo completo:", ex, flush=True)
    print(f"D244: {'ripartenza dalla settimana ' + str(w0) + ' di ' + str(W) if w0 else 'calcolo completo'} ", flush=True)
_save_at = {W - k for k in (2, 5, 9, 14, 27) if W - k >= 0}
_saved = []
for w in range(w0, W):
    lvm.ingest(w, groups.get(w, clean.iloc[:0]))
    est[w], sd[w] = lvm.estimates_with_sd(w)
    eidx.update(w, lvm, est[w])
    aidx.update(w, lvm, est[w])
    sidx.update(w, lvm, est[w])
    if QTEST:
        qidx.update(w, lvm, est[w])
    if JTEST:
        jqidx.update(w, lvm, est[w])
        jmidx.update(w, lvm, est[w])
    if CKPT and w in _save_at:
        f = os.path.join(CKPT, f"state_new_{w}.pkl")
        with open(f, "wb") as fh:
            pickle.dump((lvm, eidx, aidx, sidx, est[:w + 1], sd[:w + 1]), fh, protocol=5)
        json.dump({"w": w, "chain": _chain[w]}, open(f[:-4] + ".json", "w"))
        _saved.append(f)
if CKPT and _saved:                                     # states before the restart point are still valid (the chain is cumulative)
    for f in glob.glob(os.path.join(CKPT, "state_*.pkl")):
        if f not in _saved and json.load(open(f[:-4] + ".json"))["w"] >= w0:
            for x in (f, f[:-4] + ".json"):
                if os.path.exists(x):
                    os.remove(x)
    for f in _saved:
        w_ = f.rsplit("_", 1)[1][:-4]
        for ext in (".pkl", ".json"):
            os.replace(f[:-4] + ext, os.path.join(CKPT, f"state_{w_}{ext}"))
if QTEST:                                               # §51: the series for scripts/ix_quota_test.py
    os.makedirs(os.path.join(HERE, "..", "results", "ix_quota"), exist_ok=True)
    _eras5 = [n for n in series_names if n != "Giappone"]
    json.dump(dict(weeks=[str((t0 + pd.Timedelta(weeks=w + 1)).date()) for w in range(W)],
                   A=[None if not np.isfinite(v) else float(v) for v in qidx.series(0, W)],
                   Q=[None if not np.isfinite(v) else float(v) for v in aidx.series(0, W)],
                   eras={n: [None if not np.isfinite(v) else float(v) for v in eidx.series(series_names.index(n), W)] for n in _eras5},
                   quota_log=[[int(w_), {series_names[g]: list(v) for g, v in d_.items()}] for w_, d_ in aidx.quota_log],
                   A_baskets=[[int(w_), [series_names[_qg[c]] if _qg[c] >= 0 else "?" for c, g in b_]] for w_, e_, b_ in qidx.history]),
              open(os.path.join(HERE, "..", "results", "ix_quota", "series.json"), "w"))
if JTEST:                                               # §53: the series for scripts/ix_quota_test.py (A, Q, eras, seats)
    os.makedirs(os.path.join(HERE, "..", "results", "ix_ja"), exist_ok=True)
    _gj = series_names.index("Giappone")
    _f = lambda xs: [None if not np.isfinite(v) else float(v) for v in xs]   # noqa: E731
    json.dump(dict(weeks=[str((t0 + pd.Timedelta(weeks=w + 1)).date()) for w in range(W)],
                   A=_f(eidx.series(_gj, W)), Q=_f(jqidx.series(0, W)),
                   eras={n: _f(jmidx.series(i, W)) for i, n in enumerate(_jnames)},
                   quota_log=[[int(w_), {_jnames[g]: list(v) for g, v in d_.items()}] for w_, d_ in jqidx.quota_log],
                   A_baskets=[[int(w_), [series_of(cards[c]) for c, g in b_]] for w_, e_, b_ in eidx.history if e_ == _gj]),
              open(os.path.join(HERE, "..", "results", "ix_ja", "series.json"), "w"))
if CKPT:                                                # at most 6 states, the most recent ones
    _all = sorted(glob.glob(os.path.join(CKPT, "state_*.pkl")), key=lambda f: json.load(open(f[:-4] + ".json"))["w"])
    for f in _all[:-6]:
        for x in (f, f[:-4] + ".json"):
            os.remove(x)

try:                                                  # ECB reference rate, USD per EUR
    u = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1&format=jsondata"
    d = json.load(urllib.request.urlopen(u, timeout=20))
    s_ = d["dataSets"][0]["series"]
    usd_per_eur = list(s_[list(s_)[0]]["observations"].values())[0][0]
    rate_date = d["structure"]["dimensions"]["observation"][0]["values"][-1]["id"]
except Exception:
    usd_per_eur, rate_date = None, None
EUR = round(1 / usd_per_eur, 4) if usd_per_eur else 0.9
asof = min((t0 + pd.Timedelta(weeks=W)).date(), (t0 + pd.Timedelta(days=float(clean["day"].max()))).date())   # never after the last sale
day = lambda d: str((t0 + pd.Timedelta(days=float(d))).date())            # noqa: E731
wk = lambda w: str((t0 + pd.Timedelta(weeks=int(w) + 1)).date())          # noqa: E731
cid = {c: i for i, c in enumerate(cards)}


def why(pg, r):
    if pg >= 0.5:
        return None
    return "molto sotto il valore: possibile carta rovinata, falso o voto sbagliato" if r < 0 else \
        "molto sopra il valore: possibile lotto, asta gonfiata o Best Offer"


# PSA populations per grade from tcgcharts (D77): display and capitalisation only, never in the value
tc_cards = os.path.join(HERE, "..", "data", "raw", "tcgcharts", "cards.json")
POP = {cid_: m.get("pop") or {} for cid_, m in json.load(open(tc_cards)).items()} if os.path.exists(tc_cards) else {}
out_cards = []
# D141: 1st Edition and Shadowless printings estimated by the engine get a page of their own; their base becomes "Unlimited"
_by_id = {c["id"]: c for c in catalog}
VARIANT_NAME = {"1st": "1st Edition", "shadowless": "Shadowless", "1st-shadowless": "1st Edition", "1st-red": "1st Edition, Red Cheeks",
                "1st-yellow": "1st Edition, Yellow Cheeks", "shadowless-red": "Shadowless, Red Cheeks", "shadowless-yellow": "Shadowless, Yellow Cheeks"}
variants = [dict(_by_id[v.split("/")[0]], id=v, n=f'{_by_id[v.split("/")[0]]["n"]} ({VARIANT_NAME.get(v.split("/")[1], v.split("/")[1])})', variant=v.split("/")[1])
            for v in cards if "/" in v and v.split("/")[0] in _by_id]
for c in catalog + variants:
    i = cid.get(c["id"])
    if i is None or (clean["card"] == i).sum() < MIN_SALES or lvm.fit[i] is None:
        continue
    first_w = int(clean.loc[clean["card"] == i, "week"].min())
    g_out = []
    for gi, g in enumerate(GRADES):
        now, s_now = est[-1, i, gi], sd[-1, i, gi]
        hist = [[wk(w), round(float(np.exp(est[w, i, gi])), 2), round(float(np.exp(est[w, i, gi] - Z * sd[w, i, gi])), 2),
                 round(float(np.exp(est[w, i, gi] + Z * sd[w, i, gi])), 2)]
                for w in range(first_w, W) if np.isfinite(est[w, i, gi])]
        n_g = int(((clean["card"] == i) & (clean["grade"] == g)).sum())
        n13 = int(((clean["card"] == i) & (clean["grade"] == g) & (clean["week"] >= W - 13)).sum())
        rec = clean.loc[(clean["card"] == i) & (clean["grade"] == g) & (clean["week"] >= W - 13), "price"]
        med13 = float(rec.median()) if len(rec) else None
        if REVIEW_RECENT and len(rec):                    # D204 test: 30 days if >= 5 sales, else the last 5 of the 13 weeks
            _r = clean.loc[(clean["card"] == i) & (clean["grade"] == g) & (clean["week"] >= W - 13)].sort_values("day")
            _d30 = _r.loc[_r["day"] >= clean["day"].max() - 30, "price"]
            med13 = float((_d30 if len(_d30) >= 5 else _r["price"].tail(5)).median())
        # D98: an estimate more than 2x away from the median of its own sales of the last 13 weeks is not shown
        off = bool(med13 and abs(float(now) - np.log(med13)) > np.log(2))
        # D226: eBay (>= 2 sales) and the auction houses (>= 1) of the last 13 weeks more than 5x apart: not the same card
        # and grade for sure (another printing under the same number, or a wrong record); the grade goes under review
        _v13 = clean.loc[(clean["card"] == i) & (clean["grade"] == g) & (clean["week"] >= W - 13), ["price", "venue"]]
        _eb, _au = _v13.loc[_v13["venue"] == "ebay", "price"], _v13.loc[_v13["venue"] != "ebay", "price"]
        venue_split = [round(float(_eb.median()), 2), round(float(_au.median()), 2)] if len(_eb) >= 2 and len(_au) >= 1 and abs(np.log(_au.median() / _eb.median())) > np.log(5) else None
        off = off or bool(venue_split)
        stale = False
        # D141: no sales in 13 weeks and more than 2x away from the last credible sale: not shown either (the page shows that sale)
        if not n13:
            _ok = [o for o, p_ in zip(lvm.obs[i], lvm.fit[i]["pgen"]) if o["g"] == gi and p_ > 0.5]
            if _ok and abs(float(now) - _ok[-1]["y"]) > np.log(2):
                off = stale = True
        # D161: a change is shown only when the grade already had 3 sales of its own at the start of the period
        _mine = clean.loc[(clean["card"] == i) & (clean["grade"] == g), "week"]
        ch30 = round(float(np.exp(now - est[-5, i, gi]) - 1), 4) if (_mine <= W - 5).sum() >= 3 and np.isfinite(est[-5, i, gi]) else None
        ch90 = round(float(np.exp(now - est[-14, i, gi]) - 1), 4) if (_mine <= W - 14).sum() >= 3 and np.isfinite(est[-14, i, gi]) else None
        if off or stale:                                  # D211: no change shown on an estimate the page does not show
            ch30 = ch90 = None
        _p30 = clean.loc[(clean["card"] == i) & (clean["grade"] == g) & (clean["day"] >= clean["day"].max() - 30), "price"].to_numpy()
        _days_g = clean.loc[(clean["card"] == i) & (clean["grade"] == g), "day"]
        last_sale = str((t0 + pd.Timedelta(days=float(_days_g.max()))).date()) if len(_days_g) else None   # D232
        _sb = Z * float(np.sqrt(s_now ** 2 + params.sigma_e ** 2 + params.sigma_q ** 2))
        g_out.append(dict(grade=g, value=round(float(np.exp(now)), 2), lo=round(float(np.exp(now - Z * s_now)), 2),
                          hi=round(float(np.exp(now + Z * s_now)), 2), ch30=ch30,
                          ch90=ch90, pop=POP.get(c["id"], {}).get(str(g)) or POP.get(c["id"], {}).get(g), sales_all=n_g,
                          sales90=n13, last_sale=last_sale, tier=TIERS[int(tier_of(n13, Z * s_now))],      # confidence tier (D47)
                          med90=round(med13, 2) if med13 else None, off=off, stale=stale, venue_split=venue_split,
                          # D208: how far a sale of the last 13 weeks usually lands from the value (median |log|), on all of them
                          disp90=round(float(np.median(np.abs(np.log(rec.to_numpy()) - float(now)))), 4) if n13 >= 5 else None,
                          # D223: share of those sales within 15% of the value (13 weeks, >= 5 sales)
                          in15=round(float(np.mean(np.abs(np.log(rec.to_numpy()) - float(now)) <= np.log(1.15))), 3) if n13 >= 5 else None,
                          # D223: the real sales of the last 30 days (count; 10th, 25th, 75th, 90th percentile with >= 5)
                          n30=int(len(_p30)), q30=[round(float(x), 2) for x in np.percentile(_p30, [10, 25, 75, 90])] if len(_p30) >= 5 else None,
                          # D224: the SlabRange = where sales land: value x exp(+-Z sqrt(s^2 + sigma_e^2 + sigma_q^2))
                          slo=round(float(np.exp(now - _sb)), 2), shi=round(float(np.exp(now + _sb)), 2),
                          history=hist))
    ob, pg = lvm.obs[i], lvm.fit[i]["pgen"]
    sl = []
    for o, p_ in zip(ob, pg):
        gi = o["g"]
        w = min(int(o["t"]), W - 1)
        sl.append(dict(date=day(o["t"] * 7), grade=GRADES[gi], price=round(float(np.exp(o["y"])), 2),
                       venue={0: "eBay", 1: "Casa d'aste", 2: "Prezzo fisso"}[o.get("v", int(o["a"]))], cert=bool(o["k"]), pgen=round(float(p_), 3),
                       why=why(p_, o["y"] - est[w, i, gi])))
    rem = removed[removed["card"] == i]
    excluded = [dict(date=day(d_), grade=int(g), price=round(float(p), 2), why=r)
                for d_, g, p, r in zip(rem["day"], rem["grade"], rem["price"], rem["reason"])]
    out_cards.append(dict(lang=c.get("lang", "en"), en=c.get("en"), en_same=c.get("en_same"), id=c["id"], name=c["n"], variant=c.get("variant"), base=c["id"].split("/")[0] if "/" in c["id"] else None, set=c["set"], no=c["no"], tot=c.get("tot"), series=series_of(c["id"]),
                          rarity=c.get("r"), illustrator=c.get("ill"), img=hires.get(c["id"].split("/")[0]) or thumbs.get(c["id"].split("/")[0]) or c.get("img"),
                          thumb=thumbs.get(c["id"].split("/")[0]), grades=g_out, sales=sl, excluded=excluded, deals=[],
                          beta=round(float(lvm.fit[i]["theta"][4]), 3), n_sales=int((clean["card"] == i).sum())))

_with_var = {c["base"] for c in out_cards if c.get("base")}
for c in out_cards:                                                # D141: the base printing says which one it is
    if c["id"] in _with_var:
        c["name"] += " (Unlimited)"
        c["variants"] = sorted(x["id"] for x in out_cards if x.get("base") == c["id"])
# D135: cards beyond the eBay budget (and Japanese printings) are in the catalogue without their listings checked
from slabwise.ebay_budget import monitored  # noqa: E402
_mon = monitored(json.load(open(os.path.join(HERE, "data", "cards.json"))), datetime.now(timezone.utc).strftime("%Y-%m-%d"))
for c in out_cards:
    if c["id"] not in _mon:
        c["deals_off"] = True
# deals from active eBay listings (D72): only listings with deal probability >= 0.5 reach the site
DEALS_MIN = 0.5
lst_path = os.path.join(HERE, "..", "data", "raw", "ebay", "listings.json")
deals_asof, deal_stats = None, None
if os.path.exists(lst_path):
    from slabwise.deals import landed_eur, score  # noqa: E402
    L_ = json.load(open(lst_path))
    deals_asof = L_["asof"]
    certs_path = os.path.join(HERE, "data", "certs.json")
    known = json.load(open(certs_path))["certs"] if os.path.exists(certs_path) else {}
    rows_ = []
    for r in L_["listings"]:
        i = cid.get(r["card"])
        if i is None or lvm.fit[i] is None:
            continue
        gi = GRADES.index(r["grade"])
        if r.get("cert") and r["cert"] in known:                        # identity: the cert must agree with the title
            last = known[r["cert"]][-1]
            if last[1].split("/")[0] != r["card"] or last[2] != r["grade"]:
                continue
        cost = landed_eur(r["ask_usd"] * EUR, r["ship_usd"] * EUR, r.get("country"))
        rows_.append((r, i, gi, cost))
    if rows_:
        m_ = np.array([est[-1, i, gi] for _, i, gi, _ in rows_])
        s_ = np.array([sd[-1, i, gi] for _, i, gi, _ in rows_])
        pg_, pd_, deal_stats = score([r["ask_usd"] for r, *_ in rows_], [c["landed_eur"] / EUR for *_, c in rows_], m_, s_,
                                     [bool(r.get("cert")) for r, *_ in rows_], params.sigma_q)
        by_card = {c["id"]: c for c in out_cards}
        for (r, i, gi, cost), pg__, pd__, mm in zip(rows_, pg_, pd_, m_):
            if pd__ < DEALS_MIN or r["card"] not in by_card:
                continue
            if any(g_["grade"] == r["grade"] and (g_.get("off") or not g_["sales_all"]) for g_ in by_card[r["card"]]["grades"]):
                continue                                              # D98: no deal against an estimate under review
            by_card[r["card"]]["deals"].append(dict(grade=r["grade"], ask_usd=r["ask_usd"], cert=bool(r.get("cert")),
                                                    **{k: round(v, 2) if isinstance(v, float) else v for k, v in cost.items()},
                                                    value_eur=round(float(np.exp(mm)) * EUR, 2), p_gen=round(float(pg__), 3),
                                                    p_deal=round(float(pd__), 3), suspicious=False, url=r["url"], title=r["title"],
                                                    market=r["market"], seller_pct=r.get("seller_pct"), seller_n=r.get("seller_n"),
                                                    authenticity=r.get("authenticity", False), best_offer=r.get("best_offer", False)))
        for c in out_cards:
            c["deals"].sort(key=lambda d: -d["p_deal"])
    print("annunci", len(L_["listings"]), "valutati", len(rows_), "occasioni >= 0,5", sum(len(c["deals"]) for c in out_cards), deal_stats)

# eras: what we can say honestly without populations
roll = {}
for c in out_cards:
    r_ = roll.setdefault(c["series"], dict(series=c["series"], n=0, sales=0, ch30=[]))
    r_["n"] += 1
    r_["sales"] += c["n_sales"]
    if c["grades"][0]["ch30"] is not None:
        r_["ch30"].append(c["grades"][0]["ch30"])
indexes = {}


def index_stats(ser, basket):
    """D136: components with weight and contribution, returns, volatility, maximum drawdown (ser: log level by week)."""
    v = np.array([x for x in ser if np.isfinite(x)])
    lv = np.exp(v - v[-1])                                   # level relative to today
    weeks = [w for w in range(len(ser)) if np.isfinite(ser[w])]
    ret = {f"w{k}": round(float(1 / lv[-1 - k] - 1), 4) for k in (1, 4, 13, 26, 52) if len(v) > k}
    _y0 = [i for i, w in enumerate(weeks) if wk(w) >= f"{wk(weeks[-1])[:4]}-01-01"]
    if _y0 and _y0[0] > 0:
        ret["ytd"] = round(float(1 / lv[_y0[0] - 1] - 1), 4)
    d = np.diff(v)[-26:]
    vol = round(float(np.std(d, ddof=1) * np.sqrt(52)), 4) if len(d) > 4 else None
    peak = np.maximum.accumulate(v)
    i = int(np.argmin(v - peak))
    mdd = dict(value=round(float(np.exp(v[i] - peak[i]) - 1), 4), at=wk(weeks[i]), peak=wk(weeks[int(np.argmax(v[:i + 1]))]))
    n = len(basket)
    comps = []
    for c, g in basket:
        now, then = est[W - 1, c, g], est[W - 5, c, g]
        ch = float(now - then) if np.isfinite(now) and np.isfinite(then) else None
        comps.append(dict(id=cards[c], grade=GRADES[g], weight=round(1 / n, 4), value=round(float(np.exp(now))) if np.isfinite(now) else None,
                          ch4=round(float(np.exp(ch) - 1), 4) if ch is not None else None, contrib=round(ch / n, 4) if ch is not None else None))
    comps.sort(key=lambda x: -abs(x["contrib"] or 0))
    return dict(returns=ret, vol=vol, mdd=mdd, components=comps)


def publish(idx, e, kind, label):
    """One published index (D121, D136), on the common base week when it exists there, else on its own first week."""
    ser = idx.series(e, W)
    if np.isfinite(ser).sum() < INDEX_MIN_WEEKS:
        return None
    b = index_base_w if np.isfinite(ser[index_base_w]) else int(np.argmax(np.isfinite(ser)))
    ser = ser - ser[b]
    pts = [[wk(w), round(float(100 * np.exp(v)), 2)] for w, v in enumerate(ser) if np.isfinite(v)]
    basket = next((bk for w_, e_, bk in reversed(idx.history) if e_ == e), [])
    return dict(kind=kind, label=label, base=wk(b), points=pts, sizes=[[wk(w_), len(bk)] for w_, e_, bk in idx.history if e_ == e], ch30=round(pts[-1][1] / pts[max(0, len(pts) - 5)][1] - 1, 4),
                basket=[f"{cards[c]} PSA {GRADES[g]}" for c, g in basket], **index_stats(ser, basket))


_ser = {e: eidx.series(e, W) for e in range(len(series_names))}
INDEX_MIN_WEEKS = 26                                       # D121: a series index is shown once it has half a year
_first = [int(np.argmax(np.isfinite(v))) for v in _ser.values() if np.isfinite(v).sum() >= INDEX_MIN_WEEKS]
index_base_w = max(_first) if _first else 0                # D121: one common base, 100 on the same week for every series
for e, name in enumerate(series_names):
    ser = _ser[e]
    if np.isfinite(ser).sum() < INDEX_MIN_WEEKS:
        continue
    ser = ser - ser[index_base_w] if np.isfinite(ser[index_base_w]) else ser
    pts = [[wk(w), round(float(100 * np.exp(v)), 2)] for w, v in enumerate(ser) if np.isfinite(v)]
    last_basket = next((b for w_, e_, b in reversed(eidx.history) if e_ == e), [])
    indexes[name] = dict(points=pts, ch30=round(pts[-1][1] / pts[max(0, len(pts) - 5)][1] - 1, 4),
                         basket=[f"{cards[c]} PSA {GRADES[g]}" for c, g in last_basket], **index_stats(ser, last_basket),
                         sizes=[[wk(w_), len(bk)] for w_, e_, bk in eidx.history if e_ == e])
# D137: PSA graded total per card (all grades), for the share of 10s on the card page
_TCP = json.load(open(tc_cards)) if os.path.exists(tc_cards) else {}
for c in out_cards:
    c["psa_total"] = (_TCP.get(c["id"]) or {}).get("psa_population")
# D165, D209: price for rarity (PSA only). log PSA 10 value on log PSA 10 population, one slope for all and a level for each
# era and language (groups of at least 8 cards); x = value / value expected for its population, in its group.
# Hidden gem (D209): x < 0.5 and a PSA 10 population at or below the median of its group. Only PSA 10 grades with at least
# 3 sales in 13 weeks and not in review.
_rr = []
for c in out_cards:
    g10 = next((g for g in c["grades"] if g["grade"] == 10), None)
    try:
        pop10 = float(g10["pop"]) if g10 and g10.get("pop") else 0
    except (TypeError, ValueError):
        pop10 = 0
    if g10 and pop10 > 0 and g10["sales90"] >= 3 and not g10.get("off"):
        _rr.append((c, np.log(pop10), np.log(g10["value"]), (c.get("lang") == "ja", c["series"])))
_cnt = {}
for r in _rr:
    _cnt[r[3]] = _cnt.get(r[3], 0) + 1
_rr = [r for r in _rr if _cnt[r[3]] >= 8]
rarity_fit = None
if len(_rr) >= 30:
    _x = np.array([r[1] for r in _rr]); _y = np.array([r[2] for r in _rr])
    _G = sorted(set(r[3] for r in _rr))
    _X = np.column_stack([_x] + [[1.0 if r[3] == k else 0.0 for r in _rr] for k in _G])
    _beta = np.linalg.lstsq(_X, _y, rcond=None)[0]
    _res = _y - _X @ _beta
    _med = {k: float(np.median([r[1] for r in _rr if r[3] == k])) for k in _G}
    for (c, lx, _, k), e in zip(_rr, _res):
        c["rarity_price"] = dict(x=round(float(np.exp(e)), 3), pop10=int(round(float(np.exp(lx)))),
                                 pop10_med=int(round(float(np.exp(_med[k])))), gem=bool(np.exp(e) < 0.5 and lx <= _med[k]))
    # Japanese against English at equal PSA 10 population (one line for all, as in D165): the note on the Japan page
    _b1, _a1 = np.polyfit(_x, _y, 1)
    _r1 = _y - (_a1 + _b1 * _x)
    _ja = [e for r, e in zip(_rr, _r1) if r[3][0]]
    _en = [e for r, e in zip(_rr, _r1) if not r[3][0]]
    rarity_fit = dict(n=len(_rr), slope=round(float(_beta[0]), 3), groups=len(_G),
                      gems=sum(1 for c, *_ in _rr if c["rarity_price"]["gem"]), n_ja=len(_ja),
                      ja_vs_en=round(float(np.exp(np.mean(_ja) - np.mean(_en))), 3) if _ja and _en else None)
    print("prezzo per rarità", rarity_fit)
index_all = publish(aidx, 0, "generale", "Generale")
_set_label = {}
for c in cards:
    _set_label.setdefault(_set_of(c), next((x["set"] for x in catalog if x["id"] == c), _set_of(c)))
index_sets = {k: v for k, v in ((s_, publish(sidx, e, "set", _set_label.get(s_, s_))) for e, s_ in enumerate(set_names)) if v}
print("indice generale", index_all and index_all["points"][-1], "indici di set", list(index_sets))
rollups = [dict(series=r_["series"], n=r_["n"], sales=r_["sales"], ch30=round(float(np.median(r_["ch30"])), 4) if r_["ch30"] else None, cap=None, top3=None)
           for r_ in sorted(roll.values(), key=lambda x: ERAS.index(x["series"]) if x["series"] in ERAS else 99)]   # D154: in time order

# the stories of the week, from real sales only
# D182: only movements the site itself shows (ch30, D161: own sales at the start of the period), never the jump from a
# new card's prior; only grades with at least 3 recent sales of their own
def _story_ok(g):                       # also an established history: the 90-day change is shown (D161), so not a newcomer
    return g["sales90"] >= 3 and g.get("ch90") is not None and not g.get("off") and not g.get("stale")


cand = [(abs(g["ch30"]), c, gi) for c in out_cards for gi, g in enumerate(c["grades"])
        if g.get("ch30") is not None and g["hi"] / g["lo"] < 1.5 and _story_ok(g)]
stories = []
if cand:
    _, mc, mg = max(cand, key=lambda x: x[0])
    g = mc["grades"][mg]
    ch = g["ch30"]
    stories.append(dict(kind="mover", title="Lo slab del mese", card=mc["id"], grade=g["grade"], value=g["value"], lo=g["lo"], hi=g["hi"],
                        change7=round(float(ch), 4),
                        hook=f"{mc['name']} PSA {g['grade']}: {'+' if ch > 0 else '−'}{abs(ch) * 100:.0f}% in 30 giorni",
                        reel=dict(mode="trend", card=mc["id"], grade=g["grade"], prev=round(g["value"] / (1 + ch) * EUR), now=round(g["value"] * EUR), days=30)))
recent = str(asof - timedelta(days=60))
caught = [(s_["pgen"], c, s_) for c in out_cards for s_ in c["sales"] if s_["date"] >= recent and s_["pgen"] < 0.5]
if caught:
    pg_, cc, ss = min(caught, key=lambda x: x[0])
    stories.append(dict(kind="caught", title="Smascherata", card=cc["id"], grade=ss["grade"], price=ss["price"], pgen=ss["pgen"], why=ss["why"],
                        value=next(g["value"] for g in cc["grades"] if g["grade"] == ss["grade"]),
                        hook="Venduto a $" + f"{ss['price']:,.0f}".replace(",", ".") + ", ma per il nostro modello non è credibile"))
lad = [(c["grades"][0]["value"] / c["grades"][1]["value"], c) for c in out_cards
       if len(c["grades"]) > 1 and c["grades"][0]["grade"] == 10 and c["grades"][1]["grade"] == 9 and _story_ok(c["grades"][0]) and _story_ok(c["grades"][1])]
if lad:
    lr, lc = max(lad, key=lambda x: x[0])
    stories.append(dict(kind="ladder", title="Il salto di voto", card=lc["id"], ratio=round(lr, 2), v10=lc["grades"][0]["value"], v9=lc["grades"][1]["value"],
                        hook=f"{lc['name']}: un PSA 10 vale {lr:.1f} volte un PSA 9".replace(".", ",")))
def _nm(c):                              # a Japanese printing is named after its English twin in the reels
    if c.get("lang") == "ja" and c.get("en"):
        tw = next((x for x in out_cards if x["id"] == c["en"]), None)
        if tw:
            return tw["name"] + " giapponese"
    return c["name"]


# D184: two more stories (the biggest fall, the era that moved most) and the same five all week long
falls = [(g["ch30"], c, gi) for c in out_cards for gi, g in enumerate(c["grades"])
         if g.get("ch30") is not None and g["ch30"] < 0 and g["hi"] / g["lo"] < 1.5 and _story_ok(g) and c["id"] not in {x.get("card") for x in stories}]
if falls:
    _, fc, fg = min(falls, key=lambda x: x[0])
    g = fc["grades"][fg]
    ch = g["ch30"]
    stories.insert(1, dict(kind="mover", title="In discesa", card=fc["id"], grade=g["grade"], value=g["value"], lo=g["lo"], hi=g["hi"],
                           change7=round(float(ch), 4), hook=f"{_nm(fc)} PSA {g['grade']}: −{abs(ch) * 100:.0f}% in 30 giorni",
                           reel=dict(mode="trend", card=fc["id"], grade=g["grade"], prev=round(g["value"] / (1 + ch) * EUR), now=round(g["value"] * EUR), days=30)))
_em = []
for e_, ix_ in (indexes or {}).items():
    pts_ = (ix_ or {}).get("points") or []
    if len(pts_) > 4 and pts_[-5][1]:
        _em.append((pts_[-1][1] / pts_[-5][1] - 1, e_))
if _em:
    ech, era_ = max(_em, key=lambda x: abs(x[0]))
    ecap = sum(g["value"] * (g.get("pop") or 0) for c in out_cards if c["series"] == era_ and c["lang"] != "ja" for g in c["grades"]) if era_ != "Giappone" else \
        sum(g["value"] * (g.get("pop") or 0) for c in out_cards if c["lang"] == "ja" for g in c["grades"])
    stories.append(dict(kind="era", title="L'era della settimana", series=era_, change=round(float(ech), 4), cap=round(float(ecap)),
                        hook=f"Indice {era_}: {'+' if ech >= 0 else '−'}{abs(ech) * 100:.1f}% in 4 settimane".replace(".", ",")))
_monday = date.today() - timedelta(days=date.today().weekday())
_pp = os.path.join(HERE, "data", "pulse.json")
_old = json.load(open(_pp)) if os.path.exists(_pp) else None
_ids = {c["id"] for c in out_cards}
if _old and _old.get("monday") == str(_monday) and all(not x.get("card") or x["card"] in _ids for x in _old["stories"]):
    pulse = dict(week=_old["week"], stories=_old["stories"])                  # this week's stories are already chosen
else:
    pulse = dict(week=f"{asof - timedelta(days=6)}/{asof}", stories=stories)
    json.dump(dict(monday=str(_monday), **pulse), open(_pp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
venues = clean["venue"].value_counts().to_dict()
sold = {c["id"] for c in out_cards}
ja_pending = [dict(id=c["id"], name=c["n"], set=c["set"], no=c["no"], tot=c.get("tot"), rarity=c.get("r"), illustrator=c.get("ill"),
                   img=c.get("img"), en=c.get("en"), en_same=c.get("en_same"), series=series_of(c["id"]), source=c.get("source"),
                   sales=int((clean["card"] == cid[c["id"]]).sum()) if c["id"] in cid else 0)
              for c in catalog_ja if c["id"] not in sold]
ENGINE = ("LVM v1.20" if params.grade_jump and params.step_t > 0 else "LVM v1.15" if params.step_t > 0 else "LVM v1.14") if params.step_prior and params.pop_steps else "LVM v1.10"      # shown in the seals (D105)
# D149: indices computed with the long history (protocol §29), when the daily run has written them
_if = os.path.join(HERE, "data", "index_full.json")
index_source = None
if os.environ.get("SLABWISE_INDEX_SELF") == "1" and os.environ.get("SLABWISE_TC_HISTORY") == "1":
    # D228: this run has the long history, so it trims its own indices (same rule as index_full_extract.py)
    from slabwise.index_full import extract as _extract_full
    _full = _extract_full(dict(indexes=indexes, index_all=index_all, index_sets=index_sets, asof=str(asof), index_base=wk(index_base_w)))
    json.dump(_full, open(_if, "w"), separators=(",", ":"))
    indexes, index_all, index_sets = _full["indexes"], _full["index_all"], _full["index_sets"]
    index_base_w = None
    index_source = dict(kind="storico", asof=_full.get("asof"), base=_full.get("index_base"))
elif os.path.exists(_if) and not os.environ.get("SLABWISE_TC_HISTORY") and os.environ.get("SLABWISE_INDEX_FULL", "1") == "1":
    _full = json.load(open(_if))
    if set(_full["indexes"]) <= set(series_names):          # D154: a file from the old groups is not used
        indexes, index_all, index_sets = _full["indexes"], _full["index_all"], _full["index_sets"]
        index_base_w = None
        index_source = dict(kind="storico", asof=_full.get("asof"), base=_full.get("index_base"))
    else:
        print("index_full.json ha gruppi diversi da quelli di oggi: indici senza storico")
_ih = os.path.join(HERE, "data", "index_history.json")       # D138: rebuilt index history, only once §27 passed
index_history = json.load(open(_ih)) if os.path.exists(_ih) else None
# D194: the Slab-Meter, the market's temperature, from four facts of this build (no new data, no effect on prices)
def _main_grade(c):                       # the card's most traded grade with a shown 30-day change
    gs = [g for g in c["grades"] if g.get("ch30") is not None and not g.get("off") and not g.get("stale") and g.get("sales_all")]
    return max(gs, key=lambda g: g["sales90"]) if gs else None


_mg = [(c, _main_grade(c)) for c in out_cards if c["lang"] != "ja"]
_mg = [(c, g) for c, g in _mg if g]
_up = sum(1 for _, g in _mg if g["ch30"] > 0.005); _dn = sum(1 for _, g in _mg if g["ch30"] < -0.005)
_breadth = _up / max(1, _up + _dn)
_wk = clean.groupby("week").size()
_last = float(_wk.get(W - 2, 0)); _base = float(np.mean([_wk.get(w, 0) for w in range(W - 10, W - 2)]))   # the last full week against the 8 before
_vol = _last / _base if _base else 1.0
_hi = _lo = 0
for _c, _g in _mg:
    _h = [r[1] for r in (_g.get("history") or [])][-52:]
    if len(_h) >= 13:
        _hi += _h[-1] >= max(_h) * 0.999; _lo += _h[-1] <= min(_h) * 1.001
_hl = _hi / (_hi + _lo) if _hi + _lo else 0.5
_ix = (index_all or {}).get("points") or []
_ixch = _ix[-1][1] / _ix[-5][1] - 1 if len(_ix) > 4 and _ix[-5][1] else 0.0
_clip = lambda x: max(-1.0, min(1.0, x))  # noqa: E731
_parts = dict(breadth=100 * _breadth, volume=50 + 50 * _clip((_vol - 1) / 0.5), highs=100 * _hl, index=50 + 50 * _clip(_ixch / 0.10))
_score = float(np.mean(list(_parts.values())))
_state = "esplode" if _score >= 80 else "caldo" if _score >= 60 else "tiepido" if _score >= 40 else "freddo" if _score >= 20 else "gelo"
slabmeter = dict(score=round(_score, 1), degrees=round(33 + _score * 0.09, 1), state=_state, parts={k: round(v, 1) for k, v in _parts.items()},
                 up=_up, down=_dn, sales_week=int(_last), sales_avg8=round(_base, 1), highs=int(_hi), lows=int(_lo), index_4w=round(_ixch, 4))
print("slab-meter", slabmeter)
# D190, D195: the tap, from the GemRate reads (data/raw/gemrate/tap.json, private, written by scripts/gemrate_tap.py)
tap = {}
_tp = os.path.join(HERE, "..", "data", "raw", "gemrate", "tap.json")
if os.path.exists(_tp):
    _ids = {c["id"] for c in out_cards}
    for _k, _v in json.load(open(_tp)).items():
        if _k in _ids and _v.get("trend"):
            _w = [int(b - a) for a, b in zip(_v["trend"], _v["trend"][1:])]
            tap[_k] = dict(state=_v.get("tap_state"), new10=_v.get("new10_30"), sold10=_v.get("sold10_30"), ratio=_v.get("tap10"),
                           weekly=_w[-52:], total=_v.get("total"), psa10=_v.get("psa10"), asof=_v.get("updated"))
    print("rubinetto", len(tap), "carte")
# D212: when the PSA 10 share from our populations and the one from GemRate's own counts differ by more than 5 points,
# the page gives no single Gem Rate: it says the two counts disagree and shows both; the card leaves the comparisons.
for c in out_cards:
    _t, _g10 = tap.get(c["id"]), next((g for g in c["grades"] if g["grade"] == 10), None)
    if _t and _t.get("total") and _t.get("psa10") is not None and _g10 and _g10.get("pop") and c.get("psa_total"):
        _a, _b = _g10["pop"] / c["psa_total"], _t["psa10"] / _t["total"]
        if abs(_a - _b) > 0.05:
            c["gem_conflict"] = [round(_a, 4), round(_b, 4)]
res = dict(real=True, rarity_fit=rarity_fit, engine=ENGINE, deals_asof=deals_asof, deal_stats=deal_stats, ja_pending=ja_pending, indexes=indexes, index_history=index_history, index_all=index_all, index_sets=index_sets, index_base=(index_source["base"] if index_source else wk(index_base_w)), index_source=index_source, asof=str(asof), eur_rate=EUR, eur_rate_date=rate_date, cards=out_cards, rollups=rollups, pulse=pulse, slabmeter=slabmeter, tap=tap,
           params={k: v for k, v in params.__dict__.items()}, n_sales=int(len(clean)), n_removed=int(len(removed)), venues=venues,
           venue_gaps={v: round(float(lvm.offs[k]), 4) for k, v in enumerate(("ebay", "auction", "fixed"))},
           note="Dati veri: vendite concluse eBay (anche tramite Alt e tcgcharts), Goldin e Fanatics Collect (dal 2023). "
                "Popolazioni PSA da tcgcharts.")
# SLABWISE_OUT: another output file, for test runs (protocol §27) that must not replace the site's data
json.dump(res, open(os.environ.get("SLABWISE_OUT") or os.path.join(HERE, "data", "real.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("cards", len(out_cards), "stories", len(stories), "sales", len(clean), "EUR", EUR, rate_date)
