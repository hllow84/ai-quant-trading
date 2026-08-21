# STATE OF PLAY — AI Quant Trading Lab

**Last updated: 2026-08-21 (out-of-regime re-run complete).** Read this file first in any new session. It is the
standalone briefing: where the research stands, what was settled, what is still
open, and which files matter. `research_log.md` holds the per-test detail;
`CLAUDE.md` holds the standing working rules.

> **2026-08-11 — THE LAST LEAD IS DEAD.** The diversified index-trend basket (§2)
> was re-run **unchanged** on 2013-2017 and its Sharpe flipped **+1.04 → −0.28**,
> with **gross PF collapsing to 1.006** — no edge even before costs. 2018-2025 was
> a favourable regime, not a discovered edge. §2 is retained below as a record of
> what was believed, with the kill stated inline. **There is now no live lead in
> this project.** See §7 for what that leaves.

> **2026-08-21 — THE SNEAKY PIVOT'S GROSS EDGE SURVIVED OUT OF REGIME (§9.4).**
> The 2013-2017 re-run is done. **gross PF > 1 held in 14 of 16 cells** (mean
> 1.321 → 1.155, best 1.536 → 1.363, one cell improved). That is the first time
> anything in this project has survived the test that killed everything else —
> compare the index basket, whose gross PF collapsed 1.363 → **1.006**.
> **It is still not a lead**, and the reasons are now different and sharper: net
> PF > 1 fell 16/16 → 3/16 at 15-17% cost_R, DSR 0/16, OOS holds 0/16, it loses to
> buy-and-hold in BOTH regimes (+0.26 vs +1.21 out of regime), and **its P&L is
> concentrated in a single year in each window** — +27.2R of ~+42R from 2025 in
> regime, +29.2R of +14.8R from 2017 out of it, negative in most other years.
> The setup finds a real repeatable inefficiency that is too small to pay for
> itself. Read §9.4 before acting on any of it.

---

## 1. BOTTOM LINE — the FTMO hunt is concluded, and the answer is no

**Across 475 systematic backtest configurations, no FTMO-viable edge was found —
and no own-capital edge either (§6).** The closest thing to a positive result in
the whole project is §9.4: a setup whose GROSS edge survives out of regime but
cannot pay its own transaction costs.

Trial composition (this is the cumulative DSR trial count, N=435):

| Batch | Instrument(s) | Configs | Outcome |
|---|---|---|---|
| Family sweep (5 fam × 5 TF) | XAUUSD | 75 | 0 survive |
| HTF-trend-gated breakout | XAUUSD | 12 | 0 survive |
| US index sweep (5 fam × 5 TF × 2) | NAS100, US30 | 150 | 0 survive |
| Index trend basket (2 fam × 3 TF × 6) | 6 indices | 108 | 0 survive |
| Pre-2018 out-of-regime (2 fam × 3 TF × 5) | 5 indices | 90 | 0 survive (§6) |
| Sneaky Pivot 2018-25 (3 inst x 2 x 2 x 2) | NAS100, US30, XAUUSD | 24 | 0 survive (§9.2) |
| Sneaky Pivot 2013-17 out-of-regime | NAS100, US30 | 16 | 0 survive (§9.4) |
| **Total** | | **475** | **0 survive** |

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

---

## 9. THE FOUR-STRATEGY BRIEF (opened 2026-08-19)

Four externally-sourced discretionary strategies were handed in for testing:

1. **5-Step Option Trading Framework** — day/swing options on NVDA, MU, SPY, QQQ.
2. **15-Minute "Sneaky Pivot"** — rules-based 3-candle reversal at prior-day levels.
3. **S&P 500 Futures Reversal** — 1-minute trend-break + engulfing reversal into
   pre-marked 15-minute zones.
4. **Thematic Catalyst Trend Following** — multi-week holds in leading growth stocks.

### 9.1 Feasibility triage — what this repo can and cannot honestly test

