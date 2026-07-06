"""
backtest.py — Vectorized backtest engine.

Signals are lagged by exactly one bar inside run() — no look-ahead by construction.
All costs (fees, slippage, funding) enter the P&L before any metric is computed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class LookAheadError(ValueError):
    """Raised when a factor is detectably correlated with future or same-bar returns."""


def guard_look_ahead(
    factor: pd.Series,
    returns: pd.Series,
    threshold: float = 0.5,
) -> None:
    """
    Call this on the raw factor BEFORE run().  Raises LookAheadError if the factor
    is suspiciously correlated with same-bar or next-bar returns.

    A real predictive factor should have near-zero contemporaneous correlation
    with the thing it is trying to predict.  A threshold of 0.5 is conservative;
    a factor = next_bar_return will typically exceed 0.9.
    """
    aligned = factor.dropna().align(returns.dropna(), join="inner")
    f, r = aligned[0], aligned[1]

    corr_next = float(f.corr(r.shift(-1).reindex(f.index)))
    if abs(corr_next) > threshold:
        raise LookAheadError(
            f"Factor correlation with NEXT-bar return = {corr_next:.3f} "
            f"(threshold {threshold}) — likely look-ahead contamination."
        )

    corr_same = float(f.corr(r.reindex(f.index)))
    if abs(corr_same) > threshold:
        raise LookAheadError(
            f"Factor correlation with SAME-bar return = {corr_same:.3f} "
            f"(threshold {threshold}) — likely contemporaneous contamination."
        )


def run(
    signal: pd.Series,
    asset_returns: pd.Series,
    funding_rates: pd.Series | None = None,
    fee_bps: float = 7.0,
    slippage_bps: float = 5.0,
    direction: str = "both",
    guard: bool = True,
) -> dict:
    """
    Run a single backtest pass.

    Parameters
    ----------
    signal : pd.Series of {-1, 0, +1}
        Raw signal at each bar. Shifted by 1 bar internally — position at bar t
        is always set from signal at bar t-1. Never pass pre-shifted signals.
    asset_returns : pd.Series
        Bar returns of the underlying (close-to-close or log-returns).
    funding_rates : pd.Series | None
        Periodic funding rate per bar. Applied on held notional each bar.
        Must share the same index as asset_returns if provided.
    fee_bps : float
        Taker fee in basis points applied on each unit of turnover.
    slippage_bps : float
        Slippage in basis points applied on each unit of turnover.
    direction : str
        'long'  — zero out short signals.
        'short' — zero out long signals.
        'both'  — unrestricted long/short.
    guard : bool
        If True (default), call guard_look_ahead before computing any P&L.
        Set to False only in tests that intentionally probe what happens without
        the guard — never disable it in production research pipelines.

    Returns
    -------
    dict with keys:
        position, gross_ret, net_ret, equity, turnover, fee_cost, slip_cost, fund_cost
    """
    if direction not in ("long", "short", "both"):
        raise ValueError(f"direction must be 'long', 'short', or 'both' — got {direction!r}")

    if guard:
        guard_look_ahead(signal, asset_returns)

    idx = asset_returns.index
    sig = signal.reindex(idx).fillna(0)

    if direction == "long":
        sig = sig.clip(lower=0)
    elif direction == "short":
        sig = sig.clip(upper=0)

    # THE mandatory lag — trade on yesterday's signal only
    position = sig.shift(1).fillna(0)

    gross_ret = position * asset_returns

    turnover  = position.diff().abs().fillna(position.abs().iloc[0])

    fee_cost  = turnover * (fee_bps  / 10_000)
    slip_cost = turnover * (slippage_bps / 10_000)

    if funding_rates is not None:
        fund_cost = position * funding_rates.reindex(idx).fillna(0)
    else:
        fund_cost = pd.Series(0.0, index=idx)

    net_ret = gross_ret - fee_cost - slip_cost - fund_cost
    equity  = (1 + net_ret).cumprod()

    return {
        "position":  position,
        "gross_ret": gross_ret,
        "net_ret":   net_ret,
        "equity":    equity,
        "turnover":  turnover,
        "fee_cost":  fee_cost,
        "slip_cost": slip_cost,
        "fund_cost": fund_cost,
    }
