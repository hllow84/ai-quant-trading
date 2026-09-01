#!/usr/bin/env python3
"""
FEASIBILITY CHECK (follow-up) - run before building any new strategy.

Prior script (research/ftmo_btc_intrend_pullback_feasibility.py) used a fixed-
leverage model. This one re-checks the SAME 7 confirmed BTC uptrends under this
project's actual risk convention: 0.5-1% of account equity risked per trade,
with an EXPLICIT stop-loss.

Two stop placements are tested per uptrend:
  (a) TIGHT stop  - conventional stop distances; count how many uptrends it would
      have been hit DURING (stopped out of a trend that kept going).
  (b) WIDE stop   - just beyond that trend's own worst internal pullback; then
      compute the real % of equity at risk when the position is sized so the
      wide stop is a survivable slice of the FTMO 10% budget (only ONE such
      position ever open), NOT 1%.

Everything logged to stdout.
"""
import numpy as np
import pandas as pd

pd.set_option("display.width", 170)
pd.set_option("display.max_columns", 40)
LOG = print

# --------------------------------------------------------------------------
# LOAD  (identical to prior script)
# --------------------------------------------------------------------------
close = (pd.read_csv("data/momentum_crypto_adjclose.csv", parse_dates=["date"])
         .set_index("date")["BTC"].rename("close").sort_index())
h1 = pd.read_csv("data/BTCUSDT_H1_2018_2025_binance.csv", parse_dates=["datetime_utc"])
h1 = h1.set_index("datetime_utc").sort_index()
daily_ohlc = pd.DataFrame({
    "high": h1["mid_high"].resample("1D").max(),
    "low":  h1["mid_low"].resample("1D").min(),
    "close": h1["mid_close"].resample("1D").last(),
}).dropna()
daily_ohlc.index = daily_ohlc.index.tz_localize(None)

df = pd.DataFrame(index=close.index)
df["close"] = close
df["high"] = daily_ohlc["high"].reindex(df.index).fillna(df["close"])
df["low"] = daily_ohlc["low"].reindex(df.index).fillna(df["close"])
df["high"] = df[["high", "close"]].max(axis=1)
df["low"] = df[["low", "close"]].min(axis=1)

SMA_LEN, MIN_DAYS = 100, 60
df["sma"] = df["close"].rolling(SMA_LEN).mean()
df["above"] = df["close"] > df["sma"]
valid = df.dropna(subset=["sma"])


def find_runs(mask, min_len):
    runs, in_run, start_i = [], False, 0
    for i, v in enumerate(mask.values):
        if v and not in_run:
            in_run, start_i = True, i
        elif not v and in_run:
            in_run = False
            if i - start_i >= min_len:
                runs.append((mask.index[start_i], mask.index[i - 1]))
    if in_run and len(mask) - start_i >= min_len:
        runs.append((mask.index[start_i], mask.index[-1]))
    return runs


runs = find_runs(valid["above"], MIN_DAYS)
LOG("=" * 80)
LOG(f"CONFIRMED UPTRENDS (close > SMA100 for >= 60d): {len(runs)} found")
LOG("=" * 80)

FTMO_DAILY = 0.05
FTMO_MAXDD = 0.10
RISK_CONV = 0.01     # 1% per-trade convention (project standard is 0.5-1%)

