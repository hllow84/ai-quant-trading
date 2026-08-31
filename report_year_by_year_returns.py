#!/usr/bin/env python3
"""
report_year_by_year_returns.py -- STATE_OF_PLAY section 22 (reporting only,
NOT a new trial batch, cumulative trial count UNCHANGED at N=946).

GOAL: year-by-year ABSOLUTE return (not vs any benchmark, not risk-adjusted)
for every strategy in this project that has a saved / reconstructable return
series, in two views:

  VIEW 1  FULL HISTORY  -- every calendar year's absolute return, count of
          positive vs negative years, worst single year, max peak-to-trough
          drawdown.
  VIEW 2  POST-COVID    -- 2021-01-01 -> each series' own last data date,
          resliced. Monthly granularity (the window is too short for annual
          buckets to say anything). Plus a 2021-2022 vs 2023-2026 split so a
          reader can see whether any post-COVID edge is itself front-loaded.

Two ranked tables at the end (full-history consistency, post-COVID
consistency), ranked by % of periods positive then by worst-period
magnitude -- NOT Sharpe, NOT vs benchmark -- followed by an explicit
full-history-vs-post-COVID DISAGREEMENT analysis.

Strategies are sorted into tiers by what granularity their saved evidence
actually supports; nothing is forced.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.momentum_rotation import (
    build_weights, simulate, SECTOR_ETFS, ASSET_ETFS, UNIVERSE,
)
import run_vol_protected_structures as vps

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
POST_COVID_START = pd.Timestamp("2021-01-01")
SPLIT_A = ("2021-01-01", "2022-12-31")   # recovery / rally + 2022 bear
SPLIT_B = ("2023-01-01", "2099-12-31")   # 2023 -> latest

EXPANDED_UNIVERSE = SECTOR_ETFS + ASSET_ETFS + [
    "DBC", "USO", "UNG", "SLV", "VGK", "INDA", "FXI", "MTUM", "VTV", "MDY"]
CRYPTO_RANKED = ["ETH", "SOL", "BNB", "ADA", "AVAX", "UNI", "AAVE", "LINK",
                 "SAND", "MANA", "DOGE", "CASH_USD"]
COUNTRY_RANKED = ["EWJ", "EWG", "EWU", "EWZ", "INDA", "FXI", "EFA", "EEM", "SPY", "IEF"]


# ─────────────────────────── metric helpers ───────────────────────────

def equity(daily_ret: pd.Series) -> pd.Series:
    return (1.0 + daily_ret.fillna(0.0)).cumprod()


def max_drawdown(daily_ret: pd.Series) -> float:
    eq = equity(daily_ret)
    return float((eq / eq.cummax() - 1.0).min())


def calendar_year_returns(daily_ret: pd.Series) -> pd.Series:
    return daily_ret.groupby(daily_ret.index.year).apply(lambda s: (1 + s).prod() - 1.0)


def month_returns(daily_ret: pd.Series) -> pd.Series:
    g = daily_ret.groupby([daily_ret.index.year, daily_ret.index.month])
    m = g.apply(lambda s: (1 + s).prod() - 1.0)
    m.index = pd.to_datetime([f"{y}-{mo:02d}-01" for y, mo in m.index])
    return m.sort_index()


def span_return(daily_ret: pd.Series, start: str, end: str) -> tuple[float, int, int]:
    s = daily_ret[(daily_ret.index >= start) & (daily_ret.index <= end)]
    if s.empty:
        return float("nan"), 0, 0
    m = month_returns(s)
    tot = float((1 + s).prod() - 1.0)
    return tot, int((m > 0).sum()), int((m <= 0).sum())


def summarize_full(name: str, daily_ret: pd.Series) -> dict:
    daily_ret = daily_ret.dropna()
    yr = calendar_year_returns(daily_ret)
    pos = int((yr > 0).sum())
    neg = int((yr <= 0).sum())
    return dict(
        strategy=name, first=str(daily_ret.index.min().date()),
        last=str(daily_ret.index.max().date()), n_years=len(yr),
        pos_years=pos, neg_years=neg, pct_pos_years=100.0 * pos / len(yr),
        worst_year=float(yr.min()), worst_year_label=int(yr.idxmin()),
        best_year=float(yr.max()), best_year_label=int(yr.idxmax()),
        total_return=float((1 + daily_ret).prod() - 1.0),
        max_dd=max_drawdown(daily_ret),
        _year_series=yr,
    )


def summarize_postcovid(name: str, daily_ret: pd.Series) -> dict:
    d = daily_ret.dropna()
    d = d[d.index >= POST_COVID_START]
    if d.empty:
        return dict(strategy=name, empty=True)
    m = month_returns(d)
    pos = int((m > 0).sum())
    neg = int((m <= 0).sum())
    ta, pa, na = span_return(daily_ret, *SPLIT_A)
    tb, pb, nb = span_return(daily_ret, SPLIT_B[0], str(d.index.max().date()))
    return dict(
        strategy=name, empty=False, first=str(d.index.min().date()),
        last=str(d.index.max().date()), n_months=len(m),
        pos_months=pos, neg_months=neg, pct_pos_months=100.0 * pos / len(m),
        worst_month=float(m.min()), worst_month_label=str(m.idxmin().date())[:7],
        best_month=float(m.max()), best_month_label=str(m.idxmax().date())[:7],
        total_return=float((1 + d).prod() - 1.0),
        max_dd=max_drawdown(d),
        split_2021_2022_ret=ta, split_2021_2022_posmo=pa, split_2021_2022_negmo=na,
        split_2023_plus_ret=tb, split_2023_plus_posmo=pb, split_2023_plus_negmo=nb,
        _month_series=m,
    )


# ─────────────────────────── series builders ───────────────────────────

def momo(panel_file: str, universe, benchmark: str, defensive: str,
         cost_bps: float, n: int = 12, k: int = 5) -> pd.Series:
    adj = pd.read_csv(DATA / panel_file, index_col=0, parse_dates=True).sort_index()
    we, to = build_weights(adj, n, k, universe=universe, benchmark=benchmark, defensive=defensive)
    sim = simulate(adj, we, to, cost_bps_per_side=cost_bps, universe=universe)
    net = sim["net"]
    return net[net.index >= we.index.min()].rename("ret")


def vrp_series() -> dict[str, pd.Series]:
    spy = vps.load_close("SPY_daily_yfinance.csv")
    vix = vps.load_close("vix_daily_yfinance.csv")
    svxy = vps.load_close("svxy_daily_yfinance.csv")
    vixy = vps.load_close("vixy_daily_yfinance.csv")
    rv = vps.trailing_rv(spy, vps.RV_WINDOW)
    ratio = (vix / rv).dropna()
    out = {}
    for thr in (1.2, 1.5):
        base = vps.base_signal(vix, ratio, svxy, thr)
        out[f"VRP naked SVXY §20 (thr {thr})"] = base["net_ret"].rename("ret")
        if thr == 1.2:
            out["VRP §21-A fixed 10% sizing (thr 1.2)"] = vps.structure_A(base, 0.10).rename("ret")
            out["VRP §21-A fixed 20% sizing (thr 1.2)"] = vps.structure_A(base, 0.20).rename("ret")
            b20, _ = vps.structure_B(base, vix, 0.20, vps.B_COOLDOWN_DAYS)
            out["VRP §21-B vol-of-vol breaker +20% (thr 1.2)"] = b20.rename("ret")
            c10, _ = vps.structure_C(base, vixy, 1.0)
            out["VRP §21-C paired VIXY hedge h=1.0 (thr 1.2)"] = c10.rename("ret")
    return out


def trade_series(csv: str, filt: dict) -> pd.Series:
    """Daily account-fraction return from a per-trade file: ret_frac summed by
    exit DAY (1% risk/trade sizing already baked into ret_frac), then treated
    as a daily return series so compounding and drawdown are real."""
    df = pd.read_csv(RESULTS / csv)
    for col, val in filt.items():
        df = df[df[col].astype(str) == str(val)]
    if df.empty:
        raise ValueError(f"{csv}: no rows for {filt}")
    ex = pd.to_datetime(df["exit_time"], utc=True).dt.tz_localize(None).dt.normalize()
    daily = df.assign(_d=ex).groupby("_d")["ret_frac"].sum().sort_index()
    idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    return daily.reindex(idx).fillna(0.0).rename("ret")


# ─────────────────────────── assembly ───────────────────────────

def build_all() -> tuple[dict[str, pd.Series], list[str]]:
    S: dict[str, pd.Series] = {}
    notes: list[str] = []

    # -- Tier 1: momentum rotation family (daily series, reconstructed from the engine) --
    S["MomoRot US-sector §12 (N12/K5, headline)"] = momo(
        "momentum_universe_adjclose.csv", UNIVERSE, "SPY", "IEF", 3.0)
    S["MomoRot US-sector widened 27-univ §12.2 (N12/K5)"] = momo(
        "momentum_universe_expanded_adjclose.csv", EXPANDED_UNIVERSE, "SPY", "IEF", 3.0)
    try:
        S["MomoRot crypto-sectors §17 (N12/K5)"] = momo(
            "momentum_crypto_adjclose.csv", CRYPTO_RANKED, "BTC", "CASH_USD", 12.0)
    except Exception as e:
        notes.append(f"crypto-sectors momentum rotation could not be rebuilt: {e}")
    try:
        S["MomoRot country-ETFs §17 (N12/K5)"] = momo(
            "momentum_countries_adjclose.csv", COUNTRY_RANKED, "ACWI", "IEF", 3.0)
    except Exception as e:
        notes.append(f"country-ETF momentum rotation could not be rebuilt: {e}")

    # -- Tier 1: volatility risk premium §20 + protected structures §21 (daily) --
    S.update(vrp_series())

    # -- Tier 2: trade-based price-pattern strategies (daily from per-trade ret_frac) --
    S["Sneaky Pivot §9 best cell 2018-2025 (NAS100 swing/sneaky/session)"] = trade_series(
        "sneaky_pivot_trades.csv",
        dict(instrument="NAS100", target="swing", stop="sneaky", trigger="session"))
    S["Sneaky Pivot §9.4 same cell 2013-2017 (out-of-regime)"] = trade_series(
        "sneaky_pivot_trades_pre2018.csv",
        dict(instrument="NAS100", target="swing", stop="sneaky", trigger="session"))
    S["ORB §10 best cell 2018-2025 (NAS100 OR30 2R)"] = trade_series(
        "orb_trades.csv", dict(instrument="NAS100", or_minutes="30", target="2R"))
    S["ORB §10 same cell 2013-2017 (out-of-regime)"] = trade_series(
        "orb_trades_pre2018.csv", dict(instrument="NAS100", or_minutes="30", target="2R"))

    return S, notes


def annual_only_rows() -> pd.DataFrame:
    """Tier 2b: strategies whose ONLY saved period breakdown is annual R totals
    (yr_YYYY columns) -- no daily/monthly series was persisted, so these appear
    in VIEW 1 (annual, in R units) only and cannot enter VIEW 2's monthly view."""
    rows = []

    def take(csv, label, sort_col="net_R_total", ascending=False, extra_filt=None):
        df = pd.read_csv(RESULTS / csv)
        if extra_filt:
            for c, v in extra_filt.items():
                df = df[df[c].astype(str) == str(v)]
        if sort_col not in df.columns:
            for alt in ("net_R_total", "total_R", "net_r_total", "sum_net_R"):
                if alt in df.columns:
                    sort_col = alt
                    break
        df = df.sort_values(sort_col, ascending=ascending)
        r = df.iloc[0]
        yrs = {int(c[3:]): float(r[c]) for c in df.columns
               if c.startswith("yr_") and pd.notna(r[c])}
        if not yrs:
            return
        pos = sum(1 for v in yrs.values() if v > 0)
        rows.append(dict(
            strategy=label, source=csv,
            n_years=len(yrs), pos_years=pos, neg_years=len(yrs) - pos,
            pct_pos_years=100.0 * pos / len(yrs),
            worst_year_R=min(yrs.values()),
            worst_year_label=min(yrs, key=yrs.get),
            best_year_R=max(yrs.values()), total_R=sum(yrs.values()),
            years=yrs,
            postcovid_R=sum(v for y, v in yrs.items() if y >= 2021),
            pre2021_R=sum(v for y, v in yrs.items() if y < 2021),
        ))

    take("positioning_reversal_scored.csv",
         "Positioning-extreme reversal §18 (best BTC/ETH cell, R units)")
    take("sweep_stocks_scored.csv",
         "Individual US stocks §14 (best cell 2018-2025, R units)")
    take("sweep_m1_scored.csv",
         "M1 row §11 (best cell 2018-2025, R units)")
    take("sweep_crypto_scored.csv",
         "Crypto 5-family sweep §13 (best cell, R units)")
    return pd.DataFrame(rows)


