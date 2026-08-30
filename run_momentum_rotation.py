#!/usr/bin/env python3
"""
run_momentum_rotation.py -- Cross-sectional momentum rotation, tested per
STATE_OF_PLAY section 7 rule 3 doctrine: honesty gates including an
out-of-regime stress window, look-ahead guard, cost-inclusive net returns,
deflated Sharpe against a stated a priori pool, per-year concentration, and
a buy-and-hold SPY comparison -- full period AND stress window.

Grid (4 cells, a priori, stated -- no tuning beyond this):
    N in {6, 12} trailing months  x  K in {3, 5} top holdings

Data: data/momentum_universe_adjclose.csv (built by
scripts/download_momentum_universe.py), yfinance daily adjusted close,
max available history per ticker.

Windows:
    FULL    : entire available history (per-ticker start varies; see report)
    STRESS  : 2000-01-01 -> 2009-12-31, sealed, SAME 4 configs, unchanged
              parameters -- dot-com crash + financial crisis. Some ETFs
              (XLRE, XLC, GLD, EEM, and TLT/IEF for part of it) have no data
              this early; they are simply absent from the ranking pool on any
              date before their own inception, exactly as they would have
              been absent from a real 2000 portfolio. Stated, not backfilled.

Cumulative trial count: this batch adds 8 trials (4 FULL + 4 STRESS, the
project convention per STATE_OF_PLAY section 1 -- out-of-regime re-runs on
new/adjusted windows count as new trials, distinct from same-window
re-scorings). Prior count 622 -> 630.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe
from research.momentum_rotation import (
    UNIVERSE, BENCHMARK, DEFENSIVE, build_weights, simulate, look_ahead_guard,
    COST_BPS_PER_SIDE, SPREAD_BPS_PER_SIDE, COMMISSION_BPS_PER_SIDE,
)

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

BARS_PER_YEAR = 252
GRID = [(n, k) for n in (6, 12) for k in (3, 5)]
STRESS_START = pd.Timestamp("2000-01-01")
STRESS_END = pd.Timestamp("2009-12-31")
PRIOR_TRIALS = 622


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(DATA / "momentum_universe_adjclose.csv", index_col=0, parse_dates=True)
    df = df.sort_index()
    return df


def slice_window(s: pd.Series, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.Series:
    if start is not None:
        s = s[s.index >= start]
    if end is not None:
        s = s[s.index <= end]
    return s


def compute_metrics(net_ret: pd.Series, gross_ret: pd.Series, label: str) -> dict:
    net_ret = net_ret.dropna()
    gross_ret = gross_ret.dropna()
    if len(net_ret) < 30:
        return {"label": label, "n_obs": len(net_ret), "insufficient": True}

    equity = (1.0 + net_ret).cumprod()
    gross_equity = (1.0 + gross_ret).cumprod()

    net_sharpe = sharpe(net_ret, bars_per_year=BARS_PER_YEAR)
    gross_sharpe = sharpe(gross_ret, bars_per_year=BARS_PER_YEAR)
    net_pf = profit_factor(net_ret)
    gross_pf = profit_factor(gross_ret)
    mdd = max_drawdown(equity)
    years = len(net_ret) / BARS_PER_YEAR
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    gross_total_ret = gross_equity.iloc[-1] / gross_equity.iloc[0] - 1.0
    gross_cagr = (1 + gross_total_ret) ** (1 / years) - 1 if years > 0 else float("nan")

    # per-year concentration on log returns (additive)
    log_ret = np.log1p(net_ret)
    yearly = log_ret.groupby(net_ret.index.year).sum()
    total_log = yearly.sum()
    top_year_share = float(yearly.abs().max() / abs(total_log)) if total_log != 0 else float("nan")
    top_year = int(yearly.abs().idxmax())

    cost_frac_of_gross = float(1 - (total_ret / gross_total_ret)) if gross_total_ret not in (0, np.nan) else float("nan")

    return {
        "label": label, "n_obs": len(net_ret), "insufficient": False,
        "gross_sharpe": gross_sharpe, "net_sharpe": net_sharpe,
        "gross_pf": gross_pf, "net_pf": net_pf,
        "gross_cagr": gross_cagr, "net_cagr": cagr,
        "maxDD": mdd, "top_year": top_year, "top_year_share": top_year_share,
        "cost_pct_of_gross": cost_frac_of_gross * 100 if np.isfinite(cost_frac_of_gross) else float("nan"),
        "total_net_return": total_ret, "total_gross_return": gross_total_ret,
        "equity": equity,
    }


def spy_buy_hold(adjclose: pd.DataFrame, start, end) -> dict:
    px = slice_window(adjclose[BENCHMARK], start, end)
    ret = px.pct_change().dropna()
    equity = (1 + ret).cumprod()
    years = len(ret) / BARS_PER_YEAR
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    return {
        "sharpe": sharpe(ret, bars_per_year=BARS_PER_YEAR),
        "cagr": cagr, "maxDD": max_drawdown(equity), "total_return": total_ret,
        "n_obs": len(ret),
    }


def run_window(adjclose: pd.DataFrame, start, end, label: str) -> list[dict]:
    rows = []
    for n_months, top_k in GRID:
        weights_at_exec, turnover_at_exec = build_weights(adjclose, n_months, top_k)
        if len(weights_at_exec) == 0:
            rows.append({"N": n_months, "K": top_k, "window": label, "insufficient": True,
                          "note": "no valid rebalance dates (insufficient history)"})
            continue
        guard_pass = look_ahead_guard(weights_at_exec, adjclose, n_months)
        sim = simulate(adjclose, weights_at_exec, turnover_at_exec)

        gross_w = slice_window(sim["gross"], start, end)
        net_w = slice_window(sim["net"], start, end)
        m = compute_metrics(net_w, gross_w, label=f"N{n_months}_K{top_k}_{label}")
        m.update({"N": n_months, "K": top_k, "window": label, "look_ahead_guard_pass": guard_pass,
                   "n_rebalances_in_window": int(((weights_at_exec.index >= (start or weights_at_exec.index.min())) &
                                                   (weights_at_exec.index <= (end or weights_at_exec.index.max()))).sum())})
        rows.append(m)
    return rows


def main():
    print("Loading momentum universe panel ...")
    adjclose = load_panel()
    print(f"Panel: {adjclose.shape[0]} rows x {adjclose.shape[1]} cols, "
          f"{adjclose.index[0].date()} -> {adjclose.index[-1].date()}")
    for t in UNIVERSE + [BENCHMARK]:
        first_valid = adjclose[t].first_valid_index()
        print(f"  {t}: data from {first_valid.date() if first_valid is not None else 'MISSING'}")

    # ── FULL PERIOD ──────────────────────────────────────────────────────────
    print("\n=== FULL PERIOD ===")
    full_rows = run_window(adjclose, None, None, "FULL")

    # ── STRESS WINDOW 2000-2009 ─────────────────────────────────────────────
    print("\n=== STRESS WINDOW 2000-01-01 -> 2009-12-31 ===")
    print("Tickers with data covering all/part of the stress window:")
    for t in UNIVERSE + [BENCHMARK]:
        fv = adjclose[t].first_valid_index()
        if fv is None:
            continue
        if fv <= STRESS_END:
            coverage = "FULL" if fv <= STRESS_START else f"PARTIAL from {fv.date()}"
            print(f"  {t}: {coverage}")
        else:
            print(f"  {t}: NOT AVAILABLE until {fv.date()} -- absent from stress-window ranking entirely")
    stress_rows = run_window(adjclose, STRESS_START, STRESS_END, "STRESS")

    # ── BENCHMARKS ───────────────────────────────────────────────────────────
    bh_full = spy_buy_hold(adjclose, None, None)
    bh_stress = spy_buy_hold(adjclose, STRESS_START, STRESS_END)
    print(f"\nSPY buy-and-hold FULL: Sharpe {bh_full['sharpe']:.3f}, CAGR {bh_full['cagr']*100:.2f}%, "
          f"maxDD {bh_full['maxDD']*100:.2f}%, n_obs {bh_full['n_obs']}")
    print(f"SPY buy-and-hold STRESS: Sharpe {bh_stress['sharpe']:.3f}, CAGR {bh_stress['cagr']*100:.2f}%, "
          f"maxDD {bh_stress['maxDD']*100:.2f}%, n_obs {bh_stress['n_obs']}")

    # ── DSR: structural pool = this batch's own a priori cells, per window ──
    def add_dsr(rows: list[dict]):
        valid = [r for r in rows if not r.get("insufficient")]
        sr_pool = np.array([r["net_sharpe"] for r in valid])
        for r in rows:
            if r.get("insufficient"):
                r["dsr"] = float("nan")
                continue
            res = deflated_sharpe(r["net_sharpe"], sr_pool, n_obs=r["n_obs"], ann_factor=BARS_PER_YEAR)
            r["dsr"] = res["dsr"]
            r["e_max_sr"] = res["e_max_sr"]

    add_dsr(full_rows)
    add_dsr(stress_rows)

    # ── ASSEMBLE CONFIG TABLE ───────────────────────────────────────────────
    table = []
    for fr in full_rows:
        sr = next((s for s in stress_rows if s["N"] == fr["N"] and s["K"] == fr["K"]), None)
        row = {
            "N_months": fr["N"], "K_holdings": fr["K"],
            "full_gross_cagr_pct": fr.get("gross_cagr", float("nan")) * 100 if not fr.get("insufficient") else float("nan"),
            "full_net_cagr_pct": fr.get("net_cagr", float("nan")) * 100 if not fr.get("insufficient") else float("nan"),
            "full_gross_sharpe": fr.get("gross_sharpe"),
            "full_net_sharpe": fr.get("net_sharpe"),
            "full_dsr": fr.get("dsr"),
            "full_maxDD_pct": fr.get("maxDD", float("nan")) * 100 if not fr.get("insufficient") else float("nan"),
            "full_top_year": fr.get("top_year"),
            "full_top_year_share_pct": fr.get("top_year_share", float("nan")) * 100 if not fr.get("insufficient") else float("nan"),
            "full_cost_pct_of_gross": fr.get("cost_pct_of_gross"),
            "full_vs_spy_bh_sharpe": (fr.get("net_sharpe") - bh_full["sharpe"]) if not fr.get("insufficient") else float("nan"),
            "full_beats_spy_bh": (fr.get("net_sharpe", -99) > bh_full["sharpe"]) if not fr.get("insufficient") else False,
            "look_ahead_guard_pass": fr.get("look_ahead_guard_pass"),
        }
        if sr is not None and not sr.get("insufficient"):
            row.update({
                "stress_gross_sharpe": sr.get("gross_sharpe"),
                "stress_net_sharpe": sr.get("net_sharpe"),
                "stress_dsr": sr.get("dsr"),
                "stress_maxDD_pct": sr.get("maxDD", float("nan")) * 100,
                "stress_net_cagr_pct": sr.get("net_cagr", float("nan")) * 100,
                "stress_top_year_share_pct": sr.get("top_year_share", float("nan")) * 100,
                "stress_vs_spy_bh_sharpe": sr.get("net_sharpe") - bh_stress["sharpe"],
                "stress_beats_spy_bh": sr.get("net_sharpe", -99) > bh_stress["sharpe"],
            })
        else:
            row.update({k: float("nan") for k in [
                "stress_gross_sharpe", "stress_net_sharpe", "stress_dsr", "stress_maxDD_pct",
                "stress_net_cagr_pct", "stress_top_year_share_pct", "stress_vs_spy_bh_sharpe"]})
            row["stress_beats_spy_bh"] = False
        table.append(row)

    df_table = pd.DataFrame(table)
    df_table.to_csv(RESULTS / "momentum_rotation_configs.csv", index=False)
    print("\n=== CONFIG TABLE (4 cells) ===")
    print(df_table.to_string(index=False))

    # ── VERDICT ──────────────────────────────────────────────────────────────
    print("\n=== SURVIVAL GATES ===")
    survivors = []
    for row in table:
        gates = {
            "dsr_gt_0.95": (row["full_dsr"] > 0.95) if np.isfinite(row["full_dsr"]) else False,
            "top_year_le_60pct": (row["full_top_year_share_pct"] <= 60) if np.isfinite(row["full_top_year_share_pct"]) else False,
            "beats_spy_full": row["full_beats_spy_bh"],
            "beats_spy_stress": row["stress_beats_spy_bh"],
            "stress_dsr_gt_0.95": (row["stress_dsr"] > 0.95) if np.isfinite(row.get("stress_dsr", float("nan"))) else False,
        }
        survives = all(gates.values())
        print(f"N={row['N_months']} K={row['K_holdings']}: {gates} -> {'SURVIVES' if survives else 'fails'}")
        if survives:
            survivors.append(row)

    print(f"\nSurvivors: {len(survivors)}/4")
    if survivors:
        print("Config(s) that cleared every gate:")
        for s in survivors:
            print(f"  N={s['N_months']} K={s['K_holdings']}")
    else:
        print("VERDICT: KILL. No config clears the full deflated-Sharpe + concentration + "
              "out-of-regime buy-and-hold bar.")

    # save trade/return series for audit
    RESULTS.joinpath("momentum_rotation_summary.txt").write_text(
        df_table.to_string(index=False) + "\n\nSPY B&H FULL: " + str(bh_full) +
        "\nSPY B&H STRESS: " + str(bh_stress) + "\n"
    )
    print(f"\nSaved: {RESULTS / 'momentum_rotation_configs.csv'}")
    print(f"Cumulative trial count: {PRIOR_TRIALS} + 8 (4 FULL + 4 STRESS) = {PRIOR_TRIALS + 8}")


if __name__ == "__main__":
    main()
