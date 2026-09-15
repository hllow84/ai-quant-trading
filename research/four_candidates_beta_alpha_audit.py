#!/usr/bin/env python3
"""
SECTION 33 -- BETA/ALPHA DECOMPOSITION + LONG/SHORT EXPOSURE AUDIT +
RESTRICTED 4-STRATEGY ENSEMBLE, for the project's 4 "real candidate"
strategies.

NAME RECONCILIATION (stated plainly, not silently assumed): the brief
named these 4 by short nicknames that don't exactly match any single
saved series name. Resolved as follows, and this mapping is the one
material judgment call in this task:

  1. "on-chain BTC H=20"    -> D|On-chain active-address surge H20 (BTCUSDT)
                                Exact match, section 30. Already in
                                results/ensemble_daily_returns.csv.
  2. "gold-silver pairs"    -> C|Pairs GLD-SLV N1.5 (the N1.5, tighter/more
                                active threshold; N2.0 also exists in the
                                inventory and is not used here -- flagged,
                                not silently merged). Already in
                                results/ensemble_daily_returns.csv.
  3. "capped vol spread"    -> D|Credit-spread FILTERED 1pct (SPY), section
                                27/31. Reasoning: "capped" = defined-risk
                                credit SPREAD (bounded max loss, literally
                                the point of section 27's redesign) run at
                                a 1pct-of-spot fixed-fraction cap; "vol" =
                                the IV-rank/VIX filter gating entries. This
                                is a materially better textual match than
                                the VRP family (which is "vol-of-vol" and
                                "naked", not "capped"). Already in
                                results/ensemble_daily_returns.csv.
  4. "ORB gold RETEST"      -> RETEST OR30/1R, XAUUSD, continuous 2017-2025
                                (research/report_retest_xauusd_2017_2025_continuous.py).
                                This one is NOT in the 64-series ensemble
                                inventory -- it was never extracted into
                                ensemble_daily_returns.csv. Re-extracted
                                fresh here using the SAME functions that
                                script already calls (build_trades,
                                build_daily_returns), not re-implemented.

PART 1: CAPM-style regression of each candidate's daily returns against
BTC's daily returns (the market benchmark named in the brief), OLS,
over each candidate's own real overlap with BTC's own real data range
(BTC spot only exists from 2017-08-17 in this project's data -- stated,
not silently extended). Beta = slope, annualized alpha = intercept
compounded at the series' own 365-day calendar-grid convention.

PART 2: long/short exposure, read from each strategy's own real trade/
position data (not inferred).

PART 3: restricted 4-strategy ensemble using ONLY these 4 series,
pairwise-available equal-weighting (no zero-fill), 0.6 correlation-pruning
rule applied explicitly.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "research"))

import numpy as np
import pandas as pd

import ensemble_correlation as ec
from research.dsr import deflated_sharpe
from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, build_position_series
from strategies.orb import orb, ET

RESULTS = _ROOT / "results"
DATA = _ROOT / "data"
CORR_PRUNE_THRESHOLD = 0.60  # stated a priori per the brief


# ─────────────────────── build ORB gold RETEST fresh ───────────────────────

def build_orb_gold_retest() -> tuple[pd.Series, pd.DataFrame]:
    """Byte-identical logic to report_retest_xauusd_2017_2025_continuous.py:
    RETEST OR30/1R, XAUUSD, one continuous M1 frame 2017-01-02..2025-12-31.
    Returns (daily_ret, trades_df) -- trades_df carries the 'side' column
    needed for the Part-2 long/short audit."""
    ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
    PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

    def mid_frame(path):
        spot = load_m1_spot(path)
        m = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m["spread"] = spot["spread"]
        m["volume"] = spot["volume"]
        return m, spot

    m17, spot17 = mid_frame(DATA / "XAUUSD_M1_2017_spot_dukascopy.csv")
    m18, spot18 = mid_frame(DATA / "XAUUSD_M1_2018_2025_spot_dukascopy.csv")
    m = pd.concat([m17, m18]).sort_index()
    spot = pd.concat([spot17, spot18]).sort_index()
    assert m.index.is_monotonic_increasing and not m.index.has_duplicates
    daily_index = aggregate_daily(spot).index

    cands = orb(m, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    tr = de_overlap(simulate_trades(m, cands, strictly_after=False, cost_bps=None, slip_bps_fn=None))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    tr = tr.sort_values("exit_time").reset_index(drop=True)

    pos = build_position_series(tr, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:80]}"
    print(f"  [ORB gold RETEST] look-ahead guard: {guard}, {len(tr)} trades, "
          f"{tr['entry_time'].min()} .. {tr['exit_time'].max()}")

    daily_ret = build_daily_returns(tr, daily_index)
    return ec.to_calendar_grid(daily_ret), tr


# ─────────────────────── BTC daily benchmark ───────────────────────

def build_btc_benchmark() -> pd.Series:
    m1 = pd.read_csv(DATA / "BTCUSDT_M1_2017_2025_binance.csv", parse_dates=["datetime_utc"])
    m1 = m1.set_index("datetime_utc").sort_index()
    daily_close = m1["mid_close"].resample("1D").last().dropna()
    ret = daily_close.pct_change().dropna()
    ret.index = pd.DatetimeIndex(ret.index).tz_localize(None)
    return ret.rename("BTC")


# ─────────────────────── CAPM regression ───────────────────────

def capm(strategy_ret: pd.Series, btc_ret: pd.Series, ann_factor: int = 365) -> dict:
    df = pd.concat([strategy_ret.rename("y"), btc_ret.rename("x")], axis=1).dropna()
    n = len(df)
    if n < 60:
        return dict(n=n, beta=float("nan"), alpha_daily=float("nan"), alpha_ann=float("nan"), r2=float("nan"),
                    first=None, last=None)
    x = df["x"].to_numpy()
    y = df["y"].to_numpy()
    X = np.column_stack([np.ones(n), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    alpha_daily, beta = coef[0], coef[1]
    y_hat = X @ coef
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    alpha_ann = (1.0 + alpha_daily) ** ann_factor - 1.0
    return dict(n=n, beta=float(beta), alpha_daily=float(alpha_daily), alpha_ann=float(alpha_ann),
                r2=float(r2), first=str(df.index.min().date()), last=str(df.index.max().date()))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 112
    print("=" * W)
    print("  SECTION 33 -- BETA/ALPHA DECOMPOSITION + LONG/SHORT AUDIT + RESTRICTED 4-STRATEGY ENSEMBLE")
    print("=" * W)

    frame_all = pd.read_csv(RESULTS / "ensemble_daily_returns.csv", index_col=0, parse_dates=True)

    print("\nBuilding ORB gold RETEST fresh (not in the 64-series ensemble file -- new extraction)...")
    orb_ret, orb_trades = build_orb_gold_retest()

    print("Building BTC daily benchmark (Binance M1 spot, 2017-08-17 onward)...")
    btc_ret = build_btc_benchmark()
    print(f"  BTC benchmark real range: {btc_ret.index.min().date()} .. {btc_ret.index.max().date()}, "
          f"{len(btc_ret):,} days")

    series = {
        "ORB gold RETEST (XAUUSD, RETEST OR30/1R)": orb_ret,
        "On-chain BTC H=20": frame_all["D|On-chain active-address surge H20 (BTCUSDT)"],
        "Capped vol spread (Credit-spread FILTERED 1pct, SPY)": frame_all["D|Credit-spread FILTERED 1pct (SPY)"],
        "Gold-silver pairs (GLD-SLV N1.5)": frame_all["C|Pairs GLD-SLV N1.5"],
    }
    for name, s in series.items():
        s2 = s.dropna()
        print(f"  {name}: {s2.index.min().date()} .. {s2.index.max().date()}, {len(s2):,} real days")

    # ═════════════════════ PART 1 -- CAPM ═════════════════════
    print("\n" + "=" * W)
    print("  PART 1 -- BETA/ALPHA DECOMPOSITION vs BTC (OLS, real-overlap only)")
    print("=" * W)
    capm_rows = []
    for name, s in series.items():
        res = capm(s, btc_ret)
        low_beta = abs(res["beta"]) < 0.15 if np.isfinite(res["beta"]) else False
        pos_alpha = res["alpha_ann"] > 0 if np.isfinite(res["alpha_ann"]) else False
        verdict = ("LOW-BETA + POSITIVE-ALPHA (real, market-independent skill)" if low_beta and pos_alpha else
                    "market-explained / beta-driven" if not low_beta and res["beta"] * res["alpha_ann"] >= 0 else
                    "mixed -- flagged, read the numbers")
        print(f"\n  {name}")
        print(f"    overlap with BTC benchmark: {res['first']} .. {res['last']}  (n={res['n']} real days)")
        print(f"    beta={res['beta']:+.4f}   alpha(daily)={res['alpha_daily']:+.6f}   "
              f"alpha(annualized)={res['alpha_ann']*100:+.2f}%   R^2={res['r2']:.4f}")
        print(f"    VERDICT: {verdict}")
        capm_rows.append(dict(strategy=name, **res, verdict=verdict))
    pd.DataFrame(capm_rows).to_csv(RESULTS / "four_candidates_capm.csv", index=False)

    # ═════════════════════ PART 2 -- long/short exposure ═════════════════════
    print("\n" + "=" * W)
    print("  PART 2 -- LONG/SHORT EXPOSURE AUDIT (read from each strategy's own real trade/position data)")
    print("=" * W)
    exposure_rows = []

    # ORB gold RETEST
    side_counts = orb_trades["side"].value_counts()
    n_long, n_short = int(side_counts.get("long", 0)), int(side_counts.get("short", 0))
    n_tot = n_long + n_short
    print(f"\n  ORB gold RETEST: {n_tot} trades, LONG {n_long} ({100*n_long/n_tot:.1f}%), "
          f"SHORT {n_short} ({100*n_short/n_tot:.1f}%) -- takes BOTH sides, directional breakout, "
          f"not structurally biased long by construction (whichever side of the opening range breaks first).")
    exposure_rows.append(dict(strategy="ORB gold RETEST", structure="directional breakout, both sides",
                               pct_long=100*n_long/n_tot, pct_short=100*n_short/n_tot, n_trades=n_tot))

    # On-chain BTC H=20 -- verified from source, not just cited
    print(f"\n  On-chain BTC H=20: LONG-ONLY by construction (verified in run_onchain_signal.py -- entries "
          f"trigger only on z > ADDR_Z_THRESHOLD, no short branch exists in the trade-building loop; "
          f"section 30's own docstring states this a priori). 100% long when in a position, 0% short, "
          f"flat the rest of the time (no_pos gate).")
    exposure_rows.append(dict(strategy="On-chain BTC H=20", structure="long-only (verified in source)",
                               pct_long=100.0, pct_short=0.0, n_trades=None))

    # Capped vol spread (credit-spread FILTERED 1pct)
    import research.credit_spread_iv_filter as cs
    from research.delta10_iv_filter import load_data, IV_LOOKBACK, TOP_TERCILE
    df_cs = load_data()
    iv_rank = df_cs["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible_filtered = (iv_rank >= TOP_TERCILE).fillna(False)
    pooled_trades, _, _, _, _ = cs.run_combined_book(df_cs, eligible_filtered, "FILTERED", cs.WIDTH_PCTS["1pct"])
    n_put = int((pooled_trades["opt_type"] == "put").sum())
    n_call = int((pooled_trades["opt_type"] == "call").sum())
    n_cs = n_put + n_call
    print(f"\n  Capped vol spread (Credit-spread FILTERED 1pct): {n_cs} trades, "
          f"PUT-CREDIT-SPREAD (bull-put, bullish-tilted short-vol) {n_put} ({100*n_put/n_cs:.1f}%), "
          f"CALL-CREDIT-SPREAD (bear-call, bearish-tilted short-vol) {n_call} ({100*n_call/n_cs:.1f}%) -- "
          f"BOTH books run concurrently with shared capital, approximating a short-strangle/short-vol "
          f"structure. This is NOT a simple long or short directional bet -- it profits from range-bound "
          f"markets and is hurt by large moves in EITHER direction, though the two legs' deltas are not "
          f"guaranteed to net to exactly zero on any given day.")
    exposure_rows.append(dict(strategy="Capped vol spread (Credit-spread FILTERED 1pct)",
                               structure="short-vol, both bull-put + bear-call books concurrent",
                               pct_long=100*n_put/n_cs, pct_short=100*n_call/n_cs, n_trades=n_cs))

    # Gold-silver pairs
    import research.strat_pairs as sp
    df_pairs = sp.build_pair_frame("GLD", "SLV")
    log_ratio = np.log(df_pairs["close_a"]) - np.log(df_pairs["close_b"])
    roll_mean = log_ratio.rolling(sp.ROLL_WINDOW).mean().shift(1)
    roll_std = log_ratio.rolling(sp.ROLL_WINDOW).std().shift(1)
    z = (log_ratio - roll_mean) / roll_std
    N = 1.5
    pos = pd.Series(0, index=df_pairs.index, dtype=int)
    state = 0
    for i in range(len(df_pairs)):
        zv = z.iloc[i]
        if not np.isfinite(zv):
            pos.iloc[i] = 0
            continue
        if state == 0:
            if zv >= N:
                state = -1
            elif zv <= -N:
                state = 1
        else:
            if abs(zv) <= sp.EXIT_BAND or abs(zv) >= N + sp.STOP_EXTRA:
                state = 0
        pos.iloc[i] = state
    pct_long_gld = 100 * (pos == 1).sum() / len(pos)
    pct_short_gld = 100 * (pos == -1).sum() / len(pos)
    pct_flat = 100 * (pos == 0).sum() / len(pos)
    print(f"\n  Gold-silver pairs (N1.5): dollar-neutral pairs trade -- when in a position it is ALWAYS "
          f"simultaneously long one leg and short the other (0.5x each, gross exposure 1x). Time in "
          f"long-GLD/short-SLV: {pct_long_gld:.1f}%, short-GLD/long-SLV: {pct_short_gld:.1f}%, flat: "
          f"{pct_flat:.1f}%. Structurally market-neutral by construction, not a net directional bet on "
          f"either metal or the broader market.")
    exposure_rows.append(dict(strategy="Gold-silver pairs (N1.5)", structure="dollar-neutral, both legs concurrent",
                               pct_long=pct_long_gld, pct_short=pct_short_gld, n_trades=None))
    pd.DataFrame(exposure_rows).to_csv(RESULTS / "four_candidates_exposure.csv", index=False)

    print(f"\n  COMBINED-PORTFOLIO EXPOSURE SUMMARY: of the 4 candidates, only ORB gold RETEST carries "
          f"outright net directional risk on any given trade (but splits both ways over time, "
          f"{100*n_long/n_tot:.0f}%/{100*n_short/n_tot:.0f}% long/short). On-chain BTC H=20 is the ONE "
          f"candidate that is structurally a pure long-only bet on BTC rising -- it has ZERO short exposure "
          f"and is flat (not short) the rest of the time, so it offers NO protection if BTC falls; it can "
          f"only avoid losing by being out of the market, not by profiting from a decline. The credit-spread "
          f"and pairs strategies are both structurally close to market-neutral by construction (short-vol "
          f"and dollar-neutral respectively), so the combined 4-strategy book is NOT simply 'long the market' "
          f"-- but it also has no strategy in it designed to profit meaningfully FROM a bear market, only "
          f"ones designed to avoid or be indifferent to one.")

    # ═════════════════════ PART 3 -- restricted 4-strategy ensemble ═════════════════════
    print("\n" + "=" * W)
    print("  PART 3 -- RESTRICTED 4-STRATEGY ENSEMBLE (ONLY these 4, pairwise-available, no zero-fill)")
    print("=" * W)
    four = pd.DataFrame({
        "ORB gold RETEST": orb_ret,
        "On-chain BTC H=20": frame_all["D|On-chain active-address surge H20 (BTCUSDT)"],
        "Capped vol spread": frame_all["D|Credit-spread FILTERED 1pct (SPY)"],
        "Gold-silver pairs N1.5": frame_all["C|Pairs GLD-SLV N1.5"],
    })
    corr4 = four.corr(min_periods=60)
    print("\n  4x4 CORRELATION MATRIX (pairwise-complete, real overlapping days only):")
    print(corr4.round(3).to_string())
    corr4.to_csv(RESULTS / "four_candidates_corr_matrix.csv")

    pruned = []
    dropped = []
    kept = []
    import itertools
    names4 = list(four.columns)
    for a, b in itertools.combinations(names4, 2):
        c = corr4.loc[a, b]
        flag = abs(c) > CORR_PRUNE_THRESHOLD
        pruned.append((a, b, c, flag))
        if flag:
            print(f"  !! |corr|={abs(c):.3f} > {CORR_PRUNE_THRESHOLD} between '{a}' and '{b}' -- exceeds the "
                  f"pruning threshold.")
    any_high = any(f for _, _, _, f in pruned)
    if not any_high:
        print(f"\n  No pair among these 4 exceeds |corr| > {CORR_PRUNE_THRESHOLD}. Nothing pruned -- all 4 kept.")
        kept = names4
    else:
        # drop the member of the worst-offending pair with the lower own-Sharpe, repeat until clean
        work = four.copy()
        kept = names4[:]
        while True:
            c = work[kept].corr(min_periods=60)
            worst = None
            worst_val = CORR_PRUNE_THRESHOLD
            for a, b in itertools.combinations(kept, 2):
                v = abs(c.loc[a, b])
                if v > worst_val:
                    worst_val, worst = v, (a, b)
            if worst is None:
                break
            a, b = worst
            sr_a = ec.sharpe_ann(work[a].dropna())
            sr_b = ec.sharpe_ann(work[b].dropna())
            drop = a if sr_a < sr_b else b
            print(f"  Dropping '{drop}' (own Sharpe {min(sr_a, sr_b):+.3f}) -- its pair exceeded "
                  f"|corr|={worst_val:.3f} with the kept set.")
            dropped.append(drop)
            kept.remove(drop)
        print(f"\n  After pruning: kept {kept}")

    print(f"\n  BUILDING COMBINED PORTFOLIO -- KEPT SET: {kept}")
    grp = four[kept].dropna(how="all")
    live = grp.notna().sum(axis=1)
    print(f"  Full honest span: {grp.index.min().date()} .. {grp.index.max().date()} ({len(grp):,} days)")
    print(f"  live-component-count-per-day: mean={live.mean():.2f}  min={live.min()}  max={live.max()}")
    combo = ec.equal_weight_available(grp)
    dd = ec.max_dd_recovery(combo.dropna())
    sr = ec.sharpe_ann(combo.dropna())
    tys = ec.top_year_share(combo.dropna())
    pool_sr = np.array([ec.sharpe_ann(four[c].dropna()) for c in names4])
    d = deflated_sharpe(sr, pool_sr, n_obs=len(combo.dropna()), ann_factor=ec.BARS_PER_YEAR,
                         skewness=float(combo.dropna().skew()), excess_kurtosis=float(combo.dropna().kurtosis()))
    print(f"\n  COMBINED (4-candidate restricted ensemble, kept N={len(kept)}):")
    print(f"    total_return={float(ec.equity(combo.dropna()).iloc[-1]-1)*100:+.1f}%  sharpe={sr:+.3f}  "
          f"maxDD={dd['max_dd']*100:.1f}%  recovery_days={dd['recovery_days']}  "
          f"top_year_share={tys*100 if not np.isnan(tys) else float('nan'):.1f}%  DSR={d['dsr']:.4f} (pool N=4)")

    print(f"\n  STANDALONE comparison (each of the 4, own full-history stats):")
    for c in names4:
        s2 = four[c].dropna()
        sr_c = ec.sharpe_ann(s2)
        eq_c = ec.equity(s2)
        dd_c = ec.max_dd_recovery(s2)
        print(f"    {c:35s} sharpe={sr_c:+.3f}  total_return={float(eq_c.iloc[-1]-1)*100:+.1f}%  "
              f"maxDD={dd_c['max_dd']*100:.1f}%")

    out3 = pd.DataFrame([dict(
        method=f"4-CANDIDATE RESTRICTED ENSEMBLE (kept N={len(kept)})", kept=", ".join(kept),
        dropped=", ".join(dropped) if dropped else "none",
        first=str(grp.index.min().date()), last=str(grp.index.max().date()), n_days=len(grp),
        total_return=float(ec.equity(combo.dropna()).iloc[-1] - 1), sharpe=sr, max_dd=dd["max_dd"],
        recovery_days=dd["recovery_days"], top_year_share=tys, dsr=d["dsr"], dsr_pool_n=4,
    )])
    out3.to_csv(RESULTS / "four_candidates_restricted_ensemble.csv", index=False)
    print(f"\nSaved: results/four_candidates_capm.csv, four_candidates_exposure.csv, "
          f"four_candidates_corr_matrix.csv, four_candidates_restricted_ensemble.csv")


if __name__ == "__main__":
    main()
