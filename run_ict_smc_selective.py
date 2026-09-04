#!/usr/bin/env python3
"""
run_ict_smc_selective.py -- SELECTIVE variant of the audited ICT SMC model
(research_log section 29). Builds ONE new, clearly-labelled variant,
"ICT-SMC SELECTIVE v1", that layers FOUR pre-registered discretionary-trader
filters on top of the EXACT section-28 engine (run_ict_smc.py).

WHAT IS REUSED UNCHANGED FROM run_ict_smc.py (imported, not re-implemented):
    - the per-bar ICT state machine mechanics (sweep -> displacement -> Order
      Block / sweep-armed FVG, OB aging, FVG 3-slot array, kill zones)
    - the cost model (per-instrument: XAUUSD legacy $/oz; EURUSD/SPX500 index
      bps 0.35 comm + 0.15/1.00 slip; BTCUSDT CRYPTO_COST_BPS 20 bps)
    - the min-stop-distance floor  max(20 ticks, 5 bps of price)  and its
      fill-gap re-check -- byte identical, via run_ict_smc.run_one_window
    - entry at the NEXT bar's open, sequential no_pos gate, stop-first tie-break
    - the $100k / 1% compounding convention, the ruin diagnostic, the
      look-ahead guard, per-year concentration, buy-and-hold comparison
    - the same 7 a priori cells (XAUUSD x2 windows, EURUSD x2, SPX500 x2,
      BTCUSDT x1), same files, same windows.

Only ONE thing changes: which raw signals are ACCEPTED. Four filters, each a
real pre-registered gate with a named reason. Every threshold is stated here
BEFORE the run and is NOT tuned after seeing results.

=======================================================================
FILTER 1 -- SWEEP QUALITY  (reason: distinguish an institutional-grade
            liquidity raid from a shallow wick through a minor pivot)
-----------------------------------------------------------------------
The base model sweeps `last_sl` / `last_sh` -- the most recent CONFIRMED
pivot, detected with pivot_len=5 i.e. an 11-bar centred window. That is a
minor pivot. SELECTIVE v1 additionally requires the swept level to be a
SIGNIFICANT prior swing: at/near the extreme of the last
    SIG_SWING_LOOKBACK = 240  M1 bars  (= 4 hours; >> the 11-bar pivot window)
Concretely, for a bull sweep the swept swing LOW must satisfy
    last_sl  <=  min(low, 240) * (1 + SWEEP_EXTREME_TOL_BPS/1e4)
with  SWEEP_EXTREME_TOL_BPS = 10  (the swept low sits within 10 bps of the
4-hour low, i.e. it really is the low that stops rest under). Symmetric for
a bear sweep against max(high, 240).

FILTER 2 -- REAL HIGHER-TIMEFRAME CONTEXT  (reason: one EMA is not "HTF
            context"; a disciplined trader checks the larger trend stack)
-----------------------------------------------------------------------
On top of the existing daily-50-EMA bias, SELECTIVE v1 requires a full
daily MA stack alignment using a longer period:
    HTF_EMA_LONG = 200   (daily 200 EMA, prior-day confirmed value)
Long setups require   close > dailyEMA200   AND   dailyEMA50 > dailyEMA200.
Short setups require   close < dailyEMA200   AND   dailyEMA50 < dailyEMA200.
(The 50/200 relationship is the stated longer-trend condition -- a daily
golden/death-cross regime, not a single line.)

FILTER 3 -- SELECTIVITY CAP  (reason: a discretionary trader does not fire
            on every valid signal; they take the best one and wait)
-----------------------------------------------------------------------
    WEEKLY_TRADE_CAP = 1 entry per rolling 7 calendar days per instrument.
RANKING / "highest-conviction" rule (stated): the displacement candle that
triggered the setup must be the strongest kind -- its body must exceed the
20-bar average body by
    DISP_CONVICTION_MIN = 2.0x   (the base model only requires disp_mult=1.5x).
A TRUE ex-post "largest displacement candle of the week" pick is NOT
look-ahead-free (it needs the whole week visible), so the causal
implementation is: (a) an absolute conviction floor of 2.0x displacement
strength removes the weak setups entirely, and (b) the 1-per-7-days cap
keeps the FIRST setup that clears every other filter. This is the honest
causal approximation of "take only the highest-conviction setup and wait".

FILTER 4 -- LEVEL SIGNIFICANCE  (reason: institutions target KNOWN
            reference points, not an arbitrary recent pivot)
-----------------------------------------------------------------------
The swept level must have genuine prior significance -- it passes if ANY of:
  (a) PRIOR-DAY H/L: within  PDHL_TOL_BPS = 15 bps  of the previous calendar
      day's high or low (classic PDH / PDL liquidity pool);
  (b) DEFENDED LEVEL: touched (bar high/low within  TOUCH_TOL_BPS = 10 bps )
      on at least  TOUCH_MIN_COUNT = 3  distinct prior bars within the last
      TOUCH_LOOKBACK = 480  M1 bars (8 hours) before the sweep;
  (c) ROUND NUMBER: within  ROUND_NUM_TOL_BPS = 10 bps  of a round number,
      step per instrument  XAUUSD 10.0 / EURUSD 0.0050 / SPX500 25.0 /
      BTCUSDT 1000.0 .

=======================================================================
ALL FOUR ARE APPLIED TOGETHER as the single variant this run tests. A
follow-up ablation (section 29.x) could isolate which filter matters most by
toggling one at a time; this run deliberately tests the combined, realistic
version first -- a fair test of disciplined ICT trading, not a strawman.

HONESTY GATES (same standard as section 28): look-ahead guard, real costs,
per-year concentration, out-of-regime test where a real window exists, vs
buy-and-hold. PLUS, per the section-29 brief: explicit TRADE COUNT REDUCTION
vs section 28, and re-confirmation of the account-ruin diagnostic (does any
cell still grind toward <=1% of starting equity, and at what trade number).

TRIALS: 7 a priori cells (the section-28 set, re-run under the new variant).
Cumulative project trial count carried from section 28 (N=1098) -> 1105.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

# ── reuse section 28's engine wholesale ──────────────────────────────────
import run_ict_smc as base
from run_ict_smc import (
    load_dukas_mid, load_crypto_mid, run_one_window, cell_stats, bh_dollars,
    daily_bias_ema, confirmed_pivots, index_slip_bps,
    PIVOT_LEN, DISP_MULT, OB_MAX_BARS, SWEEP_WINDOW, RR_RATIO,
    LONDON_KZ, NY_KZ, FALLBACK_LOOKBACK, OB_SCAN_BARS, MINTICK,
    MIN_STOP_TICKS, MIN_STOP_BPS, START_CAP, BARS_PER_YEAR, CONC_BAR,
    DATA, RESULTS, CELLS,
)
from research.ftmo_engine import RISK_PER_TRADE
from research.metrics import sharpe
from research.dsr import deflated_sharpe, expected_max_sharpe

PRIOR_TRIALS = 1098          # cumulative after section 28
NEW_TRIALS = 7              # same 7 a priori cells, re-run under SELECTIVE v1

# ── SELECTIVE v1 pre-registered thresholds (stated before the run) ───────
SIG_SWING_LOOKBACK    = 240      # bars (4h) -- "significant" swing window
SWEEP_EXTREME_TOL_BPS = 10.0     # swept level within 10 bps of the 240-bar extreme
HTF_EMA_LONG          = 200      # daily 200 EMA, added on top of the 50 EMA bias
WEEKLY_TRADE_CAP      = 1        # entries per rolling 7 calendar days per instrument
WEEKLY_WINDOW_DAYS    = 7
DISP_CONVICTION_MIN   = 2.0      # displacement body >= 2.0x 20-bar avg (base: 1.5x)
PDHL_TOL_BPS          = 15.0     # swept level within 15 bps of prior-day H or L
TOUCH_TOL_BPS         = 10.0     # a "touch" = bar extreme within 10 bps of the level
TOUCH_LOOKBACK        = 480      # bars (8h) searched for prior touches
TOUCH_MIN_COUNT       = 3        # >= 3 distinct prior touches => defended level
ROUND_NUM_TOL_BPS     = 10.0     # swept level within 10 bps of a round number
ROUND_STEP            = {"XAUUSD": 10.0, "EURUSD": 0.0050, "SPX500": 25.0, "BTCUSDT": 1000.0}


# ---------------------------------------------------------------------------
# daily prior-value helpers -- SAME broadcast pattern as run_ict_smc.daily_bias_ema
# ---------------------------------------------------------------------------
def _daily_prior_extreme(m1: pd.DataFrame, how: str) -> np.ndarray:
    """Previous calendar day's high (how='high') or low (how='low'), broadcast
    to every M1 bar of the following day. lookahead_off equivalent."""
    src = m1["mid_high"] if how == "high" else m1["mid_low"]
    daily = src.resample("1D").max() if how == "high" else src.resample("1D").min()
    daily = daily.dropna().shift(1)
    day_key = m1.index.normalize()
    mapped = daily.reindex(day_key.unique()).reindex(day_key)
    mapped.index = m1.index
    return mapped.to_numpy()


def _daily_prior_ema(m1: pd.DataFrame, span: int) -> np.ndarray:
    """Prior-day confirmed daily EMA(span), broadcast to M1 -- identical
    construction to run_ict_smc.daily_bias_ema (which is hard-wired to span=50)."""
    dc = m1["mid_close"].resample("1D").last().dropna()
    ema = dc.ewm(span=span, adjust=False).mean().shift(1)
    day_key = m1.index.normalize()
    mapped = ema.reindex(day_key.unique()).reindex(day_key)
    mapped.index = m1.index
    return mapped.to_numpy()


# ---------------------------------------------------------------------------
# vectorized state -- base fields + the extra series the 4 filters need
# ---------------------------------------------------------------------------
def compute_state_selective(m1: pd.DataFrame, inst: str) -> dict:
    st = base.compute_vectorized_state(m1)          # UNCHANGED base fields

    close = m1["mid_close"]; open_ = m1["mid_open"]; high = m1["mid_high"]; low = m1["mid_low"]

    # -- levels actually swept (base model uses these exact ffilled pivots) --
    ph_confirmed, pl_confirmed = confirmed_pivots(high, low, PIVOT_LEN)
    st["last_sh_arr"] = ph_confirmed.ffill().to_numpy()
    st["last_sl_arr"] = pl_confirmed.ffill().to_numpy()

    # -- FILTER 1: significant-swing extremes over the last N bars --
    st["sig_low"]  = low.rolling(SIG_SWING_LOOKBACK).min().to_numpy()
    st["sig_high"] = high.rolling(SIG_SWING_LOOKBACK).max().to_numpy()

    # -- FILTER 2: daily 50/200 EMA stack (prior-day confirmed) --
    ema50 = daily_bias_ema(m1).to_numpy()                 # byte-identical to base bias
    ema200 = _daily_prior_ema(m1, HTF_EMA_LONG)
    c = close.to_numpy()
    st["htf_long_ok"]  = (c > ema200) & (ema50 > ema200)
    st["htf_short_ok"] = (c < ema200) & (ema50 < ema200)

    # -- FILTER 3: displacement strength ratio (for the conviction floor) --
    body = (close - open_).abs()
    avg_body = body.rolling(20).mean()
    with np.errstate(divide="ignore", invalid="ignore"):
        st["disp_ratio"] = (body / avg_body).to_numpy()

    # -- FILTER 4: prior-day H/L --
    st["pdh"] = _daily_prior_extreme(m1, "high")
    st["pdl"] = _daily_prior_extreme(m1, "low")
    st["round_step"] = ROUND_STEP[inst]
    return st


def _level_significant(lvl: float, i: int, extreme_seg: np.ndarray,
                       pdh: float, pdl: float, step: float) -> bool:
    """FILTER 4: prior-day H/L proximity OR >=3 defended touches OR round number."""
    if not np.isfinite(lvl) or lvl <= 0:
        return False
    tol_pdhl = lvl * PDHL_TOL_BPS / 1e4
    if np.isfinite(pdh) and abs(lvl - pdh) <= tol_pdhl:
        return True
    if np.isfinite(pdl) and abs(lvl - pdl) <= tol_pdhl:
        return True
    nearest_round = round(lvl / step) * step
    if abs(lvl - nearest_round) <= lvl * ROUND_NUM_TOL_BPS / 1e4:
        return True
    if extreme_seg.size:
        touches = int(np.count_nonzero(np.abs(extreme_seg - lvl) <= lvl * TOUCH_TOL_BPS / 1e4))
        if touches >= TOUCH_MIN_COUNT:
            return True
    return False


# ---------------------------------------------------------------------------
# stateful loop -- a COPY of run_ict_smc.run_state_machine with the 4 gates.
# The mechanics (OB scan, aging, FVG array, kill zone, stop/target, min-stop
# floor) are unchanged; only signal ACCEPTANCE is narrowed.
# ---------------------------------------------------------------------------
def run_state_machine_selective(m1: pd.DataFrame, inst: str) -> pd.DataFrame:
    mintick = MINTICK[inst]
    st = compute_state_selective(m1, inst)
    n = len(m1)
    close, open_, high, low = st["close"], st["open_"], st["high"], st["low"]
    bullish_bias, bearish_bias, mkt_str = st["bullish_bias"], st["bearish_bias"], st["mkt_str"]
    bull_sweep, bear_sweep = st["bull_sweep"], st["bear_sweep"]
    bull_disp, bear_disp = st["bull_disp"], st["bear_disp"]
    bull_fvg_new, bear_fvg_new = st["bull_fvg_new"], st["bear_fvg_new"]
    in_kz = st["in_kz"]
    lowest10, highest10 = st["lowest10"], st["highest10"]
    last_sh_arr, last_sl_arr = st["last_sh_arr"], st["last_sl_arr"]
    sig_low, sig_high = st["sig_low"], st["sig_high"]
    htf_long_ok, htf_short_ok = st["htf_long_ok"], st["htf_short_ok"]
    disp_ratio = st["disp_ratio"]
    pdh, pdl = st["pdh"], st["pdl"]
    step = st["round_step"]

    buf = mintick * 5
    tol_ext = SWEEP_EXTREME_TOL_BPS / 1e4

    awaiting_bull = awaiting_bear = False
    bull_sw_bar = bear_sw_bar = -1
    bull_ob_hi = bull_ob_lo = np.nan
    bear_ob_hi = bear_ob_lo = np.nan
    bull_ob_on = bear_ob_on = False
    bull_ob_age = bear_ob_age = 0
    bull_fvg_armed = bear_fvg_armed = False
    bull_fvg_arm_age = bear_fvg_arm_age = 0
    bull_arm_disp = bear_arm_disp = 0.0     # displacement ratio that armed the setup
    bfvg: list[tuple[float, float]] = []
    sfvg: list[tuple[float, float]] = []

    cnt = dict(sweep_bull=0, sweep_bear=0, q_sweep_bull=0, q_sweep_bear=0,
               rej_quality=0, rej_levelsig=0, rej_htf=0, rej_conviction=0, rej_minstop=0)

    raw_long = np.zeros(n, dtype=bool)
    raw_short = np.zeros(n, dtype=bool)
    sl_long_arr = np.full(n, np.nan); tp_long_arr = np.full(n, np.nan)
    sl_short_arr = np.full(n, np.nan); tp_short_arr = np.full(n, np.nan)

    for i in range(2, n):
        # ---- sweep arming, now gated by FILTER 1 (quality) + FILTER 4 (significance) ----
        if bull_sweep[i]:
            cnt["sweep_bull"] += 1
            lvl = last_sl_arr[i]
            q_ok = np.isfinite(sig_low[i]) and np.isfinite(lvl) and lvl <= sig_low[i] * (1 + tol_ext)
            if not q_ok:
                cnt["rej_quality"] += 1
            else:
                seg = low[max(i - TOUCH_LOOKBACK, 0):i]
                if not _level_significant(lvl, i, seg, pdh[i], pdl[i], step):
                    cnt["rej_levelsig"] += 1
                else:
                    cnt["q_sweep_bull"] += 1
                    awaiting_bull = True
                    bull_sw_bar = i
        if bear_sweep[i]:
            cnt["sweep_bear"] += 1
            lvl = last_sh_arr[i]
            q_ok = np.isfinite(sig_high[i]) and np.isfinite(lvl) and lvl >= sig_high[i] * (1 - tol_ext)
            if not q_ok:
                cnt["rej_quality"] += 1
            else:
                seg = high[max(i - TOUCH_LOOKBACK, 0):i]
                if not _level_significant(lvl, i, seg, pdh[i], pdl[i], step):
                    cnt["rej_levelsig"] += 1
                else:
                    cnt["q_sweep_bear"] += 1
                    awaiting_bear = True
                    bear_sw_bar = i

        if awaiting_bull and (i - bull_sw_bar) > SWEEP_WINDOW:
            awaiting_bull = False
        if awaiting_bear and (i - bear_sw_bar) > SWEEP_WINDOW:
            awaiting_bear = False

        # ---- OB creation + FVG arming on sweep->displacement (UNCHANGED mechanics) ----
        if awaiting_bull and bull_disp[i]:
            awaiting_bull = False
            lim = max(i - OB_SCAN_BARS, 0)
            for k in range(i - 1, lim - 1, -1):
                if close[k] < open_[k]:
                    bull_ob_hi, bull_ob_lo = open_[k], close[k]
                    bull_ob_on, bull_ob_age = True, 0
                    break
            bull_fvg_armed, bull_fvg_arm_age = True, 0
            bull_arm_disp = disp_ratio[i] if np.isfinite(disp_ratio[i]) else 0.0

        if awaiting_bear and bear_disp[i]:
            awaiting_bear = False
            lim = max(i - OB_SCAN_BARS, 0)
            for k in range(i - 1, lim - 1, -1):
                if close[k] > open_[k]:
                    bear_ob_hi, bear_ob_lo = close[k], open_[k]
                    bear_ob_on, bear_ob_age = True, 0
                    break
            bear_fvg_armed, bear_fvg_arm_age = True, 0
            bear_arm_disp = disp_ratio[i] if np.isfinite(disp_ratio[i]) else 0.0

        # ---- OB aging / FVG arm aging / new FVG registration (UNCHANGED) ----
        if bull_ob_on:
            bull_ob_age += 1
            if close[i] < bull_ob_lo or bull_ob_age > OB_MAX_BARS:
                bull_ob_on = False
        if bear_ob_on:
            bear_ob_age += 1
            if close[i] > bear_ob_hi or bear_ob_age > OB_MAX_BARS:
                bear_ob_on = False
        if bull_fvg_armed:
            bull_fvg_arm_age += 1
            if bull_fvg_arm_age > OB_MAX_BARS:
                bull_fvg_armed = False
        if bear_fvg_armed:
            bear_fvg_arm_age += 1
            if bear_fvg_arm_age > OB_MAX_BARS:
                bear_fvg_armed = False
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

        # ---- LONG entry: base conditions + FILTER 2 (htf stack) + FILTER 3 (conviction floor) ----
        if bullish_bias[i] and mkt_str[i] == 1 and in_kz[i] and (in_bull_ob or (bull_fvg_armed and in_bull_fvg)):
            if not htf_long_ok[i]:
                cnt["rej_htf"] += 1
            elif bull_arm_disp < DISP_CONVICTION_MIN:
                cnt["rej_conviction"] += 1
            else:
                sl = (bull_ob_lo if bull_ob_on else lowest10[i]) - buf
                if (c - sl) >= min_stop:
                    raw_long[i] = True
                    sl_long_arr[i] = sl
                    tp_long_arr[i] = c + (c - sl) * RR_RATIO
                else:
                    cnt["rej_minstop"] += 1

        if bearish_bias[i] and mkt_str[i] == -1 and in_kz[i] and (in_bear_ob or (bear_fvg_armed and in_bear_fvg)):
            if not htf_short_ok[i]:
                cnt["rej_htf"] += 1
            elif bear_arm_disp < DISP_CONVICTION_MIN:
                cnt["rej_conviction"] += 1
            else:
                sl = (bear_ob_hi if bear_ob_on else highest10[i]) + buf
                if (sl - c) >= min_stop:
                    raw_short[i] = True
                    sl_short_arr[i] = sl
                    tp_short_arr[i] = c - (sl - c) * RR_RATIO
                else:
                    cnt["rej_minstop"] += 1

    out = pd.DataFrame({
        "raw_long": raw_long, "raw_short": raw_short,
        "sl_long": sl_long_arr, "tp_long": tp_long_arr,
        "sl_short": sl_short_arr, "tp_short": tp_short_arr,
    }, index=m1.index)
    out.attrs["cnt"] = cnt
    return out


# ---------------------------------------------------------------------------
# FILTER 3 -- selectivity cap: <= 1 kept signal per rolling 7 calendar days.
# Look-ahead-free: walks signals in time order, keeps a signal only if the
# last KEPT signal was >= 7 days earlier. Applied to the full-file raw series
# BEFORE run_one_window (which then applies the unchanged no_pos gate on top).
# ---------------------------------------------------------------------------
def apply_selectivity_cap(sig: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    idx = sig.index
    rl = sig["raw_long"].to_numpy()
    rs = sig["raw_short"].to_numpy()
    fire = np.flatnonzero(rl | rs)
    keep = np.zeros(len(rl), dtype=bool)
    last_kept = None
    win = pd.Timedelta(days=WEEKLY_WINDOW_DAYS)
    for i in fire:
        t = idx[i]
        if last_kept is None or (t - last_kept) >= win:
            keep[i] = True
            last_kept = t
    sig2 = sig.copy()
    sig2["raw_long"] = rl & keep
    sig2["raw_short"] = rs & keep
    return sig2, int(fire.size), int(keep.sum())


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    W = 122
    print("=" * W)
    print("  ICT-SMC SELECTIVE v1  --  section 28 engine + 4 pre-registered discretionary filters")
    print("  (1) significant-swing sweep  (2) daily 50/200 EMA stack  (3) 1 trade / 7d + 2.0x displacement floor")
    print("  (4) level significance: prior-day H/L | >=3 defended touches | round number")
    print("  Headline: pure compounded dollar return vs buy-and-hold, DIRECTLY comparable to section 28.")
    print("=" * W)

    # section-28 numbers for the side-by-side (loaded, not retyped)
    s28 = pd.read_csv(RESULTS / "ict_smc.csv").set_index("label")

    _file_cache: dict[str, pd.DataFrame] = {}
    _sig_cache: dict[str, pd.DataFrame] = {}
    _cap_info: dict[str, tuple[int, int]] = {}
    results = []
    all_trades = {}
    guard_reports = []

    for cell in CELLS:
        fpath = DATA / cell["file"]
        ck = cell["file"]
        if ck not in _file_cache:
            print(f"\n[{cell['inst']}] loading {cell['file']} ...", flush=True)
            m1 = load_crypto_mid(fpath) if cell["kind"] == "crypto" else load_dukas_mid(fpath)
            print(f"[{cell['inst']}] {len(m1):,} bars, {m1.index.min()} -> {m1.index.max()}", flush=True)
            _file_cache[ck] = m1
        m1 = _file_cache[ck]

        if ck not in _sig_cache:
            print(f"[{cell['inst']}] computing SELECTIVE v1 state machine (slow O(n) pass) ...", flush=True)
            sig = run_state_machine_selective(m1, cell["inst"])
            c = sig.attrs["cnt"]
            print(f"[{cell['inst']}] sweeps seen L/S {c['sweep_bull']:,}/{c['sweep_bear']:,} ; "
                  f"pass quality+significance L/S {c['q_sweep_bull']:,}/{c['q_sweep_bear']:,} "
                  f"(rej: quality {c['rej_quality']:,}, level-sig {c['rej_levelsig']:,})", flush=True)
            print(f"[{cell['inst']}] entry rejections -- htf-stack {c['rej_htf']:,}, "
                  f"conviction<2.0x {c['rej_conviction']:,}, min-stop {c['rej_minstop']:,}", flush=True)
            n_pre_cap = int(sig["raw_long"].sum() + sig["raw_short"].sum())
            sig, n_fire, n_kept = apply_selectivity_cap(sig)
            print(f"[{cell['inst']}] raw signals {n_pre_cap:,} -> after 1-per-7d cap {n_kept:,} "
                  f"(whole file, pre-no_pos)", flush=True)
            _sig_cache[ck] = sig
            _cap_info[ck] = (n_pre_cap, n_kept)
        sig = _sig_cache[ck]

        print(f"  [{cell['label']}] resolving trades (no_pos-gated, section-28 run_one_window) ...", flush=True)
        tr = run_one_window(m1, cell["start"], cell["end"], sig, cell["cost_bps"], cell["slip_fn"],
                            cell["label"], MINTICK[cell["inst"]])
        tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True) if not tr.empty else tr.get("entry_time")
        tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True) if not tr.empty else tr.get("exit_time")

        guard_ok = True
        if not tr.empty:
            for _, row in tr.head(200).iterrows():
                pos = m1.index.searchsorted(row["entry_time"])
                if pos == 0 or abs(m1["mid_open"].iloc[pos] - row["entry_mid"]) > 1e-6:
                    guard_ok = False
                    break
        guard_reports.append((cell["label"], guard_ok, len(tr)))

        stats = cell_stats(tr)
        bh = bh_dollars(m1, cell["start"], cell["end"])
        results.append(dict(inst=cell["inst"], label=cell["label"], regime=cell["regime"],
                            start=cell["start"], end=cell["end"], bh_ending=bh, **stats))
        all_trades[cell["label"]] = tr

    df = pd.DataFrame(results)
    df.to_csv(RESULTS / "ict_smc_selective.csv", index=False)
    if all_trades:
        nonempty = [t.assign(cell=k) for k, t in all_trades.items() if not t.empty]
        if nonempty:
            pd.concat(nonempty, ignore_index=True).to_csv(RESULTS / "ict_smc_selective_trades.csv", index=False)

    # ---- HEADLINE: SELECTIVE v1 vs section-28 vs buy-and-hold ----
    print("\n" + "#" * W)
    print("  HEADLINE -- COMPOUNDED $ RETURN ($100,000 start, 1% risk/trade) :  SELECTIVE v1  vs  section 28  vs  B&H")
    print("#" * W)
    hdr = f"  {'cell':<52} {'SELECTIVE v1 $':>15} {'sel %':>8} {'sec28 $':>13} {'B&H $':>13} {'sel beat B&H?':>13}"
    print(hdr)
    print("  " + "-" * (W - 4))
    for _, r in df.iterrows():
        sel_pct = (r["ending_cap"] / START_CAP - 1) * 100
        s28cap = float(s28.loc[r["label"], "ending_cap"]) if r["label"] in s28.index else float("nan")
        beat = "YES" if (r["bh_ending"] and r["ending_cap"] > r["bh_ending"]) else "no"
        print(f"  {r['label']:<52} ${r['ending_cap']:>13,.0f} {sel_pct:>+7.1f}% "
              f"${s28cap:>11,.0f} ${r['bh_ending']:>11,.0f} {beat:>13}")

    # ---- TRADE COUNT REDUCTION (explicit, per section-29 brief) ----
    print("\n" + "#" * W)
    print("  TRADE COUNT REDUCTION -- how much did selectivity cut volume?  (in-window resolved trades)")
    print("#" * W)
    print(f"  {'cell':<52} {'sec28 n':>9} {'SELECTIVE n':>12} {'reduction':>11}")
    tot28 = totS = 0
    for _, r in df.iterrows():
        n28 = int(s28.loc[r["label"], "n"]) if r["label"] in s28.index else 0
        nS = int(r["n"])
        tot28 += n28; totS += nS
        red = f"-{(1 - nS / n28) * 100:.1f}%" if n28 else "n/a"
        print(f"  {r['label']:<52} {n28:>9,} {nS:>12,} {red:>11}")
    print("  " + "-" * (W - 4))
    red_tot = f"-{(1 - totS / tot28) * 100:.1f}%" if tot28 else "n/a"
    print(f"  {'TOTAL (7 cells)':<52} {tot28:>9,} {totS:>12,} {red_tot:>11}")

    # ---- RUIN DIAGNOSTIC re-confirmation ----
    print("\n" + "#" * W)
    print("  ACCOUNT-RUIN DIAGNOSTIC (section-29 brief: does any cell still grind toward zero, and at what trade #?)")
    print("#" * W)
    print("  Trade # at which equity first fell to <= 1% of the $100,000 start (None = never in this window):")
    any_ruin = False
    for _, r in df.iterrows():
        rt = r["ruin_trade"]
        if rt is not None and pd.notna(rt):
            any_ruin = True
            s = f"trade #{int(rt)} of {int(r['n'])}"
        else:
            s = "never (did not reach 1% of start)"
        print(f"    {r['label']:<52} {s}")
    print(f"\n  Any cell still ruining under SELECTIVE v1: {'YES' if any_ruin else 'NO'}")

    # ---- trade counts / win rates / PF ----
    print("\n" + "#" * W)
    print("  TRADE STATS")
    print("#" * W)
    print(f"  {'cell':<52} {'trades':>7} {'win%':>6} {'grossPF':>8} {'netPF':>7} {'topYr':>6}")
    for _, r in df.iterrows():
        ty = f"{r['top_year']*100:.0f}%" if np.isfinite(r["top_year"]) else "n/a"
        gp = f"{r['gross_pf']:.3f}" if np.isfinite(r["gross_pf"]) else "n/a"
        npf = f"{r['net_pf']:.3f}" if np.isfinite(r["net_pf"]) else "n/a"
        wr = f"{r['win_rate']*100:.0f}%" if np.isfinite(r["win_rate"]) else "n/a"
        print(f"  {r['label']:<52} {int(r['n']):>7} {wr:>6} {gp:>8} {npf:>7} {ty:>6}")

    # ---- plain verdict ----
    print("\n" + "#" * W)
    print("  PLAIN VERDICT PER INSTRUMENT (in-regime window; real dollars)")
    print("#" * W)
    for _, r in df[df["regime"] == "in"].iterrows():
        beat = r["bh_ending"] and r["ending_cap"] > r["bh_ending"]
        s28cap = float(s28.loc[r["label"], "ending_cap"]) if r["label"] in s28.index else float("nan")
        print(f"  {r['inst']}: SELECTIVE v1 {'DID' if beat else 'did NOT'} beat holding {r['inst']} "
              f"(${r['ending_cap']:,.0f} vs ${r['bh_ending']:,.0f}; section 28 was ${s28cap:,.0f}).")

    # ---- SECONDARY: statistical reference ----
    print("\n" + "=" * W)
    print("  SECONDARY -- STATISTICAL REFERENCE (Sharpe, DSR, guard, concentration). Not the headline.")
    print("=" * W)
    srs = df["sharpe"].to_numpy(dtype=float)
    e_max, Np, mu, sd = expected_max_sharpe(srs)
    print(f"  DSR reference pool: N={Np} a priori cells, E[max SR] {e_max:+.3f}")
    print(f"  {'cell':<52} {'Sharpe':>8} {'DSR':>7} {'maxDD':>8} {'guard':>7}")
    for i, r in df.iterrows():
        _, guard_ok, _ = guard_reports[i]
        if r["n"] >= 5 and np.isfinite(r["sharpe"]):
            d = deflated_sharpe(float(r["sharpe"]), srs, n_obs=max(int(r["n_obs"]), 5),
                                ann_factor=BARS_PER_YEAR, skewness=float(r["skew"]),
                                excess_kurtosis=float(r["ekurt"]))["dsr"]
            d = f"{d:.3f}"
        else:
            d = "n/a"
        sr = f"{r['sharpe']:+.2f}" if np.isfinite(r["sharpe"]) else "n/a"
        mdd = f"{r['max_dd']*100:.1f}%" if np.isfinite(r["max_dd"]) else "n/a"
        print(f"  {r['label']:<52} {sr:>8} {d:>7} {mdd:>8} {'PASS' if guard_ok else 'FAIL':>7}")

    any_guard_fail = any(not ok for _, ok, _ in guard_reports)
    print(f"\n  Look-ahead guard: {'*** FAIL ***' if any_guard_fail else 'PASS on every cell'} "
          "(spot-checked first 200 trades/cell: entry_mid == the NEXT bar's open after the signal bar).")

    n_survivors = int(((df["net_pf"] > 1) & (df["sharpe"] > 0) & (df["ending_cap"] > df["bh_ending"].fillna(np.inf))
                       & (df["top_year"].fillna(1.0) <= CONC_BAR)).sum())
    print(f"\n  Cells clearing net PF>1 AND Sharpe>0 AND beats-B&H AND not-year-concentrated: {n_survivors}/{len(df)}")

    cumulative = PRIOR_TRIALS + NEW_TRIALS
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (the section-28 cell set, re-run under SELECTIVE v1).")
    print(f"  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {NEW_TRIALS}).")
    print("  saved -> results/ict_smc_selective.csv, results/ict_smc_selective_trades.csv, "
          "results/ict_smc_selective_run.log")
    print("=" * W)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
