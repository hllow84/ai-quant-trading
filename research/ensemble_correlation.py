#!/usr/bin/env python3
"""
ENSEMBLE / COMBINATION TEST -- section 32.

GOAL (user's direct ask): does combining MANY signals from across this
project -- including individually-KILLED ones, not just the survivors --
into one basket produce a better, smoother result than requiring each to
pass alone? The critical output is the FULL pairwise correlation matrix:
are these signals actually independent, or do most just move with the
broader market (so "combining" dilutes rather than diversifies)?

METHOD
  1. Inventory every strategy/instrument cell in this project with a real,
     reconstructable daily return series (not re-run from scratch -- the
     SAME engine code and SAME saved trade/price data already used for
     each section's verdict is called again here, in-memory, to recover
     the daily series that was never itself persisted to disk). Nothing
     here is a new backtest; it is series EXTRACTION.
  2. Reindex every series to a full calendar-day grid over ITS OWN
     [first, last] data range (off-days -> 0% return, consistent with the
     convention already used by report_year_by_year_returns.py's
     trade_series()); outside its own range the series is left NaN.
  3. Pairwise correlation via pandas .corr() (pairwise-complete
     observations) -- reported in FULL as a CSV, plus the distribution.
  4. Two combined portfolios: (a) equal-weight ALL series, each day
     averaged only over series with data that day (staggered-inception
     equal weighting, stated explicitly); (b) equal-weight a
     LOW-CORRELATION-FILTERED subset, built by a greedy walk over series
     sorted by history length (longest first), keeping a candidate only if
     its max |corr| against everything already kept is below THRESHOLD.
  5. Report total return, max DD, recovery time, Sharpe (annualised on
     365 calendar days, consistent with the calendar-day grid), per-year
     concentration (top calendar year's share of total log-return), and
     DSR as REFERENCE ONLY (pool = every component's own full-history
     Sharpe, per research/dsr.py -- never metrics.py's broken version).

NOT a new trial batch in the usual per-config sense -- this is a portfolio-
of-existing-trials study. Logged as ONE new row (the ensemble test itself)
per repo convention; existing component trials are not re-counted.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 365  # every series below is reindexed to a calendar-day grid
LOW_CORR_THRESHOLD = 0.30  # stated a priori, not tuned after seeing the matrix

# ─────────────────────────── generic helpers ───────────────────────────

def to_calendar_grid(daily_ret: pd.Series) -> pd.Series:
    """Reindex a (possibly business-day / trading-day) return series onto a
    full calendar-day grid spanning its own [first,last]; off-days -> 0.0.
    This is the SAME convention report_year_by_year_returns.trade_series()
    already uses for the trade-based series, applied uniformly here so every
    series in the combined study is on one common daily grid."""
    daily_ret = daily_ret.dropna()
    daily_ret.index = pd.DatetimeIndex(daily_ret.index).tz_localize(None) if daily_ret.index.tz is not None else pd.DatetimeIndex(daily_ret.index)
    daily_ret = daily_ret.groupby(daily_ret.index.normalize()).sum()
    idx = pd.date_range(daily_ret.index.min(), daily_ret.index.max(), freq="D")
    return daily_ret.reindex(idx).fillna(0.0)


def equity(r: pd.Series) -> pd.Series:
    return (1.0 + r.fillna(0.0)).cumprod()


def sharpe_ann(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 30 or r.std(ddof=1) == 0:
        return float("nan")
    return float(r.mean() / r.std(ddof=1) * np.sqrt(BARS_PER_YEAR))


def max_dd_recovery(r: pd.Series) -> dict:
    eq = equity(r)
    peak = eq.cummax()
    dd = 1.0 - eq / peak
    max_dd = float(dd.max())
    trough = dd.idxmax()
    peak_date = eq.loc[:trough].idxmax()
    peak_val = float(eq.loc[peak_date])
    after = eq.loc[eq.index > trough]
    hit = after[after >= peak_val]
    rec_date = hit.index[0] if len(hit) else None
    rec_days = int((rec_date - trough).days) if rec_date is not None else None
    return dict(max_dd=max_dd, peak_date=peak_date, trough_date=trough,
                recovery_date=rec_date, recovery_days=rec_days)


def top_year_share(r: pd.Series) -> float:
    yr = r.groupby(r.index.year).apply(lambda s: np.log1p(s).sum())
    total = yr.sum()
    if total <= 0 or not np.isfinite(total):
        return float("nan")
    return float(yr.max() / total)


def summarize(name: str, r: pd.Series) -> dict:
    r = r.dropna()
    dd = max_dd_recovery(r)
    return dict(
        name=name, first=str(r.index.min().date()), last=str(r.index.max().date()),
        n_days=len(r), years=round(len(r) / 365.25, 1),
        total_return=float(equity(r).iloc[-1] - 1.0),
        sharpe=sharpe_ann(r), max_dd=dd["max_dd"],
        recovery_days=dd["recovery_days"], top_year_share=top_year_share(r),
    )


# ─────────────────────────── series builders ───────────────────────────

def trade_series_generic(csv: str, filt: dict, entry_col="entry_time", exit_col="exit_time",
                          ret_col="ret_frac") -> pd.Series:
    df = pd.read_csv(RESULTS / csv)
    for col, val in filt.items():
        df = df[df[col].astype(str) == str(val)]
    if df.empty:
        raise ValueError(f"{csv}: no rows for {filt}")
    ex = pd.to_datetime(df[exit_col], utc=True).dt.tz_localize(None).dt.normalize()
    daily = df.assign(_d=ex)[ret_col].groupby(ex).sum().sort_index()
    return daily.rename("ret")


def build_group_A() -> dict[str, pd.Series]:
    """Tier 1/2 -- reuse report_year_by_year_returns.build_all() verbatim
    (already-audited series builders for momentum rotation, VRP, Sneaky
    Pivot, ORB)."""
    import report_year_by_year_returns as y
    S, notes = y.build_all()
    if notes:
        print("  [group A notes]", notes)
    return {f"A|{k}": v for k, v in S.items()}


def build_group_B_ict_smc() -> dict[str, pd.Series]:
    """ICT SMC full model (sec 28) -- 7 cells (4 in-regime 2018-2025, 3
    short out-of-regime windows), from the SAME per-trade file (ret_frac
    already includes real costs)."""
    cells = pd.read_csv(RESULTS / "ict_smc_trades.csv")["cell"].unique().tolist()
    out = {}
    for c in cells:
        try:
            out[f"B|ICT-SMC {c}"] = trade_series_generic("ict_smc_trades.csv", {"cell": c})
        except Exception as e:
            print(f"  [group B] skip {c}: {e}")
    return out


def build_group_C_six_strategies() -> dict[str, pd.Series]:
    """Sec 31 six named strategies -- Bollinger/MACD/Ichimoku (7 instruments
    each), Turtle Sys1/Sys2 (7 each), Pairs (2 pairs x N in {1.5,2.0}),
    MACD-slow (BTCUSDT/ETHUSDT, n=3 only -- the middle of the 3 tested
    exit-patience values, picked a priori not by performance, to avoid
    tripling near-duplicate crypto MACD series)."""
    import research.six_strategies_engine as eng
    import research.strat_bollinger as sb
    import research.strat_macd as sm
    import research.strat_ichimoku as si
    import research.strat_turtle as st
    import research.strat_pairs as sp
    import research.strat_macd_slow as sms

    out = {}
    for inst in eng.ALL_INSTRUMENTS:
        daily = eng.load_daily(inst)
        for tag, mod in (("Bollinger", sb), ("MACD", sm), ("Ichimoku", si)):
            pos = mod.build_position(daily)
            r = eng.full_report(f"{tag} {inst}", daily, pos)
            out[f"C|{tag} {inst}"] = r["daily_ret"]
        r1 = st.run_system(daily, 20, 10, True)
        r2 = st.run_system(daily, 55, 20, False)
        out[f"C|Turtle Sys1 {inst}"] = r1["daily_ret"]
        out[f"C|Turtle Sys2 {inst}"] = r2["daily_ret"]

    for a, b in [("GLD", "SLV"), ("NAS100", "US30")]:
        df = sp.build_pair_frame(a, b)
        for N in (1.5, 2.0):
            r = sp.run_pair(df, N)
            out[f"C|Pairs {a}-{b} N{N}"] = r["daily_ret"]

    for inst in sms.INSTRUMENTS:
        daily = eng.load_daily(inst)
        pos = sms.build_position(daily, 3)
        r = eng.full_report(f"MACD-slow n3 {inst}", daily, pos)
        out[f"C|MACD-slow-n3 {inst}"] = r["daily_ret"]
    return out


def build_group_D_options_onchain() -> dict[str, pd.Series]:
    """Sec 27 credit-spread FILTERED/1pct (SPY, 1993-2026) and sec 30 on-chain
    H=20 (BTCUSDT, 2018-2025), both via the SAME continuous-account functions
    the project's own report_*_continuous.py scripts already call -- daily_ret
    was computed there but never persisted to a CSV, so it is re-extracted in
    memory here rather than duplicated by hand."""
    out = {}
    import research.credit_spread_iv_filter as cs
    from research.delta10_iv_filter import load_data, IV_LOOKBACK, TOP_TERCILE
    df = load_data()
    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible_filtered = (iv_rank >= TOP_TERCILE).fillna(False)
    _, daily_ret, _, _, _ = cs.run_combined_book(df, eligible_filtered, "FILTERED", cs.WIDTH_PCTS["1pct"])
    out["D|Credit-spread FILTERED 1pct (SPY)"] = daily_ret.rename("ret")

    import run_onchain_signal as sig
    import research.report_onchain_h20_continuous as h20
    addr = sig.load_addr()
    daily = sig.load_btc_daily()
    z = sig.build_signal(addr, daily.index)
    _, daily_ret2, _, guard_ok = h20.build_full_daily_series(daily, z, h20.H)
    assert guard_ok, "on-chain H20 look-ahead guard failed on re-extraction"
    out["D|On-chain active-address surge H20 (BTCUSDT)"] = daily_ret2.rename("ret")
    return out


def build_all_series() -> dict[str, pd.Series]:
    S = {}
    S.update(build_group_A())
    S.update(build_group_B_ict_smc())
    S.update(build_group_C_six_strategies())
    S.update(build_group_D_options_onchain())
    return {k: to_calendar_grid(v) for k, v in S.items()}


# ─────────────────────────── combination ───────────────────────────

def equal_weight_available(frame: pd.DataFrame) -> pd.Series:
    """Each day: average over whichever series has real (non-NaN) data that
    day -- a staggered-inception equal-weight basket, stated explicitly
    (NOT the same as filling 0 for missing history, which would silently
    understate the combined vol during the early, thin-membership period).
    Days with zero series present are dropped (cannot exist inside the
    frame's own overall span since every series has 100% dense calendar
    coverage inside its own start/end)."""
    return frame.mean(axis=1, skipna=True)


def greedy_low_corr_subset(frame: pd.DataFrame, corr: pd.DataFrame, threshold: float,
                            eligible: list[str] | None = None) -> list[str]:
    """Greedy, longest-history-first walk: keep a candidate iff its max |corr|
    against everything already kept is below threshold. `eligible` restricts
    the candidate pool (e.g. to components with a positive own-Sharpe) without
    changing the correlations themselves (still computed against the full
    universe elsewhere)."""
    lengths = frame.notna().sum().sort_values(ascending=False)
    if eligible is not None:
        lengths = lengths[lengths.index.isin(eligible)]
    kept: list[str] = []
    for name in lengths.index:
        if not kept:
            kept.append(name)
            continue
        max_abs_corr = corr.loc[name, kept].abs().max()
        if pd.isna(max_abs_corr) or max_abs_corr < threshold:
            kept.append(name)
    return kept


def inverse_vol_weight(frame: pd.DataFrame) -> pd.Series:
    """Static inverse-of-own-full-history-vol weights (not per-day re-estimated),
    normalized to sum to 1 across whichever series are present each day -- a
    supplementary check on whether the naive equal-weight result is an
    artefact of a few components' wildly larger volatility dominating the
    blend, or a real finding independent of weighting scheme."""
    vol = frame.std(skipna=True)
    inv = 1.0 / vol.replace(0.0, np.nan)
    w = frame.notna().astype(float).mul(inv, axis=1)
    w = w.div(w.sum(axis=1), axis=0)
    return (frame.fillna(0.0) * w).sum(axis=1)


# ─────────────────────────── main ───────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 110
    print("=" * W)
    print("  SECTION 32 -- ENSEMBLE / COMBINATION TEST: does combining many signals (incl. killed ones) help?")
    print("=" * W)

    print("\nExtracting every reconstructable daily return series...")
    S = build_all_series()
    names = sorted(S.keys())
    print(f"TOTAL SERIES: {len(names)}")

    frame = pd.DataFrame({n: S[n] for n in names})
    frame = frame.sort_index()
    frame.to_csv(RESULTS / "ensemble_daily_returns.csv")

    # ---- per-series summary ----
    summ = pd.DataFrame([summarize(n, S[n]) for n in names]).sort_values("sharpe", ascending=False)
    summ.to_csv(RESULTS / "ensemble_component_summary.csv", index=False)
    print("\nPER-COMPONENT SUMMARY (top 15 by own full-history Sharpe):")
    print(summ.head(15).to_string(index=False))
    print("\nPER-COMPONENT SUMMARY (bottom 10 by own full-history Sharpe):")
    print(summ.tail(10).to_string(index=False))

    short = summ[summ["years"] < 2.0]
    if len(short):
        print(f"\n!! {len(short)} series have < 2 years of history -- correlation vs these is unstable, flagged not hidden:")
        print(short[["name", "first", "last", "years"]].to_string(index=False))

    # ---- correlation matrix ----
    corr = frame.corr(min_periods=60)
    corr.to_csv(RESULTS / "ensemble_correlation_matrix.csv")
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    n_pairs = len(pairs)
    print(f"\nCORRELATION MATRIX: {corr.shape[0]}x{corr.shape[0]} ({n_pairs:,} unique pairs), "
          f"saved in full -> results/ensemble_correlation_matrix.csv")
    print(f"  mean pairwise corr    : {pairs.mean():+.3f}")
    print(f"  median pairwise corr  : {pairs.median():+.3f}")
    print(f"  std of pairwise corr  : {pairs.std():.3f}")
    print(f"  pairs |corr| > 0.70   : {int((pairs.abs() > 0.70).sum()):,} ({100*(pairs.abs()>0.70).mean():.1f}%)")
    print(f"  pairs |corr| > 0.50   : {int((pairs.abs() > 0.50).sum()):,} ({100*(pairs.abs()>0.50).mean():.1f}%)")
    print(f"  pairs |corr| < 0.30   : {int((pairs.abs() < 0.30).sum()):,} ({100*(pairs.abs()<0.30).mean():.1f}%)")
    print(f"  pairs |corr| < 0.10   : {int((pairs.abs() < 0.10).sum()):,} ({100*(pairs.abs()<0.10).mean():.1f}%)")

    top_pairs = pairs.abs().sort_values(ascending=False).head(15)
    print("\nTOP 15 MOST-CORRELATED PAIRS (|corr|):")
    for (a, b), v in top_pairs.items():
        print(f"  {corr.loc[a,b]:+.3f}  {a}  <->  {b}")
    bottom_pairs = pairs.abs().sort_values(ascending=True).head(15)
    print("\n15 MOST-INDEPENDENT PAIRS (|corr| closest to 0):")
    for (a, b), v in bottom_pairs.items():
        print(f"  {corr.loc[a,b]:+.3f}  {a}  <->  {b}")

    # ---- combined portfolio: ALL series, equal weight of whoever has data ----
    combo_all = equal_weight_available(frame)
    s_all = summarize("EQUAL-WEIGHT ALL (N=%d)" % len(names), combo_all)

    # ---- ALL series, static inverse-vol weight (supplementary: is the
    # equal-weight result an artefact of a few high-vol components dominating?) ----
    combo_ivol = inverse_vol_weight(frame)
    s_ivol = summarize(f"INVERSE-VOL-WEIGHT ALL (N={len(names)})", combo_ivol)

    # ---- low-correlation-filtered subset, candidate pool = EVERYTHING (blind to quality) ----
    kept = greedy_low_corr_subset(frame, corr, LOW_CORR_THRESHOLD)
    combo_filt = equal_weight_available(frame[kept])
    s_filt = summarize(f"EQUAL-WEIGHT LOW-CORR SUBSET, quality-blind (thr {LOW_CORR_THRESHOLD}, N={len(kept)})", combo_filt)

    print(f"\nLOW-CORRELATION-FILTERED SUBSET, QUALITY-BLIND (greedy, longest-history-first, threshold |corr|<{LOW_CORR_THRESHOLD}):")
    print(f"  kept {len(kept)}/{len(names)} series:")
    for k in kept:
        print(f"    - {k}")
    n_ruin_kept = sum(1 for k in kept if summ.set_index("name").loc[k, "sharpe"] < -1.0)
    print(f"  !! {n_ruin_kept}/{len(kept)} kept series have their own full-history Sharpe < -1.0 (catastrophic, "
          f"not merely losing) -- low correlation was achieved partly by admitting IDIOSYNCRATIC RUIN, not just")
    print(f"     independent-but-healthy signals. This is checked directly by the quality-filtered variant below.")

    # ---- low-correlation-filtered subset, candidate pool restricted to own-Sharpe > 0 ----
    positive_names = summ.loc[summ["sharpe"] > 0, "name"].tolist()
    kept_q = greedy_low_corr_subset(frame, corr, LOW_CORR_THRESHOLD, eligible=positive_names)
    combo_filt_q = equal_weight_available(frame[kept_q])
    s_filt_q = summarize(f"EQUAL-WEIGHT LOW-CORR SUBSET, positive-Sharpe-only (thr {LOW_CORR_THRESHOLD}, N={len(kept_q)})", combo_filt_q)
    print(f"\nLOW-CORRELATION-FILTERED SUBSET, POSITIVE-OWN-SHARPE ONLY (same greedy method, candidate pool "
          f"restricted to the {len(positive_names)}/{len(names)} series with own full-history Sharpe > 0):")
    print(f"  kept {len(kept_q)}/{len(positive_names)} eligible series:")
    for k in kept_q:
        print(f"    - {k}")

    # ---- DSR reference only ----
    from research.dsr import deflated_sharpe
    pool_sr = summ["sharpe"].dropna().to_numpy()

    def dsr_of(combo):
        c = combo.dropna()
        return deflated_sharpe(sharpe_ann(c), pool_sr, n_obs=len(c), ann_factor=BARS_PER_YEAR,
                                skewness=float(c.skew()), excess_kurtosis=float(c.kurtosis()))

    dsr_all, dsr_ivol, dsr_filt, dsr_filt_q = dsr_of(combo_all), dsr_of(combo_ivol), dsr_of(combo_filt), dsr_of(combo_filt_q)

    print("\n" + "=" * W)
    print("  COMBINED PORTFOLIO RESULTS")
    print("=" * W)
    rows = [("ALL %d COMPONENTS, EQUAL-WEIGHT" % len(names), s_all, dsr_all),
            ("ALL %d COMPONENTS, INVERSE-VOL-WEIGHT" % len(names), s_ivol, dsr_ivol),
            (f"LOW-CORR SUBSET, QUALITY-BLIND (N={len(kept)})", s_filt, dsr_filt),
            (f"LOW-CORR SUBSET, POSITIVE-SHARPE-ONLY (N={len(kept_q)})", s_filt_q, dsr_filt_q)]
    for label, s, dsr in rows:
        print(f"\n  {label}")
        print(f"    span            : {s['first']} -> {s['last']}  ({s['years']} yrs, {s['n_days']} days)")
        print(f"    total return    : {s['total_return']*100:+.1f}%")
        print(f"    Sharpe (ann.)   : {s['sharpe']:+.3f}")
        print(f"    max drawdown    : {s['max_dd']*100:.1f}%")
        print(f"    recovery        : {s['recovery_days']} days" if s['recovery_days'] is not None else "    recovery        : NOT recovered")
        print(f"    top-year share  : {s['top_year_share']*100:.0f}%" if np.isfinite(s['top_year_share']) else "    top-year share  : n/a")
        print(f"    DSR (reference) : {dsr['dsr']:.4f}  (pool N={dsr['pool_n']}, E[max SR]={dsr['e_max_sr']:+.3f}, z={dsr['z']:+.2f})")

    # ---- best individual component, for comparison ----
    best_row = summ.iloc[0]
    print(f"\n  BEST SINGLE COMPONENT BY OWN SHARPE (for comparison, not a fair pool-adjusted comparison):")
    print(f"    {best_row['name']}: Sharpe {best_row['sharpe']:+.3f}, total return {best_row['total_return']*100:+.1f}%, "
          f"max DD {best_row['max_dd']*100:.1f}%")

    out = pd.DataFrame([s_all, s_ivol, s_filt, s_filt_q])
    out["dsr"] = [dsr_all["dsr"], dsr_ivol["dsr"], dsr_filt["dsr"], dsr_filt_q["dsr"]]
    out["dsr_pool_n"] = [dsr_all["pool_n"], dsr_ivol["pool_n"], dsr_filt["pool_n"], dsr_filt_q["pool_n"]]
    out["dsr_e_max_sr"] = [dsr_all["e_max_sr"], dsr_ivol["e_max_sr"], dsr_filt["e_max_sr"], dsr_filt_q["e_max_sr"]]
    out.to_csv(RESULTS / "ensemble_combined_results.csv", index=False)
    pd.Series(kept, name="kept_series_quality_blind").to_csv(RESULTS / "ensemble_low_corr_subset_members.csv", index=False)
    pd.Series(kept_q, name="kept_series_positive_sharpe").to_csv(RESULTS / "ensemble_low_corr_subset_members_positive.csv", index=False)

    print("\nFiles: results/ensemble_daily_returns.csv, ensemble_component_summary.csv, "
          "ensemble_correlation_matrix.csv, ensemble_combined_results.csv, "
          "ensemble_low_corr_subset_members.csv, ensemble_low_corr_subset_members_positive.csv")


if __name__ == "__main__":
    main()
