# STATE OF PLAY — AI Quant Trading Lab

**Last updated: 2026-07-22.** Read this file first in any new session. It is the
standalone briefing: where the research stands, what was settled, what is still
open, and which files matter. `research_log.md` holds the per-test detail;
`CLAUDE.md` holds the standing working rules.

---

## 1. BOTTOM LINE — the FTMO hunt is concluded, and the answer is no

**Across 345 systematic backtest configurations, no FTMO-viable edge was found.**

Trial composition (this is the cumulative DSR trial count, N=345):

| Batch | Instrument(s) | Configs | Outcome |
|---|---|---|---|
| Family sweep (5 fam × 5 TF) | XAUUSD | 75 | 0 survive |
| HTF-trend-gated breakout | XAUUSD | 12 | 0 survive |
| US index sweep (5 fam × 5 TF × 2) | NAS100, US30 | 150 | 0 survive |
| Index trend basket (2 fam × 3 TF × 6) | 6 indices | 108 | 0 survive |
| **Total** | | **345** | **0 survive** |

Separate from that count, and also negative: 6 crypto factor studies (5 kills +
1 overfit), 3 intraday gold FTMO strategies, 3 swing gold FTMO strategies, and 2
SMA-200 baselines. Best FTMO Phase-1 pass rate ever observed across all of it:
**5.3%**, against a 30% bar. Most configs score 0.0%.

### The structural reason it fails (this is the useful part)

The failure is not bad luck across strategies — it is a vice with two jaws:

- **Fast strategies die on cost.** At M5–M15 the stop distance is small, so
  cost-to-risk runs 21–60% of 1R. On gold, commission alone ($0.07/oz) exceeded
  the entire gross edge of the best breakout variant. No signal quality fixes
  this.
- **Cost-surviving strategies die on FTMO's clock.** Widening stops to H4/D1
  cuts cost_R to 1–5% — the cost problem is genuinely solved — but those trades
  hold for days to weeks. FTMO Phase 1 wants ~10% in 60 days without a 5% daily
  or 10% total drawdown. Swing systems cannot get there; they trade too rarely
  and their drawdowns arrive at the wrong times.

**Anything that survives retail costs holds too long to pass FTMO; anything fast
enough for FTMO does not survive costs.** Do not spend more time on FTMO
price-pattern variants. That question is answered.

---

## 2. THE ONE REAL LEAD — diversified index trend-following (own capital, not FTMO)

A 6-index equal-risk basket on the **macross** family is the only thing in this
project that beat a buy-and-hold benchmark on a risk-adjusted basis.

**Best basket — H4 macross v2, 6 indices, equal risk:**

| Metric | Basket | EW B&H basket | Best single B&H (NAS100) |
|---|---|---|---|
| Net Sharpe | **+0.80** | +0.63 | +0.84 |
| Max drawdown | **7.8%** | 32.3% | 35.7% |
| CAGR | 4.0% | 10.8% | 18.3% |
| Annual vol | 4.1% | 14.9% | — |
| Net PF | 1.20 | — | — |
| IS / OOS Sharpe | +0.70 / +0.95 | — | — |
| cost_R | ~1.9% of 1R | — | — |

**What is genuinely good here:**
- Beats the equal-weight B&H basket by +0.17 Sharpe with **4× lower drawdown**.
- Holds out of sample (IS +0.70 → OOS +0.95), 1,440 trades.
- Costs are a non-issue at last: ~1% of R at D1, ~2% at H4.
- **Diversification mechanically works.** Mean pairwise member correlation is
  **0.02–0.14** — the six index trends are near-independent. 11 of 18 baskets
  beat their *average* member (mean uplift +0.078 Sharpe; best cell: basket 0.80
  vs average member 0.41).

**Why it is NOT a green light — three independent reservations:**

1. **DSR 0.21–0.45, against a 0.95 bar.** With the corrected gate (§4), no
   config or basket is statistically distinguishable from the best-of-N you would
   expect by chance. The edge is real in-sample but not *proven*.
