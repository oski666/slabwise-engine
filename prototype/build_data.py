"""Demo data for prototype v2: the real LVM engine run on a simulated market built
around our 23 real catalogue cards (names, sets and TCGdex images are real; graded
sales, populations and listings are simulated and must be labelled as demo, P14).

Output: prototype/data/demo.json
"""
import json
import os
import sys
from datetime import date, timedelta

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from slabwise.backtest import _listing_em  # noqa: E402
from slabwise.identity import identity_layer, sim_cert_lookup  # noqa: E402
from slabwise.model import LatentValueModel, LVMParams  # noqa: E402
from slabwise.schema import GRADE_INDEX, GRADES  # noqa: E402
from slabwise.sim import ERAS, SimConfig, simulate  # noqa: E402

cards = json.load(open(os.path.join(HERE, "data", "cards.json")))
thumbs = json.load(open(os.path.join(HERE, "data", "images.json")))
hires = json.load(open(os.path.join(HERE, "data", "hires.json")))
C = len(cards)

# Demo scale for the PSA 10 value of each card today (USD). Only gives the
# simulated market a believable size; it is not a price estimate.
DEMO_PSA10 = {
    "base1-4": 32000, "base1-2": 6500, "base1-15": 4200, "base1-10": 1500, "base1-3": 1400,
    "base1-1": 2200, "base1-8": 900, "base1-58": 1100, "base2-11": 2500, "base3-5": 3800,
    "base3-4": 3000, "base5-4": 6500, "neo1-9": 12000, "neo3-14": 4500, "gym2-1": 3500,
    "gym2-13": 4000, "sv03.5-199": 650, "sv03.5-205": 180, "sv04.5-232": 1100,
    "swsh7-215": 3700, "svp-085": 1900, "me02-125": 1400, "sv03.5-168": 260,
}
SERIES = [  # (prefix, label shown in the UI, model era)
    ("base", "Wizards of the Coast", "wotc"), ("gym", "Wizards of the Coast", "wotc"),
    ("neo", "Wizards of the Coast", "wotc"), ("swsh", "Spada e Scudo", "sm_swsh"),
    ("svp", "Scarlatto e Violetto", "sv"), ("sv", "Scarlatto e Violetto", "sv"),
    ("me", "Mega Evoluzione", "sv"),
]


def series_of(cid):
    for pre, label, era in SERIES:
        if cid.startswith(pre):
            return label, era
    return "Altro", "sv"


WEEKS = 156
END = date(2026, 10, 19)                       # last simulated week ends here
START = END - timedelta(weeks=WEEKS)
for seed in range(11, 200):          # first demo market where every card trades at least 12 times
    cfg = SimConfig(seed=seed, n_cards=C, weeks=WEEKS, rate_scale=5.0, flood=False)
    m = simulate(cfg)
    counts = m.sales[m.sales["t_kind"] == "genuine"].groupby("card").size().reindex(range(C), fill_value=0)
    if counts.min() >= 12:
        break
print("demo seed", seed)

# re-label the simulated cards: era from the real series, scale from DEMO_PSA10
era = np.array([ERAS.index(series_of(c["id"])[1]) for c in cards])
for i, c in enumerate(cards):
    k = np.log(DEMO_PSA10[c["id"]]) - m.value[i, 0, -1]
    m.value[i] += k
    rows = (m.sales["card"] == i) & (m.sales["t_kind"] != "fake")
    m.sales.loc[rows, "price"] *= np.exp(k)
    lr = (m.listings["card"] == i) & (m.listings["t_kind"] != "fake")
    m.listings.loc[lr, "ask"] *= np.exp(k)
    m.listings.loc[lr, "t_copy_value"] *= np.exp(k)
    fl = (m.listings["card"] == i) & (m.listings["t_kind"] == "fake")
    m.listings.loc[fl, "ask"] = np.exp(m.value[i, 0, m.listings.loc[fl, "week"].to_numpy()] - 0.6)
m.era[:] = era
m.era_obs[:] = era

