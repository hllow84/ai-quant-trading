# STATE OF PLAY — AI Quant Trading Lab

**Last updated: 2026-08-11.** Read this file first in any new session. It is the
standalone briefing: where the research stands, what was settled, what is still
open, and which files matter. `research_log.md` holds the per-test detail;
`CLAUDE.md` holds the standing working rules.

> **2026-08-11 — THE LAST LEAD IS DEAD.** The diversified index-trend basket (§2)
> was re-run **unchanged** on 2013-2017 and its Sharpe flipped **+1.04 → −0.28**,
> with **gross PF collapsing to 1.006** — no edge even before costs. 2018-2025 was
> a favourable regime, not a discovered edge. §2 is retained below as a record of
> what was believed, with the kill stated inline. **There is now no live lead in
> this project.** See §7 for what that leaves.

---

## 1. BOTTOM LINE — the FTMO hunt is concluded, and the answer is no

**Across 435 systematic backtest configurations, no FTMO-viable edge was found —
and as of 2026-08-11, no own-capital edge either (§6).**

Trial composition (this is the cumulative DSR trial count, N=435):

| Batch | Instrument(s) | Configs | Outcome |
|---|---|---|---|
| Family sweep (5 fam × 5 TF) | XAUUSD | 75 | 0 survive |
| HTF-trend-gated breakout | XAUUSD | 12 | 0 survive |
| US index sweep (5 fam × 5 TF × 2) | NAS100, US30 | 150 | 0 survive |
| Index trend basket (2 fam × 3 TF × 6) | 6 indices | 108 | 0 survive |
| Pre-2018 out-of-regime (2 fam × 3 TF × 5) | 5 indices | 90 | 0 survive (§6) |
| **Total** | | **435** | **0 survive** |

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

## 2. ~~THE ONE REAL LEAD~~ — KILLED 2026-08-11 by the out-of-regime test

> ⚠️ **This section is a historical record.** Everything below was true of
> 2018-2025 and is reproduced unchanged so the reasoning can be audited. It did
> **not** survive §6. Read §6 before acting on any number in this section.

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

**Verdict (as of 2026-07-22): real but modest. Own-capital candidate, not an FTMO
strategy** (basket FTMO pass rate 1.1%). It needs the work in §5 before any capital.

> **Verdict as of 2026-08-11: KILLED.** Reservation 3 above — "OOS > IS is
> suspicious in our favour" — was the correct instinct. §6 tested it and it was
> regime, not robustness.

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

> **2026-08-11 update — this finding PARTIALLY survives the out-of-regime test.**
> On 2013-2017 macross still beats trend-continuation, by a similar margin
> (basket mean Sharpe **−0.233 vs −0.602**, gap +0.369, against +0.509 in regime).
> So the *relative ordering of the two families is robust across regimes.*
> **But both are negative out of regime.** macross being reliably less bad than
> trend-continuation is an ordering, not an edge. Do not read this section as
> "macross works" — read it as "if you ever trade one of these two, it is this
> one, and neither is currently tradeable."

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

## 5. THE PLAN OF 2026-07-22 — step 3 ran, and it ended the plan

The previous session listed five next steps. **Step 3 (regime robustness) was
explicitly flagged as "the one that can actually kill the lead." It was run on
2026-08-11, and it did.** See §6.

Steps 1, 2, 4 and 5 (vol targeting, leverage/financing modelling, widening the
basket, macross-only) were all improvements *to the §2 lead*. With the lead dead
they are **moot** — there is no longer an edge for them to refine. Do not pick
them up. Widening the basket in particular would only add instruments to a
strategy whose gross PF out of regime is 1.006.

---

## 6. THE OUT-OF-REGIME TEST — the lead was a favourable-regime artifact

Run 2026-08-11. The macross basket was re-run **completely unchanged** — same
code, families, variants, cost model, engine, and parameters (`run_basket_trend.py`
logic imported wholesale by `run_basket_pre2018.py`). **Nothing was re-tuned.**
Only the data window changed. Both windows use the **same 5 indices**, so the
comparison isolates regime rather than basket membership.

### Headline — H4 macross v2 basket

