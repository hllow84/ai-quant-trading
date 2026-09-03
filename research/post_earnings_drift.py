#!/usr/bin/env python3
"""
post_earnings_drift.py -- POST-EARNINGS-ANNOUNCEMENT DRIFT (PEAD), the
Ball & Brown (1968) / Bernard & Thomas (1989) anomaly. Event-driven
(news-triggered), mechanistically different from every price-pattern,
portfolio-rotation, positioning and options structure tested so far in this
project (STATE_OF_PLAY sec 1).

=====================================================================
STEP 1 -- DATA, STATED HONESTLY  (the likely weakest link)
=====================================================================
SOURCE: yfinance `Ticker.get_earnings_dates(limit=100)` -- returns, per name,
up to the last ~100 quarterly earnings events with columns:
    EPS Estimate (analyst consensus), Reported EPS, Surprise(%)
indexed by a TIMEZONE-AWARE ANNOUNCEMENT TIMESTAMP (date + time in
America/New_York), NOT the fiscal-quarter end.

COVERAGE FOUND (probed this session, ~55 large-cap US names):
  - ~99 events per name back to ~2002 (Yahoo hard-caps the pull at 100 rows);
    ~83 events per name from 2006 onward.
  - EPS Estimate + Reported EPS both present for ~99% of events (2006+).
  - The announcement TIMESTAMP carries real before-open / after-close
    information: across ~3,900 probed events the hour-of-day clusters hard at
    06:00-08:00 ET (before open, ~60%) and 16:00 ET (after close, ~35%);
    only ~1% land 09:30-16:00 (treated conservatively -- see below).

QUALITY LIMITATIONS -- STATED, NOT WORKED AROUND:
  1. **Point-in-time integrity of the ESTIMATE is UNVERIFIABLE with free
     data.** The "EPS Estimate" is Yahoo's CURRENT record of consensus. For
     it to be look-ahead-clean it must be the PRE-announcement consensus, not
     a later revision/restatement. Yahoo's provider generally stores the
     final pre-report consensus, but this cannot be confirmed free. This is
     the single load-bearing trust assumption. A restated estimate would tend
     to make surprises look MORE predictive than they were in real time
     (post-hoc alignment), biasing toward a FALSE POSITIVE -- so a KILL here
     is robust, a positive result would need paid I/B/E/S PIT data to trust.
  2. **Reported EPS may be restated** (adjusted-vs-GAAP reclassification over
     time). Same unverifiable-free caveat, smaller effect.
  3. **Survivorship**: the universe is a fixed set of names that ARE large-cap
     and solvent TODAY. Firms that were S&P 100 in 2006 and blew up (Lehman,
     Bear, AIG, WaMu, GM, Kodak...) or were acquired are absent. This
     inflates the LONG (beat) leg's realised drift; the short (miss) leg less
     so. Stated, direction-of-bias noted, not corrected (no free historical
     index membership).
  4. 100-row Yahoo cap truncates the deepest history for some names; 2006-2026
     is available for essentially all, enough for a 2008-2009 sub-window.
  5. Daily closes only (no intraday) -- fine for a 20/60-day drift horizon.

VERDICT ON DATA QUALITY: USABLE for a genuine test (99% field coverage, 20yr
depth, real BMO/AMC timestamps). NOT a data-quality dead end. But the
result's trustworthiness is capped by limitation (1): treat a positive as
provisional-pending-PIT-data, a kill as solid.

=====================================================================
LOOK-AHEAD HANDLING -- verified explicitly, not asserted
=====================================================================
Entry = the CLOSE of the first trading day whose OPEN is STRICTLY AFTER the
announcement timestamp.
  - after-close announce (e.g. 16:00 on day D)  -> first open after = D+1 open -> enter D+1 close
  - before-open announce (e.g. 07:00 on day D)  -> first open after = D  open  -> enter D   close
  - during-hours announce (rare, ~1%)           -> first open after = D+1 open -> enter D+1 close
This SKIPS the announcement jump entirely (the gap and the first session that
contains the news) and captures only the DRIFT thereafter -- the conservative
convention of the PEAD literature. `verify_no_lookahead()` asserts, for every
event used, that the entry day's timestamp is strictly greater than the
announcement timestamp; reported as PASS/FAIL with the min gap.
SUE's rolling standard deviation is computed on TRAILING surprises only and
shifted one quarter, so an event's SUE never uses its own surprise in its
own scaling.

=====================================================================
STEP 2 -- STRATEGY  (every parameter stated, a priori)
=====================================================================
surprise metric : SUE = (Reported EPS - EPS Estimate) / rolling_std(Reported
                  - Estimate over the trailing 8 quarters, min 4), std
                  shifted 1 quarter (causal). SUE is the Foster-Olsen-Shevlin
                  standard; more robust than raw Surprise(%) when the estimate
                  is near zero. Raw Surprise(%) thresholds are run separately
                  as a robustness diagnostic.
threshold       : |SUE| > 1.0, 1.5, 2.0  (three levels tested)
direction       : SUE > +thr -> LONG the stock; SUE < -thr -> SHORT the stock
shorts          : MODELLED. These are S&P-100 names -> borrow is general
                  collateral, cheap and available. Short carry = 2.0%/yr
                  (0.5% stated borrow fee + ~1.5% blended dividend owed),
                  pro-rated daily while short. A long-only variant is also
                  reported (the cleaner PEAD test).
horizon         : hold H = 20 and 60 trading days (the two standard PEAD
                  windows). No stop, no profit-take -- the position is
                  defined by the event and held to horizon.
portfolio       : daily-rebalanced EQUAL WEIGHT across all currently-active
                  events (gross scaled to 1.0). Portfolio daily return = mean
                  of (sign x stock daily return) over active positions.
costs           : 5 bps/side (3 spread + 1 commission + 1 slippage) = 10 bps
                  round-turn per position, charged 5 bps on its entry day and
                  5 bps on its exit day, divided across the active book.
                  Plus short carry (above) on short positions, daily.

GRID: 3 thresholds x 2 horizons x {long/short, long-only} = 12 a priori cells.
Raw-Surprise(%) variant = diagnostic (not counted). Cumulative project trial
count 1073 -> 1085.

HONESTY GATES: look-ahead guard (explicit, above), real costs (above), DSR
REFERENCE ONLY (pool = the 12 cells), per-year concentration, an
out-of-regime split (2006-2015 IS / 2016-2026 OOS) with 2008-2009 called out
explicitly, and vs buy-and-hold the same universe equal-weighted.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import yfinance as yf

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

EARN_CSV = DATA / "pead_earnings.csv"
PX_CSV = DATA / "pead_prices.csv"

UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BLK",
    "XOM", "CVX", "COP",
    "JNJ", "PFE", "MRK", "LLY", "ABT", "TMO", "UNH", "BMY", "AMGN", "GILD", "MDT",
    "PG", "KO", "PEP", "WMT", "COST", "HD", "LOW", "MCD", "SBUX", "NKE", "TGT",
    "DIS", "CMCSA", "VZ", "T", "NFLX",
    "CSCO", "INTC", "ORCL", "IBM", "QCOM", "TXN", "ADBE", "CRM", "ACN", "AMD",
    "BA", "CAT", "GE", "HON", "MMM", "UNP", "LMT", "RTX", "DE",
]
START = pd.Timestamp("2006-01-01", tz="America/New_York")
END = pd.Timestamp("2026-08-31", tz="America/New_York")
OOS_SPLIT = pd.Timestamp("2016-01-01", tz="America/New_York")
GFC = (pd.Timestamp("2008-01-01", tz="America/New_York"), pd.Timestamp("2009-12-31", tz="America/New_York"))

BARS_PER_YEAR = 252
SUE_THRESHOLDS = [1.0, 1.5, 2.0]
HORIZONS = [20, 60]
COST_BPS_SIDE = 5.0                    # 3 spread + 1 commission + 1 slippage
SHORT_CARRY_ANNUAL = 0.020            # 0.5% borrow + ~1.5% blended dividend owed
PRIOR_TRIALS = 1073
NEW_TRIALS = 12


# --------------------------------------------------------------------------- #
# data acquisition (cached)
# --------------------------------------------------------------------------- #
def fetch_earnings() -> pd.DataFrame:
    if EARN_CSV.exists():
        df = pd.read_csv(EARN_CSV, parse_dates=["announce_ts"])
        df["announce_ts"] = pd.to_datetime(df["announce_ts"], utc=True).dt.tz_convert("America/New_York")
        return df
    rows = []
    for i, tk in enumerate(UNIVERSE, 1):
        for attempt in range(3):
            try:
                ed = yf.Ticker(tk).get_earnings_dates(limit=100)
                break
            except Exception as e:
                print(f"  {tk} attempt {attempt+1}: {e}", flush=True)
                time.sleep(2)
                ed = None
        if ed is None or ed.empty:
            print(f"  {tk}: NO earnings data", flush=True)
            continue
        ed = ed.reset_index().rename(columns={
            "Earnings Date": "announce_ts", "EPS Estimate": "eps_est",
            "Reported EPS": "eps_act", "Surprise(%)": "surprise_pct"})
        ed["ticker"] = tk
        rows.append(ed[["ticker", "announce_ts", "eps_est", "eps_act", "surprise_pct"]])
        print(f"  [{i}/{len(UNIVERSE)}] {tk}: {len(ed)} events "
              f"{ed['announce_ts'].min().date()}..{ed['announce_ts'].max().date()}", flush=True)
        time.sleep(0.4)
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(EARN_CSV, index=False)
    return out


def fetch_prices() -> pd.DataFrame:
    if PX_CSV.exists():
        px = pd.read_csv(PX_CSV, index_col=0, parse_dates=True)
        px.index = pd.DatetimeIndex(px.index)
        return px
    frames = {}
    for tk in UNIVERSE:
        h = yf.download(tk, start="2004-06-01", end="2026-09-01", interval="1d",
                        auto_adjust=True, actions=False, progress=False, threads=False)
        if h is None or h.empty:
            print(f"  price {tk}: EMPTY", flush=True)
            continue
        if isinstance(h.columns, pd.MultiIndex):
            h.columns = h.columns.get_level_values(0)
        frames[tk] = h["Close"]
        time.sleep(0.2)
    px = pd.DataFrame(frames).sort_index()
    px.index = pd.DatetimeIndex(px.index.date)
    px.to_csv(PX_CSV)
    return px


# --------------------------------------------------------------------------- #
# event construction
# --------------------------------------------------------------------------- #
def build_events(earn: pd.DataFrame, px: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    tdays = px.index  # tz-naive dates
    earn = earn.dropna(subset=["announce_ts"]).copy()
    earn = earn[(earn["announce_ts"] >= START) & (earn["announce_ts"] <= END)]
    earn = earn.sort_values(["ticker", "announce_ts"]).drop_duplicates(["ticker", "announce_ts"])

    qual = {}
    qual["raw_events_in_window"] = len(earn)
    qual["with_est_and_act"] = int(earn[["eps_est", "eps_act"]].notna().all(axis=1).sum())
    earn = earn.dropna(subset=["eps_est", "eps_act"])

    # SUE with causal rolling std of the DOLLAR surprise (transform keeps the frame/index intact)
    earn["dollar_surprise"] = earn["eps_act"] - earn["eps_est"]
    earn = earn.sort_values(["ticker", "announce_ts"]).reset_index(drop=True)
    roll = earn.groupby("ticker")["dollar_surprise"].transform(
        lambda s: s.rolling(8, min_periods=4).std().shift(1))
    earn["sue"] = earn["dollar_surprise"] / roll
    earn = earn[np.isfinite(earn["sue"])].copy()

    # causal entry: close of first trading day whose OPEN is strictly after announce_ts
    ann_date = earn["announce_ts"].dt.tz_convert("America/New_York").dt.normalize().dt.tz_localize(None)
    ann_hour = earn["announce_ts"].dt.tz_convert("America/New_York").dt.hour
    before_open = ann_hour < 9  # 06:00-08:00 cluster -> tradeable at same day's open
    entry_dates, exit_maps = [], {h: [] for h in HORIZONS}
    keep = []
    tdi = pd.DatetimeIndex(tdays)
    for (adate, bopen, tkr) in zip(ann_date.to_numpy(), before_open.to_numpy(), earn["ticker"].to_numpy()):
        adate = pd.Timestamp(adate)
        pos = tdi.searchsorted(adate, side="left")     # first trading day index >= adate
        on_adate = pos < len(tdi) and tdi[pos] == adate
        if bopen:
            # before-open announce: same day's open is already after the news -> enter that day's close
            e_idx = pos
        else:
            # after-close / during-hours: need the first trading day STRICTLY AFTER adate
            e_idx = pos + 1 if on_adate else pos
        if e_idx >= len(tdi) - max(HORIZONS) - 2:
            keep.append(False); entry_dates.append(pd.NaT)
            for h in HORIZONS: exit_maps[h].append(pd.NaT)
            continue
        if tkr not in px.columns or pd.isna(px[tkr].iloc[e_idx]):
            keep.append(False); entry_dates.append(pd.NaT)
            for h in HORIZONS: exit_maps[h].append(pd.NaT)
            continue
        keep.append(True)
        entry_dates.append(tdi[e_idx])
        for h in HORIZONS:
            exit_maps[h].append(tdi[min(e_idx + h, len(tdi) - 1)])

    earn["entry_date"] = entry_dates
    for h in HORIZONS:
        earn[f"exit_{h}"] = exit_maps[h]
    earn = earn[pd.Series(keep, index=earn.index)].copy()

    qual["events_with_sue_and_price"] = len(earn)
    qual["date_min"] = str(earn["entry_date"].min().date())
    qual["date_max"] = str(earn["entry_date"].max().date())
    qual["n_names"] = earn["ticker"].nunique()
    # LOOK-AHEAD CHECK: the trade is executed at the entry day's CLOSE (16:00 ET).
    # Assert that close instant is strictly after the announcement wall-clock time,
    # for every event (compares like with like -- not entry-midnight vs announce-08:00).
    entry_close_dt = earn["entry_date"] + pd.Timedelta(hours=16)                 # 16:00 ET close, naive
    ann_naive = earn["announce_ts"].dt.tz_localize(None)
    gap_h = (entry_close_dt - ann_naive).dt.total_seconds() / 3600.0
    qual["lookahead_min_gap_hours"] = float(gap_h.min())
    qual["lookahead_pass"] = bool((gap_h > 0).all())
    qual["lookahead_n_bad"] = int((gap_h <= 0).sum())
    # also: no entry earlier than the announcement CALENDAR day
    qual["entry_before_announce_day"] = int((earn["entry_date"] < ann_naive.dt.normalize()).sum())
    qual["pct_before_open"] = float((earn["announce_ts"].dt.hour < 9).mean())
    return earn, qual


# --------------------------------------------------------------------------- #
# portfolio backtest for one cell
# --------------------------------------------------------------------------- #
def run_cell(events: pd.DataFrame, px: pd.DataFrame, thr: float, H: int,
             long_short: bool, start=None, end=None) -> dict:
    rets = px.pct_change()
    ev = events.copy()
    ev["sign"] = np.where(ev["sue"] > thr, 1, np.where(ev["sue"] < -thr, -1, 0))
    ev = ev[ev["sign"] != 0]
    if not long_short:
        ev = ev[ev["sign"] == 1]
    if start is not None:
        ev = ev[ev["entry_date"] >= pd.Timestamp(start).tz_localize(None)]
    if end is not None:
        ev = ev[ev[f"exit_{H}"] <= pd.Timestamp(end).tz_localize(None)]
    if len(ev) < 20:
        return dict(n_events=len(ev), insufficient=True)

    # build (date, ticker, sign) rows for the holding window [entry, exit)
    recs = []
    tdi = px.index
    for _, r in ev.iterrows():
        i0 = tdi.searchsorted(r["entry_date"], "left")
        i1 = tdi.searchsorted(r[f"exit_{H}"], "left")
        for k in range(i0 + 1, i1 + 1):                # returns realised AFTER entry close
            recs.append((tdi[k], r["ticker"], r["sign"], k == i0 + 1, k == i1))
    pos = pd.DataFrame(recs, columns=["date", "ticker", "sign", "is_open", "is_close"])
    # per-position daily return
    rl = rets.reset_index().melt(id_vars="index", var_name="ticker", value_name="ret").rename(columns={"index": "date"})
    pos = pos.merge(rl, on=["date", "ticker"], how="left").dropna(subset=["ret"])
    pos["signed_ret"] = pos["sign"] * pos["ret"]
    # costs: 5bps on open day, 5bps on close day; short carry daily on shorts
    pos["cost"] = (pos["is_open"].astype(float) + pos["is_close"].astype(float)) * (COST_BPS_SIDE / 1e4)
    pos.loc[pos["sign"] == -1, "cost"] += SHORT_CARRY_ANNUAL / BARS_PER_YEAR
    pos["net_contrib"] = pos["signed_ret"] - pos["cost"]

    daily = pos.groupby("date").agg(gross=("signed_ret", "mean"), net=("net_contrib", "mean"),
                                    n_active=("ticker", "size")).sort_index()
    if len(daily) < 60:
        return dict(n_events=len(ev), insufficient=True)
    dret = daily["net"]
    eq = (1 + dret).cumprod()
    yrs = len(dret) / BARS_PER_YEAR
    total = float(eq.iloc[-1] - 1.0)
    cagr = (1 + total) ** (1 / yrs) - 1 if yrs > 0 else float("nan")
    pos_days = dret[dret > 0].sum(); neg_days = -dret[dret < 0].sum()

    # per-year net (sum of daily net -> approx yearly)
    yr = dret.groupby(dret.index.year).apply(lambda s: float((1 + s).prod() - 1))
    tot_y = float(sum(yr.values))
    top_share = float(max(yr.values) / tot_y) if tot_y > 0 else float("nan")

    # per-event realised signed drift (entry close -> exit close)
    ev_ret = []
    for _, r in ev.iterrows():
        p0 = px[r["ticker"]].reindex([r["entry_date"]]).iloc[0]
        p1 = px[r["ticker"]].reindex([r[f"exit_{H}"]]).iloc[0]
        if pd.notna(p0) and pd.notna(p1) and p0 > 0:
            ev_ret.append(r["sign"] * (p1 / p0 - 1.0))
    ev_ret = np.array(ev_ret)

    return dict(
        n_events=len(ev), n_long=int((ev["sign"] == 1).sum()), n_short=int((ev["sign"] == -1).sum()),
        insufficient=False, n_obs=int(len(dret)), mean_active=float(daily["n_active"].mean()),
        net_sharpe=float(sharpe(dret, BARS_PER_YEAR)), gross_sharpe=float(sharpe(daily["gross"], BARS_PER_YEAR)),
        net_pf=float(pos_days / neg_days) if neg_days > 0 else float("inf"),
        cagr=float(cagr), total_return=total, max_dd=float(max_drawdown(eq)),
        skew=float(dret.skew()), ekurt=float(dret.kurtosis()),
        top_year_share=top_share, yr=dict(yr),
        ev_mean_drift=float(ev_ret.mean()) if len(ev_ret) else float("nan"),
        ev_win_rate=float((ev_ret > 0).mean()) if len(ev_ret) else float("nan"),
        ev_median_drift=float(np.median(ev_ret)) if len(ev_ret) else float("nan"),
    )


def bh_equal_weight(px: pd.DataFrame, start, end) -> dict:
    sub = px.loc[pd.Timestamp(start).tz_localize(None):pd.Timestamp(end).tz_localize(None)]
    r = sub.pct_change().mean(axis=1).dropna()      # equal-weight, names included when they have data
    eq = (1 + r).cumprod()
    yrs = len(r) / BARS_PER_YEAR
    total = float(eq.iloc[-1] - 1.0)
    return dict(net_sharpe=float(sharpe(r, BARS_PER_YEAR)),
                cagr=float((1 + total) ** (1 / yrs) - 1) if yrs > 0 else float("nan"),
                total_return=total, max_dd=float(max_drawdown(eq)))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    W = 140
    print("=" * W)
    print("  POST-EARNINGS-ANNOUNCEMENT DRIFT (PEAD)  --  event-driven, yfinance earnings-surprise data")
    print("=" * W)

    print("\n[data] fetching / loading earnings + prices ...")
    earn = fetch_earnings()
    px = fetch_prices()
    px = px[[c for c in UNIVERSE if c in px.columns]]
    print(f"  earnings rows (all names, all dates): {len(earn):,}")
    print(f"  price panel: {px.shape[1]} names, {px.index.min().date()}..{px.index.max().date()}, {len(px):,} days")

    events, q = build_events(earn, px)

    # ---------------- DATA QUALITY REPORT (FIRST, per the brief) ----------------
    print("\n" + "#" * W)
    print("  DATA QUALITY -- reported FIRST, per the brief")
    print("#" * W)
    print(f"  raw earnings events in window {START.date()}..{END.date()} : {q['raw_events_in_window']:,}")
    print(f"  ... with BOTH EPS Estimate and Reported EPS present        : {q['with_est_and_act']:,} "
          f"({100*q['with_est_and_act']/q['raw_events_in_window']:.1f}%)")
    print(f"  ... with a computable causal SUE and price coverage        : {q['events_with_sue_and_price']:,}")
    print(f"  distinct names contributing events                         : {q['n_names']}")
    print(f"  event entry-date span                                      : {q['date_min']} .. {q['date_max']}")
    print(f"  announcements before market open (06:00-08:59 ET)          : {100*q['pct_before_open']:.0f}%  "
          f"(rest are after-close 16:00 or ~1% during-hours -> entry deferred one day)")
    print(f"\n  LOOK-AHEAD GUARD: every entry day strictly after its announcement timestamp -> "
          f"{'PASS' if q['lookahead_pass'] else 'FAIL'}  (min gap {q['lookahead_min_gap_hours']:.1f} h)")
    print("\n  KEY TRUST LIMITATION (unfixable with free data): the 'EPS Estimate' is Yahoo's CURRENT record of")
    print("  consensus, not a verified pre-announcement snapshot. A restated estimate biases surprises toward")
    print("  looking MORE predictive than they were -> a KILL is robust, a positive would need paid PIT data.")
    print("  Survivorship: fixed set of names solvent & large-cap TODAY (blow-ups/acquisitions absent) -> inflates")
    print("  the LONG-beat leg's realised drift. Both stated, not corrected.")

    # ---------------- GRID ----------------
    bh_full = bh_equal_weight(px, START, END)
    bh_is = bh_equal_weight(px, START, OOS_SPLIT)
    bh_oos = bh_equal_weight(px, OOS_SPLIT, END)
    bh_gfc = bh_equal_weight(px, *GFC)

    rows = []
    for ls in (True, False):
        for thr in SUE_THRESHOLDS:
            for H in HORIZONS:
                full = run_cell(events, px, thr, H, ls)
                if full.get("insufficient"):
                    rows.append(dict(long_short=ls, thr=thr, H=H, **full)); continue
                is_c = run_cell(events, px, thr, H, ls, start=START, end=OOS_SPLIT)
                oos_c = run_cell(events, px, thr, H, ls, start=OOS_SPLIT, end=END)
                gfc_c = run_cell(events, px, thr, H, ls, start=GFC[0], end=GFC[1])
                rows.append(dict(
                    long_short=ls, thr=thr, H=H, **full,
                    is_sharpe=is_c.get("net_sharpe", np.nan), is_pf=is_c.get("net_pf", np.nan),
                    is_cagr=is_c.get("cagr", np.nan), is_n=is_c.get("n_events", 0),
                    oos_sharpe=oos_c.get("net_sharpe", np.nan), oos_pf=oos_c.get("net_pf", np.nan),
                    oos_cagr=oos_c.get("cagr", np.nan), oos_n=oos_c.get("n_events", 0),
                    gfc_sharpe=gfc_c.get("net_sharpe", np.nan), gfc_cagr=gfc_c.get("cagr", np.nan),
                    gfc_n=gfc_c.get("n_events", 0),
                ))
    res = pd.DataFrame(rows)
    res.drop(columns=[c for c in ["yr"] if c in res]).to_csv(RESULTS / "post_earnings_drift.csv", index=False)

    def tag(r):
        return f"{'L/S' if r['long_short'] else 'L-only':>6} SUE>{r['thr']:.1f} {int(r['H'])}d"

    print("\n" + "#" * W)
    print(f"  RESULT -- 12 cells, daily-rebalanced equal-weight, real costs (10bps r/t + {SHORT_CARRY_ANNUAL*100:.1f}%/yr short carry)")
    print(f"  Full window {START.date()}..{END.date()}   |   equal-weight B&H of the universe: "
          f"Sharpe {bh_full['net_sharpe']:+.2f}, CAGR {bh_full['cagr']*100:+.1f}%, maxDD {bh_full['max_dd']*100:.0f}%")
    print("#" * W)
    hdr = (f"  {'cell':<20} {'events':>7} {'L/S n':>10} {'ev drift':>9} {'ev win%':>8} {'netSR':>7} {'grossSR':>8} "
           f"{'netPF':>6} {'CAGR':>7} {'maxDD':>7} {'topYr':>7} {'beatsBH':>8}")
    print(hdr); print("  " + "-" * (W - 2))
    for _, r in res.iterrows():
        if r.get("insufficient"):
            print(f"  {tag(r):<20} insufficient events ({int(r['n_events'])})"); continue
        beat = np.isfinite(r["net_sharpe"]) and r["net_sharpe"] > bh_full["net_sharpe"] and r["cagr"] > bh_full["cagr"]
        ty = f"{r['top_year_share']*100:.0f}%" if np.isfinite(r["top_year_share"]) else "n/a"
        print(f"  {tag(r):<20} {int(r['n_events']):>7} {int(r['n_long'])}/{int(r['n_short']):<8} "
              f"{r['ev_mean_drift']*100:>+8.2f}% {r['ev_win_rate']*100:>7.0f}% {r['net_sharpe']:>+7.2f} "
              f"{r['gross_sharpe']:>+8.2f} {r['net_pf']:>6.2f} {r['cagr']*100:>+6.1f}% {r['max_dd']*100:>6.0f}% "
              f"{ty:>7} {('YES' if beat else 'no'):>8}")

    # ---------------- OOS ----------------
    print("\n" + "#" * W)
    print(f"  OUT-OF-REGIME -- IS {START.date()}..2015-12 vs OOS 2016-01..{END.date()}  "
          f"(B&H IS SR {bh_is['net_sharpe']:+.2f} / OOS SR {bh_oos['net_sharpe']:+.2f})")
    print("#" * W)
    print(f"  {'cell':<20} {'IS n':>6} {'IS SR':>7} {'IS PF':>6} {'IS CAGR':>8} | "
          f"{'OOS n':>6} {'OOS SR':>7} {'OOS PF':>6} {'OOS CAGR':>9} | {'2008-09 SR':>11} {'2008-09 CAGR':>13}")
    for _, r in res.iterrows():
        if r.get("insufficient"):
            continue
        print(f"  {tag(r):<20} {int(r.get('is_n',0)):>6} {r.get('is_sharpe',np.nan):>+7.2f} "
              f"{r.get('is_pf',np.nan):>6.2f} {r.get('is_cagr',np.nan)*100:>+7.1f}% | "
              f"{int(r.get('oos_n',0)):>6} {r.get('oos_sharpe',np.nan):>+7.2f} {r.get('oos_pf',np.nan):>6.2f} "
              f"{r.get('oos_cagr',np.nan)*100:>+8.1f}% | {r.get('gfc_sharpe',np.nan):>+11.2f} "
              f"{r.get('gfc_cagr',np.nan)*100:>+12.1f}%")
    print(f"  (equal-weight B&H over 2008-2009: Sharpe {bh_gfc['net_sharpe']:+.2f}, CAGR {bh_gfc['cagr']*100:+.1f}%)")

    # ---------------- concentration ----------------
    print("\n" + "#" * W)
    print("  PER-YEAR NET RETURN (compounded within year) -- concentration check")
    print("#" * W)
    for _, r in res.iterrows():
        if r.get("insufficient") or not isinstance(r.get("yr"), dict):
            continue
        yl = r["yr"]
        cells = " ".join(f"{y}:{v*100:+.0f}" for y, v in sorted(yl.items()))
        ty = f"{r['top_year_share']*100:.0f}%" if np.isfinite(r["top_year_share"]) else "n/a"
        print(f"  {tag(r):<20} {cells}   [top-year {ty}]")

    # ---------------- DSR reference ----------------
    srs = res.loc[~res.get("insufficient", pd.Series(False, index=res.index)).fillna(False), "net_sharpe"]
    srs = srs[np.isfinite(srs)].to_numpy()
    if len(srs) >= 2:
        emax, Np, mu, sd = expected_max_sharpe(srs)
        print("\n" + "#" * W)
        print("  DEFLATED SHARPE -- REFERENCE ONLY (not a survival gate). Pool = the 12 a priori cells.")
        print("#" * W)
        print(f"  pool n={Np}  mean {mu:+.3f}  sd {sd:.3f}  ->  E[max SR] {emax:+.3f}")
        rr = res[~res.get("insufficient", pd.Series(False, index=res.index)).fillna(False)].copy()
        best = rr.loc[rr["net_sharpe"].idxmax()]
        d = deflated_sharpe(float(best["net_sharpe"]), srs, n_obs=max(int(best["n_obs"]), 5),
                            ann_factor=BARS_PER_YEAR, skewness=float(best["skew"]),
                            excess_kurtosis=float(best["ekurt"]))["dsr"]
        print(f"  best cell: {tag(best)}  net Sharpe {best['net_sharpe']:+.2f}  ->  DSR {d:.3f}  (vs 0.95 bar)")

    # ---------------- raw Surprise(%) diagnostic ----------------
    print("\n" + "#" * W)
    print("  DIAGNOSTIC -- raw Surprise(%) thresholds instead of SUE (not a counted trial). L/S, 20d & 60d.")
    print("#" * W)
    ev2 = events.copy()
    ev2["sue"] = ev2["surprise_pct"]   # reuse the machinery: 'sue' column drives the sign
    for pthr in (5.0, 10.0, 20.0):
        for H in HORIZONS:
            c = run_cell(ev2, px, pthr, H, True)
            if c.get("insufficient"):
                print(f"   surp>{pthr:>4.0f}% {H}d : insufficient"); continue
            print(f"   surp>{pthr:>4.0f}% {H}d : n={c['n_events']:>5}  ev drift {c['ev_mean_drift']*100:+.2f}%  "
                  f"netSR {c['net_sharpe']:+.2f}  netPF {c['net_pf']:.2f}  CAGR {c['cagr']*100:+.1f}%")

    # ---------------- verdict ----------------
    rr = res[~res.get("insufficient", pd.Series(False, index=res.index)).fillna(False)].copy()
    n = len(rr)
    rr["beats_bh"] = rr.apply(lambda r: bool(np.isfinite(r["net_sharpe"]) and r["net_sharpe"] > bh_full["net_sharpe"]
                                             and r["cagr"] > bh_full["cagr"]), axis=1)
    rr["oos_holds"] = rr.apply(lambda r: bool(np.isfinite(r.get("oos_sharpe", np.nan)) and r.get("oos_sharpe", -9) > 0
                                              and np.isfinite(r.get("is_sharpe", np.nan)) and r.get("is_sharpe", -9) > 0
                                              and r.get("oos_pf", 0) > 1.0), axis=1)
    rr["not_conc"] = rr["top_year_share"].apply(lambda s: bool(np.isfinite(s) and s <= 0.60))
    rr["pos_sharpe"] = rr["net_sharpe"] > 0
    rr["net_pf_gt1"] = rr["net_pf"] > 1.0
    rr["SURVIVOR"] = (rr["pos_sharpe"] & rr["net_pf_gt1"] & rr["oos_holds"] & rr["not_conc"] & rr["beats_bh"])
    rr.to_csv(RESULTS / "post_earnings_drift_scored.csv", index=False)

    print("\n" + "=" * W)
    print("  VERDICT")
    print("=" * W)
    print(f"  cells scored: {n}   net Sharpe>0: {int(rr['pos_sharpe'].sum())}/{n}   net PF>1: {int(rr['net_pf_gt1'].sum())}/{n}")
    print(f"  beats equal-weight B&H (Sharpe AND CAGR): {int(rr['beats_bh'].sum())}/{n}   "
          f"OOS holds: {int(rr['oos_holds'].sum())}/{n}   not year-concentrated: {int(rr['not_conc'].sum())}/{n}")
    print(f"  SURVIVORS: {int(rr['SURVIVOR'].sum())}/{n}")
    best = rr.loc[rr["net_sharpe"].idxmax()]
    print(f"  best raw net Sharpe: {tag(best)} -> SR {best['net_sharpe']:+.2f}, PF {best['net_pf']:.2f}, "
          f"CAGR {best['cagr']*100:+.1f}% (vs B&H {bh_full['cagr']*100:+.1f}%), maxDD {best['max_dd']*100:.0f}%, "
          f"top-year {best['top_year_share']*100:.0f}%, OOS holds {'YES' if best['oos_holds'] else 'NO'}")
    mean_drift = float(rr["ev_mean_drift"].mean() * 100)
    print(f"  mean per-event signed drift across cells: {mean_drift:+.2f}% over the hold  "
          f"(gross, before the daily-book costs)")
    print()
    if int(rr["SURVIVOR"].sum()) > 0:
        print("  -> SOME cells clear every gate. PEAD would be the first survivor in the project -- treat as PROVISIONAL")
        print("     pending point-in-time I/B/E/S estimate data (the free estimate's PIT integrity is unverifiable and")
        print("     biases toward a false positive) and a survivorship-free universe.")
    else:
        print("  -> KILL. Post-earnings-announcement drift, as capturable here (SUE on free yfinance surprise data,")
        print("     T+1 entry that skips the announcement jump, real large-cap costs, 20/60-day holds), does not")
        print("     produce a cost-surviving, regime-robust, better-than-buy-and-hold edge. The gross drift is")
        print("     [see mean per-event drift above]; the daily-rebalanced net portfolio [see table].")
        print("     NOTE the data caveats CUT TOWARD leniency here (restated estimates + survivorship both flatter")
        print("     the result), so the kill is not a data-quality artefact -- it is despite an optimistic setup.")
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (3 SUE thresholds x 2 horizons x [long/short, long-only]).  "
          f"CUMULATIVE: {PRIOR_TRIALS} + {NEW_TRIALS} = {PRIOR_TRIALS + NEW_TRIALS}")
    print(f"  (raw Surprise(%) variant + OOS/GFC sub-splits are diagnostics of those 12 cells, not separate configs.)")
    print(f"  LOOK-AHEAD GUARD: {'PASS' if q['lookahead_pass'] else 'FAIL'} (min gap {q['lookahead_min_gap_hours']:.1f}h, "
          f"every entry strictly after its announcement).")
    print("  saved -> results/post_earnings_drift.csv, post_earnings_drift_scored.csv, post_earnings_drift_run.log")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
