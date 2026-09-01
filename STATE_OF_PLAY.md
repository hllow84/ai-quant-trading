# STATE OF PLAY — AI Quant Trading Lab

**Last updated: 2026-08-30 (momentum rotation SECOND audit §12.3 — 6 more checks, no new bugs, filter and cost robustness both PASS).** Read this file first in any new session. It is the
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
>
> **SECOND AUDIT (§12.3, same day) ran 6 more checks — trial-count honesty,
> ticker inception integrity on all 27 instruments, a filter-design
> perturbation test (150d/250d SMA, bi-monthly rebalance), a 4x cost
> bracket, sized survivorship, and DSR pool re-derivation. No new bug.
> The two mechanism-stress-tests both came back ROBUST: full-period Sharpe
> spans only 0.566-0.639 and stress Sharpe 0.523-0.610 across all filter
> variants (none flips sign or collapses), and doubling transaction costs
> moves the CAGR margin over SPY by only -0.25pp. Verdict unchanged: KILL
> on DSR alone, now the most thoroughly-audited result in this project.**
>
> **SAME-DAY AUDIT (§12.1) FOUND A REAL BUG IN THE ABOVE.** Full-period
> metrics had been computed over the strategy's entire 1993-2026 data span
> including 6.4-7.0 years before it could structurally trade (insufficient
> lookback/SMA history) — those years sit in the return series as exact
> zeros, which pads volatility and CAGR down. Recomputed on the correct
> live-only window with SPY sliced identically: **the rotation beats SPY on
> Sharpe in ALL 4 full-period configs (0.578-0.608 vs SPY's 0.511-0.518),
> not 0/4 as first reported**, and a vol-matched (levered-to-SPY's-vol)
> comparison beats SPY's CAGR in all 4 full-period AND all 4 stress-window
> configs. **The verdict is still KILL — DSR alone remains unclearable
> (best 0.505 against a 0.95 bar)** — but the reason is narrower and the
> finding is stronger than first reported. A widened 27-instrument universe
> (§12.2) changes nothing: still 0/4, DSR is still the only binding gate.

---

## 1. BOTTOM LINE — the FTMO hunt is concluded, and the answer is no

**Across 946 systematic backtest configurations, no FTMO-viable edge was found —
and no own-capital edge either (§6).** The closest thing to a positive result in
the whole project is §12 (audited in §12.1, widened in §12.2): a portfolio-level
cross-sectional momentum rotation whose cost and concentration profile is clean
for the first time, which beats SPY buy-and-hold on a risk-adjusted (Sharpe)
basis in BOTH the full period and the stress window once a measurement bug in
the original run is corrected, and whose vol-matched CAGR beats SPY buy-and-hold
in all 8 tested cells across both windows — but which still cannot clear DSR
against even its own 4-cell pool, in either the 17-instrument or the widened
27-instrument universe. §9.4 (a setup whose GROSS edge survives out of regime
but cannot pay its own transaction costs) is the closest positive result among
the price-pattern candidates specifically.

Trial composition (this is the cumulative DSR trial count, N=1030 — see the
2026-09-01 line at the foot of the table for the +84 ORB entry-filter batch, §10.5):

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
| Cross-sectional momentum rotation, full period + 2000-09 stress (§12) | 17-ETF universe, SPY benchmark | 8 | 0 survive; audited §12.1, DSR is the sole blocking gate |
| Cross-sectional momentum rotation, widened universe (§12.2) | 27-instrument universe, SPY benchmark | 8 | 0 survive (§12.2) — same DSR ceiling |
| Crypto, 5 fam × 3 var × 3 TF (§13) | BTCUSDT, ETHUSDT | 90 | 0 survive (§13) — cost-vs-stop-distance kills it, same mechanism as §11 |
| Individual US stocks, in regime (§14) | AAPL, JPM, XOM, JNJ, WMT, CAT | 90 | 0 survive (§14) — DSR + buy-and-hold both bind |
| Individual US stocks, 2010-17 out-of-regime (§14) | AAPL, JPM, XOM, JNJ, WMT, CAT | 90 | 0 survive (§14) — most durable gross edge in the project, still killed |
| Regime-adaptive strategy selection, safeguarded (§15) | BTCUSDT, ETHUSDT | 4 | 0 survive (§15) — new failure mode: switching signal too noisy for hysteresis to bind |
| Regime-switch lookback expansion, 12/24mo (§16) | BTCUSDT, ETHUSDT | 4 | 0 survive (§16) — confirms §15 across the full lookback range |
| Momentum rotation generalization (§17) | crypto sectors (4), country ETFs (4) | 8 | 0 survive (§17) — kills on both, for two different reasons |
| Positioning-extreme contrarian reversal (§18) | BTCUSDT, ETHUSDT | 8 | 0 survive (§18) — first non-price-based signal tested, clean kill |
| Volatility risk premium harvest (§20) | SVXY (VIX vs SPY realized vol) | 2 | 0 survive (§20) — KILLED ON TAIL RISK: -83% single-day loss (2018 Volmageddon), regardless of headline Sharpe |
| Protected VRP structures (§21) | SVXY + cash / VIX circuit breaker / VIXY hedge | 12 | 0 survive (§21) — only small fixed sizing (f=0.10) stays inside the account bar, and it shrinks CAGR to ~2% at SR +0.43 < SPY; breaker & hedge are blind to same-day gap events |
| ORB entry filters — RETEST + DI, each separately, both windows (§10.5) | XAUUSD, NAS100, US30, BTCUSDT | 84 | 0 survive (§10.5) — RETEST fixes concentration/DD/OOS in regime but fails DSR, buy-and-hold and the 2013-17 out-of-regime gate; DI inert; BTCUSDT cost-doomed |
| **Total** | | **1030** | **0 survive** |

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
| **Cross-sectional momentum rotation, full + stress + widened universe** | **16** | **cost & concentration clean, beats B&H Sharpe in BOTH windows after an audit bug-fix (§12.1), vol-matched CAGR beats B&H in all 8 cells — still fails DSR alone, widened universe (§12.2) doesn't change it** |

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

### 10.5 TWO MORE ENTRY FILTERS — RETEST and +DI/-DI, tested 2026-09-01, both killed

**Question:** the plain ORB kill (§10) and its two prior variants (§10.2 moderate
stop, §10.4 trend filter) all died the same way — an in-regime edge that (a)
inverts or vanishes out of regime and (b) is single-year concentrated. Do either
of two *entry-selection* filters survive where those died? Tested **each filter
SEPARATELY** (never combined), on **every instrument with M1 on disk**, always
reported next to the unfiltered baseline in the same run.

**Instruments & data.** M1 already on disk: **XAUUSD** (2018-2025), **NAS100 /
US30** (2018-2025 + 2013-2017 M1RTH out-of-regime). **BTCUSDT M1 was pulled
fresh** for this test (`scripts/download_btcusdt_m1_binance.py`, Binance's own
`data.binance.vision` 1m archive, 2018-01-01 → 2026-09-01, 4.55M bars, 30
historical exchange-outage gaps, modelled spread ~0.0013 bps per §13 — ETH
skipped, "same as BTC for trend" per the brief). **No pre-2018 out-of-regime
window exists for XAUUSD (no pre-2018 M1) or BTCUSDT (Binance starts 2017-08) —
stated, not worked around.** Crypto session = the repo's existing 00:00-23:59
UTC day (`run_sweep_crypto.py` boundary), *not* a re-invented "session".

**Risk parameters (exact, from `research/ftmo_engine.py`, not inherited
silently).** Fixed-fractional **1.00%** of equity per trade (`RISK_PER_TRADE =
0.01`). Stop = opposite side of the OR; **1R = the OR width, UNCHANGED by either
filter** (both filters only change trade *selection* / entry *timing*, so the
comparison against the baseline is like-for-like). Targets 1R / 2R /
hold-to-session-close. One position per instrument per day, no pyramiding. Costs
per instrument = its existing sections' model (XAUUSD legacy $/oz; NAS100/US30
the §10 spread + 0.35 bps + ET-anchored 1.00/0.15 bps slippage; BTCUSDT the §13
20 bps taker + 1-2 bps slippage).

**Filter 2 — RETEST (definition used, stated before the result).** After the
first break of the day, price must return to **within 10% of the OR's own width**
of the broken level (long: a later bar's low ≤ or_high + 0.10·range), **within
the remainder of the same session**. If a bar **closes back through** the broken
level first, the setup is **CANCELLED for the day — no immediate-entry fallback,
no trade** (stated explicitly). Entry on a good retest = limit fill at the broken
OR level.

**Filter 5 — DIRECTIONAL MOVEMENT (definition used).** Standard **Wilder
14-period DMI on the session (daily) bars, `.shift(1)`** so it is strictly
causal. Long breaks only if +DI > −DI on the prior session, shorts only if
−DI > +DI, else no trade. ("At the moment of breakout" read as the prevailing
*daily* DMI state — a 14-minute intrabar DMI is noise and the breakout session's
own bar would be look-ahead, exactly as §10.4 read its trend filter.)

**Grid.** 4 instruments × (1-2 windows) × 2 OR × 3 targets × 3 variants
(ORIGINAL / RETEST / DI). **New trials this batch: 84** (72 filter cells + 12
first-time ORIGINAL cells for XAUUSD/BTCUSDT; the NAS100/US30 ORIGINAL cells
reproduce §10 and are not re-counted). Look-ahead guard **PASS 108/108**.

**Result — batch summary (traded cells; gates: guard + grossPF>1 + netPF>1 +
SR>0 + DSR>0.95 + OOS holds + top-year ≤60% + beats B&H):**

| variant | cells | grossPF>1 | netPF>1 | SR>0 | DSR>0.95 | OOS holds | not year-conc | beats B&H | **SURVIVORS** |
|---|---|---|---|---|---|---|---|---|---|
| ORIGINAL | 36 | 25 | 5 | 5 | 0 | 1 | 0 | 0 | **0** |
| **RETEST** | 36 | **34** | **18** | **18** | **0** | **17** | **15** | **4** | **0** |
| DI | 36 | 26 | 6 | 6 | 0 | 3 | 1 | 0 | **0** |

**RETEST is the most interesting negative in the whole ORB block.** In regime it
does what §10.2 and §10.4 could not: it roughly **halves-to-quarters max
drawdown** (e.g. XAUUSD OR30 1R 41%→10%; US30 OR15 1R 61%→14%), **fixes the
single-year concentration** (not-concentrated 0/36 → 15/36), **makes OOS hold**
(1/36 → 17/36), and turns net PF positive in half the cells. And it still **does
not survive**, on three independent gates:

1. **DSR 0/36.** Best cell XAUUSD OR30 1R: gross PF 1.78, net PF 1.34, SR **+1.14**,
   top-year 36%, DD 10% — DSR **0.000**. Recomputed against a *clean* structural
   pool (in-regime RETEST+DI cells, BTCUSDT excluded as cost-doomed, n=36,
   E[max SR] +1.378): DSR only **0.282**, every other RETEST cell < 0.10. The
   Sharpe uplift (~+0.5 to +1.1) is inside the noise of testing this many cells.
2. **Beats buy-and-hold only 4/36** — and all 4 are US30/NAS100 cells where the
   index B&H Sharpe is low (+0.55). Against gold (B&H SR **+1.19**) the best
   RETEST cell (+1.14) still loses.
3. **Out of regime (2013-2017, NAS100/US30): 0/12 net-PF-positive**, every cell
   SR-negative (netPF 0.70-0.99, best NAS100 OR15 close 0.991 / SR −0.03). The
   in-regime improvement is a **2018-2025 phenomenon — the same signature that
   killed §10, §10.2 and §10.4.**

**DI is inert.** Removes ~50% of trades, moves mean net PF by **+0.02** and mean
SR by **+0.01** vs baseline, clears no gate the baseline didn't. Fails DSR, OOS,
concentration and B&H everywhere.

**BTCUSDT is structurally dead on cost** on all three variants: cost_R **52-77%
of 1R** (20 bps taker fee against a ~25-50 bps OR stop), net PF 0.2-0.7, SR −1 to
−9, maxDD ~100%. Confirms §11 (tight-stop intraday) and §13 (crypto cost
structure). No out-of-regime window exists to test further.

**Verdict — plain kill.** Neither entry filter, on any instrument, in any
window, clears every gate. RETEST comes closest (XAUUSD OR30 1R) and fails on
DSR, on buy-and-hold, and — where it can be tested — out of regime. A *different*
retest study (a stop wide enough not to be cost-dominated; retest tolerance and
window as free-but-stated parameters; 2013-2017 tested first) remains logically
possible and would carry its own trials — but the plain, pre-registered form
here does not survive. **Cumulative trials: N=1030** (946 prior + 84).

### Files (10.5)

| file | what it is |
|---|---|
| `strategies/orb.py` | `wilder_dmi_direction()` + `orb(..., retest=, di_dir=, session_tz=, open_min=, close_min=, min_sess_bars=)` — additive; all defaults reproduce §10 byte-identically (verified: default call == explicit ET-session call, identical entry times) |
| `run_orb_entry_filters.py` | the runner — 4 instruments, both windows, 3 variants/cell, all gates, DSR (structural + clean recompute), the comparison table |
| `scripts/download_btcusdt_m1_binance.py` | the one-off BTCUSDT M1 pull (binance.vision archive + ccxt tail) |
| `results/orb_entry_filters.csv`, `orb_entry_filters_scored.csv`, `orb_entry_filters_run.log` | the numeric evidence |
| `data/BTCUSDT_M1_2018_2025_binance.csv` | 418 MB, gitignored; reproduce with the download script |

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

> ⚠️ **2026-08-30, same day — AUDITED. The "loses to SPY on the full period"
> finding above was a MEASUREMENT BUG, not a strategy fact — see §12.1. The
> corrected verdict is still KILL, but for a narrower reason (DSR only), not
> the reason stated above. Read §12.1 before citing the full-period Sharpe or
> CAGR numbers in this section.**

---

## 12.1 AUDIT of section 12 — one real bug found, verdict narrows but does not flip

Five checks were run against the §12 code and data, independently, after the
original run: `scripts/audit_momentum_rotation.py`, full output in
`results/momentum_rotation_audit_run.log`.

### Audit 2 — risk-free rate consistency: PASS, no issue

`research/metrics.py::sharpe()` is `mean(returns)/std(returns) * sqrt(bars_per_year)`
— no risk-free subtraction anywhere. `run_momentum_rotation.py` calls this
**same function** for both the rotation configs and `spy_buy_hold()`. One
function, two call sites, so both sides are structurally guaranteed to treat
the risk-free rate identically (zero, on both). No fix needed.

### Audit 3 — total-return correctness: PASS, verified empirically

`scripts/download_momentum_universe.py` pulls every ticker — the ranked
universe, SPY, **and IEF** — through one loop and one `yf.download(...,
auto_adjust=True)` call site; there is no branch that treats the benchmark or
the defensive leg differently. Confirmed empirically, not just by reading the
code (fresh pull, 2003-01-02 → 2003-05-30, `auto_adjust=True` vs `False`):

| ticker | adj/raw close ratio, 2003-01-02 | adj/raw close ratio, 2003-05-30 |
|---|---|---|
| SPY | 0.6515 | 0.6541 |
| IEF | 0.5030 | 0.5095 |

Both ratios are far from 1.0 and drift toward 1.0 as of 2025 (the adjustment
factor shrinks as fewer future distributions remain to be backed out) — proof
that dividend/coupon reinvestment is baked into the adjusted series for
**both** the equity benchmark and the bond defensive leg, not just the ranked
universe.

### Audit 4 — survivorship: stated limitation, not fixed

The 17-ETF + SPY universe (and the 27-instrument expanded universe in §12.2)
consists only of funds that exist and trade today; any sector or asset-class
ETF that was ever delisted, merged, or never launched is absent by
construction, and free data cannot correct this. Known, unfixed limitation —
not fabricated around.

### Audit 5 — general code review: one real bug found

Re-reading `momentum_rotation.py`/`run_momentum_rotation.py` end to end
surfaced one issue not caught by audits 1-4: **`compute_metrics()` in the
original driver computed "full period" Sharpe/vol/CAGR over the ENTIRE
`adjclose` span (1993-01-29 → 2026-08-28, 8,453 daily observations), but no
config can trade before it has enough lookback history** — `build_weights()`
correctly refuses to emit a weight row until N months of universe data and
200 days of SPY history exist, so the **first live rebalance is 1999-07-01
(N=6) or 2000-01-03 (N=12)**. `simulate()` fills exactly `0.0` return for
every day before the first execution date (by construction, since
`weights_daily` is all-zero there) — those days are real rows in the daily
return series, not NaNs, so `dropna()` does not remove them and they entered
every full-period statistic.

This pads volatility **down** (6.4-7.0 years of exact-zero return days lower
the sample variance) and pads CAGR **down** (the same total return gets
divided by ~33.5 years instead of the ~27 years actually invested) — a
conservative-direction bug, not a flattering one, but a real one, and it also
means the original vol-mismatch reported in the section 12 banner note (which
audit 1 was designed to check) was computed on the wrong window.

No other unverified assumption survived the re-read: the causal execution
lag, the cost model's turnover computation, the DSR pool construction, and the
concentration calculation (which is unaffected by this bug — padding
years contribute exactly `log(1+0)=0` to both the numerator and denominator of
the top-year-share ratio, changing nothing) were all re-derived and match
their stated behavior.

### Audit 1 — volatility mismatch, RECOMPUTED on the corrected (live-window) period

`window_metrics()` now computes both the strategy and SPY over the **identical**
window — `[first_exec_date, panel_end]` per config — instead of SPY's full
1993-2026 history against the strategy's zero-padded full-history series.

| N | K | live window starts | corrected vol | corrected Sharpe | corrected CAGR | SPY vol (same window) | SPY Sharpe (same window) | SPY CAGR (same window) |
|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 1999-07-01 | 15.49% | **0.596** | 8.36% | 19.23% | 0.518 | 8.43% |
| 6 | 5 | 1999-07-01 | 13.92% | **0.582** | 7.38% | 19.23% | 0.518 | 8.43% |
| 12 | 3 | 2000-01-03 | 15.82% | **0.578** | 8.20% | 19.27% | 0.511 | 8.36% |
| 12 | 5 | 2000-01-03 | 14.49% | **0.608** | 8.07% | 19.27% | 0.511 | 8.36% |

**The vol mismatch is real and confirmed** — the strategy runs 19-28% lower
annualised volatility than SPY over the identical window in every cell, driven
by the defensive filter, exactly as hypothesised. **And the correction reverses
the original "loses to SPY" reading on RISK-ADJUSTED terms**: on the properly
matched window, the rotation's Sharpe (0.578-0.608) **beats** SPY's Sharpe
(0.511-0.518) in **all 4 configs**, unlevered — this did not hold in the
original padded computation (0.514-0.541 vs SPY's full-history 0.650).
Unlevered CAGR is still marginally below SPY's (7.4-8.4% vs 8.4-8.4%) because
the strategy is running noticeably less risk to get there.

### Vol-matched (constant-leverage) comparison — full period

A single constant leverage multiplier (`SPY_vol / strategy_vol` on that
config's live-window vol, applied to daily net returns, no re-optimisation)
was applied to each config:

| N | K | leverage to match SPY vol | vol-matched Sharpe | vol-matched CAGR | vol-matched maxDD | SPY CAGR (same window) | vol-matched CAGR vs SPY |
|---|---|---|---|---|---|---|---|
| 6 | 3 | 1.241x | 0.596 | **10.08%** | 40.58% | 8.43% | **BEATS by +1.65pp** |
| 6 | 5 | 1.381x | 0.582 | **9.78%** | 42.00% | 8.43% | **BEATS by +1.35pp** |
| 12 | 3 | 1.218x | 0.578 | **9.71%** | 52.00% | 8.36% | **BEATS by +1.35pp** |
| 12 | 5 | 1.330x | 0.608 | **10.36%** | 49.25% | 8.36% | **BEATS by +2.00pp** |

**Vol-matched CAGR beats SPY buy-and-hold in all 4 configs, full period.**
Levered maxDD (40.6-52.0%) stays below SPY's own 55.2% in every cell despite
matching its volatility — a symptom of the defensive filter's non-normal
return shape (it caps downside participation, so matching *average* vol still
leaves a smaller max loss). **Financing cost of the leverage and overnight/
gap risk at 1.2-1.4x are NOT modelled** — the same caveat section 2 raised
for the old macross basket lead applies here unchanged: this shows the
volatility-adjusted comparison is fair, not that a 1.2-1.4x levered ETF
rotation is a deployable product.

### Vol-matched comparison — stress window 2000-2009 (unaffected by the padding bug)

| N | K | raw Sharpe | raw CAGR | leverage | vol-matched Sharpe | vol-matched CAGR | vol-matched maxDD | SPY CAGR |
|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 0.696 | 11.45% | 1.263x | 0.696 | **14.08%** | 41.17% | −0.91% |
| 6 | 5 | 0.684 | 10.05% | 1.437x | 0.684 | **13.87%** | 43.37% | −0.91% |
| 12 | 3 | 0.563 | 9.00% | 1.226x | 0.563 | **10.63%** | 52.25% | −0.91% |
| 12 | 5 | 0.610 | 9.08% | 1.362x | 0.610 | **11.82%** | 50.19% | −0.91% |

SPY's own stress-window Sharpe recomputed here is 0.067 / CAGR −0.91% (a small
restatement from the original run's 0.071 / −0.52%, because the original
number was also computed on the un-matched 1993-2026-length SPY series sliced
to the window rather than a window-local recomputation — same bug, opposite
side, immaterial to any verdict since both were already near-flat). **Vol-matched
CAGR beats SPY by 10.9 to 15.0 percentage points a year in the stress
window, in all 4 configs** — a far larger margin than the full-period result,
because the filter's crash-avoidance is the dominant effect precisely when
SPY is flat-to-negative.

### DSR, recomputed on the corrected Sharpes — the gate that actually decides this

| window | N | K | corrected Sharpe | DSR (own 4-cell pool) |
|---|---|---|---|---|
| full | 6 | 3 | 0.596 | 0.4805 |
| full | 6 | 5 | 0.582 | 0.4512 |
| full | 12 | 3 | 0.578 | 0.4429 |
| full | 12 | 5 | 0.608 | **0.5053** (best) |
| stress | 6 | 3 | 0.696 | 0.4889 |
| stress | 6 | 5 | 0.684 | 0.4744 |
| stress | 12 | 3 | 0.563 | 0.3271 |
| stress | 12 | 5 | 0.610 | 0.3833 |

Still **0/4 clear 0.95 in either window** — the correction moves every DSR up
modestly (E[max SR] rose to 0.605 full / 0.704 stress on the corrected,
tighter Sharpe cluster) but the grid remains too flat for any single cell to
separate from a 4-trial null.

### Corrected verdict

Re-running the original 5 survival gates with the corrected full-period
Sharpe:

| gate | original (buggy) | corrected |
|---|---|---|
| DSR > 0.95, full | 0/4 | 0/4 (unchanged) |
| DSR > 0.95, stress | 0/4 | 0/4 (unchanged) |
| top-year ≤ 60%, full | 4/4 PASS | 4/4 PASS (unaffected by the bug) |
| **beats SPY Sharpe, full** | **0/4 FAIL** | **4/4 PASS — the bug flipped this gate** |
| beats SPY Sharpe, stress | 4/4 PASS | 4/4 PASS (unaffected — already inside the live window) |
| **SURVIVORS** | **0/4** | **0/4 (unchanged)** |

**The verdict does not change — still KILL — but the REASON narrows.** The
original section 12 said the strategy loses to buy-and-hold in the regime
that supplies most of the sample; that was an artefact of comparing SPY's true
33.5-year Sharpe against the rotation's bug-diluted 27-year-diluted-by-6.5-
zero-years Sharpe. On a fair, identical window, **the rotation beats SPY on a
risk-adjusted (Sharpe) basis in the full period as well as the stress window,
and vol-matched CAGR beats SPY in every one of 8 cells across both windows.**
What kills it is **DSR alone**: the N/K grid is genuinely too flat (Sharpe
0.578-0.608 full, a 0.03 spread) for any cell to be a statistical outlier
against even its own tiny 4-trial pool. This is the same reading as the
original section 12 closing paragraph, now on firmer ground: a real, robust
finding with no single config extreme enough for DSR to reward it — but now
demonstrably also a finding that **outperforms indexing** on the metric that
matters (risk-adjusted return), not one that loses on both counts as first
reported.

Files: `scripts/audit_momentum_rotation.py`. Results:
`results/momentum_rotation_audit_full.csv`, `momentum_rotation_audit_stress.csv`,
`momentum_rotation_audit_run.log`. Reproduce: `python scripts/audit_momentum_rotation.py`.

Not a new trial batch — this is a re-verification and bug-fix of the existing
8 trials from section 12, run against the same data and same configs.
Cumulative trial count unchanged by the audit itself: **N=630**.

---

## 12.2 WIDENED UNIVERSE — separate test, run after the audit, does not change the verdict

Per the audit brief, a second and independent question: does adding more
liquid instrument classes change the result? 10 new tickers were added to the
17-ETF base universe (27 ranked instruments total, SPY still benchmark-only),
same causal rebalance logic, same 4-cell grid, same cost model, same
audit-corrected (live-window) metric methodology from the start.

| category | tickers added | verified inception |
|---|---|---|
| commodities | DBC, USO, UNG, SLV | 2006-02, 2006-04, 2007-04, 2006-04 (GLD already in base, 2004-11) |
| international / country | VGK, INDA, FXI | 2005-03, 2012-02, 2004-10 |
| factor | MTUM, VTV | 2013-04, 2004-01 |
| mid-cap breadth | MDY | 1995-05 (IWM small-cap already in base, 2000-05) |

All pulled fresh via `scripts/download_momentum_universe_expanded.py` (same
`period="max"`, `auto_adjust=True` method as the base pull), real verified
dates, nothing fabricated or backfilled.

### Full period (live window, expanded universe)

| N | K | live from | Sharpe | SPY Sharpe (same window) | CAGR | SPY CAGR | maxDD | top-year share | beats SPY Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 1999-07-01 | 0.479 | 0.518 | 7.32% | 8.43% | 36.37% | 18.5% | **NO** |
| 6 | 5 | 1999-07-01 | 0.558 | 0.518 | 7.70% | 8.43% | 31.77% | 13.4% | yes |
| 12 | 3 | 2000-01-03 | 0.537 | 0.511 | 8.65% | 8.36% | 43.71% | 18.6% | yes |
| 12 | 5 | 2000-01-03 | **0.630** | 0.511 | **9.18%** | 8.36% | 37.50% | 14.0% | yes |

### Stress window 2000-2009 (same 4 configs; most new tickers only partially cover this window, stated above the numbers in the run log — INDA and MTUM are absent entirely, others phase in 2004-2007; only MDY has full coverage)

| N | K | Sharpe | SPY Sharpe | CAGR | SPY CAGR | maxDD | beats SPY Sharpe |
|---|---|---|---|---|---|---|---|
| 6 | 3 | 0.710 | 0.067 | 12.49% | −0.91% | 33.86% | yes |
| 6 | 5 | **0.816** | 0.067 | **13.01%** | −0.91% | 31.77% | yes |
| 12 | 3 | 0.640 | 0.067 | 11.76% | −0.91% | 43.71% | yes |
| 12 | 5 | 0.704 | 0.067 | 11.47% | −0.91% | 37.50% | yes |

### DSR and verdict — unchanged from §12.1

| window | best DSR (own 4-cell pool) |
|---|---|
| full | 0.5279 (N=12, K=5) |
| stress | 0.5276 (N=6, K=5) |

**0/4 survive in either window — same DSR ceiling problem as the base
universe.** 3/4 configs beat SPY on Sharpe full-period (N=6,K=3 is the one
exception — the widened universe hands it slightly noisier signal, not
better), and 4/4 beat SPY in the stress window, both consistent with §12.1.
**Widening the universe does not change the verdict**: DSR remains the sole
binding gate, and the wider instrument set neither produces a config extreme
enough to clear it nor changes which gate is doing the killing. This result is
reported separately from the vol-matching test in §12.1 — the two are
independent findings and must not be conflated: vol-matching answers "is the
comparison to SPY fair," universe-widening answers "does more breadth help,"
and the answers are "yes, and once fair the strategy already wins on Sharpe"
and "no, breadth doesn't move the needle," respectively.

Files: `scripts/download_momentum_universe_expanded.py`, `research/momentum_rotation.py`
(gained an optional `universe` parameter, additive, default preserves section
12 byte-identically), `run_momentum_rotation_expanded.py`. Data:
`data/momentum_universe_expanded_adjclose.csv`, `data/{DBC,USO,UNG,SLV,VGK,INDA,FXI,MTUM,VTV,MDY}_daily_yfinance.csv`,
`data/momentum_universe_expanded_report.csv`. Results:
`results/momentum_rotation_expanded_full.csv`, `momentum_rotation_expanded_stress.csv`,
`momentum_rotation_expanded_run.log`. Reproduce:
`python scripts/download_momentum_universe_expanded.py && python run_momentum_rotation_expanded.py`

**Cumulative trials: N=638** (630 prior + 4 full period + 4 stress window,
expanded-universe grid; this is a genuinely new a priori design choice — a
different, wider instrument set — not a re-scoring of section 12's 8 trials).

---

## 12.3 SECOND AUDIT — six more checks, no new bugs found, two robustness tests both PASS

The first audit (§12.1) found and fixed one real bug. Passing five prior
checks is not evidence nothing else is wrong, so this is a second, independent
pass, assuming more could remain. `scripts/audit_momentum_rotation_2.py`, full
output in `results/momentum_rotation_audit2_run.log`.

### Audit 6 — honest trial count behind the grid

`git log --oneline --all -- research/momentum_rotation.py run_momentum_rotation.py
scripts/download_momentum_universe.py` shows **exactly two commits ever touched
this strategy's code**: the initial implementation and the audit-1 fix +
widened-universe commit. `git show <first-commit>:research/momentum_rotation.py`
confirms the **first committed version already contains** `SMA_WINDOW=200`,
monthly rebalance, and `GRID=[(n,k) for n in (6,12) for k in (3,5)]` — the
exact parameters specified verbatim in the task prompt that opened this line
of work. No other commit, branch, stash, or reflog entry touches this file,
and no other `run_momentum_rotation*.py` variant exists in the repository
before that first commit.

**Conclusion: the grid was chosen before any result was seen, with HIGH
confidence from git history — not proof.** A value could in principle have
been explored interactively and never saved to any file; no evidence of that
exists, and none can be ruled out with absolute certainty from a git history
alone. Stated honestly rather than asserted. If such unsaved exploration had
occurred, the true trial count behind the reported 4-cell pool would be
**understated**, E[max SR] would be **higher**, and DSR would be **harder to
clear** — so any residual doubt here pushes the verdict further toward the
kill, never away from it. This is not counted as a new trial batch.

### Audit 7 — ticker inception integrity, all 27 tickers cross-checked externally

Every ticker's `first_valid_index()` in the loaded panel was compared against
its real fund inception date, sourced independently (web search against
stockanalysis.com, etfdb.com, ishares.com, ssga.com, Vanguard fund
documentation, and SEC filings — not taken from the original download script's
own reporting).

| ticker | known inception | data first-valid | gap |
|---|---|---|---|
| SPY | 1993-01-22 | 1993-01-29 | +7d |
| XLK/XLF/XLE/XLV/XLI/XLY/XLP/XLU/XLB | 1998-12-16 | 1998-12-22 (all 9) | +6d |
| XLRE | 2015-10-07 | 2015-10-08 | +1d |
| XLC | 2018-06-18 | 2018-06-19 | +1d |
| TLT / IEF | 2002-07-22 | 2002-07-30 | +8d |
| GLD | 2004-11-18 | 2004-11-18 | +0d |
| IWM | 2000-05-22 | 2000-05-26 | +4d |
| EFA | 2001-08-14 | 2001-08-27 | +13d |
| EEM | 2003-04-07 | 2003-04-14 | +7d |
| DBC | 2006-02-03 | 2006-02-06 | +3d |
| USO | 2006-04-10 | 2006-04-10 | +0d |
| UNG | 2007-04-18 | 2007-04-18 | +0d |
| SLV | 2006-04-21 | 2006-04-28 | +7d |
| VGK | 2005-03-04 | 2005-03-10 | +6d |
| INDA | 2012-02-02 | 2012-02-03 | +1d |
| FXI | 2004-10-05 | 2004-10-08 | +3d |
| MTUM | 2013-04-16 | 2013-04-18 | +2d |
| VTV | 2004-01-26 | 2004-01-30 | +4d |
| MDY | 1995-05-04 | 1995-05-04 | +0d |

**Every one of 27 gaps is ≥ 0 — data never begins before a ticker's known
inception, anywhere.** Gaps range 0–13 days and reflect the standard
distinction between a fund's legal registration date and its first trading
day (the direction is always "data starts a few days to two weeks LATER than
the fund legally existed," never earlier) — expected, not a red flag. No
evidence of backfilled, interpolated, or placeholder pre-inception data in
either the base or widened universe.

### Audit 8 — filter perturbation test: ROBUST

Three one-shot alternative designs, none chosen to flatter the result, tested
against N=12/K=5 (the strongest audited cell) on the base 17-instrument
universe, same live-window methodology, same cost model:

| variant | full Sharpe | full CAGR | full maxDD | stress Sharpe | stress CAGR | stress maxDD |
|---|---|---|---|---|---|---|
| ORIGINAL (200d SMA, monthly) | 0.608 | 8.07% | 39.03% | 0.610 | 9.08% | 39.03% |
| 150-day SMA, monthly | 0.639 | 8.37% | 39.78% | 0.573 | 8.30% | 39.78% |
| 250-day SMA, monthly | 0.599 | 7.89% | 44.10% | 0.523 | 7.28% | 44.10% |
| 200-day SMA, bi-monthly rebalance | 0.566 | 7.65% | 39.03% | 0.586 | 8.61% | 39.03% |

Full-period Sharpe spans **0.566–0.639** (spread 0.073) and stress-window
Sharpe spans **0.523–0.610** (spread 0.087) across all four variants — none
collapses, none inverts sign, none drops below SPY's full-period Sharpe by
more than a rounding error (150d SMA actually improves on the original; 250d
SMA and bi-monthly are the softest but stay firmly positive and in the same
range as the original). **AUDIT 8 VERDICT: ROBUST.** The mechanism (defensive
tilt via a long moving-average filter, monthly-ish rebalance) is not a knife's
edge that only works at exactly 200 days and exactly monthly — it is a real,
broad effect across the entire neighbourhood of reasonable filter choices.

### Audit 9 — cost sensitivity: ROBUST

N=12/K=5, base universe, cost swept from half to double the original 6bps
round-turn assumption (a wide bracket, not a narrow one):

| cost assumption | full Sharpe | full vol-matched CAGR margin vs SPY | stress Sharpe | stress vol-matched CAGR margin vs SPY |
|---|---|---|---|---|
| HALF (3bps round-turn) | 0.614 | **+2.12pp** | 0.614 | **+12.82pp** |
| ORIGINAL (6bps round-turn) | 0.608 | +2.00pp | 0.610 | +12.73pp |
| DOUBLE (12bps round-turn) | 0.596 | **+1.75pp** | 0.604 | **+12.57pp** |

Doubling the cost assumption moves the full-period Sharpe by only **−0.012**
and the vol-matched CAGR margin over SPY by only **−0.25 percentage points** —
the strategy's low turnover (monthly rebalance) means transaction costs were
never close to the margin of the finding, exactly as the structural hypothesis
predicted back in section 12. **AUDIT 9 VERDICT: ROBUST — the conclusion
(beats SPY risk-adjusted, and on vol-matched CAGR) survives even the
pessimistic cost case, in both windows, by a wide margin.**

### Audit 10 — survivorship, sized rather than left as a generic disclaimer

None of the 27 tickers has ever been delisted, merged, or liquidated — all 27
trade actively as of 2026. The one identified corporate action is **FXI's 2011
rename** from "iShares FTSE/Xinhua China 25" to "iShares China Large-Cap ETF"
— same ticker, same fund, same continuous price series, no data gap, no
restatement, no effect on this backtest. The original 9 Select Sector SPDRs
(1998) are the oldest and structurally most stable US sector-ETF family in
existence; XLRE (2015) and XLC (2018) are new launches following real GICS
sector splits, correctly excluded from the ranking pool before their real
launch dates (audit 7), not survivorship-biased inclusions of funds that
"happened" to survive. The residual bias is **universe selection**, not
individual-fund survivorship: this backtest cannot include a sector or
asset-class ETF that was discontinued before 2026 and is unknown to this
audit. For the specific instrument class tested — large, liquid, well-known
SPDR/iShares/Vanguard/Invesco funds — closures in this category are rare, but
no exhaustive historical-closure search was performed. **Sized as small, not
proven zero.**

### Audit 11 — DSR pool construction, re-verified explicitly

`research/dsr.py::structural_pool()` is built for the timeframe×family grid
used by the price-pattern strategies elsewhere in this repo; the
momentum-rotation driver does not call it by name (an N×K grid isn't a
timeframe×family grid) but builds the same-intent a priori pool manually —
this batch's own 4 cells, no outcome selection. Re-derived one more time,
explicitly, from the corrected (post-audit-1) live-window simulation:

**FULL pool:** `[0.595921, 0.581640, 0.577558, 0.607983]` (N6K3, N6K5, N12K3,
N12K5) — identical to the values audit 1 reported, confirmed not stale.
**STRESS pool:** `[0.695629, 0.684052, 0.562532, 0.610368]` — also identical.
DSR values recomputed from these pools match audit 1 to 4 decimal places
(best full 0.5053, best stress 0.4889). **No discrepancy found.**

### Updated verdict after the second audit

**No new bug was found.** Six additional checks — trial-count honesty, ticker
inception integrity across all 27 instruments, a filter-design perturbation
test, a wide cost-sensitivity bracket, a sized survivorship estimate, and an
explicit DSR pool re-derivation — all came back clean, and the two checks that
actually stress-test the finding (audits 8 and 9) both came back **ROBUST**,
not fragile.

**What this thoroughness means, plainly:** the section-12/12.1 finding — a
monthly-rebalance, SPY-200-SMA-filtered cross-sectional momentum rotation
beats SPY buy-and-hold on a risk-adjusted (Sharpe) and vol-matched-CAGR basis
in both the full period and the 2000-2009 stress window — is not a fragile
artefact of one exact filter length, one exact rebalance cadence, or an
optimistic cost assumption. It holds across a 150–250 day SMA neighbourhood,
survives a switch to bi-monthly rebalancing, and survives a 4x cost bracket
(half to double the assumed round-turn cost) with the CAGR margin over SPY
barely moving. The universe is free of look-ahead-contaminating pre-inception
data and free of any identified survivorship distortion for the specific 27
funds used.

**What this thoroughness does NOT mean:** it does not make the strategy
DSR-significant — the N/K grid (and every perturbation tested here) clusters
in the same narrow Sharpe band (roughly 0.52–0.64 full period), so no single
configuration is a statistical outlier against even its own tiny a priori
pool, and that is a property of the grid, not something audits 6-11 could
fix. It does not model leverage financing cost or overnight/gap risk for the
vol-matched comparison. It does not correct for universe-selection
survivorship (small, unproven-zero). And it is not evidence that this
specific 4-cell configuration, rather than the broader class of "monthly
cross-sectional rotation with a long-SMA defensive filter," is what should be
deployed — the perturbation test's message is that the MECHANISM is robust,
not that N=12/K=5/200-day/monthly is a privileged point worth over-trusting
relative to its neighbours.

**Verdict: still KILL, on DSR alone, and now the most thoroughly-audited
result in this project's history.** Two independent audits, eleven checks,
one real bug found and fixed (narrowing, not flipping, the kill), zero
fragility found in the two mechanism-stress-tests that matter most.

Files: `scripts/audit_momentum_rotation_2.py`. Results:
`results/momentum_rotation_audit2_inception.csv`,
`momentum_rotation_audit2_perturbation.csv`,
`momentum_rotation_audit2_cost_sensitivity.csv`,
`momentum_rotation_audit2_run.log`. `research/momentum_rotation.py` gained two
additive optional parameters (`sma_window`, `rebalance_step` on
`build_weights()`); default values reproduce sections 12/12.1/12.2
byte-identically. Reproduce: `python scripts/audit_momentum_rotation_2.py`.

Not a new trial batch — audits 6, 7, 10, 11 are verification with no new
backtest cells, and audits 8-9's perturbation/sensitivity runs are one-shot
robustness checks explicitly excluded from the DSR pool (same treatment as
the ORB implementation audit, §10.1-10.3). **Cumulative trial count unchanged:
N=638.**

---

## 12.4 LIVE (paper-first) DEPLOYMENT INFRASTRUCTURE — built 2026-08-31, engineering only, no new trials

Per Brendan's own explicit judgment call (STATE_OF_PLAY §12.3's own read: the
finding is not DSR-significant but the mechanism is robust and beats SPY
risk-adjusted across every audited perturbation), a paper-first live pipeline
was built for the strongest audited cell: **N=12, K=5, 200-day SMA, monthly
rebalance, base 17-ETF universe.** This is engineering, not research — no
new backtest cells, no re-tuning. `research/momentum_rotation.py::build_weights()`
is imported and called unchanged; `live/signals.py`'s module docstring
documents exactly how a live signal for "today" is extracted from it without
modifying that file (a single NaN placeholder row dated into the next
calendar month, so `build_weights()` has an execution-date label to attach
today's weights to — the placeholder's price is never read).

Broker: Alpaca (paper trading environment, genuine live-API mirror, not a
separate simulator). Price data for the signal itself stays on yfinance —
the same source the backtest was validated against — Alpaca is used only for
account state, the trading calendar, and order execution.

**Hard risk limits, code-enforced (`live/risk.py`):** 25% per-ETF position
cap (stated departure from the audited 100%-IEF defensive allocation —
excess in a risk-off signal sits in cash, never redistributed), a 15%
drawdown-from-peak kill switch that halts all new orders until manually
cleared, and a target-weight sanity check (sum to 1.0±1%, no negatives) that
refuses to trade on a malformed signal rather than placing it.

**Paper-trading gate:** `live/config.py`'s `PAPER_ONLY = True` must be
manually edited to place any real order, gated additionally on 3 logged
paper monthly rebalances and an interactive real-money confirmation phrase
(a non-interactive/scheduled run cannot satisfy either the paper-count gate
or the confirmation prompt). First 3 rebalances (paper or live) require a
manual keypress review of the printed trade list.

**Monitoring:** `live/monitor.py` computes trailing Sharpe/CAGR from monthly
equity snapshots, compares against the audited 0.51-0.64 Sharpe range and
SPY buy-and-hold, and states a plain stop-live rule (2 consecutive monitor
runs with negative trailing Sharpe AND >10pp CAGR underperformance vs SPY).

Files: `live/config.py`, `broker.py`, `signals.py`, `risk.py`, `state.py`,
`logging_utils.py`, `rebalance.py`, `monitor.py`, `run_rebalance.bat`,
`README.md`, `.env.example`. Setup and scheduling documented in
`live/README.md`. **No trials added — cumulative trial count unchanged: N=638.**

## 12.5 WALK-FORWARD VALIDATION — the year-by-year record a real allocator reads, run 2026-08-31

The §12.1/§12.3 audits validated the momentum rotation against a single
static split (full period + one 2000-2009 stress window). A walk-forward is
the industry-standard replacement for that: repeated, rolling,
**non-overlapping calendar-year** out-of-sample scoring, exactly the way a
live fund experiences a strategy — one year at a time, never seeing the
future. **Nothing is fitted** — the config is frozen at the original a priori
/ §12.4-deployment cell (**N=12 months, K=5 holdings, 200-day SPY SMA filter,
monthly rebalance, base 17-ETF universe**); `research.momentum_rotation`'s
`build_weights()`/`simulate()` are called unmodified. Walk-forward re-slices
the *same* cost-inclusive (6 bps round-turn) simulated return series by year
and adds zero degrees of freedom — **not a new trial batch, N unchanged**.

First execution date for N=12 is 2000-01-03 (needs 12 months universe history
+ 200 days SPY history — §12.1). First full walk-forward year: **2000**.
Look-ahead guard: **PASS**.

### Year-by-year record, 2000 → 2026 (2026 partial, data ends 2026-08-28)

| year | strat net % | SPY B&H % | beat SPY? | % of year risk-off | cum. strat | cum. SPY | cum. (strat − SPY) |
|---|---|---|---|---|---|---|---|
| 2000 | −7.42 | −9.74 | **YES** | 31 | 0.926 | 0.903 | +0.023 |
| 2001 | −10.99 | −11.76 | **YES** | 100 | 0.824 | 0.796 | +0.028 |
| 2002 | −9.89 | −21.58 | **YES** | 90 | 0.743 | 0.625 | +0.118 |
| 2003 | +29.39 | +28.18 | **YES** | 27 | 0.961 | 0.801 | +0.160 |
| 2004 | +14.39 | +10.70 | **YES** | 14 | 1.099 | 0.886 | +0.213 |
| 2005 | +19.27 | +4.83 | **YES** | 6 | 1.311 | 0.929 | +0.382 |
| 2006 | +22.15 | +15.85 | **YES** | 8 | 1.601 | 1.076 | +0.525 |
| 2007 | +15.94 | +5.15 | **YES** | 11 | 1.857 | 1.132 | +0.725 |
| 2008 | +17.00 | −36.79 | **YES** | 98 | 2.172 | 0.715 | +1.457 |
| 2009 | +9.66 | +26.35 | no | 40 | 2.382 | 0.904 | +1.478 |
| 2010 | +16.35 | +15.06 | **YES** | 24 | 2.771 | 1.040 | +1.731 |
| 2011 | +1.39 | +1.90 | no | 37 | 2.810 | 1.059 | +1.750 |
| 2012 | +5.10 | +15.99 | no | 1 | 2.953 | 1.229 | +1.724 |
| 2013 | +33.03 | +32.31 | **YES** | 0 | 3.928 | 1.626 | +2.303 |
| 2014 | +11.33 | +13.46 | no | 2 | 4.373 | 1.845 | **+2.529 (peak)** |
| 2015 | −6.43 | +1.23 | no | 21 | 4.092 | 1.868 | +2.225 |
| 2016 | −3.72 | +12.00 | no | 19 | 3.940 | 2.092 | +1.849 |
| 2017 | +19.11 | +21.71 | no | 0 | 4.693 | 2.546 | +2.148 |
| 2018 | −11.40 | −4.57 | no | 16 | 4.158 | 2.429 | +1.729 |
| 2019 | +3.48 | +31.22 | no | 11 | 4.303 | 3.188 | +1.115 |
| 2020 | +19.48 | +18.33 | **YES** | 23 | 5.141 | 3.772 | +1.369 |
| 2021 | +15.23 | +28.73 | no | 0 | 5.924 | 4.856 | +1.068 |
| 2022 | −18.91 | −18.18 | no | 81 | 4.804 | 3.973 | +0.831 |
| 2023 | +7.05 | +26.18 | no | 6 | 5.142 | 5.013 | +0.129 |
| 2024 | +17.24 | +24.89 | no | 0 | 6.029 | 6.261 | −0.232 |
| 2025 | +18.17 | +17.72 | **YES** | 17 | 7.124 | 7.370 | −0.246 |
| 2026* | +10.56 | +13.68 | no | 7 | 7.876 | 8.378 | −0.502 |

### HEADLINE METRIC — individual-year consistency vs SPY

**Beat SPY in 13 of 27 years. Underperformed in 14 of 27. Walk-forward
yearly hit rate: 48.1% — a coin flip.**

The 14 losing years, stated plainly (no cherry-picking): 2009 (−16.7 pp),
2011 (−0.5), 2012 (−10.9), 2014 (−2.1), 2015 (−7.7), 2016 (−15.7), 2017
(−2.6), 2018 (−6.8), 2019 (−27.7), 2021 (−13.5), 2022 (−0.7), 2023 (−19.1),
2024 (−7.7), 2026* (−3.1).

### The finding the aggregate Sharpe hid: the edge is entirely pre-2009

| sub-period | years beat SPY | mean annual excess |
|---|---|---|
| **2000–2008** | **9 / 9 (every year)** | **+11.6 pp/yr** |
| **2009–2026** | **4 / 18** | **−8.6 pp/yr** |

Cumulative (strat − SPY) climbed monotonically to **+2.53× at end-2014**,
then declined every year since and went **negative in 2024** (−0.23) — the
strategy now **trails SPY on cumulative growth over the full walk-forward**
(×7.88 vs ×8.38). §12.1's "beats SPY risk-adjusted, full period" (Sharpe
0.61 vs 0.51) is *arithmetically* still true, but the walk-forward shows
**100% of that outperformance was banked in 2000–2008**, when the 200-day
SMA filter parked the book in IEF through the dot-com collapse and the GFC
(2001 100% risk-off, 2002 90%, 2008 98%). Every risk-off *majority* year in
the record (2001, 2002, 2008, 2022) except 2022 is a large win; the filter
is a **crash hedge**, and it has not had a crash to hedge since 2008 that it
also called correctly (2020's drop was too fast for a monthly 200-SMA check;
2022's slow bleed it half-caught, still lost by 0.7 pp).

### Walk-forward aggregate (2000 → 2026-08), context only

| | strategy | SPY B&H |
|---|---|---|
| CAGR | 8.07% | 8.32% |
| Sharpe | 0.61 | 0.51 |
| max drawdown (daily) | 39.0% | 55.2% |
| growth multiple | ×7.88 | ×8.38 |
| worst calendar year | −18.91% (2022) | — |
| best / median year | +33.03% (2013) / +11.33% | — |

### Robustness appendix — other 3 a priori grid cells, same walk-forward

| config | years beat / 27 | hit % | CAGR | Sharpe | maxDD |
|---|---|---|---|---|---|
| N6/K3 | 11/27 | 40.7 | 8.22% | 0.59 | 33.9% |
| N6/K5 | 10/27 | 37.0 | 7.51% | 0.59 | 32.0% |
| N12/K3 | 13/27 | 48.1 | 8.20% | 0.58 | 44.6% |
| **N12/K5 (headline)** | **13/27** | **48.1** | **8.07%** | **0.61** | **39.0%** |

No cell beats SPY in more than 13 of 27 years; the front-loaded pattern is
identical across the grid.

### Verdict

The walk-forward is **harsher than the §12.3 conclusion, not softer**. §12.3
said "real, robust mechanism, killed on DSR alone." The year-by-year record a
real allocator actually reads says: **a strategy that beat SPY every year of
2000–2008 by parking in bonds through two bear markets, and has beaten it in
only 4 of the 18 years since — now trailing on cumulative growth.** It is a
**conditional crash hedge**, not a standalone alpha sleeve, and the condition
(a bear market the 200-day SMA calls in time) has essentially not paid since
the GFC. This does not "resurrect" the strategy — §12's KILL stands, and the
walk-forward strengthens the case for it.

### Staged real-capital plan (built anyway, per the task — and doubling as a falsification test)

The plan is written against the frozen N=12/K=5 config and the `live/`
pipeline from §12.4. Its premise is explicit: **the honest base case is "the
edge is a crash hedge that has not paid since 2009," and the staged deploy is
a way to find out within ~2 years whether the post-GFC drought is noise or
the real state of the strategy. If the pre-committed gates fail, the plan
worked.**

| stage | capital | min. duration | advance only if | halt / de-scale if |
|---|---|---|---|---|
| **0 — paper** (running, §12.4) | $0 | ≥3 rebalances **and** ≥6 months | weights match `build_weights()` to the share; realised cost ≤15 bps round-turn (2× the 6 bps assumption); no operational failure. Paper P&L is **not** a performance gate — 6 months is too short for a monthly strategy | any plumbing failure |
| **1 — minimum real** | $10,000 | 12 months (≥12 rebalances), no adds | live trailing Sharpe ≥ **0.35**; live 12-mo return not worse than **−19%** (worst backtest year); mean \|live − replay monthly return\| < 1.0 pp | drawdown-from-peak > 20%; **or** 2 consecutive monthly monitor runs with negative trailing Sharpe **and** CAGR >10 pp below SPY (already `live/monitor.py`'s rule); **or** operational failure |
| **2 — scaled** | $50,000 in 2 tranches ($30k, then +$20k after 6 clean months) | 18 months | full Stage 1+2 live Sharpe (≥30 mo) inside **[0.35, 0.85]** (0.61 backtest sits mid-band; landing **above** 0.85 is *also* a flag — treat as luck, don't accelerate); live cumulative ≥ same-cashflow SPY B&H, or within 5 pp with lower drawdown; **≥1 genuine risk-off period traded live** with the filter moving to IEF as designed (extend Stage 2 until one occurs — the filter *is* the edge) | as Stage 1 |
| **3 — full allocation** | target sleeve (e.g. $150–250k) in 3 monthly tranches | ongoing, quarterly review | — | live trailing Sharpe < 0.35 for 2 consecutive quarters → de-scale one full stage, re-observe 6 months; 20% drawdown → exit to cash, restart at Stage 1 |

**Band rationale:** 0.35 is ~1 annual-Sharpe-stdev below the *worst individual
walk-forward year's* Sharpe floor — i.e. "not outside what 27 years already
showed." "Live Sharpe" = trailing-since-inception daily Sharpe annualised
from monthly equity marks (`live/monitor.py` produces it).

**Ladder exit condition (not indefinite paper trading):** if by **42 months**
of live trading the strategy has not sustained a live Sharpe ≥ 0.35 **and**
has not beaten a same-cashflow SPY buy-and-hold on either return or
risk-adjusted return, **stop**. Given the §12.3/§12.5 prior ("small edge or
none, and nothing since 2009"), 42 months of real money is enough to
distinguish the two, and a clean stop is this plan's success condition, not
its failure.

Files: `run_momentum_rotation_walkforward.py`. Results:
`results/momentum_rotation_walkforward.csv` (year table),
`results/momentum_rotation_walkforward_configs.csv` (4-cell aggregate),
`results/momentum_rotation_walkforward_plan.txt`. Reproduce:
`python run_momentum_rotation_walkforward.py`.

**Not a new trial batch** — frozen config, re-slices the §12 simulation by
year, fits nothing. **Cumulative trial count unchanged: N=946.**


## 13. CRYPTO — the same 5-family sweep on a genuinely new instrument class, tested 2026-08-31, killed

### Why this run exists

Every price-pattern kill in sections 1-11 was tested on gold and index CFDs
only. Crypto is a structurally different instrument class: 24/7/365 trading
(no session structure to be session-agnostic ABOUT), and — the important
one — a fee-dominated cost structure rather than a spread-dominated one.
That second difference makes it a genuine, non-redundant test of the
cost-vs-stop-distance mechanism section 11 established, not just "the same
test on a different ticker."

### Why M15/H1/H4, not M1 — stated, as required

M1 is deliberately excluded. Section 11 found a clean, **instrument-agnostic**
mechanism: cost per trade is fixed while 1R (an ATR-scaled stop) shrinks with
the square root of bar duration, so cost_R blows out and kills every M1
config regardless of instrument (gold, two different index CFDs). That
mechanism is about stop distance vs. fixed cost, not about any one
instrument's tape — running M1 again here would re-confirm an already-
established structural conclusion, not test anything new. H1 is the anchor
(the mid-point of the M5-H4 ladder); M15 and H4 bracket it.

### The grid, every default stated, nothing tuned

| axis | setting | note |
|---|---|---|
| Instruments | BTCUSDT, ETHUSDT | Binance spot, via ccxt |
| Timeframes | M15, H1, H4 | native Binance candles, NOT resampled from an M1 archive |
| Families | trend, breakout, meanrev, momentum, macross | imported from `strategies/sweep_families.py`, UNCHANGED |
| Variants | 3 stated per family, unchanged | no parameter re-tuned for crypto |
| Window | 2018-01-01 to 2026-08-31 | matches this repo's standard "2018-2025" window |
| Risk | 1% / trade, `de_overlap` (one position at a time) | repo convention |
| Grid | 2 x 3 x 5 x 3 = **90 configs** | |

### Data — real Binance spot, verified, spread stated honestly

`scripts/download_crypto_ohlcv.py` pulled native OHLCV via ccxt's Binance
adapter, paginated, from 2018-01-01 through today. Both BTC/USDT and
ETH/USDT trade continuously since 2017-08-17 (verified via `since=0`).

| | M15 bars | H1 bars | H4 bars | gaps > 1.5x bar spacing |
|---|---|---|---|---|
| BTCUSDT | 303,218 | 75,816 | 18,969 | 27 (H1), a handful of documented exchange-outage windows (e.g. 2018-02-09), none exceeding ~1.5 days |
| ETHUSDT | 303,218 | 75,816 | 18,969 | 27 (H1), same dates |

**Spread — real, not fabricated, but honestly limited.** Free historical
per-bar bid/ask for crypto is not available via ccxt/Binance REST
(`fetchOHLCV` is trade-based, not quote-based) — the same limitation
section 12 documented for yfinance ETF data. What IS real: a live
top-of-book spread, measured fresh at pull time (BTCUSDT 0.0013 bps,
ETHUSDT 0.041 bps), applied as a constant historical assumption. This
matters little in practice: it is negligible next to the 20 bps taker-fee
assumption below, which is the real cost driver for crypto — the opposite
of every FX/index/ETF instrument in this project, where spread dominates
and commission is near-zero.

**Costs.** Binance spot taker fee, no BNB/VIP discount (the conservative
default a retail account actually pays): **10 bps per side, 20 bps
round-turn.** Plus 1 bps/side normal slippage, 2 bps/side in the repo's
existing `NEWS_HOURS_UTC` windows (reused unchanged as a conservative, not
crypto-specific, proxy for elevated-volatility periods).

### Out-of-regime — stated honestly: crypto cannot get the same treatment FX/indices did

STATE_OF_PLAY section 7 rule 3 calls for a genuine pre-sample holdout.
Binance BTC/USDT and ETH/USDT both begin 2017-08-17 — four months before
this project's 2018 baseline. There is no clean multi-year pre-2018 window
to hold out. **This run does not claim a genuine out-of-regime test for
crypto.** Instead, as the task explicitly allowed ("as far back as clean
data allows"), the single 2018-2025 window is split into two regimes
within itself (2018-21 vs 2022-25) by **re-slicing the same simulated
trades** — not a new simulation grid, so **not counted as new trials**
(same treatment section 11 gave its RTH-matched control) — and explicitly
weaker evidence than a true holdout.

### The result

| gate | result |
|---|---|
| look-ahead guard | **90/90 PASS** |
| gross PF > 1 | 62/90 (mean 1.021) |
| net PF > 1 | **12/90** |
| net Sharpe > 0 | **12/90** |
| DSR > 0.95 (structural pool = this batch's own 90 a priori cells) | **0/90** (best ~0, batch mean Sharpe -2.75) |
| OOS holds (2023-01-01 split) | 5/90 |
| regime split holds (2018-21 vs 22-25, informational only) | 5/90 |
| top year <= 60% of net R | 7/90 |
| beats buy-and-hold | 1/90 (ETHUSDT H4 breakout v1 only) |
| **SURVIVORS** | **0/90** |

**Cost gradient, confirming section 11's mechanism on a fourth/fifth
instrument with a completely different cost structure:**

| timeframe | mean cost_R (% of 1R) |
|---|---|
| M15 | 37.5% |
| H1 | 16.6% |
| H4 | 7.6% |

The same 1/sqrt(TF) shape section 11 established on spread-dominated FX/index
costs reappears on a fee-dominated crypto cost model. **maxDD reaches
99-100% on most M15/H1 cells — verified NOT an equity-curve artefact**:
0/90 cells have a single day losing >=100% of equity (`n_ruin_days`), so
these are genuine, valid catastrophic drawdowns from repeated fee-eaten
losses compounding, not a broken statistic (contrast section 11, where
maxDD WAS invalid at M1 for this reason).

Best cell: **ETHUSDT H4 breakout v1** — net Sharpe +0.56, net PF 1.209,
cost_R 7.0%, DSR 0.000, beats ETH buy-and-hold (Sharpe +0.56 vs +0.49).
BTCUSDT's best cell (H4 macross v1, Sharpe +0.48) loses to BTC buy-and-hold
(+0.53). Buy-and-hold itself is brutal here: BTC maxDD 81.2%, ETH maxDD
94.0%, over this window.

### Verdict

**KILL, 0/90 survivors.** The mechanism established structurally in
section 11 — fixed cost per trade against an ATR-scaled stop that shrinks
with the square root of bar duration — reproduces cleanly on crypto despite
a completely different cost regime (taker fee, not spread). This is not a
redundant re-test: it confirms the finding generalizes across the specific
economic source of the cost, not just across instruments that happen to
share Dukascopy-style spread data. **Extends the "no price-pattern edge"
conclusion to a fourth/fifth instrument class.**

Files: `scripts/download_crypto_ohlcv.py`, `run_sweep_crypto.py`. Data:
`data/BTCUSDT_*_2018_2025_binance.csv`, `data/ETHUSDT_*_2018_2025_binance.csv`,
`data/crypto_ohlcv_report.csv`. Results: `results/sweep_crypto.csv`,
`sweep_crypto_scored.csv`. Reproduce:
`python scripts/download_crypto_ohlcv.py && python run_sweep_crypto.py`.

**Cumulative trials: N=728** (638 prior + 90 crypto).

> ⚠️ **2026-08-31, follow-up session — ANNUALISATION FACTOR CORRECTION,
> flagged not re-run.** Crypto trades every calendar day, so the daily
> return series above has a real observation on all 365 days/year, not 252
> trading days/year like every FX/index/equity series in this repo. This
> section used the repo-wide default `BARS_PER_YEAR=252` on that
> 365-observation series, which UNDERSTATES the correct annualisation
> factor by sqrt(252/365)=0.831x — true Sharpe magnitude throughout this
> section is ~1.204x larger, same sign, than reported above. **This does
> not flip the verdict**: best crypto DSR was ~0 (best cell Sharpe +0.56,
> corrected ~+0.67), nowhere near the 0.95 bar either way, and every
> SURVIVOR gate besides raw Sharpe sign is unaffected by a constant
> rescaling — still 0/90 survivors. Found while building section 15
> (`research/regime_switch.py`, which uses the correct 365 factor
> throughout); the 90-cell grid above is NOT re-run (out of scope, verdict
> unaffected) — flagged here rather than silently carried forward.

---

## 14. INDIVIDUAL US STOCKS — the same 5-family sweep, tested 2026-08-31, killed — but the most durable gross edge in the project

### Why this run exists

Every price-pattern kill in this project was tested on gold and index CFDs.
Individual equities are a structurally different instrument class:
idiosyncratic single-name risk, earnings gaps, no 24-hour session, and (for
this small 6-name test) no survivorship concern since all 6 are chosen for
liquidity/diversity, still trading today, not picked with hindsight of
which looked good in a backtest.

### Universe and why daily bars, stated as a limitation not worked around

6 large-cap, diverse-sector S&P 500 names: **AAPL** (Technology), **JPM**
(Financials), **XOM** (Energy), **JNJ** (Health Care), **WMT** (Consumer
Staples), **CAT** (Industrials).

yfinance intraday history was checked empirically before choosing a
resolution: **60-minute bars covers about 1 year of history, 15-minute bars
about 60 days.** Neither is remotely enough for this repo's standing
8-year-in-regime + multi-year-holdout convention (section 7 rule 3). Per
the task's explicit fallback, **daily bars are used instead** — a real,
stated limitation. The 5-family grid's parameters (all expressed in bars)
rescale to trading days instead of minutes/hours, the same honest rescaling
section 11 did in the opposite direction (ATR 14 -> 14 trading days, EMA
200 -> 200 trading days ~10 months, max hold H -> 12-96 trading days ~2-19
weeks).

### The grid and costs

| axis | setting |
|---|---|
| Instruments | AAPL, JPM, XOM, JNJ, WMT, CAT |
| Timeframe | D1 only (yfinance daily, `auto_adjust=True`) |
| Families/variants | imported UNCHANGED from `strategies/sweep_families.py` |
| Windows | in regime 2018-01-01 to 2025-12 (OOS split 2023-01-01); out of regime 2010-01-01 to 2017-12-31 (OOS split 2016-01-01) — a GENUINE multi-year holdout, unlike crypto, since all 6 tickers have clean daily data back to 2010 |
| Costs | 2 bps stated round-turn spread (conservative for these 6 liquid names) + 1 bps commission + 0.5-1.5 bps slippage |
| Grid | 6 x 1 x 5 x 3 = **90 configs per window** |

`run_sweep_stocks_pre2018.py` holds no strategy/cost/scoring code — it
rebinds names on `run_sweep_stocks` and calls its `main()`, same pattern as
`run_sweep_m1_pre2018.py`.

### The result — in regime (2018-2025)

| gate | result |
|---|---|
| look-ahead guard | **90/90 PASS** |
| gross PF > 1 | 58/90 |
| net PF > 1 | 55/90 |
| net Sharpe > 0 | 55/90 |
| DSR > 0.95 | **0/90** (best 0.45, CAT breakout v1) |
| OOS holds | 25/90 |
| top year <= 60% of net R | 18/90 |
| beats buy-and-hold | 3/90 (WMT macross v0, CAT breakout v1, CAT momentum v1) |
| **SURVIVORS** | **0/90** |

Best raw net Sharpe: CAT breakout v1, +0.97 (gross PF 2.19, net PF 2.15,
cost_R 1.2%, DSR 0.45, OOS holds YES). AAPL's best config (SR +0.73) loses
to AAPL buy-and-hold (SR +0.94) despite being a genuinely strong trading
system — AAPL simply compounded harder than any of these 15 mechanical
configs traded it.

### The result — out of regime (2010-2017), and the persistence finding

| gate | result |
|---|---|
| gross PF > 1 | 58/90 (mean PF **rose** 1.142 -> 1.201) |
| net PF > 1 | 55/90 (unchanged count) |
| mean net Sharpe | +0.074 -> **+0.082** (rose) |
| DSR > 0.95 | **0/90** (best 0.19) |
| beats buy-and-hold | 7/90 |
| **SURVIVORS** | **0/90** |

**43/90 cells are gross-positive in BOTH windows; 38/90 are net-profitable
in BOTH windows.** This is the strongest cross-regime persistence of ANY
candidate this project has tested — compare the index basket's 2/18, ORB's
2/12, the M1 row's 3/30; only the Sneaky Pivot's 14/16 (on a much smaller
16-cell grid) comes close. Mean gross PF did not merely survive the
holdout, it improved.

**Family ordering, and a genuine structural contrast with section 11:**

| family | mean gross PF (in regime) | mean Sharpe (in regime) |
|---|---|---|
| breakout | 1.303 | +0.336 |
| macross | 1.271 | +0.123 |
| momentum | 1.167 | +0.128 |
| trend | 1.131 | +0.094 |
| meanrev | **0.838** | **-0.311** |

Mean-reversion is the WORST family here, the only one with negative mean
Sharpe — individual large-cap stocks trend on daily bars more than they
mean-revert. This is the **opposite** finding from section 11's M1 row,
where meanrev was the single best family (8/9 gross-positive cells) and
breakout was the single worst (0/9). Same families, same code, opposite
ranking at a different timeframe on a different instrument class — a real
structural fact about market microstructure at these two scales, not a
contradiction in the harness.

### Verdict

**KILL, 0/90 + 0/90 survivors in both windows — but this is the most
durable gross edge this project has found on any price-pattern family.**
It survives a genuine 8-year holdout not just intact but slightly stronger.
It is still not tradeable, because two gates bind independently of cost or
regime: **DSR never approaches 0.95 in either window** (the grid is too
flat/noisy relative to its own 90-cell pool for any single config to be a
statistical outlier), and **most cells lose to buy-and-hold** (AAPL, JPM,
JNJ and WMT all compounded harder over these windows than any of the 15
mechanical systems traded them; CAT and XOM are the exceptions). Extends
the "no exploitable price-pattern edge" conclusion to a fourth instrument
class, on the strongest evidence this project has produced for any
single-name or basket price-pattern family.

Files: `scripts/download_us_stocks.py`, `run_sweep_stocks.py`,
`run_sweep_stocks_pre2018.py`. Data:
`data/{AAPL,JPM,XOM,JNJ,WMT,CAT}_D1_2010_2025_yfinance.csv`,
`data/us_stocks_report.csv`. Results: `results/sweep_stocks.csv`,
`sweep_stocks_scored.csv`, `sweep_stocks_pre2018.csv`,
`sweep_stocks_pre2018_scored.csv`. Reproduce:
`python scripts/download_us_stocks.py && python run_sweep_stocks.py && python run_sweep_stocks_pre2018.py`.

**Cumulative trials: N=908** (728 prior + 90 in regime + 90 out of regime).

## 15. REGIME-ADAPTIVE STRATEGY SELECTION (BTC/ETH) — safeguards worked as designed, killed for a NEW reason, tested 2026-08-31

### Why this run exists

Every family/instrument in this project has been tested as a single static
system. This asks a different question: can SWITCHING between the same 5
families over time, using only trailing performance and with anti-whipsaw
safeguards **designed in from the start**, beat both doing nothing
(buy-and-hold) and picking one thing and sticking with it (the best static
config from section 13)?

### The design, every safeguard stated and how it was implemented

| safeguard | implementation |
|---|---|
| Rank by trailing Sharpe, not raw return | `trailing_sharpe()` on each family's own daily net-return series, causal (`index < as_of` only) |
| Hysteresis | challenger must exceed the incumbent's trailing Sharpe by **> 0.30** before a family-to-family switch is taken |
| Minimum hold | decision dates are spaced **exactly one lookback window apart** (3mo or 6mo) — a switch cannot physically happen more often than once per window; this is structural, not a post-hoc check |
| Circuit breaker | if the best candidate's trailing Sharpe is **< 0.0**, go to CASH instead of the least-bad loser |
| Switching cost | 20bps (one Binance taker round-turn), charged only on an actual switch, kept separate from each family's own internal per-trade cost |

Candidates: the same 5 families (`strategies/sweep_families.py`), variant v0
of each (the first stated variant, same index for every family/instrument,
chosen a priori, never cherry-picked), on **H4** — section 13's lowest-cost
crypto timeframe (mean cost_R 7.6%), the only realistic base for a real
switching system. Instruments: BTCUSDT, ETHUSDT. Lookbacks tested: 3 and 6
months. Grid: 2 x 2 = **4 configs**.

### A genuine correction to section 13, found and fixed here

Crypto trades every calendar day, so the daily return series built for each
family has a real observation on all 365 days/year, not 252 trading
days/year like every FX/index/equity series in this repo. Section 13 used
the repo-wide default `BARS_PER_YEAR=252` on that 365-observation series,
which **understates** the correct annualisation factor — true Sharpe
magnitude there is ~1.204x larger (sqrt(365/252)), same sign. **This does
not flip section 13's verdict**: its best crypto DSR was ~0 (best cell
Sharpe +0.56, corrected ~+0.67), nowhere near the 0.95 bar either way, and
every other SURVIVOR gate is unaffected by a constant rescaling. This
module uses the correct factor (365) throughout; section 13's 90-cell grid
is flagged here rather than silently re-used, not re-run (out of this
session's scope, verdict unaffected).

### Causality — verified explicitly, not asserted

`research/regime_switch.py::verify_causality()` independently re-derives
every decision date's trailing Sharpe from the raw family return series and
confirms (a) it matches the value the switching loop actually used, and
(b) the window it was computed from contains no date on or after the
decision date. **4/4 configs PASS.**

### The result

| inst | lookback | Sharpe(365) | DSR | net PF | maxDD | total ret | switches/decisions | switches/yr | time in cash | regime split holds |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 3mo | -0.60 | 0.09 | 0.835 | 49.1% | -42.0% | 22/34 | 2.54 | 2.8% | no |
| BTCUSDT | 6mo | -0.63 | 0.07 | 0.830 | 47.3% | -43.1% | 13/17 | 1.50 | 5.7% | no |
| ETHUSDT | 3mo | -0.26 | 0.35 | 0.923 | 37.4% | -22.1% | 27/34 | 3.12 | 10.5% | no |
| ETHUSDT | 6mo | -0.11 | 0.52 | 0.968 | 35.9% | -12.8% | 14/17 | 1.62 | 17.3% | no |

**All 4 configs lose to both benchmarks:**

| instrument | adaptive best | buy-and-hold | best static H4 (section 13) |
|---|---|---|---|
| BTCUSDT | SR -0.60 (3mo) | SR +0.64 | macross v1, SR +0.48 |
| ETHUSDT | SR -0.11 (6mo) | SR +0.58 | breakout v1, SR +0.56 |

**SURVIVORS: 0/4.** DSR does not clear 0.95 (best 0.52), the internal
regime split (2018-21 vs 2022-25, informational — no genuine pre-2018
crypto holdout exists, same limitation as section 13) does not hold in any
of the 4 configs, and the adaptive approach beats neither benchmark on
either instrument at either lookback.

### Did the safeguards work as designed? YES, mechanically — switching frequency was NOT low, and here is exactly why

The task's own prediction was that switching frequency should come out LOW
given the safeguards. It did not: **22/34 (65%) and 13/17 (76%) of decision
points resulted in a switch for BTCUSDT; 27/34 (79%) and 14/17 (82%) for
ETHUSDT** — 1.5 to 3.1 switches per year. This was measured, not assumed,
and it is worth explaining precisely rather than just reporting the number.

**The minimum-hold safeguard worked exactly as designed** — a switch
literally cannot occur more often than once per lookback window, by
construction of the decision-date spacing, and `verify_causality()`
confirms no decision ever used a future return. **The hysteresis safeguard
also worked exactly as designed** — it correctly blocked every switch where
the challenger's edge over the incumbent was ≤0.30 (median gap on a HOLD
decision: 0.34; median gap when a switch actually fired: 0.80-0.91, well
clear of the threshold — the gate itself is not leaking).

**What failed is the ASSUMPTION that "differences of ≥0.3 trailing Sharpe
are meaningful, not noise" on this data.** Measured directly: the median
gap between the best and second-best of the 5 families' trailing Sharpe, at
ANY decision point, is **0.67** — more than double the hysteresis margin.
Individual family trailing Sharpes routinely swing by 2-5 points from one
quarter to the next (e.g. BTCUSDT momentum: +2.19 -> +1.82 -> +0.76 ->
+1.31 -> -1.04 across five consecutive quarters in 2018-19). At the scale
of a single family's daily-return series over a 3-6 month window on a
noisy, high-volatility instrument, the SAMPLING NOISE of the trailing-
Sharpe estimator is simply larger than any hysteresis margin that would
still leave the system able to switch at all. A 0.3 margin was chosen as
"a real gap, not a coin-flip margin" in the abstract, and it IS — the
problem is that on this specific signal, real (non-noise) week-to-week
regime persistence turns out to be weaker than the ESTIMATION noise of a
5-way trailing-Sharpe horse race, so the hysteresis filter has almost
nothing low-signal to filter out: nearly every quarter genuinely does
present a large, non-marginal gap between the top candidate and whatever
is currently held, but that gap mostly reflects estimator noise, not
persistent skill.

**This is a genuinely NEW failure mode, not a repeat of whipsaw or
late-chasing** (both of which were the two mechanisms this design was built
specifically to prevent, and did prevent — see above). The mechanism here
is: **trailing Sharpe over 3-6 months, computed on 5 already-marginal
strategies applied to a volatile instrument, is not a stable enough signal
for even a real (non-coin-flip) hysteresis margin to produce low turnover.**
The fix implied is not a bigger margin (an even larger hysteresis would
just push the system further toward "always hold cash or the first pick,"
which is a different design, not a validation of this one) — it is that
none of the five candidate families has enough of an underlying edge (per
section 13, none is close to a real DSR-significant edge) for a
performance-chasing selector, however well-guarded, to have real signal to
rotate on. Circuit breaker time-in-cash (2.8-17.3%) stayed low precisely
because family trailing Sharpes cross zero individually often enough that
SOME family usually looks positive even when none of them has a real edge
— which is itself consistent with section 13's finding that these are five
marginal, noisy systems, not the expected behaviour of a genuinely working
regime detector.

### Verdict

**KILL, 0/4 survivors — for a new, precisely quantified reason: the
switching signal (trailing Sharpe of five already-marginal crypto systems)
is too noisy for a real, non-coin-flip hysteresis margin to produce low
turnover, not because the safeguards leaked.** Both mechanically-verified
mechanisms (minimum hold, hysteresis threshold) performed exactly as
specified. The adaptive approach loses to both buy-and-hold and the single
best static config on both instruments at both lookbacks tested.

Files: `research/regime_switch.py` (engine), `run_regime_switch.py`
(driver). Results: `results/regime_switch.csv` (per-config metrics),
`results/regime_switch_decisions.csv` (every decision, every family's
trailing Sharpe, every action — the full audit trail). Reproduce:
`python run_regime_switch.py`.

**Cumulative trials: N=912** (908 prior + 4 regime-switch cells).

## 16. REGIME-SWITCH FOLLOW-UP — longer lookbacks (still no relief) and a seasonality test (clean negative), tested 2026-08-31

Two extensions of section 15, requested as a genuinely separate question
each: does a longer trailing-Sharpe lookback fix the switching-frequency
problem (Part A), and does a completely different selection mechanism —
calendar seasonality instead of recent performance — find any real signal
(Part B)? `research/regime_switch.py`'s engine (hysteresis 0.30, circuit
breaker floor 0.0, switch cost 20bps, minimum hold structural) is reused
byte-for-byte unchanged in Part A; Part B is a genuinely different
mechanism and is tested on its own terms, not forced through the same
switching engine.

### PART A — longer lookbacks (12mo, 24mo), does switching frequency drop?

**Prediction being tested**: if section 15's high switching frequency
(65-82% of decisions) was purely a small-sample noise artefact of 3-6
month trailing-Sharpe windows, lengthening the window should push it down
toward something sane (the task's own bar: <20%).

| lookback | switching frequency (pooled, 2 instruments) | decisions (total) |
|---|---|---|
| 3mo | 72.1% | 68 |
| 6mo | 79.4% | 34 |
| 12mo | **62.5%** | 16 |
| 24mo | 87.5% | 8 |

**It did not drop toward sane.** 12-month lookback is the best of the four
(62.5%), still more than 3x the task's own "sane" bar of 20%. 24-month
lookback — caveat: only 8 total decisions across both instruments, so this
number is itself noisy (one flip moves it 12.5 points) — came back UP to
87.5%, the highest of any lookback tested. There is no monotonic
improvement with window length in this data.

**Full comparison table, all 4 lookbacks:**

| inst | LB | Sharpe(365) | DSR | net PF | maxDD | total ret | switches/decisions | switch% | time in cash | regime holds |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 3mo | -0.60 | 0.09 | 0.835 | 49.1% | -42.0% | 22/34 | 64.7% | 2.8% | no |
| BTCUSDT | 6mo | -0.63 | 0.07 | 0.830 | 47.3% | -43.1% | 13/17 | 76.5% | 5.7% | no |
| BTCUSDT | 12mo | -0.37 | 0.25 | 0.866 | 26.2% | -23.5% | 5/8 | 62.5% | 23.1% | no |
| BTCUSDT | 24mo | -0.19 | 0.43 | 0.911 | 26.2% | -11.5% | 3/4 | 75.0% | 46.2% | no |
| ETHUSDT | 3mo | -0.26 | 0.35 | 0.923 | 37.4% | -22.1% | 27/34 | 79.4% | 10.5% | no |
| ETHUSDT | 6mo | -0.11 | 0.52 | 0.968 | 35.9% | -12.8% | 14/17 | 82.4% | 17.3% | no |
| ETHUSDT | 12mo | -0.12 | 0.51 | 0.963 | 27.3% | -12.7% | 5/8 | 62.5% | 19.2% | no |
| ETHUSDT | 24mo | -0.35 | 0.27 | 0.895 | 40.2% | -26.5% | 4/4 | 100.0% | 30.7% | no |

**All 8 cells still lose to buy-and-hold AND to the best static section-13
config, on both instruments, at every lookback tested.** Best per instrument:
BTCUSDT SR -0.19 (24mo) vs B&H +0.64 vs best static +0.48; ETHUSDT SR -0.11
(6mo) vs B&H +0.58 vs best static +0.56. DSR does drift up somewhat with
longer lookback (0.07-0.09 at 3-6mo -> 0.25-0.52 at 12-24mo) simply because
fewer, chunkier decisions reduce estimation noise in the DSR calculation
itself — but no cell approaches 0.95, and Sharpe stays negative throughout.
No regime split (2018-21 vs 2022-25) holds at any lookback.

**Reading: longer lookbacks reduce absolute switch COUNT (fewer decision
points exist per year by construction) but do not reduce the underlying
PROBLEM identified in section 15** — the gap between the best and
second-best family's trailing Sharpe remains large relative to the 0.30
hysteresis margin at every window length tested, because family-level
performance genuinely does not persist reliably from one evaluation period
to the next on this data, regardless of how that period is sized. This
confirms, rather than merely repeats, section 15's finding: the noise is
not a 3-6 month artefact.

**New trials this batch: 4** (2 instruments x {12mo, 24mo}). Files:
`run_regime_switch_longlb.py`. Results: `results/regime_switch_longlb.csv`,
`results/regime_switch_longlb_decisions.csv`,
`results/regime_switch_all_lookbacks.csv` (all 4 lookbacks combined).
Reproduce: `python run_regime_switch_longlb.py`.

### PART B — seasonality: a genuinely different mechanism, tested properly, clean negative

**Method, stated before any result was read** (`scripts/test_seasonality.py`):
for each (instrument, family) — the SAME 5 families, variant v0, UNCHANGED
— each daily H4 net-return series is aggregated into one number per
(calendar year, calendar quarter): the sum of daily returns in that
quarter, restricted to COMPLETE quarters only (2026 Q3 excluded — the data
ends 2026-08-31, partway through Jul-Sep). A Kruskal-Wallis test (chosen
because per-quarter sums are not assumed Gaussian) is run per
(instrument, family) across the 4 quarter groups (~8-9 year-observations
each): H0 = the calendar quarter makes no difference to that family's
return distribution. **5 families x 2 instruments = 10 independent tests,
Bonferroni-corrected: alpha = 0.05/10 = 0.005**, decided before any
p-value was read.

| result | value |
|---|---|
| tests run | 10 (5 families x BTCUSDT/ETHUSDT) |
| pairs clearing Bonferroni threshold (p < 0.005) | **0/10** |
| pairs clearing even the UNCORRECTED alpha=0.05 | **0/10** |
| smallest raw p-value observed | **0.258** (BTCUSDT macross) — not close to either bar |
| largest KW statistic | 4.032 (BTCUSDT macross) |

**CONCLUSION: no statistically real seasonal pattern exists in this test —
a clean negative, not a near-miss dressed up as a finding.** Per the task's
explicit instruction, no seasonal selection rule was built or backtested:
picking the smallest-p-value cell (BTCUSDT macross, p=0.258) and
backtesting it anyway would be exactly the "eyeball a table and pick the
best-looking cell" failure mode this test exists to prevent, and at p=0.258
there is nothing there to pick even informally — a quarter effect this
weak is indistinguishable from chance with ~8-9 years of data per group.

**This is still a real, disclosed part of the project's search space, even
though it produced no backtest.** 10 genuine a priori statistical
hypotheses were tested. Because none produced a Sharpe-bearing backtested
configuration, **these 10 tests are NOT added to the Sharpe/DSR trial
pool** (DSR requires an actual Sharpe value; forcing an entry for a pure
hypothesis test with none would corrupt, not honestly extend, that pool) —
but they ARE disclosed here as a separately-tracked multiple-comparisons
budget, exactly the same principle this project applies to every other
batch: state the search that was actually done, not just the one config
that would look best if reported alone.

Files: `scripts/test_seasonality.py`. Results: `results/seasonality_test.csv`
(all 10 KW tests), `results/seasonality_quarter_means.csv` (the per-quarter
means the tests were run on, for anyone who wants to verify the negative
result by eye). Reproduce: `python scripts/test_seasonality.py`.

### Combined verdict

**Both parts KILL. Neither failure mode is new-new relative to what
sections 13/15 already established, but each closes a real, previously-open
question honestly:**
- Part A: a longer lookback does not rescue safeguarded switching —
  confirms section 15's diagnosis holds across the whole reasonable
  lookback range (3-24 months), not just the two originally tested.
- Part B: seasonality is a genuinely different, independently-tested
  hypothesis, and it is cleanly negative — the five families do not have
  detectable calendar-quarter structure on this crypto data, at any
  reasonable significance bar.

**Cumulative trials: N=916** (912 prior + 4 lookback-expansion cells; the
10 seasonality hypothesis tests are disclosed above but not added to the
Sharpe/DSR trial count, since none produced a backtested Sharpe).

## 17. MOMENTUM ROTATION — DOES THE MECHANISM GENERALIZE TO NEW UNIVERSES? Tested 2026-08-31, killed on both, differently

### Why this run exists

Sections 12/12.1-12.4 established that the audited momentum-rotation
mechanism (trailing N-month return ranking + a causal long-SMA market
filter) beats SPY on a risk-adjusted basis on the original 17-ETF US-sector
universe, survives two independent audits, and is robust to filter/cost
perturbation — but never clears DSR against even its own 4-cell pool, and
was never tested on any universe besides US sector/asset-class ETFs. This
asks the obvious next question: is the MECHANISM general, or is it a
property of that one universe?

### A necessary, additive change to `research/momentum_rotation.py` — verified non-breaking

`build_weights()` hardcoded `BENCHMARK="SPY"` and `DEFENSIVE="IEF"` as
module constants, which cannot work for a universe with no SPY column
(crypto) or where SPY is itself a ranked competitor (country ETFs, per this
task's own design). Two optional parameters, `benchmark` and `defensive`,
were added — same additive convention already used twice before in this
file (`sma_window`, `rebalance_step`, section 12.3) — defaulting to the
original constants, so every existing call site is unaffected. **Verified,
not assumed**: `build_weights(adjclose, 6, 3)` and `build_weights(adjclose,
12, 5)` on the original 17-ETF panel reproduce first-execution dates
1999-07-01 and 2000-01-03 exactly, matching section 12.1's audited values,
before any new-universe result was trusted. The ranking logic, the causal
filter logic, the execution lag, and `simulate()`'s cost model are all
**byte-for-byte unchanged**.

### Grid and methodology — identical to the audited (corrected) original

N in {6, 12} months, K in {3, 5} holdings — same 4-cell grid per universe.
Same causal execution lag (unchanged code). Metrics computed on each
config's own live window from the start (the section-12.1 correction is
built in from the beginning here, not repeated as a bug and then fixed).
Look-ahead guard reused unchanged (`look_ahead_guard()`): **8/8 PASS.**

### Universe A — crypto sectors

11 ranked instruments across 6 categories (real Binance spot, verified
inception dates): **ETH, SOL, BNB, ADA, AVAX** (L1 smart-contract
platforms), **UNI, AAVE** (DeFi), **LINK** (oracle/infrastructure),
**SAND, MANA** (gaming/metaverse), **DOGE** (meme-coin). Benchmark/filter
basis: **BTC** (excluded from ranking — crypto's own SPY-equivalent "is the
market risk-on" gauge). Defensive leg: **CASH_USD**, a synthetic
constant-price (0% return, no yield) column — no crypto equivalent of IEF
exists; stated as a conservative simplification (real stablecoin holdings
typically earn some yield, so this understates the true defensive return —
the safe direction to be wrong). Costs: **12 bps/side (24 bps round-turn)**
— Binance spot taker fee (10bps) + a 2bps slippage cushion, reflecting
section 13's finding that crypto cost is fee-dominated, not
spread-dominated; a genuinely different, honestly-derived cost input from
the ETF study's 3bps/side, not a copy-paste.

| N | K | first live exec | Sharpe | DSR | CAGR | maxDD | top-year share | beats BTC bench | beats equal-wt basket |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 2018-06-01 | +0.695 | 0.22 | 25.9% | 65.8% | **74%** | YES | YES |
| 6 | 5 | 2019-08-01 | +0.812 | 0.36 | 37.4% | 65.7% | **92%** | YES | YES |
| 12 | 3 | 2018-12-01 | +0.764 | 0.31 | 30.1% | 66.5% | **78%** | no | no |
| 12 | 5 | 2020-02-01 | +0.944 | 0.54 | 48.0% | 57.0% | **77%** | YES | YES |

**Gate tally: guard 4/4, Sharpe>0 4/4, DSR>0.95 0/4, not concentrated 0/4,
beats bench 3/4, beats basket 3/4 — SURVIVORS 0/4.**

**Stress window: 2022-01-01 → 2022-12-31 (LUNA collapse May 2022, FTX
collapse Nov 2022)** — crypto's own severe stress period; crypto data does
not reach back to a decade-scale holdout the way the original 2000-2009
test did, stated honestly rather than faked. Result, and precisely what it
means: the strategy posts Sharpe +0.76 to +0.78 and near-zero maxDD (0.2%)
in this window, decisively beating both BTC buy-and-hold (Sharpe **-1.07**)
and the equal-weight basket (**-0.61 to -0.74**) — **but this is because
the BTC-based 200-day SMA filter flags risk-off almost immediately and the
strategy sits in CASH_USD for effectively the entire year** (verified
directly: 363 of 365 days in the window carry exactly zero net return,
across every N/K config, since the filter is N/K-independent). This is a
real, correctly-computed, mechanistically coherent result — the defensive
filter does exactly its job — but it is a "the filter went to cash and 0%
beat a crash" result, not "the ranking picked resilient crypto sectors
during the stress period." Worth stating precisely rather than reporting
the flattering Sharpe number without its mechanism.

**What actually kills it: single-year concentration, badly.** Top calendar
year carries 74-92% of total log-return across all 4 configs — none comes
close to the 60% bar every other candidate in this project is held to, and
by a wide margin. This is the SAME failure signature that killed the index
trend basket (section 6), Sneaky Pivot (section 9), and ORB (section 10) —
a real gross/risk-adjusted edge that is not a best-of-N artefact (it beats
its own benchmarks in 3/4 configs) but is concentrated in one dominant
period (almost certainly the 2020-2021 bull run) rather than being a
repeatable, diversified source of return.

### Universe B — country/region equity ETFs

10 ranked instruments: **EWJ** (Japan), **EWG** (Germany), **EWU** (UK),
**EWZ** (Brazil), **INDA** (India), **FXI** (China), **EFA** (developed
ex-US, broad), **EEM** (emerging markets, broad), **SPY** (United States —
explicitly a ranked competitor here, per the task's instruction, unlike
the original study where it was the excluded benchmark), **IEF**
(defensive leg, the SAME instrument the original study used, reused
unchanged). New benchmark/filter basis: **ACWI** (MSCI All-Country World
Index, global, excluded from ranking — SPY could no longer play this role
since it is now a ranked competitor). Costs: same 3bps/side as the
original study — same instrument class, no reason to re-derive.

| N | K | first live exec | Sharpe | DSR | CAGR | maxDD | top-year share | beats ACWI bench | beats equal-wt basket |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 3 | 2009-02-02 | +0.354 | 0.39 | 4.40% | 29.7% | 29% | no | no |
| 6 | 5 | 2009-02-02 | +0.425 | 0.51 | 5.26% | 26.4% | 26% | no | no |
| 12 | 3 | 2009-02-02 | +0.312 | 0.33 | 3.63% | 25.4% | 32% | no | no |
| 12 | 5 | 2009-02-02 | +0.385 | 0.44 | 4.54% | 24.8% | 30% | no | no |

**Gate tally: guard 4/4, Sharpe>0 4/4, DSR>0.95 0/4, not concentrated 4/4,
beats bench 0/4, beats basket 0/4 — SURVIVORS 0/4.**

All 4 configs start live on the same date (2009-02-02) because ACWI's
2008-03-28 inception plus the 200-day SMA warmup sets a single binding
constraint regardless of N/K — a genuine data-depth artefact of choosing a
2008-launched global benchmark, stated not hidden.

**Stress window: 2008-01-01 → 2012-12-31 (GFC + Eurozone debt crisis)** —
the earliest stress period available, constrained by ACWI's 2008-03-28
inception (a real limitation: this cannot reach back to the original
study's full 2000-2009 window because its NEW benchmark didn't exist for
most of it). Unlike crypto, the strategy stays genuinely invested through
this window (mean stress Sharpe +0.04 to +0.15, weakly positive, not a
cash-parking artefact) but **loses to both ACWI (Sharpe +0.775) and the
equal-weight basket (+0.713) in every cell** — the opposite failure mode
from crypto: here concentration is NOT the problem (best-in-project-class
26-32% top-year share, comfortably under the 60% bar), but the risk-adjusted
return itself is simply mediocre — not badly wrong, just consistently
behind both of the things it needs to beat.

### Full comparison — original US-sector ETFs vs the two new universes

| metric (best cell) | original US-sector ETFs (§12.1) | crypto sectors | country ETFs |
|---|---|---|---|
| Sharpe (best cell) | 0.608 (N12K5) | 0.944 (N12K5) | 0.425 (N6K5) |
| DSR (best cell) | 0.505 | 0.54 | 0.51 |
| beats own benchmark (Sharpe) | **4/4** | 3/4 | **0/4** |
| beats equal-weight basket | n/a (not tested in §12) | 3/4 | **0/4** |
| top-year concentration | **4/4 PASS** (12.4-13.8%) | **0/4 PASS** (74-92%) | **4/4 PASS** (26-32%) |
| stress-window behavior | filter avoids two crashes while STAYING partly invested; beats SPY 4/4 | filter goes ~100% cash for the whole stress year; "beats" BTC by not participating, not by better picks | stays invested; weakly positive but loses to both benchmarks |
| DSR > 0.95 | 0/4 | 0/4 | 0/4 |
| **SURVIVORS** | 0/4 | **0/4** | **0/4** |

### Verdict

**KILL on both new universes — but for two DIFFERENT, informative reasons,
neither of which is simply "the original US-sector result, restated."**

- **Crypto sectors**: the mechanism produces a real, benchmark-beating
  gross/risk-adjusted edge (3/4 cells beat both BTC and the equal-weight
  basket) — but it is catastrophically single-year concentrated (74-92%,
  worse than every other candidate this project has tested, including the
  ones killed specifically for concentration). It also does not clear DSR.
  The stress-window "win" is a cash-parking artefact of the defensive
  filter, not evidence the ranking works well in a crypto crash.
- **Country ETFs**: concentration is genuinely NOT a problem (the best
  result in this project's history on that specific gate), and the
  strategy stays meaningfully invested through its own stress window — but
  the risk-adjusted return is simply not good enough: it loses to buy-and-
  hold ACWI and to an equal-weight country basket in every single cell,
  both in the full period and the stress window. DSR does not clear
  either.

**Neither universe validates the mechanism as general.** The original
US-sector result's specific combination — a real edge that beats its
benchmark on Sharpe AND is not concentrated AND (per section 12.1) beats
SPY's CAGR on a vol-matched basis — does not reproduce on either new
cross-section tested here. This narrows, rather than broadens, what can
honestly be claimed for the mechanism: it worked, imperfectly (DSR-
insignificant even there), on the ONE universe it was originally built and
audited on, and neither of two structurally different cross-sections
(crypto sectors, global equity regions) reproduces that same combination
of strengths.

Files: `research/momentum_rotation.py` (additive `benchmark`/`defensive`
params, verified non-breaking), `scripts/download_crypto_momentum_universe.py`,
`scripts/download_momentum_countries.py`,
`run_momentum_rotation_generalization.py`. Data:
`data/momentum_crypto_adjclose.csv`, `data/momentum_crypto_report.csv`,
`data/momentum_countries_adjclose.csv`, `data/momentum_countries_report.csv`.
Results: `results/momentum_rotation_generalization.csv`. Reproduce:
`python scripts/download_crypto_momentum_universe.py && python scripts/download_momentum_countries.py && python run_momentum_rotation_generalization.py`.

**Cumulative trials: N=924** (916 prior + 8 generalization cells: 4 crypto
+ 4 country-ETF configs).

## 18. POSITIONING-EXTREME CONTRARIAN REVERSAL — funding rate + open interest, BTC/ETH, tested 2026-08-31, killed cleanly

### Why this run exists

Every candidate tested so far in this project — sections 1-11 (price-pattern
families on gold/indices), section 13 (the same families on crypto),
section 17 (momentum rotation on new universes) — trades PRICE SHAPE: some
function of past OHLC. This tests a genuinely different information
category: a bet on OTHER TRADERS' POSITIONING. Mechanism, stated in one
sentence (also in `strategies/positioning_reversal.py`'s docstring): when
funding rate sits at an extreme percentile of its own trailing distribution
AND open interest is elevated (many traders crowded onto the side paying
that extreme funding), the crowd is prone to a forced unwind/squeeze as the
extreme resolves — this trades a documented phenomenon (crowded-positioning
squeezes / funding-rate mean reversion), not an arbitrary rule.

### Data — reused, not re-derived, from the prior checkpointed probe

`notes/crypto_data_availability.md` (probed 2026-08-22) already established
the binding constraint, reused here verbatim: **Binance's own open-interest
history is ~30-day retention only** (verified: any `startTime` before
~2026-07-25 returns HTTP 400 `-1130`) — unusable for a multi-year study.
Open interest comes from **Bybit v5** instead (funding rate stays on
Binance, which has full history). This cross-venue split (funding=Binance,
OI=Bybit) is stated, not hidden, per repo convention (data venue != execution
venue). Fresh pull (`scripts/download_crypto_funding_oi.py`), verified
depth matching the prior probe closely:

| symbol | funding obs (Binance, 8h) | funding start | OI obs (Bybit, 1h) | OI start | OI gaps > 3h |
|---|---|---|---|---|---|
| BTCUSDT | 7,641 | 2019-09-10 | 53,228 | 2020-08-04 | 0 |
| ETHUSDT | 7,407 | 2019-11-27 | 51,355 | 2020-10-21 | 0 |

**Bybit OI is the shallow leg and sets the usable window, exactly as the
prior probe predicted** — years shorter than the H1 price panel already on
disk (2018-01-01) or the funding-only history (2019). After a further
90-day rolling-percentile warmup, the actual usable start is
**2020-11-02 (BTC)** and **2021-01-19 (ETH)** — stated plainly, not
silently shortened.

### Causality — the real risk in this study, verified explicitly (not the usual position-series guard alone)

The novel risk here is a leaked FEATURE value (a funding/OI observation
used before it was actually knowable), a different failure mode from a
leaked trade resolution. Both funding_pctl and oi_pctl are computed on
each feature's own native timestamps using a strictly causal rolling
window (funding: trailing 270 obs = 90 days @ 8h; OI: trailing 2160 obs =
90 days @ 1h — each observation's percentile rank uses only observations
at or before it), aligned onto the H1 price index via `merge_asof`
(backward match: each bar gets the latest feature value at or before its
own timestamp), **then lagged by one additional full H1 bar** as an
explicit conservative safety buffer beyond the already-causal merge.
`verify_feature_causality()` asserts, for every bar actually used, that the
feature's source timestamp is strictly before that bar's own timestamp —
**PASS for both features, both instruments.** The existing position-series
look-ahead guard (`research/backtest.py`) is also reused unchanged and
independently confirms no held position correlates with future returns:
**8/8 PASS.**

### Strategy — every threshold stated, grid small and a priori

| parameter | value | note |
|---|---|---|
| funding_bar | **5%, 10%** (grid axis) | each tail of funding rate's own trailing 90-day percentile distribution |
| oi_bar | **70th percentile** (fixed, not swept) | "elevated" open interest = top 30% of its own trailing 90-day distribution |
| direction | contrarian | funding extreme HIGH (crowded longs) -> SHORT; extreme LOW (crowded shorts) -> LONG |
| stop | 1.0 x ATR(14), H1 | tighter than the trend-family stops — a squeeze thesis expects a fast move |
| target | **1.5R, 2.0R** (grid axis) | |
| max hold | 48 bars (H1) = 2 days | funding resets every 8h; an unwind is expected to resolve fast if it's going to |
| costs | SAME as section 13's crypto sweep — `CRYPTO_COST_BPS` (20bps taker-fee-dominated round-turn), imported unchanged | |
| ann. factor | 365 (section-13 correction, applied correctly from the start) | |

2 instruments x 4 grid cells (funding_bar x R) = **8 configs.**

### The result — headline numbers, then immediately qualified by concentration and OOS (per the task's explicit instruction)

| inst | v | funding_bar | R | trades | gross PF | net PF | Sharpe | DSR | maxDD | cost_R% | top-yr | OOS holds | vs B&H |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0 | 5 | 1.5 | 419 | 1.042 | 0.598 | -2.13 | 0.05 | 75.7% | 34.3% | n/a | no | lose |
| BTCUSDT | 1 | 5 | 2.0 | 414 | 1.055 | 0.655 | -1.74 | 0.27 | 74.2% | 33.8% | n/a | no | lose |
| BTCUSDT | 2 | 10 | 1.5 | 541 | 1.032 | 0.589 | -2.44 | 0.01 | 83.5% | 34.6% | n/a | no | lose |
| BTCUSDT | 3 | 10 | 2.0 | 531 | 1.035 | 0.640 | -2.07 | 0.08 | 82.3% | 34.1% | n/a | no | lose |
| ETHUSDT | 0 | 5 | 1.5 | 392 | 0.971 | 0.651 | -1.76 | 0.26 | 67.2% | 24.8% | n/a | no | lose |
| ETHUSDT | 1 | 5 | 2.0 | 381 | 0.978 | 0.686 | -1.52 | 0.47 | 67.6% | 24.9% | n/a | no | lose |
| ETHUSDT | 2 | 10 | 1.5 | 508 | 0.982 | 0.657 | -1.93 | 0.15 | 76.3% | 25.0% | n/a | no | lose |
| ETHUSDT | 3 | 10 | 2.0 | 494 | 0.980 | 0.685 | -1.73 | 0.29 | 76.9% | 25.1% | n/a | no | lose |

**There is barely a gross edge to begin with** (gross PF 0.971-1.055 —
essentially the coin-flip baseline every family sweep in this project uses
as its own reference point for "no signal"), and what little exists is
consumed by cost (cost_R 24.8-34.6% of 1R — the same cost-vs-stop-distance
mechanism sections 11 and 13 established, now confirmed on a genuinely
different signal type: a 1x-ATR H1 stop is tight enough that even this
strategy's own inherently low trade frequency (funding/OI extremes are
rare) does not protect it from the fixed-cost-vs-tight-stop problem).

### CONCENTRATION — reported prominently, per the task's explicit instruction, not as a footnote

**"top%" is n/a for all 8 configs — worse than concentration, not a pass**:
total net R is negative in every single cell, so the top-year-share ratio
is undefined by this project's own stated convention (a losing config must
not be waved through by an undefined ratio). The per-year breakdown shows
why plainly: every config is net-negative in **every calendar year from
2022 onward**, with the single largest loss cluster in **2023** (-40 to
-54 net R across all 8 configs) — not a concentration story where one bad
year explains an otherwise-good result, but a strategy that simply loses
money in most years it traded. This is the CLEAN opposite of the
"deceptively concentrated" pattern sections 6/9/10 and — most recently —
section 17's crypto-sectors result exhibited (a real edge hiding behind one
dominant year): here there is no edge to hide, in any year.

### OUT-OF-REGIME SPLIT — 2023-01-01, same convention as sections 11/13/16

| inst | v | IS trades | IS PF | IS Sharpe | OOS trades | OOS PF | OOS Sharpe | holds? |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0 | 201 | 0.722 | -3.41 | 218 | 0.502 | -7.02 | no |
| BTCUSDT | 1 | 199 | 0.780 | -2.53 | 215 | 0.558 | -5.93 | no |
| BTCUSDT | 2 | 255 | 0.682 | -3.92 | 286 | 0.517 | -6.67 | no |
| BTCUSDT | 3 | 252 | 0.742 | -3.08 | 279 | 0.561 | -5.85 | no |
| ETHUSDT | 0 | 199 | 0.768 | -2.75 | 193 | 0.549 | -5.82 | no |
| ETHUSDT | 1 | 190 | 0.845 | -1.70 | 191 | 0.553 | -5.76 | no |
| ETHUSDT | 2 | 248 | 0.793 | -2.35 | 260 | 0.547 | -5.97 | no |
| ETHUSDT | 3 | 237 | 0.832 | -1.83 | 257 | 0.570 | -5.66 | no |

**Negative in-sample AND negative out-of-sample, every cell — and it gets
WORSE out of sample**, not just fails to improve. There is no regime in
this window where the strategy worked; 0/8 hold by any definition.

### DSR — computed, but the same caveat this project has applied before when a pool is uniformly bad

Structural pool = this batch's own 8 a priori cells: E[max SR] **-1.491**
(mean -1.916, sd 0.291) — a deeply negative pool. As sections 11 and 13
already established, when every cell in the pool is bad, DSR is not doing
informative work and a merely-less-catastrophic cell can post a
higher-looking DSR (best here: ETHUSDT v1, DSR 0.474) while still losing
money on every trade — **SURVIVOR requires net PF>1 and Sharpe>0, both of
which bind long before DSR does, and neither one clears on any cell.**

### Verdict

**KILL, 0/8 survivors, cleanly and completely** — every gate fails except
the causality/look-ahead guards (8/8 PASS, confirming the test itself is
methodologically sound, not merely unlucky in its result). No gross edge
to speak of (PF ~1.00), what exists is eaten by cost, concentration is
undefined because there's no positive return to concentrate, out-of-sample
performance is worse than in-sample, and every config loses decisively to
simple buy-and-hold (BTC B&H Sharpe +0.81, ETH +0.50, vs this strategy's
best of -1.52). **The positioning-extreme contrarian hypothesis, at the
specification tested here (H1 execution, 1x-ATR stop, 2-day max hold, 5%/
10% funding tails, 70th-percentile OI threshold), is not real.** This is
the first non-price-based signal tested in this project, and the answer is
a clean, honestly-earned no — extending the "no exploitable edge in the
free data this project can reach" conclusion to a genuinely different
information category, not merely repeating it on another price series.

Files: `scripts/download_crypto_funding_oi.py`,
`strategies/positioning_reversal.py`, `run_positioning_reversal.py`. Data:
`data/{BTCUSDT,ETHUSDT}_funding_binance.csv`,
`data/{BTCUSDT,ETHUSDT}_oi_bybit.csv`, `data/crypto_funding_oi_report.csv`.
Results: `results/positioning_reversal.csv`,
`results/positioning_reversal_scored.csv`. Reproduce:
`python scripts/download_crypto_funding_oi.py && python run_positioning_reversal.py`.

**Cumulative trials: N=932** (924 prior + 8 positioning-reversal cells).

## 19. CROSS-ASSET LEAD-LAG — a third information category, tested 2026-08-31, clean statistical negative

### Why this run exists

Every candidate tested so far in this project was self-referential: an
asset predicting its own future from its own past (price patterns,
sections 1-11/13), its own cross-sectional rank among similar assets
(momentum rotation, sections 12/17), or its own positioning extremes
(section 18). This tests a third, genuinely different information
category: does ONE market's move predict ANOTHER market's move with a lag?

### A real bug caught and fixed before any p-value was trusted

The DXY→XAUUSD/CEW pairing initially used `searchsorted` to find "the next
trading day after DXY's date" in the target series — but DXY's real ICE
index history reaches back to 1971, while XAUUSD's Dukascopy archive starts
2018 and CEW's inception is 2009. Every DXY date BEFORE the target's
inception silently collapsed onto the target's very first available date
(searchsorted's natural behavior at the start of an array), which would
have paired **decades of stale, temporally meaningless DXY returns** against
a single early target observation, corrupting the sample (n=13,965 and
n=14,129 — nearly the whole of DXY's 1971-2026 history — for windows that
should hold at most ~1,800-4,300 genuine daily pairs). Caught by checking
the raw counts against what the actual overlapping window should produce,
**before** reading any correlation or p-value. Fixed with an explicit
"next day" sanity bound (reject any pairing more than 5 calendar days
apart) and re-run. This is exactly the kind of look-ahead-adjacent bug the
task warned cross-asset alignment is prone to — not a missing timestamp
lag, but a silent index-alignment fallback that only manifests when the two
series have different starting depths, and it would have inflated both `n`
and (by diluting genuine signal with noise from an unrelated era)
distorted the correlation estimate had it gone unnoticed.

### Four pre-registered pairs, exact lag and causal design stated for each

| # | pair | signal | target | lag |
|---|---|---|---|---|
| 1 | NAS100 → BTC | prior UTC-day close-to-close return (last H1 bar of day D-1 to last H1 bar of day D) | BTC's forward 4h return | entry = first BTCUSDT H1 bar strictly after NAS100's signal timestamp, **plus one further conservative H1 bar of lag** |
| 2 | NAS100 → BTC | same | BTC's forward 8h return | same |
| 3 | DXY → XAUUSD | prior trading-day close-to-close return (real ICE US Dollar Index) | XAUUSD's UTC-calendar-day return on the FIRST day strictly after DXY's close | next full day only, never same-day |
| 4 | DXY → CEW | same | CEW's close-to-close return on its next NYSE trading day | same |

**DXY source, stated as required**: the task offered UUP (an ETF proxy) or
"a better free DXY source if one exists." yfinance serves **DX-Y.NYB**, the
actual ICE US Dollar Index (not an ETF wrapper) with history to 1971 vs
UUP's 2007 inception and its own expense-ratio/tracking-error noise on top
— used instead of UUP for exactly that reason.

**Causality — verified explicitly for every observation, not sampled**:
`verify_causality()` asserts the entry/target timestamp is strictly after
the signal timestamp for every row used. **All 4 pairs: PASS, 100% of
observations**, both before and after the sanity-bound fix above.

### METHOD, stated before any result was read

Pearson correlation between the lagged predictor return and the forward
target return (all non-overlapping observations — NAS100 signals are one
per UTC day against a 4-8h target window; DXY/XAUUSD/CEW are daily-to-
next-daily). Two-sided t-test on the correlation coefficient.
**Bonferroni correction: alpha=0.05 / 4 tests = 0.0125**, decided before
any p-value was read — same discipline section 16's seasonality test used.

### RESULTS — the actual numbers, not just the verdict

| pair | n | r | p-value | causal | significant (Bonferroni) |
|---|---|---|---|---|---|
| DXY → CEW (next day) | 4,339 | -0.0359 | **0.0179** | PASS | no |
| DXY → XAUUSD (next day) | 1,764 | -0.0414 | 0.0822 | PASS | no |
| NAS100 → BTC (4h) | 2,017 | +0.0190 | 0.3931 | PASS | no |
| NAS100 → BTC (8h) | 2,017 | -0.0108 | 0.6270 | PASS | no |

**0/4 pairs clear the Bonferroni-corrected threshold.** One pair (DXY→CEW)
is worth naming precisely rather than glossing over: its raw p-value
(0.0179) clears the UNCORRECTED alpha=0.05 — it would have looked like a
"finding" under naive single-test reporting — but does not clear the
pre-registered corrected bar (0.0125), and the correlation itself is tiny
(r=-0.036, explaining under 0.15% of variance). This is precisely the
scenario the Bonferroni correction exists to catch: with 4 tests run, a
p=0.0179 result has a non-trivial chance of occurring by chance alone even
if none of the 4 relationships is real, and the correction correctly
declines to act on it. The other three pairs are not even close (p=0.08 to
0.63).

### CONCLUSION: NO statistically real cross-asset lead-lag relationship was found

Per the task's explicit instruction, **no directional strategy was built or
backtested on any of these 4 pairs.** Forcing a backtest onto the
smallest-p-value pair (DXY→CEW) anyway would be exactly the failure mode
this pre-registered test and its correction exist to prevent — and even
that pair's own correlation (r=-0.036) is far too small to plausibly
survive real crypto/ETF transaction costs even if it were statistically
genuine, which the correction says it is not.

### Trial accounting

**This batch produced 0 backtested configurations** — same treatment as
section 16's seasonality test: 4 genuine, pre-registered a priori
statistical hypothesis tests are disclosed here as a real multiple-
comparisons budget, but are NOT added to the Sharpe/DSR trial pool, since
none produced a backtested Sharpe value to add. **Cumulative Sharpe/DSR
trial count is unchanged: N=932.**

Files: `scripts/download_dxy_cew.py`, `scripts/test_cross_asset_leadlag.py`.
Data: `data/DXYNYB_daily_yfinance.csv`, `data/CEW_daily_yfinance.csv`,
`data/dxy_cew_report.csv`. Results:
`results/cross_asset_leadlag_test.csv`. Reproduce:
`python scripts/download_dxy_cew.py && python scripts/test_cross_asset_leadlag.py`.

**Reading: the third distinct information category tested in this project
(after cross-sectional ranking and positioning) also produces no free,
exploitable signal at the pre-registered significance bar — a clean,
honestly-earned negative, including one genuinely close call (DXY→CEW)
that the multiple-testing discipline correctly caught and did not act on.
A real alignment bug was also caught and fixed in this study before any
number was trusted, worth carrying forward as a general caution for any
future cross-asset test in this repo: verify observation counts against
the expected overlap window BEFORE reading any statistic, not after.**

## 20. VOLATILITY RISK PREMIUM HARVEST — VIX vs realized vol, tested 2026-08-31, KILLED ON TAIL RISK

### Why this run exists

A fourth distinct information category: a bet on volatility being
mispriced, not on price direction (sections 1-11/13), cross-sectional rank
(12/17), positioning (18), or cross-asset lead-lag (19).

### Base rate — confirmed BEFORE any strategy was built, per the task's explicit requirement

**Documented hypothesis stated first**: implied volatility (VIX) has
historically run persistently above subsequently-realized volatility on
average (the "volatility risk premium") — vol sellers have, on average and
over long periods, collected more premium than the turbulence that
actually showed up cost them. `scripts/test_vol_risk_premium.py` confirms
this on this project's own data, BEFORE any strategy touches it:

| | value |
|---|---|
| sample | 8,431 trading days, 1993-02-01 → 2026-07-30 |
| mean VIX (implied) | 19.51 vol points |
| mean forward-realized SPY vol (20 trading days) | 15.82 vol points |
| **mean spread (VIX − forward realized vol)** | **+3.69 vol points** |
| % of days VIX > forward realized vol | **83.3%** |
| t-stat on mean spread ≠ 0 | **48.5** (n=8,431) |
| by decade | 1990s +4.11, 2000s +3.22, 2010s +3.74, 2020s +3.87 — consistent across ALL four decades, not one regime carrying the result |

**CONFIRMED on this data.** This is a real, persistent, decade-consistent
pattern, not a discovered artefact being dressed up. Building a strategy on
it is well-motivated — which makes what follows more informative, not
less: this is not a strategy failing because its premise was wrong.

### Strategy, proxy, and costs — every choice stated

**Proxy: SVXY** (ProShares Short VIX Short-Term Futures ETF, the task's
named product), available since 2011-10-04. Its REAL historical price is
used unmodified — expense ratio, VIX-futures roll cost/contango drag, AND
its genuine **2018-02-05/06 near-wipeout** (ProShares deleveraged from -1x
to -0.5x VIX-futures exposure immediately after — the fate its cousin XIV
suffered outright, termination) are all authentically embedded in the
price series pulled here, not modeled around or assumed away.

**Signal**: causal. Trailing 20-trading-day realized SPY vol (annualized,
same window as the base-rate check). Ratio = VIX(t) / trailing_RV(t),
known fully at the CLOSE of day t. Position for day t+1 = LONG SVXY if
ratio(t) > threshold, else CASH — the position is only ever exposed to
return realized strictly AFTER the signal was known. **Causality
re-derived independently for every day, both thresholds: PASS.**
Thresholds tested (task-stated): **1.2x and 1.5x.**

**Costs**: 5bps/side (10bps round-turn), a stated conservative assumption
for a specialized, less-liquid-than-SPY vol ETF, charged only when the
position actually changes. **No separate borrow/financing cost added**:
SVXY is a LONG position (never a short sale requiring borrow) in a fund
that itself holds the short-VIX-futures exposure internally — its roll
cost and expense ratio are already embedded in the real price series
pulled above, so a second "short-vol financing charge" on top would
double-count a cost the data already reflects. Stated explicitly, not
assumed.

### TAIL RISK — reported FIRST, prominently, per the task's explicit instruction

| threshold | worst single day | worst single week | 2018 Volmageddon window (Feb) | 2020 COVID window (Feb15-Apr15) |
|---|---|---|---|---|
| 1.2x | **-83.0%** (2018-02-06) | **-92.1%** (week of 2018-02-08) | strategy total return **-90.8%** | -11.4% |
| 1.5x | **-83.0%** (2018-02-06) | **-85.3%** (week of 2018-02-08) | strategy total return **-84.8%** | -0.4% |

**The strategy was LONG SVXY heading into 2018-02-06 at BOTH thresholds** —
the exact real Volmageddon session in which SVXY's actual traded price fell
83% in a single day. This is not a hypothetical stress test bolted on
after the fact; it is what this exact causal signal, applied to this exact
real price series, actually produced. A single day destroyed the large
majority of whatever capital was allocated to this position — **83%+ of
position capital gone in one session**, and the whole month of February
2018 alone erased 85-91% of the strategy's value at that point in its
history.

### Headline numbers — shown only AFTER the tail risk above, deliberately

| threshold | in-position | switches | gross SR | net SR | net PF | maxDD | total net return | top-year share | DSR |
|---|---|---|---|---|---|---|---|---|---|
| 1.2x | 63.8% of days | 337 | +0.45 | +0.43 | 1.119 | 93.1% | **+98.1%** (over ~15yr) | 142% (see note) | 0.56 |
| 1.5x | 36.7% of days | 292 | +0.11 | +0.09 | 1.032 | 91.8% | **-69.9%** | n/a (total ≤ 0) | 0.14 |

At threshold 1.2x, the net Sharpe (+0.43) and cumulative +98.1% return
**would read as a plausible, unremarkable candidate if the tail-risk
section above were skipped** — this is exactly the trap the task warned
against: "an attractive average performance masking a real,
undiversifiable tail risk." maxDD (93.1%) already signals something is
badly wrong here even on the standard metric, but a headline Sharpe alone
would not have made that obvious without the explicit worst-day/-week
figures front and center. Top-year concentration reads a non-intuitive
142% because the -90.8% February 2018 loss is so large relative to the
15-year cumulative total that the ratio construction (top/total, when
total is small and positive) produces a number over 100% — itself another
signal of how completely one event dominates the entire multi-year result,
not a data error.

vs buy-and-hold SPY over the identical window: Sharpe +0.96, maxDD 33.7%,
worst day -10.9% (2020-03-16, COVID), worst week -18.0%. **Both thresholds
lose to SPY on Sharpe alone** (+0.43 and +0.09 vs +0.96) — before even
invoking the tail-risk kill rule. SVXY buy-and-hold itself, for reference,
carries a worse worst-day (-83.0%) and worse maxDD (95.2%) than either
signal-gated variant, confirming the signal did at least reduce EXPOSURE
FREQUENCY to the tail event relative to being permanently long SVXY — but
not enough to avoid landing directly on it.

### Verdict

**KILL ON TAIL-RISK GROUNDS, REGARDLESS OF THE HEADLINE SHARPE, exactly as
the task's critical instruction specifies.** Both thresholds breach the
stated catastrophic-loss bar (single-day < -30%, single-week < -50%) by a
wide margin — a single real historical session (2018-02-06) alone would
have destroyed the large majority of capital allocated to this position.
Neither threshold beats SPY on risk-adjusted return even setting the tail
event aside, and DSR clears nowhere near 0.95 either way (best 0.56).
**SURVIVORS: 0/2**, on tail risk alone, independent of every other gate.

The confirmed base rate (VRP is real, +3.69 vol points, 83% of days, four
consecutive decades) does NOT translate into a tradeable retail-accessible
edge via a naked long-SVXY implementation: the well-documented mechanism by
which volatility sellers get paid on average is precisely the same
mechanism that occasionally, without much prior warning from a 20-day
trailing realized-vol signal, produces a near-total loss in a single
session. This is not a data problem, a look-ahead bug, or a cost-modeling
issue — the causality is verified PASS, the base rate is real, the costs
are conservative and the proxy's real price history (including its own
survival-threatening event) was used unmodified. **The strategy family
itself carries a structural, undiversifiable tail risk that a 20-day
trailing signal cannot see coming, and no amount of a good-looking average
Sharpe changes that.**

Files: `scripts/download_vix_svxy.py`, `scripts/test_vol_risk_premium.py`,
`run_vol_risk_premium.py`. Data: `data/vix_daily_yfinance.csv`,
`data/svxy_daily_yfinance.csv`, `data/vix_svxy_report.csv`. Results:
`results/vol_risk_premium_base_rate.csv`, `results/vol_risk_premium.csv`.
Reproduce: `python scripts/download_vix_svxy.py && python scripts/test_vol_risk_premium.py && python run_vol_risk_premium.py`.

**Cumulative trials: N=934** (932 prior + 2 threshold cells).


## 21. PROTECTED VRP STRUCTURES — can a position structure make the real edge survivable? Tested 2026-08-31, KILLED (edge shrinks below usefulness once properly protected)

### Why this run exists

Section 20 confirmed the volatility risk premium is **real** (VIX averages
+3.69 vol points above forward-realized SPY vol, 83.3% of days, t=48.5,
consistent across all four decades) but killed the naked long-SVXY harvest
on tail risk: **-83.0% in a single session** (2018-02-06, real SVXY traded
price) and **-85% to -92% across that week**, at both signal thresholds.
This run keeps the confirmed edge and the signal **completely unchanged**
(VIX(t) / trailing-20d-realized-SPY-vol(t) > threshold → LONG SVXY t+1,
else CASH; thresholds 1.2x and 1.5x; SVXY real price; 5bps/side; full
2011-10-04 → 2026-08-28 window including Volmageddon and COVID) and asks a
different question: **does a protective position structure keep the edge
survivable through that exact event without trying to predict it?**

Three structures, 12 a priori cells (2 thresholds each). DSR deflation pool
= this batch's own 12 cells (the section-20 naked references are recomputed
here for exact comparability — they reproduce §20 to the decimal — but are
NOT counted as new trials). Cash is assumed to earn **0%** throughout —
conservative, it biases *against* every protected structure.

### The account-level honesty bar (redefined from §20, as the task requires)

§20's bar was position-level (single-day < -30%, week < -50%). §21's bar is
**whole-account**: does the entire account ever lose **more than 15% (soft)
/ 20% (hard) in a single week**, or **more than 15% in a single day**?

### RESULTS — worst account-level day / week FIRST, per the honesty gates

| structure | thr | param | worst DAY | worst WEEK | Feb-2018 | net SR | CAGR | maxDD | DSR | inside HARD bar? |
|---|---|---|---|---|---|---|---|---|---|---|
| **naked §20** | 1.2x | f=1.0 | **-83.0%** | **-92.1%** | -90.8% | +0.43 | +4.7% | 93.1% | — | NO |
| A fixed-fraction | 1.2x | **f=0.10** | **-8.3%** | **-14.3%** | -12.9% | +0.43 | +1.9% | 15.3% | 0.15 | **YES** |
| A fixed-fraction | 1.2x | f=0.20 | -16.6% | -27.3% | -24.9% | +0.43 | +3.6% | 29.0% | 0.15 | NO |
| B vol-of-vol breaker | 1.2x | +20%/1d, cd3 | -26.4% | -26.5% | -13.3% | +0.54 | +13.6% | 48.9% | 0.24 | NO |
| B vol-of-vol breaker | 1.2x | +30%/1d, cd3 | -32.0% | -41.0% | -31.2% | +0.58 | +15.9% | 48.8% | 0.29 | NO |
| C paired VIXY hedge | 1.2x | h=0.5 | -84.6% | -88.7% | -87.5% | -0.02 | -8.6% | 90.1% | 0.00 | NO |
| C paired VIXY hedge | 1.2x | h=1.0 | -86.2% | -85.9% | -84.3% | -0.66 | -26.3% | 99.0% | 0.00 | NO |
| **naked §20** | 1.5x | f=1.0 | -83.0% | -85.3% | -84.8% | +0.09 | -7.7% | 91.8% | — | NO |
| A fixed-fraction | 1.5x | **f=0.10** | **-8.3%** | **-9.5%** | -9.2% | +0.09 | +0.3% | 14.0% | 0.01 | **YES** |
| A fixed-fraction | 1.5x | f=0.20 | -16.6% | -18.8% | -18.3% | +0.09 | +0.4% | 26.8% | 0.01 | NO (day < -15%) |
| B vol-of-vol breaker | 1.5x | +20%/1d, cd3 | -26.4% | -26.5% | -13.3% | -0.02 | -4.6% | 77.3% | 0.00 | NO |
| B vol-of-vol breaker | 1.5x | +30%/1d, cd3 | -26.4% | -26.5% | -10.6% | +0.16 | +0.2% | 63.9% | 0.02 | NO |
| C paired VIXY hedge | 1.5x | h=0.5 | -84.7% | -85.7% | -85.4% | -0.20 | -12.1% | 89.1% | 0.00 | NO |
| C paired VIXY hedge | 1.5x | h=1.0 | -86.3% | -86.3% | -86.3% | -0.49 | -20.0% | 96.5% | 0.00 | NO |

vs **B&H SPY** same window: Sharpe **+0.96**, maxDD 33.7%, worst day
-10.9%, worst week -18.0%. **Every one of the 12 protected cells loses to
SPY on Sharpe.** vs B&H SVXY: Sharpe +0.57, worst day -83.0%, worst week
-92.1%.

### STRUCTURE A — small fixed fractional sizing: works, but only by risking almost nothing

Account return = f × (§20 net strategy return), rebalanced daily to a
constant fraction f; the rest sits in cash at 0%.

- **What Volmageddon costs the WHOLE ACCOUNT:** at **f=0.10** the worst
  single day is exactly 0.10 × -83.0% = **-8.3%**, and the worst *week*
  (daily-rebalanced compound, not a clean f-scaling) is **-14.3%** (1.2x) /
  **-9.5%** (1.5x). At **f=0.20**: worst day **-16.6%**, worst week
  **-27.3%** (1.2x) / -18.8% (1.5x).
- **f=0.10 is the ONLY structure in the entire run that stays inside the
  hard account bar** (week ≥ -20% AND day ≥ -15%) at both thresholds. f=0.20
  already breaches it.
- **But the edge it preserves is not useful.** Sizing does not change
  Sharpe (still +0.43 / +0.09, both < SPY's +0.96) and it scales CAGR down
  to **+1.9% / +0.3%** — far below just holding SPY, or T-bills, over the
  same 15 years. DSR 0.15 / 0.01, nowhere near 0.95. Per-year: 2018 is
  still -14% of account (1.2x, f=0.10) — the single worst year by a wide
  margin, so even at survivable size the result is event-dominated.

### STRUCTURE B — vol-of-vol circuit breaker: dodges Volmageddon, blind to same-day gaps

Full sizing (f=1). If VIX(t)/VIX(t-1) − 1 > b (known at t's close, same
causal timing as the base signal), force CASH for t+1 and hold flat for a
3-day cooldown. b ∈ {+20%, +30%}.

- **It genuinely dodges Volmageddon.** At b=+20%, the breaker fires on
  2018-02-02's close (VIX +28.5%) and again on 2018-02-05's close (VIX
  +115.6%), taking the account to cash across 02-05, 02-06, 02-07, 02-08 —
  avoiding both the -32% (02-05) and the -83% (02-06) SVXY sessions. Feb
  2018 account impact drops from -90.8% (naked) to **-13.3%**. This raises
  net Sharpe *above* the naked version (+0.54 vs +0.43 at 1.2x) and lifts
  CAGR to +13.6%.
- **It is still killed by a same-day gap event it structurally cannot
  see.** The breaker's worst day/week is **Brexit, 2016-06-24: VIX +49%
  and SVXY -26% on the SAME day**, with the *prior* day's VIX move DOWN
  -18%. No pre-close warning existed, so the breaker took the full -26.4%
  no matter how long its cooldown. Worst week -26.5% breaches the -20% hard
  account bar at every b/threshold combination. (b=+30% is worse still: it
  misses the +28.5% pre-warning on 02-02, holds the -32% on 02-05, and
  posts a -32.0% / -41.0% worst day/week.)
- **False-alarm rate, stated honestly:** at b=+20%, 80 triggers over 15
  years, only 25 followed by an SVXY 5-day drop ≤ -15% → **69% false-alarm
  rate**. At b=+30%: 32 triggers, 15 true → 53%. The breaker pays for its
  Volmageddon protection by sitting out dozens of ordinary
  premium-collection windows (visible in the per-year detail: 2019, 2020,
  2021 all turn negative or flat under the breaker where the naked strategy
  earned).

### STRUCTURE C — paired VIXY hedge: the carry bleed swamps the premium AND the tail timing defeats it

Alongside the §20 SVXY position (weight 1.0 when long), hold an additional
long-vol overlay in **VIXY** (ProShares VIX Short-Term Futures ETF, the
direct long-vol counterpart of SVXY; chosen over VXX because VXX's current
note only starts 2018-01-25 — see `scripts/download_vixy.py`) at weight h
of the SVXY notional, only while the position is on. VIXY's real price
embeds its own roll cost / expense ratio exactly as SVXY's does; the
overlay pays 5bps/side on turnover.

- **Steady-state drag, quantified:** the hedge leg loses money on **57-59%
  of ordinary on-position days**, for an annualised drag of **-22% to -36%
  per year at h=0.5** and **-45% to -71% per year at h=1.0**. This alone
  turns the strategy negative: net Sharpe -0.02 to -0.66, CAGR -8.6% to
  -26.3%.
- **And it does not even fix the tail.** VIXY gained +32% to +67% *across*
  Feb 2018, but SVXY's -83% fell on **2018-02-06**, the day *after* VIX's
  +116% spike — and on that specific day VIX mean-reverted -20% and **VIXY
  was -3.2%**. The hedge delivered almost nothing on the one day the loss
  actually landed. Worst account day/week stays at **-85% to -88%**;
  Feb-2018 account impact -84% to -88%. The hedge changes the tail
  magnitude by only a few points while bleeding double-digit CAGR every
  ordinary year.

### Why B and C both fail on the same underlying mechanism

Both are timing-based protections keyed to VIX moving. Volmageddon's worst
SVXY session (02-06, -83%) was **not** a day VIX spiked — VIX *fell* -20%
that day while SVXY collapsed on VIX-futures roll/leverage mechanics. The
circuit breaker only escaped it because 02-06 was pre-warned by 02-05's
+116%. Brexit (2016-06-24) had **no** pre-warning — a clean overnight gap —
and neither a prior-close breaker nor a same-day-held hedge can help with
that. The tail risk §20 identified is not just "large", it is **partly
unhedgeable by any instrument or trigger that acts on observable
volatility**, because the worst realised losses are gap-driven and
mechanics-driven rather than spike-driven.

### Verdict

**KILL — no structure makes the edge tradeable. SURVIVORS: 0/12.**

- **Structure A (f=0.10)** is the only cell that keeps the worst
  account-week inside a survivable bound (-14.3% / -9.5%), and it does so
  trivially — by putting 90% of the account in cash. What survives is a
  **+0.43 / +0.09 Sharpe that loses to SPY, a ~2% / ~0.3% CAGR that loses
  to T-bills, and a DSR of 0.15 / 0.01.** The edge, once sized down far
  enough to be survivable, shrinks below usefulness. This is the honest
  outcome the task named as valid: *"a kill on all three (edge shrinks
  below usefulness once properly protected) is also a valid outcome."*
- **Structure B** improves raw Sharpe (+0.54) and dodges Volmageddon
  specifically, but breaches the -20% hard account-week bar at every
  setting via a same-day gap event (Brexit) it is structurally blind to,
  and carries a 53-69% false-alarm rate.
- **Structure C** is a straight loser: the long-vol carry bleeds 22-71% of
  capital per year and the hedge is mistimed against the actual worst day.

The confirmed volatility risk premium (real, +3.69 vol points, 83% of days,
four decades) still does **not** convert into a tradeable retail edge. §20
killed it on the naked tail; §21 shows the tail cannot be structured away
without also structuring away the return — the protective cost (whether
paid as forgone size, forgone premium days, or hedge carry) is of the same
order as the premium itself.

Files: `run_vol_protected_structures.py`, `scripts/download_vixy.py`. Data:
`data/vixy_daily_yfinance.csv` (+ §20's vix/svxy/spy). Results:
`results/vol_protected_structures.csv`. Reproduce:
`python scripts/download_vixy.py && python run_vol_protected_structures.py`.

**Cumulative trials: N=946** (934 prior + 12 structure cells).

## 22. YEAR-BY-YEAR ABSOLUTE RETURN — full history vs post-COVID, every strategy with a saved return series, reported 2026-08-31

Reporting task on existing results, **not a new trial batch — cumulative
count UNCHANGED at N=946.** Absolute calendar-period return only: not vs any
benchmark, not risk-adjusted. Driver: `report_year_by_year_returns.py`
(rebuilds each daily return series from the same engine / trade files the
original sections used). Outputs: `results/year_by_year_full_history.csv`,
`year_by_year_postcovid.csv`, `year_by_year_annual_R_only.csv`.

### Which strategies can be resliced, and how finely (stated plainly, nothing forced)

| tier | what it means | strategies |
|---|---|---|
| **1 — daily series** (annual + monthly) | full net daily return series rebuilt from `research/momentum_rotation.py` or the VRP modules | MomoRot §12 US-sector (N12/K5), §12.2 widened 27-univ, §17 crypto-sectors, §17 country-ETFs; VRP §20 naked SVXY (thr 1.2 and 1.5); VRP §21 structures A (f=0.10, f=0.20), B (breaker +20%), C (VIXY hedge h=1.0) |
| **2 — per-trade records** (annual + monthly) | daily P&L from `ret_frac` bucketed by trade exit day (1%-risk sizing already baked in) | Sneaky Pivot §9 best cell (NAS100 swing/sneaky/session), 2018-25 **and** its 2013-17 out-of-regime run; ORB §10 best cell (NAS100 OR30 2R), 2018-25 **and** 2013-17 |
| **2b — annual R totals only** (VIEW 1 only, R units, **no monthly**) | only `yr_YYYY` columns were persisted, no daily series | Positioning-extreme reversal §18; Individual US stocks §14; M1 row §11; Crypto 5-family sweep §13 |
| **3 — cannot be resliced at all** | only whole-period summary metrics saved | XAUUSD 5-family sweep §1 (75), US-index sweep §1 (150), HTF breakout §1 (12), Index trend basket §2/§6 (108+90), Regime-switch §15/§16A (only `n_pos_years` saved). Seasonality §16B and Cross-asset lead-lag §19 are statistical tests, not strategies — no return series exists. |

### VIEW 1 — FULL HISTORY, calendar-year absolute return

Ranked by **% of years positive**, then by worst-year magnitude. `%` columns are account return; the four Tier-2b rows are in **R units** (1R ≈ 1% of account at this repo's sizing) and are **not comparable** to the `%` rows — ranked separately.

| # | strategy | span | pos yrs | worst year | max DD | total return |
|---|---|---|---|---|---|---|
| 1 | VRP §21-A fixed **20%** sizing (thr 1.2) | 2011–2026 | **13/16 (81%)** | −25.8% (2018) | −29.0% | +69% |
| 2 | VRP §21-A fixed **10%** sizing (thr 1.2) | 2011–2026 | **13/16 (81%)** | −13.4% (2018) | −15.3% | +32% |
| 3 | Sneaky Pivot §9 best cell 2018–2025 | 2018–2025 | 6/8 (75%) | −7.0% (2024) | −14.7% | +47% |
| 4 | **MomoRot US-sector §12 (N12/K5)** | 2000–2026 | 20/27 (74%) | −18.9% (2022) | −39.0% | **+688%** |
| 5 | MomoRot crypto-sectors §17 | 2020–2026 | 5/7 (71%) | −45.1% (2025) | −57.0% | **+4101%** |
| 6 | MomoRot US-sector widened §12.2 | 2000–2026 | 19/27 (70%) | −13.2% (2018) | −37.5% | +934% |
| 7 | VRP naked SVXY §20 (thr 1.2) | 2011–2026 | 11/16 (69%) | **−91.6% (2018)** | **−93.1%** | +98% |
| 8 | VRP §21-B vol-of-vol breaker +20% | 2011–2026 | 11/16 (69%) | −18.6% (2018) | −48.9% | +563% |
| 9 | MomoRot country-ETFs §17 | 2009–2026 | 11/18 (61%) | −15.4% (2022) | −24.8% | +118% |
| 10 | VRP naked SVXY §20 (thr 1.5) | 2011–2026 | 8/16 (50%) | −87.2% (2018) | −91.8% | −70% |
| 11 | ORB §10 best cell 2018–2025 | 2018–2025 | 4/8 (50%) | −13.8% (2020) | −33.5% | +21% |
| 12 | Sneaky Pivot §9.4 **2013–2017** (out-of-regime) | 2013–2017 | 2/5 (40%) | −11.1% (2015) | −27.6% | +1% |
| 13 | VRP §21-C paired VIXY hedge h=1.0 | 2011–2026 | **0/16 (0%)** | −85.1% (2018) | −99.0% | −99% |
| 14 | ORB §10 **2013–2017** (out-of-regime) | 2013–2017 | **0/5 (0%)** | −36.4% (2014) | −79.0% | −77% |

Tier-2b, annual **R** units (ranked separately):

| strategy | pos yrs | worst year | total | pre-2021 vs 2021+ |
|---|---|---|---|---|
| Crypto 5-family sweep §13 (best cell) | 7/9 (78%) | −3.8R (2022) | +63.1R | +38.8R vs +24.2R |
| Individual US stocks §14 (best cell) | 6/9 (67%) | −3.0R (2019) | +33.8R | −1.9R vs +35.7R |
| Positioning reversal §18 (best cell) | 1/6 (17%) | −45.8R (2023) | **−100.5R** | 0R vs −100.5R |
| M1 row §11 (best cell) | 0/8 (0%) | −3002R (2024) | **−13317R** | −3993R vs −9325R |

### VIEW 2 — POST-COVID ONLY (2021-01-01 → each series' own last data date), MONTHLY granularity

End dates: momentum & VRP series 2026-08-28/31; Sneaky Pivot 2025-12-09; ORB 2025-12-31. Window = **68 months** (60 for the trade strategies). Tier-2b strategies (§18/§14/§11/§13) **have no monthly series and are absent from this view** — for them, "post-COVID" can only mean summing `yr_2021…yr_2026` (shown in VIEW 1's last column).

Ranked by **% of months positive**, then worst-month magnitude:

| # | strategy | pos months | worst month | max DD | total | **2021–2022** | **2023→latest** |
|---|---|---|---|---|---|---|---|
| 1 | MomoRot US-sector widened §12.2 | 46/68 (68%) | −11.2% | −25.3% | +82% | +15.4% | +57.4% |
| 2 | MomoRot country-ETFs §17 | 41/68 (60%) | −6.6% | −22.5% | +42% | −5.1% | +49.8% |
| 3 | MomoRot US-sector §12 (N12/K5) | 40/68 (59%) | −6.6% | −26.0% | +53% | −6.6% | +64.0% |
| 4 | ORB §10 best cell 2018–2025 | 35/60 (58%) | −7.4% | −18.5% | +66% | +21.9% | +36.2% |
| 5 | VRP §21-A fixed 20% sizing | 39/68 (57%) | −2.6% | −5.5% | +23% | +8.0% | +13.6% |
| 6 | VRP §21-A fixed 10% sizing | 39/68 (57%) | −1.3% | −2.8% | +11% | +4.0% | +6.7% |
| 7 | VRP naked SVXY §20 (thr 1.2) | 38/68 (56%) | −13.1% | −26.7% | +127% | +36.6% | +66.4% |
| 8 | VRP §21-B vol-of-vol breaker +20% | 37/68 (54%) | −16.5% | −30.2% | +42% | +7.9% | +31.5% |
| 9 | VRP naked SVXY §20 (thr 1.5) | 31/68 (46%) | −13.1% | −22.0% | +62% | −10.6% | +81.1% |
| 10 | Sneaky Pivot §9 best cell 2018–2025 | 27/60 (45%) | −5.1% | −14.7% | +44% | +15.9% | +24.4% |
| 11 | VRP §21-C paired VIXY hedge h=1.0 | 26/68 (38%) | −13.7% | −79.9% | −77% | −47.1% | −56.9% |
| 12 | MomoRot crypto-sectors §17 | 22/68 (32%) | −38.2% | −57.0% | **+1428%** | **+1748.5%** | **−17.3%** |

**Post-COVID front-loading — the explicit check the task asked for:**
- **MomoRot crypto-sectors** is the extreme case: +1748% in 2021–2022, **−17%** in 2023→2026. Essentially all of it is 2021 (Jan +220%, Feb +118%, Apr +118%); the BTC-200SMA filter then sat in synthetic cash for all of 2022 and all of 2026-YTD. This is the same 2021-crypto-bull artefact §17 already killed it for.
- **The three equity momentum rotations are the reverse** — flat-to-negative 2021–2022, then **+50% to +64%** in 2023→2026. That is not an edge appearing; it is the 2023–2025 equity bull. Absolute monthly hit-rate 59–68% over 2021–2026 is "stocks went up," not alpha — and §12.5's walk-forward already showed the *vs-SPY* edge has been absent since 2009.
- **VRP naked/breaker** front-load mildly toward 2023+ (naked 1.5: −11% then +81%), driven by a calm-vol 2023–2025 with no Volmageddon-style event in the window — exactly the regime in which short-vol looks riskless right up until it doesn't (§20/§21).
- **ORB and Sneaky Pivot** are the two that are *not* front-loaded within the post-COVID window (ORB +22% then +36%; SP +16% then +24%) — but see the disagreement note below.

### DOES THE POST-COVID RANKING MATERIALLY DISAGREE WITH FULL HISTORY?

Yes, four names move ≥3 places — and in every case the move is a **short-window / regime artefact**, not evidence the post-COVID world rewards something real:

| strategy | full-hist rank → post-COVID rank | why it moves, and whether it means anything |
|---|---|---|
| **ORB §10 (2018–2025 cell)** | 11 → **4** (▲7) | Looks much better recently: +66% post-COVID, not front-loaded. **But this is the strategy §10 called "the hardest kill in the project"** — gross-*negative* out of regime (2013–2017: 0/5 positive years, −77%, −79% DD; bottom of VIEW 1). The post-COVID window is entirely *inside* the 2018–2025 regime §10 already judged, where ORB also made +21% — and still lost to buy-and-hold NAS100 and earned 74% of its P&L in one year. 60 months in one regime cannot overturn a two-window test that already ran. **Not real.** |
| **MomoRot country-ETFs §17** | 9 → **2** (▲7) | 60% positive months, +50% since 2023. Same story as the US-sector rotation: the 2023–2025 global-equity rally, not a mechanism. §17 killed it (DSR + loses to its own equal-weight basket); nothing here changes that. |
| **MomoRot US-sector widened §12.2** | 6 → **1** (▲5) | Top of the post-COVID table on 68% positive months. It is the 2023–2025 bull again — §12.2's own verdict (same DSR ceiling as §12) stands, and §12.5's walk-forward showed the vs-SPY edge is pre-2009 only. |
| **Sneaky Pivot §9 (2018–2025 cell)** | 3 → **10** (▼7) | The *opposite* disagreement: looked good on **8 annual buckets** (6/8 positive years, 75%) but only 45% of **months** are positive post-COVID, and its +44% post-COVID total leans on **Oct 2025 alone (+21.2% in one month)**. The annual view flattered a concentrated record — exactly reservation 3 in §9.2. The finer (monthly) lens is the more honest one here. |
| MomoRot crypto-sectors §17 | 5 → 12 (▼7) | 2021 carried the entire full-history record; strip the annual view's 2021 bucket and the monthly post-COVID hit-rate is 32%. Confirms the front-loading. |

**Bottom line.** No strategy "looks bad over 27 years but genuinely good post-COVID." Every apparent post-COVID improvement (ORB, both surviving momentum rotations) is the **2023–2025 equity/vol-calm regime** filling a short 60–68-month window, and in each case a longer or out-of-regime test that *already exists in this project* (§10's 2013–2017 ORB inversion, §12.5's pre-2009-only momentum edge, §17's kills, §20/§21's tail) contradicts the flattering recent picture. The one genuine cross-view disagreement points the *unfavourable* way: Sneaky Pivot's annual record is more concentrated than it looks, visible only once you drop to monthly buckets. **The post-COVID window is too short and too single-regime to promote anything the full-history and out-of-regime tests already retired.**

### Consistency winners on absolute return alone (for completeness, not as a recommendation)

If the only question is "how often is a calendar period green and how bad is the worst one," the two structurally safe answers are the **VRP §21-A fixed-fraction sleeves** (81% of years positive full-history, worst month −1.3%/−2.6%, max DD −2.8%/−5.5% post-COVID) — because they are 90%/80% cash by construction (§21) — and, with more variance, the **US-sector momentum rotation** (74% of years positive, but −39% max DD and a vs-SPY edge that §12.5 showed is gone since 2009). Everything with a headline-grabbing total return (crypto momentum +4101%, VRP breaker +563%, momentum US +688%) carries either a −57% to −99% drawdown, a single-year/single-regime concentration, or both.

Files: `report_year_by_year_returns.py`, `results/year_by_year_full_history.csv`,
`results/year_by_year_postcovid.csv`, `results/year_by_year_annual_R_only.csv`.
Reproduce: `python report_year_by_year_returns.py`. **No trials added — N=946.**

## 23. WIN RATE > 50% — every config across the project, reported 2026-08-31

Reporting task on **saved results only** — nothing re-run, **cumulative
trial count UNCHANGED at N=946**. Driver: `report_winrate_over_50.py`.
Scans every scored result CSV for configs whose **net per-trade win rate**
(fraction of trades with net R > 0, verified against `orb_trades.csv` to 3
dp) is strictly above 50%, regardless of the ultimate kill verdict. `avgWin`
/ `avgLoss` in R are reconstructed exactly from `(win_rate, net_pf,
net_R_mean)` — an identity given those definitions, cross-checked against
the raw ORB trade file (NAS100 OR15 1R → +0.868 / −1.006 R both ways).

### What could and could not be assessed

| batch | win-rate data | # configs with win rate > 50% |
|---|---|---|
| Individual US stocks §14 (90 in-regime + 90 OOS) | saved | **20** (9 in-regime, 11 OOS) |
| Index trend/macross single-instrument configs §2 / §6 (108 + 90) | saved | **12** (7 in-regime §2, 5 OOS §6) |
| ORB §10 original (12) + §10.2 moderate-stop (12) + §10.4 trend-filtered (12) | saved | **11** (4 + 4 + 3, all in-regime; 0 out-of-regime) |
| Gold/index 5-family sweep §1 (150) | saved | 0 (max win rate **exactly 50.0%** — nothing strictly above) |
| XAUUSD HTF breakout §1 (12) | saved | 0 (max 42.2%) |
| M1 row §11 (45 + 30) | saved | 0 (max 37–39%) |
| Crypto 5-family sweep §13 (90) | saved | 0 (max 45.1%) |
| 15-min Sneaky Pivot §9 (24 + 16) | saved | 0 (max 42.1%) |
| Positioning-extreme reversal §18 (8) | saved | 0 (max 40.8%) |
| **XAUUSD 5-family sweep §1 (75)** | **NOT saved** | **unknowable** — `sweep_progress.csv` never stored a win-rate column (only gross/net PF, Sharpe, IS/OOS). Cannot be recovered without a re-run. |

**43 trade-based configs total** clear the 50% win-rate bar. **14 of the 43
sit on fewer than 40 trades** (daily strategies over ~8 years) — those win
rates are statistically noisy and flagged `!thin` below.

### TABLE A — the 43 configs with net win rate > 50% (sorted by win rate; representative rows)

Full list in `results/winrate_over_50_trade_configs.csv`. `avgWin`/`avgLoss`/`netMeanR` in R; `netPF`/`netSR` after real costs.

| sec | win % | avgWin R | avgLoss R | net PF | net SR | trades | strategy — config — window | killed by |
|---|---|---|---|---|---|---|---|---|
| 14 | **73.3%** | +0.97 | −0.60 | 4.44 | +0.91 | **15** !thin | US stock — XOM D1 meanrev v1 — OOS 2010-17 | DSR + loses to B&H |
| 6 | 66.7% | +1.59 | −1.01 | 3.16 | +0.85 | **9** !thin | Index — US30 D1 macross v1 — OOS 2013-17 | family gross PF collapses OOS + DSR |
| 14 | 63.2% | +1.99 | −1.01 | 3.38 | +0.83 | **19** !thin | US stock — AAPL D1 macross v1 — OOS 2010-17 | DSR + B&H |
| 14 | 62.5% | +1.62 | −1.01 | 2.67 | +0.81 | **32** !thin | US stock — WMT D1 macross v0 — in 2018-25 | DSR + B&H |
| 2 | 62.5% | +1.88 | −1.01 | 3.10 | +0.74 | **16** !thin | Index — NAS100 D1 macross v1 — in 2018-25 | family gross PF collapses OOS + DSR |
| **2** | **60.0%** | **+1.27** | **−0.85** | **2.25** | **+1.07** | **80** | **Index — NAS100 D1 trend v0 — in 2018-25** | **family gross PF collapses OOS (1.363→1.006, §6) + DSR 0.21–0.45** |
| 2 | 58.2% | +1.27 | −0.99 | 1.78 | +0.78 | 67 | Index — NAS100 D1 trend v1 — in 2018-25 | family gross PF collapses OOS + DSR |
| 14 | 55.7% | +1.26 | −0.93 | 1.72 | +0.69 | 70 | US stock — AAPL D1 trend v0 — in 2018-25 | DSR (best 0.45) + B&H |
| 14 | 55.0% | +1.94 | −1.01 | 2.35 | +0.84 | 40 | US stock — CAT D1 momentum v1 — in 2018-25 | DSR + B&H |
| 14 | 55.0% | +1.33 | −1.01 | 1.60 | +0.84 | 111 | US stock — CAT D1 momentum v2 — OOS 2010-17 | DSR + B&H |
| 14 | 54.7% | +1.80 | −1.01 | 2.15 | +0.97 | 64 | US stock — CAT D1 breakout v1 — in 2018-25 | DSR + B&H |
| 14 | 54.5% | +1.22 | −0.95 | 1.54 | +0.73 | 112 | US stock — AAPL D1 breakout v2 — in 2018-25 | DSR + B&H |
| 10.4 | 54.0% | +0.76 | −0.88 | 1.02 | +0.10 | 822 | ORB trend-filtered — NAS100 OR30 1R — in 2018-25 | OOS gross <1 + concentration + DSR |
| 10 | 52.8% | +0.79 | −0.87 | 1.01 | +0.09 | 1609 | ORB original — NAS100 OR30 1R — in 2018-25 | OOS gross inverts + concentration 0/12 + B&H 4/4 + DSR |
| 10.2 | 52.1% | +0.86 | −1.12 | 0.83 | −1.27 | 1616 | ORB moderate-stop — NAS100 OR15 1R — in 2018-25 | moderate stop made in-regime **worse** + all §10 kills |

…and 28 more (mostly §14 US-stock D1 cells at 50–56% win and §2/§6 index D1/H8 macross+trend cells), every one carrying `DSR` and either `B&H` or `OOS-INV(family)`.

**Only 7 of the 43 are simultaneously > 50% win, net PF > 1, positive net Sharpe, AND on ≥ 40 trades:**
NAS100 D1 trend v0 (§2, SR +1.07 / 80 tr), NAS100 D1 trend v1 (§2, +0.78 / 67), CAT D1 breakout v1 (§14, +0.97 / 64), CAT D1 momentum v1 (§14, +0.84 / 40), CAT D1 momentum v2 (§14 OOS, +0.84 / 111), AAPL D1 trend v0 (§14, +0.69 / 70), AAPL D1 breakout v2 (§14, +0.73 / 112). **All 7 are D1 trend/breakout/momentum on an index or a single stock, and all 7 are killed by DSR — plus buy-and-hold (§14 stocks) or the §6 out-of-regime family collapse (§2 index).**

### ORB specifics

Of ORB's 11 in-regime configs above 50% win, **only two are net-profitable at all** — NAS100 OR30 1R original (net PF 1.01, SR +0.09) and its trend-filtered twin (net PF 1.02, SR +0.10) — both statistically indistinguishable from break-even on ~1,600 / ~820 trades. Every other ORB > 50%-win config (all the OR15 1R and US30 cells, and every moderate-stop cell) is **net-losing**. **No ORB config exceeds 50% win rate on the 2013-17 out-of-regime window** (max 47–49%) — consistent with §10's finding that the edge inverts there.

### TABLE B — portfolio / period strategies (no per-trade win rate)

Momentum rotation §12/§12.2/§17 and volatility premium §20/§21 are period strategies. Period analogue used: **% of calendar years with a positive absolute return**, from `results/year_by_year_full_history.csv` (§22 reslice, not recomputed).

| % positive years | pos/total | avg + year | avg − year | best yr | worst yr | total ret | max DD | strategy | killed by |
|---|---|---|---|---|---|---|---|---|---|
| **81.2%** | 13/16 | n/s | n/s | +24% | −25.8% | +69% | −29.0% | VRP §21-A fixed 20% sizing | §21: edge shrinks below usefulness once sized to survive; loses to SPY; DSR 0.15 |
| **81.2%** | 13/16 | n/s | n/s | +11% | −13.4% | +32% | −15.3% | VRP §21-A fixed 10% sizing | §21: same — CAGR ~2%, < T-bills; DSR 0.01 |
| **74.1%** | 20/27 | **+15.3%** | **−9.8%** | +33% | −18.9% | +688% | −39.0% | MomoRot US-sector §12 (N12/K5) | §12: DSR never clears 0.95; §12.5: vs-SPY edge is entirely pre-2009 |
| 71.4% | 5/7 | n/s | n/s | +1696% | −45.1% | +4101% | −57.0% | MomoRot crypto-sectors §17 | §17: 2021-bull artefact; DSR; loses to its own equal-weight basket |
| 70.4% | 19/27 | n/s | n/s | +39% | −13.2% | +934% | −37.5% | MomoRot US-sector widened §12.2 | §12.2: same DSR ceiling as §12 |
| 68.8% | 11/16 | +44.1% | −25.9% | +165% | **−91.6%** | +98% | **−93.1%** | VRP naked SVXY §20 (thr 1.2) | §20: tail risk — −83% in one 2018 session; loses to SPY |
| 68.8% | 11/16 | n/s | n/s | +104% | −18.6% | +563% | −48.9% | VRP §21-B vol-of-vol breaker +20% | §21: still breaches −20% weekly bar on the Brexit gap; 53–69% false alarms |
| 61.1% | 11/18 | n/s | n/s | +26% | −15.4% | +118% | −24.8% | MomoRot country-ETFs §17 | §17: DSR; loses to equal-weight basket |
| 50.0% | 8/16 | +25.5% | −20.6% | +66% | −87.2% | −70% | −91.8% | VRP naked SVXY §20 (thr 1.5) | §20: tail risk; net total return negative |
| 0.0% | 0/16 | — | — | −0% | −85.1% | −99% | −99.0% | VRP §21-C paired VIXY hedge h=1.0 | §21: hedge carry −45 to −71%/yr; still mistimed against the tail |

(n/s = per-year series for avg +/− year not separately persisted in §22; only summary stats.)

### TABLE C — momentum rotation §12 (N12/K5): recent sub-period breakout

From `results/momentum_rotation_walkforward.csv` (§12.5 walk-forward, **resliced, not re-run**). Data ends 2026-08-28, so 2026 is partial (Jan–Aug).

| period | years | positive years (abs) | "win rate" (abs) | beat SPY | avg year | worst | best | strategy cum | SPY cum | avg within-year SR |
|---|---|---|---|---|---|---|---|---|---|---|
| last **3** calendar years (2024–2026) | 3 | 3 | **100%** | **1 / 3 (33%)** | +15.3% | +10.6% | +18.2% | **+53.2%** | +67.1% | +1.37 |
| last **4** calendar years (2023–2026) | 4 | 4 | **100%** | **1 / 4 (25%)** | +13.3% | +7.0% | +18.2% | **+64.0%** | +110.9% | +1.19 |
| last 3 **complete** years (2023–2025) | 3 | 3 | **100%** | 1 / 3 (33%) | +14.2% | +7.0% | +18.2% | +48.3% | +85.5% | +1.25 |

Momentum rotation has been **positive in absolute terms every one of the last 3–4 years** (a 100% period "win rate"), with a healthy ~+1.2–1.4 average within-year Sharpe — but it **beat SPY in only one of them** and its cumulative return over each recent window is 14–47 percentage points *behind* SPY. This is the same picture §12.5's full walk-forward gave: the strategy makes money in a bull market, just less of it than the index, and its genuine edge (crash defence) has had nothing to do since 2008.

### VERDICT — did any config have win rate > 50% AND survive every gate?

**NO. Unambiguously not.** STATE_OF_PLAY §1: *946 configs, 0 survive.* Zero
configs survived every honesty gate, so by construction none of the 43
trade-based configs above 50% win rate, and none of the period strategies
above 50% positive-years, did either.

- The **43 trade-based > 50%-win configs** are dominated by **D1 trend /
  macross / breakout / momentum** on individual US large-caps (§14) and US /
  EU index CFDs (§2). Every one is killed by **DSR** (a flat 90-cell or
  18-basket a-priori pool in which no single config is a statistical
  outlier), and additionally by **losing to buy-and-hold** (§14) or by the
  **§6 out-of-regime family collapse** (§2). The single best on
  risk-adjusted terms — NAS100 D1 trend v0, 60% win, net PF 2.25, net SR
  +1.07, 80 trades — is one of the exact cells §6 demonstrated was a
  2018-2025 regime artefact (its family's gross PF falls to 1.006 on
  2013-17).
- The **highest win rates of all** (73%, 67%, 63%) sit on **9–19 trades** —
  noise, not evidence.
- **ORB**: only two > 50%-win configs are even break-even (net PF ≈ 1.01,
  SR ≈ +0.09), and none exceeds 50% win out of regime.
- The **XAUUSD 5-family sweep §1 (75 configs)** cannot be assessed at all —
  win rate was never saved for that batch.
- **Period strategies**: VRP fixed-fraction sleeves (81% positive years)
  and US-sector momentum rotation (74%) look consistent, but the VRP
  sleeves earn ~2–4% CAGR (below T-bills) precisely because they hold
  80–90% cash, and momentum rotation loses to SPY (§12.5). Both killed.

A high win rate has never been a scarce ingredient in this project — 43
configs have one. What none of them also have is a deflated-Sharpe-
significant, cost-surviving, regime-robust, better-than-buy-and-hold edge.

Files: `report_winrate_over_50.py`,
`results/winrate_over_50_trade_configs.csv`,
`results/winrate_over_50_period_strategies.csv`,
`results/winrate_over_50_momentum_recent.csv`. Reproduce:
`python report_winrate_over_50.py`. **No trials added — N = 946.**
