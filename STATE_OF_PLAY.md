# STATE OF PLAY — AI Quant Trading Lab

**Last updated: 2026-08-30 (cross-sectional momentum rotation tested and killed, §12).** Read this file first in any new session. It is the
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

> **2026-08-26 — THE OPENING RANGE BREAKOUT IS DEAD, AND IT DIED HARDER THAN
> ANYTHING BEFORE IT (§10).** ORB was tested in its real, evidence-backed form —
> anchored to the **US cash open, 09:30 ET**, which no prior sweep in this project
> had isolated. In regime it looks like a find: **gross PF > 1 in 12 of 12 cells**
> (1.100–1.174). Out of regime it does not shrink, it **inverts**: **12/12 → 2/12**,
> mean gross PF **1.141 → 0.960** — the average cell now loses money *before costs*.
> Put the three out-of-regime tests side by side and ORB is the worst of them:
> index basket 1.363 → 1.006, Sneaky Pivot 1.321 → 1.155 (14/16 held), **ORB
> 1.141 → 0.960 (2/12 held)**. It also fails every other gate in regime — net PF
> 5/12, DSR 0/12, OOS holds 1/12, single-year concentration 0/12, and it loses to
> buy-and-hold in all four instrument×window comparisons. **This is a clean kill.**

> **2026-08-27 — THE M1 ROW IS RUN, AND IT IS THE FIRST CANDIDATE TO FAIL THE
> GROSS TEST *IN* REGIME (§11).** Every timeframe sweep in this project started at
> M5; the 1-minute bar was never tested. It has been now — same 5 families, same
> stated variants, same engine, 45 cells in regime and 30 out of it. **Mean gross
> PF is 0.996 in regime and 0.988 out of it: below 1.00 in BOTH windows.** The
> three previous candidates each had a real in-regime gross edge that later shrank
> (Sneaky Pivot), collapsed (index basket) or inverted (ORB). M1 never had one to
> lose, so the out-of-regime run *confirms* rather than *reveals*. Two findings
> worth carrying, and they are separate:
> **(1)** a gross edge at M1 does exist and is statistically real — XAUUSD
> mean-reversion earns **+0.0398 R/trade at t = +9.6 (daily-block), p = 5.5e-12** —
> but it is **~3% of the cost it must pay**. The family ordering is systematic:
> **mean-reversion 8/9 cells gross-positive, breakout 0/9**. The M1 tape reverts;
> breakouts fail.
> **(2)** the cost gradient is confirmed on like-for-like data (M1 cost_R
> **2.6-2.7x** M5, steeper than the sqrt-5 prediction) **and then flattens
> completely once the overnight tape is removed** — restricted to the US cash
> session, M1 cost_R is **26.4%** against M5's 27.8%, a ratio of **0.95x**. M1 is
> not intrinsically more cost-punished than M5; trading M1 across the 23-hour tape
> is. Neither finding rescues anything, and **0/45 configs survive.**

> **2026-08-29/30 — ORB'S KILL SURVIVES AN IMPLEMENTATION AUDIT AND A
> TREND-FILTERED VARIANT (§10.1-10.4).** Two follow-on tests, neither changes
> the §10 verdict. **(1) Implementation audit:** checked whether the kill
> reflected a real absence of edge or a conservative bug — entry timing was
> already intrabar (not close-confirmed), the fire rate was 93.9-100% (no
> hidden filter), the stop-first tie rule affected **zero** of 30,840 trades,
> and a deliberately-designed cost-sane MODERATE stop (25 bps fixed, replacing
> the OR-width geometry) made the in-regime numbers **worse**, not better
> (net PF>1 5/12→2/12). **(2) Trend filter:** gating breaks to only trade with
> a causal 50-session daily trend fixed **neither** failure mode that killed
> the plain version — out-of-regime gross PF stays under 1.00 on average
> (0.960→0.979), and single-year concentration gets two cells **worse** (top
> year ≥100% of net R, up from none) because a direction filter concentrates
> INTO trending years rather than spreading P&L. **0/48 cells survive across
> both follow-on batches.** No code-level or filter-based reason remains to
> doubt the §10 kill.