| # | Testable here? | Binding constraint |
|---|---|---|
| 2 | **YES, fully** | Entirely mechanical. Done — §9.2. |
| 3 | **Mostly** | SPX500 has no M1 in the repo (H1 only); NAS100/US30 M1 stand in for ES. "Draw a trendline and wait for the break" and "a powerful engulfing candle" need mechanising, and each mechanisation is a fork to state. |
| 1 | **Underlying only** | The option layer is **not testable at any price we have**. Delta 0.30-0.35 selection, a 25% contract-drawdown stop and "sell half at +100%" are all functions of the option's own path — implied vol, theta, the surface. There is no free historical intraday option chain. The entry logic (15-min ORB break, 30-minute pivot off the 21 EMA) IS testable on the underlying, but **a positive result there would not validate the options version**: theta and the option spread can convert a small positive underlying edge into a loser, and the asymmetric exits change the payoff shape entirely. Also NVDA/MU are single stocks — no data in the repo. |
| 4 | **NO, not honestly** | Two blockers, neither fixable with data on hand. (a) **Hindsight themes.** Choosing "AI, memory, optics, space" in 2026 and backtesting from 2018 is look-ahead of the purest kind; a legitimate test needs a point-in-time rule that would have *selected* those themes contemporaneously. (b) **Survivorship.** It needs a point-in-time US equity universe including delisted names. Strip both away and what remains — RS-line highs, 21/50/200 MA regime, base breakouts — is the macross/trend family that §2 and §6 already killed. **Do not run a hindsight-theme backtest and report a number from it.** |

### 9.2 Strategy 2 — the 15-minute Sneaky Pivot (2018-2025 run complete)

24 configs: 3 instruments (NAS100, US30, XAUUSD) x 2 targets x 2 stops x 2 trigger
windows. Every axis is a fork the brief leaves open; **no numeric parameter is
fitted**. Session RTH 09:30-16:00 ET, real per-bar spread + commission + slippage,
1% risk/trade, M1 resolution. Full detail in `research_log.md` (2026-08-19).

| | Result |
|---|---|
| gross PF > 1 | **24 / 24** (1.170 - 1.548) |
| net PF > 1 | 20 / 24 |
| positive net Sharpe | 20 / 24 |
| OOS holds (2023 split) | 15 / 24 |
| DSR > 0.95 | **0 / 24** |
| look-ahead guard | 24 / 24 PASS |

**Best config — NAS100, swing target, sneaky-candle stop, session trigger:**
gross PF 1.536, net PF 1.384, net Sharpe **+0.53**, maxDD 14.7%, 189 trades,
win rate 40.7%, IS PF 1.26 / OOS PF 1.60, cost_R 6.6% of 1R.

**What is genuinely new here.** No other family in this project has been positive
gross in *every* cell. 435 prior trials produced gross PF clustered at 1.00-1.05;
this one runs 1.17-1.55 across three different instruments and eight structural
variants. Sign-consistency across independent instruments is not a best-of-N
artefact — DSR tests the maximum, and says nothing about it.

**Why it is still NOT a lead — four independent reservations:**

1. **DSR 0.42 against a 0.95 bar.** Structural pool = this batch's own 24 a priori
   cells, E[max SR] +0.590. The best config scores +0.53 — *below* the best-of-24
   you would expect from noise. (The project-cumulative 459-trial pool gives
   E[max SR] +7.08 and is meaningless: it is exactly the sigma-contamination
   `research/dsr.py` BUG 2 documents. Earlier runners used it as their gate,
   which is why every one of them reported DSR 0.000.)
2. **Loses to buy-and-hold on all three instruments** — NAS100 +0.53 vs +0.84,
   US30 +0.32 vs +0.55, XAUUSD +0.21 vs +1.19 — though at 2-3x lower drawdown.
3. **Regime concentration, the exact signature that killed §2.** The NAS100 best
   config earns **+27.2R in 2025 alone** out of ~+42R total, and is negative in
   2020 (-5.9R) and 2024 (-7.1R). US30's best is -14.8R in 2023.
4. **The best cells are not quite the strategy as written.** "Swing target" configs
   post the highest gross R but hit that target **3 times in 189 trades**. In
   practice they are "hold to the cash close with a stop". The extra R comes from
   letting winners run to the bell, not from the swing line.

