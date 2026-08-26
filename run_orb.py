#!/usr/bin/env python3
"""
run_orb.py — the OPENING RANGE BREAKOUT at the US CASH OPEN (09:30 ET),
tested cost-inclusively on real Dukascopy M1 with a real spread.

WHY RUN A BREAKOUT AT ALL, AFTER SECTION 1 KILLED THE FAMILY
-------------------------------------------------------------
The prior sweeps killed a GENERIC breakout: an arbitrary rolling range on an
arbitrary timeframe, plus one London-opening-range gold variant anchored to
07:00-08:00 UTC. Not one of those isolates the US cash open. The ORB claim is
narrower and specific: the 09:30 ET auction concentrates overnight information
into a short high-volume window, and the first extension beyond that window
persists. That proposition has never been run in this repo, and external
evidence (a documented NQ ORB survivor) says this particular version can clear
honest gates where the generic family did not. So it gets one clean test.

GRID (small, a priori, stated — breadth not depth)
--------------------------------------------------
    2 instruments (NAS100, US30)
  x 2 opening ranges (15 min, 30 min)
  x 3 targets (1R, 2R, hold-to-close)
  = 12 configs THIS BATCH.

Stop is always the opposite side of the opening range, so 1R IS the OR range.
There is no numeric optimisation anywhere in this script.

SPX500 IS ABSENT, AND THAT IS A DATA FACT, NOT A CHOICE
--------------------------------------------------------
The repo holds SPX500 at H1 only (data/SPX500_H1_*.csv). A 15-minute opening
range cannot be built from hourly bars, so SPX500 cannot be tested here without
a fresh multi-hundred-MB M1 pull. NAS100 and US30 are the two indices with M1 in
BOTH windows, which is also what makes the out-of-regime re-run possible.

COSTS — and the one place this study departs from the repo default
-------------------------------------------------------------------
Indices use the engine's bps model: REAL per-bar spread from the data
(round-turn) + 0.35 bps commission (round-turn) + per-side slippage. The
departure is slippage. The engine's default NEWS_HOURS_UTC windows are fixed in
UTC, so under EST they END at exactly 09:30 ET — every winter ORB entry would be
charged NORMAL slippage in the single most volatile minute of its day. That is
an artefact of a UTC-defined rule meeting an ET-defined strategy, so this run
supplies its own ET-anchored slippage function:

    entries 09:30-10:30 ET : 1.00 bps per side   (the opening hour)
    entries after 10:30 ET : 0.15 bps per side   (the repo normal figure)

1.00 bps per side is deliberately punitive: it is 2x the repo's existing "news"
figure and ~6.7x normal, and on NAS100 at 20,000 it is 2 index points of slip
per side on a stop order. A 0.50 bps sensitivity (the repo news figure) is
printed alongside — it is a RE-SCORING of the same 12 configs, not 12 more
trials, so it does not enter the DSR pool.

GATES (all must pass; FTMO is deliberately absent — section 1 closed that)
--------------------------------------------------------------------------
  1. look-ahead guard PASS, plus an ORB-specific assertion that no entry exists
     before the opening range is complete.
  2. gross PF > 1 — is there an edge BEFORE costs at all?
  3. net PF > 1 and positive net Sharpe (correctly annualised, 252 daily obs).
  4. DSR > 0.95 against a STATED STRUCTURAL pool (this batch's 12 a priori
     cells). The project-cumulative pool is printed for CONTRAST only —
     research/dsr.py BUG 2 documents that it is sigma-contaminated.
  5. OOS holds across the fixed split.
  6. NOT single-year concentrated (top calendar year <= 60% of total net R).
     This is the signature that killed the index basket and the Sneaky Pivot.
  7. Beats buy-and-hold the same index over the same window.

Gate 8 — OUT OF REGIME — is run separately by run_orb_pre2018.py, per
STATE_OF_PLAY section 7 rule 3. Nothing here is a lead until it survives that.

Usage:  py -3.14 run_orb.py            (full run)
        py -3.14 run_orb.py --analyze  (re-score from CSV, no 300 MB reload)
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from strategies.orb import orb, OR_MINUTES, TARGETS, RTH_OPEN_MIN, ET

BARS_PER_YEAR = 252
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
WINDOW_LABEL = "2018-2025"
MIN_OOS_TRADES = 20
DSR_BAR = 0.95
CONC_BAR = 0.60          # top single year may not exceed 60% of total net R

# Cumulative trial count carried by the project before this batch (STATE_OF_PLAY section 1).
PRIOR_TRIALS = 475
PRIOR_CSVS = [
    "sweep_progress.csv",                   # 75  gold family sweep
    "htf_breakout.csv",                     # 12  HTF-gated breakout
    "sweep_indices.csv",                    # 150 US index sweep
    "basket_configs.csv",                   # 108 index trend basket 2018-25
    "basket_configs_scored_pre2018.csv",    # 90  pre-2018 out-of-regime basket
    "sneaky_pivot.csv",                     # 24  sneaky pivot 2018-25
    "sneaky_pivot_pre2018.csv",             # 16  sneaky pivot out of regime
]

# ── cost model ───────────────────────────────────────────────────────────────
COMMISSION_BPS = 0.35       # round-turn, index CFD, repo standard
SLIP_OPEN_BPS = 1.00        # per side, entries 09:30-10:30 ET (the opening hour)
SLIP_NORMAL_BPS = 0.15      # per side, entries after 10:30 ET (repo standard)
SLIP_SENSITIVITY_BPS = 0.50 # per side, the alternative opening-hour figure

OPEN_WINDOW_END_MIN = 10 * 60 + 30      # 10:30 ET


def slip_bps(ts: pd.Timestamp) -> float:
    """Per-side slippage in bps, defined in ET so it does not drift across DST.

    The opening hour of the US cash session is the widest, fastest tape of the
    day and ORB fires stop orders into it by construction. Charging the repo's
    normal 0.15 bps there would flatter this strategy specifically.
    """
    et = pd.Timestamp(ts).tz_convert(ET)
    m = et.hour * 60 + et.minute
    return SLIP_OPEN_BPS if RTH_OPEN_MIN <= m < OPEN_WINDOW_END_MIN else SLIP_NORMAL_BPS


def in_open_window(ts) -> bool:
    et = pd.Timestamp(ts).tz_convert(ET)
    m = et.hour * 60 + et.minute
    return bool(RTH_OPEN_MIN <= m < OPEN_WINDOW_END_MIN)


COST_BPS = dict(commission=COMMISSION_BPS,
                slip_normal=SLIP_NORMAL_BPS, slip_news=SLIP_OPEN_BPS)

INSTRUMENTS = {
    "NAS100": (_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv", COST_BPS),
    "US30":   (_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",   COST_BPS),
}

OUT_CSV = _ROOT / "results" / "orb.csv"
SCORED_CSV = _ROOT / "results" / "orb_scored.csv"
TRADES_CSV = _ROOT / "results" / "orb_trades.csv"


# ── scoring ──────────────────────────────────────────────────────────────────
def _split_stats(trades: pd.DataFrame) -> tuple:
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < OOS_SPLIT, exit_t >= OOS_SPLIT

    def pf(mask):
        return profit_factor(trades.loc[mask, "net_R"]) if mask.any() else float("nan")

    def sr(mask):
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, BARS_PER_YEAR) if len(d) > 1 else float("nan")

    return int(is_m.sum()), int(oos_m.sum()), pf(is_m), pf(oos_m), sr(is_m), sr(oos_m)


def _year_concentration(trades: pd.DataFrame) -> tuple[float, float, int, int]:
    """(top-year net R, top year as a share of total net R, #years, #positive years).

    Share is only meaningful when the total is positive; it is reported as NaN
    otherwise so a losing config cannot be waved through by an undefined ratio.
    """
    yr = pd.to_datetime(trades["exit_time"], utc=True).dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    total = float(agg.sum())
    top = float(agg.max()) if len(agg) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return top, share, int(len(agg)), int((agg > 0).sum())


def score(m1: pd.DataFrame, params: dict, daily_index, cost_bps) -> tuple[dict, pd.DataFrame]:
    empty = pd.DataFrame()
    cands = orb(m1, params)
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty

    # ORB-SPECIFIC LOOK-AHEAD ASSERTION: no candidate may be armed before the
    # opening range that defines it is complete. This is checked on the
    # candidates themselves, independently of the statistical guard below.
    ent = pd.DatetimeIndex([c["entry_time"] for c in cands]).tz_convert(ET)
    ent_min = ent.hour * 60 + ent.minute
    earliest_legal = RTH_OPEN_MIN + int(params["or_minutes"])
    or_ok = bool((ent_min >= earliest_legal).all())

    # strictly_after=False on purpose: resolution INCLUDES the breakout minute, so
    # the trade is charged that minute's own adverse excursion (a spike through the
    # OR high that collapses back through the OR low inside the same bar is taken as
    # a stop, via the engine's stop-first tie rule). That is the conservative side of
    # the choice and it leaks nothing — the fill level is a resting stop order known
    # before the bar opens. Skipping the entry bar would quietly hand the strategy a
    # free minute of the most volatile tape of the day.
    trades = de_overlap(simulate_trades(m1, cands, strictly_after=False,
                                        cost_bps=cost_bps, slip_bps_fn=slip_bps))
    if trades.empty:
        return dict(n_cands=len(cands), n_trades=0, guard="N/A"), empty

    pos = build_position_series(trades, m1.index)
    try:
        guard_look_ahead(pos, m1["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS" if or_ok else "FAIL:OR-window"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_stats(trades)
    top_R, top_share, n_years, n_pos_years = _year_concentration(trades)

    return dict(
        n_cands=len(cands), n_trades=len(trades), guard=guard,
        or_entry_min=int(ent_min.min()), or_entry_legal_min=earliest_legal,
        n_long=int((trades["side"] == "long").sum()),
        n_short=int((trades["side"] == "short").sum()),
        gross_pf=profit_factor(trades["gross_R"]),
        net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        net_R_total=float(trades["net_R"].sum()),
        gross_R_total=float(trades["gross_R"].sum()),
        win_rate=float((trades["net_R"] > 0).mean()),
        risk_med=float(trades["risk_price"].median()),
        risk_med_bps=float((trades["risk_price"] / trades["entry_mid"]).median() * 1e4),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)),
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        top_year_R=top_R, top_year_share=top_share,
        n_years=n_years, n_pos_years=n_pos_years,
    ), trades


def buy_and_hold(daily: pd.DataFrame) -> dict:
    """Daily buy-and-hold on the same file, mid prices, spread crossed once."""
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread_close"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def main():
    rows, bh, ledger = [], {}, []
    for inst, (path, cost_bps) in INSTRUMENTS.items():
        if not path.exists():
            print(f"[{inst}] MISSING {path.name} — skipped.", flush=True)
            continue
        print(f"[{inst}] loading M1 ...", flush=True)
        spot = load_m1_spot(path)
        daily = aggregate_daily(spot)
        daily_index = daily.index
        bh[inst] = buy_and_hold(daily)
        m1 = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m1["spread"] = spot["spread"]
        m1["volume"] = spot["volume"]
        del spot
        print(f"[{inst}] {len(m1):,} M1 bars {m1.index[0].date()} -> {m1.index[-1].date()} "
              f"| median spread {m1['spread'].median():.3f} "
              f"({m1['spread'].median() / m1['mid_close'].median() * 1e4:.2f} bps) "
              f"| B&H SR {bh[inst]['sharpe']:+.2f}", flush=True)

        for n_or in OR_MINUTES:
            for target in TARGETS:
                p = dict(or_minutes=n_or, target=target)
                res, tr = score(m1, p, daily_index, cost_bps)
                rows.append(dict(instrument=inst, **p, **res))
                if not tr.empty:
                    ledger.append(tr.assign(instrument=inst, **p))
                print(f"  {inst:>6} OR={n_or:>2}m tgt={target:<5} "
                      f"cands={res.get('n_cands', 0):>4} n={res.get('n_trades', 0):>4} "
                      f"grPF={res.get('gross_pf', float('nan')):.3f} "
                      f"netPF={res.get('net_pf', float('nan')):.3f} "
                      f"SR={res.get('sharpe', float('nan')):+.2f} "
                      f"guard={res.get('guard', '?')[:4]}", flush=True)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    trades_all = pd.concat(ledger, ignore_index=True) if ledger else pd.DataFrame()
    if not trades_all.empty:
        trades_all.to_csv(TRADES_CSV, index=False)
    analyze(df, bh, trades_all)


def _prior_sharpes() -> tuple[np.ndarray, str]:
    vals, notes = [], []
    for name in PRIOR_CSVS:
        p = _ROOT / "results" / name
        if p.exists():
            s = pd.to_numeric(pd.read_csv(p)["sharpe"], errors="coerce").dropna().to_numpy()
            vals.append(s)
            notes.append(f"{name}:{len(s)}")
        else:
            notes.append(f"{name}:MISSING")
    arr = np.concatenate(vals) if vals else np.array([])
    return arr, ", ".join(notes)


KEYS = ["instrument", "or_minutes", "target"]


def per_year(trades_all: pd.DataFrame, traded: pd.DataFrame):
    """Year-by-year net R for EVERY config. Single-year concentration is a gate
    here, not a footnote — it is what killed the index basket and the Sneaky
    Pivot, and a blended Sharpe hides it completely."""
    if trades_all.empty:
        return
    print("\n  YEAR-BY-YEAR net R, ALL configs (single-year concentration = gate 6)")
    years = sorted(pd.to_datetime(trades_all["exit_time"], utc=True).dt.year.unique())
    head = "  " + f"{'config':<26}" + "".join(f"{y:>8}" for y in years) + f"{'total':>9}{'top%':>7}"
    print(head)
    print("  " + "-" * (len(head) - 2))
    for _, b in traded.sort_values("sharpe", ascending=False).iterrows():
        m = np.ones(len(trades_all), dtype=bool)
        for k in KEYS:
            m &= (trades_all[k].astype(str) == str(b[k])).to_numpy()
        t = trades_all[m]
        if t.empty:
            continue
        yr = pd.to_datetime(t["exit_time"], utc=True).dt.year
        agg = t.groupby(yr)["net_R"].sum()
        label = f"{b['instrument']} OR{int(b['or_minutes'])} {b['target']}"
        share = b.get("top_year_share", float("nan"))
        print(f"  {label:<26}" + "".join(f"{agg.get(y, 0.0):>+8.1f}" for y in years)
              + f"{agg.sum():>+9.1f}"
              + (f"{share * 100:>6.0f}%" if np.isfinite(share) else f"{'n/a':>7}"))
    print("  Read: net R per calendar year. 'top%' = best single year as a share of the")
    print(f"  total; > {CONC_BAR:.0%} fails gate 6. 'n/a' means the total is <= 0, so the ratio")
    print("  is undefined — that is a worse outcome than concentration, not a pass.")


def cost_sensitivity(trades_all: pd.DataFrame, traded: pd.DataFrame):
    """Re-score the SAME trades at the alternative opening-hour slippage figure.

    This is a re-scoring, not new configs: it adds nothing to the DSR pool. It
    exists because the 1.00 bps opening-hour figure is a judgement call, and the
    reader is entitled to see how much of the verdict rests on it.
    """
    if trades_all.empty:
        return
    d_bps = SLIP_OPEN_BPS - SLIP_SENSITIVITY_BPS
    t = trades_all.copy()
    is_open = t["entry_time"].map(in_open_window)
    # cost falls by 2 sides x d_bps on trades entered inside the opening hour
    delta_R = np.where(is_open, 2.0 * d_bps / 1e4 * t["entry_mid"] / t["risk_price"], 0.0)
    t["net_R_alt"] = t["net_R"] + delta_R

    print(f"\n  COST SENSITIVITY — opening-hour slippage {SLIP_OPEN_BPS:.2f} bps/side "
          f"(headline) vs {SLIP_SENSITIVITY_BPS:.2f} bps/side (repo news figure)")
    print(f"  {'config':<26} {'costR%':>7} {'netPF':>7} | {'costR%':>7} {'netPF':>7} "
          f"{'d netPF':>8}  {'open-hr entries':>16}")
    print("  " + "-" * 88)
    for _, b in traded.sort_values("sharpe", ascending=False).iterrows():
        m = np.ones(len(t), dtype=bool)
        for k in KEYS:
            m &= (t[k].astype(str) == str(b[k])).to_numpy()
        sub = t[m]
        if sub.empty:
            continue
        alt_cost = sub["cost_R"] - (sub["net_R_alt"] - sub["net_R"])
        pf_alt = profit_factor(sub["net_R_alt"])
        label = f"{b['instrument']} OR{int(b['or_minutes'])} {b['target']}"
        print(f"  {label:<26} {sub['cost_R'].mean() * 100:>6.1f}% {b['net_pf']:>7.3f} | "
              f"{alt_cost.mean() * 100:>6.1f}% {pf_alt:>7.3f} {pf_alt - b['net_pf']:>+8.3f}  "
              f"{is_open[m].mean() * 100:>15.0f}%")


def analyze(df: pd.DataFrame, bh: dict, trades_all: pd.DataFrame | None = None):
    traded = df[df.get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch

    prior, prior_note = _prior_sharpes()
    sr_batch = traded["sharpe"].fillna(0.0).to_numpy()
    pool_project = np.concatenate([prior, sr_batch]) if prior.size else sr_batch

    def _dsr(r, pool):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
            return np.nan
        return deflated_sharpe(
            sr_best=float(r["sharpe"]), sr_trials=pool, n_obs=int(r["n_obs"]),
            skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
            excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0,
        )["dsr"]

    traded["dsr"] = traded.apply(lambda r: _dsr(r, sr_batch), axis=1)
    traded["dsr_cumulative_pool"] = traded.apply(lambda r: _dsr(r, pool_project), axis=1)
    e_struct = expected_max_sharpe(sr_batch)
    e_cumul = expected_max_sharpe(pool_project)

    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["not_concentrated"] = (traded["top_year_share"].notna()
                                  & (traded["top_year_share"] <= CONC_BAR))
    traded["beats_bh"] = traded.apply(
        lambda r: bool(np.isfinite(r["sharpe"]) and r["instrument"] in bh
                       and r["sharpe"] > bh[r["instrument"]]["sharpe"]), axis=1)
    traded["SURVIVOR"] = (traded["gross_edge"] & (traded["net_pf"] > 1.0)
                          & (traded["sharpe"] > 0) & (traded["dsr"] > DSR_BAR)
                          & traded["oos_holds"] & traded["not_concentrated"]
                          & traded["beats_bh"] & (traded["guard"] == "PASS"))

    W = 128
    print("\n" + "=" * W)
    print(f"  OPENING RANGE BREAKOUT — US CASH OPEN 09:30 ET | real Dukascopy M1 with spread, {WINDOW_LABEL}")
    print("  OR = first N min after 09:30 America/New_York (per-bar DST-correct); entry = stop order at the OR")
    print("  extreme, armed only from 09:30+N; stop = opposite side of the OR (so 1R = the OR range);")
    print("  flat at the 16:00 ET cash close; ONE position per day per instrument.")
    print(f"  Cost: REAL per-bar spread (round-turn) + {COMMISSION_BPS} bps commission + "
          f"{SLIP_OPEN_BPS}/{SLIP_NORMAL_BPS} bps per-side slippage (09:30-10:30 ET / after), "
          f"1% risk/trade, NO tuning")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS (DSR N): "
          f"{PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print(f"  DSR pool (HEADLINE) = STRUCTURAL: this batch's {len(sr_batch)} a priori cells "
          f"-> E[max SR] {e_struct[0]:+.3f} (mu {e_struct[2]:+.3f}, sd {e_struct[3]:.3f})")
    print(f"  DSR pool (CONTRAST) = project-cumulative {len(pool_project)} "
          f"[{prior_note}] -> E[max SR] {e_cumul[0]:+.3f} (mu {e_cumul[2]:+.3f}, sd {e_cumul[3]:.3f})")
    print("                        ^ NOT a gate: sigma-contaminated by legacy structurally-doomed")
    print("                          configs (research/dsr.py BUG 2). Shown so the difference is visible.")
    print(f"  Gates: guard PASS + gross PF>1 + net PF>1 + SR>0 + DSR>{DSR_BAR} + OOS holds "
          f"+ top year <= {CONC_BAR:.0%} of net R + beats B&H")
    print("=" * W)

    if traded.empty:
        print("  NO config produced a single trade. Check the setup filter before reading anything into this.")
        return

    print(f"  {'inst':>6} {'OR':>3} {'target':>6} {'cands':>5} {'trades':>6} "
          f"{'grPF':>6} {'netPF':>6} {'Sharpe':>7} {'DSR':>5} {'maxDD':>6} {'win%':>5} "
          f"{'costR%':>7} {'top%':>5} {'OOS?':>4} {'B&H?':>5} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
        share = r["top_year_share"]
        print(f"  {r['instrument']:>6} {int(r['or_minutes']):>3} {r['target']:>6} "
              f"{int(r['n_cands']):>5} {int(r['n_trades']):>6} "
              f"{r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} {r['sharpe']:>+7.2f} "
              f"{r['dsr']:>5.2f} {r['max_dd'] * 100:>5.1f}% {r['win_rate'] * 100:>4.1f}% "
              f"{r['cost_R_mean'] * 100:>6.1f}% "
              + (f"{share * 100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
              + f" {'YES' if r['oos_holds'] else 'no':>4} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:5]:>5}")
    print("=" * W)

    print("\n  GROSS vs NET R — is there an edge BEFORE costs? (the test that killed the last lead)")
    print(f"  {'inst':>6} {'OR':>3} {'target':>6} {'grossR/trd':>11} {'costR/trd':>10} "
          f"{'netR/trd':>9} {'cost as %R':>11} {'1R (bps)':>9} {'tgt/stop/time':>14}")
    print("  " + "-" * 92)
    for _, r in traded.sort_values(["instrument", "or_minutes", "target"]).iterrows():
        mix = f"{int(r['n_targets'])}/{int(r['n_stops'])}/{int(r['n_time'])}"
        print(f"  {r['instrument']:>6} {int(r['or_minutes']):>3} {r['target']:>6} "
              f"{r['gross_R_mean']:>+11.4f} {r['cost_R_mean']:>10.4f} {r['net_R_mean']:>+9.4f} "
              f"{r['cost_R_mean'] * 100:>10.1f}% {r['risk_med_bps']:>9.1f} {mix:>14}")

    if trades_all is not None and not trades_all.empty:
        cost_sensitivity(trades_all, traded)

    survivors = traded[traded["SURVIVOR"]]
    best = traded.sort_values("sharpe", ascending=False).iloc[0]

    print("\n  VERDICT")
    print("  " + "-" * 90)
    if len(survivors):
        print(f"  {len(survivors)} config(s) cleared every gate in this window:")
        for _, r in survivors.iterrows():
            print(f"    {r['instrument']} OR{int(r['or_minutes'])} tgt={r['target']}: "
                  f"SR {r['sharpe']:+.2f}, DSR {r['dsr']:.3f}, grossPF {r['gross_pf']:.3f}, "
                  f"netPF {r['net_pf']:.3f}, IS PF {r['is_pf']:.2f} / OOS PF {r['oos_pf']:.2f}, "
                  f"top year {r['top_year_share'] * 100:.0f}%")
        print("\n  NOT A LEAD YET — STATE_OF_PLAY section 7 rule 3: the 2013-2017 out-of-regime")
        print("  re-run (run_orb_pre2018.py) must be passed before any of this is believed.")
    else:
        print("  NO config cleared all gates.")
        print(f"  Best raw net Sharpe: {best['instrument']} OR{int(best['or_minutes'])} "
              f"tgt={best['target']} -> SR {best['sharpe']:+.2f}")
        print(f"    - gross PF {best['gross_pf']:.3f} -> "
              f"{'edge exists before costs' if best['gross_pf'] > 1 else 'NO edge even before costs'}")
        print(f"    - net PF   {best['net_pf']:.3f}  (cost {best['cost_R_mean'] * 100:.1f}% of 1R)")
        print(f"    - DSR {best['dsr']:.3f} (need > {DSR_BAR}) -> "
              f"{'PASS' if best['dsr'] > DSR_BAR else 'FAIL: inside the noise of this batch'}")
        print(f"    - OOS holds: {'YES' if best['oos_holds'] else 'NO'} "
              f"(IS PF {best['is_pf']:.2f} / OOS PF {best['oos_pf']:.2f}, "
              f"OOS SR {best['oos_sharpe']:+.2f}, OOS trades {int(best['oos_trades'])})")
        share = best["top_year_share"]
        print(f"    - single-year concentration: "
              + (f"top year = {share * 100:.0f}% of net R "
                 f"({'PASS' if share <= CONC_BAR else 'FAIL'}, bar {CONC_BAR:.0%})"
                 if np.isfinite(share) else "n/a — total net R <= 0"))
        print(f"    - vs buy-and-hold: {'BEATS' if best['beats_bh'] else 'LOSES TO'} it")

    print("\n  vs BUY-AND-HOLD (same file, same window):")
    for inst, b in bh.items():
        sub = traded[traded["instrument"] == inst]
        if sub.empty:
            continue
        s = sub.sort_values("sharpe", ascending=False).iloc[0]
        print(f"    {inst:>6}: best strategy SR {s['sharpe']:+.2f} (maxDD {s['max_dd'] * 100:.1f}%) "
              f"vs B&H SR {b['sharpe']:+.2f} (maxDD {b['max_dd'] * 100:.1f}%) -> "
              f"{'BEATS' if s['sharpe'] > b['sharpe'] else 'LOSES TO'} B&H")

    if trades_all is not None:
        per_year(trades_all, traded)

    print("\n  Batch summary:")
    print(f"    look-ahead guard    : {(traded['guard'] == 'PASS').sum()} / {len(traded)} PASS")
    print(f"    gross PF > 1        : {(traded['gross_pf'] > 1).sum()} / {len(traded)}")
    print(f"    net PF > 1          : {(traded['net_pf'] > 1).sum()} / {len(traded)}")
    print(f"    positive net Sharpe : {(traded['sharpe'] > 0).sum()} / {len(traded)}")
    print(f"    OOS holds           : {traded['oos_holds'].sum()} / {len(traded)}")
    print(f"    not year-concentrated: {traded['not_concentrated'].sum()} / {len(traded)}")
    print(f"    beats buy-and-hold  : {traded['beats_bh'].sum()} / {len(traded)}")
    print(f"    clears DSR haircut  : {(traded['dsr'] > DSR_BAR).sum()} / {len(traded)} "
          f"(structural pool; contaminated cumulative pool: {(traded['dsr_cumulative_pool'] > DSR_BAR).sum()})")
    print(f"    SURVIVORS (all gates): {int(traded['SURVIVOR'].sum())} / {len(traded)}")
    print(f"\n  Results -> {OUT_CSV}\n  Scored  -> {SCORED_CSV}")

    traded.to_csv(SCORED_CSV, index=False)


def analyze_only():
    df = pd.read_csv(OUT_CSV)
    trades_all = pd.read_csv(TRADES_CSV) if TRADES_CSV.exists() else pd.DataFrame()
    if not trades_all.empty:
        for c in ("entry_time", "exit_time"):
            trades_all[c] = pd.to_datetime(trades_all[c], utc=True)
    bh = {}
    for inst, (path, _) in INSTRUMENTS.items():
        if path.exists():
            bh[inst] = buy_and_hold(aggregate_daily(load_m1_spot(path)))
    analyze(df, bh, trades_all)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--analyze" in sys.argv:
        analyze_only()
    else:
        main()
