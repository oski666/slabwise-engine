"""Fit the LVM hyper-parameters on the training window only (pillars P7, P11).

Step 1 (variances, Case-Shiller style): resales of the same cert are compared.
After removing the era index, Var(y2 - y1) = 2 sigma_e^2 + q_L * gap, so a robust
line through squared differences against the time gap gives sigma_e (intercept)
and the card drift q_L (slope).
Step 2: the remaining parameters by predictive likelihood, as below.

Objective: mean log predictive density of the next clean sale under the model's
own mixture (genuine + two-sided contamination). It needs no ground truth, so
the same procedure runs unchanged on real data. Coordinate search over a small
grid, two passes, then the parameters are frozen for the evaluation period.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from .identity import identity_layer, sim_cert_lookup
from .model import LatentValueModel, LVMParams
from .schema import GRADE_INDEX
from .sim import ERAS

GRID = {
    "q_L": [0.0001, 0.0003, 0.0006, 0.0012, 0.0025],
    "q_d": [0.0, 0.00002, 0.0001],
    "sigma_e": [0.07, 0.09, 0.12, 0.15],
    "sigma_q": [0.03, 0.06, 0.09],
    "tau_f": [0.01, 0.02, 0.04, 0.08],
    "tau_s": [0.0, 0.001, 0.003, 0.006],   # v1.3 (D33): 0 keeps the v1.2 factor
}


def predictive_score(clean, n_cards, era, params, train_weeks=52, warmup=26, n_eras=len(ERAS), return_model=False):
    m = LatentValueModel(n_cards, era, n_eras, params)
    groups = {wk: g for wk, g in clean.groupby("week")}
    empty = clean.iloc[:0]
    total, n = 0.0, 0
    for w in range(train_weeks):
        g = groups.get(w, empty)
        if w > warmup and len(g):
            mean, sd = m.estimates_with_sd(w - 1)
            cc = g["card"].to_numpy().astype(int)
            gi = np.array([GRADE_INDEX[int(x)] for x in g["grade"]])
            y = np.log(g["price"].to_numpy())
            vn = g["venue"].to_numpy()
            mu = mean[cc, gi] + m.offs[np.where(vn == "auction", 1, np.where(vn == "fixed", 2, 0))]
            ok = g["cert_ok"].to_numpy().astype(bool)
            fin = np.isfinite(mu)
            noise = np.where(g["venue"].to_numpy() == "auction", params.sigma_a, params.sigma_e)
            var = sd[cc, gi] ** 2 + noise ** 2 + params.sigma_q ** 2
            for flag in (False, True):
                sel = fin & (ok == flag)
                if sel.any():
                    _, _, _, ll = m._mix(y[sel] - mu[sel], var[sel], flag)
                    total += ll.sum()
                    n += sel.sum()
        m.ingest(w, g)
    if return_model:
        return total / max(n, 1), m
    return total / max(n, 1)


def predictive_coverage(clean, n_cards, era, params, train_weeks=52, warmup=26, n_eras=len(ERAS)):
    """Share of sales after the warm-up, inside the calibration weeks, that fall in the model's 80% predictive band
    (value sd, sale noise and copy noise; the same band as R4 of phase R)."""
    m = LatentValueModel(n_cards, era, n_eras, params)
    groups = {wk: g for wk, g in clean.groupby("week")}
    empty = clean.iloc[:0]
    inside, n = 0, 0
    for w in range(train_weeks):
        g = groups.get(w, empty)
        if w > warmup and len(g):
            mean, sd = m.estimates_with_sd(w - 1)
            cc = g["card"].to_numpy().astype(int)
            gi = np.array([GRADE_INDEX[int(x)] for x in g["grade"]])
            y = np.log(g["price"].to_numpy())
            mu = mean[cc, gi]
            fin = np.isfinite(mu)
            noise = np.where(g["venue"].to_numpy() == "auction", params.sigma_a, params.sigma_e)
            band = 1.2816 * np.sqrt(sd[cc, gi] ** 2 + noise ** 2 + params.sigma_q ** 2)
            inside += int((np.abs(y - mu) <= band)[fin].sum())
            n += int(fin.sum())
        m.ingest(w, g)
    return inside / max(n, 1)


COVERAGE_K = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]


def coverage_fit(clean, n_cards, era, n_eras, p, train_weeks=52, warmup=26):
    """v1.11 (D87, protocol §16): one factor on the three noises so that the 80% predictive band holds 80% of the
    sales of the calibration weeks. Returns (params, k, coverage)."""
    clean = clean[clean["week"] < train_weeks]
    best = None
    for k in COVERAGE_K:
        cand = replace(p, sigma_e=p.sigma_e * k, sigma_a=p.sigma_a * k, sigma_q=p.sigma_q * k)
        cov = predictive_coverage(clean, n_cards, era, cand, train_weeks, warmup, n_eras)
        key = (abs(cov - 0.80), abs(k - 1.0))
        if best is None or key < best[0]:
            best = (key, cand, k, cov)
    return best[1], best[2], best[3]


def repeat_sales_variances(clean, model, era, min_pairs=200):
    """Return (sigma_e, q_L) from same-cert resales, or None if too few pairs."""
    c = clean[clean["cert_ok"] & clean["cert"].notna()].sort_values("day")
    d, gap = [], []
    for _, g in c.groupby("cert"):
        if len(g) < 2:
            continue
        e = era[int(g["card"].iloc[0])]
        t = g["day"].to_numpy() / 7.0
        wk = np.minimum(t.astype(int) + 1, len(model.F[e]) - 1)
        y = np.log(g["price"].to_numpy()) - np.array([model.F[e][i] for i in wk])
        d.extend(np.diff(y))
        gap.extend(np.diff(t))
    if len(d) < min_pairs:
        return None
    d, gap = np.array(d), np.array(gap)
    qs = np.quantile(gap, np.linspace(0, 1, 7))
    xs, ys = [], []
    for a, b in zip(qs[:-1], qs[1:]):
        sel = (gap >= a) & (gap <= b)
        xs.append(gap[sel].mean())
        ys.append(np.median(d[sel] ** 2) / 0.4549)      # median of chi2(1) = 0.4549
    A = np.vstack([np.ones(len(xs)), xs]).T
    icpt, slope = np.linalg.lstsq(A, np.array(ys), rcond=None)[0]
    # differences are taken on the *estimated* index, which already absorbs part of
    # each card's move, so the slope is used as it is (no further correction)
    sigma_e = float(np.clip(np.sqrt(max(icpt, 1e-4) / 2), 0.04, 0.25))
    q_L = float(np.clip(slope, 5e-5, 0.003))
    return sigma_e, q_L, len(d)


def calibrate(market, passes=2, verbose=True, train_weeks=52):
    clean, _ = identity_layer(market.sales, sim_cert_lookup(market.sales))
    return calibrate_clean(clean, market.cfg.n_cards, market.era_obs, len(ERAS), train_weeks, passes, verbose)


def calibrate_clean(clean, n_cards, era, n_eras, train_weeks=52, passes=2, verbose=False, trend=False, coverage=False):
    """Same procedure on any clean sales table (simulated or real). trend=False keeps the v1.2
    era factor (tau_s = 0). The v1.3 trend (trend=True) was not adopted (D36): research only."""
    clean = clean[clean["week"] < train_weeks]
    warm = min(26, train_weeks // 2)
    p = LVMParams()
    best, model = predictive_score(clean, n_cards, era, p, train_weeks, warm, n_eras, return_model=True)
    grid = dict(GRID)
    if not trend:
        grid.pop("tau_s")
    rs = repeat_sales_variances(clean, model, era)
    if rs is not None:                       # variances identified by resales: fix them
        p = replace(p, sigma_e=rs[0], q_L=rs[1])
        grid.pop("q_L")
        grid.pop("sigma_e")
        best = predictive_score(clean, n_cards, era, p, train_weeks, warm, n_eras)
        if verbose:
            print(f"  vendite ripetute: {rs[2]} coppie -> sigma_e={rs[0]:.3f}, q_L={rs[1]:.5f}")
    log = [(dict(p.__dict__), best)]
    for _ in range(passes):
        for name, values in grid.items():
            for v in values:
                if getattr(p, name) == v:
                    continue
                cand = replace(p, **{name: v})
                sc = predictive_score(clean, n_cards, era, cand, train_weeks, warm, n_eras)
                log.append((dict(cand.__dict__), sc))
                if sc > best:
                    best, p = sc, cand
                    if verbose:
                        print(f"  {name}={v}: {sc:.4f}", flush=True)
    if coverage:                              # v1.11 (D87)
        p, k, cov = coverage_fit(clean, n_cards, era, n_eras, p, train_weeks, warm)
        log.append(({"coverage_k": k, "coverage": cov}, best))
        if verbose:
            print(f"  copertura: k={k} -> {cov:.3f}", flush=True)
    return p, best, log