Costs behave exactly as §1 predicts: 5.7-8.2% of 1R on the indices (a non-issue),
14.4-17.3% on gold — and all four net-negative configs are XAUUSD.

**Two forks in the brief were NOT crossed (identified 2026-08-21 by diffing the
code against the source text, now stored verbatim at `notes/four_strategy_brief.md`
with a full delta table):**

1. **Range High/Low is RTH, the brief says *absolute*.** The text reads "the
   previous day's absolute highest and lowest printed price points";
   `strategies/sneaky_pivot.py` uses the prior 09:30-16:00 ET session extremes.
   On a 23-hour index CFD the overnight extreme frequently exceeds the cash one,
   so these are genuinely different lines and "a flush into the Range Low" is a
   different event. The RTH choice is defensible and deliberate — the pre-2018
   archive is cash-session only, so an absolute-range variant can never be
   regime-tested, and "the opening candle of the day" is meaningless against a
   23-hour session — but **the absolute-range variant IS testable on 2018-2025
   and has never been run.**
2. **"Aggressively" is unquantified.** The brief wants C1 to "plow aggressively"
   into the zone; the code requires only that C1 trades at/through the line and is
   directional into it, with no magnitude threshold. That is the right
   conservative call (any threshold is a fitted number) but it means the tested
   setup fires on gentle drifts as well as real flushes.

Neither fork is a defect in the 24-config run — both are honest readings, and
crossing them adds trials to the DSR pool. They are recorded so that no future
session mistakes the tested strategy for the strategy as written.

### 9.3 The out-of-regime test (DONE 2026-08-21) — how it was run

**§7 rule 3 applied: 2013-2017 first, not last.** The repo's M1 archive started
2018-01, so `scripts/download_pre2018_m1.mjs` pulled 2013-09-30 → 2018 M1 bid+ask
for NAS100 and US30, RTH-only (13:00-21:00 UTC). Both files passed the sanity gate
and were promoted:

| | NAS100 | US30 |
|---|---|---|
| M1 bars | 443,449 | 467,543 |
| sessions | 1,030 | 1,082 |
| span | 2013-09-30 → 2017-12-29 | 2013-09-30 → 2017-12-29 |
| per-year bars (2014-17) | 102k-110k | 109k-112k |
| negative spreads | 0 | 0 |

The gate floor is 55,000 bars/year, so both clear by roughly 2x even after the 71
confirmed single-side archive holes (~50 lost NAS100 sessions).

`run_sneaky_pivot_pre2018.py` contains **no strategy, cost or scoring code**. It
imports `run_sneaky_pivot` as a module, rebinds four names — data files, OOS split
(2016-01-01), output paths, banner label — and calls its `main()`. Every object
that decides a number is the one the 2018-2025 run used, so the two windows cannot
drift. XAUUSD has no pre-2018 M1, so the grid is 16 cells rather than 24 and the
comparison is restricted to the 16 index cells on both sides.

**RTH coverage was verified, not assumed.** The 08-19 probe note recorded pre-2018
coverage as 13:30-20:00 UTC, which in EST months would have truncated every session
at 15:00 ET and silently moved the force-flat exit. Measured: EST days reach 20:59
UTC (15:59 ET), EDT days reach 20:00 UTC (16:00 ET). Full sessions in both halves,
median 370/390 bars. `MIN_RTH_BARS=300` would NOT have caught the truncation.

### 9.4 The result — the gross edge survived, and it still is not a lead

**gross PF > 1: 16/16 in regime → 14/16 out of regime.** Mean 1.321 → 1.155. The
best in-regime cell went 1.536 → 1.363, and NAS100 swing/sneaky/c3 *improved*,
1.529 → 1.547. **No other family in this project has ever survived this test.** The
index basket, by contrast, went 1.363 → 1.006 — its edge was gone before costs.

| gate | in regime | out of regime |
|---|---|---|
| gross PF > 1 | 16/16 | **14/16** |
| net PF > 1 | 16/16 | 3/16 |
| positive net Sharpe | 16/16 | 3/16 |
| OOS holds | 15/24 (all cells) | **0/16** |
| DSR > 0.95 | 0/24 | **0/16** (best 0.53) |
| look-ahead guard | PASS | 16/16 PASS |

