"""
sneaky_pivot.py — the 15-minute "Sneaky Pivot" (Strategy 2 of the 2026-08-19 brief).

THE STRATEGY AS GIVEN
---------------------
1. Plot four lines from the PREVIOUS day: Range High / Range Low (yesterday's
   extremes) and Swing High / Swing Low (the next major high above the range high
   and the next major low below the range low, found by looking left).
2. Only trade when price reaches one of those four lines. The upper pair is the
   sell zone, the lower pair the buy zone.
3. Three-candle framework on the 15-minute chart:
     C1 (opening candle) plows aggressively into a zone,
     C2 (the "sneaky" candle) reverses — green at support, red at resistance,
     C3 is the trigger — enter the moment price crosses C2's high (long) or
     C2's low (short).
4. Stop below the sneaky candle / low of day (longs), mirrored for shorts.
   Target the opposite side of the range.

MECHANISATION DECISIONS (each one is a real fork; all are stated, none tuned)
----------------------------------------------------------------------------
* SESSION = 09:30-16:00 America/New_York. "The opening 15-minute candle of the
  day" only means anything against a cash-session open, and these index CFDs
  quote nearly around the clock. This also matches the data: the pre-2018 M1
  archive covers ONLY 13:30-20:00 UTC (= the US cash session), so an RTH
  definition is the one that can be tested identically in both regimes.
* RANGE HIGH/LOW = the previous session's RTH extremes, for the same reason.
  A 23-hour "absolute" range is a different strategy, not a refinement of this
  one; it is a follow-up, not a parameter.
* "PLOWS AGGRESSIVELY INTO" the zone is read as: C1 must trade at or through the
  near line of the zone (low <= range_low for a long setup) AND be directional
  into it (a red C1 for a long, green for a short). No magnitude threshold is
  imposed — inventing one would be a tuned parameter the brief does not contain.
* Both zones hit in the same opening candle (an outside C1) is AMBIGUOUS and the
  day is skipped rather than resolved by a made-up tie-break.
* SWING levels are N-bar daily pivots. A pivot at day i is only CONFIRMED at day
  i+N, so a swing line is usable on trade day d only if i+N <= d-1. Skipping that
  lag is the classic way this pattern leaks the future.

Everything is expressed in MID prices; the bid/ask spread is charged explicitly
by research/ftmo_engine.py, so there is no double-count against bid/ask fills.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ET = "America/New_York"

RTH_OPEN_MIN  = 9 * 60 + 30    # 09:30 ET
RTH_CLOSE_MIN = 16 * 60        # 16:00 ET
C1 = (RTH_OPEN_MIN, RTH_OPEN_MIN + 15)        # 09:30-09:45
C2 = (RTH_OPEN_MIN + 15, RTH_OPEN_MIN + 30)   # 09:45-10:00
C3 = (RTH_OPEN_MIN + 30, RTH_OPEN_MIN + 45)   # 10:00-10:15

# A session must be substantially complete to be usable. 390 minutes is a full
# RTH day; days with big holes (half-days, feed gaps in the early archive) would
# otherwise silently produce a truncated range or a phantom force-flat.
MIN_RTH_BARS = 300

# ── a priori parameter grid (structure, not tuning) ───────────────────────────
PIVOT_N = 5           # daily pivot half-width for the swing lines
PIVOT_LOOKBACK = 120  # trading days to look left for the "next major" level
TARGETS  = ("range", "swing")     # "ride back toward the Range High OR Swing High"
STOPS    = ("sneaky", "lod")      # "below the sneaky candle / low of day"
TRIGGERS = ("c3", "session")      # literal C3-only window, vs the rest of the day


def rth_m1(m1_mid: pd.DataFrame) -> pd.DataFrame:
    """M1 mid frame restricted to the RTH session, with ET date/minute columns."""
    et = m1_mid.index.tz_convert(ET)
    minute = et.hour * 60 + et.minute
    mask = (minute >= RTH_OPEN_MIN) & (minute < RTH_CLOSE_MIN)
    out = m1_mid.loc[mask].copy()
    out["et_date"] = et[mask].normalize()
    out["et_min"] = minute[mask]
    return out


def rth_daily(rth: pd.DataFrame) -> pd.DataFrame:
    """Daily RTH bars (the Range High / Range Low source) + a coverage count."""
    g = rth.groupby("et_date")
    daily = pd.DataFrame({
        "open":   g["mid_open"].first(),
        "high":   g["mid_high"].max(),
        "low":    g["mid_low"].min(),
        "close":  g["mid_close"].last(),
        "n_bars": g.size(),
    })
    daily.index.name = "et_date"
    return daily


def _window(rth: pd.DataFrame, lo: int, hi: int) -> pd.DataFrame:
    """OHLC of one intraday minute-window, per ET date."""
    sub = rth.loc[(rth["et_min"] >= lo) & (rth["et_min"] < hi)]
    g = sub.groupby("et_date")
    return pd.DataFrame({
        "open":   g["mid_open"].first(),
        "high":   g["mid_high"].max(),
        "low":    g["mid_low"].min(),
        "close":  g["mid_close"].last(),
        "n_bars": g.size(),
    })


def _pivots(high: np.ndarray, low: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """N-bar fractal pivots. Index i is a pivot high if it is the max of [i-n, i+n]."""
    m = len(high)
    ph = np.zeros(m, dtype=bool)
    pl = np.zeros(m, dtype=bool)
    for i in range(n, m - n):
        if high[i] >= high[i - n:i + n + 1].max():
            ph[i] = True
        if low[i] <= low[i - n:i + n + 1].min():
            pl[i] = True
    return ph, pl


def swing_levels(daily: pd.DataFrame, pivot_n: int = PIVOT_N,
                 lookback: int = PIVOT_LOOKBACK) -> pd.DataFrame:
    """
    Per trade day d: the nearest CONFIRMED pivot high above yesterday's range
    high, and the nearest confirmed pivot low below yesterday's range low.

    A pivot at day i needs n further days to be identified, so it is only
    available from day i+n onward — hence the `i + pivot_n <= d - 1` gate. This
    is the look-ahead trap in every "look left and mark the swing" rule.
    """
    high = daily["high"].to_numpy()
    low = daily["low"].to_numpy()
    ph, pl = _pivots(high, low, pivot_n)
    ph_idx = np.flatnonzero(ph)
    pl_idx = np.flatnonzero(pl)

    sw_hi = np.full(len(daily), np.nan)
    sw_lo = np.full(len(daily), np.nan)
    for d in range(1, len(daily)):
        rng_hi, rng_lo = high[d - 1], low[d - 1]
        lo_bound = max(0, d - 1 - lookback)
        ok_h = ph_idx[(ph_idx >= lo_bound) & (ph_idx + pivot_n <= d - 1)]
        ok_l = pl_idx[(pl_idx >= lo_bound) & (pl_idx + pivot_n <= d - 1)]
        above = high[ok_h][high[ok_h] > rng_hi]
        below = low[ok_l][low[ok_l] < rng_lo]
        if above.size:
            sw_hi[d] = above.min()      # the NEXT major high above, not the highest
        if below.size:
            sw_lo[d] = below.max()      # the NEXT major low below
    return pd.DataFrame({"swing_high": sw_hi, "swing_low": sw_lo}, index=daily.index)


def sneaky_pivot(m1_mid: pd.DataFrame, params: dict) -> list[dict]:
    """
    Generate candidate trades. Each dict is what research/ftmo_engine.simulate_trades
    consumes: entry_time / side / entry_mid / stop / target / session_end.

    params: target in {"range","swing"}, stop in {"sneaky","lod"},
            trigger in {"c3","session"}, plus optional pivot_n / lookback.
    """
    target_mode = params["target"]
    stop_mode = params["stop"]
    trig_mode = params["trigger"]
    pivot_n = int(params.get("pivot_n", PIVOT_N))
    lookback = int(params.get("lookback", PIVOT_LOOKBACK))

    rth = rth_m1(m1_mid)
    daily = rth_daily(rth)
    swings = swing_levels(daily, pivot_n, lookback)

    c1 = _window(rth, *C1)
    c2 = _window(rth, *C2)
    trig_lo, trig_hi = (C3 if trig_mode == "c3" else (C3[0], RTH_CLOSE_MIN))
    win = rth.loc[(rth["et_min"] >= trig_lo) & (rth["et_min"] < trig_hi)]

    # Per-date views of the trigger window and of the whole session (for the
    # force-flat timestamp). Built once; the day loop only indexes into them.
    win_by_day = {d: (v.index, v["mid_high"].to_numpy(), v["mid_low"].to_numpy())
                  for d, v in win.groupby("et_date")}
    last_bar = rth.index.to_series().groupby(rth["et_date"]).last()

    dates = daily.index
    hi = daily["high"].to_numpy()
    lo = daily["low"].to_numpy()
    nb = daily["n_bars"].to_numpy()

    out: list[dict] = []
    for d in range(1, len(dates)):
        day = dates[d]
        if nb[d] < MIN_RTH_BARS or nb[d - 1] < MIN_RTH_BARS:
            continue                       # incomplete session: range or exit unreliable
        if day not in c1.index or day not in c2.index or day not in win_by_day:
            continue

        rng_hi, rng_lo = hi[d - 1], lo[d - 1]
        a, b = c1.loc[day], c2.loc[day]

        hit_low = a["low"] <= rng_lo and a["close"] < a["open"]
        hit_high = a["high"] >= rng_hi and a["close"] > a["open"]
        if hit_low == hit_high:
            continue                       # neither zone, or an ambiguous outside C1

        if hit_low:                        # ---- long setup at the buy zone ----
            if not (b["close"] > b["open"]):
                continue                   # C2 must be the green "sneaky" candle
            side = "long"
            trigger = float(b["high"])
            stop = float(b["low"]) if stop_mode == "sneaky" else float(min(a["low"], b["low"]))
            target = float(rng_hi) if target_mode == "range" else float(swings["swing_high"].iat[d])
        else:                              # ---- short setup at the sell zone ----
            if not (b["close"] < b["open"]):
                continue
            side = "short"
            trigger = float(b["low"])
            stop = float(b["high"]) if stop_mode == "sneaky" else float(max(a["high"], b["high"]))
            target = float(rng_lo) if target_mode == "range" else float(swings["swing_low"].iat[d])

        if not np.isfinite(target):
            continue                       # no confirmed swing level available yet
        if side == "long" and not (stop < trigger < target):
            continue
        if side == "short" and not (target < trigger < stop):
            continue

        idx, w_hi, w_lo = win_by_day[day]
        fired = (w_hi >= trigger) if side == "long" else (w_lo <= trigger)
        if not fired.any():
            continue                       # C2's extreme never crossed — no trade
        k = int(np.argmax(fired))

        out.append({
            "entry_time": idx[k],
            "side": side,
            "entry_mid": trigger,          # stop order at the level; slippage charged separately
            "stop": stop,
            "target": target,
            "session_end": last_bar.loc[day],
            "et_date": day,
        })
    return out