# --------------------------------------------------------------------------
# Per-trend geometry: entry = close on run's first day (hold-through trade)
# --------------------------------------------------------------------------
rows = []
for s, e in runs:
    seg = df.loc[s:e]
    entry = seg["close"].iloc[0]
    # drawdown measured FROM ENTRY (what a fixed stop below entry actually sees)
    dd_from_entry = (seg["low"].min() / entry) - 1.0
    dd_from_entry_close = (seg["close"].min() / entry) - 1.0
    # trailing peak-to-trough inside the trend (what a TRAILING stop sees)
    peak = seg["high"].cummax()
    p2t = (seg["low"] / peak - 1.0).min()
    worst_1d = seg["close"].pct_change().min()
    trend_ret = seg["close"].iloc[-1] / entry - 1.0
    # date the low-from-entry occurred, and how much trend remained after it
    low_dt = seg["low"].idxmin()
    days_total = len(seg)
    days_after_low = len(seg.loc[low_dt:]) - 1
    move_after_low = seg["close"].iloc[-1] / seg.loc[low_dt, "low"] - 1.0
    rows.append(dict(
        start=s.date(), end=e.date(), days=days_total, entry=round(entry),
        trend_ret=trend_ret, dd_from_entry=dd_from_entry,
        dd_from_entry_close=dd_from_entry_close, p2t_trailing=p2t,
        worst_1d=worst_1d, low_dt=low_dt.date(),
        days_after_low=days_after_low, move_after_low=move_after_low,
    ))
T = pd.DataFrame(rows)

# --- sensitivity: realistic (non-perfect) entry = 20 trading days into the run ---
LAG = 20
lag_rows = []
for s, e in runs:
    seg = df.loc[s:e]
    if len(seg) <= LAG + 5:
        continue
    seg2 = seg.iloc[LAG:]
    entry = seg2["close"].iloc[0]
    lag_rows.append(dict(
        start=s.date(), dd_from_entry=(seg2["low"].min() / entry) - 1.0,
        trend_ret=seg2["close"].iloc[-1] / entry - 1.0,
    ))
L = pd.DataFrame(lag_rows)

show = T.copy()
for c in ["trend_ret", "dd_from_entry", "dd_from_entry_close", "p2t_trailing", "worst_1d", "move_after_low"]:
    show[c] = (show[c] * 100).round(1).astype(str) + "%"
LOG("\nPer-uptrend geometry (entry = close on first day of the run):\n")
LOG(show.to_string(index=False))
LOG(f"""
KEY:
  dd_from_entry       = deepest intraday level reached below the ENTRY price
                        (what a FIXED stop placed below entry is exposed to)
  dd_from_entry_close = same but on a closing basis
  p2t_trailing        = worst peak->trough dip inside the trend
                        (what a TRAILING stop set at that distance is exposed to)
  worst_1d            = worst single-day close-to-close drop inside the trend
  move_after_low      = how much BTC rallied from that low to the trend's end
                        (i.e. what you forfeit by being stopped out there)
""")

# --------------------------------------------------------------------------
# (a) TIGHT STOP  -  conventional distances, count mid-trend stop-outs
# --------------------------------------------------------------------------
LOG("=" * 80)
LOG("(a) TIGHT STOP  -  fixed stop at (entry - d%).  1% equity risk => position")
LOG("    notional = 1% / d  of equity.  Stopped 'during' = intraday low pierced")
LOG("    the stop before the trend ended.")
LOG("=" * 80)

tight_tbl = []
for d in [0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25]:
    hit = (T["dd_from_entry"] <= -d)
    n_hit = int(hit.sum())
    pos_notional = RISK_CONV / d                       # fraction of equity
    # avg trend upside forfeited on the trends where it stopped out
    forfeit = T.loc[hit, "move_after_low"].mean() if n_hit else np.nan
    # if NOT stopped, profit at trend end on the survivors, at this position size
    surv = T.loc[~hit, "trend_ret"]
    prof_surv = (pos_notional * surv).mean() if len(surv) else np.nan
    tight_tbl.append(dict(
        stop_dist=f"{d*100:.0f}%",
        pos_notional_x_equity=f"{pos_notional:.2f}x",
        trends_stopped_out=f"{n_hit}/7",
        trends_survived=f"{7-n_hit}/7",
        avg_upside_forfeited=("n/a" if np.isnan(forfeit) else f"{forfeit*100:.0f}%"),
        avg_acct_profit_if_survived=("n/a" if np.isnan(prof_surv) else f"{prof_surv*100:.1f}%"),
    ))
