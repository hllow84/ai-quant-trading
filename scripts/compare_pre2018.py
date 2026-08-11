#!/usr/bin/env python3
"""compare_pre2018.py — side-by-side of the index-trend lead in and out of regime.

Three columns, deliberately:
  orig6  2018-2025, 6 indices, split 2023-01-01 — the PUBLISHED lead (STATE_OF_PLAY §2)
  new5   2018-2025, 5 indices, split 2022-01-01 — matched baseline, GER40 removed
  pre2018 2013-2017, 5 indices, split 2016-01-01 — the out-of-regime test

orig6 vs new5 isolates the cost of dropping GER40 and moving the split; new5 vs
pre2018 is then a clean REGIME comparison with basket membership held fixed.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
R = ROOT / "results"
LEAD = dict(timeframe="H4", family="macross", variant=2)


def load(tag):
    return pd.read_csv(R / f"basket_results_{tag}.csv")


def cell(df, **k):
    m = pd.Series(True, index=df.index)
    for c, v in k.items():
        m &= df[c] == v
    return df[m].iloc[0] if m.any() else None


def main():
    frames = {"orig6": pd.read_csv(R / "basket_results.csv"),
              "new5": load("new5"), "pre2018": load("pre2018")}
    W = 96
    print("=" * W)
    print("  OUT-OF-REGIME TEST — H4 macross v2 basket, the STATE_OF_PLAY §2 lead")
    print("=" * W)
    hdr = f"  {'metric':<22}{'orig6 2018-25':>16}{'new5 2018-25':>16}{'pre2018 2013-17':>18}"
    print(hdr)
    print("  " + "-" * (W - 4))
    rows = [("members", "n_members", "{:.0f}"), ("trades", "n_trades", "{:.0f}"),
            ("net Sharpe", "sharpe", "{:+.3f}"), ("net PF", "net_pf", "{:.3f}"),
            ("gross PF", "gross_pf", "{:.3f}"), ("max drawdown", "max_dd", "{:.1%}"),
            ("CAGR", "cagr", "{:.2%}"), ("ann vol", "ann_vol", "{:.1%}"),
            ("mean member corr", "mean_member_corr", "{:.3f}"),
            ("IS Sharpe", "is_sharpe", "{:+.3f}"), ("OOS Sharpe", "oos_sharpe", "{:+.3f}"),
            ("OOS holds", "oos_holds", "{}"), ("DSR (structural)", "dsr", "{:.3f}"),
            ("cost_R mean", "cost_R_mean", "{:.2%}")]
    cells = {t: cell(f, **LEAD) for t, f in frames.items()}
    for label, col, fmt in rows:
        vals = []
        for t in ("orig6", "new5", "pre2018"):
            c = cells[t]
            v = "-" if c is None or col not in c else (
                str(c[col]) if fmt == "{}" else fmt.format(float(c[col])))
            vals.append(v)
        print(f"  {label:<22}{vals[0]:>16}{vals[1]:>16}{vals[2]:>18}")

    print("\n" + "=" * W)
    print("  DOES ANYTHING SURVIVE OUT OF REGIME? (all 18 baskets per window)")
    print("=" * W)
    print(f"  {'window':<10}{'best SR':>10}{'best cell':>22}{'SR>0':>7}{'netPF>1':>9}"
          f"{'OOS-holds':>11}{'DSR>0.95':>10}")
    print("  " + "-" * (W - 4))
    for t in ("orig6", "new5", "pre2018"):
        f = frames[t]
        b = f.loc[f["sharpe"].idxmax()]
        name = f"{b['timeframe']} {b['family']} v{int(b['variant'])}"
        print(f"  {t:<10}{b['sharpe']:>+10.3f}{name:>22}{int((f['sharpe'] > 0).sum()):>7}"
              f"{int((f['net_pf'] > 1).sum()):>9}{int(f['oos_holds'].astype(str).eq('True').sum()):>11}"
              f"{int((f['dsr'] > 0.95).sum()):>10}")

    print("\n" + "=" * W)
    print("  FAMILY MEANS — is macross still the edge out of regime?")
    print("=" * W)
    print(f"  {'window':<10}{'macross mean SR':>18}{'trend mean SR':>16}{'macross-trend':>16}")
    print("  " + "-" * (W - 4))
    for t in ("orig6", "new5", "pre2018"):
        f = frames[t]
        mm = f[f.family == "macross"]["sharpe"].mean()
        tm = f[f.family == "trend"]["sharpe"].mean()
        print(f"  {t:<10}{mm:>+18.3f}{tm:>+16.3f}{mm - tm:>+16.3f}")
    print("=" * W)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