> **2026-08-30 — CROSS-SECTIONAL MOMENTUM ROTATION TESTED, KILLED, BUT
> STRUCTURALLY DIFFERENT FROM EVERYTHING ABOVE (§12).** A portfolio-level,
> monthly-rebalance sector/asset-class rotation (rank 17 ETFs by trailing
> 6/12-month return, hold top 3/5, market-timed to cash via SPY's 200-day
> SMA) was tested on fresh yfinance daily data — the first non-price-pattern
> structure and the first new data source in this project since the crypto
> factor studies. **Two gates PASS for the first time ever:** cost is a
> genuine non-issue (5-7% of gross return, confirming the a priori hypothesis
> that monthly turnover is a different cost regime from every intraday
> family), and single-year P&L concentration is **0/4 triggered** — the
> first candidate in this project whose profit is not carried by one year.
> It also **beats SPY buy-and-hold 4/4 in the 2000-2009 stress window**
> (Sharpe 0.56-0.70 vs SPY's 0.071) while every prior candidate lost to
> buy-and-hold in its stress window. **Still killed:** it loses to SPY
> buy-and-hold in the full 1998-2026 period (0/4), and DSR cannot clear 0.95
> even against its own 4-cell pool because the N/K grid is nearly flat
> (Sharpe 0.51-0.54 across all four cells) — a real, robust finding with no
> single config extreme enough to be statistically distinguishable from a
> 4-trial null.

---

## 1. BOTTOM LINE — the FTMO hunt is concluded, and the answer is no

**Across 630 systematic backtest configurations, no FTMO-viable edge was found —
and no own-capital edge either (§6).** The closest thing to a positive result in
the whole project is §12: a portfolio-level cross-sectional momentum rotation
whose cost and concentration profile is clean for the first time, and which
beats buy-and-hold in the stress window, but still loses to buy-and-hold in
the full-period benchmark and cannot clear DSR against even its own 4-cell
pool. §9.4 (a setup whose GROSS edge survives out of regime but cannot pay
its own transaction costs) is the closest positive result among the
price-pattern candidates specifically.

Trial composition (this is the cumulative DSR trial count, N=622):

| Batch | Instrument(s) | Configs | Outcome |
|---|---|---|---|
| Family sweep (5 fam × 5 TF) | XAUUSD | 75 | 0 survive |
| HTF-trend-gated breakout | XAUUSD | 12 | 0 survive |
| US index sweep (5 fam × 5 TF × 2) | NAS100, US30 | 150 | 0 survive |
| Index trend basket (2 fam × 3 TF × 6) | 6 indices | 108 | 0 survive |
| Pre-2018 out-of-regime (2 fam × 3 TF × 5) | 5 indices | 90 | 0 survive (§6) |
| Sneaky Pivot 2018-25 (3 inst x 2 x 2 x 2) | NAS100, US30, XAUUSD | 24 | 0 survive (§9.2) |
| Sneaky Pivot 2013-17 out-of-regime | NAS100, US30 | 16 | 0 survive (§9.4) |
| ORB @ US cash open 2018-25 (2 inst x 2 OR x 3 tgt) | NAS100, US30 | 12 | 0 survive (§10) |
| ORB @ US cash open 2013-17 out-of-regime | NAS100, US30 | 12 | 0 survive (§10) |
| M1 row, in regime (5 fam × 3 var × 3) | XAUUSD, NAS100, US30 | 45 | 0 survive (§11) |
| M1 row, 2013-17 out-of-regime | NAS100, US30 | 30 | 0 survive (§11) |
| ORB moderate-stop variant, both windows (§10.1-10.3) | NAS100, US30 | 24 | 0 survive (§10.2) |
| ORB trend-filtered variant, both windows (§10.4) | NAS100, US30 | 24 | 0 survive (§10.4) |
| Cross-sectional momentum rotation, full period + 2000-09 stress (§12) | 17-ETF universe, SPY benchmark | 8 | 0 survive (§12) |
| **Total** | | **630** | **0 survive** |

**Correction, 2026-08-30:** the ORB moderate-stop variant (§10.1-10.3, run
2026-08-29/30) was a genuinely new a priori design choice — 12 cells x 2 windows
— and should have been added to this table and to `run_orb.py`'s `PRIOR_TRIALS`
at the time. It was not; this table now includes it retroactively (574 → 598 →
622 with the trend-filter batch below). No verdict changes: both added batches
scored 0/24 and 0/24 survivors.

The 30 RTH-matched control cells in §11 are a **re-scoring** of the already-counted
2018-2025 M1 grid on a data subset, not new trials, and are excluded from the total
— the same treatment §6 gave its matched 5-index window.

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
| 15-min Sneaky Pivot, both windows | 40 | gross edge survives, cannot pay its costs (§9.4) |
| **ORB @ the US cash open, both windows** | **24** | **gross edge INVERTS out of regime (§10)** |
| **The M1 row, both windows** | **75** | **gross PF < 1.00 in BOTH windows — no edge to lose (§11)** |
| ORB moderate-stop variant, both windows | 24 | implementation audit — kill confirmed, not fixed (§10.1-10.3) |
| ORB trend-filtered variant, both windows | 24 | filter fixes neither failure mode — same kill (§10.4) |
| **Cross-sectional momentum rotation, full + stress** | **8** | **cost & concentration clean, beats B&H in stress, still loses to B&H full-period + fails DSR (§12)** |

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
gold work, or basket-widening. As of 2026-08-27 the timeframe sweep is **complete**
— M1 was the last unrun row and §11 closes it, so "try a faster timeframe" is now
an answered question, not an open one. All are closed; §1 and §6 explain why. As of
2026-08-26 add **opening-range breakouts** to that list in their plain form —
§10 tested the one version the prior sweeps had never isolated (the 09:30 ET cash
open) and it is the hardest kill in the project, going gross-NEGATIVE out of
regime. A filtered or differently-costed ORB is a different strategy with its own
trials, and rule 3 applies to it: **test 2013-2017 first.**

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
| `run_sweep_m1.py` | **The M1 row (§11).** 3 instruments x 5 families x 3 variants = 45 configs at the 1-minute bar; `--rth` runs the session-matched control |
| `run_sweep_m1_pre2018.py` | M1 out-of-regime driver — matched RTH control then 2013-2017; rebinds names only, no logic of its own |
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


---

## 10. THE OPENING RANGE BREAKOUT AT THE US CASH OPEN — tested 2026-08-26, killed

### Why it was worth one clean test

§1 killed a *generic* breakout family: an arbitrary rolling range on an arbitrary
timeframe, plus one gold "London opening range" variant anchored to 07:00–08:00
UTC. **None of those isolates the US cash open**, and the ORB claim is narrower
and specific: the 09:30 ET auction concentrates overnight information into a
short high-volume window, and the first extension beyond that window persists.
External evidence (a documented NQ ORB survivor) said this particular version
clears honest gates where the generic family did not. That is a different
proposition, so it got one clean test under §7 rule 3 — **out of regime first,
not last.**

### The strategy, every default stated, nothing tuned

| axis | setting | note |
|---|---|---|
| Opening range | first **N = 15** or **30** minutes after 09:30 ET | both canonical; neither chosen by result |
| Entry | resting **stop order at the OR extreme**, armed only from 09:30+N | first break of the day wins; opposite side cancelled |
| Stop | **the opposite side of the OR**, so **1R = the OR range** | the brief's "or a stated fraction of it" was NOT used, so no fraction is a free parameter |
| Target | **1R**, **2R**, or **hold to the cash close** with the stop live | |
| Exit | force-flat at the **16:00 ET** cash close | no overnight holds |
| Frequency | **one position per day per instrument** | no re-entry, no reversal |

**12 configs per window** (2 instruments × 2 OR × 3 targets). No numeric
optimisation anywhere. `run_orb_pre2018.py` holds **no** strategy, cost or scoring
code — it imports `run_orb` and rebinds five names, so both windows execute the
*same objects*. Both indices have M1 in both windows, so unlike the Sneaky Pivot
test (which lost gold) the grid is **identical on both sides**.

### DST — the thing that silently breaks this strategy, handled and verified

09:30 ET is **13:30 UTC under EDT** and **14:30 UTC under EST**. A fixed offset
would build the "opening range" from 08:30–08:45 ET (pre-market) all winter and
10:30–10:45 ET (an hour into the session) all summer — two different strategies,
neither of them ORB, for half the sample each.

Every bar is converted with `tz_convert("America/New_York")`, which carries the
full IANA DST history per timestamp. **`scripts/verify_orb_sessions.py` is a hard
gate that proves it from the data rather than asserting it**, and it exits 1:

| check | NAS100 18-25 | US30 18-25 | NAS100 13-17 | US30 13-17 |
|---|---|---|---|---|
| UTC clock of the 09:30 ET bar | **13:30 / 14:30 only** | same | same | same |
| EDT / EST sessions | 1,075 / 604 | 1,087 / 512 | 645 / 368 | 678 / 391 |
| opening bar present | 100.0% | 99.9% | 98.5% | 98.9% |
| OR15 has ≥13 of 15 bars | 100.0% | 99.6% | 98.1% | 98.3% |
| reaches 15:59 ET | 99.0% | 99.0% | 96.0% | 96.0% |
| median RTH bars/session | 390 | 390 | 390 | 390 |

The observed offset flips land on the first session after the **2nd Sunday in
March** and the **1st Sunday in November** in all eight years — the correct US
rule, read off the data, not assumed.

### Costs — including the one place this study departs from the repo default

Real per-bar Dukascopy spread (round-turn) + 0.35 bps commission + per-side
slippage, 1% risk/trade. **The departure is slippage, and it was necessary.** The
engine's `NEWS_HOURS_UTC` windows are fixed in UTC, so under EST they end at
*exactly* 09:30 ET — every winter ORB entry would have been charged NORMAL
slippage in the single most volatile minute of its day. So this run supplies an
**ET-anchored** slippage function: **1.00 bps per side for entries 09:30–10:30 ET**
(2× the repo's news figure, ~6.7× normal, ≈ 2 index points on NAS100 at 20,000),
0.15 bps after. `simulate_trades` gained an **optional** `slip_bps_fn`; default
`None` reproduces the old branch exactly, verified by synthetic regression
(default == explicit-None, and `cost_R` == the original formula to 1e-15).
**No prior result in this repo moves.**

| | in regime | out of regime |
|---|---|---|
| cost_R (% of 1R) | **5.7 – 9.9%** | **11.9 – 17.5%** |
| median 1R (bps of price) | 32 – 60 | 23 – 41 |

Same vice as §1, reached a third time: 1R is the OR's own range, 2013–2017 was a
low-vol grind, so stops are tighter and an unchanged spread eats more of them.
**But costs are NOT what kills this** — out of regime the *gross* number is
negative on its own.

A **0.50 bps sensitivity** (the repo's existing news figure) is reported on the
same trades — a re-scoring, not new trials, so it adds nothing to the DSR pool.
It lifts net PF by only **+0.035 to +0.066**, moves two more in-regime cells above
1.00, and **changes no verdict**.

### The result

**In regime (2018-01-03 → 2025-12-31, split 2023-01-01), 12 configs:**

| gate | result |
|---|---|
| look-ahead guard | **12/12 PASS** |
| gross PF > 1 | **12/12** (1.100–1.174, mean 1.141) |
| net PF > 1 | 5/12 |
| positive net Sharpe | 5/12 |
| OOS holds | 1/12 |
| DSR > 0.95 | **0/12** (best 0.381) |
| top year ≤ 60% of net R | **0/12** |
| beats buy-and-hold | **0/12** |
| **SURVIVORS** | **0/12** |

Best cell — **NAS100, OR30, 2R target**: gross PF 1.174, net PF 1.039, net Sharpe
**+0.23**, maxDD 33.5%, 1,609 trades, win 46.1%, cost_R 5.7%, IS PF 0.99 / OOS PF
1.11. DSR pool **stated**: structural = this batch's own 12 a priori cells,
E[max SR] **+0.341** (μ −0.153, σ 0.297). The 487-Sharpe cumulative pool
(E[max SR] +7.00) is printed for contrast only — it is `research/dsr.py` BUG 2.

**Out of regime (2013-09-30 → 2017-12-29, split 2016-01-01), the same 12 cells:**

| | in regime | out of regime |
|---|---|---|
| gross PF > 1 | 12/12 | **2/12** |
| mean gross PF | 1.141 | **0.960** |
| net PF > 1 | 5/12 | **0/12** |
| positive net Sharpe | 5/12 | **0/12** |
| mean net Sharpe | −0.153 | **−2.316** |
| best in-regime cell (NAS100 OR30 2R) | grPF 1.174 / netPF 1.039 / SR +0.23 | **grPF 0.965 / netPF 0.730 / SR −2.13** |
| cells positive-gross in BOTH windows | — | **2/12** |
| cells net-profitable in BOTH windows | — | **0/12** |

### Why this is the hardest kill in the project

Line the three out-of-regime tests up:

| candidate | gross PF, in → out | cells still gross-positive | reading |
|---|---|---|---|
| Index trend basket (§6) | 1.363 → **1.006** | 2/18 baskets +SR | edge annihilated; it was regime |
| Sneaky Pivot (§9.4) | 1.321 → **1.155** | **14/16** | edge real, too small to pay its costs |
| **ORB (this section)** | 1.141 → **0.960** | **2/12** | **edge inverts — gross-negative out of regime** |

ORB is the only one whose *mean* gross PF ends **below 1**. The basket lost its
edge; ORB acquires a negative one.

Two more independent failures, both in regime:

- **Single-year concentration, 0/12 — the third appearance of the signature that
  killed the last two candidates.** The best cell earns **+21.3R of its +28.9R
  total in 2023 alone (74%)** and is negative in 2018, 2019, 2020 and 2025. Three
  other net-positive NAS100 cells have a single year worth **154%, 180% and 193%**
  of their total — one good year larger than the entire P&L. **All six US30 cells
  sum negative** over 2018–2025.
- **Loses to buy-and-hold 4 times out of 4**, on Sharpe *and* on drawdown:
  NAS100 +0.23 vs **+0.84**, US30 −0.20 vs **+0.55** in regime; −1.37 vs **+1.21**
  and −1.70 vs **+1.05** out of regime, at 33.5–61.0% maxDD against 35.7%/37.0%.

### On the external evidence, stated fairly

The documented NQ ORB survivor is **not reproduced here**. What the data does show
is that the in-regime gross signature is exactly what such a study would report —
12/12 gross-positive cells on 2018–2025, net-positive on NAS100 — **and that it
does not exist before 2018**. That is consistent with, though not proof of, the
published result being a 2018–2025 artefact: the same failure mode as this
project's own last two candidates.

A *different* ORB remains possible — a trend or VWAP filter, volatility-scaled
sizing, a stated stop fraction, NQ futures costs rather than index-CFD costs.
Each of those is a **different strategy carrying its own trials**, and §7 rule 3
applies to each: test 2013–2017 first. The plain, evidence-backed form tested
here does not survive.

### What could not be tested, stated plainly

**SPX500 was asked for and is absent for a data reason, not a choice.** The repo
holds SPX500 at **H1 only**; a 15-minute opening range cannot be built from hourly
bars, and adding it needs a fresh multi-hundred-MB M1 pull. NAS100 and US30 are
the two indices with M1 in **both** windows — which is exactly what makes the
out-of-regime test possible at all. Pre-2009 is unreachable for the same reason
§6 gives: the Dukascopy index CFD archive does not go back that far with a real
ask side.

### Files

| file | what it is |
|---|---|
| `strategies/orb.py` | the strategy; every mechanisation fork stated in the docstring |
| `run_orb.py` | 2018-2025, 12 configs, all gates, cost sensitivity, per-year table |
| `run_orb_pre2018.py` | out-of-regime driver — rebinds 5 names, no logic of its own |
| `scripts/verify_orb_sessions.py` | **hard gate**: DST mapping + OR/close coverage |
| `scripts/run_orb.sh` / `.cmd` | detached chained runner (verify → in regime → out of regime, ~80 s) |
| `results/orb*.csv`, `results/orb_run.log` | the numeric evidence behind this section |

**Cumulative trials: N=499** (475 prior + 12 in regime + 12 out of regime).

### 10.1 IMPLEMENTATION AUDIT (2026-08-29/30) — the kill is real, not an artefact of the code

Five audits were run against the ORB implementation to check whether the kill in
§10 reflects a real absence of edge or an overly conservative translation into
code. **Verdict: the implementation is sound. The kill holds.** None of the four
things checked changed the verdict; the fifth (a deliberately re-designed stop)
made the in-regime result *worse*, not better.

1. **Entry timing — already intrabar, not close-confirmed.** `strategies/orb.py`
   fires the instant a bar's `mid_high`/`mid_low` touches the OR level (a resting
   stop order), not on bar close — exactly what a live trader watching the tape
   would get. Measured on all 4 datasets x 2 OR windows (5,933 breakout bars): if
   the code had instead required CLOSE-beyond-level confirmation, **41.6-45.9% of
   real breakout bars would have been missed or delayed** (price closes back
   inside the range in the same minute). The current code is the *less*
   conservative, more realistic choice, not the reverse — there was no slippage
   to quantify because the assumption audited for was never made.
2. **Fire rate — clean, no filtered-out-setup problem.** Per instrument/year/OR,
   fire rate against valid (complete, non-degenerate) opening ranges is
   **93.9-100%**, far above the 85-90% sanity bar, in both windows
   (`scripts/audit_orb.py`, `results/audit_orb_fire_rate.csv`). Days lost to
   filters are negligible and stated separately from "no breakout": truncated
   sessions 44-62/window (data-completeness, not a strategy filter),
   OR-incomplete 0-9, degenerate range 0, same-minute entry ties 0-13. True
   no-breakout (inside) days are 0-13 per instrument/window — ORB's core premise
   (price usually clears the OR somewhere in a 6.5-hour session) holds
   empirically; there is no hidden filter suppressing trades.
3. **Stop-first tie rule — provably inert on this data.** Re-resolving all 12
   configs x 2 windows (30,840 total trades) under the OPPOSITE convention
   (target-first) changed **zero** trades — `n_true_ties = 0` in every one of 24
   cells (`scripts/audit_orb_tiebreak.py`, `results/audit_orb_tiebreak.csv`). At
   M1 resolution the OR range (32-60 bps in regime) is always far larger than a
   single minute's high-low range, so stop and target are never hit in the same
   bar. The conservative assumption costs nothing because the situation it
   guards against never occurs.
4. **The OR-width stop was never cost-informed — confirmed, and tested against a
   deliberate alternative.** It was geometry, not design: 1R is "whatever the
   opening range happened to be," which is exactly what the code comment already
   said. A new MODERATE stop was added (`strategies/orb.py` `MODERATE_STOP_BPS =
   25`, `stop_mode='moderate'`): a FIXED 25 bps of entry price, solved from the
   batch's own measured round-turn cost (~2.9-3.6 bps) to land cost_R at the
   middle of a stated 10-15% target band (25 bps -> ~11-13% cost_R, measured
   10.9-13.4% in regime). This is the ONE new variant the audit called for,
   tested at the same 2x2x3 breadth (12 more cells, both windows) as the
   original grid, entry/breakout-detection logic unchanged.

### 10.2 RE-RUN — same 12 original cells + 12 moderate-stop cells, both windows, same gates

`scripts/run_orb_rerun.py`. Nothing about `orb()`'s DEFAULT behaviour changed
(`stop_mode` defaults to `'or_range'`), so `results/orb.csv` /
`orb_pre2018.csv` are unaffected and reproduce byte-identically.

| | IN REGIME — OLD (or_range) | IN REGIME — NEW (moderate) | OUT OF REGIME — OLD | OUT OF REGIME — NEW |
|---|---|---|---|---|
| gross PF > 1 | 12/12 | 12/12 | 2/12 | 3/12 |
| net PF > 1 | 5/12 | **2/12** | 0/12 | 0/12 |
| positive Sharpe | 5/12 | **2/12** | 0/12 | 0/12 |
| DSR > 0.95 | 0/12 | 0/12 | 0/12 | 0/12 |
| OOS holds | 1/12 | 1/12 | 0/12 | 0/12 |
| not year-concentrated | 0/12 | 0/12 | 0/12 | 0/12 |
| beats buy-and-hold | 0/12 | 0/12 | 0/12 | 0/12 |
| **SURVIVORS** | **0/12** | **0/12** | **0/12** | **0/12** |
| mean gross PF | 1.141 | 1.131 | 0.960 | 0.973 |
| mean net Sharpe | −0.153 | **−0.561** | −2.316 | −2.340 |

DSR structural pool (this run's own 24 a-priori cells): in regime E[max SR]
**+0.570**, out of regime E[max SR] **−0.872** (n=24 each).

**The corrections do not change the verdict — and the one substantive change
(the moderate stop) makes the in-regime picture WORSE, not better**: net PF>1
and positive Sharpe both fall from 5/12 to 2/12, and mean net Sharpe drops from
−0.153 to −0.561. The tighter, cost-calibrated stop trades more often into the
same fixed round-turn cost per trade at a *smaller* R, which is the vice from
§1 stated the other way round — a stop chosen to keep cost_R in a "sane" 10-15%
band is still a stop that lets a fixed cost eat a larger share of a smaller R
than the geometric OR width did (which was already cheaper, at 5.7-9.9%). Out
of regime both variants stay dead on every gate. **0/48 cells survive across
old + new, both windows.**

### 10.3 Plain verdict

**ORB's kill in §10 reflects a real absence of edge, not a flawed or overly
conservative implementation.** Every audited assumption was checked against the
data and either (a) was already the realistic, non-conservative choice (entry
timing), (b) provably never bound (the stop-first tie rule, the fire-rate
filters), or (c) was replaced with a deliberately different, cost-motivated
design and made no cell survive — indeed made the in-regime numbers worse. There
is no code-level reason left to doubt the kill.

### Files

| file | what it is |
|---|---|
| `scripts/audit_orb.py` | AUDIT 1 (intrabar vs close) + AUDIT 2 (fire-rate table), all 4 datasets |
| `scripts/audit_orb_tiebreak.py` | AUDIT 3 (stop-first vs target-first tie sensitivity) |
| `scripts/run_orb_rerun.py` | AUDIT 4 re-run — 12 original + 12 moderate-stop cells, both windows |
| `results/audit_orb_fire_rate.csv`, `audit_orb_tiebreak.csv` | AUDIT 2/3 evidence |
| `results/orb_rerun_in_scored.csv`, `orb_rerun_out_scored.csv` | AUDIT 4 re-run evidence |

### 10.4 TREND-FILTERED VARIANT (tested 2026-08-30) — killed the same way, for the same two reasons

**Question:** does gating ORB to trend-aligned breaks only (long breaks taken
only above a causal daily trend average, short only below) survive where the
plain version died? The plain kill was driven by two specific failures — (a)
out-of-regime gross PF reversal, (b) single-year P&L concentration — and a
direction-only filter has no mechanism to fix either on its own. This was
tested empirically rather than assumed.

**Filter, stated and causal.** Daily 50-session SMA (`strategies/orb.py`
`daily_trend_direction()`, `TREND_SMA_LENGTH=50`, ~10 weeks, the canonical
"intermediate trend" length — not fitted) of the **cash-session close** (not the
23-hour CFD close, so the same definition applies identically on both windows —
the pre-2018 file is RTH-only). Long breaks require the PRIOR session's close
above its own (also prior-only) SMA; short breaks require below. The value used
for session D is built with an explicit `.shift(1)`, so nothing from D itself
can leak in. Checked two ways, not just asserted: the existing statistical
look-ahead guard (run on the filtered position series, 24/24 PASS) plus a direct
`assert_causal()` re-derivation in `scripts/run_orb_trend.py` that recomputes the
UNSHIFTED sign(close−SMA) from the prior session alone for every surviving
candidate and confirms it matches. Breakout detection, entry, target, and
`stop_mode='or_range'` (the audited default, not the §10.1 moderate stop) are
byte-identical to §10 — the filter only removes candidates, it never re-prices
or re-times a surviving one.

**Grid.** Same 12 cells as §10 (2 instruments × 2 OR × 3 targets), both windows,
run alongside a same-run recompute of the 12 unfiltered cells for a clean
side-by-side (`scripts/run_orb_trend.py`; the unfiltered recompute matches
`results/orb.csv` / `orb_pre2018.csv`).

**What the filter actually did.** It is a real, substantial filter, not a
token gate: it removed roughly **half** the trades in regime (787-800 of
1,530-1,616, i.e. NAS100 OR15 1616→816, US30 OR30 1530→754) and **~49-51%**
out of regime (472-529 of 970-1,025). Removed-vs-kept win rate and mean net R
are close and sign-mixed across cells — e.g. NAS100 OR15 1R in regime: removed
win rate 52.2% vs kept 52.7%, removed mean net R −0.0257 vs kept −0.0192; US30
OR15 close in regime: removed mean net R **+0.0295** (removed trades were
better) vs kept **−0.0751**. **The filter is not disproportionately removing
losers** — full table in `results/orb_trend_run.log` and both
`orb_trend_*_scored.csv` files.

| gate | IN REGIME unfiltered | IN REGIME trend-filtered | OUT OF REGIME unfiltered | OUT OF REGIME trend-filtered |
|---|---|---|---|---|
| gross PF > 1 | 12/12 | 12/12 | 2/12 | **5/12** |
| net PF > 1 | 5/12 | 4/12 | 0/12 | 0/12 |
| positive Sharpe | 5/12 | 4/12 | 0/12 | 0/12 |
| DSR > 0.95 | 0/12 | 0/12 | 0/12 | 0/12 |
| OOS holds | 1/12 | 2/12 | 0/12 | 0/12 |
| top-year ≤ 60% | 0/12 | 1/12 | 0/12 | 0/12 |
| top-year ≥ 100% (extreme) | — | 2/12 | — | 0/12 |
| beats buy-and-hold | 0/12 | 0/12 | 0/12 | 0/12 |
| **SURVIVORS** | **0/12** | **0/12** | **0/12** | **0/12** |
| mean gross PF | 1.141 | 1.132 | 0.960 | 0.979 |
| mean net Sharpe | −0.153 | −0.149 | −2.316 | −1.614 |

DSR structural pool = this batch's own 12 a priori cells: in regime E[max SR]
**+0.314** (mu −0.149, sd 0.278); out of regime E[max SR] **−0.730** (mu −1.614,
sd 0.531).

**Verdict — plain kill, and for the predicted reasons.** The trend filter fixes
**neither** of the two failures that killed the plain version:

1. **Out-of-regime gross PF is still broken.** It nudges up (mean 0.960 → 0.979,
   gross-positive cells 2/12 → 5/12) but stays under 1.00 on average and every
   net gate stays at 0/12 — net PF, positive Sharpe, OOS holds, beats-B&H all
   0/12, identical to the unfiltered result. A direction filter cannot manufacture
   an edge in price action that was not there pre-2018, and it did not.
2. **Single-year concentration is not fixed — it gets locally better and locally
   worse.** In regime `not_concentrated` improves from 0/12 to 1/12 (still fails
   11/12), but two cells now show EXTREME concentration (top year ≥ 100% of net
   R: NAS100 OR30 1R at 256%, NAS100 OR30 2R at 103%) that were not extreme
   before — consistent with the predicted mechanism: a trend filter concentrates
   exposure INTO trending years, it does not spread P&L more evenly.

Both predicted failure modes hold exactly as stated before the test ran. **This
is a valid, clean kill** — no config was crowned for a net-PF tick when it still
failed concentration or the out-of-regime gate. **0/24 trend-filtered cells
survive across both windows.**

### Files (10.4)

| file | what it is |
|---|---|
| `strategies/orb.py` | `daily_trend_direction()` + `orb(..., trend_dir=...)` — the filter, additive, default `None` reproduces §10 byte-identically |
| `scripts/run_orb_trend.py` | the trend-filtered runner, both windows, filter-impact analysis, `assert_causal()` |
| `results/orb_trend_in_regime_scored.csv`, `orb_trend_out_regime_scored.csv` | filtered results |
| `results/orb_trend_*_unfiltered_reference.csv` | same-run unfiltered recompute, for the side-by-side |
| `results/orb_trend_run.log` | full run log incl. the removed-vs-kept trade table |

---

## 11. THE M1 ROW — the last unrun timeframe, tested 2026-08-27, killed

### Why it was worth one clean test

Every timeframe sweep in this project deliberately started at M5. The 75-config
gold sweep, the 150-config index sweep and the basket work all span M5→H4 or
H4→D1. **M1 was never run**, which left one honest gap in an otherwise complete
grid and left a prediction untested. That is a small, cheap, falsifiable question,
and unlike a new strategy family it adds no new degrees of freedom: the families,
the variants and every numeric parameter are imported unchanged.

### The grid, every default stated, nothing tuned

| axis | setting | note |
|---|---|---|
| Instruments | XAUUSD, NAS100, US30 | the three with M1 on disk |
| Timeframe | **M1**, execution and signal on the same frame | `strictly_after=True`, as M5-H4 |
| Families | trend, breakout, meanrev, momentum, macross | imported from `strategies/sweep_families.py` |
| Variants | **3 stated per family**, unchanged | no numeric parameter re-tuned for M1 |
| Risk | 1% / trade, `de_overlap` (one position at a time) | repo convention |
| Costs | XAUUSD legacy $/oz model; indices 0.35 bps commission + 0.15/0.50 bps per-side slippage | **each instrument keeps the model it already used at M5-H4** |
| Split | 2023-01-01 in regime, 2016-01-01 out of regime | fixed, no peeking |

**45 configs in regime, 30 out of regime.** `run_sweep_m1_pre2018.py` holds no
strategy, cost or scoring code — it rebinds names on `run_sweep_m1` and calls its
`main()`, so both windows execute the *same objects*.

**What "the same variants at M1" actually means, stated because it is material.**
Every parameter in the grid is expressed in BARS, so running it at M1 rescales all
of them: ATR 14 → 14 minutes, EMA 200 → 200 minutes, max hold H → **12-96
MINUTES**. That is the correct and only honest way to add a row to a timeframe
sweep — it is what each of M5 through H4 did in its turn — and it does mean the M1
row is a set of ultra-short-hold systems.

### Two things that had to be right before any number could be read

**`scripts/verify_m1.py` is a hard gate (exits 1) and proves both from the data
rather than asserting them.**

1. **The execution-frame identity.** `resample_mid(m1, "1min")` is verified to be
   *exactly* the native bar relabelled to its close time — checked on 200k-row
   slices of all five files. So M1 runs the identical convention as M5-H4 and
   leaks nothing.
2. **The annualisation factor.** This is the single easiest number at M1 to
   inflate by ~30x. Headline Sharpe uses **calendar-daily aggregated returns
   annualised at 252**, because the factor is a property of the *return series*,
   not of the signal timeframe — an M1 system and a D1 system both emit one return
   per trading day.

| | XAUUSD | NAS100 | US30 |
|---|---|---|---|
| M1 bars | 1,827,147 | 2,211,511 | 2,090,818 |
| **measured** M1 bars/year | 228,550 | 276,723 | 261,531 |
| daily observations | 1,601 | 2,018 | 1,922 |
| factor used | **252** | **252** | **252** |
| Sharpe if per-bar returns were annualised instead | −724.34 | −658.25 | −705.30 |
| **inflation avoided** | **30.1x** | **33.1x** | **32.2x** |

Note also that `metrics.py::BARS_PER_YEAR["1m"] = 525,600` assumes a 24/7 year and
**overstates the real M1 bar count by 1.9-2.3x**. It is not used anywhere in this
run, and it is the wrong number even for the wrong method.

### FINDING (1) — there IS a gross edge at M1, it is statistically real, and it is ~3% of its cost

This is the useful result, and it is *not* "no edge". `scripts/m1_gross_significance.py`
tests gross R per trade against zero on the best cell of each family, with a
daily-block t so intraday clustering cannot inflate the count:

| instrument | family | gross R / trade | t (per-trade) | t (daily-block) | p | **edge as % of its cost** |
|---|---|---|---|---|---|---|
| XAUUSD | meanrev | **+0.0398** | +6.89 | **+9.61** | 5.5e-12 | **2.96%** |
| NAS100 | macross | +0.0288 | +3.66 | +6.48 | 2.5e-04 | 3.41% |
| NAS100 | trend | +0.0178 | +3.12 | +3.78 | 1.8e-03 | 3.49% |
| NAS100 | momentum | +0.0107 | +1.65 | +2.83 | marginal | 1.68% |
| NAS100 | breakout | −0.0040 | −0.76 | −0.03 | 0.45 | −0.50% |

**And the family ordering is systematic, not a best-of-N artefact:**

| family | cells gross-positive (of 9) | mean gross R / trade | mean gross PF |
|---|---|---|---|
| meanrev | **8/9** | **+0.0169** | 1.0323 |
| macross | 6/9 | +0.0059 | 1.0087 |
| trend | 6/9 | +0.0049 | 1.0088 |
| momentum | 4/9 | +0.0004 | 1.0004 |
| breakout | **0/9** | **−0.0154** | 0.9744 |

**The M1 tape mean-reverts and breakouts fail** — negative on every one of nine
cells across three different instruments. That is a clean structural anti-finding
with no counterpart at M5-H4, and it is the opposite sign to what the ORB study
(§10) was looking for one timeframe up. It is also, in the end, worth nothing:
a 3%-of-cost edge cannot pay a cost of any size.

### FINDING (2) — the cost gradient is confirmed, then flattens completely once the overnight tape is removed

**The prediction, stated before the run.** Cost per trade is fixed while 1R is an
ATR-scaled stop, and ATR scales roughly with the square root of bar duration, so
cost_R should scale ~1/sqrt(TF) and the M5→M1 step should multiply it by
sqrt(5) = 2.24x.

**On the 23-hour session-agnostic data the M5-H4 rows used, it holds — and is
steeper than predicted:**

| instrument | H4 | H1 | M30 | M15 | M5 | **M1** | M5→M1 | predicted | error |
|---|---|---|---|---|---|---|---|---|---|
| XAUUSD | 3.7% | 7.6% | 11.4% | 17.3% | 32.7% | **88.5%** | **2.71x** | 73.2% | +20.9% |
| NAS100 | 2.7% | 5.4% | 8.9% | 14.4% | 27.8% | **71.5%** | **2.57x** | 62.2% | +15.0% |
| US30 | 2.5% | 5.1% | 8.2% | 13.4% | 26.0% | **68.6%** | **2.64x** | 58.1% | +18.0% |

**45/45 cells sit above the 20% cost_R band that killed M5.**

**But restrict M1 to the US cash session and the gradient vanishes.** The matched
control re-runs the same 2018-2025 files on [13:00, 21:00) UTC — the liquid tape a
real M1 trader would use, and the window the pre-2018 archive forces:

| | NAS100 | US30 |
|---|---|---|
| M1 cost_R, 23-hour | 71.5% | 68.6% |
| **M1 cost_R, cash session only** | **26.4%** | **26.5%** |
| M5 cost_R (23-hour, for reference) | 27.8% | 26.0% |
| **M5 → M1 ratio, like-for-like session** | **0.95x** | **1.02x** |

Two effects compound: the cash session's median spread is **2.2x tighter** (1.03
vs 2.31 bps on NAS100) *and* its 1R is **1.9x larger** (11.2 vs 6.0 bps), because
cash-session minutes are more volatile. **So the honest statement is that M1 is
not intrinsically more cost-punished than M5 — trading M1 across the 23-hour tape
is.** This qualifies, rather than overturns, the §1 vice: the cost gradient is real
down to M5, and the extra penalty at M1 is a session-liquidity effect, not a
timeframe effect.

It rescues nothing. At 26% cost_R the net PF is still **0/30**.

> **A correction worth carrying.** The gradient often quoted as "gold cost_R: M5
> 60%, M15 32%, M30 21%" comes from `htf_breakout.csv` — the HTF-gated breakout
> batch, whose stop is *the breakout bar's own range* and therefore much tighter.
> Verified: HTF breakout M5 60.3% / M15 32.5% / M30 21.9%; the **5-family sweep**
> this row extends runs M5 32.7% / M15 17.3% / M30 11.4% / H1 7.6% / H4 3.7%.
> Both are real. The family-sweep gradient is the correct baseline for §11.

### The result

**In regime (2018-01 → 2025-12, split 2023-01-01), 45 configs:**

| gate | result |
|---|---|
| look-ahead guard | **45/45 PASS** |
| gross PF > 1 | 24/45 (mean **1.0049**, median 1.0024, range 0.946-1.071) |
| net PF > 1 | **0/45** |
| positive net Sharpe | **0/45** |
| DSR > 0.95 | 0/45 |
| OOS holds | 0/45 |
| top year ≤ 60% of net R | 0/45 |
| beats buy-and-hold | **0/45** |
| **SURVIVORS** | **0/45** |

Best cell — NAS100 macross v1: gross PF 1.0278, net PF 0.4398, net Sharpe
**−13.72**, cost_R 60.5%. Buy-and-hold beats every config on every instrument:
XAUUSD +1.19, NAS100 +0.84, US30 +0.55.

**Out of regime (2013-09-30 → 2017-12-29), 30 cells against the RTH-matched control:**

| | in regime (RTH-matched) | out of regime |
|---|---|---|
| gross PF > 1 | 16/30 | 9/30 |
| **mean gross PF** | **0.9960** | **0.9879** |
| net PF > 1 | **0/30** | **0/30** |
| mean net PF | 0.647 | 0.412 |
| mean net Sharpe | −10.37 | −15.22 |
| mean cost_R | 26.5% | 57.1% |
| median 1R | 8.8 bps | 6.1 bps |
| cells positive-gross in BOTH windows | — | **3/30** (all NAS100 macross) |
| cells net-profitable in BOTH windows | — | **0/30** |

cost_R doubles out of regime on the same **stop-distance** mechanism §9.4 and §10
found from the other side: 1R falls 8.8 → 6.1 bps in the low-vol 2013-2017 grind
while the spread widens 1.03 → 2.39 bps.

### Where this sits against the project's other out-of-regime tests

| candidate | mean gross PF, in → out | cells holding | reading |
|---|---|---|---|
| Index trend basket (§6) | 1.363 → **1.006** | 2/18 | edge annihilated; it was regime |
| Sneaky Pivot (§9.4) | 1.321 → **1.155** | 14/16 | edge real, too small to pay its costs |
| ORB @ cash open (§10) | 1.141 → **0.960** | 2/12 | edge inverts — gross-negative out of regime |
| **M1 row (this section)** | **0.996 → 0.988** | **3/30** | **no in-regime edge to lose** |

M1 is the **first candidate in this project to fail the gross test *in* regime**.
The other three all looked like finds on 2018-2025 and were undone by the second
window. M1 is undone by the first, so the out-of-regime run confirms rather than
reveals — which is itself a useful data point about the value of §7 rule 3: it
catches artefacts, but a candidate this weak never needed it.

### Two things that are NOT usable numbers in this batch, stated plainly

- **maxDD and the equity curve are invalid here.** At 1% risk/trade M1 fires ~25
  trades/day, so **27/45 cells contain a day that loses ≥ 100% of equity** (which
  sends `(1+r).cumprod()` non-positive) and **45/45 end below 1% of starting
  equity**. Sharpe *is* leverage-invariant (μ/σ cancels the scale) and so are gross
  PF, net PF, cost_R and R/trade — the verdict rests on those. The mechanism is
  stark: mean net R per trade reaches **−1.076 R** on the worst cells, i.e. the
  cost alone exceeds the entire risk unit.
- **DSR is not informative here and is doing no work.** The structural pool (this
  batch's own 45 a priori cells) has mean Sharpe **−20.01**, sd 2.86, E[max SR]
  **−13.61**. When every cell is catastrophic, a merely *less* catastrophic one can
  post a high-looking DSR while losing money on every trade. SURVIVOR requires net
  PF > 1 **and** Sharpe > 0, both of which bind long before DSR does. The
  project-cumulative 544-Sharpe pool (E[max SR] +14.95) is printed for contrast
  only — the exact σ-contamination `research/dsr.py` BUG 2 documents.

### Data caveat, reported not hidden

US30 2013-2017 holds **1 bar of 467,543 (0.0002%) with a spread of exactly zero**
(bid == ask at that minute's close). There are **zero negative spreads in any
file**. A zero spread hands that one trade a free round-turn, which *flatters* the
strategy — the safe direction to be wrong for a kill — and `verify_m1.py` now caps
zero-spread bars at 0.01% of a file rather than ignoring them.

### Files

| file | what it is |
|---|---|
| `run_sweep_m1.py` | 45 in-regime configs, all gates, both findings, per-year table |
| `run_sweep_m1_pre2018.py` | matched RTH control + out-of-regime driver; **rebinds names only** |
| `scripts/verify_m1.py` | **hard gate**: data + execution-frame identity + annualisation identity |
| `scripts/m1_gross_significance.py` | is the gross edge real? t-tests, per-trade and daily-block |
| `scripts/probe_m1.py`, `scripts/smoke_test_m1.py` | pre-flight and end-to-end pipeline checks |
| `scripts/run_m1.sh` / `.cmd` | detached chained runner (gate → in regime → control + out of regime, ~13 min) |
| `results/sweep_m1*.csv`, `results/m1_gross_significance.csv`, `results/m1_run.log` | the numeric evidence behind this section |

**Cumulative trials: N=574** (499 prior + 45 in regime + 30 out of regime; the 30
RTH-matched control cells are a re-scoring, not new trials).

---

## 12. CROSS-SECTIONAL MOMENTUM ROTATION — tested 2026-08-30, killed but structurally different

### Why this got a clean test after §1-§11 killed everything else

Sections 1-11 all tested **price-pattern strategies on a single instrument at a
time**: an intraday signal (breakout, reversal, MA cross) applied to gold or one
or two equity index CFDs, at timeframes from M1 to D1. This is a different
species entirely — **portfolio-level**, **monthly rebalance** (not intraday),
and it **ranks many instruments against each other** rather than reading one
instrument's own price history. It is also the first test in this project on a
**genuinely new data source** (yfinance daily adjusted close on liquid US-listed
ETFs) rather than Dukascopy CFD spot/bid-ask. Brendan's own surviving strategy
type is this family, so it earned an independent, honest test here rather than
being assumed to work.

### The strategy, every default stated, nothing tuned beyond the grid

| axis | setting | note |
|---|---|---|
| Universe | 11 SPDR sector ETFs (XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC) + 6 asset-class ETFs (TLT GLD IEF IWM EFA EEM) | SPY is benchmark-only, never ranked or held |
| Rebalance | monthly, on the **last trading day actually present in the data** each calendar month | not a calendar-day approximation |
| Ranking signal | trailing **N-month total return**, month-end close to month-end close | **N = 6 and N = 12**, both tested |
| Holdings | top **K**, equal-weighted | **K = 3 and K = 5**, both tested |
| Market filter | **100% into IEF** (intermediate treasuries) whenever SPY's close on the signal date is below SPY's own causal 200-day SMA | SMA computed from daily closes through the signal date only |
| Grid | **N x K = 4 configs**, no other filters, no numeric optimisation | |

### Causality — the ranking date lag, stated and verified

Signal is measured at **close(t)**, where t is the last trading day of the
month. The trade is modelled as **executed at close(t+1)** — the next trading
day, never the same close used to rank it — so the **first live return earned
is close(t+2)/close(t+1) − 1**, a full extra trading day of lag beyond the
minimum. Implemented in `research/momentum_rotation.py::simulate()` as
`weights_daily.shift(1) . daily_returns`, where `weights_daily` is itself
built from weights indexed at the execution date and forward-filled — so a
rebalance's weights can never touch the daily return that produced its own
ranking. `look_ahead_guard()` asserts every execution date's *own preceding
trading day* (its signal date, by construction) is strictly before it, for
every one of the 4 configs. **PASS 4/4.**

### Data — pulled fresh, no gaps, no backfilling

`scripts/download_momentum_universe.py` pulled `period="max"` daily OHLCV via
yfinance, `auto_adjust=True` (dividend/split-adjusted close), with retry on
failure. Actual verified start dates (not assumed):

| ticker | data from | ticker | data from |
|---|---|---|---|
| SPY | 1993-01-29 | XLRE | 2015-10-08 |
| XLK/XLF/XLE/XLV/XLI/XLY/XLP/XLU/XLB | 1998-12-22 (all 9) | XLC | 2018-06-19 |
| IWM | 2000-05-26 | TLT / IEF | 2002-07-30 |
| EFA | 2001-08-27 | GLD | 2004-11-18 |
| EEM | 2003-04-14 | | |

No gaps beyond weekends/holidays in any file (verified programmatically, flagged
threshold >3 calendar days). XLRE and XLC are genuinely newer instruments, as
their inception dates show — not backfilled or estimated. A ticker without data
at a given signal date is simply absent from that date's ranking pool, exactly
as it would have been unavailable to a real portfolio manager at the time.

### Costs — confirmed structurally different, as predicted

Real per-bar bid-ask spreads are not available from yfinance (it reports
close, not bid/ask), so a **stated conservative assumption** stands in: 2 bps
per side spread (typical of these highly liquid SPDR/major ETFs) + 1 bp per
side commission-equivalent = **3 bps per side, 6 bps round-turn**, applied to
turnover at every rebalance even though monthly rebalancing is inherently
low-turnover.

| | full period | stress window |
|---|---|---|
| cost as % of gross return | **5.0 – 7.1%** | (embedded in net figures below) |

**This confirms explicitly what the brief predicted**: monthly rebalancing
sits in a completely different cost regime from every intraday family tested
in this project. Compare cost_R elsewhere: M1 breakout 60.5%, ORB 5.7-17.5%,
Sneaky Pivot 5.8-17.3%. Cross-sectional rotation's cost load is **roughly an
order of magnitude smaller** than the typical intraday candidate, and this is
the structural reason the family survives where the others didn't — even
though the final verdict is still a kill (below).

### The result — full period

| gate | result |
|---|---|
| look-ahead guard | **4/4 PASS** |
| net Sharpe (range across 4 cells) | **0.514 – 0.541** (a tight cluster — N/K barely matters) |
| gross Sharpe | 0.526 – 0.550 |
| net CAGR | 5.9 – 6.7% |
| maxDD | 32.0 – 44.6% |
| top single year ≤ 60% of total net log-return | **4/4 PASS** (12.4 – 13.8%) — first candidate in this project to clear this gate at all |
| DSR > 0.95 (structural pool = this batch's own 4 a priori cells) | **0/4** (best 0.500, E[max SR] +0.541) |
| beats SPY buy-and-hold (Sharpe 0.650, CAGR 10.86%, maxDD 55.2%) | **0/4** |
| **SURVIVORS** | **0/4** |

The DSR pool is tiny (N=4) and still cannot be cleared, because the four
cells' Sharpes (0.514-0.541) are so close together that none of them is an
outlier even against a 4-trial null — a genuinely flat, robust result rather
than a lucky best-of-4.

### The result — stress window, 2000-01-01 → 2009-12-31, SAME 4 configs, unchanged

Per STATE_OF_PLAY section 7 rule 3 (test the stress window, don't skip it).
Universe availability in this window, stated plainly:

| coverage | tickers |
|---|---|
| full coverage (pre-2000 start) | SPY, the 9 original SPDR sectors, IWM |
| partial coverage (phases in mid-window at real inception) | EFA (2001-08), TLT/IEF (2002-07), EEM (2003-04), GLD (2004-11) |
| **not available at all** | XLRE (2015), XLC (2018) — absent from ranking entirely for the whole window |

| gate | result |
|---|---|
| net Sharpe (range) | **0.562 – 0.696** — HIGHER than the full-period range |
| net CAGR | 9.0 – 11.5% |
| maxDD | same figures as full period (the stress window sits inside the worst full-period drawdown) |
| DSR > 0.95 (this batch's own 4-cell stress pool) | **0/4** (best 0.489) |
| beats SPY buy-and-hold (Sharpe **0.071**, CAGR **−0.52%** over the decade) | **4/4 PASS** |

The market filter is doing real work here: SPY buy-and-hold is essentially flat
over the dot-com crash + financial crisis decade, while the rotation earns a
Sharpe in the 0.56-0.70 range **by sidestepping the two crashes**, not by
picking better sectors during them.

### Why this is a kill, and why it is a more interesting kill than §1-§11

Two gates that killed every prior candidate — cost and single-year
concentration — **do not fire here at all**. That is a genuinely new outcome
in this project. But two other gates still bind:

1. **Loses to SPY buy-and-hold in the regime that supplies most of the
   sample.** The 1998-2026 full period is dominated by a multi-decade equity
   bull market with two sharp-but-short crashes (2008, 2020) that a monthly
   200-day-SMA filter reacts to with a lag; SPY's own Sharpe (0.650) simply
   outruns a diversified, partially-defensive rotation across that much
   history. This is the mirror image of the stress-window result: the filter
   that saves the strategy in 2000-2009 costs it Sharpe in the 27-year
   aggregate.
2. **DSR cannot clear 0.95 even against a 4-cell pool**, because the grid is
   flat. This is the opposite failure mode from every prior candidate (which
   typically failed DSR by being mediocre against a *demanding* pool of dozens
   of cells). Here the pool is minimal and the bar is still not cleared,
   because there is no standout cell to reward — the finding (rotation +
   trend filter helps in equity stress regimes) is more robust than any
   single N/K choice within it, and DSR by construction refuses credit for
   that kind of flat robustness.

**Verdict: KILL, same standard as every other section.** It does not clear
DSR, and it loses to the simplest possible benchmark (SPY buy-and-hold) over
the period that matters most for total return. It is recorded in detail
because it is the first candidate whose cost and concentration profile
resembles a genuinely deployable strategy, and because a future session
revisiting cross-sectional rotation should start from "the mechanism helps in
crashes, and still loses to indexing across a multi-decade bull market" rather
than re-deriving that from scratch.

### Files

| file | what it is |
|---|---|
| `scripts/download_momentum_universe.py` | yfinance daily pull, retry-on-failure, per-ticker report |
| `research/momentum_rotation.py` | ranking, weighting, market filter, causal simulation, look-ahead guard |
| `run_momentum_rotation.py` | driver: full period + stress window, DSR, concentration, buy-and-hold comparison, verdict |
| `data/momentum_universe_adjclose.csv`, `data/*_daily_yfinance.csv`, `data/momentum_universe_report.csv` | raw + merged data |
| `results/momentum_rotation_configs.csv`, `results/momentum_rotation_summary.txt`, `results/momentum_rotation_run.log` | the numeric evidence behind this section |

Reproduce: `python scripts/download_momentum_universe.py && python run_momentum_rotation.py`

**Cumulative trials: N=630** (622 prior + 4 full period + 4 stress window).
