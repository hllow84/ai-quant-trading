"""
combined_book_risk_parity.py — §51: risk-parity (inverse-volatility)
re-weighting of all five combined-book pairings tested in §44/§47/§48/
§49/§50, replacing the fixed 50/50 nominal-capital weight with a weight
inversely proportional to each leg's own daily-return volatility.

MOTIVATION: §49 flagged this directly as an open question. ORB gold's
standalone volatility is ~3x US30 breakout's, so a fixed 50/50 NOMINAL-
CAPITAL split let gold dominate the combined book's realized risk despite
its 50% capital share — muting the benefit of the lowest correlation
found in any pairing (+0.011). Risk parity (w_i proportional to 1/sigma_i)
equalizes each leg's contribution to portfolio variance instead of its
capital share — for two assets, this is EXACT when correlation is zero
and a close approximation at the near-zero correlations found throughout
this project (+0.011 to +0.074).

METHOD: reuses the already-saved per-leg daily-return CSVs from each of
the five prior sections UNCHANGED (no re-running any backtest) — this is
pure re-weighting of already-computed return series, not a new parameter
search. w_A = (1/std_A) / (1/std_A + 1/std_B), w_B = 1 - w_A, computed
ONCE from each leg's full-sample daily-return std (an in-sample weight
choice, stated plainly — a true walk-forward risk-parity scheme would
re-estimate weights on a rolling basis, not attempted here since the
question was whether risk-parity in principle recovers §49's lost
benefit, not to build a deployable rebalancing scheme).

Zero new trials — a re-weighting of five already-scored portfolio checks,
no parameter search. Cumulative trial count (N=1570) unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown
from research.ftmo_engine import equity_from_returns

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252

PAIRS = [
    dict(name="§44 NAS100+US30 macross", file="macross_h4_combined_book.csv",
         legA="nas100_ret", legB="us30_ret", labA="NAS100 macross", labB="US30 macross"),
    dict(name="§47 NAS100+US30 breakout", file="breakout_h4_combined_book.csv",
         legA="nas100_ret", legB="us30_ret", labA="NAS100 breakout", labB="US30 breakout"),
    dict(name="§48 US30 macross+breakout", file="us30_macross_breakout_combined_book.csv",
         legA="us30_macross_ret", legB="us30_breakout_ret", labA="US30 macross", labB="US30 breakout"),
    dict(name="§49 ORB gold+US30 breakout", file="orb_gold_us30_breakout_combined_book.csv",
         legA="orb_gold_ret", legB="us30_breakout_ret", labA="ORB gold", labB="US30 breakout"),
    dict(name="§50 NAS100 macross+breakout", file="nas100_macross_breakout_combined_book.csv",
         legA="nas100_macross_ret", legB="nas100_breakout_ret", labA="NAS100 macross", labB="NAS100 breakout"),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    rows = []
    for p in PAIRS:
        df = pd.read_csv(RESULTS / p["file"], parse_dates=["date"]).set_index("date")
        a, b = df[p["legA"]], df[p["legB"]]

        std_a, std_b = a.std(), b.std()
        w_a = (1.0 / std_a) / (1.0 / std_a + 1.0 / std_b)
        w_b = 1.0 - w_a

        fixed = 0.5 * a + 0.5 * b
        rp = w_a * a + w_b * b

        sh_fixed, dd_fixed = sharpe(fixed, BARS_PER_YEAR), max_drawdown(equity_from_returns(fixed))
        sh_rp, dd_rp = sharpe(rp, BARS_PER_YEAR), max_drawdown(equity_from_returns(rp))

        sh_a = sharpe(a[a != 0], BARS_PER_YEAR) if (a != 0).any() else float("nan")
        sh_b = sharpe(b[b != 0], BARS_PER_YEAR) if (b != 0).any() else float("nan")

        print(f"=== {p['name']} ===")
        print(f"  std({p['labA']})={std_a:.5f}  std({p['labB']})={std_b:.5f}  "
              f"-> risk-parity weights: {p['labA']}={w_a:.2f} / {p['labB']}={w_b:.2f}")
        print(f"  Fixed 50/50:    Sharpe={sh_fixed:+.3f}  maxDD={dd_fixed*100:.1f}%")
        print(f"  Risk-parity:    Sharpe={sh_rp:+.3f}  maxDD={dd_rp*100:.1f}%")
        print(f"  Delta (RP - fixed): Sharpe {sh_rp - sh_fixed:+.3f}, maxDD {(dd_rp - dd_fixed)*100:+.1f}pp\n")

        rows.append(dict(pair=p["name"], w_a=w_a, w_b=w_b,
                          sharpe_fixed=sh_fixed, maxdd_fixed=dd_fixed,
                          sharpe_rp=sh_rp, maxdd_rp=dd_rp))

    out = RESULTS / "combined_book_risk_parity.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (re-weighting of already-scored portfolio checks, "
          "no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