**Why it is still not a lead — three reasons, and they are not the old ones:**

1. **The edge cannot pay for itself.** cost_R is 15-17% of 1R out of regime vs
   5.8-6.8% in it, and net PF > 1 survives in only 3 of 16 cells. Note the
   mechanism, because the earlier note in this file was wrong about it: full-window
   spreads are **2.39 bps vs 2.31 in regime — essentially equal**. The gap is
   stop distance. 1R is the sneaky candle's own range, 2013-2017 was a low-vol
   grind, so stops are ~2.5x tighter and an unchanged spread eats 2.5x more of
   them. §1's vice, reached from the other side.
2. **One year carries each window.** In regime the NAS100 best cell earned +27.2R
   in 2025 out of ~+42R. Out of regime the best cell earns **+29.2R in 2017 out of
   +14.8R net total**, and is negative in 2014, 2015 and 2016. US30's best manages
   +10.1R in 2016 against -9.1 in 2015 and -7.0 in 2017, summing **negative**.
   This is the signature that killed §2, and it now appears in both windows.
3. **It loses to buy-and-hold in both regimes, and by more out of regime** —
   +0.26 vs NAS100 B&H **+1.21** and US30 **+1.05**, against +0.53 vs +0.84 in
   regime. Two indices, two windows, four comparisons, four losses.

**The honest summary: the setup finds a real, repeatable gross inefficiency — 14/16
positive-gross cells across two instruments and two disjoint windows is not a
best-of-N artefact — that is too small to clear its own transaction costs, too
concentrated to trust, and beaten by holding the index.** That is a more
interesting result than a kill, and it is still not something to trade.

### 9.5 Data facts from the pre-2018 pull

**Measured, not assumed:**

- Pre-2018 index M1 quotes cover the US cash session only. The 08-19 probe recorded
  this as "13:30-20:00 UTC", which is the **EDT** picture; re-measured 2026-08-21
  across the finished pull, **EST days run to 20:59 UTC (15:59 ET)** and EDT days to
  20:00 UTC (16:00 ET). The full 09:30-16:00 ET session is present in both halves of
  the year — median 370 (EST) / 390 (EDT) bars. Taking the original note literally
  would have truncated every winter session an hour early, and `MIN_RTH_BARS=300`
  would not have caught it. Bid and ask merge **100%** on timestamp.
- That is sufficient for an RTH-anchored strategy, and it retroactively justifies
  the RTH session choice: the same definition is testable in both regimes. A
  23-hour "absolute range" variant is a *different* strategy, not a parameter, and
  cannot be tested pre-2018 at all.
- **The M1 "rate limit" was mostly self-inflicted, and this is worth carrying
  forward.** Batch 40 / 300 ms does draw a real HTTP 429. But the 70-minute stall
  on 2026-08-21 was not a ban: `retryCount: 4` makes dukascopy-node fire four
  internal retries back-to-back, with NO pause, for every hourly file — and on a
  day the archive has no data for, every file fails, so ~32 requests go out in ~3
  seconds and trip the burst limiter. **The library manufactures a rate-limit
  error out of a no-data day.** Isolated by varying one flag: retry 0 → 0 bars in
  278 ms; retry 4 → 429 in 3,270 ms, cache irrelevant. A single probe returned 60
  bars in 128 ms from the same IP while the run sat wedged. Fix: `retryCount: 0`,
  and let the outer loop retry, which paces itself. After it, batch 4 / 2000 ms
  ran ~60 days/min to completion. **Rule: before believing a 429, probe once from
  a fresh process.**
- Pre-2018 index M1 has **genuine single-side holes** — one side present, the
  other absent for a whole day, scattered through 2015-2017. 71 confirmed; three
  paced re-fetches recovered **0 of them**, so they are archive facts, not
  transient failures. Cost NAS100 ~50 sessions out of 1,080. Per-year bar counts
  still clear the gate by ~2x.
