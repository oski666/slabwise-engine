"""Walk-forward backtest following docs/BACKTEST_PROTOCOL.md."""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from .baselines import (CardLadderIndexed, LastSale, PriceChartingAgeWeighted, SlabwiseV0,
                        TCGChartsTiered)
from .identity import identity_layer, sim_cert_lookup
from .model import LatentValueModel, LVMParams
from .schema import GRADE_INDEX
from .sim import ERAS, SimConfig, simulate

WARMUP = 26
BASELINES = (LastSale, TCGChartsTiered, PriceChartingAgeWeighted, CardLadderIndexed, SlabwiseV0)


@dataclass
class RunResult:
    names: list
    est: dict            # name -> (weeks, cards, 4) log estimates
    sd: np.ndarray       # LVM sd, same shape
    clean: pd.DataFrame
    market: object
    seconds: dict
    model: object = None


def genuine_mask(df):
    """Clean records whose price reflects the atom they are filed under."""
    ok = df["t_kind"].eq("genuine")
    fixed = df["t_kind"].eq("misgrade") & df["cert_ok"] & (df["grade"] == df["t_grade"])
    return ok | fixed


def run(market, mode="A", params: LVMParams | None = None, weeks=None, only=None) -> RunResult:
    s = market.sales
    W = weeks or market.cfg.weeks
    lookup = sim_cert_lookup(s)
    clean, _ = identity_layer(s, lookup)
    if mode == "B":                       # competitors get only their published filters
        comp_feed, _ = identity_layer(s, None, verify_certs=False, dedup_cross_feed=False)
    else:
        comp_feed = clean
    C = market.cfg.n_cards
    models = []
    for cls in BASELINES:
        if only and cls.name not in only:
            continue
        models.append((cls(C, market.era_obs, len(ERAS)), comp_feed))
    lvm = LatentValueModel(C, market.era_obs, len(ERAS), params)
    if params.pop_steps and getattr(market, "pops", None) is not None:   # v1.14 (D101)
        lvm.set_pops(market.pops)
    if not only or lvm.name in only:
        models.append((lvm, clean))
    names = [m.name for m, _ in models]
    est = {n: np.full((W, C, 4), np.nan) for n in names}
    sd = np.full((W, C, 4), np.nan)
    secs = {n: 0.0 for n in names}
    groups = {id(f): {wk: g for wk, g in f.groupby("week")} for _, f in models}
    empty = clean.iloc[:0]
    for w in range(W):
        for m, feed in models:
            t0 = time.time()
            m.ingest(w, groups[id(feed)].get(w, empty))
            if m is lvm:
                est[m.name][w], sd[w] = lvm.estimates_with_sd(w)
            else:
                est[m.name][w] = m.estimates(w)
            secs[m.name] += time.time() - t0
    return RunResult(names, est, sd, clean, market, secs, lvm)


def _bucket(rate):
    return np.select([rate >= 1, rate >= 1 / 4.33, rate >= 1 / 13], ["alta", "media", "bassa"], "rarissima")