clean, removed = identity_layer(m.sales, sim_cert_lookup(m.sales))
params = LVMParams(q_L=0.0003, q_d=0.00002, sigma_e=0.085, sigma_q=0.07, tau_f=0.02)
lvm = LatentValueModel(C, era, len(ERAS), params)
groups = {w: g for w, g in clean.groupby("week")}
est = np.full((WEEKS, C, 4), np.nan)
sd = np.full((WEEKS, C, 4), np.nan)
for w in range(WEEKS):
    lvm.ingest(w, groups.get(w, clean.iloc[:0]))
    est[w], sd[w] = lvm.estimates_with_sd(w)

Z = 1.2816
day = lambda d: (START + timedelta(days=float(d))).isoformat()          # noqa: E731
wk_date = lambda w: (START + timedelta(weeks=int(w) + 1)).isoformat()   # noqa: E731


def reason(pg, r, ok):
    if pg >= 0.5:
        return None
    if r < 0:
        return "molto sotto il valore: probabile carta raw, falso o voto sbagliato" if not ok else "molto sotto il valore"
    return "molto sopra il valore: possibile lotto, asta gonfiata o Best Offer"


# listings of the last two weeks with deal probability (EM learned on earlier weeks)
L = m.listings
L = L[L["week"] >= 60].reset_index(drop=True)
li_w = L["week"].to_numpy() - 1
li_c = L["card"].to_numpy()
li_g = np.array([GRADE_INDEX[int(g)] for g in L["grade"]])
li_m = est[li_w, li_c, li_g]
li_s = sd[li_w, li_c, li_g]
ask = np.log(L["ask"].to_numpy())
has_cert = np.array([isinstance(x, str) for x in L["cert"]])
r_all = ask - li_m
train = (L["week"].to_numpy() < WEEKS - 2) & np.isfinite(li_m)
mu_c, s_c, _ = _listing_em(r_all[train & has_cert], li_s[train & has_cert])
pis = {}
for flag in (True, False):
    _, _, pis[flag] = _listing_em(r_all[train & (has_cert == flag)], li_s[train & (has_cert == flag)], fixed=(mu_c, s_c))

