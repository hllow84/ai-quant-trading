#!/usr/bin/env python3
"""
FEASIBILITY CHECK (run before building any new strategy):

Can a multi-month BTC trend-following hold, sized to plausibly produce a
"few hundred K" outcome, survive FTMO's rules (5% daily loss, 10% max total
drawdown) given BTC's REAL historical *in-trend* pullback behaviour?

Data on disk:
  - data/momentum_crypto_adjclose.csv : BTC daily CLOSE 2017-08-17 .. 2026-08-31 (continuous)
  - data/BTCUSDT_H1_2018_2025_binance.csv : BTC H1 mid OHLC 2018-01-01 .. 2026-08-31
    -> resampled to daily OHLC to get TRUE intraday peak-to-trough dips.

Everything is logged to stdout.
"""
import numpy as np
import pandas as pd

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)

LOG = print

# --------------------------------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------------------------------
LOG("=" * 78)
LOG("STEP 0  -  LOAD BTC DATA")
LOG("=" * 78)

close = (
    pd.read_csv("data/momentum_crypto_adjclose.csv", parse_dates=["date"])
    .set_index("date")["BTC"]
    .rename("close")
    .sort_index()
)
LOG(f"daily close series : {close.index.min().date()} .. {close.index.max().date()}  ({len(close)} days)")

h1 = pd.read_csv("data/BTCUSDT_H1_2018_2025_binance.csv", parse_dates=["datetime_utc"])
h1 = h1.set_index("datetime_utc").sort_index()
daily_ohlc = pd.DataFrame({
    "open":  h1["mid_open"].resample("1D").first(),
    "high":  h1["mid_high"].resample("1D").max(),
    "low":   h1["mid_low"].resample("1D").min(),
    "close": h1["mid_close"].resample("1D").last(),
}).dropna()
daily_ohlc.index = daily_ohlc.index.tz_localize(None)
LOG(f"daily OHLC (from H1): {daily_ohlc.index.min().date()} .. {daily_ohlc.index.max().date()}  ({len(daily_ohlc)} days)")

# Master frame: use daily close everywhere; attach intraday high/low where available.
df = pd.DataFrame(index=close.index)
df["close"] = close
df["high"] = daily_ohlc["high"].reindex(df.index)
df["low"] = daily_ohlc["low"].reindex(df.index)
# before 2018 (no intraday) fall back to close for hi/lo
df["high"] = df["high"].fillna(df["close"])
df["low"] = df["low"].fillna(df["close"])
# guard: hi/lo must bracket close
df["high"] = df[["high", "close"]].max(axis=1)
df["low"] = df[["low", "close"]].min(axis=1)

# --------------------------------------------------------------------------
# 2. STEP 1  -  IDENTIFY SUSTAINED UPTRENDS
# --------------------------------------------------------------------------
LOG("\n" + "=" * 78)
LOG("STEP 1  -  IDENTIFY SUSTAINED UPTRENDS")
LOG("=" * 78)
SMA_LEN = 100
MIN_DAYS = 60  # '2+ months'

df["sma"] = df["close"].rolling(SMA_LEN).mean()
df["above"] = df["close"] > df["sma"]
df["sma_rising"] = df["sma"] > df["sma"].shift(20)   # robustness variant

LOG(f"""
PRIMARY definition of a 'sustained uptrend':
  daily CLOSE > {SMA_LEN}-day SMA on every day, for >= {MIN_DAYS} consecutive trading days.
  The run ends the first day close drops below the {SMA_LEN}-day SMA.
ROBUSTNESS variant additionally requires the {SMA_LEN}-day SMA to be rising
  (SMA today > SMA 20 days ago) on every day of the run.
""")


def find_runs(mask: pd.Series, min_len: int):
    runs = []
    in_run = False
    for i, (dt, v) in enumerate(mask.items()):
        if v and not in_run:
            in_run = True
            start_i = i
        elif not v and in_run:
            in_run = False
            if i - start_i >= min_len:
                runs.append((mask.index[start_i], mask.index[i - 1]))
    if in_run and len(mask) - start_i >= min_len:
        runs.append((mask.index[start_i], mask.index[-1]))
    return runs


valid = df.dropna(subset=["sma"])

for label, mask in [
    ("PRIMARY (close > SMA100)", valid["above"]),
    ("ROBUSTNESS (close > SMA100 AND SMA100 rising)", valid["above"] & valid["sma_rising"]),
]:
    runs = find_runs(mask, MIN_DAYS)
    LOG(f"\n--- {label}:  {len(runs)} qualifying uptrend(s) ---")


# --------------------------------------------------------------------------
# 3. STEP 2  -  WORST IN-TREND PEAK-TO-TROUGH PULLBACK
# --------------------------------------------------------------------------
LOG("\n" + "=" * 78)
LOG("STEP 2  -  LARGEST PEAK-TO-TROUGH PULLBACK *WITHIN* EACH UPTREND")
LOG("=" * 78)


