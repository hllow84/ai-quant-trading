#!/usr/bin/env python3
"""
report_winrate_over_50.py  --  STATE_OF_PLAY section 23 (REPORTING ONLY).

Scans every SAVED backtest-result CSV in results/ and lists every config
whose NET per-trade win rate is strictly above 50%, regardless of whether
the config was ultimately killed. No backtest is re-run; nothing is added
to the cumulative trial count (N = 946, unchanged).

win_rate in the scored CSVs = fraction of trades with net R > 0 (verified
against the raw trade files for ORB: orb_scored win_rate matches
(net_R>0).mean() on results/orb_trades.csv to 3 dp).

avg win / avg loss (in R) are reconstructed exactly from (win_rate, net_pf,
net_R_mean):
    B = net_R_mean / (net_pf - 1)          # loss_rate * avg_loss
    A = net_pf * B                         # win_rate  * avg_win
    avg_win  =  A / win_rate
    avg_loss = -B / (1 - win_rate)
This is an identity, not an approximation, given the definitions of
win_rate, net_pf and net_R_mean. Cross-checked against ORB raw trades:
NAS100 OR15 1R -> reconstructed +0.868 / -1.006 R vs trade-level
+0.868 / -1.006 R.

Portfolio / period strategies (momentum rotation sec12/12.2/17, volatility
premium sec20/21) have NO per-trade win rate; they are reported in a
SEPARATE table using "% of calendar years with a positive absolute return"
as the period analogue, taken from results/year_by_year_full_history.csv
(the reslice already saved in section 22). The section 12.5 walk-forward
recent-sub-period breakout is taken from
results/momentum_rotation_walkforward.csv (already saved, not recomputed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).parent / "results"


# ── (csv, section, batch, window, kill-code, stop_mode filter) ─────────────
# kill-code legend printed under Table A
TRADE_SOURCES = [
    ("orb_scored.csv", "10", "ORB @ US cash open (OR-range stop)", "in 2018-25",
     "OOS-INV + CONC + B&H + DSR", None),
    ("orb_scored_pre2018.csv", "10", "ORB @ US cash open (OR-range stop)", "OOS 2013-17",
     "OOS-INV + DSR", None),
    ("orb_rerun_in_scored.csv", "10.2", "ORB moderate 25bps-stop variant", "in 2018-25",
     "WORSENED-IN + OOS-INV + CONC + B&H + DSR", "moderate"),
    ("orb_rerun_out_scored.csv", "10.2", "ORB moderate 25bps-stop variant", "OOS 2013-17",
     "OOS-INV + DSR", "moderate"),
    ("orb_trend_in_regime_scored.csv", "10.4", "ORB trend-filtered variant (daily 50-SMA gate)", "in 2018-25",
     "OOS-INV + CONC + DSR", None),
    ("orb_trend_out_regime_scored.csv", "10.4", "ORB trend-filtered variant", "OOS 2013-17",
     "OOS-INV + DSR", None),
    ("sweep_stocks_scored.csv", "14", "Individual US stocks, 5-family sweep", "in 2018-25",
     "DSR + B&H", None),
    ("sweep_stocks_pre2018_scored.csv", "14", "Individual US stocks, 5-family sweep", "OOS 2010-17",
     "DSR + B&H", None),
    ("basket_configs_scored.csv", "2", "Index trend/macross single-instrument config", "in 2018-25",
     "OOS-INV(family) + DSR", None),
    ("basket_configs_scored_pre2018.csv", "6", "Index trend/macross single-instrument config", "OOS 2013-17",
     "OOS-INV(family) + DSR", None),
    ("sweep_indices_scored.csv", "1", "Gold/index 5-family sweep (150 cfg)", "2018-25", "COST + DSR", None),
    ("htf_breakout_scored.csv", "1", "XAUUSD HTF-trend-gated breakout (12 cfg)", "2018-25", "COST", None),
    ("sweep_m1_scored.csv", "11", "M1 row, 5-family (45 cfg)", "in 2018-25", "GROSS<1", None),
    ("sweep_m1_pre2018_scored.csv", "11", "M1 row, 5-family", "OOS 2013-17", "GROSS<1", None),
    ("sweep_crypto_scored.csv", "13", "Crypto BTC/ETH 5-family x 3 TF (90 cfg)", "2018-25", "COST", None),
    ("positioning_reversal_scored.csv", "18", "Positioning-extreme reversal (funding+OI)", "BTC/ETH 20-26",
     "NEG-EDGE", None),
    ("sneaky_pivot_scored.csv", "9", "15-min Sneaky Pivot (24 cfg)", "in 2018-25", "COST + DSR", None),
    ("sneaky_pivot_scored_pre2018.csv", "9.4", "15-min Sneaky Pivot", "OOS 2013-17", "COST + CONC", None),
]

KILL_LEGEND = {
    "OOS-INV": "gross edge inverts / collapses on the 2013-17 out-of-regime window",
    "OOS-INV(family)": "whole index-basket family's gross PF collapses 1.363->1.006 out of regime (sec6)",
    "CONC": "single-year P&L concentration (one year > 60-100%+ of total net R)",
    "B&H": "loses to simple buy-and-hold of the instrument",
    "DSR": "deflated Sharpe never approaches 0.95 vs the batch's own a-priori pool",
    "COST": "gross edge too small to pay real transaction costs",
    "GROSS<1": "gross profit factor below 1.00 - no edge even before costs",
    "WORSENED-IN": "the moderate-stop redesign made the in-regime result strictly worse",
    "NEG-EDGE": "net edge negative; DSR pool uniformly bad",
}

SKIP_FILE_NOTE = {
    "sweep_progress.csv": ("1", "XAUUSD 5-family sweep (75 cfg)",
        "no win_rate column was ever saved for this batch - only gross/net PF, Sharpe, IS/OOS. "
        "Win rate for these 75 configs is NOT recoverable from saved results."),
}

# per-batch kill context, one line, for the write-up
BATCH_KILL = {
    "10": "sec10: OOS gross PF inverts to 0.960 (2013-17); single-year concentration 0/12; loses to B&H 4/4; DSR 0/12",
    "10.2": "sec10.2: the 25bps moderate stop made in-regime net-PF>1 fall 5/12->2/12; all other kills unchanged",
    "10.4": "sec10.4: the daily-50-SMA trend filter fixed neither failure mode (OOS gross <1; concentration still fails); DSR 0/12",
    "14": "sec14: DSR never approaches 0.95 in EITHER window (best 0.45 in / 0.19 out); most cells lose to buy-and-hold. Most durable GROSS edge in the project.",
    "2": "sec2/sec6: this was the project's lead; sec6 out-of-regime test collapsed the family gross PF 1.363->1.006 (regime artifact); DSR 0.21-0.45",
    "6": "sec6: the out-of-regime test itself - macross lead Sharpe flips negative on 2013-17; 0/18 baskets clear DSR",
}


def reconstruct_win_loss(win_rate, net_pf, net_R_mean):
    if not np.isfinite(net_pf) or abs(net_pf - 1.0) < 1e-9:
        return float("nan"), float("nan")
    B = net_R_mean / (net_pf - 1.0)         # loss_rate * avg_loss   (R)
    A = net_pf * B                          # win_rate  * avg_win    (R)
    avg_win = A / win_rate if win_rate else float("nan")
    avg_loss = -B / (1.0 - win_rate) if win_rate < 1 else float("nan")
    return avg_win, avg_loss


def id_string(row) -> str:
    bits = []
    for c in ("instrument", "timeframe", "or_minutes", "target", "family", "variant", "stop_mode"):
        if c in row and pd.notna(row[c]):
            v = row[c]
            if c == "or_minutes":
                v = f"OR{int(v)}"
            elif c == "variant":
                v = f"v{v}"
            elif c == "stop_mode":
                if v == "or_range":
                    continue
                v = f"[{v} stop]"
            bits.append(str(v))
    return " ".join(bits)


def scan_trades():
    rows = []
    for csv, sec, batch, window, killcode, stopfilt in TRADE_SOURCES:
        p = R / csv
        if not p.exists():
            continue
        d = pd.read_csv(p)
        if "win_rate" not in d.columns:
            continue
        if stopfilt is not None and "stop_mode" in d.columns:
            d = d[d["stop_mode"] == stopfilt]          # only the genuinely-new variant rows
        hi = d[d["win_rate"] > 0.50].copy()
        for _, r in hi.iterrows():
            sharpe = r.get("sharpe", r.get("net_sharpe", np.nan))
            aw, al = reconstruct_win_loss(r["win_rate"], r.get("net_pf", np.nan), r.get("net_R_mean", np.nan))
            rows.append(dict(
                section=sec, strategy=batch, config=id_string(r), window=window,
                win_rate=float(r["win_rate"]) * 100.0,
                avg_win_R=aw, avg_loss_R=al,
                net_pf=float(r.get("net_pf", np.nan)),
                net_sharpe=float(sharpe) if pd.notna(sharpe) else np.nan,
                net_R_mean=float(r.get("net_R_mean", np.nan)),
                n_trades=int(r.get("n_trades", 0)),
                kill_code=killcode,
                _src=csv,
            ))
    return pd.DataFrame(rows).sort_values("win_rate", ascending=False)


def period_table():
    p = R / "year_by_year_full_history.csv"
    d = pd.read_csv(p)
    keep = d[d["strategy"].str.startswith(("MomoRot", "VRP"))].copy()
    # per-year avg pos / avg neg where a saved per-year file exists
    extra = {}
    wf = pd.read_csv(R / "momentum_rotation_walkforward.csv")
    yrs = wf["strat_return_pct"].to_numpy() / 100.0
    extra["MomoRot US-sector §12 (N12/K5, headline)"] = (
        float(np.mean(yrs[yrs > 0])), float(np.mean(yrs[yrs <= 0])))
    vrp = pd.read_csv(R / "vol_risk_premium.csv")
    for _, rr in vrp.iterrows():
        ycols = [c for c in vrp.columns if c.startswith("yr_")]
        v = np.expm1(rr[ycols].astype(float).to_numpy())   # stored as log returns
        lab = f"VRP naked SVXY §20 (thr {rr['threshold']})"
        extra[lab] = (float(np.mean(v[v > 0])), float(np.mean(v[v <= 0])))
    out = []
    for _, r in keep.iterrows():
        ap, an = extra.get(r["strategy"], (np.nan, np.nan))
        out.append(dict(
            strategy=r["strategy"],
            span=f"{r['first'][:4]}-{r['last'][:4]}",
            pct_pos_years=r["pct_pos_years"],
            pos_years=f"{int(r['pos_years'])}/{int(r['n_years'])}",
            avg_pos_year=ap * 100 if np.isfinite(ap) else np.nan,
            avg_neg_year=an * 100 if np.isfinite(an) else np.nan,
            best_year=r["best_year"] * 100, worst_year=r["worst_year"] * 100,
            total_return=r["total_return"] * 100, max_dd=r["max_dd"] * 100,
        ))
    df = pd.DataFrame(out).sort_values("pct_pos_years", ascending=False)
    return df


def momentum_recent_subperiods():
    wf = pd.read_csv(R / "momentum_rotation_walkforward.csv")
    wf = wf.sort_values("year")
    end = int(wf["year"].max())          # 2026 (partial)
    views = {
        "last 3 calendar years (2024-2026, 2026 partial to Aug)": wf[wf.year >= end - 2],
        "last 4 calendar years (2023-2026, 2026 partial to Aug)": wf[wf.year >= end - 3],
        "last 3 COMPLETE years (2023-2025)": wf[(wf.year >= 2023) & (wf.year <= 2025)],
    }
    rows = []
    for label, sub in views.items():
        s = sub["strat_return_pct"].to_numpy() / 100.0
        spy = sub["spy_return_pct"].to_numpy() / 100.0
        comp = float(np.prod(1 + s) - 1)
        comp_spy = float(np.prod(1 + spy) - 1)
        rows.append(dict(
            period=label, n_years=len(sub),
            pos_years=int((s > 0).sum()), win_rate_abs=100.0 * (s > 0).mean(),
            beat_spy_years=int(sub["beat_spy"].sum()), beat_spy_rate=100.0 * sub["beat_spy"].mean(),
            avg_year=float(np.mean(s)) * 100, worst_year=float(np.min(s)) * 100, best_year=float(np.max(s)) * 100,
            cum_return=comp * 100, cum_spy=comp_spy * 100,
            avg_within_year_sharpe=float(sub["strat_within_year_sharpe"].mean()),
        ))
    return pd.DataFrame(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    trades = scan_trades()
    period = period_table()
    recent = momentum_recent_subperiods()

    W = 150
    print("=" * W)
    print("  SECTION 23 - EVERY BACKTESTED CONFIG WITH NET WIN RATE > 50%  (reporting only, N=946 unchanged, nothing re-run)")
    print("=" * W)

    print("\n  TABLE A - TRADE-BASED CONFIGS WITH NET PER-TRADE WIN RATE > 50%, sorted by win rate desc")
    print("  avgWin / avgLoss in R (1R = config's own risk unit), reconstructed exactly from (winRate, netPF, netMeanR).")
    print("  netPF / netSR are AFTER real costs. 'kill' = compact code, legend below. '!thin' flags < 40 trades.")
    print("  " + "-" * (W - 4))
    hdr = (f"  {'sec':>5}  {'win%':>6} {'avgWin':>7} {'avgLoss':>8} {'netPF':>6} {'netSR':>7} {'nTr':>6}  "
           f"{'strategy':<44} {'config':<22} {'window':<11} kill")
    print(hdr)
    print("  " + "-" * (W - 4))
    for _, r in trades.iterrows():
        thin = " !thin" if r["n_trades"] < 40 else ""
        print(f"  {r['section']:>5}  {r['win_rate']:>5.1f}% {r['avg_win_R']:>+7.2f} {r['avg_loss_R']:>+8.2f} "
              f"{r['net_pf']:>6.2f} {r['net_sharpe']:>+7.2f} {r['n_trades']:>6d}  "
              f"{r['strategy'][:44]:<44} {r['config'][:22]:<22} {r['window']:<11} {r['kill_code']}{thin}")
    print("  " + "-" * (W - 4))
    print(f"  {len(trades)} trade-based configs have net win rate > 50%   "
          f"({int((trades['n_trades'] < 40).sum())} of them on < 40 trades - treat those win rates as noisy).")
    print("\n  KILL-CODE LEGEND:")
    for k, v in KILL_LEGEND.items():
        print(f"     {k:<16} {v}")

    print("\n  Batches scanned that produced NO config strictly above 50% win rate (max win rate in parentheses):")
    for csv, sec, batch, window, killcode, stopfilt in TRADE_SOURCES:
        p = R / csv
        if not p.exists():
            continue
        d = pd.read_csv(p)
        if "win_rate" not in d.columns:
            continue
        if stopfilt is not None and "stop_mode" in d.columns:
            d = d[d["stop_mode"] == stopfilt]
        if len(d) and (d["win_rate"] > 0.50).sum() == 0:
            print(f"     sec{sec:<5} {batch} [{window}] - max win rate {d['win_rate'].max()*100:.1f}%")
    for f, (sec, batch, note) in SKIP_FILE_NOTE.items():
        print(f"     sec{sec:<5} {batch} - {note}")

    print("\n\n  TABLE B - PORTFOLIO / PERIOD STRATEGIES (momentum rotation sec12/12.2/17, volatility premium sec20/21)")
    print("  These have NO per-trade win rate. Shown: % of CALENDAR YEARS with a positive absolute return")
    print("  (period analogue), from results/year_by_year_full_history.csv (section 22 reslice, not recomputed).")
    print("  " + "-" * (W - 4))
    print(f"  {'%pos yr':>8} {'pos/tot':>8} {'avgPosYr':>9} {'avgNegYr':>9} {'bestYr':>8} {'worstYr':>9} "
          f"{'totRet':>9} {'maxDD':>8}  strategy")
    print("  " + "-" * (W - 4))
    for _, r in period.iterrows():
        ap = f"{r['avg_pos_year']:>+8.1f}%" if np.isfinite(r['avg_pos_year']) else f"{'n/s':>9}"
        an = f"{r['avg_neg_year']:>+8.1f}%" if np.isfinite(r['avg_neg_year']) else f"{'n/s':>9}"
        print(f"  {r['pct_pos_years']:>7.1f}% {r['pos_years']:>8} {ap} {an} "
              f"{r['best_year']:>+7.0f}% {r['worst_year']:>+8.1f}% {r['total_return']:>+8.0f}% {r['max_dd']:>7.1f}%  {r['strategy']}")
    print("  (n/s = per-year series for avg pos/neg not separately saved; only summary stats were persisted in section 22)")

    print("\n\n  TABLE C - MOMENTUM ROTATION sec12 (N12/K5): RECENT SUB-PERIOD BREAKOUT (from sec12.5 walk-forward, resliced not re-run)")
    print("  " + "-" * (W - 4))
    print(f"  {'period':<52} {'yrs':>4} {'pos':>4} {'win%':>6} {'beatSPY':>8} {'avgYr':>7} {'worst':>7} {'best':>7} "
          f"{'cumRet':>8} {'cumSPY':>8} {'~yrSR':>6}")
    print("  " + "-" * (W - 4))
    for _, r in recent.iterrows():
        print(f"  {r['period']:<52} {r['n_years']:>4d} {r['pos_years']:>4d} {r['win_rate_abs']:>5.0f}% "
              f"{r['beat_spy_years']}/{r['n_years']:<2d}({r['beat_spy_rate']:>3.0f}%) {r['avg_year']:>+6.1f}% {r['worst_year']:>+6.1f}% "
              f"{r['best_year']:>+6.1f}% {r['cum_return']:>+7.1f}% {r['cum_spy']:>+7.1f}% {r['avg_within_year_sharpe']:>+6.2f}")

    print("\n\n" + "=" * W)
    print("  DID ANY CONFIG IN THE 946-TRIAL PROJECT HAVE WIN RATE > 50% *AND* SURVIVE EVERY HONESTY GATE?")
    print("=" * W)
    print("""
  NO. Zero configs in the entire project survived every gate (STATE_OF_PLAY sec1: "946 ... 0 survive"),
  so by construction nothing with win rate > 50% survived either. Of the {n} trade-based configs above
  50% win rate:
    - every ORB config (sec10 / 10.2 / 10.4): killed on out-of-regime gross-PF inversion + single-year
      concentration + loses-to-buy&hold; only ONE (NAS100 OR30 1R, 52.8% win) is even net-profitable
      in-sample (net PF 1.014, net Sharpe +0.09).
    - every individual-US-stock config (sec14, both windows): killed on DSR (never approaches 0.95 in
      either window) + loses to buy&hold. This is the project's most durable GROSS edge - and several
      of these have genuinely attractive win/PF (e.g. XOM D1 meanrev v1 2010-17: 73.3% win, net PF 4.44,
      net SR +0.91) - but a flat 90-cell DSR pool and simple buy&hold both bind.
    - every index trend/macross config (sec2 / 6): killed because the family's gross edge collapses
      out of regime (PF 1.363 -> 1.006, sec6) and DSR 0.21-0.45 never clears; the high-win-rate cells
      are all D1/H8 macross+trend, the exact cells sec6 showed were a 2018-2025 regime artifact.
  Portfolio strategies (Table B): several exceed 50% positive-YEARS (VRP fixed-fraction sleeves 81%,
  momentum rotation 74%, crypto-sector momentum 71%) but every one is killed too - VRP sec20/21 on
  tail risk / edge-shrinks-below-usefulness, momentum rotation sec12 on DSR and (sec12.5) a vs-SPY
  edge that is entirely pre-2009.
""".format(n=len(trades)))

    trades.drop(columns=["_src"]).to_csv(R / "winrate_over_50_trade_configs.csv", index=False)
    period.to_csv(R / "winrate_over_50_period_strategies.csv", index=False)
    recent.to_csv(R / "winrate_over_50_momentum_recent.csv", index=False)
    print(f"  saved: results/winrate_over_50_trade_configs.csv, winrate_over_50_period_strategies.csv, "
          f"winrate_over_50_momentum_recent.csv")


if __name__ == "__main__":
    main()