EUR = 0.92          # demo exchange rate (USD -> EUR)
rng = np.random.default_rng(5)
out_cards = []
for i, c in enumerate(cards):
    label, _ = series_of(c["id"])
    g_out = []
    for gi, g in enumerate(GRADES):
        h = [[wk_date(w), round(float(np.exp(est[w, i, gi])), 2), round(float(np.exp(est[w, i, gi] - Z * sd[w, i, gi])), 2),
              round(float(np.exp(est[w, i, gi] + Z * sd[w, i, gi])), 2), round(float(np.exp(m.value[i, gi, w])), 2)]
             for w in range(52, WEEKS) if np.isfinite(est[w, i, gi])]
        now, s_now = est[-1, i, gi], sd[-1, i, gi]
        g_out.append(dict(
            grade=g, value=round(float(np.exp(now)), 2), lo=round(float(np.exp(now - Z * s_now)), 2),
            hi=round(float(np.exp(now + Z * s_now)), 2), ch30=round(float(np.exp(now - est[-5, i, gi]) - 1), 4),
            ch90=round(float(np.exp(now - est[-14, i, gi]) - 1), 4), pop=int(m.pops[i, gi] * 40),    # demo scale: simulated pops are ~40x smaller than real ones
            sales90=int(((clean["card"] == i) & (clean["grade"] == g) & (clean["week"] >= WEEKS - 13)).sum()),
            history=h))
    # sales of the last 52 weeks used by the model, with their genuineness
    ob = lvm.obs[i]
    pg = lvm.fit[i]["pgen"]
    th = lvm.fit[i]["theta"]
    sales = []
    for o, p_ in zip(ob, pg):
        if o["t"] < WEEKS - 52:
            continue
        gi = o["g"]
        w = min(int(o["t"]), WEEKS - 1)
        r = o["y"] - est[w, i, gi]
        sales.append(dict(date=day(o["t"] * 7), grade=GRADES[gi], price=round(float(np.exp(o["y"])), 2),
                          venue="Casa d'aste" if o["a"] else "eBay", cert=bool(o["k"]), pgen=round(float(p_), 3),
                          why=reason(p_, r, o["ok"])))
    rem = removed[(removed["card"] == i) & (removed["week"] >= WEEKS - 52)]
    excluded = [dict(date=day(d), grade=int(g), price=round(float(p), 2), why=w_)
                for d, g, p, w_ in zip(rem["day"], rem["grade"], rem["price"], rem["reason"])]
    # listings
    sel = np.where((li_c == i) & (L["week"].to_numpy() >= WEEKS - 2) & np.isfinite(li_m))[0]
    deals = []
    for j in sel:
        gi = li_g[j]
        flag = bool(has_cert[j])
        var = li_s[j] ** 2 + s_c ** 2
        ng = np.exp(-0.5 * (r_all[j] - mu_c) ** 2 / var) / np.sqrt(2 * np.pi * var)
        ul = 0.25 if -4 < r_all[j] < 0 else 1e-4
        p_gen = (1 - pis[flag]) * ng / ((1 - pis[flag]) * ng + pis[flag] * ul)
        v1 = li_s[j] ** 2 + params.sigma_q ** 2
        pv = 1 / (1 / v1 + 1 / s_c ** 2)
        pm = pv * (li_m[j] / v1 + (ask[j] - mu_c) / s_c ** 2)
        eu = rng.random() < 0.3
        price_eur = float(np.exp(ask[j])) * EUR
        ship = 12.0 if eu else 38.0 * EUR
        vat = 0.0 if eu else 0.22 * (price_eur + ship)
        fee = 0.0 if eu else 15.0
        landed_usd = (price_eur + ship + vat + fee) / EUR
        # P15 / METHOD 7: the copy must be worth at least 10 % more than what it costs in Italy
        p_val = norm.cdf((pm - np.log(landed_usd) - np.log(1.10)) / np.sqrt(pv))
        deals.append(dict(grade=GRADES[gi], ask_usd=round(float(np.exp(ask[j])), 2), cert=flag,
                          origin="UE" if eu else "USA", price_eur=round(price_eur, 2), ship_eur=round(ship, 2),
                          vat_eur=round(vat, 2), fee_eur=round(fee, 2),
                          landed_eur=round(price_eur + ship + vat + fee, 2),
                          value_eur=round(float(np.exp(li_m[j])) * EUR, 2),
                          p_gen=round(float(p_gen), 3), p_deal=round(float(p_gen * p_val), 3),
                          suspicious=bool(p_gen < 0.5)))
    deals.sort(key=lambda d: -d["p_deal"])
    out_cards.append(dict(id=c["id"], name=c["n"], set=c["set"], no=c["no"], tot=c.get("tot"), series=label,
                          rarity=c.get("r"), illustrator=c.get("ill"), img=hires.get(c["id"]) or thumbs.get(c["id"]),
                          thumb=thumbs.get(c["id"]), grades=g_out, sales=sales, excluded=excluded, deals=deals[:8],
                          beta=round(float(th[4]), 3)))

# rollups by series: collection value = sum value x population, concentration, coverage
roll = {}
for c in out_cards:
    r_ = roll.setdefault(c["series"], dict(series=c["series"], cards=[], cap=0.0, cap30=0.0))
    cap = sum(g["value"] * g["pop"] for g in c["grades"])
    cap30 = sum(g["value"] / (1 + g["ch30"]) * g["pop"] for g in c["grades"])
    r_["cards"].append((c["name"], cap))
    r_["cap"] += cap
    r_["cap30"] += cap30
rollups = []
for r_ in roll.values():
    top = sorted(r_["cards"], key=lambda x: -x[1])
    rollups.append(dict(series=r_["series"], cap=round(r_["cap"]), ch30=round(r_["cap"] / r_["cap30"] - 1, 4),
                        n=len(top), top3=round(sum(x[1] for x in top[:3]) / r_["cap"], 3), leader=top[0][0]))
rollups.sort(key=lambda x: -x["cap"])

# ---- weekly pulse: the stories of the week, each ready to become a reel
def week_move(c, gi):
    return float(est[-1, c, gi] - est[-2, c, gi])


cand = []
for i, c in enumerate(out_cards):
    for gi, g in enumerate(c["grades"]):
        if g["hi"] / g["lo"] < 1.35:                      # only moves we are fairly sure about
            cand.append((abs(week_move(i, gi)), i, gi))
_, mi, mg = max(cand)
mv = out_cards[mi]["grades"][mg]
best_deal = max(((d["p_deal"], c, d) for c in out_cards for d in c["deals"]), key=lambda x: x[0])
caught = min(((s_["pgen"], c, s_) for c in out_cards for s_ in c["sales"] if s_["date"] >= (END - timedelta(days=28)).isoformat()),
             key=lambda x: x[0])