# ─────────────────────────── printing ───────────────────────────

def p(s=""):
    print(s)


def fmt_pct(x, w=8, dp=1):
    return f"{x*100:+{w}.{dp}f}%" if pd.notna(x) else f"{'n/a':>{w+1}}"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    S, notes = build_all()
    full = [summarize_full(k, v) for k, v in S.items()]
    postc = [summarize_postcovid(k, v) for k, v in S.items()]
    annual = annual_only_rows()

    W = 118
    p("=" * W)
    p("  SECTION 22 — YEAR-BY-YEAR ABSOLUTE RETURN, ALL STRATEGIES WITH A RECONSTRUCTABLE RETURN SERIES")
    p("  Absolute return only. Not vs benchmark, not risk-adjusted. Reporting task — cumulative trials UNCHANGED at N=946.")
    p("=" * W)

    # ---------- inventory ----------
    p("\n  WHICH STRATEGIES CAN BE RESLICED, AND HOW FINELY")
    p("  " + "-" * (W - 4))
    p("  TIER 1 — full daily return series rebuilt from the engine (annual + monthly, both views):")
    for k in S:
        if k.startswith(("MomoRot", "VRP")):
            p(f"     • {k}")
    p("  TIER 2 — per-trade records with timestamps; daily series from ret_frac by exit day (annual + monthly):")
    for k in S:
        if k.startswith(("Sneaky", "ORB")):
            p(f"     • {k}")
    p("  TIER 2b — ONLY annual R totals (yr_YYYY cols) were saved; VIEW 1 (annual, R units) only, NO monthly:")
    for _, r in annual.iterrows():
        p(f"     • {r['strategy']}  [{r['source']}]")
    p("  TIER 3 — NO per-period series or per-year breakdown saved; cannot be resliced by period at all:")
    p("     • XAUUSD 5-family sweep §1 (75 cfg)      — results/sweep_progress.csv: summary metrics only")
    p("     • US-index 5-family sweep §1 (150 cfg)   — results/sweep_indices_scored.csv: summary metrics only")
    p("     • HTF-trend-gated breakout §1 (12 cfg)   — results/htf_breakout_scored.csv: summary metrics only")
    p("     • Index trend basket §2 / §6 (108+90)    — results/basket_results*.csv: summary metrics only")
    p("     • Regime-switch §15 / §16A (8 cfg)       — results/regime_switch*.csv: only n_pos_years / top_year_R saved")
    p("     • Seasonality §16B, Cross-asset lead-lag §19 — statistical tests, not strategies: no return series exists")
    for n in notes:
        p(f"     ! {n}")

    # ---------- VIEW 1 detail ----------
    p("\n\n" + "=" * W)
    p("  VIEW 1 — FULL HISTORY, calendar-year absolute returns")
    p("=" * W)
    for f in full:
        yr = f["_year_series"]
        p(f"\n  {f['strategy']}")
        p(f"    span {f['first']} → {f['last']}   |   total return {fmt_pct(f['total_return'],1,0)}"
          f"   |   max peak-to-trough drawdown {fmt_pct(f['max_dd'],1,1)}")
        cells = "  ".join(f"{y}:{v*100:+.0f}%" for y, v in yr.items())
        p(f"    {cells}")
        p(f"    positive years {f['pos_years']}/{f['n_years']} ({f['pct_pos_years']:.0f}%)   "
          f"worst year {f['worst_year']*100:+.1f}% ({f['worst_year_label']})   "
          f"best year {f['best_year']*100:+.1f}% ({f['best_year_label']})")

    p("\n  TIER 2b — annual R totals only (1 unit = 1R risked; ~1% of account at this repo's sizing):")
    for _, r in annual.iterrows():
        yrs = r["years"]
        cells = "  ".join(f"{y}:{v:+.1f}R" for y, v in sorted(yrs.items()))
        p(f"\n  {r['strategy']}")
        p(f"    {cells}")
        p(f"    positive years {r['pos_years']}/{r['n_years']} ({r['pct_pos_years']:.0f}%)   "
          f"worst year {r['worst_year_R']:+.1f}R ({r['worst_year_label']})   total {r['total_R']:+.1f}R")
        p(f"    pre-2021 {r['pre2021_R']:+.1f}R   vs   2021+ {r['postcovid_R']:+.1f}R")

    # ---------- VIEW 2 detail ----------
    end_dates = {f["strategy"]: f["last"] for f in full}
    p("\n\n" + "=" * W)
    p("  VIEW 2 — POST-COVID ONLY (2021-01-01 → each series' own last data date), MONTHLY granularity")
    p("=" * W)
    for pcs in postc:
        if pcs.get("empty"):
            p(f"\n  {pcs['strategy']}: no data in the post-COVID window — skipped.")
            continue
        m = pcs["_month_series"]
        p(f"\n  {pcs['strategy']}")
        p(f"    window {pcs['first']} → {pcs['last']}   |   total {fmt_pct(pcs['total_return'],1,0)}"
          f"   |   max drawdown {fmt_pct(pcs['max_dd'],1,1)}")
        by_year = {}
        for ts, v in m.items():
            by_year.setdefault(ts.year, []).append(f"{ts.month:02d}:{v*100:+.1f}")
        for y, mm in by_year.items():
            p(f"      {y}  " + "  ".join(mm))
        p(f"    positive months {pcs['pos_months']}/{pcs['n_months']} ({pcs['pct_pos_months']:.0f}%)   "
          f"worst month {pcs['worst_month']*100:+.1f}% ({pcs['worst_month_label']})   "
          f"best month {pcs['best_month']*100:+.1f}% ({pcs['best_month_label']})")
        p(f"    FRONT-LOADING CHECK — 2021-2022: total {pcs['split_2021_2022_ret']*100:+.1f}% "
          f"({pcs['split_2021_2022_posmo']}+/{pcs['split_2021_2022_negmo']}- months)   ||   "
          f"2023-onward: total {pcs['split_2023_plus_ret']*100:+.1f}% "
          f"({pcs['split_2023_plus_posmo']}+/{pcs['split_2023_plus_negmo']}- months)")

    # ---------- RANKED TABLE 1 ----------
    p("\n\n" + "=" * W)
    p("  RANKED TABLE 1 — FULL-HISTORY CONSISTENCY  (by % positive years, then by worst-year magnitude)")
    p("  ranked on ABSOLUTE return only — no Sharpe, no benchmark")
    p("=" * W)
    r1 = sorted(full, key=lambda f: (-f["pct_pos_years"], f["worst_year"]))
    p(f"  {'#':>2}  {'strategy':<58}{'yrs+':>7}{'%pos':>7}{'worstYr':>10}{'maxDD':>9}{'totRet':>11}")
    p("  " + "-" * (W - 4))
    for i, f in enumerate(r1, 1):
        p(f"  {i:>2}  {f['strategy'][:57]:<58}{f['pos_years']:>3}/{f['n_years']:<3}"
          f"{f['pct_pos_years']:>6.0f}%{f['worst_year']*100:>9.1f}%{f['max_dd']*100:>8.1f}%"
          f"{f['total_return']*100:>10.0f}%")
    p("\n  (Tier 2b, annual R units, ranked separately — not comparable to the % returns above:)")
    a1 = annual.sort_values(["pct_pos_years", "worst_year_R"], ascending=[False, False])
    for i, (_, r) in enumerate(a1.iterrows(), 1):
        p(f"  {i:>2}  {r['strategy'][:57]:<58}{r['pos_years']:>3}/{r['n_years']:<3}"
          f"{r['pct_pos_years']:>6.0f}%{r['worst_year_R']:>8.1f}R{'':>9}{r['total_R']:>9.1f}R")

    # ---------- RANKED TABLE 2 ----------
    p("\n\n" + "=" * W)
    p("  RANKED TABLE 2 — POST-COVID CONSISTENCY  (2021-01-01 → latest; by % positive months, then worst-month magnitude)")
    p("=" * W)
    r2 = sorted([x for x in postc if not x.get("empty")],
               key=lambda x: (-x["pct_pos_months"], x["worst_month"]))
    p(f"  {'#':>2}  {'strategy':<58}{'mo+':>8}{'%pos':>7}{'worstMo':>10}{'maxDD':>9}{'totRet':>10}")
    p("  " + "-" * (W - 4))
    for i, x in enumerate(r2, 1):
        p(f"  {i:>2}  {x['strategy'][:57]:<58}{x['pos_months']:>4}/{x['n_months']:<3}"
          f"{x['pct_pos_months']:>6.0f}%{x['worst_month']*100:>9.1f}%{x['max_dd']*100:>8.1f}%"
          f"{x['total_return']*100:>9.0f}%")

    # ---------- DISAGREEMENT ----------
    p("\n\n" + "=" * W)
    p("  FULL-HISTORY vs POST-COVID — does the ranking materially disagree?")
    p("=" * W)
    rank_full = {f["strategy"]: i for i, f in enumerate(r1, 1)}
    rank_pc = {x["strategy"]: i for i, x in enumerate(r2, 1)}
    common = [s for s in rank_full if s in rank_pc]
    p(f"  {'strategy':<58}{'full#':>7}{'pc#':>6}{'Δrank':>7}   note")
    p("  " + "-" * (W - 4))
    for s in sorted(common, key=lambda s: rank_pc[s]):
        d = rank_full[s] - rank_pc[s]
        flag = ""
        if d >= 3:
            flag = "↑ looks much BETTER post-COVID than over full history"
        elif d <= -3:
            flag = "↓ looks much WORSE post-COVID than over full history"
        p(f"  {s[:57]:<58}{rank_full[s]:>7}{rank_pc[s]:>6}{d:>+7}   {flag}")

    # save
    RESULTS.mkdir(exist_ok=True)
    pd.DataFrame([{k: v for k, v in f.items() if not k.startswith("_")} for f in full]
                 ).to_csv(RESULTS / "year_by_year_full_history.csv", index=False)
    pd.DataFrame([{k: v for k, v in x.items() if not k.startswith("_")}
                  for x in postc if not x.get("empty")]
                 ).to_csv(RESULTS / "year_by_year_postcovid.csv", index=False)
    if not annual.empty:
        annual.drop(columns=["years"]).to_csv(RESULTS / "year_by_year_annual_R_only.csv", index=False)
    p(f"\n  saved: results/year_by_year_full_history.csv, year_by_year_postcovid.csv, "
      f"year_by_year_annual_R_only.csv")


if __name__ == "__main__":
    main()
