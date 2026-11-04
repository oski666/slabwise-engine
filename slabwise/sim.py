"""Simulated graded-card market with known ground truth (protocol, phase S).

Everything an estimator sees is in the observed columns of ``schema.OBSERVED``.
The true value of every atom in every week is returned separately so the
backtest can measure error against the truth, not only against the next sale.

Log value of card c, grade g, week w:
    V[c, g, w] = base[c] + beta[c] * F[era[c], w] + idio[c, w] + spike[c, w] + gap[c, g, w]
where gap[c, 10] = 0 and gaps for lower grades are negative.
A sale of copy k at a venue adds the copy quality q[k], a venue offset and noise.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .schema import GRADES

ERAS = ("wotc", "ex_dp", "bw_xy", "sm_swsh", "sv")


@dataclass
class SimConfig:
    seed: int = 1
    n_cards: int = 300
    weeks: int = 156
    contamination: float = 0.15      # share of feed records that are contaminated
    dup_rate: float = 0.06           # share of genuine sales reported twice
    cert_rate_ebay: float = 0.55     # share of eBay listings showing a cert
    sale_noise: float = 0.09         # eBay transaction noise (log)
    copy_quality: float = 0.07       # sd of copy quality (log)
    auction_premium: float = 0.06    # auction houses get the better copies
    crash_era: str = "sv"
    crash_start: int = 92
    crash_len: int = 6
    crash_size: float = -0.43        # about -35 %
    flood: bool = True               # fake "PSA 10" flood on one liquid card
    spike_share: float = 0.10        # share of cards with an event spike
    era_mislabel: float = 0.0        # share of cards whose era label (given to estimators) is wrong
    rate_scale: float = 1.0          # multiplies every sale rate (demo markets with fewer, busier cards)
    langs: int = 0                   # European languages besides English (v1.2 test only, D28)
    pop_gap: float = 0.0             # D101: true 10->9 step grows with log(pop9 / pop10) (v1.14 test, "useful populations")
    vintage_gap: float = 0.0         # extra 10->9 gap of Wizards-era cards (v1.7 test only, D55)
    lang_rate: float = 0.25          # their sale rate relative to English
    listings_per_sale: float = 0.6
    listing_contamination: float = 0.20
    contam_mix: dict = field(default_factory=lambda: {
        "misgrade": 0.22, "raw": 0.15, "fake": 0.08, "variant": 0.10,
        "lot": 0.12, "bo_ask": 0.13, "shill": 0.20,
    })


@dataclass
class SimMarket:
    cfg: SimConfig
    sales: pd.DataFrame          # observed + truth columns
    listings: pd.DataFrame       # active listings for the deal test
    value: np.ndarray            # true log value, shape (cards, 4 grades, weeks)
    rate: np.ndarray             # true weekly sale rate per atom, shape (cards, 4)
    era: np.ndarray              # true era index per card
    era_obs: np.ndarray          # era label given to estimators
    factor: np.ndarray           # true era factor, shape (eras, weeks)
    flood_card: int
    pops: np.ndarray = None      # graded population per atom, shape (cards, 4)
    lang_gap: np.ndarray = None  # true log gap of each European language, shape (cards, langs)


def _era_factors(cfg: SimConfig, rng: np.random.Generator) -> np.ndarray:
    W = cfg.weeks
    F = np.zeros((len(ERAS), W))
    drift = {"wotc": 0.0016, "ex_dp": 0.0008, "bw_xy": 0.0, "sm_swsh": 0.0, "sv": 0.0}
    vol = {"wotc": 0.008, "ex_dp": 0.010, "bw_xy": 0.012, "sm_swsh": 0.014, "sv": 0.018}
    for e, name in enumerate(ERAS):
        steps = drift[name] + vol[name] * rng.standard_normal(W)
        if name == "sm_swsh":                        # slow bull, then a soft decline
            steps[60:100] += 0.30 / 40
            steps[110:150] -= 0.12 / 40
        if name == "sv":                             # strong bull, then a fast crash
            steps[40:80] += 0.50 / 40
        if name == cfg.crash_era:
            steps[cfg.crash_start:cfg.crash_start + cfg.crash_len] += cfg.crash_size / cfg.crash_len
        steps[0] = 0.0
        F[e] = np.cumsum(steps)
    return F


def simulate(cfg: SimConfig | None = None) -> SimMarket:
    cfg = cfg or SimConfig()
    rng = np.random.default_rng(cfg.seed)
    C, W, G = cfg.n_cards, cfg.weeks, len(GRADES)

    era = rng.choice(len(ERAS), size=C, p=[0.22, 0.12, 0.14, 0.22, 0.30])
    F = _era_factors(cfg, rng)

    base = np.log(400) + 1.2 * rng.standard_normal(C)            # PSA 10 value at week 0
    beta = np.clip(1 + 0.25 * rng.standard_normal(C), 0.4, 1.8)
    idio_sd = rng.uniform(0.008, 0.025, C)
    idio = np.cumsum(idio_sd[:, None] * rng.standard_normal((C, W)), axis=1)
    idio[:, 0] = 0

    spike = np.zeros((C, W))                                      # event spikes that mean-revert
    for c in rng.choice(C, size=int(C * cfg.spike_share), replace=False):
        w0 = rng.integers(20, W - 10)
        size = rng.uniform(0.3, 0.7)
        t = np.arange(W - w0)
        spike[c, w0:] = size * 0.5 ** (t / 4.0)

    g1 = np.clip(rng.normal(0.9, 0.3, C), 0.2, 2.0)               # 10 -> 9
    g1 = g1 + cfg.vintage_gap * (era == ERAS.index("wotc"))      # D55 test: vintage PSA 10 far above PSA 9
    g2 = np.clip(rng.normal(0.55, 0.2, C), 0.1, 1.2)              # 9 -> 8
    g3 = np.clip(rng.normal(0.35, 0.15, C), 0.05, 0.8)            # 8 -> 7
    gap0 = np.stack([np.zeros(C), -g1, -(g1 + g2), -(g1 + g2 + g3)], axis=1)
    gap_walk = np.cumsum(0.004 * rng.standard_normal((C, G, W)), axis=2)
    gap_walk[:, 0, :] = 0
    gap = gap0[:, :, None] + gap_walk

    level = base[:, None] + beta[:, None] * F[era] + idio + spike  # (C, W)
    value = level[:, None, :] + gap                                # (C, G, W)

    # long-tailed liquidity: weekly sale rate per atom
    pop_c = np.exp(rng.normal(np.log(0.07), 1.5, C))
    gmul = np.array([1.0, 1.4, 0.9, 0.5])
    rate = np.clip(pop_c[:, None] * gmul[None, :] * cfg.rate_scale, 0.002, 6.0)

    # copies (population) per atom
    pops = np.maximum(3, rng.poisson(rate * 250 + 3)).astype(int)
    if cfg.pop_gap:                                               # D101: no extra random draws, markets stay identical at 0
        xg = np.log(pops[:, 1] / pops[:, 0])
        value = value - (cfg.pop_gap * (xg - xg.mean()))[:, None, None] * (np.arange(G) > 0)[None, :, None]
    copy_q = [[rng.normal(0, cfg.copy_quality, pops[c, g]) for g in range(G)] for c in range(C)]
    sold_before = [[set() for _ in range(G)] for _ in range(C)]

    def value_of(c, g_val, w):
        """True log value of card c at any numeric grade (grades < 7 extrapolated)."""
        if g_val in GRADES:
            return value[c, GRADES.index(g_val), w]
        return value[c, 3, w] - 0.30 * (7 - g_val)

    rows = []
    next_item = 1

    def add(**kw):
        nonlocal next_item
        kw.setdefault("item_id", next_item)
        next_item += 1
        rows.append(kw)

    for w in range(W):
        for c in range(C):
            for gi, g in enumerate(GRADES):
                n = rng.poisson(rate[c, gi])
                for _ in range(n):
                    k = None
                    if sold_before[c][gi] and rng.random() < 0.25:
                        k = rng.choice(list(sold_before[c][gi]))
                    if k is None:
                        k = int(rng.integers(pops[c, gi]))
                    sold_before[c][gi].add(k)
                    q = copy_q[c][gi][k]
                    auction = rng.random() < (0.08 if value[c, gi, w] > np.log(1000) else 0.02)
                    venue = "auction" if auction else "ebay"
                    noise = cfg.sale_noise * rng.standard_t(5) / np.sqrt(5 / 3)
                    if auction:
                        q_eff = q + abs(rng.normal(0, cfg.copy_quality))  # best copies go to auction
                        p = value[c, gi, w] + q_eff + cfg.auction_premium + 0.6 * noise
                    else:
                        p = value[c, gi, w] + q + noise
                    has_cert = auction or rng.random() < cfg.cert_rate_ebay
                    cert = f"C{c}-{g}-{k}" if has_cert else None
                    day = w * 7 + rng.uniform(0, 7)
                    item = next_item
                    add(day=day, card=c, grade=g, cert=cert, venue=venue, price=float(np.exp(p)),
                        flag_lot=False, flag_bo=False, t_kind="genuine", t_card=c, t_grade=g, t_copyq=q)
                    if rng.random() < cfg.dup_rate:                       # duplicate record
                        same_item = rng.random() < 0.5
                        add(item_id=item if same_item else None, day=day + rng.uniform(0, 1.5), card=c,
                            grade=g, cert=cert, venue=venue, price=float(np.exp(p)) * (1 + rng.normal(0, 0.003)),
                            flag_lot=False, flag_bo=False, t_kind="duplicate", t_card=c, t_grade=g, t_copyq=q)
                # contaminated records arrive in proportion to the atom's activity
                lam_c = rate[c, gi] * cfg.contamination / max(1e-9, 1 - cfg.contamination)
                for _ in range(rng.poisson(lam_c)):
                    kind = rng.choice(list(cfg.contam_mix), p=np.array(list(cfg.contam_mix.values())) /
                                      sum(cfg.contam_mix.values()))
                    day = w * 7 + rng.uniform(0, 7)
                    v = value[c, gi, w]
                    rec = dict(day=day, card=c, grade=g, venue="ebay", flag_lot=False, flag_bo=False,
                               t_kind=kind, t_card=c, t_grade=g, t_copyq=0.0, cert=None)
                    if kind == "misgrade":
                        real = int(rng.choice([g - 1, g - 2, g - 3, rng.integers(1, 7)]))
                        real = max(1, real)
                        rec.update(t_grade=real, price=float(np.exp(value_of(c, real, w) + rng.normal(0, 0.1))))
                        if rng.random() < 0.6:
                            rec["cert"] = f"M{c}-{real}-{next_item}"
                    elif kind == "raw":
                        rec.update(price=float(np.exp(value[c, 0, w]) * rng.uniform(0.05, 0.35)), t_grade=0)
                    elif kind == "fake":
                        rec.update(price=float(rng.uniform(8, 60)), t_card=-1, t_grade=0)
                    elif kind == "variant":
                        rec.update(price=float(np.exp(v + rng.choice([-1, 1]) * rng.uniform(0.7, 1.6))), t_card=-1)
                        if rng.random() < 0.5:
                            rec["cert"] = f"V{c}-{g}-{next_item}"
                    elif kind == "lot":
                        rec.update(price=float(np.exp(v) * rng.uniform(2, 5)), flag_lot=rng.random() < 0.7)
                    elif kind == "bo_ask":
                        rec.update(price=float(np.exp(v) * rng.uniform(1.1, 1.5)), flag_bo=rng.random() < 0.85)
                    elif kind == "shill":
                        rec.update(price=float(np.exp(v) * rng.uniform(1.4, 3.0)))
                        if rng.random() < cfg.cert_rate_ebay:
                            k = int(rng.integers(pops[c, gi]))
                            rec["cert"] = f"C{c}-{g}-{k}"
                    add(**rec)

    flood_card = -1
    if cfg.flood:
        # tcgcharts' documented failure case: many cheap fake "PSA 10" in two weeks
        liquid = np.where((era == ERAS.index("sv")) & (rate[:, 0] > 0.4))[0]
        flood_card = int(liquid[0]) if len(liquid) else int(np.argmax(rate[:, 0]))
        for _ in range(12):
            add(day=100 * 7 + rng.uniform(0, 14), card=flood_card, grade=10, cert=None, venue="ebay",
                price=float(rng.uniform(22, 38)), flag_lot=False, flag_bo=False,
                t_kind="fake", t_card=-1, t_grade=0, t_copyq=0.0)

    lang_gap = None
    if cfg.langs:
        # separate random stream: the English market is identical with or without languages
        rl = np.random.default_rng(cfg.seed + 2000)
        mu_true = np.array([-0.5, -0.7, -0.6, -0.9, -0.8, -1.0])[:cfg.langs]
        lang_gap = mu_true[None, :] + 0.15 * rl.standard_normal((C, cfg.langs))
        for w in range(W):
            for c in range(C):
                for gi, g in enumerate(GRADES):
                    for j in range(cfg.langs):
                        for _ in range(rl.poisson(rate[c, gi] * cfg.lang_rate)):
                            q = rl.normal(0, cfg.copy_quality)
                            noise = cfg.sale_noise * rl.standard_t(5) / np.sqrt(5 / 3)
                            p = value[c, gi, w] + lang_gap[c, j] + q + noise
                            add(day=w * 7 + rl.uniform(0, 7), card=c, grade=g, cert=None, venue="ebay",
                                price=float(np.exp(p)), flag_lot=False, flag_bo=False, t_kind="genuine",
                                t_card=c, t_grade=g, t_copyq=q, lang=j + 1)
    sales = pd.DataFrame(rows)
    if cfg.langs:
        sales["lang"] = sales["lang"].fillna(0).astype(int)
    missing = sales["item_id"].isna()
    sales.loc[missing, "item_id"] = np.arange(10_000_000, 10_000_000 + missing.sum())
    sales["item_id"] = sales["item_id"].astype(int)
    sales = sales.sort_values("day").reset_index(drop=True)
    sales["week"] = (sales["day"] // 7).astype(int)
    sales["sale_id"] = np.arange(len(sales))

    listings = _listings(cfg, rng, value, rate, pops, copy_q, value_of)
    era_obs = era.copy()
    if cfg.era_mislabel > 0:
        r2 = np.random.default_rng(cfg.seed + 1000)
        wrong = r2.random(C) < cfg.era_mislabel
        era_obs[wrong] = r2.integers(len(ERAS), size=wrong.sum())
    return SimMarket(cfg, sales, listings, value, rate, era, era_obs, F, flood_card, pops, lang_gap)


def _listings(cfg, rng, value, rate, pops, copy_q, value_of) -> pd.DataFrame:
    """Active Buy-It-Now listings for the deal test, from week 52 on."""
    C, G, W = value.shape
    rows = []
    for w in range(52, W):
        for c in range(C):
            for gi, g in enumerate(GRADES):
                for _ in range(rng.poisson(rate[c, gi] * cfg.listings_per_sale)):
                    k = int(rng.integers(pops[c, gi]))
                    q = copy_q[c][gi][k]
                    true_copy = value[c, gi, w] + q
                    if rng.random() < cfg.listing_contamination:
                        kind = rng.choice(["misgrade", "raw", "fake", "variant"])
                        if kind == "misgrade":
                            real = max(1, g - int(rng.integers(1, 4)))
                            true_copy = value_of(c, real, w)
                            ask = np.exp(true_copy + rng.normal(0.05, 0.15))
                            cert = f"M{c}-{real}-L" if rng.random() < 0.6 else None
                        elif kind == "raw":
                            true_copy = value[c, 0, w] + np.log(rng.uniform(0.05, 0.35))
                            ask = np.exp(true_copy + rng.normal(0.3, 0.2))
                            cert = None
                        elif kind == "fake":
                            true_copy = np.log(15)
                            ask = np.exp(value[c, gi, w] + rng.normal(-0.6, 0.25))
                            cert = None
                        else:
                            true_copy = value[c, gi, w] + rng.choice([-1, 1]) * rng.uniform(0.7, 1.6)
                            ask = np.exp(true_copy + rng.normal(0.05, 0.15))
                            cert = f"V{c}-{g}-L" if rng.random() < 0.5 else None
                    else:
                        kind = "genuine"
                        ask = np.exp(true_copy + rng.normal(0.06, 0.16))
                        cert = f"C{c}-{g}-{k}" if rng.random() < cfg.cert_rate_ebay else None
                    rows.append(dict(week=w, card=c, grade=g, ask=float(ask), cert=cert,
                                     t_kind=kind, t_copy_value=float(np.exp(true_copy))))
    return pd.DataFrame(rows)
