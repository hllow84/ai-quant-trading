#!/usr/bin/env python3
"""
run_orb_entry_filters.py  --  STATE_OF_PLAY section 10 follow-up.

Section 10 killed the plain Opening Range Breakout (09:30 ET cash open) and
sections 10.1-10.4 confirmed the kill is real (implementation audit; moderate
stop; daily-SMA trend filter -- all 0 survivors). This script tests TWO MORE
entry filters, EACH SEPARATELY (never combined), and reports each one on the
SAME table as the unfiltered baseline so the effect of the filter is directly
visible:

  FILTER 2  RETEST ENTRY
    Price breaks the opening range, then must pull back to within 10% of the
    OR's own width of the broken level, WITHIN THE SAME SESSION. If instead a
    bar closes back through the broken level first, the setup is CANCELLED for
    the day -- NO fallback to an immediate entry, no trade that day. Entry on a
    good retest is a limit fill at the broken OR level, so the stop (opposite
    OR side) and 1R are IDENTICAL to the baseline -- only trade selection and
    entry timing change.

  FILTER 5  DIRECTIONAL MOVEMENT (+DI / -DI)
    Standard Wilder 14-period DMI, computed on the SESSION (daily) bars and
    shifted one session so it is strictly causal. Long breaks taken only when
    +DI > -DI on the prior session; shorts only when -DI > +DI; otherwise NO
    trade that day. (A 14-minute intrabar DMI is noise and using the breakout
    session's own bar would be look-ahead -- so "at the moment of breakout" is
    read as the prevailing daily DMI state, exactly as section 10.4 read the
    trend filter.)

INSTRUMENTS -- every one with M1 on disk, plus a one-off BTCUSDT M1 pull
  XAUUSD  2018-2025          (data/XAUUSD_M1_2018_2025_spot_dukascopy.csv)
  NAS100  2018-2025 + 2013-2017 out-of-regime (M1RTH)
  US30    2018-2025 + 2013-2017 out-of-regime (M1RTH)
  BTCUSDT 2018-2025          (data/BTCUSDT_M1_2018_2025_binance.csv,
                              scripts/download_btcusdt_m1_binance.py)
  There is NO pre-2018 out-of-regime window for XAUUSD (no pre-2018 M1) or for
  BTCUSDT (Binance history starts 2017-08; no pre-crypto-derivatives regime at
  any resolution). Stated, not hidden.

CRYPTO SESSION SEMANTICS (24/7) -- the repo's EXISTING convention, not invented
  run_sweep_crypto.py already defines the crypto trading day by resample("1D")
  on UTC timestamps, i.e. the day boundary is 00:00 UTC. So for BTCUSDT:
    "opening range" = first 15 / 30 minutes after 00:00 UTC
    "session close" = the 23:59 UTC bar (force-flat there, no overnight -- which
                      for 24/7 crypto just means no position carried across the
                      UTC date line)
  Binance M1 bars are close-stamped; they are shifted -1 minute at load so they
  are open-stamped like the Dukascopy files the ORB code was written against.

RISK MANAGEMENT -- explicit, taken from research/ftmo_engine.py, not assumed
  * Fixed fractional, RISK_PER_TRADE = 1.00% of account equity per trade
    (ftmo_engine.RISK_PER_TRADE = 0.01 -- confirmed, this is the real number).
  * Stop = the opposite side of the opening range (stop_mode='or_range', the
    section-10.1 audited default). 1R = the OR width. UNCHANGED by either filter.
  * Targets: 1R, 2R, and hold-to-session-close with the stop live.
  * ONE position per instrument per day, no pyramiding (first break wins; the
    de_overlap pass also enforces one position at a time).

COSTS -- each instrument keeps the cost model of its existing sections
  XAUUSD  : engine LEGACY $/oz model (cost_bps=None) -- real per-bar spread +
            $0.03/$0.10 per-side slippage + $0.07/oz commission (run_sweep_m1.py
            section 11). NOTE, stated: the engine's news-hour slippage window
            ends 14:30 UTC, so a winter (EST) 09:30 ET = 14:30 UTC entry is
            charged NORMAL, not news, slippage. Reported, not worked around.
  NAS100 /
  US30    : the section-10 ORB model -- real per-bar spread + 0.35 bps
            commission + ET-ANCHORED slippage 1.00 bps/side 09:30-10:30 ET,
            0.15 bps/side after (run_orb.slip_bps).
  BTCUSDT : the section-13 crypto model -- 20 bps round-turn Binance taker fee
            (dominant) + real(=negligible, ~0.0013 bps) spread + 1-2 bps/side
            slippage (run_sweep_crypto.CRYPTO_COST_BPS).

HONESTY GATES (all reported per row)
  look-ahead guard (statistical, on the gated position series) + an explicit
  no-entry-before-the-OR-is-complete assertion ; gross PF > 1 ; net PF > 1 and
  net Sharpe > 0 ; DSR > 0.95 vs this batch's own a-priori structural pool
  (cumulative-N contrast printed too) ; OOS holds across the fixed split ;
  single-year net-R concentration <= 60% ; beats buy-and-hold. Any config with
  < 30 trades is flagged THIN inline -- its PF / win rate are not to be trusted.

Usage:  py -3.14 run_orb_entry_filters.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro
from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from strategies.orb import orb, rth_m1, wilder_dmi_direction, ET

BARS_PER_YEAR = 252
DSR_BAR = 0.95
CONC_BAR = 0.60
MIN_OOS_TRADES = 20
THIN = 30                     # < 30 trades -> sample too small to trust
PRIOR_TRIALS = 946           # STATE_OF_PLAY, cumulative through section 23

CRYPTO_COST_BPS = dict(commission=20.0, slip_normal=1.0, slip_news=2.0)

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
UTC_SESSION = dict(session_tz="UTC", open_min=0, close_min=1440, min_sess_bars=1200)

OR_MINUTES = (15, 30)
TARGETS = ("1R", "2R", "close")
VARIANTS = ("ORIGINAL", "RETEST", "DI")

RESULTS = _ROOT / "results"
OUT_CSV = RESULTS / "orb_entry_filters.csv"


# ── instrument table ─────────────────────────────────────────────────────────
def _inst_table():
    d = _ROOT / "data"
    return {
        "XAUUSD": dict(
            kind="dukas", session=ET_SESSION, cost_bps=None, slip_fn=None,
            windows={"in": (d / "XAUUSD_M1_2018_2025_spot_dukascopy.csv",
                            pd.Timestamp("2023-01-01", tz="UTC"))}),
        "NAS100": dict(
            kind="dukas", session=ET_SESSION, cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
            windows={"in": (d / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
                            pd.Timestamp("2023-01-01", tz="UTC")),
                     "out": (d / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv",
                             pd.Timestamp("2016-01-01", tz="UTC"))}),
        "US30": dict(
            kind="dukas", session=ET_SESSION, cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
            windows={"in": (d / "US30_M1_2018_2025_cfd_dukascopy.csv",
                            pd.Timestamp("2023-01-01", tz="UTC")),
                     "out": (d / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",
                             pd.Timestamp("2016-01-01", tz="UTC"))}),
        "BTCUSDT": dict(
            kind="crypto", session=UTC_SESSION, cost_bps=CRYPTO_COST_BPS, slip_fn=None,
            windows={"in": (d / "BTCUSDT_M1_2018_2025_binance.csv",
                            pd.Timestamp("2023-01-01", tz="UTC"))}),
    }


def load_instrument(kind: str, path: Path):
    """Return (m1_mid frame with mid_open/high/low/close+spread+volume, daily_index, bh_dict)."""
    if kind == "crypto":
        df = pd.read_csv(path)
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True, format="ISO8601")
        df = df.set_index("datetime_utc").sort_index()
        df.index = df.index - pd.Timedelta(minutes=1)   # close-stamped -> open-stamped
        m1 = df[["mid_open", "mid_high", "mid_low", "mid_close", "spread", "volume"]].copy()
        daily_index = pd.date_range(m1.index[0].normalize(), m1.index[-1].normalize(),
                                    freq="D", tz="UTC")
        close = m1["mid_close"].resample("1D").last().dropna()
        ret = close.pct_change().dropna()
        entry_cost = float(m1["spread"].iloc[0] / m1["mid_close"].iloc[0])
        eq = (1 + ret).cumprod() * (1 - entry_cost)
        bh = dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))
        return m1, daily_index, bh

    spot = load_m1_spot(path)
    daily = aggregate_daily(spot)
    m1 = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m1["spread"] = spot["spread"]
    m1["volume"] = spot["volume"]
    return m1, daily.index, ro.buy_and_hold(daily)


# ── scoring (mirrors run_orb.score, filter-aware) ────────────────────────────
def score_cands(m1, cands, cost_bps, slip_fn, split, daily_index, or_minutes, open_min):
    if not cands:
        return dict(n_trades=0, guard="N/A", n_cands=0), pd.DataFrame()

    ent = pd.DatetimeIndex([c["entry_time"] for c in cands])
    # explicit no-entry-before-the-OR-completes assertion, in the session tz
    sess_min = (ent.tz_convert(ET_SESSION["session_tz"]) if open_min else ent.tz_convert("UTC"))
    emin = sess_min.hour * 60 + sess_min.minute
    or_ok = bool((emin >= open_min + or_minutes).all())

    trades = de_overlap(simulate_trades(m1, cands, strictly_after=False,
                                        cost_bps=cost_bps, slip_bps_fn=slip_fn))
    if trades.empty:
        return dict(n_trades=0, guard="N/A", n_cands=len(cands)), trades

    pos = build_position_series(trades, m1.index)
    try:
        guard_look_ahead(pos, m1["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS" if or_ok else "FAIL:OR-window"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:32]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < split, exit_t >= split

    def _pf(m):
        return profit_factor(trades.loc[m, "net_R"]) if m.any() else float("nan")

    def _sr(m):
        sub = trades.loc[m]
        if sub.empty:
            return float("nan")
        dd = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(dd, BARS_PER_YEAR) if len(dd) > 1 else float("nan")

    yr = exit_t.dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    tot = float(agg.sum())
    top_share = (float(agg.max()) / tot) if tot > 0 else float("nan")

    return dict(
        n_cands=len(cands), n_trades=len(trades), guard=guard,
        n_long=int((trades["side"] == "long").sum()),
        n_short=int((trades["side"] == "short").sum()),
        gross_pf=profit_factor(trades["gross_R"]),
        net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_total=float(trades["net_R"].sum()),
        win_rate=float((trades["net_R"] > 0).mean()),
        risk_med_bps=float((trades["risk_price"] / trades["entry_mid"]).median() * 1e4),
        n_obs=int(len(daily_ret)),
        is_trades=int(is_m.sum()), oos_trades=int(oos_m.sum()),
        is_pf=_pf(is_m), oos_pf=_pf(oos_m), is_sharpe=_sr(is_m), oos_sharpe=_sr(oos_m),
        top_year_share=top_share, n_years=int(len(agg)), n_pos_years=int((agg > 0).sum()),
    ), trades


def run_window(name, inst, win_key):
    path, split = inst["windows"][win_key]
    if not path.exists():
        print(f"  [{name} {win_key}] MISSING {path.name} -- skipped", flush=True)
        return []
    print(f"\n[{name} {win_key}] loading {path.name} ...", flush=True)
    m1, daily_index, bh = load_instrument(inst["kind"], path)
    sess = inst["session"]
    print(f"  {len(m1):,} M1 bars {m1.index[0].date()} -> {m1.index[-1].date()} | "
          f"B&H SR {bh['sharpe']:+.2f} maxDD {bh['max_dd']*100:.1f}%", flush=True)

    rth = rth_m1(m1, sess["session_tz"], sess["open_min"], sess["close_min"])
    di = wilder_dmi_direction(rth, 14)
    di_cov = float(np.isfinite(di).mean())
    print(f"  DMI(14) daily direction available on {di_cov*100:.0f}% of sessions "
          f"(+DI>-DI on {float((di > 0).mean())*100:.0f}%)", flush=True)

    rows = []
    for n_or in OR_MINUTES:
        for tgt in TARGETS:
            p = dict(or_minutes=n_or, target=tgt, stop_mode="or_range")
            variant_cands = {
                "ORIGINAL": orb(m1, p, **sess),
                "RETEST":   orb(m1, p, retest=True, retest_tol_frac=0.10, **sess),
                "DI":       orb(m1, p, di_dir=di, **sess),
            }
            for variant, cands in variant_cands.items():
                res, _ = score_cands(m1, cands, inst["cost_bps"], inst["slip_fn"],
                                     split, daily_index, n_or, sess["open_min"])
                rows.append(dict(instrument=name, window=win_key, variant=variant,
                                 or_minutes=n_or, target=tgt,
                                 bh_sharpe=bh["sharpe"], bh_max_dd=bh["max_dd"],
                                 split=str(split.date()), **res))
                print(f"    {variant:<8} OR{n_or:>2} {tgt:<5} "
                      f"n={res.get('n_trades', 0):>4} "
                      f"grPF={res.get('gross_pf', float('nan')):.3f} "
                      f"netPF={res.get('net_pf', float('nan')):.3f} "
                      f"SR={res.get('sharpe', float('nan')):+.2f} "
                      f"{('THIN' if 0 < res.get('n_trades', 0) < THIN else '')}", flush=True)
    return rows


def main():
    table = _inst_table()
    all_rows = []
    for name, inst in table.items():
        for win_key in inst["windows"]:
            all_rows.extend(run_window(name, inst, win_key))

    df = pd.DataFrame(all_rows)
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    analyze(df)


def _new_trial_count(df):
    """Genuinely NEW configs this batch: every RETEST/DI cell, plus the ORIGINAL
    cells for instruments ORB has never been run on (XAUUSD, BTCUSDT). The
    NAS100/US30 ORIGINAL cells reproduce section 10 and are already counted."""
    traded = df[df["n_trades"].fillna(0) > 0]
    filt = traded[traded["variant"] != "ORIGINAL"]
    new_orig = traded[(traded["variant"] == "ORIGINAL")
                      & (traded["instrument"].isin(["XAUUSD", "BTCUSDT"]))]
    return len(filt) + len(new_orig), len(filt), len(new_orig)


def analyze(df):
    traded = df[df["n_trades"].fillna(0) > 0].copy()
    if traded.empty:
        print("\nNO config produced a trade.")
        return

    # ---- DSR: structural pool = this batch's own a-priori filter cells, per window ----
    n_new, n_filt, n_new_orig = _new_trial_count(df)
    cumulative = PRIOR_TRIALS + n_new

    def dsr_row(r, pool):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4 or len(pool) < 2:
            return np.nan
        return deflated_sharpe(sr_best=float(r["sharpe"]), sr_trials=np.asarray(pool),
                               n_obs=int(r["n_obs"]),
                               skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                               excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0
                               )["dsr"]

    traded["dsr"] = np.nan
    pools = {}
    for wk, g in traded.groupby("window"):
        pool = g.loc[g["variant"] != "ORIGINAL", "sharpe"].fillna(0.0).to_numpy()
        pools[wk] = pool
        traded.loc[g.index, "dsr"] = g.apply(lambda r: dsr_row(r, pool), axis=1)

    cum_pool = np.concatenate([p for p in pools.values()]) if pools else np.array([])

    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES) & (traded["oos_sharpe"] > 0))
    traded["not_conc"] = (traded["top_year_share"].notna() & (traded["top_year_share"] <= CONC_BAR))
    traded["beats_bh"] = traded["sharpe"] > traded["bh_sharpe"]
    traded["thin"] = traded["n_trades"] < THIN
    traded["SURVIVOR"] = ((traded["guard"] == "PASS") & (traded["gross_pf"] > 1.0)
                          & (traded["net_pf"] > 1.0) & (traded["sharpe"] > 0)
                          & (traded["dsr"] > DSR_BAR) & traded["oos_holds"]
                          & traded["not_conc"] & traded["beats_bh"] & ~traded["thin"])

    W = 150
    print("\n" + "=" * W)
    print("  ORB ENTRY-FILTER TEST  --  filter 2 (RETEST) and filter 5 (DI), EACH SEPARATELY, vs the unfiltered baseline")
    print("=" * W)
    print("  RISK PARAMETERS (exact, from research/ftmo_engine.py):")
    print("    - fixed fractional, 1.00% of account equity risked per trade (RISK_PER_TRADE = 0.01)")
    print("    - stop = opposite side of the opening range; 1R = the OR width; UNCHANGED by either filter")
    print("    - targets: 1R, 2R, hold-to-session-close (stop live); ONE position per instrument per day, no pyramiding")
    print("  RETEST definition: after the first break, price must return to within 10% of the OR width of the broken")
    print("    level, within the SAME session; if a bar CLOSES back through the level first the day is CANCELLED")
    print("    (no immediate-entry fallback, no trade). Entry = limit fill at the broken OR level.")
    print("  DI definition: Wilder 14-period DMI on the SESSION (daily) bars, shifted 1 session (causal). Long only")
    print("    if +DI > -DI on the prior session, short only if -DI > +DI, else no trade.")
    print("  SESSION: US instruments = 09:30-16:00 America/New_York (per-bar DST-correct). BTCUSDT = 00:00-23:59 UTC")
    print("    (repo's existing crypto day boundary); 'session close' = the 23:59 UTC bar.")
    print(f"  COSTS: XAUUSD legacy $/oz | NAS100/US30 spread+0.35bps+ET-anchored slip 1.00/0.15 | BTCUSDT 20bps taker+slip")
    print(f"  NEW TRIALS THIS BATCH: {n_new}  ({n_filt} filter cells + {n_new_orig} first-time ORIGINAL cells for XAUUSD/BTCUSDT;")
    print(f"    NAS100/US30 ORIGINAL cells reproduce section 10 and are NOT re-counted)")
    print(f"  CUMULATIVE PROJECT TRIALS (DSR N): {PRIOR_TRIALS} + {n_new} = {cumulative}")
    for wk, pool in pools.items():
        if len(pool):
            e = expected_max_sharpe(pool)
            print(f"  DSR structural pool [{wk}] = {len(pool)} filter cells -> E[max SR] {e[0]:+.3f} "
                  f"(mu {e[2]:+.3f}, sd {e[3]:.3f})")
    print(f"  Gates: guard PASS + grossPF>1 + netPF>1 + SR>0 + DSR>{DSR_BAR} + OOS holds + top-year<={CONC_BAR:.0%} + beats B&H")
    print(f"  THIN = < {THIN} trades: PF / win rate NOT trustworthy, flagged inline, cannot be a SURVIVOR")
    print("=" * W)

    hdr = (f"  {'instrument':>9} {'window':>4} {'OR':>3} {'target':>6} {'variant':>8} "
           f"{'n':>5} {'grPF':>6} {'netPF':>6} {'SR':>6} {'DSR':>5} {'maxDD':>6} {'win%':>5} "
           f"{'costR%':>7} {'topYr%':>6} {'OOS':>4} {'B&H':>4} {'flags':>13}")
    for wk in ["in", "out"]:
        sub = traded[traded["window"] == wk]
        if sub.empty:
            continue
        print(f"\n  --- {'IN-REGIME 2018-2025' if wk == 'in' else 'OUT-OF-REGIME 2013-2017 (NAS100/US30 only)'} ---")
        print(hdr)
        print("  " + "-" * (W - 4))
        for (name, n_or, tgt), grp in sub.groupby(["instrument", "or_minutes", "target"]):
            for variant in VARIANTS:
                r = grp[grp["variant"] == variant]
                if r.empty:
                    continue
                r = r.iloc[0]
                flags = []
                if r["thin"]:
                    flags.append("THIN")
                if r["SURVIVOR"]:
                    flags.append("SURV")
                ts = r["top_year_share"]
                print(f"  {name:>9} {wk:>4} {int(r['or_minutes']):>3} {tgt:>6} {variant:>8} "
                      f"{int(r['n_trades']):>5} {r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} "
                      f"{r['sharpe']:>+6.2f} {r['dsr']:>5.2f} {r['max_dd']*100:>5.1f}% "
                      f"{r['win_rate']*100:>4.1f}% {r['cost_R_mean']*100:>6.1f}% "
                      + (f"{ts*100:>5.0f}%" if np.isfinite(ts) else f"{'n/a':>6}")
                      + f" {'yes' if r['oos_holds'] else 'no':>4} "
                      f"{'BEAT' if r['beats_bh'] else 'lose':>4} {','.join(flags):>13}")
            print("  " + "." * (W - 4))

    # ---- verdict ----
    print("\n" + "=" * W)
    print("  VERDICT")
    print("=" * W)
    surv = traded[traded["SURVIVOR"]]
    if len(surv):
        print(f"  {len(surv)} config(s) clear EVERY gate:")
        for _, r in surv.iterrows():
            print(f"    {r['instrument']} {r['window']} OR{int(r['or_minutes'])} {r['target']} "
                  f"[{r['variant']}]  SR {r['sharpe']:+.2f} DSR {r['dsr']:.3f} "
                  f"grPF {r['gross_pf']:.3f} netPF {r['net_pf']:.3f} topYr {r['top_year_share']*100:.0f}%")
    else:
        print("  NO config clears every gate -- on EITHER filter, on ANY instrument, in ANY window.\n")
        for filt in ("RETEST", "DI"):
            sub = traded[(traded["variant"] == filt) & (~traded["thin"])]
            if sub.empty:
                sub = traded[traded["variant"] == filt]
                note = " (all cells THIN -- nothing with a trustworthy sample)"
            else:
                note = ""
            best = sub.sort_values("sharpe", ascending=False).iloc[0]
            gates = {
                "guard PASS": best["guard"] == "PASS",
                "grossPF>1": best["gross_pf"] > 1,
                "netPF>1": best["net_pf"] > 1,
                "SR>0": best["sharpe"] > 0,
                f"DSR>{DSR_BAR}": bool(best["dsr"] > DSR_BAR),
                "OOS holds": bool(best["oos_holds"]),
                f"top-year<={CONC_BAR:.0%}": bool(best["not_conc"]),
                "beats B&H": bool(best["beats_bh"]),
            }
            failed = [g for g, ok in gates.items() if not ok]
            print(f"  {filt}: closest cell{note} = {best['instrument']} {best['window']} "
                  f"OR{int(best['or_minutes'])} {best['target']}")
            print(f"     SR {best['sharpe']:+.2f} | grossPF {best['gross_pf']:.3f} | netPF {best['net_pf']:.3f} "
                  f"| DSR {best['dsr']:.3f} | cost {best['cost_R_mean']*100:.1f}% of 1R | "
                  f"top-year {best['top_year_share']*100:.0f}%" if np.isfinite(best['top_year_share'])
                  else f"     SR {best['sharpe']:+.2f} | grossPF {best['gross_pf']:.3f} | netPF {best['net_pf']:.3f}")
            print(f"     FAILS: {', '.join(failed) if failed else '(passes listed gates but is THIN)'}")
            # vs its own baseline
            base = traded[(traded["variant"] == "ORIGINAL") & (traded["instrument"] == best["instrument"])
                          & (traded["window"] == best["window"]) & (traded["or_minutes"] == best["or_minutes"])
                          & (traded["target"] == best["target"])]
            if not base.empty:
                b = base.iloc[0]
                print(f"     vs baseline same cell: grossPF {b['gross_pf']:.3f} netPF {b['net_pf']:.3f} "
                      f"SR {b['sharpe']:+.2f} n={int(b['n_trades'])}  ->  filter effect: "
                      f"netPF {best['net_pf']-b['net_pf']:+.3f}, SR {best['sharpe']-b['sharpe']:+.2f}, "
                      f"n {int(best['n_trades'])-int(b['n_trades']):+d}")
            print()

    # ---- batch summary ----
    print("  Batch summary (traded cells only):")
    for variant in VARIANTS:
        s = traded[traded["variant"] == variant]
        if s.empty:
            continue
        print(f"    {variant:>8}: {len(s):>2} cells | guard {int((s['guard']=='PASS').sum())}/{len(s)} "
              f"| grossPF>1 {int((s['gross_pf']>1).sum())}/{len(s)} "
              f"| netPF>1 {int((s['net_pf']>1).sum())}/{len(s)} "
              f"| SR>0 {int((s['sharpe']>0).sum())}/{len(s)} "
              f"| DSR>{DSR_BAR} {int((s['dsr']>DSR_BAR).sum())}/{len(s)} "
              f"| OOS {int(s['oos_holds'].sum())}/{len(s)} "
              f"| not-conc {int(s['not_conc'].sum())}/{len(s)} "
              f"| beats-B&H {int(s['beats_bh'].sum())}/{len(s)} "
              f"| THIN {int(s['thin'].sum())}/{len(s)} "
              f"| SURVIVORS {int(s['SURVIVOR'].sum())}/{len(s)}")
    print(f"\n  results -> {OUT_CSV}")
    traded.to_csv(RESULTS / "orb_entry_filters_scored.csv", index=False)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