2. **The Sharpe win is not a return win.** At 1% risk/trade the basket runs 4.1%
   vol vs B&H's 14.9%. Matching B&H volatility needs **~3.7× leverage** →
   ~14.6% CAGR at ~28.9% maxDD. Financing cost and overnight gap risk at 3.7×
   are **not modelled**. Levered performance is unproven, not merely unreported.
3. **OOS > IS is suspicious in our favour.** Most baskets score higher out of
   sample than in (H8 macross v2: IS +0.34 → OOS +1.34). 2023–25 was a strong
   index trend regime. That is regime tailwind, not demonstrated robustness.

**Verdict: real but modest. Own-capital candidate, not an FTMO strategy**
(basket FTMO pass rate 1.1%). It needs the work in §5 before any capital.

---

## 3. KEY FINDING — macross is the edge; trend-continuation is not

The two families both look like "trend following" and behave oppositely.

| | macross | trend-continuation |
|---|---|---|
| Basket mean Sharpe | **+0.438** | **−0.072** |
| Single-name mean Sharpe | **+0.231** | −0.020 |
| Mean Sharpe by TF (H4 / H8 / D1) | +0.300 / +0.294 / +0.099 | −0.078 / −0.051 / +0.070 |
| Positive-Sharpe configs | 37/54 | 28/54 |

macross is **positive at every timeframe**. Trend-continuation averages ~zero and
is *negative* at H4 and H8.

⚠️ **Precision matters here:** the single best config in the whole batch *is* a
trend config (NAS100 D1 trend v0, Sharpe +1.07). That is an outlier, not a family
property — the same family's worst config is −0.904. Trend-continuation is
high-variance and centred on zero; macross is consistently positive. Judge the
family by its distribution, not its best member.

**Any follow-up should drop trend-continuation and carry macross forward.**

---

## 4. THE DSR FIX — old DSR numbers are unreliable

`research/metrics.py::deflated_sharpe_ratio` was broken **two independent ways**.
It returned exactly `0.0000` or `1.0000` in essentially every study in this repo,
which is the signature of a broken statistic, not a universe without edge.

1. **Units bug (caused the saturation).** Numerator `(sr_best − E[maxSR])` was in
   annualised Sharpe units; denominator was the standard error of the
   *per-period* Sharpe. Measured: SE 0.0313 where it should be 0.3376 — **10.8×
   too small**. Every z-score was inflated ~11–16×, collapsing DSR to a step
   function at E[maxSR]. The Mertens (2002) variance was also mis-stated as
   `1 + (1 − …)` = `2 − …`, dropping the `0.5·SR²` term and adding a spurious +1.
2. **Contaminated deflation pool.** E[maxSR] scales with pool σ. The 237-trial
   pool included M5 configs at Sharpe −14.6, giving σ=3.39 and **E[maxSR] =
   +6.78** — a bar nothing can clear. The haircut was being set by how badly the
   *worst* configs failed.

**Corrected module: `research/dsr.py`.** Use `deflated_sharpe()` with an
explicitly stated pool:
- `structural_pool()` — selects on *a priori* structure (TF × family cells that
  were genuine candidates before results were seen). **This is the headline
  gate**; it carries no outcome information.
- `floor_pool()` — Sharpe ≥ floor. **Sensitivity check only.** Filtering on
  realised Sharpe is selection-on-outcome: it cuts the left tail, shrinks σ,
  lowers E[maxSR] and makes passing *easier*. Never use it as the headline.

`metrics.py` was **deliberately left untouched** so historical crypto verdicts
are not silently restated.

**Effect:** prior index top-15 → 0/15 clear DSR > 0.95. Best went 0.0000 → 0.227
(E[maxSR] +0.921 on the structural pool). The gate now spreads across 0.02–0.45
instead of saturating.