LOG("\n" + pd.DataFrame(tight_tbl).to_string(index=False))

n2 = int((T['dd_from_entry'] <= -0.02).sum())
n3 = int((T['dd_from_entry'] <= -0.03).sum())
n5 = int((T['dd_from_entry'] <= -0.05).sum())
n10 = int((T['dd_from_entry'] <= -0.10).sum())
# same, for the realistic 20-days-late entry
lg5 = int((L['dd_from_entry'] <= -0.05).sum())
lg10 = int((L['dd_from_entry'] <= -0.10).sum())
lg15 = int((L['dd_from_entry'] <= -0.15).sum())
LOG(f"""
Reading (a) -- fixed stop below entry, PERFECT entry on the trend's first day
(a best case; you cannot time the entry better than this):
  * To keep a 1%-risk position meaningfully sized (>= 0.20x equity) the stop can
    be at most 5% wide. A 2% stop -> {n2}/7 trends stop you out mid-trend; 3% -> {n3}/7;
    5% -> {n5}/7. So a 1%-risk-convention stop shakes you out of most qualifying
    uptrends before they end.
  * The stop only survives all 7 trends once it is >= 15% wide -- at which point
    the 1%-risk position is <= 0.07x equity and the "risk model" is no longer 1%.
  * Only {n10}/7 trends draw >10% below a perfectly-timed entry, which is why a very
    wide fixed-from-entry stop looks survivable -- but that stop also sits ~15%
    below the ORIGINAL entry after the trend has run +100%+, i.e. it is a
    catastrophe stop, not risk management.

Reading (a) -- realistic entry 20 trading days AFTER the trend is confirmed:
  5% stop -> {lg5}/7 stopped; 10% -> {lg10}/7; 15% -> {lg15}/7. Mixed vs the perfect-entry
  case: a later entry skips some early dips but sits higher, so a fixed % stop
  is closer to later lows. Either way a <=10%-wide stop still stops you out of
  multiple qualifying uptrends, and >=15% is not a 1%-risk stop.
""")

# --------------------------------------------------------------------------
# (b) WIDE STOP  -  just beyond each trend's own worst internal pullback
# --------------------------------------------------------------------------
LOG("=" * 80)
LOG("(b) WIDE STOP  -  fixed stop 2% beyond that trend's worst dd_from_entry.")
LOG("    Question: sized so the wide stop is a survivable slice of the FTMO 10%")
LOG("    budget (only ONE such position open), what % of equity is really risked?")
LOG("=" * 80)

BUF = 0.02
# worst dd_from_entry across all 7 trends -> the stop the trade type actually needs
worst_dd_entry = T["dd_from_entry"].min()
worst_p2t = T["p2t_trailing"].min()
worst_1d = T["worst_1d"].min()
wide_dist_entry = abs(worst_dd_entry) + BUF
wide_dist_trail = abs(worst_p2t) + BUF

LOG(f"""
worst dd_from_entry over the 7 uptrends : {worst_dd_entry*100:.1f}%   -> fixed stop must be >= {wide_dist_entry*100:.0f}% wide
worst peak->trough (trailing) over 7    : {worst_p2t*100:.1f}%   -> trailing stop must be >= {wide_dist_trail*100:.0f}% wide
worst single in-trend day               : {worst_1d*100:.1f}%
""")

