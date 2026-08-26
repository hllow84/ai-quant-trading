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


def rth_m1(m1_mid: pd.DataFrame) -> pd.DataFrame:
    """M1 mid frame restricted to the RTH cash session, with ET date/minute columns.

    m1_mid.index MUST be tz-aware UTC. tz_convert applies the IANA DST history
    per timestamp, so 09:30 ET is located correctly in both halves of the year.
    """
    et = m1_mid.index.tz_convert(ET)
    minute = et.hour * 60 + et.minute
    mask = (minute >= RTH_OPEN_MIN) & (minute < RTH_CLOSE_MIN)
    out = m1_mid.loc[mask].copy()
    out["et_date"] = et[mask].normalize()
    out["et_min"] = minute[mask]
    return out


def opening_ranges(rth: pd.DataFrame, or_minutes: int) -> pd.DataFrame:
    """Per ET session: the opening range high/low and its bar coverage."""
    lo, hi = RTH_OPEN_MIN, RTH_OPEN_MIN + or_minutes
    sub = rth.loc[(rth["et_min"] >= lo) & (rth["et_min"] < hi)]
    g = sub.groupby("et_date")
    return pd.DataFrame({
        "or_high": g["mid_high"].max(),
        "or_low": g["mid_low"].min(),
        "or_open": g["mid_open"].first(),
        "or_bars": g.size(),
    })


def orb(m1_mid: pd.DataFrame, params: dict) -> list[dict]:
    """
    Generate ORB candidate trades. Each dict is what
    research/ftmo_engine.simulate_trades consumes.

    params: or_minutes in {15, 30}, target in {"1R", "2R", "close"}.
    """
    or_minutes = int(params["or_minutes"])
    target_mode = str(params["target"])

    rth = rth_m1(m1_mid)
    if rth.empty:
        return []

    sess_bars = rth.groupby("et_date").size()
    ors = opening_ranges(rth, or_minutes)

    # Entry scan window: strictly AFTER the opening range is complete.
    entry_start = RTH_OPEN_MIN + or_minutes
    win = rth.loc[rth["et_min"] >= entry_start]
    win_by_day = {d: (v.index, v["mid_high"].to_numpy(), v["mid_low"].to_numpy())
                  for d, v in win.groupby("et_date")}
    last_bar = rth.index.to_series().groupby(rth["et_date"]).last()

    out: list[dict] = []
    for day, r in ors.iterrows():
        if sess_bars.get(day, 0) < MIN_RTH_BARS:
            continue                                   # truncated session
        if r["or_bars"] < MIN_OR_COVERAGE * or_minutes:
            continue                                   # opening range has holes
        or_hi, or_lo = float(r["or_high"]), float(r["or_low"])
        rng = or_hi - or_lo
        if not np.isfinite(rng) or rng <= 0:
            continue                                   # degenerate range
        if day not in win_by_day:
            continue

        idx, w_hi, w_lo = win_by_day[day]
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
            side, k, entry, stop = "long", i_up, or_hi, or_lo
        else:
            side, k, entry, stop = "short", i_dn, or_lo, or_hi

        if target_mode == "close":
            r_mult = NO_TARGET_R
        else:
            r_mult = float(target_mode.rstrip("R"))
        target = entry + r_mult * rng if side == "long" else entry - r_mult * rng

        out.append({
            "entry_time": idx[k],
            "side": side,
            "entry_mid": entry,        # stop order at the OR level; slippage charged separately
            "stop": stop,
            "target": target,
            "session_end": last_bar.loc[day],
            "et_date": day,
            "or_range": rng,
        })
    return out