def analyse_run(start, end):
    seg = df.loc[start:end]
    # true intraday path drawdown: running peak of HIGH, worst drop to a later LOW
    peak = seg["high"].cummax()
    dd = seg["low"] / peak - 1.0
    mdd_intraday = dd.min()
    trough_dt = dd.idxmin()
    # locate the peak that preceded that trough
    peak_val = seg.loc[:trough_dt, "high"].max()
    peak_dt = seg.loc[:trough_dt, "high"].idxmax()
    # close-to-close drawdown (equity-style, less severe)
    cpeak = seg["close"].cummax()
    cdd = (seg["close"] / cpeak - 1.0).min()
    # worst single-day close-to-close drop inside the window
    worst_1d = seg["close"].pct_change().min()
    # trend total move (close to close)
    total = seg["close"].iloc[-1] / seg["close"].iloc[0] - 1.0
    # peak-to-end move (best case entry->peak)
    return dict(
        start=start.date(), end=end.date(), days=len(seg),
        trend_ret=total,
        mdd_intraday=mdd_intraday, mdd_close=cdd, worst_1d=worst_1d,
        peak_dt=peak_dt.date(), trough_dt=trough_dt.date(),
    )


runs_primary = find_runs(valid["above"], MIN_DAYS)
rows = [analyse_run(s, e) for s, e in runs_primary]
res = pd.DataFrame(rows)
LOG("\nPRIMARY definition - every qualifying uptrend and its worst internal dip:\n")
show = res.copy()
for c in ["trend_ret", "mdd_intraday", "mdd_close", "worst_1d"]:
    show[c] = (show[c] * 100).round(1).astype(str) + "%"
LOG(show.to_string(index=False))

worst_intraday = res["mdd_intraday"].min()
worst_close = res["mdd_close"].min()
worst_1d_all = res["worst_1d"].min()
avg_intraday = res["mdd_intraday"].mean()
med_intraday = res["mdd_intraday"].median()

LOG(f"""
Across ALL qualifying uptrends (PRIMARY):
  worst  in-trend intraday peak->trough pullback : {worst_intraday*100:6.1f}%   ({res.loc[res.mdd_intraday.idxmin(),'start']} -> {res.loc[res.mdd_intraday.idxmin(),'end']})
  median in-trend intraday peak->trough pullback : {med_intraday*100:6.1f}%
  mean   in-trend intraday peak->trough pullback : {avg_intraday*100:6.1f}%
  worst  in-trend CLOSE-to-close pullback        : {worst_close*100:6.1f}%
  worst  single-day close-to-close drop          : {worst_1d_all*100:6.1f}%
""")

# robustness set
runs_rob = find_runs(valid["above"] & valid["sma_rising"], MIN_DAYS)
res_rob = pd.DataFrame([analyse_run(s, e) for s, e in runs_rob])
LOG("ROBUSTNESS definition - every qualifying uptrend and its worst internal dip:\n")
show_r = res_rob.copy()
for c in ["trend_ret", "mdd_intraday", "mdd_close", "worst_1d"]:
    show_r[c] = (show_r[c] * 100).round(1).astype(str) + "%"
LOG(show_r.to_string(index=False))
LOG(f"""
Across ALL qualifying uptrends (ROBUSTNESS):
  worst  in-trend intraday peak->trough pullback : {res_rob['mdd_intraday'].min()*100:6.1f}%
  median in-trend intraday peak->trough pullback : {res_rob['mdd_intraday'].median()*100:6.1f}%
  mean   in-trend intraday peak->trough pullback : {res_rob['mdd_intraday'].mean()*100:6.1f}%
  worst  single-day close-to-close drop          : {res_rob['worst_1d'].min()*100:6.1f}%
""")

# --------------------------------------------------------------------------
# 4. STEP 3  -  FTMO SIZING SCENARIOS
# --------------------------------------------------------------------------
LOG("=" * 78)
LOG("STEP 3  -  FTMO LEVERAGE / POSITION-SIZING SCENARIOS")
LOG("=" * 78)

FTMO_DAILY = 0.05     # 5% daily loss limit
FTMO_MAXDD = 0.10     # 10% max total drawdown

# 'leverage' L here = BTC notional exposure as a multiple of account equity.
# A BTC move of x% then moves the account by L * x%.
LOG(f"""
Model: hold BTC with notional exposure = L x account equity (L = 'leverage').
  A BTC pullback of p%  -> account equity draw of  L * p%.
  A BTC 1-day drop of d% -> account 1-day loss of   L * d%.
FTMO fails the account if account draw >= {FTMO_MAXDD*100:.0f}% (total) or >= {FTMO_DAILY*100:.0f}% (single day).

'Few hundred K' target taken as +$300,000 profit.
  On $100k account -> need account to grow +300%  -> L * (trend move) = 3.00
  On $200k account -> need account to grow +150%  -> L * (trend move) = 1.50
""")