for stopname, d in [("FIXED stop below entry", wide_dist_entry),
                    ("TRAILING stop below peak", wide_dist_trail)]:
    LOG(f"--- {stopname}: {d*100:.0f}% wide ---")
    # position size if you keep to the 1% convention
    pos_1pct = RISK_CONV / d
    # position size if the DAILY 5% limit is the binding cap (worst 1d = 13.5%)
    pos_daily_cap = FTMO_DAILY / abs(worst_1d)
    # position size if you allow the wide stop to cost HALF the 10% budget
    pos_half_budget = 0.05 / d
    # position size if the wide stop may cost the FULL 10% budget (blows account if +1 tick worse)
    pos_full_budget = FTMO_MAXDD / d
    for tag, pos in [("keep 1% risk convention", pos_1pct),
                     ("size so wide stop = 5% of equity (half the DD budget)", pos_half_budget),
                     ("size so wide stop = 10% of equity (the whole DD budget)", pos_full_budget),
                     ("size capped by the 5% DAILY limit vs worst in-trend day", pos_daily_cap)]:
        real_risk = pos * d
        daily_hit = pos * abs(worst_1d)
        # profit on avg / worst trend at this position size
        prof_avg = pos * T["trend_ret"].mean()
        prof_worst = pos * T["trend_ret"].min()
        surv_10 = "OK" if real_risk < FTMO_MAXDD else "FAILS 10%"
        surv_daily = "OK" if daily_hit < FTMO_DAILY else "FAILS 5%/day"
        LOG(f"  {tag:>58s} | pos {pos:4.2f}x equity | "
            f"risk-if-stopped {real_risk*100:5.1f}% [{surv_10:>9s}] | "
            f"worst-day hit {daily_hit*100:4.1f}% [{surv_daily}] | "
            f"acct P&L avg trend {prof_avg*100:6.1f}%  worst trend {prof_worst*100:5.1f}%")
    LOG("")

# --------------------------------------------------------------------------
# (b2) PER-TREND WIDE STOP  -  stop set beyond THIS trend's own worst dip,
#      then sized so that stop = 5% of equity (half the FTMO 10% DD budget),
#      one position at a time.  Reports the real equity-at-risk per trade.
# --------------------------------------------------------------------------
LOG("=" * 80)
LOG("(b2) PER-TREND: fixed stop 2% beyond THAT trend's own worst dd_from_entry;")
LOG("     trailing stop 2% beyond THAT trend's own worst peak->trough.")
LOG("     Position sized so the stop costs exactly 5% of equity (half the 10%")
LOG("     max-DD budget).  real_risk = 5% by construction; the point is the")
LOG("     position size it forces and the daily-limit check.")
LOG("=" * 80)
pt = []
for r in T.itertuples():
    d_fx = abs(r.dd_from_entry) + BUF
    d_tr = abs(r.p2t_trailing) + BUF
    pos_fx = 0.05 / d_fx
    pos_tr = 0.05 / d_tr
    pt.append(dict(
        trend=f"{r.start}",
        fixed_stop_w=f"{d_fx*100:.0f}%",
        pos_fixed=f"{pos_fx:.2f}x",
        worstday_hit_fixed=f"{pos_fx*abs(r.worst_1d)*100:.1f}%",
        daily_ok_fixed=("OK" if pos_fx*abs(r.worst_1d) < FTMO_DAILY else "FAILS 5%/day"),
        trail_stop_w=f"{d_tr*100:.0f}%",
        pos_trail=f"{pos_tr:.2f}x",
        pnl_fixed_thistrend=f"{pos_fx*r.trend_ret*100:.0f}%",
    ))
LOG("\n" + pd.DataFrame(pt).to_string(index=False))
LOG(f"""
Reading (b2): even sized per-trend (best case: you somehow know each trend's
worst dip in advance), holding the stop beyond the normal dip costs 5% of
equity if hit -- half the entire FTMO drawdown budget on ONE trade. The
fixed-stop position averages ~{(0.05/(T['dd_from_entry'].abs()+BUF)).mean():.2f}x equity; on the deepest-dip trends the
worst single in-trend day then costs {(0.05/(T['dd_from_entry'].abs()+BUF)*T['worst_1d'].abs()).max()*100:.1f}% in a day
(vs the 5% daily limit). 1% risk is nowhere in this picture.
""")