ladders = []
for c in out_cards:
    v10, v9 = c["grades"][0]["value"], c["grades"][1]["value"]
    ladders.append((v10 / v9, c))
lr, lc = max(ladders, key=lambda x: x[0])
era_best = max(rollups, key=lambda r: abs(r["ch30"]))
pulse = dict(
    week=f"{(END - timedelta(days=6)).isoformat()}/{END.isoformat()}",
    stories=[
        dict(kind="mover", title="Lo slab della settimana", card=out_cards[mi]["id"], grade=mv["grade"],
             value=mv["value"], lo=mv["lo"], hi=mv["hi"], change7=round(float(np.exp(week_move(mi, mg)) - 1), 4),
             hook=f"{out_cards[mi]['name']} PSA {mv['grade']}: {'+' if week_move(mi, mg) > 0 else '−'}{abs(np.exp(week_move(mi, mg)) - 1) * 100:.0f}% in 7 giorni",
             reel=dict(mode="trend", card=out_cards[mi]["id"], grade=mv["grade"],
                       prev=round(mv["value"] / np.exp(week_move(mi, mg)) * EUR), now=round(mv["value"] * EUR), days=7)),
        dict(kind="deal", title="Il deal della settimana", card=best_deal[1]["id"], grade=best_deal[2]["grade"],
             p_deal=best_deal[2]["p_deal"], landed_eur=best_deal[2]["landed_eur"], value_eur=best_deal[2]["value_eur"],
             origin=best_deal[2]["origin"],
             hook=f"{best_deal[1]['name']} PSA {best_deal[2]['grade']}: {round(best_deal[2]['p_deal'] * 100)}% di probabilità che sia un affare",
             reel=dict(mode="deal", card=best_deal[1]["id"], grade=best_deal[2]["grade"], price=round(best_deal[2]["price_eur"]),
                       ship=round(best_deal[2]["ship_eur"]), origin="eu" if best_deal[2]["origin"] == "UE" else "noneu",
                       fee=round(best_deal[2]["fee_eur"]), fv=round(best_deal[2]["value_eur"]))),
        dict(kind="caught", title="Smascherata", card=caught[1]["id"], grade=caught[2]["grade"], price=caught[2]["price"],
             pgen=caught[2]["pgen"], why=caught[2]["why"],
             value=next(g["value"] for g in caught[1]["grades"] if g["grade"] == caught[2]["grade"]),
             hook="Venduto a $" + f"{caught[2]['price']:,.0f}".replace(",", ".") + ", ma per il nostro modello non è credibile"),
        dict(kind="ladder", title="Il salto di voto", card=lc["id"], ratio=round(lr, 2),
             v10=lc["grades"][0]["value"], v9=lc["grades"][1]["value"],
             hook=f"{lc['name']}: un PSA 10 vale {lr:.1f} volte un PSA 9".replace(".", ",")),
        dict(kind="era", title="L'era della settimana", series=era_best["series"], cap=era_best["cap"], ch30=era_best["ch30"],
             hook=f"{era_best['series']}: {'+' if era_best['ch30'] > 0 else '−'}{abs(era_best['ch30']) * 100:.1f}% in 30 giorni".replace(".", ",")),
    ])

demo = dict(asof=END.isoformat(), eur_rate=EUR, cards=out_cards, rollups=rollups, pulse=pulse,
            params=dict(q_L=params.q_L, sigma_e=params.sigma_e, sigma_q=params.sigma_q),
            note="Dati dimostrativi: carte e immagini reali (TCGdex), vendite, popolazioni e annunci simulati; "
                 "valori calcolati dal Modello a Valore Latente v1.1.")
json.dump(demo, open(os.path.join(HERE, "data", "demo.json"), "w"), ensure_ascii=False, separators=(",", ":"))
n_deals = sum(1 for c in out_cards for d in c["deals"] if d["p_deal"] >= 0.8)
print("cards", C, "sales", sum(len(c["sales"]) for c in out_cards), "excluded", sum(len(c["excluded"]) for c in out_cards),
      "deals>=0.8", n_deals, "size", os.path.getsize(os.path.join(HERE, "data", "demo.json")))