> ⚠️ **Every DSR figure in `research_log.md` dated before 2026-07-22 is
> unreliable.** The kill verdicts mostly still stand — they failed on other
> grounds too (FTMO pass rate, B&H comparison, negative gross edge) — but the DSR
> numbers themselves came from a broken statistic. Re-derive with
> `recompute_dsr.py` before citing any of them.

---

## 5. OPEN NEXT STEPS (if this continues)

**Do NOT** run more FTMO price-pattern variants, more timeframe sweeps, or more
single-instrument gold work. Those surfaces are exhausted; §1 explains why.

If work continues, it is on the §2 lead, for **own capital**:

1. **Proper volatility targeting.** Replace fixed 1% risk/trade with a target
   portfolio vol (e.g. 10–15% annualised) so the basket is comparable to B&H
   without a post-hoc leverage multiplier.
2. **Model leverage and financing honestly.** At ~3.7× the CFD financing spread,
   margin mechanics and overnight gap risk materially change the result. Until
   modelled, the "beats B&H" claim only holds risk-adjusted, not in cash.
3. **Regime robustness on pre-2018 data.** The whole sample is 2018–2025 and OOS
   > IS suggests regime luck. Pull 2005–2018 (covering 2008 and the 2015–16
   drawdowns) and re-test unchanged. This is the single highest-value next test —
   it is the one that can actually kill the lead.
4. **Widen the basket.** More near-independent trends is the mechanism that
   works (corr 0.02–0.14). Candidates already verified in the Dukascopy enum:
   `fraidxeur` (CAC40), `eusidxeur` (EuroStoxx50), `ausidxaud` (ASX200),
   `cheidxchf` (SMI), `ussc2000idxusd` (Russell 2000).
5. **macross only.** Drop trend-continuation (§3).

A useful framing for next session: the lead's problem is no longer cost, and no
longer signal — it is **statistical strength and regime dependence**. Steps 3 and
1 attack exactly those.

---

## 6. DATA + CODE INVENTORY

### Merged data files (`data/`) — ALL GITIGNORED, must be re-downloaded

⚠️ **A fresh clone has NO data CSVs.** They exceed GitHub limits or are bulky, so
`.gitignore` excludes them. **All download scripts are resumable** (`.done`
markers per file) — re-running skips completed work, so an interrupted pull costs
nothing.

| File | Size | Content | Rebuild with |
|---|---|---|---|
| `XAUUSD_M1_2018_2025_spot_dukascopy.csv` | 250 MB | Gold M1 SPOT, real bid/ask + spread | `scripts/download_xauusd.sh` → `scripts/merge_xauusd.py` |
| `NAS100_M1_2018_2025_cfd_dukascopy.csv` | 312 MB | Nasdaq-100 M1 CFD | `scripts/download_indices.sh` → `scripts/merge_indices.py` |
| `US30_M1_2018_2025_cfd_dukascopy.csv` | 299 MB | Dow-30 M1 CFD | same as above |
| `NAS100_H1_…csv`, `US30_H1_…csv` | ~5 MB ea | H1 base, **derived from the M1 files** | `scripts/merge_basket.py` |
| `GER40_H1_…csv`, `UK100_H1_…csv`, `JP225_H1_…csv`, `SPX500_H1_…csv` | ~6 MB ea | H1 bid/ask CFD, downloaded directly | `scripts/download_basket.sh` → `scripts/merge_basket.py` |

All files: UTC, real bid+ask OHLC plus a real `spread` column, 2018-01 → 2025-12.

**Verified Dukascopy instrument IDs** (from the `dukascopy-node` enum, each
confirmed by price probe — never guess these):

| ID | Instrument | Probe check (2024-03-04) |
|---|---|---|
| `usatechidxusd` | Nasdaq-100 | 18,306 ✓ |
| `usa30idxusd` | Dow-30 | 39,052 ✓ |
| `usa500idxusd` | S&P 500 | 5,064–5,164 ✓ |
| `deuidxeur` | Germany 40 / DAX | 17,640–17,762 ✓ |
| `gbridxgbp` | UK 100 / FTSE | 7,599–7,682 ✓ |
| `jpnidxjpy` | Japan 225 / Nikkei | 39,756–40,246 ✓ |