# --------------------------------------------------------------------------
# VERDICT
# --------------------------------------------------------------------------
LOG("=" * 80)
LOG("VERDICT")
LOG("=" * 80)
pos_wide_1pct = RISK_CONV / wide_dist_trail          # trailing stop = the honest trend-follow case
prof_avg_1pct = pos_wide_1pct * T["trend_ret"].mean()
prof_worst_1pct = pos_wide_1pct * T["trend_ret"].min()
pos_wide_1pct_fx = RISK_CONV / wide_dist_entry       # fixed-from-entry case
prof_avg_1pct_fx = pos_wide_1pct_fx * T["trend_ret"].mean()
LOG(f"""
1) "1% risk per trade" + "hold through a multi-month BTC uptrend's normal
   internal pullbacks" are STRUCTURALLY INCOMPATIBLE for this trade type,
   whichever stop style you use:

   TRAILING stop (the normal way to ride a trend while protecting open profit):
     must be ~{wide_dist_trail*100:.0f}% wide to survive the worst in-trend peak->trough dip
     ({abs(worst_p2t)*100:.0f}%). At 1% risk that is a {pos_wide_1pct:.2f}x-equity position. The AVERAGE
     qualifying trend (+{T['trend_ret'].mean()*100:.0f}%) then returns {prof_avg_1pct*100:.1f}% of the account;
     the worst (+{T['trend_ret'].min()*100:.0f}%) returns {prof_worst_1pct*100:.1f}%. Safe, but pointless.
     Any trailing stop tight enough to matter (< ~20%) is hit in most of the 7
     trends -- you are shaken out before the trend ends.

   FIXED stop below entry, even with PERFECT entry timing:
     survives all 7 trends only at >= 15% width -> {pos_wide_1pct_fx:.2f}x-equity position at
     1% risk -> {prof_avg_1pct_fx*100:.1f}% account gain on the average trend. Anything tight
     enough to keep the position meaningful (<= 5% wide) stops you out of
     {int((T['dd_from_entry']<=-0.05).sum())}/7 trends. A realistic (late) entry makes this strictly worse.

2) THE WIDE-STOP VERSION'S IMPLIED REAL RISK.
   To hold through the dips with a position size that is actually worth taking,
   you must drop the 1% convention. Sizing so the wide stop is a survivable
   slice of the 10% FTMO budget:
     - fixed {wide_dist_entry*100:.0f}% stop, position 0.35x equity -> real risk if stopped = 5.0%
       of equity (half the entire 10% max-drawdown budget) on ONE trade.
     - trailing {wide_dist_trail*100:.0f}% stop, position 0.13x equity -> also 5.0% of equity.
   5% per trade is 5x the house convention. It is technically inside the 10%
   line ONLY if it is the sole open position and nothing else goes wrong first.
   Pushing sizing to risk the full 10% on the stop = one stop-out fails the
   account outright, and at that size the worst in-trend single day ({abs(worst_1d)*100:.1f}%)
   already breaches the 5% daily-loss limit.

3) FTMO-SURVIVABILITY OF THE WIDE-STOP VERSION.
   Yes, but only at ~3-5% implied risk per trade, one position at a time, with
   effectively no buffer left for a second loss. And even then the payoff is
   ~15-40% of the account on an average qualifying trend (not per month --
   per whole 2-7 month trend), and low single digits on a weak trend.

BOTTOM LINE: the project's 0.5-1% per-trade risk convention and "ride a
multi-month BTC trend through its normal pullbacks" cannot coexist. A stop
tight enough to honour 1% risk gets hit during most qualifying uptrends; a stop
wide enough to hold through them forces either a trivially small position
(1% risk, ~3-8% account gain per multi-month trend) or an implied real risk of
~5% of equity per trade -- FTMO-survivable only as a lone position with no
margin for error. This confirms the prior script: "a few hundred K in a few
months" is not reachable under FTMO's rules with BTC trend-holding.
""")
LOG("DONE.")
