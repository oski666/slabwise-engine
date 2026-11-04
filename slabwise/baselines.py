"""Reconstructions of competitors' published pricing methods (pillar P13).

Each estimator ingests one week of clean sales at a time and returns, at the end
of that week, a log-value estimate per atom (cards x 4 grades, NaN = no value).
They only ever see data up to the current week (P11).

Sources for the reconstructions are listed in docs/COMPETITORS.md. Where a site
does not publish a parameter we use the most natural reading and say so.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from .schema import GRADE_INDEX


class Estimator:
    name = "base"

    def __init__(self, n_cards: int, era: np.ndarray, n_eras: int):
        self.C = n_cards
        self.era = era
        self.n_eras = n_eras
        self.hist = defaultdict(list)            # (card, gi) -> list of (day, logp)

    def ingest(self, w: int, sales) -> None:
        for card, grade, day, price in zip(sales["card"], sales["grade"], sales["day"], sales["price"]):
            self.hist[(int(card), GRADE_INDEX[int(grade)])].append((float(day), float(np.log(price))))

    def estimates(self, w: int) -> np.ndarray:
        out = np.full((self.C, 4), np.nan)
        now = (w + 1) * 7.0
        for (c, gi), h in self.hist.items():
            v = self.value(h, now, c, gi)
            if v is not None:
                out[c, gi] = v
        return out

    def value(self, h, now, c, gi):
        raise NotImplementedError


class LastSale(Estimator):
    """The last recorded price (tcgcharts market cap example, Card Ladder anchor)."""
    name = "Ultima vendita"

    def value(self, h, now, c, gi):
        return h[-1][1]


class TCGChartsTiered(Estimator):
    """tcgcharts: plain median of the first window with enough sales.

    7+ sales in 14 days -> median of newest 7; else any in 28 days; else any in 90
    days; else median of the last 3. Low-sale guard on tiers 2-4: if at least 5 of
    the previous 15 sales are within a year, drop sales below (lowest of those 15) / 4.
    """
    name = "tcgcharts (mediana a fasce)"

    def value(self, h, now, c, gi):
        days = np.array([d for d, _ in h])
        lp = np.array([p for _, p in h])
        r14 = days > now - 14
        if r14.sum() >= 7:
            return float(np.median(lp[r14][-7:]))
        for win in (28, 90, None):
            sel = days > now - win if win else np.zeros(len(days), bool)
            if win is None:
                sel[-3:] = True
            if sel.any():
                idx = np.where(sel)[0]
                earlier = lp[: idx[0]][-15:]
                edays = days[: idx[0]][-15:]
                vals = lp[idx]
                if len(earlier) >= 5 and (edays > now - 365).sum() >= 5:
                    guard = earlier.min() - np.log(4)
                    kept = vals[vals >= guard]
                    if len(kept):
                        vals = kept
                return float(np.median(vals))
        return None


class PriceChartingAgeWeighted(Estimator):
    """PriceCharting: age-weighted average, abnormal prices flagged for review.

    Half-life 30 days over the last 180 days; review is approximated by dropping
    sales more than 3x above or below the window median.
    """
    name = "PriceCharting (media pesata per età)"

    def value(self, h, now, c, gi):
        days = np.array([d for d, _ in h])
        lp = np.array([p for _, p in h])
        sel = days > now - 180
        if not sel.any():
            sel = np.zeros(len(days), bool)
            sel[-1] = True
        d, p = days[sel], lp[sel]
        med = np.median(p)
        keep = np.abs(p - med) <= np.log(3)
        if not keep.any():
            return float(med)
        d, p = d[keep], p[keep]
        wts = 0.5 ** ((now - d) / 30.0)
        return float(np.log(np.sum(wts * np.exp(p)) / np.sum(wts)))


class CardLadderIndexed(Estimator):
    """Card Ladder: last sale moved by a market index since the sale date.

    The index is built per era from repeat sales of the same atom (chained weekly
    median of per-week log slopes), which is the simplest transparent version of
    "the value moves with the index".
    """
    name = "Card Ladder (ultima vendita × indice)"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.index = [[0.0] for _ in range(self.n_eras)]   # cumulative log index per week

    def ingest(self, w, sales):
        slopes = defaultdict(list)
        for card, grade, day, price in zip(sales["card"], sales["grade"], sales["day"], sales["price"]):
            key = (int(card), GRADE_INDEX[int(grade)])
            h = self.hist[key]
            if h:
                d0, p0 = h[-1]
                dt = max(1.0, (day - d0) / 7.0)
                if dt <= 26:
                    slopes[self.era[int(card)]].append((np.log(price) - p0) / dt)
        for e in range(self.n_eras):
            s = slopes.get(e, [])
            step = float(np.median(s)) if len(s) >= 3 else 0.0
            self.index[e].append(self.index[e][-1] + step)
        super().ingest(w, sales)

    def value(self, h, now, c, gi):
        d, p = h[-1]
        e = self.era[c]
        w_now = len(self.index[e]) - 1
        w_sale = min(int(d // 7) + 1, w_now)
        return p + self.index[e][w_now] - self.index[e][w_sale]


class SlabwiseV0(Estimator):
    """Our previous prototype (very close to TCGBerg's published rule stack).

    Asymmetric MAD fence (strict on the low side, high side kept at 0.3 weight),
    recency-weighted median (half-life 45 days, 365-day window), then log-space
    shrinkage towards a grade-ladder reference with k = 3.
    """
    name = "Slabwise v0 (regole, tipo TCGBerg)"

    def estimates(self, w):
        now = (w + 1) * 7.0
        own = np.full((self.C, 4), np.nan)
        n = np.zeros((self.C, 4))
        for (c, gi), h in self.hist.items():
            days = np.array([d for d, _ in h])
            lp = np.array([p for _, p in h])
            sel = days > now - 365
            if not sel.any():
                sel[-1] = True
            d, p = days[sel], lp[sel]
            med = np.median(p)
            mad = max(1.4826 * np.median(np.abs(p - med)), 0.10)
            wt = 0.5 ** ((now - d) / 45.0)
            wt[p < med - 2.5 * mad] = 0.0
            wt[p > med + 4.0 * mad] *= 0.3
            if wt.sum() == 0:
                continue
            own[c, gi] = _wmedian(p, wt)
            n[c, gi] = (wt > 0).sum()
        gaps = np.nanmedian(own[:, :-1] - own[:, 1:], axis=0)            # global ladder ratios
        gaps = np.where(np.isfinite(gaps), gaps, np.log(2.0))
        out = own.copy()
        for c in range(self.C):
            for gi in range(4):
                refs = []
                if gi > 0 and np.isfinite(own[c, gi - 1]):
                    refs.append(own[c, gi - 1] - gaps[gi - 1])
                if gi < 3 and np.isfinite(own[c, gi + 1]):
                    refs.append(own[c, gi + 1] + gaps[gi])
                if not refs:
                    continue
                ref = float(np.mean(refs))
                if np.isfinite(own[c, gi]):
                    out[c, gi] = (n[c, gi] * own[c, gi] + 3 * ref) / (n[c, gi] + 3)
        return out


def _wmedian(x, w):
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w)
    return float(x[np.searchsorted(cw, 0.5 * cw[-1])])
