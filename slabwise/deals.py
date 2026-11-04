"""Deal probability of real listings (METHOD §7, P15, D72).

For each listing with asking price A (USD) of a card and grade whose value the model estimates (log mean m,
sd s, an eBay copy):
1. identity: a cert that contradicts the card or grade of the title removes the listing (done by the caller);
2. credibility: two-sided mixture of honest asks around the value and low-side junk, learnt without labels
   on the listings themselves (``_listing_em``, the same estimator as the backtest);
3. value of the copy against the winner's curse: the model N(m, s^2 + sigma_q^2) combined with the ask as
   evidence N(log A - mu_l, s_l^2);
4. p_deal = P(genuine) x P(copy value >= landed cost x (1 + margin)), with the landed cost in Italy
   (shipping, 22% import VAT and a clearance fee from outside the EU) computed separately (P5).
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .backtest import _listing_em

EU = {"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
      "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"}
VAT_IT = 0.22
CLEARANCE_EUR = 15.0


def landed_eur(price_eur: float, ship_eur: float, country: str | None):
    """Cost in Italy of a listing: price, shipping, and import VAT plus clearance outside the EU (P5)."""
    eu = (country or "").upper() in EU
    vat = 0.0 if eu else VAT_IT * (price_eur + ship_eur)
    fee = 0.0 if eu else CLEARANCE_EUR
    return dict(price_eur=price_eur, ship_eur=ship_eur, vat_eur=vat, fee_eur=fee,
                landed_eur=price_eur + ship_eur + vat + fee, origin="UE" if eu else "USA" if (country or "").upper() == "US" else (country or "?").upper())


def score(ask_usd, landed_usd, m, s, cert, sigma_q, margin=0.10):
    """Arrays in, (p_genuine, p_deal) out. ``m``/``s`` are the model's log value and sd for each listing."""
    ask = np.log(np.asarray(ask_usd, float))
    m, s = np.asarray(m, float), np.asarray(s, float)
    cert = np.asarray(cert, bool)
    r = ask - m
    base = cert if cert.sum() >= 10 else np.ones_like(cert)      # honest ask spread from cert-verified listings when there are enough
    mu_c, s_c, _ = _listing_em(r[base], s[base])
    p_gen = np.ones(len(r))
    for flag in (True, False):
        sel = cert == flag
        if not sel.any():
            continue
        _, _, pi = _listing_em(r[sel], s[sel], fixed=(mu_c, s_c))
        var = s ** 2 + s_c ** 2
        ng = np.exp(-0.5 * (r - mu_c) ** 2 / var) / np.sqrt(2 * np.pi * var)
        ul = np.where((r < 0) & (r > -4), 0.25, 1e-4)
        pg = (1 - pi) * ng / ((1 - pi) * ng + pi * ul)
        p_gen[sel] = pg[sel]
    v1 = s ** 2 + sigma_q ** 2
    post_var = 1 / (1 / v1 + 1 / s_c ** 2)
    post_mean = post_var * (m / v1 + (ask - mu_c) / s_c ** 2)
    p_val = norm.cdf((post_mean - np.log(np.asarray(landed_usd, float)) - np.log(1 + margin)) / np.sqrt(post_var))
    return p_gen, p_gen * p_val, dict(mu_l=float(mu_c), s_l=float(s_c))


def max_landed(ask_usd, m, s, sigma_q, mu_c, s_c, margin=0.10, p=0.80):
    """Highest landed cost (USD) at which the copy is worth at least landed x (1 + margin) with probability p (D113):
    the same posterior value as score() (model value combined with the ask as evidence), solved for the cost."""
    from scipy.stats import norm as _n
    ask = np.log(np.asarray(ask_usd, float))
    m, s = np.asarray(m, float), np.asarray(s, float)
    v1 = s ** 2 + sigma_q ** 2
    post_var = 1 / (1 / v1 + 1 / s_c ** 2)
    post_mean = post_var * (m / v1 + (ask - mu_c) / s_c ** 2)
    return np.exp(post_mean - np.log(1 + margin) - _n.ppf(p) * np.sqrt(post_var))


def price_for_landed(landed_eur, ship_eur, country):
    """Inverse of landed_eur(): the item price (EUR) that gives this landed cost in Italy."""
    eu = (country or "").upper() in EU
    if eu:
        return landed_eur - ship_eur
    return (landed_eur - CLEARANCE_EUR) / (1 + VAT_IT) - ship_eur


def score_fixed(ask_usd, landed_usd, m, s, sigma_q, mu_c, s_c, pi=0.15, margin=0.10):
    """score() with the honest-ask spread already known (D114): for a handful of new listings at a time, where the
    mixture cannot be fitted again. pi = share of junk listings (the prior of the mixture)."""
    ask = np.log(np.asarray(ask_usd, float))
    m, s = np.asarray(m, float), np.asarray(s, float)
    r = ask - m
    var = s ** 2 + s_c ** 2
    ng = np.exp(-0.5 * (r - mu_c) ** 2 / var) / np.sqrt(2 * np.pi * var)
    ul = np.where((r < 0) & (r > -4), 0.25, 1e-4)
    p_gen = (1 - pi) * ng / ((1 - pi) * ng + pi * ul)
    v1 = s ** 2 + sigma_q ** 2
    post_var = 1 / (1 / v1 + 1 / s_c ** 2)
    post_mean = post_var * (m / v1 + (ask - mu_c) / s_c ** 2)
    p_val = norm.cdf((post_mean - np.log(np.asarray(landed_usd, float)) - np.log(1 + margin)) / np.sqrt(post_var))
    return p_gen, p_gen * p_val
