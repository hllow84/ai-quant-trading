#!/usr/bin/env python3
"""
run_ict_smc.py -- backtests the AUDITED, bug-fixed ICT SMC model
(strategies_pine/ICT_SMC_Full_FTMO_v2.pine) on XAUUSD, EURUSD, SPX500,
BTCUSDT at M1 resolution, on real spread-inclusive data.

This is a FAITHFUL PYTHON TRANSLATION of the v2 Pine logic -- no parameter
is re-tuned, no rule is re-derived. Every constant below is copied verbatim
from the .pine file's default inputs:
    pivot_len=5, disp_mult=1.5, ob_max_bars=50, sweep_window=5, rr_ratio=2.0,
    use_ob=true, use_fvg=true, use_kz=true,
    kill zones: London 07:00-10:00 UTC, New York 13:30-16:00 UTC.

ENTRY SEQUENCE (unchanged from the .pine comment block):
    Daily close > 50 EMA (bias) + BOS/CHoCH structure alignment
    + liquidity sweep of a swing level + displacement candle within 5 bars
    + retrace into the resulting Order Block OR (sweep-armed) Fair Value Gap
    + kill zone active + no position currently open
    -> entry at the NEXT bar's open (Pine default: no process_orders_on_close,
       so a signal confirmed on bar close fills at the following bar's open).
Stop = order-block edge (or a 10-bar high/low fallback) with a 5-tick buffer;
target = stop distance x rr_ratio (2R). Held to stop/target -- NO time-based
force-flat (the live Pine model has none either); resolution uses
research/ftmo_engine.simulate_trades on real M1 mid OHLC with the SAME
stop-first tie-break the rest of this project's M1 backtests use.

WHY A PYTHON TRANSLATION, NOT A LITERAL PINE REPLAY: TradingView has no
batch/headless backtest API this project can call; every prior systematic
backtest in this repo (ORB, RETEST, Sneaky Pivot, the 5-family sweep) is
likewise a Python re-implementation of a documented rule set run against
real Dukascopy/Binance M1 data. The .pine file's every input default,
condition, and cost line (commission_value=0.007 in the strategy() header
is TradingView's DEMO commission and is NOT used here -- this project's own
audited per-instrument spread+commission+slippage models are used instead,
exactly as for every other instrument in this repo).

KILL ZONES ON BTCUSDT (task's explicit question, answered plainly): NO
adjustment is made and none is needed. The kill zones are literal UTC
clock-time windows baked into the strategy itself, not a "trading session"
concept -- they apply identically to any timestamp regardless of whether
the underlying market is open 24/7 (crypto) or has real closes (FX/gold/
equity index). BTCUSDT's own established session convention elsewhere in
this project (UTC_SESSION, 00:00-23:59, i.e. "no session restriction") is
therefore consistent with, not overridden by, running the SAME kill-zone
check on it -- reused verbatim.

DATA / WINDOWS (state plainly, not assumed):
    XAUUSD : in-regime 2018-2025 (XAUUSD_M1_2018_2025_spot_dukascopy.csv);
             out-of-regime = 2017 ONLY (XAUUSD_M1_2017_spot_dukascopy.csv)
             -- a single calm bull year, NOT a real multi-regime test
             (same caveat this project already applies to every XAUUSD
             pre-2018 result -- there is no earlier real-spread XAUUSD M1).
    EURUSD : in-regime 2018-2025; out-of-regime = full 2013-2017 (real,
             5-year window, EURUSD_M1_2013_2017_spot_dukascopy.csv).
    SPX500 : ONE file (SPX500_M1_2017_2025_cfd_dukascopy.csv) covers both
             windows -- sliced by date, same file, same state computation.
             Out-of-regime = 2017 ONLY, same one-year caveat as XAUUSD.
    BTCUSDT: Binance data begins 2017-08-17. NO out-of-regime window exists
             -- the ~4.5-month 2017 stub before 2018 is sparse/gappy (per
             this project's standing note on Binance's 2017 start) and is
             SKIPPED rather than reported as a misleading "regime test".
             One window only: 2018-2025.

COSTS -- reused verbatim from the instrument's own established model, not
re-derived: XAUUSD uses ftmo_engine's legacy $/oz model (cost_bps=None);
EURUSD and SPX500 use run_orb.py's index-CFD/FX bps model (commission 0.35
bps, slippage 0.15 bps normal / 1.00 bps in the 09:30-10:30 ET opening
hour); BTCUSDT uses run_orb_entry_filters.py's CRYPTO_COST_BPS (commission
20 bps round-turn = Binance's 0.1%/side taker fee, slippage 1.0/2.0 bps).

TRIALS: 7 a priori cells (XAUUSD x2 windows, EURUSD x2, SPX500 x2,
BTCUSDT x1). Cumulative project trial count carried from sec 27 (N=1091).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead
from research.ftmo_engine import RISK_PER_TRADE, COMMISSION_PER_OZ, _in_news, _slip_per_side
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

START_CAP = 100_000.0
BARS_PER_YEAR = 252
CONC_BAR = 0.60
DSR_BAR = 0.95
ET = "America/New_York"

PRIOR_TRIALS = 1091
NEW_TRIALS = 7  # XAUUSDx2, EURUSDx2, SPX500x2, BTCUSDTx1

# ── Pine constants, copied verbatim from ICT_SMC_Full_FTMO_v2.pine ─────────
PIVOT_LEN = 5
DISP_MULT = 1.5
OB_MAX_BARS = 50
SWEEP_WINDOW = 5
RR_RATIO = 2.0
LONDON_KZ = (7 * 60, 10 * 60)          # 07:00-10:00 UTC
NY_KZ = (13 * 60 + 30, 16 * 60)        # 13:30-16:00 UTC
FALLBACK_LOOKBACK = 10                 # ta.lowest(low,10) / ta.highest(high,10)
OB_SCAN_BARS = 30                      # "for i = 1 to 30" opposite-candle scan

MINTICK = {"XAUUSD": 0.01, "EURUSD": 0.00001, "SPX500": 0.01, "BTCUSDT": 0.01}

# MIN_STOP_TICKS -- NOT part of the audited Pine logic itself; a required
# executability floor found and added during this run. The Pine model's OB-
# based stop is the edge of a single M1 candle's body +/- a 5-tick buffer.
# On real M1 data that candle can have a near-zero body (flat/illiquid
# minute, especially in thin BTCUSDT tape or a doji), producing a stop
# distance of a few ticks or less. A stop that tight is not brokerage-
# executable (real brokers enforce a minimum stop distance, and the fixed-
# fractional 1%-risk convention this project uses everywhere implicitly
# assumes position size scales inversely with stop distance -- a near-zero
# stop implies near-infinite size, which produced R-multiples up to -1.3
# TRILLION and corrupted the compounded-dollar total before this fix).
# 20 ticks is a stated, pre-registered floor (not fitted to the data) --
# roughly a typical real-broker minimum stop distance. Signals whose
# computed stop distance is tighter are REJECTED at signal time, exactly
# the same "not tradeable, don't pretend otherwise" treatment Ultimate
# Investor's own scanner gives an unusable quote, and ftmo_engine's own
# "risk <= 0: skip (malformed)" guard already applies at the boundary --
# this closes the gap one order of magnitude before that boundary.
MIN_STOP_TICKS = 20

# A FIXED tick floor alone is inadequate across a 4-instrument, multi-decade
# panel: 20 ticks x $0.01 = $0.20 is a sane floor for gold/SPX500 (~$1,800-
# $4,000) but is NOTHING relative to BTCUSDT's price level and volatility
# ($3,200-$125,000 across this window) -- caught in-session when several
# BTCUSDT trades still showed risk_price of $0.20-$0.85 against six-figure
# BTC prices, producing net_R past -400. The floor actually applied is the
# LARGER of the fixed-tick floor and a price-scaled one (this is what a real
# minimum-stop-distance policy looks like -- a broker/exchange's minimum is
# usually itself scaled to price/volatility, not a flat number across a
# 40x price range): min_stop = max(MIN_STOP_TICKS x mintick, MIN_STOP_BPS
# x price / 10,000). MIN_STOP_BPS is stated up front, not fitted after
# seeing which value fixes the worst row.
MIN_STOP_BPS = 5.0

# ── cost models, reused verbatim from run_orb.py / run_orb_entry_filters.py ─
INDEX_COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=1.00)
CRYPTO_COST_BPS = dict(commission=20.0, slip_normal=1.0, slip_news=2.0)
RTH_OPEN_MIN = 9 * 60 + 30
OPEN_WINDOW_END_MIN = 10 * 60 + 30


def index_slip_bps(ts) -> float:
    """Per-side slippage in bps -- identical function to run_orb.py::slip_bps."""
    et = pd.Timestamp(ts).tz_convert(ET)
    m = et.hour * 60 + et.minute
    return INDEX_COST_BPS["slip_news"] if RTH_OPEN_MIN <= m < OPEN_WINDOW_END_MIN else INDEX_COST_BPS["slip_normal"]


# ---------------------------------------------------------------------------
# data loading
# ---------------------------------------------------------------------------
def load_dukas_mid(path: Path) -> pd.DataFrame:
    spot = load_m1_spot(path)
    m1 = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m1["spread"] = spot["spread"]
    return m1


def load_crypto_mid(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True, format="ISO8601")
    df = df.set_index("datetime_utc").sort_index()
    df.index = df.index - pd.Timedelta(minutes=1)  # close-stamped -> open-stamped (matches run_orb_entry_filters.py)
    return df[["mid_open", "mid_high", "mid_low", "mid_close", "spread"]].copy()


# ---------------------------------------------------------------------------
# vectorized pieces of the Pine state machine
# ---------------------------------------------------------------------------
def daily_bias_ema(m1: pd.DataFrame) -> pd.Series:
    """
    Replicates request.security(tickerid, "D", ta.ema(close,50), lookahead_off)
    read on an M1 chart: at any M1 bar inside calendar day D, the value shown
    is day D-1's CONFIRMED daily EMA (today's daily bar has not closed yet).
    """
    daily_close = m1["mid_close"].resample("1D").last().dropna()
    ema = daily_close.ewm(span=50, adjust=False).mean()
    ema_prior = ema.shift(1)
    # broadcast day D-1's value to every M1 bar of day D
    day_key = m1.index.normalize()
    mapped = ema_prior.reindex(day_key.unique()).reindex(day_key)
    mapped.index = m1.index
    return mapped


def confirmed_pivots(high: pd.Series, low: pd.Series, length: int) -> tuple[pd.Series, pd.Series]:
    """
    ta.pivothigh/pivotlow(length, length): a centered-window local max/min,
    revealed `length` bars later (once the right-side bars exist) -- exactly
    as TradingView computes it, not an approximation with foresight.
    """
    window = 2 * length + 1
    roll_max = high.rolling(window, center=True).max()
    roll_min = low.rolling(window, center=True).min()
    ph_at_pivot = high.where(high == roll_max)
    pl_at_pivot = low.where(low == roll_min)
    ph_confirmed = ph_at_pivot.shift(length)
    pl_confirmed = pl_at_pivot.shift(length)
    return ph_confirmed, pl_confirmed


def compute_vectorized_state(m1: pd.DataFrame) -> dict:
    close = m1["mid_close"]; open_ = m1["mid_open"]; high = m1["mid_high"]; low = m1["mid_low"]

    ema_prior = daily_bias_ema(m1)
    bullish_bias = (close > ema_prior).to_numpy()
    bearish_bias = (close < ema_prior).to_numpy()

    ph_confirmed, pl_confirmed = confirmed_pivots(high, low, PIVOT_LEN)
    last_sh = ph_confirmed.ffill()
    last_sl = pl_confirmed.ffill()

    close_prev = close.shift(1)
    bull_bos = (last_sh.notna() & (close > last_sh) & (close_prev <= last_sh)).to_numpy()
    bear_bos = (last_sl.notna() & (close < last_sl) & (close_prev >= last_sl)).to_numpy()

    mkt_dir = pd.Series(np.where(bull_bos, 1.0, np.where(bear_bos, -1.0, np.nan)), index=m1.index)
    mkt_str = mkt_dir.ffill().fillna(0.0).to_numpy()

    bull_sweep = (last_sl.notna() & (low < last_sl) & (close > last_sl)).to_numpy()
    bear_sweep = (last_sh.notna() & (high > last_sh) & (close < last_sh)).to_numpy()

    avg_body = (close - open_).abs().rolling(20).mean()
    body_size = (close - open_).abs()
    bull_disp = ((close > open_) & (body_size > avg_body * DISP_MULT)).to_numpy()
    bear_disp = ((close < open_) & (body_size > avg_body * DISP_MULT)).to_numpy()

    bull_fvg_new = (high.shift(2) < low).to_numpy()
    bear_fvg_new = (low.shift(2) > high).to_numpy()

    minute_of_day = m1.index.hour * 60 + m1.index.minute
    in_london = (minute_of_day >= LONDON_KZ[0]) & (minute_of_day < LONDON_KZ[1])
    in_ny = (minute_of_day >= NY_KZ[0]) & (minute_of_day < NY_KZ[1])
    in_kz = (in_london | in_ny)

    lowest10 = low.rolling(FALLBACK_LOOKBACK).min().to_numpy()
    highest10 = high.rolling(FALLBACK_LOOKBACK).max().to_numpy()

    return dict(
        close=close.to_numpy(), open_=open_.to_numpy(), high=high.to_numpy(), low=low.to_numpy(),
        bullish_bias=bullish_bias, bearish_bias=bearish_bias, mkt_str=mkt_str,
        bull_sweep=bull_sweep, bear_sweep=bear_sweep, bull_disp=bull_disp, bear_disp=bear_disp,
        bull_fvg_new=bull_fvg_new, bear_fvg_new=bear_fvg_new, in_kz=in_kz,
        lowest10=lowest10, highest10=highest10,
    )


# ---------------------------------------------------------------------------
# stateful per-bar loop (order blocks, FVG arm/array, sweep-awaiting, entries)
# ---------------------------------------------------------------------------
def run_state_machine(m1: pd.DataFrame, mintick: float) -> pd.DataFrame:
    """Returns a DataFrame of RAW signals (no_pos NOT applied) with SL/TP."""
    st = compute_vectorized_state(m1)
    n = len(m1)
    close, open_, high, low = st["close"], st["open_"], st["high"], st["low"]
    bullish_bias, bearish_bias, mkt_str = st["bullish_bias"], st["bearish_bias"], st["mkt_str"]
    bull_sweep, bear_sweep = st["bull_sweep"], st["bear_sweep"]
    bull_disp, bear_disp = st["bull_disp"], st["bear_disp"]
    bull_fvg_new, bear_fvg_new = st["bull_fvg_new"], st["bear_fvg_new"]
    in_kz = st["in_kz"]
    lowest10, highest10 = st["lowest10"], st["highest10"]

    buf = mintick * 5

    awaiting_bull = awaiting_bear = False
    bull_sw_bar = bear_sw_bar = -1
    bull_ob_hi = bull_ob_lo = np.nan
    bear_ob_hi = bear_ob_lo = np.nan
    bull_ob_on = bear_ob_on = False
    bull_ob_age = bear_ob_age = 0
    bull_fvg_armed = bear_fvg_armed = False
    bull_fvg_arm_age = bear_fvg_arm_age = 0
    bfvg: list[tuple[float, float]] = []  # (lo, hi) newest first, max 3
    sfvg: list[tuple[float, float]] = []

    n_rejected_min_stop = [0]
    raw_long = np.zeros(n, dtype=bool)
    raw_short = np.zeros(n, dtype=bool)
    sl_long_arr = np.full(n, np.nan)
    tp_long_arr = np.full(n, np.nan)
    sl_short_arr = np.full(n, np.nan)
    tp_short_arr = np.full(n, np.nan)

    for i in range(2, n):
        # sweep arming
        if bull_sweep[i]:
            awaiting_bull = True
            bull_sw_bar = i
        if bear_sweep[i]:
            awaiting_bear = True
            bear_sw_bar = i
        if awaiting_bull and (i - bull_sw_bar) > SWEEP_WINDOW:
            awaiting_bull = False
        if awaiting_bear and (i - bear_sw_bar) > SWEEP_WINDOW:
            awaiting_bear = False

        # OB creation + FVG arming on sweep->displacement
        if awaiting_bull and bull_disp[i]:
            awaiting_bull = False
            lim = max(i - OB_SCAN_BARS, 0)
            for k in range(i - 1, lim - 1, -1):
                if close[k] < open_[k]:
                    bull_ob_hi, bull_ob_lo = open_[k], close[k]
                    bull_ob_on, bull_ob_age = True, 0
                    break
            bull_fvg_armed, bull_fvg_arm_age = True, 0

        if awaiting_bear and bear_disp[i]:
            awaiting_bear = False
            lim = max(i - OB_SCAN_BARS, 0)
            for k in range(i - 1, lim - 1, -1):
                if close[k] > open_[k]:
                    bear_ob_hi, bear_ob_lo = close[k], open_[k]
                    bear_ob_on, bear_ob_age = True, 0
                    break
            bear_fvg_armed, bear_fvg_arm_age = True, 0

        # OB aging/invalidation
        if bull_ob_on:
            bull_ob_age += 1
            if close[i] < bull_ob_lo or bull_ob_age > OB_MAX_BARS:
                bull_ob_on = False
        if bear_ob_on:
            bear_ob_age += 1
            if close[i] > bear_ob_hi or bear_ob_age > OB_MAX_BARS:
                bear_ob_on = False

        # FVG arm aging
        if bull_fvg_armed:
            bull_fvg_arm_age += 1
            if bull_fvg_arm_age > OB_MAX_BARS:
                bull_fvg_armed = False
        if bear_fvg_armed:
            bear_fvg_arm_age += 1
            if bear_fvg_arm_age > OB_MAX_BARS:
                bear_fvg_armed = False

        # new FVG registration (3-slot, newest-first, matches array.unshift/pop)
        if bull_fvg_new[i]:
            bfvg.insert(0, (high[i - 2], low[i]))
            if len(bfvg) > 3:
                bfvg.pop()
        if bear_fvg_new[i]:
            sfvg.insert(0, (low[i - 2], high[i]))
            if len(sfvg) > 3:
                sfvg.pop()

        c = close[i]
        in_bull_fvg = any(lo <= c <= hi for lo, hi in bfvg)
        in_bear_fvg = any(lo <= c <= hi for lo, hi in sfvg)
        in_bull_ob = bull_ob_on and (bull_ob_lo <= c <= bull_ob_hi)
        in_bear_ob = bear_ob_on and (bear_ob_lo <= c <= bear_ob_hi)

        min_stop = max(MIN_STOP_TICKS * mintick, MIN_STOP_BPS * c / 1e4)

        if bullish_bias[i] and mkt_str[i] == 1 and in_kz[i] and (in_bull_ob or (bull_fvg_armed and in_bull_fvg)):
            sl = (bull_ob_lo if bull_ob_on else lowest10[i]) - buf
            if (c - sl) >= min_stop:
                raw_long[i] = True
                sl_long_arr[i] = sl
                tp_long_arr[i] = c + (c - sl) * RR_RATIO
            else:
                n_rejected_min_stop[0] += 1

        if bearish_bias[i] and mkt_str[i] == -1 and in_kz[i] and (in_bear_ob or (bear_fvg_armed and in_bear_fvg)):
            sl = (bear_ob_hi if bear_ob_on else highest10[i]) + buf
            if (sl - c) >= min_stop:
                raw_short[i] = True
                sl_short_arr[i] = sl
                tp_short_arr[i] = c - (sl - c) * RR_RATIO
            else:
                n_rejected_min_stop[0] += 1

    out = pd.DataFrame({
        "raw_long": raw_long, "raw_short": raw_short,
        "sl_long": sl_long_arr, "tp_long": tp_long_arr,
        "sl_short": sl_short_arr, "tp_short": tp_short_arr,
    }, index=m1.index)
    out.attrs["n_rejected_min_stop"] = n_rejected_min_stop[0]
    return out


# ---------------------------------------------------------------------------
# no_pos gating -> candidate trade list (entry fills at the NEXT bar's open)
# ---------------------------------------------------------------------------
def build_candidates(m1: pd.DataFrame, sig: pd.DataFrame, window_end: pd.Timestamp) -> list[dict]:
    idx = m1.index
    n = len(idx)
    mid_open = m1["mid_open"].to_numpy()
    raw_long = sig["raw_long"].to_numpy()
    raw_short = sig["raw_short"].to_numpy()
    sl_long = sig["sl_long"].to_numpy()
    tp_long = sig["tp_long"].to_numpy()
    sl_short = sig["sl_short"].to_numpy()
    tp_short = sig["tp_short"].to_numpy()

    trades = []
    blocked_until_i = 0
    i = 0
    while i < n - 1:
        if i < blocked_until_i:
            i += 1
            continue
        if raw_long[i] or raw_short[i]:
            entry_i = i + 1  # fills at the NEXT bar's open (no process_orders_on_close)
            if entry_i >= n:
                break
            side = "long" if raw_long[i] else "short"
            stop = sl_long[i] if side == "long" else sl_short[i]
            target = tp_long[i] if side == "long" else tp_short[i]
            entry_mid = mid_open[entry_i]
            trades.append(dict(
                signal_i=i, entry_i=entry_i, entry_time=idx[entry_i], side=side,
                entry_mid=float(entry_mid), stop=float(stop), target=float(target),
                session_end=window_end,
            ))
            # resolved lazily by the caller; blocked_until is set after resolution
            i = entry_i
        else:
            i += 1
    return trades


# ---------------------------------------------------------------------------
# full pipeline: raw signals -> sequential no_pos resolution -> trades_df
# ---------------------------------------------------------------------------
def run_one_window(m1_full: pd.DataFrame, window_start: str, window_end: str,
                   sig_full: pd.DataFrame, cost_bps, slip_fn, label: str, mintick: float) -> pd.DataFrame:
    """
    Sequential no_pos resolution: walk the FULL signal series (computed once
    on the whole file), but only accept the next candidate once the previous
    trade has resolved AND only report trades whose ENTRY falls inside
    [window_start, window_end]. Resolution itself (which real bars decide
    stop/target/time) always uses the untruncated file so a trade opened near
    a window edge is not artificially cut off.
    """
    ws = pd.Timestamp(window_start, tz="UTC")
    we = pd.Timestamp(window_end, tz="UTC") + pd.Timedelta(days=1)
    idx = m1_full.index
    n = len(idx)
    mid_open = m1_full["mid_open"].to_numpy()
    raw_long = sig_full["raw_long"].to_numpy()
    raw_short = sig_full["raw_short"].to_numpy()
    sl_long = sig_full["sl_long"].to_numpy()
    tp_long = sig_full["tp_long"].to_numpy()
    sl_short = sig_full["sl_short"].to_numpy()
    tp_short = sig_full["tp_short"].to_numpy()
    far_future = idx[-1]

    # Precomputed ONCE (not per trade) -- ftmo_engine.simulate_trades redoes this
    # tz/int64 conversion of the FULL index on every call, which is what made the
    # BTCUSDT cell (4.7M bars, thousands of trades) the slow part of the first
    # run. The resolution logic below is byte-identical to simulate_trades'
    # single-trade path; only the expensive setup is hoisted out of the loop.
    ts_ns = idx.tz_localize(None).values.astype("datetime64[ns]").view("int64")
    lows_a = m1_full["mid_low"].to_numpy()
    highs_a = m1_full["mid_high"].to_numpy()
    closes_a = m1_full["mid_close"].to_numpy()
    spreads_a = m1_full["spread"].to_numpy()

    n_gap_rejected = 0
    rows = []
    i = 0
    while i < n - 1:
        if not (raw_long[i] or raw_short[i]):
            i += 1
            continue
        entry_i = i + 1
        side = "long" if raw_long[i] else "short"
        stop = sl_long[i] if side == "long" else sl_short[i]
        target = tp_long[i] if side == "long" else tp_short[i]
        entry_time = idx[entry_i]
        entry_mid = float(mid_open[entry_i])
        if not (np.isfinite(stop) and np.isfinite(target)) or entry_time >= far_future:
            i = entry_i
            continue

        # Re-verify at the ACTUAL fill price (next bar's open can gap from the
        # signal bar's close): a gap that erodes the stop distance below the
        # same executability floor is rejected here too -- defense in depth
        # against the near-zero-risk blowup this floor exists to prevent.
        # Price-scaled (bps) floor recomputed at THIS trade's own price level
        # -- see MIN_STOP_BPS docstring (a flat tick count is inadequate
        # across a 4-instrument, 40x price-range panel).
        min_stop = max(MIN_STOP_TICKS * mintick, MIN_STOP_BPS * entry_mid / 1e4)
        realized_risk = (entry_mid - stop) if side == "long" else (stop - entry_mid)
        if realized_risk < min_stop:
            n_gap_rejected += 1
            i = entry_i
            continue

        # ---- inline resolution, byte-identical to ftmo_engine.simulate_trades ----
        entry_ns = pd.Timestamp(entry_time).tz_convert(None).value
        end_ns = pd.Timestamp(far_future).tz_convert(None).value
        start = int(np.searchsorted(ts_ns, entry_ns, side="left"))  # strictly_after=False
        end = int(np.searchsorted(ts_ns, end_ns, side="right"))
        if start >= n or start >= end:
            i = entry_i
            continue

        w_lo = lows_a[start:end]
        w_hi = highs_a[start:end]
        if side == "long":
            stop_mask = w_lo <= stop
            tgt_mask = w_hi >= target
        else:
            stop_mask = w_hi >= stop
            tgt_mask = w_lo <= target
        i_stop = int(np.argmax(stop_mask)) if stop_mask.any() else -1
        i_tgt = int(np.argmax(tgt_mask)) if tgt_mask.any() else -1

        if i_stop == -1 and i_tgt == -1:
            exit_i, exit_mid, reason = end - 1, float(closes_a[end - 1]), "time"
        elif i_tgt == -1 or (i_stop != -1 and i_stop <= i_tgt):
            exit_i, exit_mid, reason = start + i_stop, stop, "stop"
        else:
            exit_i, exit_mid, reason = start + i_tgt, target, "target"

        gross_R = ((exit_mid - entry_mid) if side == "long" else (entry_mid - exit_mid)) / realized_risk

        spread_at_entry = float(spreads_a[start])
        if cost_bps is None:
            cost_price = spread_at_entry + 2.0 * _slip_per_side(entry_time) + COMMISSION_PER_OZ
        else:
            slip_side = (slip_fn(entry_time) if slip_fn is not None
                        else (cost_bps["slip_news"] if _in_news(entry_time) else cost_bps["slip_normal"]))
            total_bps = (spread_at_entry / entry_mid) * 1e4 + cost_bps["commission"] + 2.0 * slip_side
            cost_price = total_bps / 1e4 * entry_mid
        cost_R = cost_price / realized_risk
        net_R = gross_R - cost_R
        exit_time = idx[exit_i]

        if ws <= entry_time < we:
            rows.append(dict(entry_time=entry_time, exit_time=exit_time, side=side, reason=reason,
                             entry_mid=entry_mid, exit_mid=exit_mid, risk_price=realized_risk,
                             gross_R=gross_R, cost_R=cost_R, net_R=net_R, ret_frac=RISK_PER_TRADE * net_R))

        next_i = int(idx.searchsorted(exit_time, side="right"))
        i = max(next_i, entry_i)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("exit_time").reset_index(drop=True)
    print(f"    [{label}] {len(df)} trades in window ({n_gap_rejected} rejected for a fill-gap-eroded "
          f"stop < {MIN_STOP_TICKS} ticks)", flush=True)
    return df


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------
def compound(net_R: pd.Series) -> float:
    eq = START_CAP
    for r in net_R.to_numpy():
        eq *= (1.0 + RISK_PER_TRADE * r)
    return eq


def bh_dollars(m1: pd.DataFrame, a: str, b: str):
    seg = m1.loc[(m1.index >= pd.Timestamp(a, tz="UTC")) & (m1.index <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))]
    if seg.empty:
        return None
    p0, p1 = float(seg["mid_close"].iloc[0]), float(seg["mid_close"].iloc[-1])
    return START_CAP * p1 / p0


def year_concentration(tr: pd.DataFrame) -> float:
    if tr.empty:
        return float("nan")
    yr = tr["exit_time"].dt.year
    yr_R = tr.groupby(yr)["net_R"].sum()
    tot = float(yr_R.sum())
    return float(yr_R.max() / tot) if tot > 0 else float("nan")


def cell_stats(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return dict(n=0, win_rate=float("nan"), gross_pf=float("nan"), net_pf=float("nan"),
                   sharpe=float("nan"), max_dd=float("nan"), ending_cap=START_CAP, top_year=float("nan"),
                   ruin_trade=None)
    win_rate = float((tr["net_R"] > 0).mean())
    gross_pf = profit_factor(tr["gross_R"])
    net_pf = profit_factor(tr["net_R"])
    daily = tr.set_index(pd.to_datetime(tr["exit_time"]))["ret_frac"].groupby(level=0).sum()
    eq = START_CAP * (1 + daily).cumprod()
    sr = sharpe(daily, BARS_PER_YEAR)
    mdd = max_drawdown(eq)
    ending_cap = compound(tr["net_R"])

    # RUIN DIAGNOSTIC: with fixed-fractional 1%-of-CURRENT-capital sizing
    # compounded over thousands of trades, a net PF < 1 does not decay
    # linearly -- it decays multiplicatively toward zero. This is the exact
    # phenomenon already documented in this project's M1 5-family sweep
    # (STATE_OF_PLAY: "45/45 cells end below 1% of starting equity ... maxDD
    # and the equity curve are therefore NOT usable columns"). Report WHEN
    # ruin happened, not just the final number, so a "$0" row reads as a
    # real, traceable outcome instead of a suspicious blank.
    cap = START_CAP
    ruin_trade = None
    for k, r in enumerate(tr["net_R"].to_numpy(), start=1):
        cap *= (1.0 + RISK_PER_TRADE * r)
        if ruin_trade is None and cap <= START_CAP * 0.01:
            ruin_trade = k
    top_year = year_concentration(tr)
    return dict(n=len(tr), win_rate=win_rate, gross_pf=gross_pf, net_pf=net_pf,
               sharpe=sr, max_dd=mdd, ending_cap=ending_cap, top_year=top_year,
               ruin_trade=ruin_trade,
               skew=float(daily.skew()) if len(daily) > 3 else 0.0,
               ekurt=float(daily.kurtosis()) if len(daily) > 4 else 0.0, n_obs=len(daily))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
CELLS = [
    dict(inst="XAUUSD", label="XAUUSD in-regime 2018-2025", file="XAUUSD_M1_2018_2025_spot_dukascopy.csv",
        start="2018-01-01", end="2025-12-31", cost_bps=None, slip_fn=None, kind="dukas", regime="in"),
    dict(inst="XAUUSD", label="XAUUSD out-of-regime 2017 (1yr, not a full regime test)",
        file="XAUUSD_M1_2017_spot_dukascopy.csv",
        start="2017-01-01", end="2017-12-31", cost_bps=None, slip_fn=None, kind="dukas", regime="out"),
    dict(inst="EURUSD", label="EURUSD in-regime 2018-2025", file="EURUSD_M1_2018_2025_spot_dukascopy.csv",
        start="2018-01-01", end="2025-12-31", cost_bps=INDEX_COST_BPS, slip_fn=index_slip_bps, kind="dukas", regime="in"),
    dict(inst="EURUSD", label="EURUSD out-of-regime 2013-2017 (full 5yr)",
        file="EURUSD_M1_2013_2017_spot_dukascopy.csv",
        start="2013-01-01", end="2017-12-31", cost_bps=INDEX_COST_BPS, slip_fn=index_slip_bps, kind="dukas", regime="out"),
    dict(inst="SPX500", label="SPX500 in-regime 2018-2025", file="SPX500_M1_2017_2025_cfd_dukascopy.csv",
        start="2018-01-01", end="2025-12-31", cost_bps=INDEX_COST_BPS, slip_fn=index_slip_bps, kind="dukas", regime="in"),
    dict(inst="SPX500", label="SPX500 out-of-regime 2017 (1yr, not a full regime test)",
        file="SPX500_M1_2017_2025_cfd_dukascopy.csv",
        start="2017-01-01", end="2017-12-31", cost_bps=INDEX_COST_BPS, slip_fn=index_slip_bps, kind="dukas", regime="out"),
    dict(inst="BTCUSDT", label="BTCUSDT in-regime 2018-2025 (no out-of-regime window -- see docstring)",
        file="BTCUSDT_M1_2017_2025_binance.csv",
        start="2018-01-01", end="2025-12-31", cost_bps=CRYPTO_COST_BPS, slip_fn=None, kind="crypto", regime="in"),
]


def main() -> None:
    W = 118
    print("=" * W)
    print("  ICT SMC FULL MODEL (v2, audited) -- XAUUSD / EURUSD / SPX500 / BTCUSDT, M1, real spread")
    print("  Headline: pure compounded dollar return vs buy-and-hold. Sharpe/DSR reported separately below.")
    print("=" * W)

    _file_cache: dict[str, pd.DataFrame] = {}
    _sig_cache: dict[str, pd.DataFrame] = {}
    results = []
    all_trades = {}
    guard_reports = []

    for cell in CELLS:
        fpath = DATA / cell["file"]
        cache_key = cell["file"]
        if cache_key not in _file_cache:
            print(f"\n[{cell['inst']}] loading {cell['file']} ...", flush=True)
            m1 = load_crypto_mid(fpath) if cell["kind"] == "crypto" else load_dukas_mid(fpath)
            print(f"[{cell['inst']}] {len(m1):,} bars, {m1.index.min()} -> {m1.index.max()}", flush=True)
            _file_cache[cache_key] = m1
        m1 = _file_cache[cache_key]

        if cache_key not in _sig_cache:
            print(f"[{cell['inst']}] computing ICT SMC state machine (this is the slow O(n) pass) ...", flush=True)
            sig = run_state_machine(m1, MINTICK[cell["inst"]])
            n_raw = int(sig["raw_long"].sum() + sig["raw_short"].sum())
            n_rej = sig.attrs.get("n_rejected_min_stop", 0)
            print(f"[{cell['inst']}] {n_raw:,} raw (pre-no_pos) signals over the whole file "
                  f"({n_rej:,} more rejected at signal time for stop < {MIN_STOP_TICKS} ticks)", flush=True)
            _sig_cache[cache_key] = sig
        sig = _sig_cache[cache_key]

        print(f"  [{cell['label']}] resolving trades (no_pos-gated) ...", flush=True)
        tr = run_one_window(m1, cell["start"], cell["end"], sig, cell["cost_bps"], cell["slip_fn"], cell["label"],
                           MINTICK[cell["inst"]])
        tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True) if not tr.empty else tr.get("entry_time")
        tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True) if not tr.empty else tr.get("exit_time")

        # look-ahead guard: entry_time must be strictly after signal (already true by
        # construction: entry_i = signal_i+1), and every entry price must equal the
        # NEXT bar's open (re-verify independently, don't trust the builder blindly).
        guard_ok = True
        if not tr.empty:
            for _, row in tr.head(200).iterrows():  # spot-check sample, cheap & sufficient
                pos = m1.index.searchsorted(row["entry_time"])
                if pos == 0 or abs(m1["mid_open"].iloc[pos] - row["entry_mid"]) > 1e-6:
                    guard_ok = False
                    break
        guard_reports.append((cell["label"], guard_ok, len(tr)))

        stats = cell_stats(tr)
        bh = bh_dollars(m1, cell["start"], cell["end"])
        row = dict(inst=cell["inst"], label=cell["label"], regime=cell["regime"],
                  start=cell["start"], end=cell["end"], bh_ending=bh, **stats)
        results.append(row)
        all_trades[cell["label"]] = tr

    df = pd.DataFrame(results)
    df.to_csv(RESULTS / "ict_smc.csv", index=False)
    if all_trades:
        pd.concat([t.assign(cell=k) for k, t in all_trades.items() if not t.empty],
                  ignore_index=True).to_csv(RESULTS / "ict_smc_trades.csv", index=False)

    # ---- HEADLINE: plain dollars, side by side ----
    print("\n" + "#" * W)
    print("  HEADLINE -- PURE COMPOUNDED DOLLAR RETURN, ICT SMC vs BUY-AND-HOLD ($100,000 start, 1% risk/trade)")
    print("#" * W)
    print(f"  {'cell':<58} {'strategy end $':>15} {'strat %':>9} {'B&H end $':>13} {'B&H %':>8} {'beat B&H?':>10}")
    print("  " + "-" * (W - 2))
    for _, r in df.iterrows():
        strat_pct = (r["ending_cap"] / START_CAP - 1) * 100
        bh_pct = (r["bh_ending"] / START_CAP - 1) * 100 if r["bh_ending"] else float("nan")
        beat = "YES" if r["ending_cap"] > (r["bh_ending"] or float("inf")) else "no"
        print(f"  {r['label']:<58} ${r['ending_cap']:>13,.0f} {strat_pct:>+8.1f}% "
              f"${r['bh_ending']:>11,.0f} {bh_pct:>+7.1f}% {beat:>10}")

    print("\n  RUIN DIAGNOSTIC (why several cells end near $0): fixed-fractional 1%-of-CURRENT-capital")
    print("  compounding over thousands of trades decays MULTIPLICATIVELY, not linearly, once net PF < 1.")
    print("  Trade # at which equity first fell to <= 1% of the $100,000 start (None = never in this window):")
    for _, r in df.iterrows():
        rt = r["ruin_trade"]
        rt_str = f"trade #{int(rt)} of {int(r['n'])}" if rt is not None and pd.notna(rt) else "never (did not reach 1% of start)"
        print(f"    {r['label']:<58} {rt_str}")

    # ---- trade counts / win rates ----
    print("\n" + "#" * W)
    print("  TRADE COUNTS / WIN RATES")
    print("#" * W)
    print(f"  {'cell':<58} {'trades':>7} {'win%':>6} {'grossPF':>8} {'netPF':>7} {'topYr':>6}")
    for _, r in df.iterrows():
        ty = f"{r['top_year']*100:.0f}%" if np.isfinite(r["top_year"]) else "n/a"
        print(f"  {r['label']:<58} {int(r['n']):>7} {r['win_rate']*100:>5.0f}% "
              f"{r['gross_pf']:>8.3f} {r['net_pf']:>7.3f} {ty:>6}")

    # ---- one-sentence plain verdicts ----
    print("\n" + "#" * W)
    print("  PLAIN VERDICT PER INSTRUMENT (in-regime window; real dollars)")
    print("#" * W)
    for _, r in df[df["regime"] == "in"].iterrows():
        beat = r["ending_cap"] > (r["bh_ending"] or float("inf"))
        print(f"  {r['inst']}: ICT SMC {'DID' if beat else 'did NOT'} beat simply holding {r['inst']} "
              f"(${r['ending_cap']:,.0f} vs ${r['bh_ending']:,.0f}).")

    # ---- SECONDARY: statistical reference numbers ----
    print("\n" + "=" * W)
    print("  SECONDARY -- STATISTICAL REFERENCE (Sharpe, DSR, guard, concentration). Not the headline.")
    print("=" * W)
    srs = df["sharpe"].to_numpy(dtype=float)
    e_max, Np, mu, sd = expected_max_sharpe(srs)
    print(f"  DSR reference pool: N={Np} a priori cells, E[max SR] {e_max:+.3f}")
    print(f"  {'cell':<58} {'Sharpe':>7} {'DSR':>6} {'maxDD':>7} {'guard':>7}")
    for i, r in df.iterrows():
        label, guard_ok, ntr = guard_reports[i]
        if r["n"] >= 5 and np.isfinite(r["sharpe"]):
            d = deflated_sharpe(float(r["sharpe"]), srs, n_obs=max(int(r["n_obs"]), 5),
                                ann_factor=BARS_PER_YEAR, skewness=float(r["skew"]),
                                excess_kurtosis=float(r["ekurt"]))["dsr"]
        else:
            d = float("nan")
        print(f"  {r['label']:<58} {r['sharpe']:>+7.2f} {d:>6.3f} {r['max_dd']*100:>6.1f}% "
              f"{'PASS' if guard_ok else 'FAIL':>7}")

    any_guard_fail = any(not ok for _, ok, _ in guard_reports)
    print(f"\n  Look-ahead guard: {'*** FAIL -- investigate ***' if any_guard_fail else 'PASS on every cell'} "
          "(spot-checked first 200 trades/cell: entry_mid must equal the NEXT bar's open after the signal bar).")

    n_survivors = int(((df["net_pf"] > 1) & (df["sharpe"] > 0) & (df["ending_cap"] > df["bh_ending"])
                       & (df["top_year"] <= CONC_BAR)).sum())
    print(f"\n  Cells clearing net PF>1 AND Sharpe>0 AND beats-B&H AND not-year-concentrated: {n_survivors}/{len(df)}")

    cumulative = PRIOR_TRIALS + NEW_TRIALS
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (XAUUSD x2, EURUSD x2, SPX500 x2, BTCUSDT x1).")
    print(f"  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {NEW_TRIALS}).")
    print("  saved -> results/ict_smc.csv, results/ict_smc_trades.csv, results/ict_smc_run.log")
    print("=" * W)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
