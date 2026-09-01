"""
orb.py — the OPENING RANGE BREAKOUT, in its real, evidence-backed form:
anchored to the US CASH OPEN (09:30 America/New_York).

WHY THIS IS NOT THE BREAKOUT FAMILY ALREADY KILLED
---------------------------------------------------
STATE_OF_PLAY section 1 killed a generic "breakout" family whose range was an
arbitrary rolling window on an arbitrary timeframe, and a "London opening range"
gold variant (2026-07-18, strategy B) anchored to 07:00-08:00 UTC. Neither
isolates the US cash open. The ORB claim is specifically about 09:30 ET on US
equity indices: the auction that opens the cash session concentrates overnight
information into a short, high-volume window, and the first extension beyond
that window's range is claimed to persist. That is a different, testable
proposition, and it has never been run in this repo.

TIMEZONE — the thing that silently breaks this strategy
--------------------------------------------------------
09:30 ET is 13:30 UTC under EDT and 14:30 UTC under EST. A fixed UTC offset
misplaces the opening range for roughly half of every year — in winter it would
build the "opening range" from 08:30-08:45 ET (pre-market) and in summer from
10:30-10:45 ET (an hour into the session). Both are a different strategy.
Every bar here is converted with tz_convert("America/New_York"), which applies
the full IANA DST history per timestamp. scripts/verify_orb_sessions.py is a
hard gate that proves it from the data: the 09:30 ET bar occurs at 13:30 UTC and
14:30 UTC ONLY, and the offset flips on the correct US DST dates.

THE STRATEGY — every default stated, nothing tuned
---------------------------------------------------
* OPENING RANGE = high/low of the first N minutes after 09:30 ET, mid prices.
  N in {15, 30}. Both are canonical values; neither was chosen by result.
* ENTRY = a stop order at the OR high (long) or the OR low (short), armed only
  from 09:30+N onward — the OR must be COMPLETE before any entry can exist.
  The first break of the day wins; the opposite side is then cancelled.
  ONE position per day per instrument, no re-entry, no reversal.
* STOP = the opposite side of the opening range. 1R = the OR range itself.
  (The brief allowed "a stated fraction of it"; the full opposite side is the
  unfitted default and the only one used, so no fraction is a free parameter.)
* TARGET = 1R, 2R, or NONE ("close": hold to the cash close with the stop live).
* FORCE FLAT at the last RTH bar of the session (16:00 ET). No overnight holds.
* A session is skipped if its opening range is incomplete, degenerate (zero
  range), or the session itself is materially short — see the MIN_ constants.

LOOK-AHEAD DISCIPLINE
---------------------
The OR is built from bars with ET minute in [09:30, 09:30+N). The entry scan
starts at ET minute >= 09:30+N. No bar is in both sets, so the breakout can
never consult the range that defines it. Trade resolution then runs forward from
the breakout bar itself, with same-bar stop+target ties resolved as STOP (the
engine's conservative convention), so the breakout bar's own future is never
used to pick the better of two outcomes.

Everything is expressed in MID prices; the bid/ask spread is charged explicitly
by research/ftmo_engine.py, so there is no double-count against bid/ask fills.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ET = "America/New_York"

RTH_OPEN_MIN = 9 * 60 + 30     # 09:30 ET — the US cash open
RTH_CLOSE_MIN = 16 * 60        # 16:00 ET — the cash close

# A session must be substantially complete: a truncated day would give a phantom
# force-flat time and a range built from a partial auction.
MIN_RTH_BARS = 300             # of 390 in a full session
MIN_OR_COVERAGE = 0.85         # fraction of the OR minutes that must be present

# ── a priori grid (structure, not tuning) ────────────────────────────────────
OR_MINUTES = (15, 30)                 # the two canonical opening ranges
TARGETS = ("1R", "2R", "close")       # fixed R, or hold to the bell with the stop live
NO_TARGET_R = 1000.0                  # sentinel for "close": unreachable by construction

# ── AUDIT 4 — the MODERATE, cost-sensible stop ───────────────────────────────
# The OR-range stop (above) was never chosen for its cost properties: 1R is
# "whatever the opening range happened to be" that day, which measured out to
# 32-60 bps of price in regime and 23-41 bps out of regime (see STATE_OF_PLAY
# section 10), giving cost_R 5.7-9.9% in regime purely as a side effect of
# geometry, not by design. MODERATE_STOP_BPS is a DELIBERATE, cost-informed
# choice instead: round-turn cost per ORB trade (real spread + 0.35 bps
# commission + 2x1.00 bps opening-hour slippage) measures ~2.9-3.6 bps of price
# across all four in-regime cells (results/orb_scored.csv: cost_R_mean * risk_med_bps).
# Solving cost_R = cost_bps / R_bps for the middle of the requested 10-15% band
# (12.5%) at the measured ~3.3 bps average cost gives R_bps = 3.3/0.125 = 26.4,
# rounded to a stated 25 bps. This is a FIXED price-relative stop (0.25% of the
# entry price), not a function of the day's opening range.
MODERATE_STOP_BPS = 25.0


def rth_m1(m1_mid: pd.DataFrame, session_tz: str = ET,
           open_min: int = RTH_OPEN_MIN, close_min: int = RTH_CLOSE_MIN) -> pd.DataFrame:
    """M1 mid frame restricted to the trading session, with session date/minute columns.

    m1_mid.index MUST be tz-aware UTC and OPEN-stamped (bar label = start of the
    minute), which is the Dukascopy convention this module was written against.
    tz_convert applies the IANA DST history per timestamp, so 09:30 ET is located
    correctly in both halves of the year.

    session_tz / open_min / close_min generalise the US-cash-open default to any
    session anchored in any timezone. For a 24/7 instrument (crypto) the caller
    passes session_tz="UTC", open_min=0, close_min=1440 — the whole UTC calendar
    day is one "session", its "open" is 00:00 UTC (the repo's existing crypto
    daily boundary, run_sweep_crypto.py) and its "close" is the 23:59 UTC bar.
    The output columns keep the names et_date / et_min for backward compatibility
    regardless of the actual timezone used.
    """
    et = m1_mid.index.tz_convert(session_tz)
    minute = et.hour * 60 + et.minute
    mask = (minute >= open_min) & (minute < close_min)
    out = m1_mid.loc[mask].copy()
    out["et_date"] = et[mask].normalize()
    out["et_min"] = minute[mask]
    return out


def wilder_dmi_direction(rth: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    CAUSAL daily +DI/-DI direction, +1 (+DI > -DI) / -1 (-DI > +DI) / 0 / NaN,
    indexed by et_date. Standard Wilder 14-period DMI computed on the SESSION
    bars (one bar per et_date: high = max intra-session mid_high, low = min
    mid_low, close = last mid_close), then .shift(1) so session D is gated only
    by directional movement completed strictly BEFORE session D. This is the
    daily "trend context" reading of "+DI > -DI at the moment of breakout" — a
    14-minute intrabar DMI is noise, and using the breakout session's own bar
    would be look-ahead. Same causal pattern as daily_trend_direction().
    """
    g = rth.groupby("et_date")
    high = g["mid_high"].max()
    low = g["mid_low"].min()
    close = g["mid_close"].last()
    idx = close.index
    up_move = high.diff()
    dn_move = -low.diff()
    plus_dm = np.where((up_move > dn_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((dn_move > up_move) & (dn_move > 0), dn_move, 0.0)
    prev_close = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(),
                    (low - prev_close).abs()], axis=1).max(axis=1)
    alpha = 1.0 / length            # Wilder RMA
    atr = tr.ewm(alpha=alpha, adjust=False, min_periods=length).mean()
    plus_di = 100.0 * pd.Series(plus_dm, index=idx).ewm(
        alpha=alpha, adjust=False, min_periods=length).mean() / atr
    minus_di = 100.0 * pd.Series(minus_dm, index=idx).ewm(
        alpha=alpha, adjust=False, min_periods=length).mean() / atr
    direction = np.sign(plus_di - minus_di)
    return direction.shift(1)