# use PRIMARY worst-case numbers (most conservative / most honest)
WP = abs(worst_intraday)   # worst in-trend intraday pullback (fraction)
WD = abs(worst_1d_all)     # worst single-day drop (fraction)
MED_P = abs(med_intraday)

L_max_dd = FTMO_MAXDD / WP
L_max_day = FTMO_DAILY / WD
L_survive = min(L_max_dd, L_max_day)

LOG(f"worst in-trend intraday pullback  WP = {WP*100:.1f}%   -> L must be < {L_max_dd:.2f} to stay inside 10% total DD")
LOG(f"worst single-day drop            WD = {WD*100:.1f}%   -> L must be < {L_max_day:.2f} to stay inside 5% daily limit")
LOG(f"==> MAX SURVIVABLE LEVERAGE (every qualifying uptrend's worst dip) : L = {L_survive:.2f}\n")

scenarios = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, round(L_survive, 2)]
scenarios = sorted(set(scenarios))
tbl = []
for L in scenarios:
    dd_hit = L * WP
    day_hit = L * WD
    survives = (dd_hit < FTMO_MAXDD) and (day_hit < FTMO_DAILY)
    tbl.append(dict(
        L=L,
        acct_draw_at_worst_pullback=f"{dd_hit*100:5.1f}%",
        breaches_10pct_total="NO" if dd_hit < FTMO_MAXDD else "YES",
        acct_loss_worst_day=f"{day_hit*100:5.1f}%",
        breaches_5pct_daily="NO" if day_hit < FTMO_DAILY else "YES",
        SURVIVES="YES" if survives else "NO",
    ))
tbl = pd.DataFrame(tbl)
LOG(tbl.to_string(index=False))

# --------------------------------------------------------------------------
# 5. PROFIT AT SURVIVABLE LEVERAGE
# --------------------------------------------------------------------------
LOG("\n" + "=" * 78)
LOG("STEP 3b  -  REALISTIC PROFIT AT THE MAX SURVIVABLE LEVERAGE")
LOG("=" * 78)

# 'typical 2-4 month trend': restrict to runs 60..130 days; report avg & worst move.
res["is_typical"] = res["days"].between(60, 130)
typ = res[res["is_typical"]]
avg_move_all = res["trend_ret"].mean()
worst_move_all = res["trend_ret"].min()
avg_move_typ = typ["trend_ret"].mean() if len(typ) else float("nan")
worst_move_typ = typ["trend_ret"].min() if len(typ) else float("nan")

LOG(f"""
Qualifying-uptrend total close-to-close moves (PRIMARY set, n={len(res)}):
  average move over ALL qualifying trends            : {avg_move_all*100:6.1f}%
  worst   (smallest) qualifying-trend move           : {worst_move_all*100:6.1f}%
  average move over 'typical' 60-130d trends (n={len(typ)}) : {avg_move_typ*100:6.1f}%
  worst   'typical' 60-130d trend move               : {worst_move_typ*100:6.1f}%

NOTE: capturing the FULL trend move requires a perfectly-timed entry at the
trend's start and exit at its end. A realistic hold captures materially less.
""")

for acct in (100_000, 200_000):
    LOG(f"\n---- ${acct:,} FTMO account, held at MAX SURVIVABLE L = {L_survive:.2f} ----")
    for name, mv in [
        ("AVERAGE qualifying trend", avg_move_all),
        ("WORST qualifying trend", worst_move_all),
        ("AVERAGE typical 2-4mo trend", avg_move_typ),
    ]:
        pnl = acct * L_survive * mv
        LOG(f"  {name:32s}: BTC move {mv*100:6.1f}%  ->  P&L = ${pnl:,.0f}  ({L_survive*mv*100:.1f}% of account)")

# what leverage would 'a few hundred K' actually need, and does it survive?
LOG("\n---- Leverage required to net +$300,000, and does it survive? ----")
for acct in (100_000, 200_000):
    for name, mv in [("AVERAGE trend", avg_move_all), ("WORST trend", worst_move_all)]:
        need_L = 300_000 / (acct * mv)
        dd_at = need_L * WP
        LOG(f"  ${acct:,}, {name} (move {mv*100:.0f}%): need L = {need_L:5.2f}  "
            f"-> account draw at worst in-trend dip = {dd_at*100:5.0f}%  "
            f"({'SURVIVES' if dd_at < FTMO_MAXDD else 'BLOWS THE 10% LIMIT'})")

LOG("\nDONE.")