def metrics(res: RunResult, deals=True) -> dict:
    mk = res.market
    W = next(iter(res.est.values())).shape[0]
    truth = np.transpose(mk.value[:, :, :W], (2, 0, 1))          # (W, C, 4)
    clean = res.clean
    gen = clean[genuine_mask(clean)]
    # atoms with at least one genuine clean sale up to week w
    seen = np.zeros_like(truth, dtype=bool)
    first = gen.groupby(["card", "grade"])["week"].min()
    for (c, g), wk in first.items():
        seen[wk:, int(c), GRADE_INDEX[int(g)]] = True
    seen[:WARMUP] = False
    common = seen.copy()
    for n in res.names:
        common &= np.isfinite(res.est[n])
    bucket = np.broadcast_to(_bucket(mk.rate)[None], truth.shape)
    out = {"names": res.names, "seconds": res.seconds}
    ev, evb, ru, co = {}, {}, {}, {}
    for n in res.names:
        err = np.abs(res.est[n] - truth)
        ev[n] = float(np.median(err[common]))
        evb[n] = {b: float(np.median(err[common & (bucket == b)])) for b in ("alta", "media", "bassa", "rarissima")}
        d_est = np.diff(res.est[n], axis=0)
        d_tru = np.diff(truth, axis=0)
        both = common[1:] & common[:-1]
        ru[n] = float(np.median(np.abs(d_est - d_tru)[both]))
        co[n] = float(np.isfinite(res.est[n])[seen].mean())
    out.update(EV=ev, EV_bucket=evb, RU=ru, CO=co)

    # next-sale error: estimate at end of week w-1 vs genuine sale in week w
    es = {}
    g2 = gen[gen["week"] > WARMUP]
    wk = g2["week"].to_numpy() - 1
    cc = g2["card"].to_numpy().astype(int)
    gi = np.array([GRADE_INDEX[int(x)] for x in g2["grade"]])
    lp = np.log(g2["price"].to_numpy())
    allok = np.ones(len(lp), bool)
    for n in res.names:
        allok &= np.isfinite(res.est[n][wk, cc, gi])
    for n in res.names:
        es[n] = float(np.median(np.abs(res.est[n][wk, cc, gi] - lp)[allok]))
    out["ES"] = es

    # crash lag: era hit by the crash, 8 weeks after it ends
    e = ERAS.index(mk.cfg.crash_era)
    w0 = mk.cfg.crash_start + mk.cfg.crash_len
    win = np.zeros_like(common)
    win[w0:w0 + 8, mk.era == e, :] = True
    out["RC"] = {n: float(np.median(np.abs(res.est[n] - truth)[common & win])) for n in res.names}
    # I1 (protocol section 6): share of the true 12-week era moves captured by the estimated factor
    lv = res.model
    if lv is not None and hasattr(lv, "F"):
        mk = res.market
        Wn = mk.factor.shape[1]
        slopes = []
        for e in range(len(lv.F)):
            Fe = np.array(lv.F[e])
            ws = np.arange(64, min(Wn, len(Fe) - 1))
            est_d = Fe[ws + 1] - Fe[ws + 1 - 12]
            tru_d = mk.factor[e, ws] - mk.factor[e, ws - 12]
            if np.sum(tru_d ** 2) > 0:
                slopes.append(float(np.sum(est_d * tru_d) / np.sum(tru_d ** 2)))
        out["IDX"] = slopes

    # flood card: error on PSA 10 during and after the fake flood
    fc = mk.flood_card
    if fc >= 0:
        sl = slice(100, 106)
        out["FLOOD"] = {n: float(np.nanmedian(np.abs(res.est[n][sl, fc, 0] - truth[sl, fc, 0]))) for n in res.names}

    # calibration of the LVM 80 % interval
    lvm = "Slabwise LVM"
    if lvm in res.names:
        z = 1.2816
        m = res.est[lvm]
        inside = (truth >= m - z * res.sd) & (truth <= m + z * res.sd)
        out["CA"] = float(inside[common].mean())
        out["CA_bucket"] = {b: float(inside[common & (bucket == b)].mean()) for b in ("alta", "media", "bassa", "rarissima")}
        out["CA_seen"] = float(inside[seen & np.isfinite(m)].mean())
    if deals:
        out["DEALS"] = deal_test(res)
    return out


def deal_test(res: RunResult, margin=0.10, lvm_threshold=0.80, discount=0.20, sigma_q=0.07, train_weeks=78, debug=False):
    """Precision / recall of deal flags on simulated listings (protocol metric 7).

    A true deal is a genuine listing whose copy is worth at least `margin` more
    than the ask. Competitor rule: estimate at least `discount` above the ask.
    LVM rule: P(listing genuine) x P(copy value >= ask x (1 + margin)) >= threshold.
    The threshold equals the precision we want: with calibrated probabilities a
    flag at P >= 0.8 is right 8 times out of 10. The share of contaminated
    listings is learned without labels (EM on the training weeks only).
    """
    mk = res.market
    L = mk.listings
    W = next(iter(res.est.values())).shape[0]
    L = L[(L["week"] >= WARMUP + 1) & (L["week"] < W)].reset_index(drop=True)
    evaluate = L["week"].to_numpy() >= train_weeks       # listings before this only train the EM
    lookup = sim_cert_lookup(pd.concat([mk.sales[["cert", "t_card", "t_grade"]],
                                        _listing_truth(L)], ignore_index=True))
    # identity on listings: cert reveals out-of-scope grade / printing
    keep = np.ones(len(L), bool)
    for i, (cert, card, grade) in enumerate(zip(L["cert"].to_numpy(), L["card"].to_numpy(), L["grade"].to_numpy())):
        if isinstance(cert, str):
            hit = lookup(cert)
            if hit is not None and (hit[0] != card or hit[1] != grade):
                keep[i] = False          # cert contradicts the title: not the atom advertised
    wk = L["week"].to_numpy() - 1
    cc = L["card"].to_numpy().astype(int)
    gi = np.array([GRADE_INDEX[int(x)] for x in L["grade"]])
    ask = np.log(L["ask"].to_numpy())
    has_cert = np.array([isinstance(x, str) for x in L["cert"]])
    true_deal = (L["t_kind"].to_numpy() == "genuine") & (np.log(L["t_copy_value"].to_numpy()) >= ask + np.log(1 + margin))
    out = {}
    for n in res.names:
        m = res.est[n][wk, cc, gi]
        if n == "Slabwise LVM":
            sd = res.sd[wk, cc, gi]
            r = ask - m
            train = (L["week"].to_numpy() < train_weeks) & np.isfinite(m) & keep
            # listing spread around value and contamination share, learned without labels
            p_gen = np.ones(len(r))
            p_val = np.zeros(len(r))
            # honest ask spread learned on cert-verified listings (identity is certain),
            # then only the junk share is learned on listings without a cert
            mu_c, s_c, _ = _listing_em(r[train & has_cert], sd[train & has_cert])
            for flag in (True, False):
                sel = has_cert == flag
                tr = train & sel
                mu_l, s_l, pi = _listing_em(r[tr], sd[tr], fixed=(mu_c, s_c))
                var = sd ** 2 + s_l ** 2
                ng = np.exp(-0.5 * (r - mu_l) ** 2 / var) / np.sqrt(2 * np.pi * var)
                ul = np.where((r < 0) & (r > -4), 0.25, 1e-4)
                pg = (1 - pi) * ng / ((1 - pi) * ng + pi * ul)
                p_gen[sel] = pg[sel]
                # Bayes against the winner's curse: the ask is itself evidence of the
                # copy's value (genuine asks sit at value + mu_l with spread s_l)
                v1 = sd ** 2 + sigma_q ** 2
                post_var = 1 / (1 / v1 + 1 / s_l ** 2)
                post_mean = post_var * (m / v1 + (ask - mu_l) / s_l ** 2)
                pv = norm.cdf((post_mean - ask - np.log(1 + margin)) / np.sqrt(post_var))
                p_val[sel] = pv[sel]
            flag = keep & np.isfinite(m) & (p_gen * p_val >= lvm_threshold)
        else:
            flag = keep & np.isfinite(m) & (m >= ask - np.log(1 - discount))
        flag = flag & evaluate
        tp = (flag & true_deal).sum()
        if debug:
            out[n + "_flags"] = (flag, true_deal, L, locals().get("p_gen"), locals().get("p_val"))
        out[n] = dict(flagged=int(flag.sum()), precision=float(tp / max(1, flag.sum())),
                      recall=float(tp / max(1, (true_deal & evaluate).sum())))
    return out