TREND_SMA_LENGTH = 50   # sessions (~10 weeks), the canonical "intermediate trend" length


def daily_trend_direction(rth: pd.DataFrame, length: int = TREND_SMA_LENGTH) -> pd.Series:
    """
    CAUSAL daily trend direction, +1 (uptrend) / -1 (downtrend) / NaN (insufficient
    warmup), indexed by et_date.

    Defined entirely from the CASH-SESSION close (the RTH frame's last mid_close
    per ET date), not the 23-hour CFD close, so the same definition is available
    on BOTH windows — the in-regime file is 23-hour but the pre-2018 file is
    RTH-only (13:00-21:00 UTC), and using the cash close for both avoids the
    window-mismatch caveat run_orb_pre2018.py already documents for buy-and-hold.

    Causality: the value assigned to session D is sign(close_{D-1} - SMA_{length}(
    closes through D-1)) — an explicit .shift(1) on the (close, SMA) pair BEFORE
    comparison, so nothing about session D's own price (including its cash close)
    ever enters the trend value used to gate session D's trade. This is checked,
    not merely asserted, by the look-ahead guard in the runner (correlation of the
    gated position series with same/next-bar returns) plus a direct index-alignment
    assertion in scripts/run_orb_trend.py.
    """
    sess_close = rth.groupby("et_date")["mid_close"].last().sort_index()
    sma = sess_close.rolling(length, min_periods=length).mean()
    direction = np.sign(sess_close - sma)
    return direction.shift(1)


