#!/usr/bin/env python3
"""
baseline_sma200.py — Fixed SMA-200 long-only baseline for gold (XAUUSD).

SYMBOL and COST_PROFILES are top-level parameters. To switch instrument:
    SYMBOL = "EURUSD"   ← one-line change; add EURUSD costs to COST_PROFILES first.

Design intent:
  - This is an honest, un-tuned benchmark, not a strategy to optimize.
  - A mediocre or negative result here is the expected and correct outcome.
  - All costs are applied before any metric is reported.
  - The harness look-ahead guard is called explicitly.

Data pipeline note:
  Dukascopy (datafeed.dukascopy.com) is unreachable from this machine —
  TLS read timeout confirmed on both duka (Python) and dukascopy-node.
  Fallback: yfinance GC=F (CME gold continuous futures, same underlying).
  When Dukascopy becomes accessible, replace fetch_daily_ohlcv() — the
  rest of the script is data-source agnostic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import date

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.backtest import run as bt_run, guard_look_ahead, LookAheadError
from research.metrics import (
    sharpe, sortino, max_drawdown, profit_factor, hit_rate,
    deflated_sharpe_ratio,
)

# ══════════════════════════════════════════════════════════════════════════════
# TOP-LEVEL PARAMETERS — change SYMBOL here to switch instrument
# ══════════════════════════════════════════════════════════════════════════════
SYMBOL        = "XAUUSD"
BARS_PER_YEAR = 252            # daily trading days per year (CME gold / forex)
DATA_DIR      = _ROOT / "data" / "cache"
FETCH_START   = "2019-01-01"   # ~7 years of daily bars
FETCH_END     = date.today().strftime("%Y-%m-%d")

# yfinance ticker map: add entries here for new instruments
YF_TICKERS: dict[str, str] = {
    "XAUUSD": "GC=F",       # CME gold continuous futures
    "EURUSD": "EURUSD=X",   # FX spot
}

# ══════════════════════════════════════════════════════════════════════════════
# COST PROFILES — keyed by symbol
# bt_run() charges: turnover × (fee_bps + slippage_bps) / 10_000 per bar,
# where turnover = |Δposition|.  For a long-only strategy that enters/exits
# once per trade: one bar of turnover=1 on entry, one on exit.
# 4 bps total round-turn here = fee_bps=4 applied on each position change.
# ══════════════════════════════════════════════════════════════════════════════
COST_PROFILES: dict[str, dict] = {
    "XAUUSD": {
        "fee_bps":      4.0,   # PROVISIONAL — spread + commission, 4 bps round-turn
        "slippage_bps": 0.0,   # included in fee_bps for now
        "note": (
            "PROVISIONAL: 4 bps round-turn (spread + commission). "
            "Replace with real Dukascopy spread data when feed is accessible."
        ),
    },
    "EURUSD": {
        "fee_bps":      None,  # placeholder — not yet determined
        "slippage_bps": None,
        "note": "placeholder — costs not yet determined; fill before running",
    },
}


def _get_costs(symbol: str) -> tuple[float, float]:
    """Return (fee_bps, slippage_bps). Raises clearly if symbol not configured."""
    profile = COST_PROFILES.get(symbol)
    if profile is None:
        raise KeyError(
            f"No cost profile for '{symbol}'. "
            "Add an entry to COST_PROFILES before running."
        )
    if profile["fee_bps"] is None:
        raise ValueError(
            f"Cost profile for '{symbol}' is a placeholder — "
            "fill in fee_bps and slippage_bps before running."
        )
    return float(profile["fee_bps"]), float(profile["slippage_bps"])


# ══════════════════════════════════════════════════════════════════════════════
# DATA — download via yfinance, cache as parquet
# ══════════════════════════════════════════════════════════════════════════════

def fetch_daily_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Download daily OHLCV for symbol. Checks cache first; downloads on miss.
    Returns DataFrame with UTC DatetimeIndex and columns [open, high, low, close, volume].

    Source priority:
      1. Dukascopy — unreachable from this machine (TLS timeout); skipped.
      2. yfinance (GC=F for XAUUSD, EURUSD=X for EURUSD) — used as fallback.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check for any existing cache file for this symbol
    existing = sorted(DATA_DIR.glob(f"yfinance__{symbol}__ohlcv__1d__*.parquet"))
    if existing:
        path = existing[-1]
        print(f"  [cache] {path.name}")
        df = pd.read_parquet(path)
        return df

    ticker = YF_TICKERS.get(symbol)
    if ticker is None:
        raise ValueError(
            f"No yfinance ticker for '{symbol}'. Add it to YF_TICKERS."
        )

    print(f"  [yfinance] Downloading {ticker} daily {start} → {end} …")
    import yfinance as yf
    raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker}.")

    # yfinance returns MultiIndex columns: ('Close','GC=F'), ('High','GC=F'), …
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.columns = [c.lower() for c in raw.columns]

    df = raw[["open", "high", "low", "close", "volume"]].copy()

    # Ensure UTC DatetimeIndex
    if df.index.tz is None:
        df.index = pd.to_datetime(df.index).tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df.index.name = "date"
    df = df.dropna(subset=["close"])

    today_str = date.today().strftime("%Y-%m-%d")
    cache_path = DATA_DIR / f"yfinance__{symbol}__ohlcv__1d__{today_str}.parquet"
    df.to_parquet(cache_path)
    print(f"  [cache] Saved → {cache_path.name}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL — SMA-200 long-only, no parameters to tune
# ══════════════════════════════════════════════════════════════════════════════

def build_signal(close: pd.Series) -> pd.Series:
    """
    Long (1) when close > 200-day SMA; flat (0) otherwise. No shorting.

    bt_run() applies position[t] = signal[t-1] internally, so each bar's
    position uses only the PRIOR day's close — no look-ahead.
    The first 199 bars have NaN SMA; they are forced to 0 (flat).
    """
    sma200 = close.rolling(200, min_periods=200).mean()
    signal = (close > sma200).astype(int)
    signal = signal.where(sma200.notna(), other=0)
    return signal.rename("sma200_signal")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 62)
    print(f"  Baseline: SMA-200 long-only  |  {SYMBOL}  |  Daily bars")
    print("=" * 62)

    # ── 1. Data ────────────────────────────────────────────────────────────────
    print("\n[1] DATA")
    df    = fetch_daily_ohlcv(SYMBOL, FETCH_START, FETCH_END)
    close = df["close"].dropna()

    n_rows   = len(df)
    dt_first = close.index[0].strftime("%Y-%m-%d")
    dt_last  = close.index[-1].strftime("%Y-%m-%d")

    print(f"  Source      : yfinance {YF_TICKERS[SYMBOL]}  "
          f"(Dukascopy unreachable — TLS timeout)")
    print(f"  Rows        : {n_rows:,}")
    print(f"  First date  : {dt_first}")
    print(f"  Last date   : {dt_last}")
    print(f"  Columns     : {list(df.columns)}")
    print(f"  Price range : ${close.min():,.2f} – ${close.max():,.2f}")

    # ── 2. Cost profile ────────────────────────────────────────────────────────
    fee_bps, slippage_bps = _get_costs(SYMBOL)
    print(f"\n[2] COST PROFILE  ({SYMBOL})")
    print(f"  fee_bps      : {fee_bps}  (applied per |delta_position| by bt_run)")
    print(f"  slippage_bps : {slippage_bps}")
    print(f"  Note         : {COST_PROFILES[SYMBOL]['note']}")

    # ── 3. Signal ──────────────────────────────────────────────────────────────
    print(f"\n[3] SIGNAL  (fixed — no optimization)")
    print(f"  Rule      : long if close[t] > SMA(close, 200)[t]  →  position[t+1]")
    print(f"  Lag       : 1 bar applied inside bt_run (position = signal.shift(1))")
    print(f"  Values    : {{0, 1}}  (long-only, no shorts)")
    print(f"  n_configs : 1  (no parameter grid, no selection bias)")

    signal  = build_signal(close)
    returns = close.pct_change().rename("asset_return")

    # Align on valid index (drop NaN return on first bar)
    idx     = signal.index.intersection(returns.dropna().index)
    signal  = signal.loc[idx]
    returns = returns.loc[idx]

    # ── 4. Sharpe annualisation note ──────────────────────────────────────────
    print(f"\n[4] SHARPE ANNUALISATION")
    default_bpy  = 8_760   # harness default (hourly)
    correction   = (default_bpy / BARS_PER_YEAR) ** 0.5
    print(f"  Harness default : {default_bpy} bars/yr  (designed for 1h crypto data)")
    print(f"  This script     : {BARS_PER_YEAR} bars/yr  (daily)")
    print(f"  Correction      : sqrt({default_bpy}/{BARS_PER_YEAR}) = {correction:.2f}x")
    print(f"  Consequence     : using wrong default inflates Sharpe {correction:.2f}x; "
          f"all calls below pass bars_per_year={BARS_PER_YEAR}")

    # ── 5. Look-ahead guard ────────────────────────────────────────────────────
    print(f"\n[5] LOOK-AHEAD GUARD")
    try:
        guard_look_ahead(signal, returns, threshold=0.5)
        print("  PASS — signal |correlation| with next-bar and same-bar returns < 0.5")
    except LookAheadError as exc:
        print(f"  FAIL: {exc}")
        sys.exit(1)

    # ── 6. Backtest ────────────────────────────────────────────────────────────
    print(f"\n[6] BACKTEST  (direction=long)")

    result = bt_run(
        signal, returns,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        direction="long",
    )
    net_ret  = result["net_ret"]
    equity   = result["equity"]
    position = result["position"]

    # Gross (costs=0) for drag comparison; guard already passed, skip re-check
    result_g  = bt_run(signal, returns, fee_bps=0, slippage_bps=0,
                       direction="long", guard=False)
    net_ret_g = result_g["net_ret"]

    # ── 7. Metrics ─────────────────────────────────────────────────────────────
    sr_gross  = sharpe(net_ret_g, BARS_PER_YEAR)
    sr_net    = sharpe(net_ret,   BARS_PER_YEAR)
    sr_sort   = sortino(net_ret,  BARS_PER_YEAR)
    mdd       = max_drawdown(equity)
    pf        = profit_factor(net_ret)
    hr        = hit_rate(net_ret)
    fee_drag  = float(result["fee_cost"].sum())
    slip_drag = float(result["slip_cost"].sum())

    # Trade count: number of bars where position changes (entries + exits)
    pos_changes = int(position.diff().abs().gt(0).sum())
    entries     = int((position.diff() > 0).sum())

    # DSR — n_configs=1: no parameter selection, no haircut needed.
    # With N=1 the formula's E[max SR] → -inf, so dsr_prob → 1.0 (trivial).
    # Reporting it for completeness; the meaningful statistic here is just SR.
    try:
        dsr_prob, e_max_sr = deflated_sharpe_ratio(
            sr_best=sr_net,
            sr_trials=[sr_net],      # N = n_configs = 1
            n_obs=len(net_ret),
            skewness=float(net_ret.skew()),
            excess_kurtosis=float(net_ret.kurtosis()),
        )
    except Exception:
        dsr_prob, e_max_sr = float("nan"), float("nan")

    # ── 8. Report ──────────────────────────────────────────────────────────────
    sep = "=" * 62
    print(f"\n{sep}")
    print(f"  RESULTS  |  {SYMBOL}  |  SMA-200 baseline  |  {dt_first} – {dt_last}")
    print(sep)
    print(f"  {'Metric':<34}  {'Value':>14}")
    print(f"  {'-'*34}  {'-'*14}")
    print(f"  {'Gross Sharpe  (no costs)':<34}  {sr_gross:>14.3f}")
    print(f"  {'Net Sharpe    (after costs)':<34}  {sr_net:>14.3f}")
    print(f"  {'Deflated Sharpe prob  (n=1)':<34}  {dsr_prob:>14.4f}  *")
    print(f"  {'  E[max SR]  (n=1, trivial)':<34}  {e_max_sr:>14.3f}")
    print(f"  {'Sortino ratio':<34}  {sr_sort:>14.3f}")
    print(f"  {'Max drawdown':<34}  {mdd:>13.1%}")
    print(f"  {'Profit factor':<34}  {pf:>14.3f}")
    print(f"  {'Win rate  (active bars)':<34}  {hr:>13.1%}")
    print(f"  {'Trade entries':<34}  {entries:>14,}")
    print(f"  {'Position changes (entries+exits)':<34}  {pos_changes:>14,}")
    print(f"  {'Fee drag  (total, fraction)':<34}  {fee_drag:>14.5f}")
    print(f"  {'Slip drag (total, fraction)':<34}  {slip_drag:>14.5f}")
    print(f"  {'Annualisation  (bars/yr)':<34}  {BARS_PER_YEAR:>14,}")
    print(f"  {'Cost profile':<34}  {fee_bps} bps fee + {slippage_bps} slip")
    print(sep)
    print("  * DSR n=1: no parameter selection → no deflation needed.")
    print("    With N=1, E[max SR] → −∞ and prob → 1.0 (mathematically trivial).")
    print("    The meaningful number is Net Sharpe and its t-stat, not DSR.")
    print(sep)

    if sr_net > 0.1:
        verdict = "PROFITABLE after costs"
    elif sr_net > -0.1:
        verdict = "BREAK-EVEN after costs"
    else:
        verdict = "LOSS after costs"

    cost_diff = sr_gross - sr_net
    print(f"\n  ONE LINE: {verdict}  "
          f"(Gross SR={sr_gross:.3f}  →  Net SR={sr_net:.3f};  "
          f"cost drag={cost_diff:.3f} SR units)")
    print()


if __name__ == "__main__":
    main()
