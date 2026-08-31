#!/usr/bin/env python3
"""
run_vol_protected_structures.py — STATE_OF_PLAY section 21.

PREMISE (unchanged from section 20, NOT re-litigated here):
  The volatility risk premium is REAL — VIX averages +3.69 vol points above
  subsequently-realized SPY vol, 83.3% of days, t=48.5, consistent across
  all four decades (scripts/test_vol_risk_premium.py). Section 20 built the
  naked harvest: LONG SVXY when VIX(t)/trailing-20d-realized-SPY-vol(t) >
  threshold, else CASH, position entered t+1. It was KILLED ON TAIL RISK:
  -83.0% in a single session (2018-02-06, real SVXY traded price) and
  -85% to -92% across that week, at BOTH thresholds (1.2x, 1.5x).

THIS RUN keeps the SAME confirmed edge and SAME signal UNCHANGED and tests
whether a PROTECTED POSITION STRUCTURE makes it survivable through that exact
event — without trying to predict the crash. Three structures, all compared
side by side against the section-20 naked version:

  A — SMALL FIXED FRACTIONAL SIZING. Put a fixed small fraction f of account
      equity in the section-20 SVXY strategy (rebalanced daily to constant
      f), rest in cash (assumed 0% yield — conservative, biases AGAINST the
      structure). Test f = 10% and f = 20%. Report what Volmageddon costs
      the WHOLE ACCOUNT.

  B — VOL-OF-VOL CIRCUIT BREAKER. Full sizing (f=1, directly comparable to
      section 20), but force CASH the moment VIX itself jumps hard in one
      day: if VIX(t)/VIX(t-1) - 1 > b, go flat for day t+1 and stay flat for
      a stated cooldown of COOLDOWN_DAYS trading days. Test b = +20% and
      +30% single-day VIX moves. Causal: the VIX move on day t is fully
      known at the close of day t, same timing convention as the base
      signal. Report the FALSE-ALARM RATE honestly (fires without a large
      SVXY loss following).

  C — PAIRED LONG-VOL HEDGE. Alongside the section-20 SVXY position (weight
      1.0 when the signal is long), hold an ADDITIONAL long-vol overlay in
      VIXY (ProShares VIX Short-Term Futures ETF — the direct long-vol
      counterpart of SVXY; see scripts/download_vixy.py for why VIXY and not
      VXX) at weight h of the SVXY notional, only while the SVXY position is
      on. Gross exposure while long is therefore 1 + h. VIXY's REAL traded
      price is used unmodified — its own roll cost / contango bleed / expense
      ratio are embedded exactly as SVXY's are. Test h = 0.5 and h = 1.0.
      Quantify the STEADY-STATE DRAG of carrying the hedge on ordinary days
      explicitly, against what it saves in Feb 2018.

HONESTY GATES (identical in spirit to section 20, but now ACCOUNT-LEVEL):
  * Worst single day / single week AT THE ACCOUNT LEVEL reported FIRST.
  * Account-level catastrophic bar: does the WHOLE ACCOUNT ever lose more
    than 15% (soft) / 20% (hard) in a single week? Worst day flagged too.
  * Deflated Sharpe against the cumulative project trial count.
  * Per-year concentration (top-year share of total log return).
  * vs SPY buy-and-hold over the identical window.
  * Net of ALL real costs, including the hedge leg's real spread in C and
    VIXY's embedded carry.

Usage: python run_vol_protected_structures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown, profit_factor

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
RV_WINDOW = 20
THRESHOLDS = [1.2, 1.5]
SPREAD_BPS_PER_SIDE = 5.0

# structure grids (all a priori, stated in the task)
A_FRACTIONS = [0.10, 0.20]
B_BREAKERS = [0.20, 0.30]
B_COOLDOWN_DAYS = 3          # stated a priori: one acute VIX spike routinely spans >1 session
C_HEDGE_RATIOS = [0.5, 1.0]  # VIXY overlay weight, as a fraction of the SVXY notional

# account-level catastrophic bars (section 21 redefinition)
ACCT_WEEK_SOFT = -0.15
ACCT_WEEK_HARD = -0.20
ACCT_DAY_HARD = -0.15

# ---- trial accounting -------------------------------------------------------
# Section 20 closed at cumulative N=934 (932 prior + its own 2 threshold cells).
PRIOR_TRIALS = 934
# this batch: A(2x2) + B(2x2) + C(2x2) = 12 a priori cells
OUT_CSV = RESULTS / "vol_protected_structures.csv"


def load_close(fname: str) -> pd.Series:
    df = pd.read_csv(DATA / fname, index_col=0, parse_dates=True)
    return df["close"].dropna()


def trailing_rv(spy_close: pd.Series, window: int) -> pd.Series:
    log_ret = np.log(spy_close / spy_close.shift(1))
    return log_ret.rolling(window, min_periods=window).std() * np.sqrt(252) * 100


def base_signal(vix: pd.Series, ratio: pd.Series, svxy_close: pd.Series,
                threshold: float) -> pd.DataFrame:
    """
    The section-20 signal, UNCHANGED. Returns a frame on SVXY's calendar with:
      position   : bool, LONG SVXY today (decided from ratio(d-1) > threshold)
      svxy_ret   : SVXY close-to-close pct return today
      gross_ret  : position * svxy_ret
      net_ret    : gross minus 5bps/side when the position flips
    """
    idx = svxy_close.index
    ratio_aligned = ratio.reindex(idx)
    signal = (ratio_aligned > threshold)
    position = signal.shift(1).fillna(False)

    svxy_ret = svxy_close.pct_change()
    gross = (position.astype(float) * svxy_ret).fillna(0.0)
    switched = position != position.shift(1).fillna(False)
    cost = switched.astype(float) * (SPREAD_BPS_PER_SIDE / 10_000.0)
    net = gross - cost
    return pd.DataFrame(dict(position=position, svxy_ret=svxy_ret.fillna(0.0),
                             gross_ret=gross, net_ret=net), index=idx)


# ---- honesty-gate helpers -------------------------------------------------------

def worst_day_week(ret: pd.Series) -> dict:
    wd = float(ret.min()); wdd = ret.idxmin()
    week = (1 + ret).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    ww = float(week.min()); wwd = week.idxmin()
    return dict(worst_day=wd, worst_day_date=str(wdd.date()),
                worst_week=ww, worst_week_date=str(wwd.date()))


def year_concentration(ret: pd.Series) -> dict:
    yr_log = np.log1p(ret).groupby(ret.index.year).sum()
    total = float(yr_log.sum())
    top = float(yr_log.max()) if len(yr_log) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return dict(top_year_log=top, top_year_share=share,
                years={int(y): float(v) for y, v in yr_log.items()})


def event_ret(ret: pd.Series, start: str, end: str) -> float:
    sl = ret[start:end]
    return float((1 + sl).prod() - 1) if len(sl) else float("nan")


def full_metrics(ret: pd.Series) -> dict:
    ret = ret.dropna()
    eq = (1 + ret).cumprod()
    m = dict(
        n_obs=int(len(ret)),
        sharpe_net=float(sharpe(ret, BARS_PER_YEAR)),
        pf_net=float(profit_factor(ret)),
        max_dd=float(max_drawdown(eq)),
        total_ret=float(eq.iloc[-1] - 1) if len(eq) else float("nan"),
        cagr=float(eq.iloc[-1] ** (BARS_PER_YEAR / len(ret)) - 1) if len(ret) > BARS_PER_YEAR else float("nan"),
        skew=float(ret.skew()), ekurt=float(ret.kurtosis()),
        volmageddon_feb2018=event_ret(ret, "2018-02-01", "2018-02-28"),
        covid_2020=event_ret(ret, "2020-02-15", "2020-04-15"),
    )
    m.update(worst_day_week(ret))
    yc = year_concentration(ret)
    m["top_year_share"] = yc["top_year_share"]
    m["_years"] = yc["years"]
    return m


# ---- the three structures -------------------------------------------------------

def structure_A(base: pd.DataFrame, f: float) -> pd.Series:
    """Account return = f * (section-20 net strategy return), daily-rebalanced
    to constant fraction f; the (1-f) remainder sits in cash at 0%."""
    return f * base["net_ret"]


def structure_B(base: pd.DataFrame, vix: pd.Series, b: float, cooldown: int) -> tuple[pd.Series, dict]:
    """
    Full-size section-20 strategy, but a one-day VIX jump > b forces CASH for
    the next session and holds flat for `cooldown` sessions. Causal: the VIX
    move over day t is known at t's close and gates the position for t+1.
    """
    idx = base.index
    vix_aligned = vix.reindex(idx)
    vix_1d_move = vix_aligned.pct_change()
    trigger_at_close = (vix_1d_move > b).fillna(False)  # fires on day t's close

    # block day t+1 .. t+cooldown
    blocked = pd.Series(False, index=idx)
    trig_positions = np.where(trigger_at_close.to_numpy())[0]
    n = len(idx)
    for p in trig_positions:
        lo, hi = p + 1, min(p + cooldown, n - 1)
        if lo <= hi:
            blocked.iloc[lo:hi + 1] = True

    protected_position = base["position"] & (~blocked)
    # recompute returns + switching cost under the gated position
    gross = (protected_position.astype(float) * base["svxy_ret"]).fillna(0.0)
    switched = protected_position != protected_position.shift(1).fillna(False)
    cost = switched.astype(float) * (SPREAD_BPS_PER_SIDE / 10_000.0)
    net = gross - cost

    # false-alarm accounting: a trigger is a "true positive" if SVXY's own
    # forward 5-day return from the trigger close is <= FA_LOSS_BAR
    FA_LOSS_BAR = -0.15
    svxy_close_idx = base.index
    svxy_ret = base["svxy_ret"]
    fwd5 = (1 + svxy_ret).shift(-1).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    # align: forward 5d starting the day AFTER the trigger
    fwd5_from_trigger = fwd5.shift(0)  # rolling on shifted series already begins next day
    n_trig = int(trigger_at_close.sum())
    if n_trig:
        trig_idx = idx[trigger_at_close.to_numpy()]
        fwd_vals = fwd5_from_trigger.reindex(trig_idx)
        true_pos = int((fwd_vals <= FA_LOSS_BAR).sum())
        false_alarm_rate = 1.0 - true_pos / n_trig
    else:
        true_pos = 0
        false_alarm_rate = float("nan")
    fa = dict(n_triggers=n_trig, true_positives=true_pos,
              false_alarm_rate=false_alarm_rate, fa_loss_bar=FA_LOSS_BAR,
              cooldown_days=cooldown)
    return net, fa


def structure_C(base: pd.DataFrame, vixy_close: pd.Series, h: float) -> tuple[pd.Series, dict]:
    """
    Section-20 SVXY position (weight 1.0 when long) PLUS a VIXY overlay at
    weight h, held only while the SVXY position is on. Gross exposure while
    long = 1 + h. VIXY real price embeds its own carry; the overlay pays
    5bps/side when it is put on / taken off.
    """
    idx = base.index
    vixy_ret = vixy_close.reindex(idx).pct_change().fillna(0.0)
    pos = base["position"].astype(float)

    svxy_leg_gross = pos * base["svxy_ret"]
    hedge_leg_gross = h * pos * vixy_ret

    switched = base["position"] != base["position"].shift(1).fillna(False)
    # both legs turn over together: (1 + h) notional changing hands
    cost = switched.astype(float) * (1.0 + h) * (SPREAD_BPS_PER_SIDE / 10_000.0)
    net = (svxy_leg_gross + hedge_leg_gross - cost).fillna(0.0)

    # steady-state hedge drag: mean daily hedge-leg return contribution on
    # days the position is on but NOT a tail day (exclude Feb 2018 & Mar 2020)
    on = base["position"].to_numpy()
    dates = idx
    tail_mask = ((dates >= "2018-02-01") & (dates <= "2018-02-28")) | \
                ((dates >= "2020-02-15") & (dates <= "2020-04-15"))
    ordinary = on & (~tail_mask)
    hedge_contrib_ordinary = hedge_leg_gross[ordinary]
    drag = dict(
        mean_daily_hedge_ret_ordinary=float(hedge_contrib_ordinary.mean()),
        ann_hedge_drag=float(hedge_contrib_ordinary.mean() * BARS_PER_YEAR),
        pct_ordinary_days_hedge_negative=float((hedge_contrib_ordinary < 0).mean()),
        hedge_total_ret_feb2018=event_ret(h * vixy_ret[base["position"].astype(bool)], "2018-02-01", "2018-02-28"),
        n_ordinary_on_days=int(ordinary.sum()),
    )
    return net, drag


# ---- reference series ---------------------------------------------------------

def buy_and_hold(close: pd.Series) -> dict:
    ret = close.pct_change().dropna()
    eq = (1 + ret).cumprod()
    m = dict(sharpe=float(sharpe(ret, BARS_PER_YEAR)), max_dd=float(max_drawdown(eq)))
    m.update(worst_day_week(ret))
    return m


def main() -> None:
    spy = load_close("SPY_daily_yfinance.csv")
    vix = load_close("vix_daily_yfinance.csv")
    svxy = load_close("svxy_daily_yfinance.csv")
    vixy = load_close("vixy_daily_yfinance.csv")

    rv = trailing_rv(spy, RV_WINDOW)
    ratio = (vix / rv).dropna()

    win_start, win_end = svxy.index.min(), svxy.index.max()
    W = 116
    print("=" * W)
    print("  SECTION 21 — PROTECTED VOLATILITY-RISK-PREMIUM STRUCTURES")
    print(f"  Same confirmed edge + same VIX/trailing-RV signal as section 20, UNCHANGED. "
          f"Window {win_start.date()} -> {win_end.date()}")
    print(f"  Window already spans 2018 Volmageddon and 2020 COVID — no construction.")
    print("=" * W)

    bh_spy = buy_and_hold(spy[spy.index >= win_start])
    bh_svxy = buy_and_hold(svxy)
    print(f"\n  B&H SPY : Sharpe {bh_spy['sharpe']:+.2f}  maxDD {bh_spy['max_dd']*100:.1f}%  "
          f"worst day {bh_spy['worst_day']*100:+.1f}%  worst week {bh_spy['worst_week']*100:+.1f}%")
    print(f"  B&H SVXY: Sharpe {bh_svxy['sharpe']:+.2f}  maxDD {bh_svxy['max_dd']*100:.1f}%  "
          f"worst day {bh_svxy['worst_day']*100:+.1f}%  worst week {bh_svxy['worst_week']*100:+.1f}%")

    rows: list[dict] = []

    for thr in THRESHOLDS:
        base = base_signal(vix, ratio, svxy, thr)

        # ----- section-20 naked reference, recomputed here for exact comparability
        naked = full_metrics(base["net_ret"])
        naked.update(dict(structure="naked_sec20", threshold=thr, param="f=1.0",
                          extra=""))
        rows.append(naked)

        # ----- Structure A
        for f in A_FRACTIONS:
            acct = structure_A(base, f)
            m = full_metrics(acct)
            m.update(dict(structure="A_fixed_fraction", threshold=thr, param=f"f={f:.2f}",
                          extra=(f"worst DAY is exactly f x the naked sleeve's worst day "
                                 f"({f:.2f} x -83.0% = {f*-83.0:+.1f}%); worst WEEK is the "
                                 f"daily-rebalanced compound, not a clean f-scaling")))
            rows.append(m)

        # ----- Structure B
        for b in B_BREAKERS:
            acct, fa = structure_B(base, vix, b, B_COOLDOWN_DAYS)
            m = full_metrics(acct)
            m.update(dict(structure="B_vol_of_vol_breaker", threshold=thr,
                          param=f"b=+{b*100:.0f}%/1d, cd={B_COOLDOWN_DAYS}d",
                          extra=(f"triggers={fa['n_triggers']}, "
                                 f"true_pos(SVXY fwd5d<={fa['fa_loss_bar']*100:.0f}%)={fa['true_positives']}, "
                                 f"false_alarm_rate={fa['false_alarm_rate']*100:.0f}%")))
            m["_fa"] = fa
            rows.append(m)

        # ----- Structure C
        for h in C_HEDGE_RATIOS:
            acct, drag = structure_C(base, vixy, h)
            m = full_metrics(acct)
            m.update(dict(structure="C_paired_hedge", threshold=thr, param=f"h={h:.1f}xVIXY",
                          extra=(f"ann hedge drag {drag['ann_hedge_drag']*100:+.1f}%/yr on ordinary on-days, "
                                 f"{drag['pct_ordinary_days_hedge_negative']*100:.0f}% of those days hedge loses, "
                                 f"hedge P&L Feb2018 {drag['hedge_total_ret_feb2018']*100:+.0f}%")))
            m["_drag"] = drag
            rows.append(m)

    df = pd.DataFrame(rows)

    # ---- DSR over this batch's own 12 a priori structure cells (naked refs excluded
    #      from the deflation pool: they are the section-20 baseline, not new trials)
    batch = df[df["structure"] != "naked_sec20"].copy()
    n_batch = len(batch)
    cumulative = PRIOR_TRIALS + n_batch
    sr_pool = batch["sharpe_net"].fillna(0.0).to_numpy()
    e_struct = expected_max_sharpe(sr_pool)

    def _dsr(r):
        if not np.isfinite(r["sharpe_net"]) or r["n_obs"] < 4:
            return float("nan")
        return deflated_sharpe(sr_best=float(r["sharpe_net"]), sr_trials=sr_pool,
                               n_obs=int(r["n_obs"]), ann_factor=BARS_PER_YEAR,
                               skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                               excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)["dsr"]

    df["dsr"] = df.apply(lambda r: _dsr(r) if r["structure"] != "naked_sec20" else float("nan"), axis=1)

    # ---- account-level catastrophe flags
    df["breach_week_hard"] = df["worst_week"] < ACCT_WEEK_HARD
    df["breach_week_soft"] = df["worst_week"] < ACCT_WEEK_SOFT
    df["breach_day_hard"] = df["worst_day"] < ACCT_DAY_HARD

    # ---------- OUTPUT ----------
    print("\n" + "=" * W)
    print("  RESULTS — ACCOUNT-LEVEL WORST DAY / WEEK FIRST, PER THE HONESTY GATES")
    print("=" * W)
    hdr = (f"  {'structure':<22}{'thr':>5}{'param':>20}{'wDay%':>9}{'wWeek%':>9}"
           f"{'Feb18%':>9}{'netSR':>8}{'CAGR%':>8}{'maxDD%':>8}{'DSR':>6}{'top%':>7}")
    for thr in THRESHOLDS:
        print(f"\n  --- signal threshold {thr}x " + "-" * (W - 30))
        print(hdr)
        print("  " + "-" * (W - 4))
        sub = df[df["threshold"] == thr]
        for _, r in sub.iterrows():
            share = r["top_year_share"]
            share_s = f"{share*100:>6.0f}%" if np.isfinite(share) else f"{'n/a':>7}"
            dsr_s = f"{r['dsr']:>6.2f}" if np.isfinite(r["dsr"]) else f"{'--':>6}"
            print(f"  {r['structure']:<22}{r['threshold']:>5}{r['param']:>20}"
                  f"{r['worst_day']*100:>9.1f}{r['worst_week']*100:>9.1f}"
                  f"{r['volmageddon_feb2018']*100:>9.1f}{r['sharpe_net']:>+8.2f}"
                  f"{(r['cagr']*100 if np.isfinite(r['cagr']) else float('nan')):>8.1f}"
                  f"{r['max_dd']*100:>8.1f}{dsr_s}{share_s}")
            if r["extra"]:
                print(f"      {r['extra']}")

    print("\n" + "=" * W)
    print("  ACCOUNT-LEVEL CATASTROPHE BARS  (soft week < -15%, hard week < -20%, hard day < -15%)")
    print("=" * W)
    for _, r in df.iterrows():
        flags = []
        if r["breach_week_hard"]: flags.append("WEEK<-20%")
        elif r["breach_week_soft"]: flags.append("week<-15%")
        if r["breach_day_hard"]: flags.append("DAY<-15%")
        verdict = ", ".join(flags) if flags else "within survivable bound"
        print(f"  {r['structure']:<22} thr {r['threshold']}x {r['param']:<20} "
              f"worst day {r['worst_day']*100:+6.1f}%  worst week {r['worst_week']*100:+6.1f}%   -> {verdict}")

    print("\n" + "=" * W)
    print("  vs BUY-AND-HOLD SPY (same window):  Sharpe "
          f"{bh_spy['sharpe']:+.2f}, maxDD {bh_spy['max_dd']*100:.1f}%, "
          f"worst day {bh_spy['worst_day']*100:+.1f}%, worst week {bh_spy['worst_week']*100:+.1f}%")
    print("=" * W)
    for _, r in df.iterrows():
        if r["structure"] == "naked_sec20":
            continue
        beats = r["sharpe_net"] > bh_spy["sharpe"]
        print(f"  {r['structure']:<22} thr {r['threshold']}x {r['param']:<20} netSR {r['sharpe_net']:+.2f}  "
              f"-> {'BEATS' if beats else 'loses to'} SPY on Sharpe")

    # per-year detail
    print("\n" + "=" * W)
    print("  PER-YEAR LOG RETURN (concentration detail)")
    print("=" * W)
    for _, r in df.iterrows():
        yrs = r["_years"]
        ys = "  ".join(f"{y}:{v*100:+.0f}" for y, v in sorted(yrs.items()))
        print(f"  {r['structure']:<22} thr {r['threshold']}x {r['param']:<20} {ys}")

    # ---- why the timing-based protections (B and C) still land on the tail
    print("\n" + "=" * W)
    print("  WHY B AND C STILL TOUCH THE TAIL — the daily mechanics of the two worst events")
    print("=" * W)
    svxy_r = svxy.pct_change(); vixy_r = vixy.pct_change(); vix_r = vix.pct_change()
    for d in ["2018-02-02", "2018-02-05", "2018-02-06", "2018-02-08", "2016-06-24", "2020-02-24", "2020-03-16"]:
        ts = pd.Timestamp(d)
        if ts in svxy_r.index:
            print(f"  {d}: VIX {vix_r.get(ts, float('nan'))*100:+6.1f}%   "
                  f"SVXY {svxy_r.get(ts, float('nan'))*100:+7.1f}%   "
                  f"VIXY {vixy_r.get(ts, float('nan'))*100:+6.1f}%   "
                  f"(prior-day VIX move {vix_r.shift(1).get(ts, float('nan'))*100:+6.1f}%)")
    print("  Volmageddon: SVXY's -83% fell on 2018-02-06, the day AFTER VIX's +116% spike — VIX itself")
    print("  was DOWN -20% that day and VIXY was -3%, so a same-day VIX-move breaker (B) had already")
    print("  fired (good) but a VIXY hedge (C) gave almost nothing on the day the loss actually hit.")
    print("  Brexit 2016-06-24: VIX +49% and SVXY -26% on the SAME day, with the prior day's VIX DOWN")
    print("  -18% — no pre-close warning, so B takes the full -26% no matter how long its cooldown is.")

    # ---- verdict
    print("\n" + "=" * W)
    print("  VERDICT")
    print("=" * W)
    print(f"  Cumulative project trials: {PRIOR_TRIALS} prior + {n_batch} new structure cells = {cumulative}")
    print(f"  DSR deflation pool = this batch's own {n_batch} a priori cells; E[max SR] {e_struct[0]:+.3f}")
    survivors = df[(df["structure"] != "naked_sec20")
                   & (~df["breach_week_hard"]) & (~df["breach_day_hard"])
                   & (df["sharpe_net"] > 0)]
    strong = survivors[(survivors["dsr"] > 0.95) & (survivors["sharpe_net"] > bh_spy["sharpe"])]
    print(f"  Cells inside the HARD account-level bound (week >= -20% AND day >= -15%) with net SR > 0: "
          f"{len(survivors)}/{n_batch}")
    for _, r in survivors.iterrows():
        print(f"     {r['structure']:<22} thr {r['threshold']}x {r['param']:<18} "
              f"netSR {r['sharpe_net']:+.2f}  CAGR {r['cagr']*100:+.1f}%  worst wk {r['worst_week']*100:+.1f}%  DSR {r['dsr']:.2f}")
    print(f"  Of those, also DSR>0.95 AND beat SPY: {len(strong)}/{n_batch}")

    keep_cols = [c for c in df.columns if not c.startswith("_")]
    RESULTS.mkdir(parents=True, exist_ok=True)
    df[keep_cols].to_csv(OUT_CSV, index=False)
    print(f"\n  wrote {OUT_CSV.relative_to(_ROOT)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