def opening_ranges(rth: pd.DataFrame, or_minutes: int,
                   open_min: int = RTH_OPEN_MIN) -> pd.DataFrame:
    """Per session: the opening range high/low and its bar coverage."""
    lo, hi = open_min, open_min + or_minutes
    sub = rth.loc[(rth["et_min"] >= lo) & (rth["et_min"] < hi)]
    g = sub.groupby("et_date")
    return pd.DataFrame({
        "or_high": g["mid_high"].max(),
        "or_low": g["mid_low"].min(),
        "or_open": g["mid_open"].first(),
        "or_bars": g.size(),
    })


def orb(m1_mid: pd.DataFrame, params: dict, trend_dir: pd.Series | None = None,
        di_dir: pd.Series | None = None, retest: bool = False,
        retest_tol_frac: float = 0.10,
        session_tz: str = ET, open_min: int = RTH_OPEN_MIN,
        close_min: int = RTH_CLOSE_MIN, min_sess_bars: int = MIN_RTH_BARS) -> list[dict]:
    """
    Generate ORB candidate trades. Each dict is what
    research/ftmo_engine.simulate_trades consumes.

    params: or_minutes in {15, 30}, target in {"1R", "2R", "close"},
            stop_mode in {"or_range" (default), "moderate"} — see MODERATE_STOP_BPS.

    trend_dir: OPTIONAL daily SMA direction gate (see daily_trend_direction) — the
        §10.4 filter, kept for reproducibility. Default None = no gate.

    di_dir: OPTIONAL — output of wilder_dmi_direction(), indexed by session date.
        FILTER 5 (directional movement). A long break is taken only if
        di_dir[day] == +1 (+DI > -DI on the prior session), a short only if == -1.
        NaN (warmup) or a mismatched sign SKIPS the day — no trade, never a
        reversed one. Default None = no gate (reproduces §10 byte-identically).

    retest: OPTIONAL — FILTER 2 (retest entry). When True, a raw break does NOT
        enter immediately. After the first break of the day:
          * retest tolerance = the price must return to within
            retest_tol_frac (default 0.10) * the OR width of the broken level
            (long: some later bar's low <= or_high + 0.10*range;
             short: some later bar's high >= or_low - 0.10*range);
          * retest window = the REMAINDER OF THE SAME SESSION only — no retest by
            the session close means NO TRADE that day;
          * cancel = if any bar from the breakout bar onward CLOSES back through
            the broken level (long: close < or_high; short: close > or_low)
            BEFORE the retest is achieved, the setup is CANCELLED for the day —
            there is NO fallback to an immediate entry, no trade at all.
        Entry on a successful retest is a limit fill at the broken OR level, so
        the stop (opposite OR side) and 1R are IDENTICAL to the unfiltered ORB —
        only trade SELECTION and entry TIMING differ, which keeps the comparison
        against the baseline clean. Default False = immediate break entry.

    session_tz / open_min / close_min / min_sess_bars generalise the US cash
    session (America/New_York, 09:30, 16:00, 300 bars) to any session; crypto
    passes ("UTC", 0, 1440, e.g. 1200) so the "session" is the whole UTC day,
    its open is 00:00 UTC and its close the 23:59 UTC bar.
    """
    or_minutes = int(params["or_minutes"])
    target_mode = str(params["target"])
    stop_mode = str(params.get("stop_mode", "or_range"))
    tol_frac = float(retest_tol_frac)

    rth = rth_m1(m1_mid, session_tz, open_min, close_min)
    if rth.empty:
        return []

    sess_bars = rth.groupby("et_date").size()
    ors = opening_ranges(rth, or_minutes, open_min)

    # Entry scan window: strictly AFTER the opening range is complete.
    entry_start = open_min + or_minutes
    win = rth.loc[rth["et_min"] >= entry_start]
    win_by_day = {d: (v.index, v["mid_high"].to_numpy(), v["mid_low"].to_numpy(),
                      v["mid_close"].to_numpy())
                  for d, v in win.groupby("et_date")}
    last_bar = rth.index.to_series().groupby(rth["et_date"]).last()

    out: list[dict] = []
    for day, r in ors.iterrows():
        if sess_bars.get(day, 0) < min_sess_bars:
            continue                                   # truncated session
        if r["or_bars"] < MIN_OR_COVERAGE * or_minutes:
            continue                                   # opening range has holes
        or_hi, or_lo = float(r["or_high"]), float(r["or_low"])
        rng = or_hi - or_lo
        if not np.isfinite(rng) or rng <= 0:
            continue                                   # degenerate range
        if day not in win_by_day:
            continue

        idx, w_hi, w_lo, w_cl = win_by_day[day]
        up = w_hi >= or_hi
        dn = w_lo <= or_lo
        i_up = int(np.argmax(up)) if up.any() else -1
        i_dn = int(np.argmax(dn)) if dn.any() else -1
        if i_up == -1 and i_dn == -1:
            continue                                   # inside day: no break, no trade

        # First break of the day wins. A bar that breaks BOTH sides in the same
        # minute is ambiguous at M1 resolution and the day is skipped rather than
        # resolved by a made-up tie-break (same convention as sneaky_pivot).
        if i_up != -1 and i_dn != -1 and i_up == i_dn:
            continue
        if i_dn == -1 or (i_up != -1 and i_up < i_dn):
            side, k, entry = "long", i_up, or_hi
        else:
            side, k, entry = "short", i_dn, or_lo

        # TREND FILTER (optional, §10.4): causal daily SMA direction.
        if trend_dir is not None:
            td = trend_dir.get(day, np.nan)
            if not np.isfinite(td):
                continue
            if (side == "long" and td <= 0) or (side == "short" and td >= 0):
                continue

        # FILTER 5 — DIRECTIONAL MOVEMENT (optional): causal prior-session DMI.
        if di_dir is not None:
            dv = di_dir.get(day, np.nan)
            if not np.isfinite(dv):
                continue
            if (side == "long" and dv <= 0) or (side == "short" and dv >= 0):
                continue

        # FILTER 2 — RETEST (optional): walk forward from the breakout bar.
        entry_i = k
        if retest:
            tol = tol_frac * rng
            hit = -1
            for j in range(k, len(idx)):
                c = w_cl[j]
                if side == "long":
                    if c < or_hi:                      # closed back through the level
                        break                          # -> setup CANCELLED, no trade
                    if j > k and w_lo[j] <= or_hi + tol:
                        hit = j
                        break
                else:
                    if c > or_lo:
                        break
                    if j > k and w_hi[j] >= or_lo - tol:
                        hit = j
                        break
            if hit == -1:
                continue                               # no valid retest before close
            entry_i = hit

        # ENTRY (the OR extreme) and the breakout DETECTION above are unchanged
        # by stop_mode — only the stop distance, and therefore 1R, differs.
        if stop_mode == "moderate":
            r_price = MODERATE_STOP_BPS / 1e4 * entry
        else:
            r_price = rng
        stop = entry - r_price if side == "long" else entry + r_price

        if target_mode == "close":
            r_mult = NO_TARGET_R
        else:
            r_mult = float(target_mode.rstrip("R"))
        target = entry + r_mult * r_price if side == "long" else entry - r_mult * r_price

        out.append({
            "entry_time": idx[entry_i],
            "side": side,
            "entry_mid": entry,        # limit/stop order at the OR level; slippage charged separately
            "stop": stop,
            "target": target,
            "session_end": last_bar.loc[day],
            "et_date": day,
            "or_range": rng,
        })
    return out