| Metric | 2018-25 (6 idx, published) | 2018-25 (5 idx, matched) | **2013-17 (out of regime)** |
|---|---|---|---|
| Net Sharpe | +0.799 | +1.042 | **−0.283** |
| Net PF | 1.196 | 1.292 | **0.935** |
| **Gross PF** | 1.261 | 1.363 | **1.006** |
| Max drawdown | 7.8% | 5.7% | **10.8%** |
| CAGR | 3.97% | 5.66% | **−1.32%** |
| IS → OOS Sharpe | +0.70 → +0.95 | +0.66 → +1.38 | **−0.22 → −0.37** |
| OOS holds | YES | YES | **NO** |
| DSR (structural pool) | 0.446 | 0.690 | **0.143** |
| Trades | 1,440 | 1,166 | 557 |

Across all 18 baskets: positive Sharpe **12/18 → 2/18**; netPF>1 **12/18 → 2/18**;
OOS-holds **7/18 → 1/18**; DSR>0.95 **0/18 → 0/18**. The best pre-2018 basket is
D1 macross v0 at Sharpe **+0.097** — indistinguishable from zero.

**DSR pools (stated, per `research/dsr.py`):** single-name structural pool N=90
(H4/H8/D1 × trend+macross, this run's own a priori cells), E[maxSR] +1.104
(pre-2018) / +1.376 (in-regime); basket pool N=18, E[maxSR] +0.228 / +0.896. Note
the pre-2018 bar is *low* (+0.228, because every basket is bad) and the lead still
scores only 0.143.

### Why it failed — the edge is gone BEFORE costs

`cost_R` rose from 3.56% to 5.05% of 1R on wider pre-2018 spreads, but ~1.5% of R
cannot explain a 1.33-Sharpe swing. **Gross PF 1.006 is the real finding: the raw
signal edge is nil.** This is not a cost story and not an execution story.

The mechanism is regime shape, not regime direction. 2013-2017 was a *smooth
grinding* bull; 2018-2025 was a violent one:

| | 2013-17 | 2018-25 |
|---|---|---|
| EW B&H basket Sharpe | **+0.96** | +0.66 |
| EW B&H basket maxDD | **17.1%** | 30.7% |
| EW B&H basket CAGR | 11.8% | 11.2% |

Near-identical CAGR, wildly different path. A moving-average crossover monetises
**large persistent directional moves**. 2018-2025 supplied three (the 2020 crash
and recovery, the 2022 bear, the 2023-25 rally); 2013-2017 supplied none, so the
crossover simply whipsawed. The basket **beat** B&H by +0.39 Sharpe in regime and
**lost** to it by −1.25 out of regime.

### What could NOT be tested — stated plainly

**2008 is unreachable.** Dukascopy index CFDs do not go back that far, and the
ask side (needed for a real spread) starts later than the bid. Probed empirically
with retries off (`scripts/probe_earliest.mjs`, `probe_h1_sides.mjs`,
`probe_refine.mjs`); `instrumentMetaData` H1 starts are optimistic and were not
taken on trust.

| Index | Metadata H1 start | **Verified bid+ask (spread-usable) start** |
|---|---|---|
| SPX500 | 2011-09-18 | 2012-02 |
| NAS100 | 2011-09-18 | 2012-04 |
| JP225 | 2011-09-18 | patchy through 2012 (bid w/o ask 2012-02; ask w/o bid 2012-04) |
| UK100 | 2011-09-18 | **2013-09** |
| US30 | 2013-09-30 | 2013-09-30 |
| GER40 | 2013-09-30 | **2015** — ask absent 2013-14 (re-probed fresh: NO DATA, not a cached fault) |

So **2013-09-30 is the true floor** for a 5-index spread-costed basket, and
**GER40 cannot be included at all** pre-2018. This test therefore covers the 2014
oil crash, 2015 China Black Monday and 2016 Brexit — a real stress sample — but
**not** 2008 or 2011. The window was not silently shortened to flatter the result;
it is the deepest one the data supports.

**Data-quality caveat, reported not hidden:** pre-2018 H1 coverage is ~30% sparser
(3,566–4,286 bars/yr vs 5,739–5,822 for SPX500/UK100/JP225 in 2018-25), with
154–319 lost days per member and gaps up to 93 days; JP225's archive stops
2017-11-30. Per-year *trade* rates are nonetheless comparable (133/yr vs 146/yr),
so sparsity thinned the sample without gutting it. It makes the pre-2018 Sharpe
noisier — but it cannot manufacture a sign flip *plus* a gross-PF collapse to
1.006.

**Cumulative trials: N=435** (345 prior + 90 pre-2018). The 90 matched-window
configs are a re-scoring of the already-counted 2018-25 grid and are not
double-counted.

---

## 7. WHERE THIS LEAVES THE PROJECT

**There is no live lead.** Every surface opened in this project is now closed:

| Surface | Trials | Verdict |
|---|---|---|
| Crypto free price/derivatives factors | 6 studies | 5 kills + 1 overfit |
| Gold FTMO (intraday + swing) + SMA-200 baselines | 8 | all kill |
| Gold/index systematic sweeps + HTF breakout | 237 | 0 survive |
| Index trend basket, 2018-25 | 108 | 0 clear DSR; best was the §2 lead |
| **Index trend basket, out of regime** | **90** | **lead's Sharpe flips negative** |

The honest summary is that **price-only technical strategies on gold and equity
indices have been searched thoroughly and nothing survived.** The one candidate
that looked real was measuring a 2018-2025 regime, and the test designed to catch
exactly that caught it.

If this project continues, it should continue on a **different information set**,
not another price-pattern variant:

1. **Accept the null and stop.** A defensible outcome. 435 trials with a corrected
   DSR gate and no survivor is evidence, not failure — and it was reached without
   deploying capital into a regime artifact.
2. **On-chain crypto data (Glassnode Essentials).** Already identified as the
   justified next spend: a genuinely different information set, not a resolution
   change on the same free price data.
3. **If indices are revisited at all**, the bar is now explicit: any candidate
   must clear the out-of-regime test in §6 *before* anything else is measured.
   Test 2013-2017 first, not last.

**Do NOT** re-run FTMO price-pattern variants, timeframe sweeps, single-instrument
gold work, or basket-widening. All are closed; §1 and §6 explain why.

---

## 8. DATA + CODE INVENTORY

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

| `{NAS100,US30,SPX500,UK100,JP225}_H1_2013_2017_cfd_dukascopy.csv` | ~2 MB ea | **Pre-2018 out-of-regime window**, H1 bid/ask CFD. GER40 impossible (no ask before 2015) | `scripts/download_pre2018.mjs` (resumable per instrument/side/year) |

All 2018-2025 files: UTC, real bid+ask OHLC plus a real `spread` column,
2018-01 → 2025-12. The `2013_2017` files are the same schema, spanning
2013-09-30 → 2017-12-29 (JP225 to 2017-11-30) — see §6 for why that is the
deepest window the archive actually supports.

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
| `run_basket_trend.py` | The former lead (§2, now killed). 6 indices × H4/H8/D1 × trend+macross = 108 configs + 18 equal-risk baskets + benchmarks |
| `run_basket_pre2018.py` | **The kill shot (§6).** Same strategy code, `--suffix`/`--split`/`--tag` select the window. 5 indices × H4/H8/D1 × trend+macross = 90 configs + 18 baskets |
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
`run_all_indices.sh`/`.cmd`, `run_all_basket.sh`/`.cmd`,
`run_pre2018_compare.sh`/`.cmd` (verify → out-of-regime run → matched in-regime
run; ~35 s total).

`verify_indices.py` / `verify_basket.py` / `verify_pre2018.py` are **hard gates**:
they check first *and* last bar, per-year bar floors, that the spread column is
real and positive, and that prices are in band; `verify_pre2018.py` also reports
coverage gaps > 10 days. They exit 1 and block the sweep on failure. These exist
because a partial merge once produced a file *named* `2018_2025` that actually
held only 386k rows ending 2019-12-31 — a backtest would have silently run on two
years instead of eight.

**Archive-availability probes** (`probe_earliest.mjs`, `probe_h1_sides.mjs`,
`probe_refine.mjs`): narrow windows, **retries off** so a missing archive returns
fast and empty instead of being retried, and caching per probe so re-runs are
free. They distinguish NO-DATA from a network FAULT — the distinction that proved
GER40's missing ask is real. Two lessons worth keeping: `instrumentMetaData`'s
claimed H1 start is **optimistic**, and the **ask archive can start years after
the bid**, so availability must be probed per side, never assumed from one.

`compare_pre2018.py` prints the three-window side-by-side in §6.

### Results (`results/`) — tracked in git as of 2026-07-22

`sweep_progress.csv`, `htf_breakout*.csv`, `sweep_indices*.csv`,
`leaderboard_indices.csv`, `basket_configs_scored.csv`, `basket_results.csv`,
`dsr_recomputed.csv`, plus `pipeline_*.log`. Added 2026-08-11:
`basket_results_pre2018.csv`, `basket_configs_scored_pre2018.csv`,
`basket_results_new5.csv`, `basket_configs_scored_new5.csv`,
`pipeline_pre2018.log` — the numeric evidence behind §6.

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
