"""Deal probability on listings (slabwise/deals.py, D72): honest cheap asks are deals, absurd ones are not."""
import numpy as np

from slabwise.deals import landed_eur, score


def test_score_separates_deals_from_junk():
    rng = np.random.default_rng(0)
    n = 300
    m = rng.normal(7, 1, n)                       # log values
    s = np.full(n, 0.08)
    ask = np.exp(m + 0.12 + rng.normal(0, 0.25, n))   # honest asks sit ~12% above value, widely spread
    ask[:20] = np.exp(m[:20] - 0.30)              # genuine bargains, within the honest spread
    ask[20:40] = np.exp(m[20:40] - 2.0)           # junk: far too cheap to be the card described
    pg, pd, st = score(ask, ask * 1.05, m, s, np.zeros(n, bool), sigma_q=0.07)
    assert 0.0 < st["mu_l"] < 0.25 and 0.15 < st["s_l"] < 0.35
    assert np.median(pd[:20]) > 0.5               # bargains flagged
    assert np.median(pd[20:40]) < 0.2             # junk not flagged
    assert np.median(pd[40:]) < 0.2               # ordinary asks are not deals


def test_landed_cost():
    us = landed_eur(100.0, 20.0, "US")
    assert abs(us["landed_eur"] - (120 * 1.22 + 15)) < 1e-9 and us["origin"] == "USA"
    de = landed_eur(100.0, 10.0, "DE")
    assert de["landed_eur"] == 110.0 and de["origin"] == "UE"
