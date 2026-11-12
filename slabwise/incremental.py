"""§60 (D270): add cards without a rebuild. The saved engine state of a full rebuild is moved onto the new catalogue:
the cards already there keep everything they had; the new ones start empty and are marked as satellites (they follow
the era factors and the shared parameters and never move them, so the old cards' values do not change).
"""
from __future__ import annotations

import numpy as np


def transplant_model(old, fresh, cards_old, cards_new):
    """Engine state of `old` (catalogue cards_old) moved onto `fresh` (built for cards_new, with its era, parents and
    populations). Returns the model and the boolean satellite mask (True for the new cards)."""
    pos = {c: i for i, c in enumerate(cards_new)}
    o2n = np.array([pos[c] for c in cards_old])
    n = len(cards_new)
    m = fresh
    per_card = {"obs", "fit", "jumps", "gjumps", "_qs", "_qw", "satellite"}
    for k, v in old.__dict__.items():
        if k in per_card or k in ("C", "era", "parent", "pops"):
            continue
        setattr(m, k, v)
    m.obs = [[] for _ in range(n)]
    m.fit = [None] * n
    m.jumps = [[] for _ in range(n)]
    m.gjumps = [[] for _ in range(n)]
    m._qs, m._qw = np.zeros(n), np.zeros(n)
    for i_old, i_new in enumerate(o2n):
        m.obs[i_new] = old.obs[i_old]
        m.fit[i_new] = old.fit[i_old]
        m.jumps[i_new] = old.jumps[i_old]
        m.gjumps[i_new] = old.gjumps[i_old]
        m._qs[i_new], m._qw[i_new] = old._qs[i_old], old._qw[i_old]
    m._step_last = {int(o2n[c]): v for c, v in old._step_last.items()}
    m._gap_last = {int(o2n[c]): v for c, v in old._gap_last.items()}   # keyed by card (_learn_globals)
    if old.pops is not None and m.pops is not None:      # the old cards keep the populations they were fitted with
        pops = np.array(m.pops, float)
        pops[o2n] = np.asarray(old.pops, float)
        m.pops = pops
    sat = np.ones(n, bool)
    sat[o2n] = False
    m.satellite = sat
    return m, sat, o2n


def transplant_index(old, fresh, o2n, names_old=None, names_new=None):
    """Index state moved onto the new catalogue. Era (or set) numbers are matched by name when they are given."""
    e2e = {e: e for e in range(old.E)}
    if names_old is not None and names_new is not None:
        e2e = {e: names_new.index(nm) for e, nm in enumerate(names_old) if nm in names_new}
    ix = fresh
    ix.basket = {e: [] for e in range(fresh.E)}
    ix.level = {e: [] for e in range(fresh.E)}
    for e, b in old.basket.items():
        if e in e2e:
            ix.basket[e2e[e]] = [(int(o2n[c]), g) for c, g in b]
    for e, lv in old.level.items():
        if e in e2e:
            ix.level[e2e[e]] = list(lv)
    ix.history = [(w, e2e.get(e, e), [(int(o2n[c]), g) for c, g in b]) for w, e, b in old.history]
    ix.quota_log = list(old.quota_log)
    if old.prev is not None:
        prev = np.full((len(fresh.era), 4), np.nan)
        prev[o2n] = old.prev
        ix.prev = prev
    return ix


def transplant_series(old, o2n, n_cards, weeks):
    """est or sd of shape (w+1, old cards, 4) moved into an array (weeks, new cards, 4), NaN elsewhere."""
    out = np.full((weeks, n_cards, 4), np.nan)
    out[:old.shape[0], o2n] = old
    return out