def _listing_em(r, sd, iters=50, fixed=None):
    """Unsupervised fit: listings = N(mu, sd^2 + s^2) genuine + uniform low-side junk.
    With ``fixed`` = (mu, s) only the junk share is estimated."""
    mu, s, pi = float(np.median(r)), 0.15, 0.2
    if fixed is not None:
        mu, s = fixed
    for _ in range(iters):
        var = sd ** 2 + s ** 2
        ng = np.exp(-0.5 * (r - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)
        ul = np.where((r < 0) & (r > -4), 0.25, 1e-4)
        pg = (1 - pi) * ng / ((1 - pi) * ng + pi * ul)
        pi = float(np.clip(1 - pg.mean(), 0.005, 0.6))
        if fixed is not None:
            continue
        mu = float(np.sum(pg * r) / pg.sum())
        s = float(np.sqrt(max(np.sum(pg * ((r - mu) ** 2 - sd ** 2)) / pg.sum(), 0.0025)))
    return mu, s, pi


def _listing_truth(L):
    rows = []
    for cert, kind, card, grade in zip(L["cert"], L["t_kind"], L["card"], L["grade"]):
        if not isinstance(cert, str):
            continue
        if kind == "misgrade":
            rows.append((cert, int(card), int(cert.split("-")[1])))
        elif kind == "variant":
            rows.append((cert, -1, int(grade)))
    return pd.DataFrame(rows, columns=["cert", "t_card", "t_grade"])


TIERS = ("Vendite fresche", "Stimato", "Poco sicuro")


def tier_of(n13, half):
    """Confidence tier (D47): n13 = sales of the grade in the last 13 weeks, half = 1.2816 * sd (log)."""
    return np.where((n13 >= 3) & (half <= 0.20), 0, np.where((n13 >= 1) | (half <= 0.35), 1, 2))


def tier_metrics(res: RunResult) -> dict:
    """Protocol section 8: LVM error and 80% band coverage per confidence tier."""
    mk = res.market
    name = "Slabwise LVM"
    est, sd = res.est[name], res.sd
    W, C, G = est.shape
    truth = np.transpose(mk.value[:, :, :W], (2, 0, 1))
    cnt = np.zeros((W, C, G))
    for (wk, c, g), n in res.clean.groupby(["week", "card", "grade"]).size().items():
        if wk < W:
            cnt[int(wk), int(c), GRADE_INDEX[int(g)]] += n
    cs = np.cumsum(cnt, axis=0)
    n13 = cs - np.concatenate([np.zeros((13, C, G)), cs[:-13]], axis=0)
    ok = np.isfinite(est) & np.isfinite(sd)
    ok[:WARMUP] = False
    half = 1.2816 * np.where(ok, sd, np.inf)
    tier = tier_of(n13, half)
    err = np.abs(est - truth)
    out = {}
    for k, t in enumerate(TIERS):
        m = ok & (tier == k)
        out[t] = {"n": int(m.sum()), "err_median": float(np.median(err[m])) if m.any() else None,
                  "coverage": float(np.mean(err[m] <= half[m])) if m.any() else None}
    return out