### Runners (repo root)

| File | What it does |
|---|---|
| `run_sweep.py` | XAUUSD 75-config family sweep (5 families × 5 TF) |
| `run_htf_breakout.py` | XAUUSD 12-config HTF-trend-gated breakout |
| `run_sweep_indices.py` | NAS100/US30 150-config sweep; `--analyze` re-prints without re-running |
| `run_basket_trend.py` | **Current lead.** 6 indices × H4/H8/D1 × trend+macross = 108 configs + 18 equal-risk baskets + benchmarks |
| `recompute_dsr.py` | Recomputes DSR under the corrected gate; prints old vs fixed side by side |
| `run_ftmo.py`, `run_ftmo_swing.py` | Gold FTMO strategies A/B/C, intraday and swing |
| `baseline_gold_spot.py` | SMA-200 gold baseline vs buy-and-hold (supersedes `baseline_sma200.py`) |
| `run.py` | Crypto factor research CLI (walk-forward harness) |

### Engine / research modules (`research/`)

| File | What it does |
|---|---|
| `dsr.py` | **Corrected DSR** + pool selection. Use this, not `metrics.py`'s version |
| `metrics.py` | Sharpe/Sortino/Calmar/PF/drawdown. Its `deflated_sharpe_ratio` is the OLD broken one — left intact deliberately |
| `ftmo_engine.py` | Event-driven trade simulator: real spread + commission + news slippage, 1% risk, `de_overlap`, position series for the guard |
| `ftmo_rules.py` | FTMO Phase-1 simulation (5% daily / 10% total DD, target, min days, rolling monthly starts) |
| `gold_data.py` | Loaders: `load_m1_spot`, `load_m1_mid`, `resample_mid`, `aggregate_daily`. Used for every instrument despite the name |
| `backtest.py` | Vectorized engine + `guard_look_ahead` (wired in, default on) |
| `walkforward.py`, `optimize.py`, `preprocess.py`, `signals.py`, `report.py` | Crypto factor harness |
| `strategies/sweep_families.py` | The 5 vectorized families + stated variant grids |

### Pipeline scripts (`scripts/`)

Chained runners execute download → merge → **verify (hard gate)** → sweep in a
single process, launched detached via the `.cmd` wrapper:
`run_all_indices.sh`/`.cmd`, `run_all_basket.sh`/`.cmd`.

`verify_indices.py` / `verify_basket.py` are **hard gates**: they check first
*and* last bar, that all 8 years are present, that the spread column is real, and
that prices are in band. They exit 1 and block the sweep on failure. These exist
because a partial merge once produced a file *named* `2018_2025` that actually
held only 386k rows ending 2019-12-31 — a backtest would have silently run on two
years instead of eight.

### Results (`results/`) — tracked in git as of 2026-07-22

`sweep_progress.csv`, `htf_breakout*.csv`, `sweep_indices*.csv`,
`leaderboard_indices.csv`, `basket_configs_scored.csv`, `basket_results.csv`,
`dsr_recomputed.csv`, plus `pipeline_*.log`. ~330 KB total — this is the numeric
evidence behind every claim above.

### Operational notes

- **Launch long jobs detached** via `Start-Process` on the `.cmd` wrapper. Do not
  use `Start-Process` with a nested-quoted path directly to `bash -lc` — it exits
  instantly without running. Do not use a separate watcher process; the original
  index run died at 27/32 files because the watcher and downloader were killed
  together when the terminal closed.
- `resume_indices.txt` has the one-line restart for the index pipeline.
- Environment: Python 3.14, pandas/numpy/scipy/matplotlib, Node/npx for
  `dukascopy-node`. Banned permanently: `vectorbt`, QuantConnect API,
  `yfinance GC=F` (futures, no real spread).
