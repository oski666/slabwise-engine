"""Statistical tests for the real-data comparisons (protocol §18, D92).

Sales of the same card are not independent (same price path), so the uncertainty of a difference in median
error is measured with a cluster bootstrap: whole cards are resampled with replacement.
"""
from __future__ import annotations

import numpy as np


def cluster_bootstrap_diff(err_a, err_b, clusters, n_boot=2000, seed=0):
    """Median |error| of A minus median |error| of B, with a 95% interval from resampling clusters.
    Returns (difference, low, high, share of resamples where A is better)."""
    err_a, err_b = np.asarray(err_a, float), np.asarray(err_b, float)
    clusters = np.asarray(clusters)
    ids, inv = np.unique(clusters, return_inverse=True)
    groups = [np.flatnonzero(inv == k) for k in range(len(ids))]
    rng = np.random.default_rng(seed)
    diff = float(np.median(err_a) - np.median(err_b))
    boots = np.empty(n_boot)
    for b in range(n_boot):
        pick = np.concatenate([groups[k] for k in rng.integers(0, len(groups), len(groups))])
        boots[b] = np.median(err_a[pick]) - np.median(err_b[pick])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return diff, float(lo), float(hi), float(np.mean(boots < 0))
