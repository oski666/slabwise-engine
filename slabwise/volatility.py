"""How much a value moves (protocol §24, D127): measured on the engine's weekly estimates, never on raw sales.

moves(): 4-week changes in log; vol(): their standard deviation (the "±x% a month" on the site);
drawdown(): the largest fall from a previous high, as a fraction. NaN weeks (no estimate yet) are skipped.
"""
import numpy as np

LEVELS = ((0.03, "ferma"), (0.06, "tranquilla"), (0.12, "mossa"), (0.20, "agitata"), (np.inf, "ballerina"))


def moves(logv, step=4):
    x = np.asarray(logv, float)
    d = x[step:] - x[:-step]
    return d[np.isfinite(d)]


def vol(logv, step=4):
    d = moves(logv, step)
    return float(np.std(d)) if len(d) >= 4 else float("nan")


def drawdown(logv):
    x = np.asarray(logv, float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return float("nan")
    peak = np.maximum.accumulate(x)
    return float(1 - np.exp(np.min(x - peak)))


def level(v):
    """Word for a monthly volatility (as a log standard deviation)."""
    if not np.isfinite(v):
        return None
    m = np.exp(v) - 1
    return next(name for top, name in LEVELS if m < top)
