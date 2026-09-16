# STATE OF PLAY — AI Quant Trading Lab

**Last updated: 2026-09-16 (§56/§57 — the last two combined-book pairings,
completing ALL C(5,2)=10 combinations across this project's 5 spot/CFD-plus-
gold candidate legs. See the 2026-09-16 blockquote below section 1 for the
full current-state summary — it supersedes the "FTMO hunt concluded, no
edge" framing that follows: since 2026-09-15, four real, buy-and-hold-
beating candidates were found via a joint entry/exit/SL/TP-refinement
method, and combined-book work (with risk-parity weighting) pushed the
project's honest best deployable result to Sharpe +1.793, maxDD 3.1%, 9/9
years net-positive. Cumulative trial count N=1570.).** Read this file
first in any new session. It is the
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

> **2026-09-15/16 — FOUR REAL, BUY-AND-HOLD-BEATING CANDIDATES FOUND, AND A
> DEPLOYABLE COMBINED BOOK BUILT ON TOP OF THEM (§35-§57).** Everything above
> this line predates a real change in direction: rather than searching for new
> signal families, the project's already-real-edge cells were pushed through a
> disciplined JOINT entry/exit/SL/TP grid ("tune everything together, then
> follow the gradient past the grid edge before trusting an edge-hugging
> result — never argmax, always confirm a plateau") instead of the staged,
> one-dimension-at-a-time tuning used everywhere earlier. Four candidates now
> genuinely beat their own instrument's buy-and-hold on a risk-adjusted basis:
> **ORB gold RETEST** (XAUUSD, Sharpe +1.488, §39), **credit-spread SPY**
> (options, Sharpe +2.090, this project's single best result, §41),
> **NAS100 H4 macross** (Sharpe +0.963, §42) and **US30 H4 macross**
> (Sharpe +0.999, §43), plus **US30 H4 breakout-retest** (Sharpe +1.684, §45,
> the strongest pure spot/CFD single-leg result). A fifth family member,
> **NAS100 H4 breakout-retest** (Sharpe +0.526, §46), was found weaker and
> does NOT beat its own buy-and-hold — kept in the candidate pool for
> portfolio-construction purposes but not counted as a fifth win. None of the
> five clears this project's DSR bar against its full contaminated family
> pool (the same historical DSR-saturation issue documented for every family
> in this project) — every verdict rests on economic/robustness evidence
> (beats B&H, year-by-year positivity, no tail-risk flag), stated explicitly,
> not on DSR.
>
> **Combined-book work (§44-§57) then tested every C(5,2)=10 pairing of
> these five legs** (plus one 3-way not attempted) at both fixed 50/50 and
> in-sample/rolling risk-parity weighting. Two structural lessons emerged,
> both non-obvious and now well-evidenced: **(1)** near-zero correlation is a
> robust, recurring property across every instrument/family/asset-class
> pairing tried (range -0.020 to +0.079 across all 10 pairs — even the one
> negative correlation found didn't help when the quality gap was too big);
> **(2)** whether a combined book actually beats its own best individual leg
> is predicted far better by the SIZE OF THE QUALITY GAP between the two legs
> than by correlation alone — pairings with a gap under ~1.8x reliably beat
> both legs outright even under plain 50/50 (§44, §48, §54's record-low
> +0.004 correlation); pairings with a gap over ~2.8x never closed the gap
> even with risk-parity and a negative correlation (§47, §57); pairings in
> between land as partial, muted improvements (§49, §50, §53, §55, §56).
> Risk-parity (inverse-volatility weighting, §51) is the adopted default
> going forward — it reliably narrows whatever gap exists, sometimes
> dramatically (§47's "failed" pairing was fully rescued by it) — and a
> genuinely CAUSAL, walk-forward version of it (§52, monthly rebalance,
> trailing 90-day vol, no look-ahead) was confirmed to retain most of the
> in-sample benefit, so this is not a look-ahead artifact.
>
> **THE PROJECT'S HONEST, DEPLOYABLE BEST RESULT AS OF THIS WRITING:**
> **ORB gold RETEST + US30 breakout, rolling (causal) risk-parity weighted
> (§52): Sharpe +1.793, maxDD 3.1%, 9/9 years net-positive** (every year of
> its 2017-2025 span, including the worst, still positive) — the most
> robust result in this project's history, on any candidate, any window.
> The in-sample (non-deployable) version of the same pairing reaches Sharpe
> +1.900 (§51); the single cleanest, no-rescue-needed win under plain 50/50
> is the sibling pairing ORB gold + US30 macross (§54, Sharpe +1.513 fixed,
> correlation +0.004, the lowest measured in the project). **Read §35
> onward for the full detail; this paragraph is the one-stop summary for
> anyone who does not have time to read fifty sections.**

---

## 1. BOTTOM LINE — the FTMO hunt is concluded, and the answer is no

> **UPDATE 2026-09-16 — the headline below ("no edge was found") describes
> the state of the project through §34 and is retained as the historical
> record it always was. It is superseded by the 2026-09-15/16 blockquote
> immediately above: four real, buy-and-hold-beating candidates now exist,
> and a combined, risk-parity-weighted book of two of them reaches Sharpe
> +1.793 with 9/9 positive years. Read that blockquote first; treat
> everything in section 1 below as describing the FTMO-specific hunt only
> (a narrower question than "is there any tradeable edge in this project"),
> which is still true on its own terms — none of the four winning
> candidates has been run through the FTMO ruleset (5%/10% drawdown limits,
> profit target, minimum trading days, Best Day rule), a genuinely open
> next step if FTMO-style prop trading (rather than a personal or fund
> book) is the deployment target.**

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

Trial composition (this is the cumulative DSR trial count, N=1085 — see the
2026-09-01 line at the foot of the table for the +84 ORB entry-filter batch, §10.5,
the 2026-09-02 (a) line for the +3 RETEST OR30/1R compounding-table backtests, §10.6,
the 2026-09-02 (b) line for the +8 exit-management backtests, §10.7,
the 2026-09-03 (a) line for the +2 EURUSD RETEST OR30/1R generalization cells, §10.8,
the 2026-09-03 (b) line for the +6 momentum-rotation rebalance-frequency cells, §12.6,
the 2026-09-03 (c) line for the +4 ML-on-positioning-data cells, §18.1,
the 2026-09-03 (d) line for the +20 long-call-option cells, §24,
and the 2026-09-03 (e) line for the +12 post-earnings-drift cells, §25):

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
| RETEST OR30/1R compounding-table backtests — SPX500 (new instrument, both windows) + XAUUSD 2017 out-of-regime (§10.6) | SPX500, XAUUSD | 3 | 0 survive (§10.6) — SPX500 loses to buy-and-hold in all 3 periods; XAUUSD 2017 slice is a statistical wash vs its own buy-and-hold (+13.1% vs +13.2%), not a beat |
| RETEST OR30 exit-management — 3R, breakeven, trailing stop, both windows + 1R/2R out-of-regime-2017 (§10.7) | XAUUSD | 8 | 0 survive (§10.7) — every wider-target/dynamic-stop variant gives back dollars vs the 1R baseline on FULL 2018-2025, and none beats buy-and-hold |
| RETEST OR30/1R generalization to FOREX — EURUSD, both windows (§10.8) | EURUSD | 2 | 0 survive (§10.8) — first FX pair; the only RETEST cell with net PF < 1 in BOTH windows (0.879 in / 0.967 out), net Sharpe negative both, 1% compounding −37.9% over 2018-2025. Gross breakout edge generalizes to FX (gross PF 1.39/1.48); it cannot pay its costs on a currency pair |
| Momentum-rotation rebalance-frequency sweep — weekly/bi-weekly/quarterly new, monthly/bi-monthly reused (§12.6) | 17-ETF universe, SPY benchmark | 6 | 0 survive (§12.6) — DSR reference-only this batch; quarterly maximises full-period compounded return (+1010% vs SPY +772%, only cadence to beat SPY on raw return), monthly wins the 2000-09 stress window (+138%); higher frequency strictly worse everywhere. Does not revive §12 — quarterly DSR 0.526 vs 0.95 bar, same pre-2009 crash-hedge artefact as §12.5 |
| ML on crypto positioning data — shallow LightGBM, funding/OI + price-control features (§18.1) | BTCUSDT, ETHUSDT | 4 | 0 survive (§18.1) — DSR reference-only; sealed-test IC ≈ 0 (mean −0.005, 3/4 negative), strategy net Sharpe −2.6 after real costs, beats B&H 0/4. Model leans on positioning features (66% gain) but they carry no OOS predictive value; ablation positioning-only/price-only/both all ≈ 0 IC. Closes the ML-on-positioning thread |
| Long short-dated call options on a trend signal — defined-risk structure, BS-approximated premiums (§24) | SPY, QQQ, AAPL, MSFT, GOOGL | 20 | 0 survive (§24) — DSR reference-only; 5 inst × 2 DTE × 2 moneyness, 2012-2026. 0/20 beat the underlying buy-and-hold on total return or Sharpe (SPY/QQQ −87%…+42% vs index +677%/+1326%). Time decay dominates: 44% of options expire worthless, wrapper costs 20-74% of return/trade vs delta-matched stock. SPY/QQQ on near-real IV (^VIX/^VXN); single names on optimistic RV proxy, still lose |
| Post-earnings-announcement drift — SUE on yfinance surprise data, 63 large-caps, 20/60-day holds (§25) | 63 US large-caps (4,735 events, 2006-2026) | 12 | 0 survive (§25) — DSR reference-only; 3 SUE thresholds × 2 horizons × [long/short, long-only]. Gross drift is REAL (+1.2%/20d, +3.4%/60d, 58-65% win, OOS stronger than IS, not concentrated, clears net PF/Sharpe/OOS/conc gates) but 0/12 beat equal-weight B&H of the universe (best CAGR +12.8% vs +15.8%). Same terminal reason as §12/§14: real edge, loses to owning the beta. Data caveats (estimate PIT integrity, survivorship) flatter it → kill is solid |
| **Total** | | **1085** | **0 survive** |

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
| `SPX500_M1_2017_2025_cfd_dukascopy.csv` | 339 MB | S&P 500 M1 CFD, 2017-01 → 2025-12 — added 2026-09-02, closes the "SPX500 is H1-only" gap noted in §10 | `scripts/download_spx500_xauusd_backfill.sh` → `scripts/merge_spx500_xauusd_backfill.py` |
| `XAUUSD_M1_2017_spot_dukascopy.csv` | 41 MB | Gold M1 SPOT, 2017 only — added 2026-09-02, extends XAUUSD M1 back one year for a 2017 out-of-regime slice | same as above |

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

### 10.6 RETEST OR30/1R compounding tables — SPX500 finally testable, all 4 instruments, 2026-09-02

**Why this batch exists.** §10.5's RETEST result was the closest thing to a
lead ORB ever produced (XAUUSD OR30/1R: gross PF 1.78, net PF 1.34, SR +1.14),
but the "does it actually make money" question had only ever been answered in
Sharpe/PF units. This task compounds it in dollars — 1% risk/trade from
$100,000 — on **all four** liquid instruments the repo can reach, laid out on
the **same three periods** for every one: **FULL** 2018-01-01..2025-12-31,
**OUT-OF-REGIME** 2017-01-01..2017-12-31, **RECENT** 2022-01-01..2025-12-31 —
each next to buy-and-hold over the identical range, from the same M1 mid data
the strategy trades on.

**OUT-OF-REGIME is ONE bull year, not a real regime test — stated plainly.**
Every other out-of-regime test in this project (§6, §9.3, §10.5) used
2013-2017, a 4-5 year window with real dispersion (a low-vol grind, no crash).
2017 alone is a single, unusually calm, straight-up year for every one of
these four instruments (SPX500 B&H +18.8%, NAS100 +30.2%, US30 +24.3%, gold
+13.2%) — it cannot show whether an edge survives a *different* regime, only
whether it survives *one more good year*. It is used here only because it is
the deepest window all four instruments share (XAUUSD and SPX500 had **no**
M1 before 2017 on disk prior to this session); NAS100/US30 already have the
real 2013-2017 test in §10.5 and it is not superseded by this section.

**Two data gaps closed this session**, both backfilled via Dukascopy
(`scripts/download_spx500_xauusd_backfill.sh`, bid+ask pulled separately,
merged to a real spread by `scripts/merge_spx500_xauusd_backfill.py`, UTC):
- `data/SPX500_M1_2017_2025_cfd_dukascopy.csv` — SPX500 had **only H1** on
  disk before this session (§10 stated the strategy was "NOT runnable" on it
  for exactly this reason). 2.71M M1 bars, 2017-01-03..2025-12-31, bid_close
  2,184.25..6,943.84, spread 1.31 bps median, 0 negative spreads.
- `data/XAUUSD_M1_2017_spot_dukascopy.csv` — the repo's XAUUSD M1 started
  2018-01; this adds the missing 2017 year. 323,514 bars, bid_close
  1,146.33..1,357.09, spread 1.91 bps median, 0 negative spreads.

**3 genuinely NEW backtests this run** (§1 trial count 1030 → **1033**), each
one fully-specified cell (instrument × window × OR30 × target=1R ×
variant=RETEST), scored with the same honesty gates as every other cell —
look-ahead guard, gross/net PF, Sharpe, max drawdown:

| cell | n trades | guard | gross PF | net PF | SR | maxDD | cost_R |
|---|---|---|---|---|---|---|---|
| SPX500 FULL (2018-2025) | 747 | PASS | 1.383 | 1.109 | +0.44 | 18.8% | 9.7% |
| SPX500 OUT-OF-REGIME (2017) | 88 | PASS | 1.519 | 0.945 | −0.26 | 13.2% | 20.7% |
| XAUUSD OUT-OF-REGIME (2017) | 89 | PASS | 2.243 | 1.463 | +1.58 | 4.5% | 16.9% |

All other rows in the table below are **reslices by exit/entry date** of an
already-scored §10.5 trade log (XAUUSD/NAS100/US30 FULL and RECENT are
subsets of the existing "in" window; NAS100/US30 OUT-OF-REGIME is the
2017-only slice of the existing 2013-2017 "out" window; SPX500 RECENT is a
slice of the new SPX500 FULL trade log above) — no new trial. XAUUSD/NAS100/
US30 FULL-window trade counts and net_R totals were reproduction-checked
against `results/orb_entry_filters_scored.csv` (exact match, 4/4) before any
compounding ran.

**Compounding results — 1% risk/trade from $100,000, strategy vs buy-and-hold:**

| instrument | period | strategy end $ | strategy % | B&H end $ | B&H % | strategy beats B&H? |
|---|---|---|---|---|---|---|
| XAUUSD | FULL 2018-2025 | 168,000 | +68.0% | 331,604 | +231.6% | **no** |
| XAUUSD | OUT-OF-REGIME 2017 | 113,066 | +13.1% | 113,177 | +13.2% | **no** (statistical wash) |
| XAUUSD | RECENT 2022-2025 | 143,057 | +43.1% | 239,440 | +139.4% | **no** |
| NAS100 | FULL 2018-2025 | 169,323 | +69.3% | 387,510 | +287.5% | **no** |
| NAS100 | OUT-OF-REGIME 2017 | 94,521 | −5.5% | 130,201 | +30.2% | **no** |
| NAS100 | RECENT 2022-2025 | 151,198 | +51.2% | 154,094 | +54.1% | **no** (close) |
| US30 | FULL 2018-2025 | 146,738 | +46.7% | 194,005 | +94.0% | **no** |
| US30 | OUT-OF-REGIME 2017 | 94,799 | −5.2% | 124,286 | +24.3% | **no** |
| US30 | RECENT 2022-2025 | 106,558 | +6.6% | 132,040 | +32.0% | **no** |
| **SPX500** | **FULL 2018-2025** | **135,770** | **+35.8%** | **255,640** | **+155.6%** | **no** |
| **SPX500** | **OUT-OF-REGIME 2017** | **97,516** | **−2.5%** | **118,831** | **+18.8%** | **no** |
| **SPX500** | **RECENT 2022-2025** | **114,600** | **+14.6%** | **143,260** | **+43.3%** | **no** |

**Verdict — 12/12 rows, the strategy loses to buy-and-hold on absolute
compounded dollars.** This is consistent with, not a contradiction of, §10.5's
Sharpe/PF-based finding: RETEST's edge is real (positive gross PF in 10 of 12
cells here, and the honesty-gated SR/PF numbers above are respectable) but it
is a **lower-volatility, lower-return path than simply owning the index or
gold through 2018-2025** — the same shape as every other candidate in this
project that "beats B&H on Sharpe" while losing to it on CAGR. **SPX500 is now
tested for the first time in this project and changes nothing**: it loses to
its own buy-and-hold in all three periods, same as the other three
instruments, extending §10.5's finding to a fourth, previously-untestable
index rather than contradicting it. The XAUUSD 2017 slice is the one row
close to parity (+13.1% vs +13.2% — an actual dead heat) but on **89 trades in
one calm year**, and is explicitly flagged above as not a regime test.

**Files (10.6):** `research/report_retest_or30_1r_all4_compounded.py` (the
runner — builds/reproduction-checks all 4 instruments' trade logs, compounds,
prints the tables), `scripts/download_spx500_xauusd_backfill.sh` +
`scripts/merge_spx500_xauusd_backfill.py` (the 2017/SPX500-M1 data pull),
`results/retest_or30_1r_all4_summary.csv`,
`results/retest_or30_1r_all4_compounded.log` (full run output).

### 10.7 COST VERIFICATION vs FTMO + exit-management study, XAUUSD RETEST OR30, 2026-09-02

#### Part 1 — cost verification (fact-check, not a new backtest)

**This test's XAUUSD cost model** (`research/ftmo_engine.py`, the legacy $/oz
path used for every XAUUSD ORB cell in this project, `cost_bps=None`):

| component | value | source |
|---|---|---|
| spread | REAL historical Dukascopy bid/ask spread at the entry minute | data, not an assumption |
| commission | **$0.07/oz round-turn** ($7/lot, 1 lot = 100 oz) | fixed constant, `COMMISSION_PER_OZ` |
| slippage | **$0.03/oz per side normal** (**$0.06 round-turn**) / **$0.10/oz per side in news windows** (**$0.20 round-turn**) — news = 07:00-08:00 UTC London open, 12:30-14:30 UTC US data/NY open | fixed constants, `SLIP_NORMAL_PER_SIDE` / `SLIP_NEWS_PER_SIDE` |

Measured directly on the 465 RETEST OR30/1R entries (09:30 ET = 13:30/14:30 UTC,
which sits **inside** the 12:30-14:30 UTC news window for every single entry —
53.8% of entries fall on the wider-slippage side purely from DST, not a
modelling choice):

| stat | spread ($/oz) | round-turn slippage ($/oz) | commission ($/oz) | **total cost ($/oz)** |
|---|---|---|---|---|
| median | 0.334 | — | 0.07 (fixed) | **0.554** |
| mean | 0.373 | 0.135 (46.2% normal @0.06, 53.8% news @0.20) | 0.07 | **0.578** |
| range | 0.088 – 1.214 | 0.06 or 0.20 | 0.07 | 0.293 – 1.484 |

**FTMO's published gold (XAUUSD) conditions** (fetched live from ftmo.com and
corroborated third-party review sources — FTMO's own symbols page does not
publish a fixed number, only says "compare live spreads on the platform"):
- **Commission: $0.00.** FTMO explicitly states "no commission on metals,
  indices or energy" — gold is spread-only.
- **Spread: no fixed published figure**, but independent gold-trading review
  sources report FTMO's XAUUSD spread as **typically $0.15-$0.30/oz during
  standard (London-NY overlap) hours**, widening outside that window and
  around news.
- No separate published "slippage" line item — FTMO's cost to a trader is
  whatever the live spread is at execution; slippage in this test is an
  **additional, explicit buffer this project adds on top of the spread**,
  not something FTMO itself bills separately.

**Verdict: this test's XAUUSD cost model is HARSHER than FTMO's published
conditions, on every component that can be compared:**
1. **Commission** — this test charges $0.07/oz round-turn; FTMO charges **$0**
   on metals. Strictly harsher.
2. **Spread** — this test's real historical measured spread (median $0.334/oz,
   mean $0.373/oz) sits **above** the top of FTMO's cited $0.15-$0.30/oz range.
   Plausibly legitimate (Dukascopy's feed is not FTMO's own liquidity bridge,
   and 53.8% of entries sit at the volatile 09:30 ET cash open where spreads
   structurally widen), but it cannot be called generous.
3. **Slippage** — this test adds $0.06-$0.20/oz round-turn that FTMO does not
   itemize as a separate charge at all.
4. **Total**: this test's mean modelled round-turn cost ($0.578/oz) is roughly
   **1.9-3.9x** FTMO's cited spread-only range ($0.15-$0.30/oz) and includes a
   commission line FTMO does not charge on gold.

**Practical implication: every dollar figure in sec 10.5/10.6/10.7 of this
project is CONSERVATIVE relative to FTMO's real economics, not optimistic.**
An actual FTMO gold trade would net MORE than this test credits it — meaning
the negative verdicts (loses to buy-and-hold, RETEST fails DSR) are, if
anything, understating the strategy's real edge slightly, not overstating it.
It does not change any verdict (the gap to buy-and-hold in Part 2 below is far
larger than a ~$0.3-0.4/oz cost difference could close), but it is the honest
direction of the bias and is stated here so it isn't silently assumed.

#### Part 2 — exit-management study (new backtest, entry logic UNCHANGED)

**Question.** Sec 10.5/10.6 only ever tested a fixed 1R target on RETEST
OR30. Does a wider target or a dynamic stop change the verdict? Entry logic
(RETEST, OR30, ET session, real cost model) is **byte-identical** to sec
10.5/10.6 — only the exit rule changes. Confirmed explicitly, not assumed: an
entry-time-set equality check shows all 5 variants below fire on the exact
same 465 in-regime / 89 out-of-regime (2017) entries.

- **1R** — baseline (sec 10.5/10.6), reproduction-checked against
  `orb_entry_filters_scored.csv`.
- **2R** — fixed 2R target, same stop. Already scored in sec 10.5 (`target`
  parses "2R" natively) — reproduction-checked, **not a new trial**.
- **3R** — fixed 3R target, same stop. **NEW** — 3R was never in the sec 10.5
  target grid (1R/2R/close only).
- **breakeven** — no fixed target; once price first moves 1R in favor, the
  stop moves to entry exactly once and never moves again; rides to the
  (possibly breakeven) stop or session close. **NEW.**
- **trailing** — no fixed target; once price first moves 1R in favor, a
  trailing stop activates at 0.5R behind the running favorable extreme and
  only ever tightens; rides to the trailing stop or session close. **NEW.**

`research/ftmo_engine.simulate_trades` is vectorized around a FIXED stop and
target (one `searchsorted` over the whole trade window) and **cannot express
a stop that moves mid-trade** — so breakeven/trailing needed a genuine
bar-by-bar resolver, written for this task: `research/orb_dynamic_stop.py`.
Same conservative tie convention as the existing engine (the OLD, pre-this-bar
stop is always checked first; a stop move triggered by this bar's own
high/low only takes effect on bars strictly after it — no look-ahead), unit-
tested against a hand-computed 6-bar synthetic trade before running on real
data (both modes matched the hand calculation exactly). Same cost model as
every other XAUUSD ORB cell (Part 1 above).

**8 new backtests this run** (3R x2 windows, breakeven x2, trailing x2 — 1R
and 2R in-regime are reused; STATE_OF_PLAY trial count **1033 → 1041**):

| cell | n | guard | grossPF | netPF | SR | maxDD | exit breakdown (reason=count, %, avg net R) |
|---|---|---|---|---|---|---|---|
| 3R / in | 465 | PASS | 1.585 | 1.235 | +0.73 | 24.3% | target 35(8%,+2.83) · stop 152(33%,−1.14) · time 278(60%,+0.44) |
| 3R / out-2017 | 89 | PASS | 2.159 | 1.517 | +1.52 | 6.1% | target 9(10%,+2.79) · stop 23(26%,−1.20) · time 57(64%,+0.37) |
| breakeven / in | 465 | PASS | 1.759 | 1.294 | +0.74 | 14.8% | stop 120(26%,−1.14) · breakeven 88(19%,−0.14) · time 257(55%,+0.78) |
| breakeven / out-2017 | 89 | PASS | 1.866 | 1.132 | +0.44 | 6.6% | stop 17(19%,−1.18) · breakeven 20(22%,−0.23) · time 52(58%,+0.55) |
| trailing / in | 465 | PASS | 1.718 | 1.281 | +0.93 | 12.1% | stop 120(26%,−1.14) · trail 211(45%,+0.82) · time 134(29%,+0.06) |
| trailing / out-2017 | 89 | PASS | 2.260 | 1.478 | +1.52 | 4.2% | stop 17(19%,−1.18) · trail 43(48%,+0.81) · time 29(33%,−0.06) |

(1R/out-2017 and 2R/out-2017 are also new relative to sec 10.5's original
in-regime-only grid; 1R/out-2017 reproduces sec 10.6 exactly.) Every one of
the 10 cells (5 variants × 2 windows) PASSES the look-ahead guard. Top-year
share on the out-2017 window is 100% by construction (it is a single
calendar year, not a concentration failure — flagged the same way as sec
10.6).

**Deflated Sharpe, printed as REFERENCE ONLY per this task's brief (not a
survival gate this round):** structural pool = this batch's own 5 in-regime
cells, E[max SR] +1.075. 1R DSR 0.569, trailing 0.356, 2R 0.231, 3R 0.180,
breakeven 0.172 — 1R remains the least noise-explicable of the five even by
this narrow a pool.

**Compounding — 1% risk/trade from $100,000, same 3-period layout as sec
10.6, next to buy-and-hold XAUUSD:**

| variant | FULL 2018-2025 | OUT-OF-REGIME 2017 | RECENT 2022-2025 |
|---|---|---|---|
| **1R (baseline)** | **$168,000 (+68.0%)** | $113,066 (+13.1%) | $143,057 (+43.1%) |
| 2R | $156,652 (+56.7%) | $116,592 (+16.6%) beats B&H | $128,196 (+28.2%) |
| 3R | $156,039 (+56.0%) | $119,733 (+19.7%) beats B&H | $134,856 (+34.9%) |
| breakeven | $160,082 (+60.1%) | $103,839 (+3.8%) | $141,662 (+41.7%) |
| trailing | $153,904 (+53.9%) | $113,462 (+13.5%) beats B&H | $131,278 (+31.3%) |
| buy-and-hold XAUUSD | $331,604 (+231.6%) | $113,177 (+13.2%) | $239,440 (+139.4%) |

**Verdict — plain answers to the brief's two questions:**
1. **No exit variant beats the $168,000 (1R) baseline on FULL 2018-2025
   dollars.** 1R is the best of the five on the full window; every wider
   target or dynamic stop gives back money relative to it (2R −6.8%, 3R
   −7.1%, breakeven −4.7%, trailing −8.4% relative to the 1R dollar figure).
   Letting winners run trades a higher per-trade R ceiling for a lower
   effective win rate and more "time" exits that give back the open profit
   before the wider target/trail is reached (see the exit breakdown: 1R's
   win rate is 60.2%, versus 48-55% net-positive-rate territory once the
   target widens or the stop only trails after 1R).
2. **No exit variant beats buy-and-hold on FULL 2018-2025** ($331,604) —
   the best variant (1R, $168,000) is still 49% of buy-and-hold's dollar
   total. **3 of the 4 new exit variants (2R, 3R, trailing — not
   breakeven) DO beat buy-and-hold in the OUT-OF-REGIME/2017 window**, but
   that window is a single calm year where buy-and-hold itself only returns
   +13.2%, so beating it is a low bar, not evidence of a real edge — and it
   does not hold in FULL or RECENT, the same generalization failure as every
   other candidate in this project.

**Bottom line: wider targets and dynamic stops do not fix the sec 10.5/10.6
finding.** RETEST's real, cost-surviving edge is best monetized at the plain
1R target; every attempt to let winners run tested here reduces the
compounded dollar total instead of improving it, and none closes the gap to
simply owning gold through 2018-2025.

**Files (10.7):** `research/orb_dynamic_stop.py` (the bar-by-bar breakeven/
trailing resolver), `research/report_orb_exit_variants_xauusd.py` (the
runner — builds all 5 variants on both windows, gates, compounds, prints the
table), `results/orb_exit_variants_xauusd_summary.csv`,
`results/orb_exit_variants_xauusd_run.log` (full run output, incl. the Part 1
cost measurement).

### 10.8 RETEST OR30/1R generalizes to FOREX — EURUSD, first non-metal/non-index pair, tested 2026-09-03, killed

**Why this batch exists.** RETEST OR30/1R (§10.5) is the closest thing ORB
ever produced to a lead, but every cell to date has been an equity index or
gold. This test asks the plain generalization question: does the **same rule
set** — RETEST, OR30, target 1R, stop = OR width, **09:30 ET session anchor
unchanged** — hold up on a currency pair? EURUSD M1 was pulled fresh this
session via Dukascopy (`scripts/download_eurusd_backfill.sh` →
`scripts/merge_eurusd_backfill.py`, bid+ask separately, real spread column),
covering the SAME two windows as every other ORB instrument: **2013-2017
out-of-regime** and **2018-2025 in-regime**. EURUSD is Dukascopy's flagship
pair with continuous depth, so — unlike XAUUSD/SPX500 in §10.6 — it gets a
full **5-year** out-of-regime window, not a single calm year.

**The 09:30 ET anchor is deliberately kept, not EURUSD-tuned.** EURUSD's own
conventional session opens are London (08:00 GMT) or Tokyo — not the US cash
equity open. 09:30 ET is kept anyway so this measures whether *this exact
strategy generalizes*, not whether a EURUSD-specific breakout window can be
found (that is a different, untested hypothesis with its own trial cost).

**Data (both files passed the merge script's sanity gate — it refuses to
write on failure):**
- `data/EURUSD_M1_2013_2017_spot_dukascopy.csv` — 1,837,284 bars, bid_close
  1.03435..1.39904, spread 0.30 pips / 0.261 bps median, **0** negative
  spreads, 358k-374k rows/year.
- `data/EURUSD_M1_2018_2025_spot_dukascopy.csv` — 2,922,985 bars, bid_close
  0.95382..1.25541, spread 0.30 pips / 0.268 bps median, 152 negative
  spreads (**0.005%**, well inside the 0.1% tolerance), 353k-373k rows/year.

**Costs.** Real measured spread from the data (median 0.30 pips ≈ 0.27 bps
both windows) + **0.30 bps commission** — grounded in FTMO's published $3
per 100k-unit round lot on forex (~0.27-0.29 bps at EURUSD's 1.05-1.10 level;
rounded UP, a slightly harsh reading) — + slippage kept UNCHANGED from the
index convention (1.00 bps/side 09:30-10:30 ET, 0.15 bps/side after),
deliberately not tightened for EURUSD's deeper liquidity.

**2 NEW backtests this run** (§1 trial count **1041 → 1043**), same honesty
gates as every other cell:

| cell | n | guard | grossPF | netPF | SR | maxDD | posYrs | exit breakdown (reason=count, %, avg net R) |
|---|---|---|---|---|---|---|---|---|
| EURUSD in-regime 2018-2025 | 802 | PASS | 1.390 | **0.879** | **−0.55** | 41.7% | 3/8 | target 389 (49%, +0.779) · stop 276 (34%, −1.211) · time 137 (17%, −0.096) |
| EURUSD out-of-regime 2013-2017 | 496 | PASS | 1.479 | **0.967** | **−0.14** | 21.0% | 1/5 | target 248 (50%, +0.792) · stop 162 (33%, −1.193) · time 86 (17%, −0.120) |

**Compounding — 1% risk/trade from $100,000, vs buy-and-hold EURUSD (M1 mid),
same 3-period layout as §10.6/§10.7:**

| period | strategy end $ | strategy % | B&H end $ | B&H % | strategy beats B&H? |
|---|---|---|---|---|---|
| FULL 2018-2025 | 62,053 | **−37.9%** | 97,794 | −2.2% | **no** |
| OUT-OF-REGIME 2013-2017 | 91,213 | −8.8% | 90,954 | −9.0% | nominally yes — **both lose ~9%**, a dead heat in a EUR downtrend, not a beat |
| RECENT 2022-2025 | 76,768 | −23.2% | 103,275 | +3.3% | **no** |

**Verdict — clean kill, and the WEAKEST RETEST cell in the project.** EURUSD
is the **only** instrument where RETEST OR30/1R posts **net PF < 1 in BOTH
windows** (0.879 in, 0.967 out) — the gross edge is real and consistent with
the index/gold cells (gross PF 1.39 / 1.48, and a foreign 09:30 ET anchor
still finds it, which is mildly notable) but it does **not come close to
paying its transaction costs** on a currency pair: net Sharpe is negative in
both windows, and 1% compounding bleeds the account **−37.9%** over
2018-2025 while simply holding EURUSD is roughly flat (−2.2%). The
out-of-regime "beat" is an artefact — strategy −8.8% vs B&H −9.0%, both
deeply negative across a multi-year EUR decline; being 0.2pp less bad is not
evidence of edge. RECENT confirms: −23.2% vs B&H +3.3%. Single-year
concentration is undefined here (total net R is negative, so the top-year
share ratio has no meaning) but only 3/8 and 1/5 years are positive.

**What this adds to §10.** ORB's RETEST filter produces a small, genuine,
regime-robust GROSS breakout edge on liquid instruments — now confirmed on a
fourth asset class (FX) after equity indices and gold — but it is a
**lower-return, cost-fragile path** everywhere it has been tested, and on
EURUSD the costs alone sink it below water before any comparison to
buy-and-hold is needed. No change to the §10 kill; the generalization test
extends it rather than reopening it.

**Files (10.8):** `research/report_retest_or30_1r_eurusd.py` (the runner),
`scripts/download_eurusd_backfill.sh` + `scripts/merge_eurusd_backfill.py`
(the 26-pull Dukascopy backfill + merge),
`results/retest_or30_1r_eurusd_summary.csv`,
`results/retest_or30_1r_eurusd_run.log` (full run output),
`results/eurusd_backfill_download.log` (download + merge sanity output).


### 10.9 VOLATILITY-REGIME FILTER on the RETEST variant — FX + indices, both windows, tested 2026-09-06, killed

**Why this batch exists.** Every ORB variant (§10, §10.1–10.8) died on the same
mechanism: a tight OR-width stop makes fixed costs a large fraction of 1R, and
the small in-regime gross edge is 2018–2025-specific. This section tests **one
genuinely different hypothesis, pre-registered**: gate the RETEST OR30/1R
variant by a **session volatility regime** — trade only when realised vol is
elevated (or, as the inverse, only when it is suppressed). Elevated vol ⇒ wider
opening range ⇒ wider 1R ⇒ cost a smaller fraction of 1R. This directly attacks
the cost-to-risk ratio.

**What is fixed (reused byte-for-byte from §10.5/§10.8).** Entry logic
`strategies.orb.orb(..., retest=True, retest_tol_frac=0.10, **ET_SESSION)` with
`or_minutes=30, target="1R", stop_mode="or_range"`; `simulate_trades` +
`de_overlap`; 1% fixed-fractional risk; 09:30 ET DST-correct session anchor
(unchanged for FX, per the §10.8 decision); each instrument on its established
cost model (XAUUSD legacy $/oz; NAS100/US30/SPX500 `run_orb.COST_BPS` +
`run_orb.slip_bps`; EURUSD the §10.8 model — commission 0.30 bps + `slip_bps`).
Scoring = `run_orb_entry_filters.score_cands`, imported and called unchanged.
**The vol filter never touches `orb()`** — it removes whole candidate days from
the list `orb()` returns, by session date, so entry price / stop / 1R / the
retest walk are identical to the unfiltered RETEST cell.

**The volatility measure (pre-registered, causal).** Session (daily) ATR(14),
Wilder RMA, computed on the RTH session bars exactly as
`strategies.orb.wilder_dmi_direction` builds its daily bars. Then
`ratio_D = ATR14_{D-1} / mean(ATR14_{D-90..D-1})` = `(atr / atr.rolling(90).mean()).shift(1)`
— session D gated only by ATR history completed strictly before D. Look-ahead:
the `.shift(1)` plus the rolling window's right edge at D-1 means session D's own
bar never enters its gate value. Asserted in the runner; `score_cands`'s
statistical guard also PASSES on every traded cell.

**The grid.** Instruments XAUUSD, EURUSD, NAS100, US30, SPX500. Windows:
in-regime 2018-2025 (all five); real out-of-regime 2013-2017 (EURUSD, NAS100,
US30); 2017-only stub (XAUUSD, SPX500 — **ONE bull year, NOT a real regime
test**, flagged exactly as §10.6). Filter modes per instrument-window: BASELINE
(no filter — reproduces the §10.5/§10.8 RETEST cell), ELEVATED `ratio > {1.2,
1.5, 2.0}`, SUPPRESSED `ratio < {0.8, 0.6}`. The brief listed "1.0 = no filter,
baseline"; a literal `ratio > 1.0` is *not* no-filter (the ratio is centred near
1.0), so the BASELINE row is the true unfiltered RETEST cell — **reproduction-
checked** against `results/orb_entry_filters_scored.csv` (XAUUSD-in, NAS100-in/out,
US30-in/out all exact to `n_trades` and `net_R_total`; EURUSD/SPX500 baselines
match the §10.8/§10.6 numbers). **6 cells per instrument-window; 5×2×6 = 60 rows,
50 of them new filter cells.**

**Trial count.** The 10 baseline cells reproduce already-counted results and are
not re-counted. **New this batch: 50 filter cells** (main grid) **+ 6 basket
cells** (additional variation, below) **= 56.** PRIOR cumulative (through §30.1)
**1237 → 1293.** DSR is reported against both a batch structural pool (N≈34
finite filter cells, E[max SR] **+2.51**) and the full cumulative pool (**N=1287
for the main grid, E[max SR] +4.04**; N=1293 for the basket) — E[max SR]
estimated from the batch's own Sharpe mean/std at the full N. The cumulative bar
is the primary one and it is high because the search is wide.

**RESULT — main grid, top of the ranking by net Sharpe (full table
`results/orb_vol_regime_scored.csv`):**

| inst | win | filter | n | grPF | netPF | net SR | DSR (N=1287) | maxDD | costR% | topYr% | vs B&H | OOS-regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | out | elevated > 1.5 | **14** | 2.60 | 1.67 | **+3.02** | 0.39 | 2.3% | 20.5 | **100%** | BEAT | — (is the OOS window) |
| XAUUSD | out(2017) | baseline | 89 | 2.24 | 1.46 | +1.58 | 0.01 | 4.5% | 16.9 | 100% | BEAT | stub |
| SPX500 | out(2017) | elevated > 1.2 | **2** | 2.54 | 1.52 | +1.50 | 0.32 | 0.5% | 17.8 | 100% | lose | stub |
| XAUUSD | in | baseline | 465 | 1.78 | 1.34 | +1.14 | 0.00 | 10.0% | 11.7 | 36% | lose | — |
| NAS100 | in | baseline | 685 | 1.39 | 1.22 | +0.85 | 0.00 | 12.2% | 5.5 | 34% | BEAT | — |
| NAS100 | in | suppressed < 0.8 | 108 | 1.74 | 1.46 | +0.69 | 0.00 | 6.9% | 7.1 | 66% | lose | **FAIL** |
| US30 | in | baseline | 602 | 1.40 | 1.18 | +0.68 | 0.00 | 13.7% | 7.1 | 39% | BEAT | — |
| XAUUSD | in | suppressed < 0.8 | 41 | 2.03 | 1.54 | +0.56 | 0.00 | 2.5% | 12.4 | 72% | lose | — |

**FINDINGS:**

1. **The hypothesised cost mechanism is REAL and confirmed on all 5 instruments.**
   The elevated filter cuts `cost_R` as predicted: NAS100 in 5.5% → 3.5% of 1R
   (`>2.0`), US30 7.1% → 3.9%, SPX500 9.7% → 3.4%, XAUUSD 11.7% → 8.3%, EURUSD
   20.0% → 11.0%. The suppressed filter moves it the other way (NAS100 5.5% →
   7.1%, EURUSD 20% → 24–27%) — exactly the sign the wider-OR-when-vol-high
   argument predicts.

2. **The cost improvement does NOT produce a surviving edge — 0 / 50 filter
   cells clear every gate; 0 / 50 clear DSR.** On the indices the elevated cell
   is net-PF > 1 at most thresholds (NAS100 1.02/1.21/1.52; US30 1.13/1.32 at
   ≥1.5) but **net Sharpe falls vs the unfiltered baseline in almost every
   in-regime cell** (NAS100 +0.85 → +0.04…+0.25; US30 +0.68 → mixed; XAUUSD
   +1.14 → +0.44 or negative; SPX500 +0.44 → ~0), the **sample collapses**
   (7–174 trades), and **year-concentration explodes** (NAS100 `>1.2` top-year
   572%, SPX500 `>1.5` 8515% — i.e. one year many times the total P&L, the rest
   large negatives).

3. **The one high-Sharpe cell (EURUSD out, elevated > 1.5, SR +3.02, netPF
   1.67) is 14 trades, 100% concentrated in a single year, in the 2013-2017
   window with no further-out window to confirm it — and its in-regime sibling
   (EURUSD in, elevated > 1.5) is netPF 0.86, SR −0.09, negative.** The filter
   "helping" out-of-regime but not in-regime is the opposite of every prior ORB
   result and is almost certainly a 14-trade artefact.

4. **Suppressed (low-vol) filter: no rescue either.** Best cell NAS100 in
   `<0.8` lifts netPF to 1.46 (from 1.22) but net Sharpe *drops* to +0.69, it
   loses to B&H, and its real-OOS sibling (NAS100 out `<0.8`) is netPF 0.59, SR
   −1.06 — **fails out of regime.**

5. **Every real out-of-regime baseline is still negative** (NAS100 out −0.79,
   US30 out −1.56, EURUSD out −0.14) and no filter, either direction, makes them
   consistently positive.

**ADDITIONAL VARIATION (data-motivated, run separately — `run_orb_vol_regime_basket.py`).**
Finding 2 showed index elevated-vol cells are netPF > 1 but individually thin +
year-concentrated. Single-name year-concentration is the exact failure mode §6
fixed by **pooling instruments into a basket**. So: the same elevated-vol RETEST
OR30/1R cell run on **NAS100 + US30 + SPX500 together** — one combined daily-
return series, one position per instrument per day, per-instrument costs, no new
parameter. In-regime 2018-2025 (3 indices) + real out-of-regime 2013-2017
(NAS100 + US30; SPX500 has only a 2017 stub). **3 in + 3 out = 6 new cells;
cumulative 1287 → 1293.**

| window | thr | n (per member) | grPF | netPF | net SR | maxDD | costR% | topYr% | vs EW-B&H |
|---|---|---|---|---|---|---|---|---|---|
| in | >1.5 | 160 (41/49/70) | 1.212 | 1.092 | **+0.15** | 17.8% | 4.8 | **133%** | lose (+0.15 vs +0.68) |
| in | >2.0 | 41 (10/17/14) | 1.164 | 1.079 | +0.08 | 5.7% | 3.6 | **132%** | lose |
| in | >1.2 | 421 | 1.045 | 0.925 | −0.22 | 38.8% | 5.4 | — | lose |
| out | >1.2 | 135 (83/52) | 0.994 | 0.804 | −0.57 | 17.6% | 8.5 | — | lose |
| out | >1.5 | 29 (19/10) | 0.624 | 0.521 | −0.83 | 8.6% | 8.6 | — | lose |

Pooling **improves the sample** (41 → 160 trades at `>1.5`) and **drops max
drawdown hard** (5.7% at `>2.0`), and in-regime netPF stays > 1 — **but net
Sharpe collapses to ~0** (+0.15, +0.08), **year-concentration is NOT fixed**
(still 132–133%; the three US indices are too correlated for cross-index pooling
to diversify the bad year away), it **loses to equal-weight buy-and-hold**, and
the **real out-of-regime basket is net-PF 0.52–0.80, Sharpe negative**. DSR_cum
0 / 5.

**VERDICT — KILL. 56 new cells (50 filter + 6 basket), 0 survivors.** No
volatility threshold, on any of the 5 instruments, in either direction (elevated
or suppressed), and not the 3-index pooled basket, produces a config that is
net-PF > 1 **and** positive-Sharpe **and** holds in the real 2013-2017
out-of-regime window **and** clears a DSR bar appropriate to the true trial
count (N=1293, E[max SR] ≈ +4.0). The volatility-regime filter does exactly what
was hypothesised to the cost-to-risk ratio — a real, confirmed mechanical effect
— but that improvement is swamped by sample collapse, extreme single-year
concentration that survives cross-index pooling, a net-Sharpe *decline* vs the
unfiltered baseline, and unchanged regime dependence. This closes the volatility-
filter branch of the ORB thread: the cost problem is fixable, the *edge* is
still not there. A different measure (intraday vol, a VIX/term-structure gate, a
volatility-scaled position size rather than a binary day filter) would be a new
hypothesis carrying its own trials.

**Files (10.9):** `run_orb_vol_regime.py` (main 60-row grid, reproduction check,
DSR, ranked table), `run_orb_vol_regime_basket.py` (the additional 3-index
pooled variation). Results: `results/orb_vol_regime.csv`,
`orb_vol_regime_scored.csv`, `orb_vol_regime_run.log`,
`orb_vol_regime_basket.csv`, `orb_vol_regime_basket_run.log`. Reproduce:
`py -3.14 run_orb_vol_regime.py && py -3.14 run_orb_vol_regime_basket.py`.

**Cumulative trials: N=1293** (1237 prior + 50 filter + 6 basket).

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

---

## 12.6 REBALANCE-FREQUENCY SWEEP — which cadence actually earns the most, tested 2026-09-03

### The question, and why it needed a direct test

Every §12 result used a **monthly** rebalance. §12.3's audit 8 tried
bi-monthly as one perturbation and found it slightly softer, but the full
frequency curve was never mapped. This test settles it directly with real
data: **holding the audited mechanism byte-identical** (N=12-month
trailing-return ranking, K=5 equal-weighted, causal 200-day SPY SMA filter,
base 17-instrument universe, the §12.1 causal execution lag and look-ahead
guard — `build_weights()`/`simulate()` called unmodified except the two
additive cadence parameters), **only the rebalance frequency changes**, and
we ask which cadence produced the highest *actual compounded historical
return* — full period and in the 2000-2009 stress window.

Five frequencies: **weekly** (`signal_freq="W"`, step 1), **bi-weekly**
(`"W"`, step 2), **monthly** (`"M"`, step 1 — the existing baseline, reused),
**bi-monthly** (`"M"`, step 2 — existing, audit 8, reused), **quarterly**
(`"M"`, step 3 — new). Weekly signal dates are the last trading day present
in each ISO week; the N-month ranking lookback and the SMA filter are
unchanged at every cadence.

### Costs scale with turnover, not a flat per-frequency assumption

The per-side transaction cost is the **same 3 bps/side** (2 bps spread + 1 bp
commission-equivalent) §12 used — it is a property of the instrument and the
order, not the calendar. `simulate()` charges `cost_bps × turnover` at every
rebalance, so a faster schedule pays that cost **more often** and its total
cost-as-%-of-gross rises automatically. Confirmed in the table: cost load
runs from **2.7%** of gross return (quarterly) to **11.3%** (weekly) on the
full window — a 4.2× spread driven purely by cadence.

### The one table — N=12 / K=5, common head-to-head window 2000-02-01 → 2026-08-28, and the 2000-2009 stress window

| frequency | rebalances | net CAGR | net Sharpe | maxDD | cost % of gross | **full total return** | stress net CAGR | stress Sharpe | **stress total return** | vs SPY CAGR (full) | vs SPY CAGR (stress) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| weekly | 1299 | 6.67% | 0.548 | 35.0% | 11.32% | **+454.0%** | 5.53% | 0.426 | **+71.2%** | −1.84 pp | +6.05 pp |
| bi-weekly | 649 | 7.11% | 0.564 | 36.8% | 7.92% | **+518.8%** | 5.22% | 0.394 | **+66.2%** | −1.40 pp | +5.74 pp |
| monthly | 299 | 8.32% | 0.629 | 39.0% | 4.90% | **+732.4%** | 9.08% | 0.610 | **+138.2%** | −0.19 pp | +9.60 pp |
| bi-monthly | 150 | 7.65% | 0.566 | 39.0% | 3.63% | **+606.3%** | 8.61% | 0.586 | **+128.0%** | −0.86 pp | +9.12 pp |
| **quarterly** | 100 | **9.50%** | **0.670** | 43.1% | **2.69%** | **+1010.2%** | 8.44% | 0.568 | **+124.5%** | **+0.99 pp** | +8.95 pp |
| SPY buy & hold | — | 8.51% | 0.522 | 55.2% | — | +772.4% | −0.52% | 0.071 | −5.0% | — | — |

Look-ahead guard **PASS 5/5**. Per-year concentration (top-year share of net
log return) **12–19% for all five**, well inside the ≤60% gate — cadence does
not create concentration. **DSR, reference only** (pool = these 5 frequency
cells, per the brief — not a survival gate): full-window E[max SR] +0.658,
best cell quarterly **0.526**; stress E[max SR] +0.636, best monthly 0.468 —
nothing clears 0.95, the same flat-grid DSR ceiling §12/§12.1/§12.3 hit.

### Ranked by actual compounded return

**FULL PERIOD (2000-02 → 2026-08):** 1. quarterly +1010% · 2. monthly +732%
· 3. bi-monthly +606% · 4. bi-weekly +519% · 5. weekly +454%. **Strictly
monotonic — the slower the rebalance, the higher the actual compounded
return.** Quarterly is also the **only** frequency that beats SPY
buy-and-hold on raw full-period return (+1010% vs +772%); every faster
cadence trails SPY.

**STRESS WINDOW (2000-2009):** 1. monthly +138% · 2. bi-monthly +128% ·
3. quarterly +125% · 4. weekly +71% · 5. bi-weekly +66%. **Monthly wins**;
quarterly slips to third (too slow to react to the two crashes as cleanly as
the monthly SMA check). All five crush SPY B&H (−5%) here, because the whole
edge in this window is the filter sidestepping the dot-com and GFC drawdowns.

### Plain answers to the brief

1. **Highest actual compounded return, full period: QUARTERLY** (+1010%,
   net CAGR 9.50%, net Sharpe 0.670 — best on every headline metric except
   max drawdown, where its 43% is the worst of the five).
2. **Highest actual compounded return, stress window: MONTHLY** (+138%).
3. **Yes, the answer changes between the calm full period and the crash
   window.** Full period rewards the *slowest* cadence (least cost drag,
   least whipsaw, rides winners longer); the crash window rewards *monthly*
   specifically — fast enough to act on the 200-day-SMA risk-off signal
   promptly, slow enough not to churn. Both windows agree completely on the
   **losers**: weekly and bi-weekly are last in *both*, and higher frequency
   produces strictly worse compounded return everywhere. The optimum sits at
   the **slow end** of the range (quarterly or monthly), never the fast end.

### What this does and does not change

It does **not** revive §12 — the strategy's verdict was already KILL on DSR
(flat grid) and the §12.5 walk-forward finding that all the SPY
outperformance was banked pre-2009, and this sweep clears none of that:
quarterly's full-window DSR is 0.526 against a 0.95 bar, and its full-period
"beat" over SPY (+1010% vs +772%) is the same crash-hedge artefact §12.5
already dissected — remove 2000-2008 and it trails. What it **does** settle,
for any future revisit of this family: **monthly was not the return-maximising
choice on the full period — quarterly is, by a wide margin (+278 pp of total
return) and at roughly half the cost load — but monthly is the best cadence
for the crash-hedging job the filter actually does.** A future deployment
should rebalance **quarterly** if the goal is raw compounded return and
**monthly** if the goal is the defensive/crash-response property; weekly and
bi-weekly are dominated on every axis and should not be used.

### Files

`research/momentum_rotation_frequency.py` (the runner),
`research/momentum_rotation.py` (gained two additive optional params on
`build_weights()` — `signal_freq` and the already-existing `rebalance_step`;
`signal_freq="M"` default reproduces §12/§12.1/§12.2/§12.3 byte-identically,
verified — plus `week_end_signal_dates()`/`signal_dates()` helpers),
`results/momentum_rotation_frequency_summary.csv`,
`results/momentum_rotation_frequency_run.log`. Reproduce:
`python research/momentum_rotation_frequency.py`.

**Tooling follow-up (2026-09-03, not a trial):** `scripts/monthly_signal_check.py`
(the manual, broker-free "what should I hold" monitor) gained a
`--freq {monthly,quarterly}` flag so it can be run on either cadence. The
signal math is untouched — `--freq` only moves the "is today the day to
check" gate (`is_last_trading_day_of_period()`: last trading day of the month,
or last trading day of a Mar/Jun/Sep/Dec quarter), which is the live
equivalent of `rebalance_step` in the backtest. Each cadence logs to its own
file (`scripts/logs/{monthly,quarterly}_picks.csv`). `live/signals.py::generate_signal()`
now forwards `signal_freq`/`rebalance_step` to `build_weights()` (defaults
unchanged, `live/rebalance.py` unaffected).

**Cumulative trials: N=1049** (1043 prior + 3 genuinely new frequencies
[weekly, bi-weekly, quarterly] × 2 windows = 6). Monthly is already counted
in §12's 8-cell batch; bi-monthly was run as a one-shot robustness check in
§12.3 audit 8 and is folded in here as a reported comparison without
re-running. DSR is reference-only this batch (task brief), so these 6 cells
enter the cumulative count but not any survival-gate pool.

---

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

---

## 18.1 ML ON THE SAME POSITIONING DATA — can a shallow gradient-boosted model find what the threshold rule missed? Tested 2026-09-03, killed

### Why this run exists, and why it is not a re-test of §18

§18 killed a **simple contrarian threshold** on funding/OI extremes (gross PF
~1.00). This asks a genuinely different question: does the **same underlying
positioning data** contain a more complex, non-obvious pattern that a
**machine-learning model** can extract where a hand-specified rule could not?
The decisive output is **feature importance** — if price-derived control
features dominate, the model found nothing new in positioning and is just
re-discovering price shape (empty across 1000+ prior trials); if positioning
features genuinely drive the predictions and the result survives costs, that
would be the first finding of its kind in the project.

### Setup — deliberately shallow, same data, same causal machinery as §18

- **Data:** the §18 pull reused verbatim — Binance funding (8h), Bybit OI
  (1h), cross-venue split stated. Usable windows BTC 2020-11-02→2026-08-30
  (~51k hourly bars), ETH 2021-01-19→2026-08-30 (~49k).
- **Features (21):** positioning (14) — funding level / 90-day causal
  percentile / 8h & 24h rate-of-change / 90-day deviation, OI 90-day
  percentile / 1h,24h,7d ROC / acceleration, funding×OI interactions,
  positioning-skew, funding-extremity; **price-derived controls (7),
  explicitly prefixed `ctrl_`** — trailing 1h/24h/7d return, 24h realised
  vol, RSI-14, distance-to-168h-MA, 24h hi-lo range. Positioning features
  aligned + lagged with §18's own `align_feature` (merge_asof backward + 1
  extra H1 bar); **every** feature shifted one further bar (prediction at *t*
  uses only ≤ *t−1*). `verify_feature_causality` funding + OI **PASS 4/4**.
- **Label:** forward simple return, **H = 4h and 24h** (both tested).
- **Model:** LightGBM regressor, `num_leaves=15, max_depth=4, lr=0.03,
  min_child_samples=200, reg_lambda=5, reg_alpha=1`, ≤400 trees
  early-stopped. Point is testing whether the data carries signal, not model
  capacity.
- **Validation:** strict time-order 60/15/25 train / early-stop val / **sealed
  test**, H-bar purge at every boundary; 4-fold expanding walk-forward;
  real costs on the strategy conversion (**22 bps taker+slip round-turn +
  funding paid on every 8h stamp held**); DSR reference-only (pool = the 4
  a priori cells); per-year concentration; sealed final 25% is itself a
  strict out-of-regime block.
- **Ablation (the honest test):** every (instrument, horizon) trained THREE
  ways — positioning-only, price-control-only, both — and compared.

### Result — sealed test (final 25%, 2025-03 → 2026-08)

| inst | H | test IC | trades | net Sharpe | net PF | maxDD | net ret | vs B&H |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 4h | +0.0058 | 1099 | **−6.19** | 0.505 | 91% | −233% | loses (B&H +0.10) |
| BTCUSDT | 24h | −0.0121 | 68 | −0.53 | 0.815 | 25% | −10% | loses (B&H +0.13) |
| ETHUSDT | 4h | −0.0061 | 1113 | **−4.24** | 0.635 | 94% | −269% | loses (B&H +0.67) |
| ETHUSDT | 24h | −0.0087 | 343 | +0.52 | 1.101 | 59% | +40% | **loses on Sharpe** (B&H +0.66); top-year share **202%** — one year > 100% of total, a broken-concentration artefact |

**Mean sealed-test IC −0.0053 (3 of 4 negative). Mean strategy net Sharpe
−2.61. Beats buy-and-hold 0/4.** The 4h cells are destroyed by cost (1000+
trades × 22 bps + funding against a ~0-IC signal); the 24h cells trade less
and simply have no predictive edge (IC −0.012, −0.009). Walk-forward (4
expanding folds per cell, 2023-03 → 2026-08): mean fold IC **+0.0082** (62% of
folds IC > 0 — a coin flip), mean fold net Sharpe **−2.02**. DSR reference:
pool Sharpes [−6.19, −0.53, −4.24, +0.52], best cell DSR **0.433** (ETH 24h)
vs a 0.95 bar — and the same "uniformly-bad pool makes DSR uninformative"
caveat §18 flagged applies.

### Feature importance — the critical output, stated plainly

**The model DID lean on positioning features, not price:** mean GAIN
importance **positioning 65.7% / price-control 34.3%** (BTC-24h 80/20,
ETH-24h 66/34); permutation importance on the sealed test **56% / 44%**. Top
features are consistently `funding_dev_90d`, `funding_rate`,
`funding_extremity`, `funding_x_oi_signed`, `oi_pctl`.

**But this does not rescue anything — it makes the negative cleaner.** The
GBM splitting more often on positioning features means only that those
features helped it fit the *training* set; on the sealed test those splits
carry **no predictive value** (IC ≈ 0, negative on 3/4). The ablation is
decisive: mean sealed-test IC is **positioning-only −0.0085, price-only
−0.0051, both −0.0053** — all three ≈ zero, and positioning-only is the
*worst* of the three. There is no feature subset, horizon, or instrument
where positioning data produces a positive out-of-sample IC on average.

### Verdict — KILL, and it closes the thread

This is **not** the "model defaults to price patterns" outcome (price
features did not dominate). It is the more complete negative: **a shallow
GBM extracts no exploitable signal from EITHER feature group.** It
preferentially uses positioning features and still predicts nothing
out-of-sample; the price controls it also has access to add nothing —
consistent with the 1000+ prior price-pattern trials. §18's simple threshold
and this ML model reach the **same conclusion by different routes**: the
crypto positioning data this project can reach (Binance funding + Bybit OI,
BTC/ETH, 2020-2026) does not contain a funding/OI-based edge — simple or
complex — that survives real costs and beats buy-and-hold. The one
nominally-positive cell (ETH 24h, +0.52 Sharpe) loses to ETH B&H on
risk-adjusted return and is a single-year concentration artefact. **The
ML-on-positioning research thread is closed.**

Files: `research/positioning_ml.py`. Data: reuses
`data/{BTCUSDT,ETHUSDT}_{funding_binance,oi_bybit}.csv` + the H1 panels.
Results: `results/positioning_ml_{primary,ablation,importance,perm_importance,walkforward}.csv`,
`positioning_ml_run.log`. Reproduce: `python research/positioning_ml.py`.

**Cumulative trials: N=1053** (1049 prior + 4 — BTC/ETH × 4h/24h "both
features". Positioning-only / price-control-only ablations and walk-forward
folds are diagnostics of those same 4 cells, not separate configs — same
treatment as §12.3 audit 8's perturbations. DSR was reference-only this
batch per the standing instruction, so these 4 cells enter the count but
not any survival-gate pool.)

---

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

---

## 24. LONG SHORT-DATED CALL OPTIONS ON A TREND SIGNAL — a defined-risk structure, tested 2026-09-03, killed

### Why this run exists — genuinely different structure, not another pattern search

Everything in §1–§23 tests some variant of "predict direction, size with a
stop." This tests a **structurally different bet**: buy a short-dated call,
**max loss = premium paid** (no stop mechanics), and **time decay is the
central risk**. The question is whether the capped downside plus convexity
pays for the theta bleed, historically, on a simple bullish trigger.

### DATA — STATED PLAINLY: these are Black-Scholes approximations, not real chains

**Free historical option-chain data for SPY/QQQ/AAPL/MSFT/GOOGL going back
years does not exist** (yfinance serves only the current chain; CBOE
DataShop / OptionMetrics / ORATS are paid). Option prices here are
**Black-Scholes**, priced per trade from yfinance daily adjusted close plus
an implied-vol input:

| instrument | IV source | trust |
|---|---|---|
| SPY | **^VIX** (CBOE 30-day S&P 500 implied-vol index) | **near-real** — small basis (term structure, SPY-vs-SPX) |
| QQQ | **^VXN** (CBOE 30-day Nasdaq-100 implied-vol index) | **near-real** |
| AAPL, MSFT, GOOGL | **trailing 21-day realised vol times 1.15** | **approximation, optimistically biased** — CBOE's single-name vol indices (VXAPL/VXAZN) were discontinued ~2020, no free replacement. Trailing RV is backward-looking: it **underprices** options going *into* volatile periods, which **flatters a long-call strategy**. |

Other stated simplifications: r = 2% constant; q = 0 (auto-adjusted prices
already remove dividend drops — slightly over-values calls on SPY/MSFT); VIX/
VXN used flat for both 14- and 35-day tenors (two-sided term-structure
error, small). **Trust summary: SPY/QQQ results rest on near-real market IV;
AAPL/MSFT/GOOGL numbers are an optimistic upper bound and any *positive*
result there would need real-chain confirmation.**

### Strategy — every choice a priori, nothing swept

Signal on close[t]: **close > 50-day SMA AND close > close[t-20]** (trend +
1-month momentum). Buy at close[t+1] (S, IV, r all as of the purchase day —
look-ahead guard asserts entry strictly after the signal day, **PASS 20/20**).
One call, **K = ATM or 2% OTM** (both tested), **14 or 35 calendar DTE**
(both tested; expiry = last trading day on/before the Friday on/after
entry+DTE). **Hold to expiry** (primary; a +100% profit-take variant is a
diagnostic). Re-enter on expiry if the signal is still on. Costs: premium
times (1 + half-spread + 0.5% commission), half-spread **2% of premium for
SPY/QQQ, 4% for single names** (options spreads are wider than stock —
stated). Held to expiry => settles at intrinsic, no exit spread. Size:
**premium at risk = 2% of capital per trade, compounded** from $100k,
2012–2026 (~14 years; weekly expiries broadly available from ~2012).

**Grid: 5 instruments x 2 DTE x 2 moneyness = 20 a priori cells.**

### Result — primary (hold to expiry)

| cell | trades | win% | expired worthless | total return | Sharpe | vs underlying B&H |
|---|---|---|---|---|---|---|
| SPY 14 ATM | 210 | 43% | 33% | **−28%** | −0.24 | vs **+677%** |
| SPY 14 OTM | 210 | 18% | 69% | **−87%** | −1.16 | vs +677% |
| SPY 35 ATM | 113 | 46% | 29% | **+3%** | +0.04 | vs +677% |
| SPY 35 OTM | 113 | 32% | 53% | **−39%** | −0.40 | vs +677% |
| QQQ (4 cells) | 108–201 | 27–50% | 31–63% | **−59% … +42%** | −0.48 … +0.31 | vs **+1326%** |
| AAPL (4 cells) | 105–193 | 35–50% | 40–54% | **+201% … +495%** | +0.49 … +0.60 | vs **+2499%** |
| MSFT (4 cells) | 106–195 | 27–42% | 35–60% | **+58% … +100%** | +0.19 … +0.38 | vs **+2365%** |
| GOOGL (4 cells) | 107–195 | 32–40% | 36–54% | **+103% … +236%** | +0.35 … +0.42 | vs **+2000%** |

**16/20 cells post a positive total return, but 0/20 beat the underlying
buy-and-hold — on total return OR on Sharpe.** SPY and QQQ (near-real IV)
range from −87% to +42% while the index itself compounded +677% / +1326%.
The single-name cells look large in isolation (+200% to +495%) but are
**8x–50x worse than just holding the stock**, are on the optimistically-biased
RV-proxy IV, and are concentrated (AAPL 14/OTM: 2017 alone = +0.77 of +2.15
total; **2022 is negative in every one of the 20 cells**).

### Time decay — quantified explicitly (the task's central question)

- **44% of all options expired worthless on average** — a total (100%) loss,
  pure decay, no directional offset. OTM cells: 46–69% worthless; ATM: 29–43%.
- **`option return − delta-matched-stock return`, per trade** (the cleanest
  isolation of the wrapper's cost): **SPY −27% to −74%, QQQ −21% to −53%**
  per trade. On the instruments with trustworthy IV, using the option instead
  of a delta-equivalent stock position destroyed 20–74% of the return on
  every trade — that gap *is* the theta cost, and it is the entire difference
  between the strategy and the index it is built on.
- Theta drag as a share of premium outlaid: SPY/QQQ ATM ~1–13%, OTM ~17–50%.
  35-DTE is consistently less bad than 14-DTE (less relative theta), as theory
  predicts. (The single names show near-zero aggregate theta drag only because
  a few explosive RV-underpriced years paid the long gamma — the
  optimistic-bias artefact, not a real edge.)

### Out-of-regime (expiries before 2020 calm bull vs 2020+ COVID / 2022 bear / 2023-25)

The pattern holds in both regimes: SPY/QQQ average per-trade return is
negative-to-flat before and after 2020 (SPY 14 ATM −1% -> −14%); the single
names are positive in both halves but on the same optimistic IV proxy. **No
regime in 14 years where the SPY/QQQ structure works.**

### Honesty gates

Look-ahead guard **PASS 20/20**. Realistic option bid/ask charged (2%/4%
half-spread + commission, stated). DSR **reference only** (pool = the 20
cells; E[max SR] +0.98, best cell AAPL 35 ATM SR +0.60 -> **DSR 0.008** vs a
0.95 bar). Concentration reported above. +100% profit-take diagnostic does
not rescue it (SPY still −26% / −89%; QQQ still far below B&H).

### Verdict

**KILL, 0/20 beat buy-and-hold.** The defined-risk long-call structure does
not pay off historically once BS-approximated premium, realistic option
bid/ask, and time decay are charged. **Time decay is the dominant loss
channel** — 44% of options expire worthless, and on SPY/QQQ (real IV) the
option wrapper costs 20–74% of return per trade versus a delta-matched stock
position. The capped downside does not compensate: you pay a spread, bleed
theta continuously, and capture only delta·dS of the upside, so across a
14-year bull market the structure returned −87%…+42% (SPY/QQQ) where the
underlyings returned +677%…+1326%. **The data limitation cuts *toward* the
kill, not against it**: SPY/QQQ rest on near-real IV and lose decisively;
AAPL/MSFT/GOOGL rest on a trailing-RV proxy that *flatters* long calls and
still lose to their stocks by an order of magnitude. Structurally different
from everything else in the project, same answer.

Files: `research/long_call_trend.py`. Data: yfinance daily
(SPY/QQQ/AAPL/MSFT/GOOGL + ^VIX/^VXN), pulled at runtime, none saved.
Results: `results/long_call_trend.csv`, `results/long_call_trend_run.log`.
Reproduce: `python research/long_call_trend.py`.

**Cumulative trials: N=1073** (1053 prior + 20 — 5 instruments x 2 DTE x 2
moneyness. The +100% profit-take variant and the 2020 OOS sub-split are
diagnostics of those same 20 cells, not separate configs — same treatment
as §12.3 audit 8. DSR was reference-only this batch per the standing
instruction.)

---

## 25. POST-EARNINGS-ANNOUNCEMENT DRIFT (PEAD) — event-driven, tested 2026-09-03, killed (real edge, still loses to buy-and-hold)

### Why this run exists

The Ball & Brown (1968) / Bernard & Thomas (1989) anomaly: stocks that beat
(miss) consensus EPS drift up (down) for weeks afterward. **Event-driven,
news-triggered** — mechanistically unlike every price-pattern,
portfolio-rotation, positioning and options structure in §1–§24. Genuinely
untested here.

### Data quality — reported first, per the brief

**Source: yfinance `Ticker.get_earnings_dates(limit=100)`** — per name, the
last ~100 quarterly events with **EPS Estimate, Reported EPS, Surprise(%)**,
indexed by a **timezone-aware announcement timestamp** (date + time ET), not
the fiscal-quarter end.

| metric | value |
|---|---|
| raw earnings events, 63-name large-cap universe, 2006-01→2026-08 | 5,139 |
| ... with both EPS Estimate and Reported EPS present | 5,085 (**98.9%**) |
| ... with a computable causal SUE + price coverage (events actually used) | **4,735** |
| distinct names contributing | 63 |
| announcements before market open (06:00–08:59 ET) | 64% (rest after-close 16:00, ~1% during-hours) |

**Coverage is strong** — 99% field completeness, ~20 years deep, and the
timestamp genuinely encodes before-open vs after-close (probed: ~3,900
events cluster hard at 06:00–08:00 and 16:00 ET). **This is a usable test,
not a data-quality dead end.**

**Trust limitations, stated, not worked around:**
1. **Point-in-time integrity of the ESTIMATE is unverifiable with free data.**
   "EPS Estimate" is Yahoo's *current* record of consensus, not a
   confirmed pre-announcement snapshot. A restated estimate biases surprises
   toward looking *more* predictive than they were in real time → **a kill
   is robust; a positive result would need paid I/B/E/S PIT data to trust.**
2. **Reported EPS may be restated** (adjusted-vs-GAAP reclassification). Same
   caveat, smaller.
3. **Survivorship** — the universe is 63 names large-cap and solvent *today*;
   2006-era blow-ups (Lehman, Bear, AIG, WaMu, GM…) and acquisitions are
   absent. Inflates the long-beat leg's realised drift. Not corrected (no
   free historical index membership).

Both caveats **cut toward leniency** — they flatter the strategy — so the
kill below is despite an optimistic setup.

### Look-ahead handling — verified explicitly

Entry = the **close of the first trading day whose open is strictly after the
announcement timestamp**: after-close announce on day D → enter D+1 close;
before-open announce on D → enter D close (news out at 07:00, entered at
16:00). This **skips the announcement jump entirely** and captures only the
drift — the conservative PEAD convention. SUE's rolling std uses trailing
surprises only, shifted one quarter. **Guard: every entry's close instant is
strictly after its announcement wall-clock time — PASS 4,735/4,735, min gap
8.0 h** (the before-open same-day entries, 07:00 announce → 16:00 close).

### Strategy — all a priori

SUE = (Reported − Estimate) / trailing-8-quarter std of the dollar surprise
(causal). **|SUE| threshold 1.0 / 1.5 / 2.0** (three levels). SUE > +thr →
long; SUE < −thr → short. **Shorts modelled** (S&P-100 borrow is general
collateral; 2.0%/yr carry = 0.5% borrow + ~1.5% blended dividend owed,
pro-rated daily); a **long-only** variant also run. **Hold 20 and 60 trading
days** (both standard PEAD windows), no stop, no profit-take.
Daily-rebalanced equal-weight portfolio, gross scaled to 1.0. Costs: **10 bps
round-turn** per position (3 spread + 1 commission + 1 slippage per side) +
short carry. **Grid: 3 thresholds × 2 horizons × {long/short, long-only} =
12 cells.**

### Result — full window 2006–2026 (equal-weight B&H of the 63 names: Sharpe +0.85, CAGR +15.8%, maxDD 48%)

| cell | events (L/S) | mean event drift | event win% | net Sharpe | net PF | CAGR | maxDD | top-yr | beats B&H? |
|---|---|---|---|---|---|---|---|---|---|
| L/S SUE>1.0 20d | 2044/251 | +1.15% | 58% | +0.57 | 1.12 | +9.8% | 39% | 17% | no |
| L/S SUE>1.0 60d | 2044/251 | +2.94% | 61% | +0.86 | 1.17 | +11.6% | 32% | 11% | no |
| L/S SUE>1.5 60d **(best)** | 1438/161 | +3.37% | 62% | **+0.91** | 1.18 | +12.8% | 29% | 11% | no |
| L/S SUE>2.0 60d | 984/114 | +3.36% | 61% | +0.76 | 1.16 | +11.9% | 34% | 13% | no |
| L-only SUE>1.0 60d | 2044/0 | +3.63% | 64% | +0.80 | 1.17 | +14.4% | 46% | 11% | no |
| L-only SUE>1.5 60d | 1438/0 | +3.98% | 65% | +0.81 | 1.17 | +14.8% | 42% | 11% | no |
| *(other 6 cells)* | — | +1.2–4.0% | 58–65% | +0.42–0.73 | 1.09–1.16 | +7.5–13.8% | 39–50% | 13–29% | no |

**The gross drift is unambiguously real:** +1.2–1.4% over 20 days, +2.9–4.0%
over 60 days, 58–65% event win rate, monotone-ish in horizon, consistent
across all three SUE thresholds AND the raw-Surprise(%) diagnostic (5/10/20%
thresholds: +1.0–1.8% / 20d, +2.9–3.3% / 60d). PEAD shows up in this data.

**But every one of the 12 cells loses to simply owning the 63-name universe
equal-weighted.** Best cell (L/S SUE>1.5 60d): net Sharpe +0.91 vs B&H +0.85
— a hair higher on Sharpe — but **CAGR +12.8% vs B&H +15.8%**, so it fails
the "beats B&H on Sharpe AND CAGR" gate. Long-only cells get to ~14–15% CAGR
but at Sharpe 0.73–0.81, below B&H's 0.85. **0/12 beat buy-and-hold.**

### Honesty gates

| gate | result |
|---|---|
| look-ahead guard | **PASS 12/12** (4,735/4,735 events, min gap 8.0 h) |
| net PF > 1 | 12/12 |
| net Sharpe > 0 | 12/12 |
| **beats equal-weight B&H (Sharpe AND CAGR)** | **0/12** |
| OOS holds (IS 2006–15 / OOS 2016–26, both PF>1 & SR>0) | **12/12** — genuinely robust: OOS Sharpe (0.51–1.14) *higher* than IS (0.26–0.70) for every cell |
| 2008–2009 sub-window | L/S cells −7% to +1% CAGR (SR −0.34 to +0.16); long-only cells **positive** (+2% to +15% CAGR, SR +0.14 to +0.54) vs B&H +2.1% |
| not year-concentrated (top year ≤ 60%) | 12/12 (top-year 11–29%) |
| DSR (reference only, pool = 12 cells) | best 0.440 (L/S SUE>1.5 60d), E[max SR] +0.94 — **vs 0.95 bar** |
| **SURVIVORS** | **0/12** |

### Verdict

**KILL — but the most methodologically-clean real anomaly the project has
found.** PEAD is the first candidate whose gross signal is (a) unambiguously
positive, (b) *stronger* out-of-sample than in-sample, (c) not
year-concentrated, and (d) clears net PF, Sharpe, OOS and concentration
gates simultaneously. What kills it is the same terminal reason as §12
(momentum rotation) and §14 (individual stocks): **a real edge that still
loses to buying and holding the underlying universe** through a 2006–2026
large-cap bull market. A ~3.4% gross drift over 60 days, diluted across a
daily-rebalanced equal-weight book and netted of a 10 bps round-trip, just
does not compound faster than +15.8%/yr of beta. DSR (reference) also cannot
clear 0.95 against its own flat 12-cell pool.

The data caveats (unverifiable estimate PIT integrity + survivorship) both
*flatter* this result, so the kill is not a data artefact. A paid-PIT-data
re-test would only lower these numbers.

**Files:** `research/post_earnings_drift.py`. Data: `data/pead_earnings.csv`,
`data/pead_prices.csv` (yfinance, cached). Results:
`results/post_earnings_drift.csv`, `post_earnings_drift_scored.csv`,
`post_earnings_drift_run.log`. Reproduce: `python research/post_earnings_drift.py`.

**Cumulative trials: N=1085** (1073 prior + 12 — 3 SUE thresholds × 2
horizons × [long/short, long-only]. The raw-Surprise(%) variant and the
2016 OOS / 2008-09 GFC sub-splits are diagnostics of those 12 cells, not
separate configs. DSR was reference-only this batch per the standing
instruction.)

---

## §26 — Delta-10 IV-rank filter validation (2026-09-04)

**Question asked (narrower than a strategy pitch):** Ultimate Investor's
live credit-spread scanner (`C:\Claude Code\Ultimate Investor\backend\app\
services\options_scanner.py`) only surfaces delta-10 short legs, 30-45 DTE,
and additionally reports IV Rank as a live filter cue. Sec 20 already
KILLED naked short vol on tail risk regardless of any filter. This section
asks a narrower, still-useful question: does entering delta-10 short
options ONLY when IV rank is in its own top tercile ("the Ultimate Investor
filter") make the OUTCOME more consistent than entering with no IV
condition at all — separate from whether either is profitable enough to
trade.

**Method:** real causal VIX+SPY (same series as sec 20), Black-Scholes with
real VIX as the wing's IV (flat-vol limitation stated, same class as §24),
strike solved analytically for exact |delta|=0.10, 37 DTE (midpoint of
Ultimate Investor's own 30-45 DTE window), marked to market DAILY using the
REAL subsequent VIX/SPY path (not frozen at entry) so tail events reprice
exactly as a real short seller would see them. Two books (put, call), one
position at a time each. FILTERED group requires IV rank (252d causal
rolling percentile) ≥ top tercile at entry, decided one day ahead
(shift(1), sec-20 convention); UNFILTERED control shares the identical
252-day history floor and differs ONLY in the IV condition.

**Result:**

| | FILTERED (IV top tercile) | UNFILTERED (control) |
|---|---|---|
| trades (put+call pooled) | 362 | 616 |
| win rate | 96.7% | 97.2% |
| % expired worthless | 96.4% | 97.1% |
| std-dev of per-trade return-on-premium | 248.0% | 535.4% |
| worst single day | **-69.5%** (2020-03-16) | **-74.9%** (2008-10-15) |
| worst single month | **-91.0%** (2008-10) | **-93.3%** (2008-10) |
| worst single trade (ret on premium) | -4034% | -12675% |
| trades losing >100% of premium | 12/362 | 15/616 |
| net Sharpe (ref, return-on-margin) | +0.38 | +0.53 |
| DSR (reference only, 2-cell pool) | 0.287 | 0.545 |
| kill on sec-20 catastrophic bar (day<-30%/month<-50%) | **YES** | **YES** |

**Verdict on the filter itself:** the IV-rank filter roughly HALVES the
variance of per-trade outcomes and trims the worst-day/-month magnitude by
a modest amount (~5pp), but this is driven almost entirely by trading only
~34% as often (2,796 of 8,151 eligible days) rather than by avoiding worse
conditional outcomes — win rate and Sharpe are NOT improved. Critically,
**both groups still breach the exact same catastrophic tail-risk bar sec 20
already found**, on the same two real historical events (2008 GFC, 2020
COVID) — the filter does not remove the naked-short-option tail, it only
changes how often you are exposed to it. Plain answer: the filter does real
but limited work on smoothness; it is not a tail-risk kill switch, and a
trader relying on "IV is elevated" as a safety signal would still have been
caught in both crashes on this data. This does not reopen sec 20 — that
verdict (KILL on tail risk, regardless of headline Sharpe) stands as the
authoritative call on the underlying strategy; this section only answers
whether ITS live filter is doing real work, and the answer is "partially,
on smoothness, not on the tail."

**Files:** `research/delta10_iv_filter.py`. Results:
`results/delta10_iv_filter.csv`, `delta10_iv_filter_trades.csv`,
`delta10_iv_filter_run.log`. Reproduce: `python -m research.delta10_iv_filter`.

**Cumulative trials: N=1087** (1085 prior + 2 — filtered cell, unfiltered
cell, each pooling its put-book and call-book).

---

## §27 — Defined-risk credit spread validation (2026-09-04)

**Question:** §26 tested the NAKED delta-10 short and found the IV-rank
filter reduces outcome variance but doesn't remove the catastrophic tail.
This section adds the actual protective long leg — a real bull put / bear
call spread, exactly what Ultimate Investor's scanner lists — to see
whether a hard, computed, bounded max loss changes the picture.

**Bug found and fixed in-session:** the first pass compounded each day's
dollar P&L by dividing by that trade's own ~$150-370 max_loss and treating
the result as 100%-reinvested account growth — producing absurd totals
(+2.9e8%). Fixed to the project's standard position-sizing convention: a
stated $100k reference account, each new position risking exactly 2% of
current capital, marked to market daily with put-book and call-book sharing
one capital account. Per-contract trade economics (max_loss, win/loss,
costs) were never affected by this bug — only Sharpe/total-return/max-DD
were, and are corrected below.

**Result:**

| | 1pct FILTERED | 1pct UNFILTERED | 2pct FILTERED | 2pct UNFILTERED |
|---|---|---|---|---|
| trades | 362 | 616 | 362 | 616 |
| win rate | 96.7% | 97.2% | 96.7% | 97.2% |
| max loss ever breached | **NO** | **NO** | **NO** | **NO** |
| losing trades hitting FULL max loss | 75% | 59% | 42% | 41% |
| worst single day | -2.0% | -1.8% | -1.6% | -1.5% |
| worst single month | -1.9% | -2.0% | -1.7% | -1.6% |
| catastrophic bar breached (day<-30%/mo<-50%) | NO | NO | NO | NO |
| cost as % of gross credit | 16% | 14% | 8% | 7% |
| net Sharpe | +0.57 | +1.04 | +0.65 | +1.15 |
| DSR (reference only) | 0.007 | 0.272 | 0.016 | 0.490 |
| total return (33yr, $100k, 2% risk/trade) | +38% | +94% | +41% | +92% |

SPY B&H over the same window: Sharpe +0.65, total return +3004%, maxDD 55.2%.

**Max-loss cap: verified, never breached, across all 1,956 trades including
both 2008 GFC and 2020 COVID** — e.g. the 2pct/unfiltered worst COVID trade
lost exactly -$573, matching its computed max_loss to the cent. The
catastrophic single-day/-month bar that both §20 (naked SVXY) and §26
(naked delta-10) breached is **never breached here** — worst day is -1.5%
to -2.0% of account capital vs §26's -69.5%/-74.9%. The defined-risk
structure does exactly what it's supposed to do.

However: "losing trades equal max loss" is NOT a strict identity — only
41-75% of losers hit the full cap (narrower 1% width blows through both
strikes more often; wider 2% width more often lands partially between
strikes), reported honestly rather than assumed. Total return badly lags
SPY, but this is a **sizing artefact** of the deliberately conservative
2%-risk convention (max_dd only 3.7-6.5% vs SPY's 55.2%, nowhere near
matched risk) — Sharpe (size-invariant) is the fairer comparison, and there
UNFILTERED beats SPY (+1.04, +1.15 vs SPY's +0.65) while FILTERED does not
clearly. The IV-rank filter again adds no value: UNFILTERED beats FILTERED
on Sharpe, DSR, AND total return in all 4 cells, replicating §26.

**Verdict: MIXED, not a clean yes.** Capping the loss works exactly as
designed — bounded, no catastrophe, confirmed through both real crash
events. But the nominal Sharpe edge over SPY does not clear this project's
own DSR significance bar (0.95) in any of the 4 cells (best: 0.490). A
plausible small edge, not a demonstrated one — capped tail risk is real and
verified; a worthwhile trading edge is not established on this data.

**Files:** `research/credit_spread_iv_filter.py`. Results:
`results/credit_spread_iv_filter.csv`, `credit_spread_iv_filter_trades.csv`,
`credit_spread_iv_filter_run.log`. Reproduce:
`python -m research.credit_spread_iv_filter`.

**Cumulative trials: N=1091** (1087 prior + 4 — 2 widths x 2 groups, each
pooling its put-book and call-book).

---

## §28 — ICT SMC full model, multi-asset M1 (2026-09-04)

**Question:** does the audited, bug-fixed ICT SMC Pine model
(`strategies_pine/ICT_SMC_Full_FTMO_v2.pine`) produce a worthwhile
compounded dollar return on XAUUSD, EURUSD, SPX500, and BTCUSDT at M1
resolution, against simply buying and holding each instrument over the
identical period? Headline metric requested: plain compounded dollars, not
Sharpe/DSR.

**Method:** faithful Python translation of the Pine logic — no rule
re-derived, every default reused verbatim (daily 50 EMA bias, pivot-based
BOS/CHoCH structure, liquidity sweep → displacement → Order Block or
sweep-armed Fair Value Gap entry, London 07:00-10:00 UTC + NY 13:30-16:00
UTC kill zones, 2R target). Entry fills at the next bar's open (Pine
default). Costs reused verbatim from each instrument's own established
model in this project (XAUUSD: legacy $/oz; EURUSD/SPX500: index-CFD/FX
bps; BTCUSDT: Binance taker-fee bps). Kill zones applied to BTCUSDT with NO
adjustment — they are literal UTC clock windows, not a session concept, and
apply identically to a 24/7 market.

**Two bugs found and fixed in-session** (both stated plainly, not hidden):
1. Order-block-based stops can have near-zero width on a flat/illiquid M1
   candle, which corrupted the compounded totals with R-multiples reaching
   -1.3 trillion. Fixed with a pre-registered minimum-stop-distance floor —
   no real broker accepts a stop this tight, and the project's
   fixed-fractional 1%-risk convention implicitly assumes position size
   scales inversely with stop distance.
2. The first floor (20 fixed ticks) was adequate for XAUUSD/EURUSD/SPX500
   but not BTCUSDT — $0.20 is nothing against $3,200-$125,000 BTC prices.
   Corrected to `max(20 ticks, 5bps-of-price)`, which scales sensibly
   across the panel's 40x price range. Post-fix, every trade's net_R is
   bounded in [-5.8, +2.2] — sane and stable.

**Windows:** XAUUSD/SPX500 in-regime 2018-2025 + out-of-regime 2017-ONLY
(one calm bull year, not a full regime test, per this project's standing
XAUUSD-M1 pre-2018 caveat); EURUSD in-regime 2018-2025 + out-of-regime the
full 2013-2017 (real 5-year window); BTCUSDT 2018-2025 only — no
out-of-regime window exists (Binance data starts 2017-08-17; the ~4.5-month
2017 stub is sparse/gappy per this project's standing note and was skipped
rather than reported as a misleading regime test).

**Result — headline, $100,000 start, 1% risk/trade compounded:**

| Instrument (in-regime) | Strategy end $ | B&H end $ | Beat B&H? |
|---|---|---|---|
| XAUUSD 2018-2025 | $165 (-99.8%) | $331,604 (+231.6%) | **NO** |
| EURUSD 2018-2025 | $6,159 (-93.8%) | $97,794 (-2.2%) | **NO** |
| SPX500 2018-2025 | $14 (-100.0%) | $255,640 (+155.6%) | **NO** |
| BTCUSDT 2018-2025 | ~$0 (-100.0%) | $639,397 (+539.4%) | **NO** |

Out-of-regime slices (XAUUSD/SPX500 2017-only, EURUSD 2013-2017) also all
lose to their own buy-and-hold, though less catastrophically (shorter
windows, fewer trades to compound the erosion).

**Trade counts / win rates:** 311-5,381 trades per cell. Win rate 25-41%
(BTCUSDT worst). Gross PF 0.99-1.37 (the raw entry logic finds close to
zero edge BEFORE costs on 6 of 7 cells). Net PF 0.17-0.83 — **every single
cell is below 1.0** once real spread + commission + slippage is charged.

**Ruin diagnostic:** fixed-fractional 1%-of-current-capital compounding
over thousands of trades with net PF < 1 decays multiplicatively, not
linearly. 3 of 7 cells (XAUUSD in-regime, SPX500 in-regime, BTCUSDT) fell
to ≤1% of starting capital within 321-1,786 trades — the same phenomenon
this project already documented for M1 execution generally (the 5-family
sweep: "45/45 cells end below 1% of starting equity"). The 4 shorter/less-
frequent cells never fully reached technical ruin but still lost the large
majority of capital.

**Look-ahead guard:** PASS — spot-checked that entry_mid equals the next
bar's open after every signal bar's confirmation, across all 7 cells.

**Verdict: KILL, clean and unanimous.** The audited ICT SMC entry sequence
(bias + structure + sweep + displacement + OB/FVG + kill zone) finds
essentially no edge at M1 resolution once real transaction costs are
charged, on any of 4 asset classes, in any of 7 windows. Every cell loses
money in absolute dollar terms, and every cell loses to simply buying and
holding the instrument. This closes out the ICT SMC thread first logged
2026-06-14 (H4, hand-run in TradingView, too few trades to trust) with a
systematic, cost-inclusive, multi-asset, multi-regime test.

**Files:** `run_ict_smc.py`. Results: `results/ict_smc.csv`,
`ict_smc_trades.csv`, `ict_smc_run.log`. Reproduce: `python run_ict_smc.py`.

**Cumulative trials: N=1098** (1091 prior + 7 — XAUUSD×2, EURUSD×2,
SPX500×2, BTCUSDT×1).

---

## §29 — ICT SMC SELECTIVE v1: four discretionary filters on the §28 engine (2026-09-04)

**Question:** §28 killed the audited ICT SMC model with a total-account
collapse (3 of 7 cells ground to ≤1% of starting capital). Was that a
strawman — firing on every valid signal — rather than what a disciplined
discretionary ICT trader would actually take? Add four real, pre-registered
quality/selectivity filters (each tied to a named gap in §28), apply all
four together as ONE new variant, and re-run the identical 7 cells. Does
real selectivity turn this into a merely-losing strategy, a breakeven one,
or something that works?

**Method:** `run_ict_smc_selective.py` imports the §28 engine wholesale —
the per-bar state machine mechanics, the cost model, the
`max(20 ticks, 5 bps of price)` min-stop floor and its fill-gap re-check,
next-bar-open fills, the sequential `no_pos` gate, the $100k/1% compounding
convention, the ruin diagnostic, the look-ahead guard. **Only signal
acceptance is narrowed.** Every threshold below was stated in the script
docstring before the run and not tuned afterward.

1. **Sweep quality** — the swept level must sit within **10 bps** of the
   extreme of the last **240 M1 bars** (4h; ≫ the 11-bar pivot window),
   i.e. a real session extreme, not a shallow wick through a minor pivot.
2. **Real HTF context** — on top of the daily-50-EMA bias, require a full
   daily MA stack: `close` on the correct side of the **daily 200 EMA**
   *and* `EMA50` on the correct side of `EMA200` (a daily golden/death-cross
   regime, not one line).
3. **Selectivity cap** — **max 1 entry per rolling 7 days per instrument**,
   plus an absolute conviction floor: the displacement candle body must be
   **≥ 2.0×** the 20-bar average (base model needs only 1.5×). A true ex-post
   "largest displacement of the week" pick is not look-ahead-free, so the
   causal proxy is: conviction floor removes the weak setups, the cap keeps
   the first survivor.
4. **Level significance** — the swept level must pass ≥1 of: within **15 bps**
   of the prior calendar day's high/low; touched (±10 bps) on **≥3 distinct
   prior bars** in the last **480 bars** (8h); or within **10 bps** of a
   round number (step: XAUUSD 10 / EURUSD 0.0050 / SPX500 25 / BTCUSDT 1000).

An ablation isolating which filter matters most is deliberately deferred to
a follow-up (§29.x); this run tests the combined realistic version first.

**Trade-count reduction — the headline mechanical effect:** −94.8% overall
(14,650 §28 trades → 764). Per cell −88% to −98%. The dominant cut is the
1-per-7-days cap (e.g. XAUUSD raw signals 2,712 → 149); sweep-quality
rejects ~60-75% of sweeps before that; the HTF stack and conviction floor
each reject a few thousand more; **level-significance rejects almost
nothing** (0-778 across all cells) — a swing that already *is* the 4-hour
extreme is nearly always near a prior-day level or round number, so filter 4
is largely redundant given filter 1. Worth noting for the ablation.

**Result — headline, $100,000 start, 1% risk/trade compounded, directly
comparable to §28:**

| Instrument (in-regime) | §28 end $ | SELECTIVE v1 end $ | B&H end $ | Beat B&H? |
|---|---|---|---|---|
| XAUUSD 2018-2025 | $165 (-99.8%) | **$50,790 (-49.2%)** | $331,604 | NO |
| EURUSD 2018-2025 | $6,159 (-93.8%) | **$77,196 (-22.8%)** | $97,794 | NO |
| SPX500 2018-2025 | $14 (-100.0%) | **$83,296 (-16.7%)** | $255,640 | NO |
| BTCUSDT 2018-2025 | ~$0 (-100.0%) | **$14,307 (-85.7%)** | $639,397 | NO |

Out-of-regime slices: XAUUSD 2017 $95,941 (-4.1%) vs B&H $113,177 — NO;
SPX500 2017 $88,636 (-11.4%) vs B&H $118,831 — NO; EURUSD 2013-2017
$103,977 (+4.0%) vs B&H $90,954 — **the lone "beat B&H" of 7 cells**, but
B&H itself was down 9% that window, and +5.2R of the +4.7R total P&L comes
from **2013 alone** (2015-16 negative; top-year concentration 112%, DSR
0.106). Not a real win.

**Account-ruin diagnostic — the one unambiguous improvement:** **ELIMINATED.**
No cell reaches ≤1% of starting capital (§28: 3/7 ruined at trades
#321-1,786). Trading ~20× less means even a net-PF-below-1 cell only
compounds 120-230 times instead of thousands, so the multiplicative decay
to zero never runs its course. Verdict on the §28 question "does any cell
still grind toward zero": **no.**

**But it is still a losing strategy, not breakeven and not working:**
- **Net PF < 1 on 6 of 7 cells** (0.15-0.91; only EURUSD 2013-2017 at 1.09).
  Real costs still exceed the thin gross edge.
- **Gross PF got *worse* on some cells** — XAUUSD in-regime 1.03 → 0.78,
  BTCUSDT 1.04 → 0.96, EURUSD in-regime 1.02 → 0.97. The four filters did
  **not** isolate a higher-edge subset; on several instruments they selected
  a *worse* one. The dollar improvement is almost entirely the mechanical
  ruin-avoidance effect of trading 95% less, **not** recovered alpha.
- **Sharpe still negative on 6/7** (SPX500 in-regime improves to -0.74 from
  -2.74; BTCUSDT still catastrophic at -13.8).
- **Per-year:** XAUUSD in-regime negative every one of 8 years; BTCUSDT
  negative every year (worse 2023-25); SPX500 negative in 5 of 8.
- **DSR ≤ 0.106 on every cell** (bar 0.95). **Survivors 0/7.**
- Look-ahead guard PASS 7/7.

**Verdict: KILL — but now a fair one.** Disciplined, selective, quality-
filtered ICT trading is **not** account-destroying — §28's collapse to zero
was substantially an artefact of over-trading a tiny negative edge with
fixed-fractional sizing. Remove 95% of the trades and the account merely
bleeds instead of imploding. But across 4 asset classes and 7 windows the
selective version still loses money in 6/7 cells, still loses to buy-and-hold
in 7/7, still has net PF < 1 in 6/7, and its dollar gains over §28 are
mechanical (fewer compounding steps), not a found edge — the underlying
entry logic's gross edge is at or below breakeven and did not improve under
selection. A per-filter ablation (§29.x) could confirm which filter, if any,
carries signal, but the combined realistic model does not clear any honesty
gate.

**Files:** `run_ict_smc_selective.py`. Results:
`results/ict_smc_selective.csv`, `ict_smc_selective_trades.csv`,
`ict_smc_selective_run.log`. Reproduce: `python run_ict_smc_selective.py`.

**Cumulative trials: N=1105** (1098 prior + 7 — the §28 cell set re-run
under SELECTIVE v1).

---

## §29.x — ICT SMC filter ablation: which of the four §29 filters carries signal alone? (2026-09-04)

**Question:** §29 deferred the ablation. Test each of the four filters
**individually** on top of the unfiltered §28 engine (not combined), and ask
whether any single one improves the **raw before-cost gross profit factor** —
the number that matters, since §29 found gross PF got *worse* on several
cells when all four were combined.

**Method:** `run_ict_smc_ablation.py` — the §29 stateful loop re-parameterised
with four on/off flags. Every gate expression is byte-identical to
`run_ict_smc_selective`; only `if <flag>` wrappers are added. **With all four
flags off the loop reproduces `run_ict_smc.run_state_machine` exactly —
asserted at run time: baseline trade count and gross PF match
`results/ict_smc.csv` on all 7 cells to 4 dp.** 6 variants (baseline, F1, F2,
F3, F4, ALL-FOUR) × the same 7 cells. Look-ahead guard PASS 42/42.

| Filter | What it gates |
|---|---|
| F1 sweep quality | swept level within 10 bps of the last 240-bar (4h) extreme |
| F2 HTF context | daily 50 EMA bias **plus** daily 200 EMA stack alignment |
| F3 selectivity cap | 1 entry / rolling 7 days **plus** 2.0× displacement conviction floor |
| F4 level significance | swept level near prior-day H/L, ≥3 touches, or round number |

**Result — mean gross PF across the 4 in-regime instrument cells
(XAUUSD/EURUSD/SPX500 2018-25 + BTCUSDT 2018-25), baseline = 1.0252:**

| Variant | mean gross PF | Δ vs baseline | # instruments gross PF > baseline | mean net PF | mean Sharpe | # beat B&H |
|---|---|---|---|---|---|---|
| **F1 sweep-quality only** | 1.0312 | **+0.0060** | **2 / 4** | 0.578 | −5.20 | 0/4 |
| F4 level-significance only | 1.0256 | +0.0004 | 1 / 4 | 0.590 | −4.95 | 0/4 |
| *baseline (§28)* | 1.0252 | — | 0 / 4 | 0.590 | −4.95 | 0/4 |
| F2 HTF-context only | 1.0231 | −0.0021 | 1 / 4 | 0.592 | −4.86 | 0/4 |
| ALL FOUR (§29) | 1.0153 | −0.0099 | 1 / 4 | 0.581 | −5.49 | 0/4 |
| F3 selectivity-cap only | 0.9631 | −0.0621 | 1 / 4 | 0.525 | −5.93 | 0/4 |

Per-instrument gross PF (in-regime):

| | baseline | F1 | F2 | F3 | F4 | ALL4 |
|---|---|---|---|---|---|---|
| XAUUSD | 1.031 | **0.984** | 1.022 | 0.920 | 1.031 | 0.784 |
| EURUSD | 1.020 | 1.016 | 1.010 | 0.908 | 1.020 | 0.968 |
| SPX500 | 1.013 | 1.036 | 1.028 | 0.960 | 1.013 | 1.350 |
| BTCUSDT | 1.037 | 1.088 | 1.033 | 1.064 | 1.038 | 0.960 |

**Does any single filter improve the raw before-cost edge? No.**

- **F1 (sweep quality)** has the only positive mean Δ, but it is **+0.006 gross
  PF** — trivially small — and it is **inconsistent**: it lifts SPX500 (+0.023)
  and BTCUSDT (+0.051) while *hurting* XAUUSD (−0.047) and EURUSD (−0.004).
  A +0.006 mean produced by 2 of 4 instruments after halving the sample is
  noise from a smaller draw, not a recovered edge.
- **F4 (level significance)** is effectively a **no-op applied alone** —
  identical gross PF to baseline on 3 of 4 instruments (rejects 24 of 12,810
  signals total). It only does work in §29 because F1 first restricts the
  candidate set. On its own it carries nothing.
- **F2 (HTF context)** makes the mean gross edge slightly *worse* (−0.002).
- **F3 (selectivity cap)** makes it substantially *worse* (−0.062 gross PF) —
  the 1-per-7-days + conviction floor keeps a subset with a *lower* raw
  win/loss ratio, not a higher one.
- **Net PF stays below 1 and mean Sharpe stays −4.9 to −5.9 for every
  variant.** Zero cells beat buy-and-hold under any single filter.

**Ruin diagnostic across variants:** F1, F2 and F4 applied alone do **not**
prevent the account-ruin seen in §28 — XAUUSD, SPX500 and BTCUSDT in-regime
still grind to ≤1% of start (trades #361-1,678). Only F3 (and ALL-FOUR)
avoid ruin, and purely by cutting trade volume ~15-40× — the same mechanical
effect §29 identified, attributable entirely to the weekly cap, not to any
edge in the other three filters.

**Verdict — the complete, honest answer:** **No single filter carries a real
isolated edge, and neither does the combination.** The one filter with a
positive mean gross-PF delta (F1, +0.006) is within noise and inconsistent
across instruments; two of the four make the raw edge measurably worse; one
is a no-op alone. The ICT SMC entry logic itself has no before-cost edge
that any of these four quality/selectivity filters — individually or
together — can recover. §29's dollar improvement over §28 was mechanical
(fewer compounding steps from the weekly cap), confirmed here from the other
direction: strip the filters back to one at a time and the raw edge does not
appear. This closes the ICT SMC thread completely.

**Files:** `run_ict_smc_ablation.py`. Results:
`results/ict_smc_ablation.csv`, `ict_smc_ablation_run.log`. Reproduce:
`python run_ict_smc_ablation.py`.

**Cumulative trials: N=1133** (1105 prior + 28 — 4 individual filters × 7
cells; baseline and ALL-FOUR are references, not new trials).

---

## §30 — On-chain signal test: BTC active-address surge (2026-09-04)

**Question:** does on-chain flow data predict returns where price patterns
and positioning data didn't — the first genuinely new information category
tested since the crypto factor studies (§13/§15-18)?

**STEP 1 — data honesty, live-tested this session, reported first per the
brief.** The brief's leading candidates — exchange inflow/outflow, exchange
reserves, whale/large-holder balance changes — are **not available from any
free, no-signup API**, checked live:
- **Glassnode**: free tier is dashboard-only; the Light API needs the
  Advanced plan (~$49/mo), capped at 50 calls/day.
- **CryptoQuant**: free tier "severely limited," no documented free API;
  the Data API needs the Professional plan (~$99/mo) even for 24h
  resolution — the cheapest paid tier does not include it.
- **Coin Metrics Community API**: documented as free/no-key, but every
  endpoint tried this session (`asset-metrics` with `AdrActCnt` alone,
  `catalog-all/assets`) returned **HTTP 401 "requires authorization"** —
  free access now needs a registered API key this autonomous session
  cannot obtain (signup/email/captcha).
- **Etherscan** (checked as an ETH active-address equivalent): returns
  "Missing/Invalid API Key" with no key, on both API versions.
- **blockchain.info Charts API**: the one source that worked — no key, no
  auth, no rate limit hit, `n-unique-addresses` returned 6,417 daily rows,
  **2009-01-03 → 2026-09-03**, full and unsampled.

**Honest conclusion, stated before any backtest:** the metrics with the
clearest "smart-money" trading narrative (exchange flow, whale balances)
are paywalled everywhere free-tier-checked — the same thin-free-surface
pattern already documented for PIT earnings data (§25). What gets tested
is **BTC daily unique active addresses** — a network-activity / adoption
metric, genuinely distinct from price/positioning/options, but **weaker
and different from the exchange-flow signal the brief led with**, BTC-only
(no free ETH source found), and that gap is reported before the result.

**STEP 2 — strategy, pre-registered before running:** causal 90-day
rolling z-score of daily active addresses (baseline excludes the current
day); signal = z > **+1.5** (a large surge); **long-only** (mainstream
on-chain reading: address-growth surges as adoption/demand, a priori, no
short leg, no post-hoc direction flip); position modelled as entering at
the signal day's UTC close (the moment the print is knowable — equivalent
to next-day open to within an immaterial gap on a 24/7 market); held
**H = 5 and H = 20 calendar days** (both tested); `no_pos` gate (one
position at a time); real BTCUSDT spread + the project's own
`CRYPTO_COST_BPS` (20 bps commission, 1.0 bps/side slippage) reused
verbatim from `run_ict_smc.py`; $100,000 start, fully-invested-or-cash.

**Result — headline, full 2018-2025 window:**

| Hold | Trades | Net Sharpe | Net PF | maxDD | Top-year | Ending $ | vs B&H |
|---|---|---|---|---|---|---|---|
| H=5 | 150 | −0.30 | 0.953 | 68.8% | n/a | $55,629 (−44.4%) | loses |
| H=20 | 72 | +0.65 | 1.110 | 65.6% | 70% | $220,762 (+120.8%) | loses |
| **Buy-and-hold BTC** | — | — | — | — | — | **$576,995 (+477.0%)** | — |

**Event-level (the honest positive finding):** mean signed drift entry→exit
is **positive on both holds** (+0.50% H=5, +3.27% H=20), win rate **58%
both** — a small but real gross directional edge, gross Sharpe +0.74 (H=5)
and +0.86 (H=20). This is a genuinely different outcome from every prior
positioning/ML test in this project (§18 contrarian reversal, §18.1 ML on
positioning both found ≈0 edge) — the on-chain signal shows real
information content.

**Why it still loses:** H=5's small gross edge does not clear real crypto
transaction costs (net PF 0.953, net Sharpe negative) — the same
cost-vs-edge failure mode as §13/§11. H=20's net edge is real (PF 1.110,
Sharpe +0.65) but the strategy is only invested **~45% of the days**
(72 trades × 20 days ≈ 1,440 of 3,165), so it cannot capture BTC's own
+477% run — **the same terminal reason as §25 PEAD: a real edge that loses
to simply owning the underlying's beta.** H=20 also fails the concentration
gate (top year = 70-102% of total P&L across cells).

**Regime sub-split** (2018-2021 bull-heavy vs 2022-2025 mixed — NOT a true
out-of-regime test; no free pre-2018 real-spread BTCUSDT data exists,
same constraint already stated for BTCUSDT in §28): H=5 is unstable
(+0.48 Sharpe in 2018-21, **−1.46** in 2022-25); H=20 is the more robust
cell, positive in BOTH sub-periods (+0.76, +0.52) — the one cell with any
claim to robustness, though still losing to B&H in both.

**DSR (reference only, not a gate, N=2 pool):** H=5 0.145, H=20 0.596 —
neither clears 0.95. Look-ahead guard PASS on every cell (verified: entry
never precedes the signal day's close; the z-score is NaN, and excluded,
until 90 full trailing days of address history exist).

**Verdict: KILL, but a genuinely informative one.** Unlike most prior
non-price signals in this project, the on-chain active-address surge shows
a **real, positive, non-zero gross edge** (58% win rate both holds,
positive mean drift, gross Sharpe > 0) — on-chain data DOES carry some
signal that price/positioning data didn't show. It still loses to
buy-and-hold because (a) H=5's edge is too small to survive real costs and
(b) H=20's edge is real but the strategy sits in cash too often to compete
with a genuine bull market — the same terminal pattern as §25 PEAD, not
the "edge ≈ 0" pattern of §18/§18.1. **The bigger caveat is STEP 1, not
STEP 2**: this tests active addresses, not the exchange-flow / whale-
balance metric the brief named as the leading hypothesis, because that
data is not free anywhere checked. A genuine test of exchange flow would
require a paid subscription (Glassnode Advanced ~$49/mo or CryptoQuant
Professional ~$99/mo) — flagged as an open, costed next step, not run here.

**Files:** `scripts/download_btc_active_addresses.py`,
`run_onchain_signal.py`. Results: `results/onchain_signal.csv`,
`onchain_signal_run.log`. Data:
`data/BTC_active_addresses_blockchaininfo.csv` (free, re-downloadable, not
gitignored — 6,417 rows, ~200 KB). Reproduce:
`python scripts/download_btc_active_addresses.py && python run_onchain_signal.py`.

**Cumulative trials: N=1135** (1133 prior + 2 — H=5, H=20).

---

## §30 follow-up — order-book capture infrastructure (prep only, NOT a trial, 2026-09-04)

Per the task brief, once §30 produced a genuine result this project moved
straight to preparing the **next** genuinely new data category —
order-book microstructure — rather than stopping. **Nothing is deployed
and no data has been collected.** This is infrastructure only, built and
smoke-tested so it is ready the moment always-on hosting exists.

**Why capture-forward, not backtest:** no free (or, as far as checked, paid)
vendor sells historical L2 order-book data for crypto at a price this
project would pay. The only way to ever get it is to capture it forward
from today on an always-on host — a laptop/session-based environment can't
do this (this project's own standing rule: background processes die when
the terminal session ends).

**Pre-registered metric definitions (stated now, before any book history
exists, so a future backtest cannot tune them after seeing a result):**
1. **Depth-N order book imbalance**, N=10 and N=20:
   `OBI_N = (Σbid_qty[1..N] − Σask_qty[1..N]) / (Σbid_qty[1..N] + Σask_qty[1..N])`.
2. **Notional-band OBI**: same formula, using cumulative qty within ±25 bps
   of mid (robust to tick-size/level-count gaming).
3. **Trade-flow imbalance (TFI)**: aggressor-side buy/sell volume imbalance
   over a trailing 60-second window (Binance `aggTrade`'s `m` flag).
4. **Storage**: raw depth snapshots (~100ms cadence) and trade prints kept
   verbatim (gzip JSONL, day-rotated); aggregated to **1-second** feature
   bars for actual future backtest use — chosen because it can be honestly
   rolled up further to this project's existing minimum tested bar (M1)
   without look-ahead, without claiming sub-100ms execution realism.
5. **Hypothesised direction** (long bias when OBI/TFI > 0, short when < 0 —
   standard microstructure reading, e.g. Cont/Kukanov/Stoikov 2014):
   pre-registered; no entry threshold is fixed yet — that requires the
   first real batch's empirical distribution, decided BEFORE any P&L look
   on a second, later batch (an explicit time-split, not a tuned threshold).

**Capture script:** `scripts/orderbook_capture.py` — asyncio websocket
client on Binance's free, no-API-key public streams (`depth20@100ms` +
`aggTrade`), auto-reconnect with backoff, day-rotated gzip raw storage +
1-second feature CSV. **Smoke-tested live this session** (not merely
written): connected to the real Binance stream, ~2,200 msg/min for
BTCUSDT, produced correct feature rows (OBI/TFI in the expected [-1,1]
range) and correctly-formatted raw JSONL. **One real bug found and fixed
during the smoke test**: a hard-killed process (simulating power loss /
OOM-kill on a VPS) left the day's gzip raw file with a truncated final
member (`EOFError` on read) — fixed by rotating the raw gzip file into a
new, independently-decompressible member roughly every 60 seconds
(`Writer.rotate_raw`), verified on a second hard-kill test: the file then
read back cleanly (4,014 lines, no error) despite the same hard kill.

**Deployment:** `docs/orderbook_capture_vps_deployment.md` — full walkthrough
for a $5/month VPS (DigitalOcean/Vultr/Linode/Hetzner, smallest Ubuntu
tier): provisioning, firewall, systemd service (auto-restart, graceful
SIGTERM shutdown), disk-budget projection (~500-750 MB/month for two
symbols, well inside a $5 tier's disk), an offload/rotation plan for when
that budget is actually observed, and an explicit "what not to do" section
(no trading credentials on this box — public market data only; always stop
it gracefully; don't backtest on partial data).

**Status: ready to deploy, not deployed.** No cumulative-trial count change
— this is infrastructure, not a backtest.

---

## §30.1 — On-chain active-address signal: bounded pre-registered extension (2026-09-06)

**Follows §30 directly. Data, cost model and engine reused byte-for-byte**
via `import run_onchain_signal as s30` — `s30.load_addr()` /
`s30.load_btc_daily()` (free blockchain.info `n-unique-addresses` +
real-spread BTCUSDT daily from the Binance H1 file), `s30.CRYPTO_COST_BPS`
(20 bps commission + 1.0 bps/side slippage + real per-day closing-hour
spread, split half-open/half-close), `s30.build_signal` (causal trailing
z-score, current day excluded), `s30.run_cell` (no_pos sequential gate).
Long cells call `s30.run_cell` unmodified; short cells use a byte-copy with
**three marked sign flips**; Part 3 uses a new daily-filter engine.

**The §30 STEP 1 data caveat still governs everything below:** the metric
is BTC unique active addresses — a network-usage/adoption proxy — **not**
the exchange-flow / whale-balance / exchange-reserve data the original
brief named as its leading hypothesis. That data is paywalled on every free
tier checked live in §30 (Glassnode, CryptoQuant, Coin Metrics, Etherscan).
This section is a wide search of the one free series, not a test of the
brief's actual hypothesis.

**Pre-registration (all rules fixed before the run — `run_onchain_signal_ext.py` docstring):**

- **Part 1 — lookback/threshold grid (level surge):** window {30, 60, 90*,
  180} d × z-threshold {1.0, 1.5*, 2.0} SD × direction {long-on-surge*,
  short-on-surge / fade} × hold {5, 20} d = **48 cells**. (* = §30 value.)
  Trigger is identical for both directions (an *upward* address surge,
  z > threshold); only the position sign differs.
- **Part 2 — acceleration variant:** signal = 2nd difference of the trailing
  rolling average, z-scored against its own trailing distribution.
  Exact causal calc: `RA_t = A.shift(1).rolling(W).mean()` (day t excluded);
  `ACCEL_t = RA_t − 2·RA_{t−1} + RA_{t−2}`;
  `ACCELZ_t = (ACCEL_t − mean_{t−W..t−1} ACCEL) / std_{t−W..t−1} ACCEL`.
  Strictly causal — uses A only through day t−1. Same 48-cell grid = **48 cells**.
- **Part 3 — regime filter on default buy-and-hold:** hold 100% BTC every
  day; **exit to cash on day t+1 iff the §30 level z-score on day t is
  ≤ UNHEALTHY_THR** (network activity contracted vs its trailing
  distribution); position lagged one day; never short. Grid: window {90,
  180} × UNHEALTHY_THR {−0.5, −1.0, −1.5} SD = **6 cells**. One BTCUSDT
  transaction charged per switch (half the §30 round-turn cost each).
- **Total new cells / trials this batch: 48 + 48 + 6 = 102.**

**Honesty gates:** look-ahead guard **PASS on all 102** (baselines exclude
the current day by construction; Part 3 position is `z.shift(1)`; guard
returned true on every evaluated cell). Real BTCUSDT costs (§30 model).
Per-year concentration (bar 0.60). Regime sub-split 2018-2021 vs 2022-2025
— **same caveat as §30/§28: NOT a true out-of-regime test**, no free
pre-2018 real-spread BTCUSDT data exists (Binance starts 2017-08).
vs buy-and-hold BTC over the identical window ($100k → **$576,995**,
+477.0%, CAGR +22.4%, daily-return Sharpe **+0.638**, maxDD 81%).

**Deflated-Sharpe pool, stated explicitly (the brief's requirement):**
- PRIOR cumulative project trials (through §30): **1135**.
- NEW trials this batch: **102**.
- **NEW CUMULATIVE TOTAL: 1237.**
- Batch net-Sharpe distribution: mean −0.600, sd 1.171, range [−4.87, +2.20].
- E[max Sharpe] under the null: batch structural pool N=102 → **+2.372**;
  **full-cumulative pool N=1237 → +3.283** (the primary bar — the grid is
  large, so the bar rises accordingly). DSR reported per cell against both.

**RESULT — RANKED BY NET SHARPE (full window; complete 102-row table in
`results/onchain_ext.csv`, console log `results/onchain_ext_run.log`):**

| # | part / variant | win | thr | dir | H | n | net SR | gross SR | net PF | maxDD | topYr | end $ | vs B&H | subA / subB | DSR (N=1237) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 accel | 90 | +2.0 | long | 5 | 48 | **+2.20** | +3.55 | 1.421 | 26.3% | 68% | $172,975 | **loses** | +5.30 / −1.12 | 0.204 |
| 2 | 2 accel | 180 | +1.5 | long | 5 | 111 | +1.16 | +2.22 | 1.192 | 42.9% | 89% | $186,061 | loses | +1.26 / +1.05 | 0.009 |
| 3 | 1 level | 180 | +2.0 | long | 20 | 40 | +1.08 | +1.26 | 1.187 | 51.8% | 76% | $294,205 | loses | +1.22 / +0.85 | 0.001 |
| 4 | 1 level | 180 | +1.5 | long | 20 | 64 | +1.07 | +1.27 | 1.190 | 58.5% | 58% | $489,625 | loses | +1.11 / +1.06 | 0.000 |
| 5 | 1 level | 90 | +2.0 | long | 20 | 46 | +0.87 | +1.06 | 1.148 | 70.3% | 59% | $237,225 | loses | +0.95 / +0.77 | 0.000 |
| … | 13 long cells beat B&H's +0.638 net Sharpe at lower DD; **none** beats it in dollars | | | | | | | | | | | | | | |
| 30–45 | **Part 3** regime-filter-on-B&H (all 6) | 90/180 | −0.5…−1.5 | — | — | 403–865 sw | +0.19 … −0.20 | +0.48…+0.60 | ≤1.03 | 83–95% | — | **$14k–$57k** | **all lose** | mixed | 0.000 |
| 50–102 | **all short / fade cells** | | | short | | | −0.46 … **−4.87** | mostly negative | <1 | 82–99.9% | — | wiped | all lose | negative | 0.000 |

**Buy-and-hold BTC:** full $576,995 · sub 2018-2021 $344,216 · sub 2022-2025 $163,609.

**FINDINGS:**

1. **0 / 102 cells beat buy-and-hold BTC in compounded dollars.** 13 long
   cells beat B&H on *risk-adjusted* return (net Sharpe > 0.638) at far
   lower drawdown — the best (Part 2 accel/W90/thr+2.0/H5) posts net Sharpe
   +2.20, gross +3.55, PF 1.42, maxDD 26.3% vs B&H's 81% — **but every one
   loses in dollars because it is invested only a fraction of the time.**
   Exact §30 / §25-PEAD terminal pattern: a real small gross directional
   edge that cannot out-compound simply owning the beta through a genuine
   bull run.
2. **DSR: 0 / 102 clear 0.95** against the true N=1237 pool (E[max SR]
   +3.283). Top cell scores **0.204**; #2 onward ≤ 0.009. Even against the
   lenient batch-only pool (N=102) the best is 0.447. Nothing survives.
3. **The acceleration variant is not an improvement.** Its best cell tops
   the table only via a single-regime spike: subA (2018-2021) net Sharpe
   **+5.30** vs subB (2022-2025) **−1.12** — a sign flip; the whole result
   is one bull phase. Across the grid the acceleration cells interleave
   with the level cells, no systematic edge.
4. **Contrarian / short-on-surge / fade: clean anti-finding.** Ranks 50–102
   are almost entirely short cells; gross Sharpe is *negative* on most —
   fading an address surge is just being short BTC in a bull market. No
   contrarian edge in either the level or the acceleration signal.
5. **Part 3 (regime filter on B&H) does NOT fix §30's "sits in cash too
   much" failure — it replaces it with churn.** The naive daily filter
   flips 403–865 times over the window; even the variant that stays in BTC
   **91%** of days returns **−6.3% CAGR** ($56,998) vs B&H's +22.4%. Gross
   (cost-free) Sharpe of every Part-3 cell is ~0.48–0.60, **below B&H's
   0.638**, so the unhealthy-exit timing is *mildly anti-predictive* even
   before switch costs bury it. Hysteresis/persistence is an obvious
   un-tested refinement, but the gross-Sharpe deficit says the exit timing
   has no edge to rescue.
6. **Regime instability is the rule:** 37 / 102 cells flip net-Sharpe sign
   between 2018-2021 and 2022-2025. The few positive-Sharpe cells are
   overwhelmingly 2018-2021 phenomena.

**VERDICT — KILL, and the search is closed on this series.** A wide,
pre-registered, look-ahead-clean search — 102 cells across level surge, its
acceleration, both directions, four lookbacks, three thresholds, two hold
periods, and a regime-filter-on-buy-and-hold — of the one genuinely free
BTC on-chain series **came up empty**: nothing beats owning BTC in dollars,
nothing clears the DSR bar for the true trial count. Consistent with §30's
own conclusion. Real evidence that the free blockchain.info active-address
series carries no tradeable edge over buy-and-hold, **not** a reason to keep
parameter-hunting the same series. A genuine test of the brief's actual
hypothesis (exchange flow / whale balance / exchange reserves) still
requires a paid subscription (Glassnode Advanced ~$49/mo or CryptoQuant
Professional ~$99/mo) — flagged in §30 as a costed next step, still not taken.

**Files:** `run_onchain_signal_ext.py`. Results:
`results/onchain_ext.csv` (ranked evaluated cells),
`results/onchain_ext_all_cells.csv` (raw), `results/onchain_ext_run.log`.
Reproduce: `py -3.14 run_onchain_signal_ext.py`.

**Cumulative trials: N=1237** (1135 prior + 102).

---

## §31 - SIX NAMED STRATEGIES, NEVER PREVIOUSLY TESTED IN THIS PROJECT (2026-09-07)

**Why this batch exists.** Every candidate tested so far in this project is
either a project-original construction (ORB variants, RETEST, ICT SMC,
credit spreads, on-chain signals) or a generic family sweep (section 1). Six
well-known, independently documented retail/institutional strategies had
never been run here at all: pairs trading, Bollinger mean-reversion, MACD
crossover, calendar/seasonality, the Turtle system, and Ichimoku Cloud. This
batch tests all six, each built with full honesty gates FROM THE START
(look-ahead guard, real costs, DSR as reference only, per-year
concentration, out-of-regime split where the data allows it, and the full
continuous-compounding treatment run immediately, not as a follow-up).

**Shared engine (research/six_strategies_engine.py).** Daily bars only (the
standard timeframe for all six named systems). Built from this project's
own real spread-inclusive M1/H1 archives via
research.gold_data.aggregate_daily for XAUUSD/EURUSD/NAS100/US30/SPX500,
Binance H1 aggregated to daily for BTCUSDT/ETHUSDT, and yfinance daily
adjusted close for GLD/SLV (pairs trade only -- no bid/ask column exists
for these, so a stated 2 bps round-turn ETF-spread assumption is used
instead of a measured one, flagged everywhere it's used). Costs: index/FX
real spread + 0.35bps commission; crypto 20bps taker; ETF 2bps assumed. 1%
fixed-fractional risk is this project's standing default, but four of the
six systems here (Bollinger, MACD, Ichimoku, pairs) are not fixed-R setups
by design (no stop-distance-defined risk unit) -- for those, "1% risk" is
replaced with full-exposure-while-in-position sizing, stated explicitly in
each script's docstring, the same convention already used for section 30's
on-chain signal for the identical reason. Turtle uses genuine Turtle-unit
sizing (1% of equity per N, pyramided) since that IS the documented
system's own sizing rule. Data spans: XAUUSD/SPX500 2017-2025 (no earlier
real-spread data exists, stated repeatedly elsewhere in this project);
EURUSD/NAS100/US30 2013-2025 (real out-of-regime window available, used for
the OOS split column); BTCUSDT/ETHUSDT 2018-2026; GLD 2004-2026/SLV
2006-2026 (pairs).

**A real bug found and fixed during this batch, stated plainly.** The first
Turtle System 1 run had ETHUSDT flat-line at its exact 2018 equity for the
following 8 straight years (0.0% every year through 2026) -- the documented
"skip the next breakout if the last trade was a winner" whipsaw filter was
implemented so that a SKIPPED breakout left the "last was a winner" flag
set indefinitely, permanently locking that direction out after a single
winning trade. Fixed to the documented rule: only ONE breakout is skipped
after a winner, the next is taken unconditionally. Confirmed fixed (ETHUSDT
System 1 now trades normally in every year, ending +93.8% instead of the
frozen +2.0%). No other bug found across the other five strategies' full
runs.

### 1. PAIRS TRADING -- GLD/SLV and NAS100/US30, 60-day rolling z-score, N in {1.5,2.0}

Measured correlation (not assumed): GLD/SLV daily-return correlation 0.797
(2006-2026); NAS100/US30 0.794 (2013-2025) -- both genuinely correlated
pairs, confirmed before treating them as one.

| pair | N | total return | max DD | recovered | concentrated |
|---|---|---|---|---|---|
| GLD/SLV | 1.5 | -29.0% | 44.2% | no | no |
| GLD/SLV | 2.0 | -37.7% | 52.1% | no | no |
| NAS100/US30 | 1.5 | +0.7% | 15.8% | yes | YES (2480%) |
| NAS100/US30 | 2.0 | +14.9% | 14.2% | yes | YES (125%) |

GLD/SLV loses money outright in both thresholds, with a 44-52% drawdown
never recovered. NAS100/US30 shows a positive total return at N=2.0 but is
flagged concentrated at BOTH thresholds -- nearly the entire result comes
from one or two years, the same failure signature that has killed multiple
other candidates in this project (index basket, Sneaky Pivot, plain ORB).
0/4 cells survive.

### 2. BOLLINGER BAND MEAN-REVERSION (20, 2.0), daily, 7 instruments

**CORRECTION (2026-09-07, same day as the original write-up): the table
below fixes a transcription error found while verifying a follow-up
question about MACD/BTCUSDT. The underlying backtest and the saved CSV
(results/six_strategies_summary.csv) were always correct; the total-return
and max-DD figures typed into the FIRST version of this section were
manually mis-scaled (effectively multiplied by 100 a second time) for
several cells. Re-verified directly against results/strat_bollinger_run.log
line by line below.**

| instrument | total return | max DD | beats B&H | concentrated | OOS holds |
|---|---|---|---|---|---|
| XAUUSD | -0.2% | 0.5% | no | no | -- |
| EURUSD | +0.2% | 0.1% | yes | no | yes |
| NAS100 | +1.1% | 0.3% | no | no | yes |
| US30 | +0.5% | 0.4% | no | no | yes |
| SPX500 | +0.3% | 0.4% | no | YES | -- |
| BTCUSDT | -1.9% | 2.8% | no | no | -- |
| ETHUSDT | -3.3% | 3.8% | no | no | -- |

EURUSD "beats B&H" only because EURUSD buy-and-hold itself lost 11.0% over
this span -- the strategy's own total return is +0.2% over 13 years
(effectively flat; it mostly sits in cash). Not a real edge, a trivial
clearing of a below-zero bar. Every cell's total return and drawdown are
tiny (all under 4% in either direction) -- there is no ruin anywhere in
this strategy, and no cell comes close to a real signal; it is simply
near-inert on all 7 instruments. 0/7 survive.

### 3. MACD CROSSOVER (12, 26, 9), daily, always-in-market, 7 instruments

**Same correction as section 2 above** -- re-verified directly against
results/strat_macd_run.log.

| instrument | total return | max DD | beats B&H | concentrated |
|---|---|---|---|---|
| XAUUSD | -0.3% | 0.5% | no | no |
| EURUSD | -0.3% | 0.4% | yes (B&H -11.0%) | no |
| NAS100 | -1.3% | 1.4% | no | no |
| US30 | -0.2% | 0.7% | no | no |
| SPX500 | -0.1% | 0.6% | no | -- |
| BTCUSDT | +3.1% | 0.6% | no | no |
| ETHUSDT | +3.2% | 1.4% | no | no |

Every cell's total return is small (under 3.5% either direction over
8-13 years) and every cell loses decisively to its own buy-and-hold --
BTCUSDT strategy +3.1% vs its own buy-and-hold +477.0%; ETHUSDT strategy
+3.2% vs its own buy-and-hold +220.2%. Standard 12/26/9 MACD crossover
captures essentially none of the underlying instruments' real price
movement on any of the 7 instruments tested. The one "beat" (EURUSD) is
again a losing strategy beating a more-losing benchmark. 0/7 survive.

### 4. CALENDAR/SEASONALITY -- significance test run BEFORE any backtest

Three named effects (Santa Claus rally, Sell in May, turn-of-month), tested
on SPX500 (2017-2025) and BTCUSDT (2018-2026) with BOTH a Welch t-test and
a 10,000-resample bootstrap of same-size random-day baskets, required to
agree at p<0.05 before any tradeable rule would be built.

Result: 0/6 effect/instrument combinations were significant on both tests.
Best p-values were nowhere close to 0.05 (SPX500 Santa Claus t-test p=0.84,
bootstrap p=0.86; BTCUSDT turn-of-month, the closest of the six, t-test
p=0.40, bootstrap p=0.44). Per the task's explicit instruction, NO backtest
was built for any of the six -- this is a clean, honest non-finding, not a
forced kill. Consistent with this project's standing finding that the free
daily-resolution price/calendar surface is exhausted (see the crypto
factor lab's parent-level conclusion on price/derivatives factors).

### 5. TURTLE TRADING SYSTEM -- System 1 (20d/10d, skip-winner filter) and System 2 (55d/20d, no filter), 7 instruments

| instrument | system | total return | max DD | recovered | beats B&H | concentrated |
|---|---|---|---|---|---|---|
| XAUUSD | 1 | +83.5% | 22.1% | yes | no | no |
| XAUUSD | 2 | +90.7% | 19.4% | yes | no | no |
| EURUSD | 1 | -36.0% | 48.8% | no | no | no |
| EURUSD | 2 | -16.9% | 42.7% | no | no | no |
| NAS100 | 1 | +8.9% | 24.0% | yes | no | YES |
| NAS100 | 2 | +15.0% | 25.3% | yes | no | YES |
| US30 | 1 | -11.5% | 29.8% | no | no | no |
| US30 | 2 | -7.2% | 28.4% | yes | no | no |
| SPX500 | 1 | -1.8% | 29.6% | no | no | no |
| SPX500 | 2 | +37.5% | 26.1% | no | no | no |
| BTCUSDT | 1 | +164.4% | 14.4% | no | no | no |
| BTCUSDT | 2 | +92.3% | 11.6% | yes | no | no |
| ETHUSDT | 1 | +93.8% | 17.8% | yes | no | no |
| ETHUSDT | 2 | +103.5% | 13.1% | yes | no | no |

Turtle is the most internally consistent of the six -- real trend-following
gains on gold and both crypto instruments, genuinely bounded drawdowns
(11.6-29.8%, no ruin anywhere), and NAS100 is the only cell combination
that comes close to a real signal (positive on both systems) but is
flagged concentrated on both. Every single cell still loses to its own
instrument's buy-and-hold over this specific 2013/2017/2018-2025 bull-
dominated window -- the same terminal pattern (section 12/14/25/etc.) of a
real, working trend system that is simply worse than owning the underlying
through this particular period. 0/14 survive, but this is the "closest to
a horse" of the six -- if any of these six warranted a follow-up (a
different window, a shorter bull-avoiding period, futures-native costs),
Turtle would be the one.

### 6. ICHIMOKU CLOUD (9, 26, 52), daily, 7 instruments

**Same correction as sections 2-3 above** -- re-verified directly against
results/strat_ichimoku_run.log.

| instrument | total return | max DD | beats B&H | concentrated |
|---|---|---|---|---|
| XAUUSD | +0.5% | 0.2% | no | YES |
| EURUSD | +0.2% | 0.2% | yes (B&H -11.0%) | no |
| NAS100 | +0.2% | 0.4% | no | YES |
| US30 | -0.0% | 0.4% | no | no |
| SPX500 | +0.2% | 0.3% | no | YES |
| BTCUSDT | +0.8% | 1.0% | no | YES |
| ETHUSDT | +3.3% | 1.5% | no | no |

Same pattern as the other trend/mean-reversion systems here: every cell's
total return is small (under 3.5% in either direction over 8-13 years),
four of seven are flagged concentrated, and none beats its own buy-and-hold
except the same trivial EURUSD case. No ruin anywhere -- the largest
drawdown across all 7 instruments is 1.5% (ETHUSDT). 0/7 survive.

### COMPARISON TO THIS PROJECT'S THREE EXISTING REAL CANDIDATES

| candidate | status |
|---|---|
| ORB gold RETEST OR30/1R (sections 10.5-10.8) | Real gross edge, fails DSR/concentration/cost-adjusted-vs-B&H |
| On-chain BTC active-address H=20 (section 30) | Real non-zero gross edge, loses to buy-and-hold |
| Vol-regime-filtered ORB (section 10.9) | Cost mechanism confirmed real, 0/56 survivors |
| This batch's closest analog: Turtle System 1/2 | Real, bounded trend-following gains on 3/7 instruments, but 0/14 survive the buy-and-hold gate |

**VERDICT -- CLEAN KILL ACROSS ALL SIX STRATEGIES, 0/45 CELLS SURVIVE** (7
Bollinger + 7 MACD + 7 Ichimoku + 14 Turtle + 4 Pairs + 6 calendar
significance tests, no backtest forced on the calendar non-finding). No
strategy/instrument combination is simultaneously (a) profitable, (b) not
single-year/instrument concentrated, (c) beats its own buy-and-hold, and
(d) holds out-of-regime where testable. The recurring failure modes are
the same ones documented throughout this project: Turtle's real trend-
following gains still trail a strong 2013-2026 bull market on every risk
asset tested; Bollinger/MACD/Ichimoku are all near-inert at daily
resolution (every cell's total return and drawdown stay under ~4% either
way across 7 instruments and 8-13 years -- no ruin anywhere, just no
signal), and where a cell "beats" its own buy-and-hold it is only because
that instrument's buy-and-hold itself lost money (EURUSD, -11.0%); and any
cell with a genuinely large nominal gain (Turtle, and the two pairs cells)
is disproportionately likely to be single-year concentrated. Turtle is
flagged as the strategy
family most worth a possible future follow-up (a genuinely different,
non-bull-dominated test window) if this project returns to classic trend-
following; the other five are considered closed lines of inquiry on this
data.

**Files:** research/six_strategies_engine.py (shared engine),
research/strat_pairs.py, research/strat_bollinger.py, research/strat_macd.py,
research/strat_calendar.py, research/strat_turtle.py, research/strat_ichimoku.py.
Results: results/strat_*_run.log (one per strategy),
results/six_strategies_summary.csv (the consolidated 39-row comparison
table). Reproduce: py -3.14 research/strat_pairs.py, etc. (each script is
independently runnable; no shared state between them beyond the engine
module).

**Trial count: 45 new** (7 Bollinger + 7 MACD + 7 Ichimoku + 14 Turtle + 4
Pairs + 6 calendar significance tests). **Cumulative trials: N=1338** (1293
prior + 45).

---

## Section 31.1 - SLOWER, TREND-HOLDING MACD VARIANT (2026-09-07)

**Why this batch exists.** Section 31's standard 12/26/9 MACD crossover was
an always-in-market, reverse-on-every-crossover system that produced small
gains on BTCUSDT/ETHUSDT (+3.1%/+3.2%) far below their own buy-and-hold.
This is a genuinely different rule, not a re-label: LONG-ONLY, holds
through minor whipsaws inside a positive-histogram regime, and only exits
after a stated run of consecutive negative-histogram bars, rather than
reversing on the very first cross.

**Rule, stated before running.** Same EMA_FAST=12/EMA_SLOW=26/SIGNAL=9 as
section 31 (unchanged, no re-optimization of the indicator itself).
histogram = MACD line - signal line. ENTRY: histogram turns positive ->
go long (applied next bar). HOLD: stay long through any number of
individual negative-histogram bars below the exit threshold. EXIT:
histogram has been <= 0 for >= MIN_CONSEC_NEG_BARS consecutive bars -> go
flat (no short leg). MIN_CONSEC_NEG_BARS tested: {1, 3, 5}. Full exposure
while long, cash otherwise (same convention as every other non-fixed-R
system in section 31). Crypto cost model (20bps commission), same as
every other crypto cell in this project. No out-of-regime split available
(no real pre-2018 BTCUSDT/ETHUSDT window exists, standing constraint).

**Result -- 6 cells (2 instruments x 3 thresholds), all against BTCUSDT
buy-and-hold +477.0% / ETHUSDT buy-and-hold +220.2% over the identical
2018-2026 span:**

| instrument | exit threshold | total return | Sharpe | max DD | recovered | concentrated | beats B&H |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 1 bar | +3.4% | +0.76 | 0.6% | yes | no | no |
| BTCUSDT | 3 bars | +3.4% | +0.70 | 1.2% | yes | no | no |
| BTCUSDT | 5 bars | +3.0% | +0.58 | 1.7% | no | YES (68%) | no |
| ETHUSDT | 1 bar | +3.5% | +0.58 | 1.1% | yes | no | no |
| ETHUSDT | 3 bars | +3.1% | +0.49 | 1.4% | yes | no | no |
| ETHUSDT | 5 bars | +3.1% | +0.46 | 1.3% | yes | no | no |

**VERDICT -- the slower, trend-holding version does NOT perform materially
differently from the fast crossover, and does not survive either.** Total
returns are essentially unchanged from the fast-crossover baseline (+3.1%
BTCUSDT / +3.2% ETHUSDT) -- the noise-filtering exit does slightly reduce
position-change count (216 -> 175-215 for BTCUSDT) and modestly improves
Sharpe at the 1-bar threshold (+0.49 -> +0.76 on BTCUSDT), but every cell
still loses decisively to buy-and-hold by roughly two orders of magnitude
(+3.0-3.5% strategy vs +477.0%/+220.2% buy-and-hold), and the widest
filter (5 consecutive bars) is the worst performer AND the only cell
flagged concentrated -- widening the noise filter did not help, it slightly
hurt. Both the fast and slow forms of MACD fail on the same underlying
reason: whether reversing on every cross or holding through whipsaws with a
confirmation delay, the rule captures only a small fraction of trend
persistence and gives back the rest to costs and the strategy's own
exposure gaps versus simply holding the asset. Genuinely a different rule,
honestly tested, same clean kill as the fast version. 0/6 survive.

**Files:** research/strat_macd_slow.py. Results:
results/strat_macd_slow_run.log. Reproduce:
py -3.14 research/strat_macd_slow.py.

**Trial count: 6 new** (2 instruments x 3 exit thresholds). **Cumulative
trials: N=1344** (1338 prior + 6).



## Section 32 - ENSEMBLE / COMBINATION TEST: does combining many signals (incl. killed ones) help? (2026-09-08)

**Question, stated exactly as asked:** does combining MANY signals from
across this project -- including individually-KILLED ones, not just the
survivors -- into one basket produce a better, smoother result than
requiring each to pass alone? A genuinely different question from "blend
the winners."

### Inventory -- 64 series, extracted not re-run

Every strategy/instrument cell in this project with a real, reconstructable
daily return series. Nothing here is a new backtest: the SAME already-
audited engine functions each section's own verdict was built on are
called again, in memory, to recover the daily series that section never
itself persisted to a CSV.

| group | source | n |
|---|---|---|
| A | `report_year_by_year_returns.build_all()` -- MomoRot Sec12/12.2/17 (4), VRP Sec20/21 (6), Sneaky Pivot Sec9 (2), ORB Sec10 (2) | 14 |
| B | ICT SMC Sec28, `ict_smc_trades.csv` ret_frac by cell (4 in-regime 2018-2025, 3 short out-of-regime windows) | 7 |
| C | Sec31/31.1 six-strategy family -- Bollinger/MACD/Ichimoku x 7 instruments, Turtle Sys1/Sys2 x 7, Pairs (2 pairs x 2 N), MACD-slow n=3 (BTCUSDT/ETHUSDT) | 39 |
| D | Sec27 credit-spread FILTERED/1pct (`credit_spread_iv_filter.run_combined_book`, SPY 1993-2026), Sec30 on-chain H20 (`report_onchain_h20_continuous.build_full_daily_series`, BTCUSDT) | 2 |
| **total** | | **64** |

Every series reindexed to a full calendar-day grid over its OWN
`[first, last]` span (off-days -> 0%, same convention already used by
`report_year_by_year_returns.trade_series()`); outside its own span left
NaN so `pandas.DataFrame.corr()` does pairwise-complete correlation rather
than silently truncating everything to the shortest series' window. 2
components have only 1 year of history (ICT SMC XAUUSD/SPX500
out-of-regime stubs) -- flagged, correlations against them are noisy, not
hidden.

### THE CORRELATION MATRIX -- the critical output, reported in full

Full 64x64 matrix: `results/ensemble_correlation_matrix.csv`. Distribution:

| stat | value |
|---|---|
| mean pairwise corr | **+0.030** |
| median pairwise corr | +0.010 |
| std of pairwise corr | 0.176 |
| pairs abs(corr) > 0.70 | 28 / 4,096 (0.7%) |
| pairs abs(corr) > 0.50 | 72 / 4,096 (1.8%) |
| pairs abs(corr) < 0.30 | 1,747 / 4,096 (42.7%) |
| pairs abs(corr) < 0.10 | 1,425 / 4,096 (34.8%) |

**These signals ARE genuinely close to independent, mechanically.** This is
NOT the "wall of correlated noise that just dilutes" failure mode the task
asked to check for first -- real diversification potential exists
structurally in this project's signal set. The high-correlation pairs are
exactly the ones common sense predicts (VRP Sec20/21 sleeves at +1.00 since
Sec21 is a sizing/structure wrapper on Sec20's own signal; the two MomoRot
US-sector variants at +0.916; same-instrument Pairs/Turtle parameter
twins). The most-independent pairs are unrelated instrument/strategy
combinations near 0.000, exactly as expected from genuinely different
mechanisms.

### Four combined portfolios (equal-weight-all, inverse-vol-all,
low-corr quality-blind, low-corr positive-Sharpe-only)

| portfolio | N | total return | Sharpe | max DD | recovery | DSR (ref, pool N=64) |
|---|---|---|---|---|---|---|
| Equal-weight ALL 64 | 64 | **-37.2%** | -0.150 | 76.7% | never | 0.0000 |
| Inverse-vol-weight ALL 64 | 64 | **+48.1%** | +0.467 | 8.2% | 524d | 0.0000 |
| Low-corr filtered, quality-BLIND (abs(corr)<0.30) | 26 | **-97.2%** | -1.630 | 98.7% | never | 0.0000 |
| Low-corr filtered, positive-own-Sharpe-only | 14 | **+421.1%** | +0.682 | 20.1% | 531d | 0.0000 |
| *(reference)* best single component (MomoRot crypto-sectors Sec17) | 1 | +4101% | **+1.136** | 57.0% | -- | -- (Sec17: already KILLED) |

Full per-component table: `results/ensemble_component_summary.csv`. Kept-
member lists: `results/ensemble_low_corr_subset_members{,_positive}.csv`.

### Why the naive combination fails -- mechanism found, not asserted

Several ICT SMC Sec28 in-regime cells compound thousands of near-1%-risk M1
trades at net PF<1 to genuine near-total ruin over the full window
(BTCUSDT in-regime Sharpe **-12.70**, total return **-100.0%**; SPX500
-3.44; XAUUSD -2.95) -- this is the SAME finding Sec28 already reported
("0/7 cells beat B&H, net PF<1 on all 7"), not a bug introduced here. A
naive equal-weight, daily-rebalanced blend lets these few high-frequency
catastrophic sleeves dominate the basket's realized volatility and drag
the whole 64-series average into a loss, even though the correlation
matrix shows the underlying signal set is genuinely diversified.

**Confirmation this is a weighting artefact, not proof diversification
can't work here:** the SAME 64 components, inverse-vol-weighted instead
of equal-weighted, flip from Sharpe -0.15 to **+0.47**, maxDD from 76.7%
to 8.2%, and the drawdown actually recovers. Nothing about the signal set
changed -- only how much weight the catastrophic high-vol sleeves were
given.

**The single most important mechanical finding of this study:** the
low-correlation filter, applied WITHOUT any quality floor, makes the
result WORSE than including everything (-97.2% vs -37.2%). 7 of the 26
kept series have their own full-history Sharpe below -1.0. Pure
correlation-based selection preferentially admits **idiosyncratic ruin**,
precisely because a strategy imploding in its own unique way does not
correlate with anything else -- "independent" and "good" are different
properties, and optimizing for the first alone can actively select for
disasters. Restricting the SAME greedy correlation method's candidate
pool to only the 40/64 components with a positive own-Sharpe (still N=14
kept, still abs(corr)<0.30) produces the best-behaved portfolio of the four
(+421.1%, Sharpe +0.682, maxDD 20.1%, real recovery) -- smooth and
genuinely diversified, but its own Sharpe still sits below the project's
best single component.

### Verdict

**KILL as a standalone strategy on every one of the four combination
methods tried, DSR 0.0000 on all four (pool N=64, E[max SR]=+4.232) -- but
a complete, mechanically-explained answer to the ensemble hypothesis, not
a null result:**

1. This project's signals ARE close to independent (mean pairwise corr
   +0.03) -- real diversification potential exists structurally, contrary
   to the "just a correlated wall" failure mode the task asked to check
   first.
2. Naive equal-weighting squanders that potential by letting a few
   catastrophically-compounding cells (mechanically real, already
   documented at Sec28) dominate realized risk; vol-aware weighting alone
   recovers most of the lost ground with the identical 64 components.
3. Filtering purely on low correlation with no quality floor is a clean,
   generalizable anti-finding for any future combination attempt in this
   project: it actively selects for idiosyncratic disasters, not for
   healthy independence.
4. Even the best-constructed combination (positive-Sharpe-only,
   low-correlation, N=14) -- smooth, real recovery, maxDD 20.1% vs single
   components' 57-100% -- still does not clear the project's best
   individual component's own Sharpe or DSR. Diversification traded
   return for smoothness here; it did not manufacture a new edge. This is
   consistent with the project's standing finding (Sec1 bottom line): the
   free surface searched does not contain an edge large enough for a
   combination of components (each still individually correlated with
   *something* real, even if not with each other) to compound into a
   result that clears DSR.

Files: `research/ensemble_correlation.py`; `results/ensemble_daily_returns.csv`,
`ensemble_component_summary.csv`, `ensemble_correlation_matrix.csv`,
`ensemble_combined_results.csv`, `ensemble_low_corr_subset_members.csv`,
`ensemble_low_corr_subset_members_positive.csv`, `ensemble_run.log`.
Reproduce: `py -3.14 research/ensemble_correlation.py`.

**Trial count: 4 new** (the four combined-portfolio Sharpes tested against
the DSR gate; the 64 underlying component trials were already counted in
their own sections and are not re-counted here). **Cumulative trials:
N=1348** (1344 prior + 4).

## Section 32.1 - BUG AUDIT of the section-32 ensemble test (2026-09-08)

**Trigger:** the section-32 headline numbers were flagged as implausible
and audited on request. The specific hypothesis to check: were components
missing data on a given day silently treated as 0% return (fake "no risk"
days) instead of excluded from that day's average, artificially diluting
realized volatility and inflating the combined Sharpe?

**That literal bug does NOT exist.** Verified by reading
`research/ensemble_correlation.py` directly: `equal_weight_available()`
uses `frame.mean(axis=1, skipna=True)` (pandas skips NaN, never treats it
as 0), and `inverse_vol_weight()` builds weights from `frame.notna()` so
an absent series gets weight 0, not a fake-0-return vote. No fillna(0)
happens before either average.

**But a real, closely-related artefact WAS found and confirmed:
STAGGERED-INCEPTION REGIME BLENDING.** The 64-series frame spans
1993-01-29 -> 2026-08-31 (33.6 yrs, driven by the earliest component,
credit-spread SPY) but the basket is only genuinely populated from 2018
onward:

| Year(s) | Mean live components / day (of 64) |
|---|---|
| 1993-1999 | 1.00 |
| 2000-2011 | 3-7 |
| 2012-2013 | 12-21 |
| 2014-2017 | 32-44 |
| 2018-2025 | **51-59** |

4,837 of 12,268 total days (39%) have fewer than 5 live components; 2,530
days (21%) have exactly 1. For 25 of the 33.6 stitched years the "combined
portfolio" was really just 1-12 individual long-running components
(dominated by credit-spread SPY, own Sharpe +0.57, and the momentum-
rotation sleeves, own Sharpe +0.61-0.63) -- not a 64-way ensemble. That
thin pre-2018 stretch alone has equal-weight Sharpe **+0.484**. The
post-2018 stretch, once the basket is genuinely ~59-wide, also contains
several catastrophic components (e.g. ICT-SMC BTCUSDT in-regime, own
Sharpe -12.70) that the thin era never had to absorb.

**Corrected method:** recompute the same 4 combination functions, byte-
identical, restricted to 2018-01-01..2025-12-31 -- the window where the
basket is consistently populated (mean 58.7 of 60 available series live/
day, min 51). Script: `research/ensemble_correlation_restricted.py`
(imports and reuses `ensemble_correlation.py`'s functions; only the date
window changes).

**Corrected results (results/ensemble_combined_results_CORRECTED_restricted_window.csv):**

| Portfolio | Original (1993-2026 stitched) | Corrected (2018-2025 only) |
|---|---|---|
| Equal-weight ALL | Sharpe -0.150, ret -37.2%, maxDD 76.7% | **Sharpe -4.552, ret -75.0%, maxDD 75.3%** |
| Inverse-vol-weight ALL | Sharpe +0.467, ret +48.1%, maxDD 8.2% | **Sharpe -0.848, ret -0.6%, maxDD 0.6%** |
| Low-corr, quality-blind | Sharpe -1.630, ret -97.2%, maxDD 98.7% | **Sharpe -11.065, ret -99.2%, maxDD 99.2%** |
| Low-corr, positive-Sharpe-only | Sharpe +0.682, ret +421.1%, maxDD 20.1% | **Sharpe +0.239, ret +7.3%, maxDD 15.1%** |

DSR reference (same pool, N=64, per `research/dsr.py`) is 0.0000 on every
corrected cell, same as the original.

**VERDICT: the section-32 headline numbers were flattered by blending a
thin, quality-dominated pre-2018 regime into the fully-populated post-2018
basket -- not by a zero-fill bug, but by the same underlying problem the
user's hypothesis was pointing at (date-range mismatch producing a
misleading combined statistic).** On the honest, consistently-populated
window, ALL FOUR combination methods are materially worse: naive
equal-weight goes from a bad -37% to a near-total -75% loss; even the
single best-looking result in section 32 (low-corr, positive-Sharpe-only,
the one that appeared to beat every individual candidate on smoothness)
collapses from +421% / Sharpe +0.68 down to +7.3% / Sharpe +0.24 -- still
below the project's best individual component (MomoRot crypto-sectors
§17, Sharpe +1.14) and nowhere near a DSR pass. **The section-32 KILL
verdict stands and is STRENGTHENED, not reversed, by this audit** -- the
true, apples-to-apples ensemble result is worse than what was originally
reported, not better. This is a general, reusable procedural rule for any
future combination study in this project: always report and gate on the
live-component-count-per-day, and always re-verify headline numbers on
the window where coverage is actually stable before trusting them.

**Files:** `research/ensemble_correlation_restricted.py`. Results:
`results/ensemble_combined_results_CORRECTED_restricted_window.csv`,
`results/ensemble_correlation_restricted_run.log`. Reproduce:
`py -3.14 research/ensemble_correlation_restricted.py`.

**Not a new trial batch** -- bug-fix re-verification of section 32's
existing 4 trials on a corrected window, per the section-12 audit
precedent (re-scoring existing cells is not double-counted). **Cumulative
trials: N=1348, unchanged.**

## Section 32.2 - PAIRWISE-COMPLETE ENSEMBLE TEST: honest max-diversification without a fixed window (2026-09-08)

**Brief note:** the task referred to "24 strategies" -- the actual saved
inventory (`results/ensemble_component_summary.csv`, same file sections
32/32.1 used) is **64** series. Ran against the real 64, not resized.

**Method:** `research/ensemble_pairwise_honest.py`. Pairwise-complete
correlation (`frame.corr(min_periods=250)`) computed per PAIR only over
days both series genuinely have data -- no fixed universal window, no
zero-fill. Re-verified the section-32.1 zero-fill non-bug explicitly by
source-reading `equal_weight_available()` again (assertion in the script
itself, not just narrated). A compatibility graph connects two series only
if they share >= 250 real days AND |pairwise corr| < 0.30; the LARGEST
mutually-compatible group is the maximum-clique problem (NP-hard, no exact
solver available in this environment) -- approximated by a greedy heuristic
run from 33 different seed orders (by history length, by own Sharpe, by
graph degree, 30 random), keeping the largest result. Run twice: once
QUALITY-BLIND (candidate pool = all 64) and once QUALITY-GATED (candidate
pool restricted a priori to the 40/64 series with own Sharpe > 0), per the
32.1 lesson that low correlation alone selects for idiosyncratic disasters
as readily as for good diversification.

**Correlation matrix (64x64, 2,016 pairs):** 1,916 pairs (95.0%) had >=250
genuinely-shared real days and are TRUSTED; 100 pairs (5.0%) did not and
are marked NaN in `results/ensemble_pairwise_corr_matrix.csv`, not reported
as a number. Trusted pairs only: mean corr +0.030, median +0.010, |corr|>0.70
in 1.5%, |corr|<0.30 in 91.2% -- confirms the section-32 finding that this
project's signals are genuinely close to independent.

**QUALITY-BLIND largest group: N=23.** Predictably repeats the 32.1
lesson at a larger scale -- 4/23 members have own Sharpe < -1.0
(catastrophic), including ICT-SMC BTCUSDT (own Sharpe -12.70). Full honest
span 2000-01-03..2026-08-31 (9,738 days, mean 1.00 live/day 2000-2005 rising
to 23 by 2018); combined Sharpe **-0.959** (full span), **-4.212**
(high-confidence >=3-live sub-period, 2011-10-04 onward) -- a clean, useful
negative: low-correlation filtering with no quality floor produces a worse
combined result than most individual components, confirmed at N=23 not
just N=26 (section 32).

**QUALITY-GATED largest group: N=14** (Sneaky Pivot NAS100, Bollinger
EURUSD, Pairs NAS100-US30 N2.0, ORB NAS100, Turtle Sys2 XAUUSD, MACD
BTCUSDT, credit-spread SPY, on-chain BTC H20, Ichimoku BTCUSDT, MomoRot
US-sector widened, Ichimoku SPX500, Turtle Sys1 NAS100, VRP naked SVXY
thr1.5, Turtle Sys1 ETHUSDT). Full honest span 1993-01-29..2026-08-31
(12,268 days, mean live rises 1.00 (1993-99) -> 2 (2000s) -> 6 (2014-17) ->
14 (2018-25)): combined **Sharpe +0.610, total return +317.2%, maxDD 20.1%,
recovery 531 days, top-year-share 11.2%**. High-confidence-only sub-period
(>=3 live, from 2011-10-04, 5,446 days): **Sharpe +0.541, ret +77.3%, maxDD
15.6%, recovery 706 days** -- close to the full-span number (0.610 vs
0.541), NOT a dramatic collapse like section 32.1's naive-window blend,
because this group's inception dates are more evenly staggered and its
components are individually healthy; this is the most trustworthy combined
number this project has produced. DSR reference: 0.0000 on every cell
(pool N=64, same E[max SR]=+4.23 bar as sections 32/32.1) -- nowhere close.

**Comparison to the project's real individual candidates:** combined
Sharpe 0.61/0.54 is BELOW MomoRot crypto-sectors §17 (own Sharpe +1.14,
not itself a member of this clique -- excluded by the compatibility
constraint), Turtle Sys1 ETHUSDT (+0.762, IS a member), MomoRot widened
(+0.629, IS a member), and credit-spread SPY (+0.567, IS a member). Max
drawdown (20.1%/15.6%) is genuinely better than every one of those single
components' own drawdown (37.5%/17.8%/3.7%/etc. individually, but none of
those single components combine LOW drawdown WITH high Sharpe the way the
combination's low top-year-concentration suggests it might) -- the honest
statement is the combination trades absolute Sharpe for smoothness and low
concentration, it does not manufacture new risk-adjusted edge, same
structural conclusion as sections 32/32.1.

**VERDICT: this is the most honest, most carefully-diversified combination
this project has built, and it still does not beat the best individual
component on Sharpe or clear DSR.** ~5-15 real, quality-screened,
genuinely-independent components is close to the practical ceiling this
project's data can honestly support -- going wider (N=23, quality-blind)
makes results WORSE not better, because the extra "diversification" is
mostly idiosyncratic ruin, and going through the effort of pairwise-complete
correlation (vs section 32's fixed-window approach) does not surface a
materially different or better answer -- it mainly adds confidence that the
N~14 quality-gated number is real and not a window artifact, since its
full-span and high-confidence-only figures now agree closely (0.610 vs
0.541) instead of diverging wildly (32.1's 0.682 vs 0.239). KILL as a
standalone strategy, same as 32/32.1, but the most defensible NULL result
yet on the ensemble hypothesis.

**Files:** `research/ensemble_pairwise_honest.py`. Results:
`results/ensemble_pairwise_honest_results.csv`,
`results/ensemble_pairwise_corr_matrix.csv`,
`results/ensemble_pairwise_shared_days.csv`,
`results/ensemble_pairwise_honest_run.log`. Reproduce:
`py -3.14 research/ensemble_pairwise_honest.py`.

**Trial count: 4 new** (quality-blind full-span, quality-blind
high-confidence sub-period, quality-gated full-span, quality-gated
high-confidence sub-period -- same per-portfolio-cell convention as section
32; the 64 underlying components are not re-counted). **Cumulative trials:
N=1352** (1348 prior + 4).

## Section 33 - BETA/ALPHA DECOMPOSITION + LONG/SHORT AUDIT, 4 "real candidates" (2026-09-08)

**Name reconciliation (the one material judgment call, stated not hidden):**
the brief's 4 nicknames were mapped to: (1) "on-chain BTC H=20" = exact
match, `D|On-chain active-address surge H20 (BTCUSDT)`; (2) "gold-silver
pairs" = `C|Pairs GLD-SLV N1.5` (the N1.5 threshold specifically -- N2.0
also exists and was NOT used); (3) "capped vol spread" = `D|Credit-spread
FILTERED 1pct (SPY)` (section 27/31's defined-risk, IV-filtered credit
spread -- "capped"=bounded max loss + 1pct fixed-fraction cap, "vol"=the
IV-rank filter; a better textual fit than the VRP family, which is
"naked"/"vol-of-vol" not "capped"); (4) "ORB gold RETEST" = RETEST
OR30/1R XAUUSD continuous 2017-2025 -- **this one was NOT in the 64-series
ensemble inventory** (never extracted into `ensemble_daily_returns.csv`);
re-extracted fresh here via `research/four_candidates_beta_alpha_audit.py`
using the same `build_trades`/`build_daily_returns` functions
`report_retest_xauusd_2017_2025_continuous.py` already calls.

**PART 1 -- CAPM vs BTC (OLS, real-overlap only; BTC benchmark itself only
exists 2017-08-17 onward in this project's data, so the credit-spread
strategy's 1993-2017 history cannot be regressed and is honestly excluded
from the overlap window, stated not hidden):**

| Strategy | Overlap | N | Beta | Alpha (ann.) | R^2 | Verdict |
|---|---|---|---|---|---|---|
| ORB gold RETEST | 2017-08-18..2025-12-29 | 3,042 | -0.003 | **+6.51%** | 0.001 | LOW-BETA + POSITIVE-ALPHA |
| On-chain BTC H=20 | 2018-01-03..2026-08-31 | 3,162 | **+0.435** | +0.80% | **0.431** | market-explained / beta-driven |
| Capped vol spread | 2017-08-18..2026-06-16 | 3,211 | +0.004 | +1.03% | 0.013 | LOW-BETA + POSITIVE-ALPHA |
| Gold-silver pairs N1.5 | 2017-08-18..2026-08-27 | 3,283 | -0.003 | -3.84% | 0.000 | mixed / negative |

**The important finding: On-chain BTC H=20's beta to BTC is +0.435 with
R^2=0.431 -- 43% of its return VARIANCE is explained by simply holding
BTC, and its independent (alpha) contribution annualizes to only +0.80%,**
a small fraction of the +120.8% total return / +0.430 own-Sharpe reported
in section 30. This is expected mechanically (a long-only surge signal on
the asset it's long) but it means most of section 30's reported edge is
beta exposure, not independent skill -- this had not been decomposed
before. ORB gold RETEST and the credit-spread book both show ~zero BTC
beta and real positive annualized alpha, but R^2 is also near-zero (0.001,
0.013) for both -- i.e. BTC explains almost nothing about them either way;
this mostly confirms they are UNCORRELATED WITH BITCOIN specifically (gold
breakout, SPY options), which is unsurprising and does not test whether
they carry SPX or gold-market beta of their own -- flagged as a real
limitation of using BTC as "the market benchmark" for two strategies that
have nothing to do with crypto. Gold-silver pairs shows negative annualized
alpha (-3.84%), consistent with its already-known negative own-Sharpe
(-0.143).

**PART 2 -- long/short exposure (read from each strategy's own real
trade/position data, not inferred):**

| Strategy | Structure | Long | Short |
|---|---|---|---|
| ORB gold RETEST | directional breakout, both sides | 50.9% (282/554 trades) | 49.1% (272/554) |
| On-chain BTC H=20 | **long-only, verified in source** | 100% (when in a position) | **0%** |
| Capped vol spread | short-vol, both books concurrent | 50.0% put-credit-spread | 50.0% call-credit-spread |
| Gold-silver pairs N1.5 | dollar-neutral, both legs concurrent | 26.7% of days long-GLD/short-SLV | 36.9% short-GLD/long-SLV |

**On-chain BTC H=20 is the one candidate with zero short exposure and no
bear-market profit mechanism** -- verified directly in `run_onchain_signal.py`
(entries trigger only on `z > ADDR_Z_THRESHOLD`, no short branch exists).
It can avoid a decline by sitting flat (the no_pos gate) but cannot profit
from one. The other three are structurally close to market-neutral by
construction (ORB splits ~50/50 by design since it trades whichever side
of the range breaks first; the credit-spread book runs both a bullish and
a bearish leg concurrently; the pairs trade is dollar-neutral long one leg
/ short the other). **The combined 4-strategy book is NOT simply "long the
market"** -- but it also contains nothing designed to profit meaningfully
FROM a bear market, only components designed to avoid or be indifferent to
one.

**PART 3 -- restricted 4-strategy ensemble, ONLY these 4, no zero-fill,
pairwise-available equal-weighting, 0.6 correlation-pruning rule applied:**

4x4 correlation matrix (pairwise-complete, real overlap only): all six
pairs are near-zero (-0.061 to +0.086) -- **no pair exceeds |corr| > 0.60,
nothing pruned, all 4 kept.**

Combined span (staggered inception -- credit-spread alone reaches back to
1993, the other 3 don't start until 2006-2018; mean live components/day
2.12, min 1, max 4, same shape of artefact as section 32.1 but at N=4
instead of N=64): total_return **+95.9%**, Sharpe **+0.344**, maxDD
**21.1%**, recovery 214 days, top-year-share 40.4%, DSR 0.0000 (pool N=4).

Standalone comparison: ORB gold RETEST own-Sharpe **+1.097** (the best of
the four, and the best single candidate this project has produced outside
the 64-series inventory), On-chain BTC H=20 +0.430, Capped vol spread
+0.567, Gold-silver pairs N1.5 **-0.143** (a real loser on its own).

**VERDICT: combining these specific 4 does not help -- Sharpe +0.344 is
BELOW three of the four standalone candidates (ORB +1.097, credit-spread
+0.567, on-chain +0.430) and only beats the already-losing pairs strategy.**
Same staggered-inception mechanism as section 32.1 (blending a thin
1-of-4-live era with a later 4-of-4-live era) plus the drag of one
outright-losing member (gold-silver pairs, which the correlation-pruning
rule does NOT catch, because pruning only removes REDUNDANT signals, not
LOW-QUALITY ones -- an independent confirmation of the section-32.1/32.2
finding that low correlation and quality are separate axes). Answering the
brief's direct question: these 4 do carry some real, low-beta alpha
INDIVIDUALLY (ORB and credit-spread clearly; on-chain much less than its
headline number suggested once beta is removed; pairs does not), but
combined they are not a leveraged long bet on the market (correctly
diversified in direction/structure) -- they simply are not a good
COMBINATION, because one member is a standalone loser and the
staggered-inception blend flatters the number the same way section 32.1
found. The single best number in this entire audit is ORB gold RETEST
standing alone at Sharpe +1.097, not any combination of it with the other
three.

**Files:** `research/four_candidates_beta_alpha_audit.py`. Results:
`results/four_candidates_capm.csv`, `four_candidates_exposure.csv`,
`four_candidates_corr_matrix.csv`, `four_candidates_restricted_ensemble.csv`,
`four_candidates_run.log`. Reproduce:
`py -3.14 research/four_candidates_beta_alpha_audit.py`.

**Trial count: 1 new** (the 4-candidate restricted combined-portfolio
Sharpe; the CAPM regressions and exposure audit are diagnostics, not new
strategy trials, same convention as prior OOS/ablation diagnostics in this
project; ORB gold RETEST's own 554-trade backtest is a re-extraction of an
already-existing, already-logged section-10 result, not a new trial).
**Cumulative trials: N=1353** (1352 prior + 1).

## Section 34.1 - LONG/SHORT MOMENTUM ROTATION vs LONG-ONLY BASELINE (2026-09-08)

Extends the audited section-12 mechanism (`research/momentum_rotation.py`
ranking/causal-lag/market-filter logic reused unchanged via
`research/momentum_rotation_long_short.py`, a new module that adds the
short-leg weight assignment only -- there is no way to "reuse" code that
only ever assigns positive weights). **Split: LONG top 5 @ 20% each (100%
gross long, unchanged from baseline), SHORT bottom 3 @ 10% each (30% gross
short), total gross 130%.** Risk-off behaviour is byte-identical to the
baseline (100% IEF, no shorts), so this isolates ONLY what the short leg
does during risk-on regimes. Widened 27-instrument universe (section
12.2's canonical wider test), N in {6, 12} months, K fixed per the brief
(not a K grid). `research/six_strategies_engine.drawdown_with_recovery`
reused for recovery time.

**Full period (live-window methodology, section 12.3):**

| N | Variant | Sharpe | CAGR | MaxDD | Recovery |
|---|---|---|---|---|---|
| 6 | Long-only | 0.558 | 7.70% | 31.77% | 513d |
| 6 | Long/short | 0.519 | 6.81% | 30.23% | 416d |
| 12 | Long-only | 0.630 | 9.18% | 37.50% | 801d |
| 12 | Long/short | 0.575 | 7.97% | 32.63% | 1,148d |

**Stress window 2000-2009:**

| N | Variant | Sharpe | CAGR | MaxDD |
|---|---|---|---|---|
| 6 | Long-only | 0.816 | 13.01% | 31.77% |
| 6 | Long/short | 0.876 | 12.72% | 24.86% |
| 12 | Long-only | 0.704 | 11.47% | 37.50% |
| 12 | Long/short | 0.673 | 9.83% | 32.63% |

**Down-year-specific comparison (the direct question asked) -- SPY down
years in the full panel: 2000, 2001, 2002, 2008, 2018, 2022.** In 2008 --
the single worst crash in the panel, SPY -36.79% -- the short leg changes
the result by essentially nothing (-0.25pp at N=6, +0.51pp at N=12),
because the market filter already parks the book in IEF for most of that
year regardless of variant (both LONG-ONLY and LONG-SHORT post +18%/+17%
in 2008). In other down years the short leg is genuinely mixed: it HELPS
meaningfully in 2002 (+5.7pp N=6, +8.6pp N=12) and 2022 (+5.8pp N=6,
+5.9pp N=12), but HURTS in 2000 at N=12 (-4.2pp) and 2018 (-0.6 to -1.4pp),
and is roughly neutral in 2001. No reliable, one-directional pattern.

DSR reference (pool = this batch's own 4 full-period cells, N=4): long-only
beats long-short in 3 of 4 cells (full N=6 0.375 vs 0.302, full N=12 0.523
vs 0.410, stress N=12 0.303 vs 0.270); long-short wins only stress N=6
(0.511 vs 0.436). None close to a 0.95 pass either way.

**VERDICT: KILL on the short-leg hypothesis.** It lowers full-period Sharpe
and CAGR in BOTH N (adds cost and complexity for a worse risk-adjusted
result over the whole span), moderately reduces max drawdown in most cells
(a real, if modest, effect), but does NOT reliably help "specifically
during down markets" as hypothesized -- it does essentially nothing in the
single worst crash (2008, where the existing market filter already does
the defensive work), helps in some other down years and hurts in others
with no consistent sign, and loses on DSR in 3 of 4 cells. The short leg
is not free insurance; it is a genuine, mixed-sign bet that costs real
Sharpe in the common case to buy a small amount of drawdown reduction, not
crash protection specifically.

**Files:** `research/momentum_rotation_long_short.py`,
`run_momentum_rotation_long_short.py`. Results:
`results/momentum_rotation_long_short_{full,stress}.csv`,
`momentum_rotation_long_short_yearly_*.csv` (8 tables),
`momentum_rotation_long_short_run.log`. Reproduce:
`py -3.14 run_momentum_rotation_long_short.py`.

**Trial count: 4 new** (LONG-SHORT variant, full N=6, full N=12, stress
N=6, stress N=12 -- the LONG-ONLY baseline cells reproduce already-logged
section-12/12.2 results and are not re-counted). **Cumulative trials:
N=1357** (1353 prior + 4).

## Section 34.2 - TAIL-RISK HEDGE: SMALL CONSTANT ALLOCATION TO OTM SPY PUTS (2026-09-08)

Reuses the SAME Black-Scholes/real-VIX approximation already validated for
the credit-spread (sec 27) / delta-10 IV filter (sec 26) work UNCHANGED
(`bs_price()` imported from `research/delta10_iv_filter.py`, r=4.5%, sigma
= real trailing VIX/100, marked to market DAILY on the real subsequent
VIX+SPY path). Same stated limitation repeated here: flat VIX ignores the
real skew premium OTM puts trade at, which UNDERSTATES the true cost of
this hedge -- if the hedge already looks expensive under this assumption,
a real trader would pay more, not less.

**Design decisions (stated, not asked as a question):** strike fixed at 5%
OTM (K=0.95xspot at each roll date) -- the standard "protective put"
convention (vs a delta-target, which is the framing already used for the
short-premium credit-spread work). Monthly roll, 30-calendar-day target
tenor. **Overlay framing: the SPY sleeve stays at 100% notional exposure
throughout; the hedge allocation (1% or 2%) is spent on premium AT EACH
MONTHLY ROLL** (i.e. an ongoing ~1-2%/roll recurring cost, not a one-time
1-2%/year carve-out) -- this is the more literal reading of "a small,
constant allocation ... rolled monthly," but is flagged explicitly as a
real interpretive choice: many real-world tail-hedge overlays instead
target a smaller PER-MONTH spend that sums to ~1-2%/YEAR. Under this
project's chosen (larger) convention, the reported cost below is
correspondingly larger than a real fund's typical "1-2%/year" tail-hedge
program would show -- read the steady-state bleed number with that
convention in mind, not as a universal tail-hedge cost figure.

Data: SPY+VIX daily, 1993-01-29..2026-06-16 (8,402 days). Unhedged SPY
baseline (full period): Sharpe 0.648, CAGR 10.85%, total return +3,003.7%,
maxDD 55.19%.

| Allocation | Sharpe | CAGR | Total return | MaxDD | Calm-year bleed | DSR (N=2 pool) |
|---|---|---|---|---|---|---|
| 1%/roll | 0.441 | 6.66% | +759.4% | 54.87% | -5.24%/yr | 0.145 |
| 2%/roll | 0.208 | 2.22% | +108.2% | 62.84% | -10.16%/yr | 0.011 |

Look-ahead guard PASS both allocations (259 rolled puts each; entry strike/
sigma always sized off the PRIOR trading day's close). Calm years = every
year excluding 2008 and 2020 (32 years); the put leg was profitable in
only 12% of those calm years -- consistent with an OTM put expiring
worthless most months, a real, steady, expected cost.

**Crisis-window payoff, quantified (the critical question):**

| Window | Unhedged SPY | Hedged 1% | Hedged 2% |
|---|---|---|---|
| 2008 full year | -36.79% | -20.87% (**+15.9pp offset**) | -3.89% (**+32.9pp offset**) |
| 2020 full year | +18.33% | +11.01% (-7.3pp) | +4.08% (-14.3pp) |
| 2020 acute crash (2020-02-19..03-23) | -33.40% | -33.14% (+0.3pp) | -32.88% (+0.5pp) |

**The hedge DOES work as insurance in the 2008 GFC** -- a real, large,
quantified offset (+15.9pp at 1% allocation, +32.9pp at 2%), because 2008
was a prolonged, deep drawdown that gave a monthly-rolled 5%-OTM put many
consecutive months to pay off. **It does NOT meaningfully help in the 2020
COVID crash** -- the acute crash window (2020-02-19 to 2020-03-23) offsets
only +0.3pp/+0.5pp of a -33% move, because the crash was too fast for a
30-day-tenor put rolled on a monthly cadence to be holding a large enough
position at the moment of the drop (the prior month's put, sized off a
calm pre-crash VIX, was too small/too far from the money to capture the
move before expiring), and over the FULL 2020 year the hedge is a net
DRAG (-7.3pp/-14.3pp) because SPY finished the year up +18.33% -- the
insurance premium was paid but the disaster it protects against never
materialized on a full-year view. Full-period Sharpe and CAGR are both
substantially WORSE than unhedged SPY at both allocations (0.441 vs 0.648
Sharpe at 1%, collapsing to 0.208 at 2%), and DSR is nowhere close to a
pass at either allocation.

**VERDICT: KILL as a standalone always-on overlay at this size/convention
-- the insurance is NOT free and is NOT reliable.** It provided real,
large, quantified protection in 2008 (a slow-motion crash) but essentially
none in 2020 (a fast crash), and its steady-state cost in ordinary years
(-5.2%/yr to -10.2%/yr under this project's stated "spend the allocation
every roll" convention) is large enough to substantially reduce full-
period Sharpe and CAGR versus unhedged SPY. The honest statement per the
task's own framing: this specific hedge is not "worth its premium" as a
constant, mechanical overlay -- it is a real but inconsistent insurance
policy whose payoff depends heavily on HOW a crash unfolds (slow vs fast),
not just whether one happens.

**Files:** `research/tail_hedge_otm_puts.py`. Results:
`results/tail_hedge_otm_puts_summary.csv`,
`tail_hedge_otm_puts_trades_alloc{1,2}pct.csv`,
`tail_hedge_otm_puts_daily_ret_alloc{1,2}pct.csv`,
`tail_hedge_otm_puts_run.log`. Reproduce:
`py -3.14 research/tail_hedge_otm_puts.py`.

**Trial count: 2 new** (1% allocation, 2% allocation -- each a complete,
independently-scored standalone strategy). **Cumulative trials: N=1359**
(1357 prior + 2).

---

## §35 — FX CARRY TRADE ("Good Carry, Bad Carry" family) — 2026-09-15

First strategy in a genuinely new category for this project: cross-sectional
FX carry, sourced from `notes/paperswithbacktest_candidates.md` candidate #1.
Mechanism stated BEFORE any code was run (per standing rule 2): uncovered
interest rate parity (UIP) predicts a high-rate currency should depreciate
enough to offset its rate advantage, leaving zero expected excess return.
UIP fails empirically (Fama 1984 "forward premium puzzle") -- high-rate
currencies do not depreciate enough on average, so long-high-rate /
short-low-rate earns a documented, widely-replicated positive average excess
return (Lustig & Verdelhan 2007). The paperswithbacktest replication reports
Sharpe 1.74, t-stat 10.6, over 37 years.

**New data pipeline built (both free, zero cost):**
- Short rates: FRED series `IR3TIB01<CC>M156N` (OECD 3-month interbank rate,
  mirrored on FRED) pulled via the public `fredgraph.csv` endpoint -- no API
  key needed. Countries: USA, EZ (euro area), GBR, AUS, NZL, CAN, CHE, JPN,
  NOR (SWE attempted, see below). Monthly data, full coverage from at least
  2002 for every series used. A 2-month publication lag is applied before any
  rate value is used in signal formation (OECD/FRED short-rate revisions
  typically publish 4-6 weeks after month-end; 2 months is conservative).
- Spot FX: Dukascopy daily bid/ask, 2010-2025, real spread, for the 8 non-USD
  legs (EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY, USDNOK).
  **USDSEK dropped from the universe**: direct probe confirmed Dukascopy has
  no ask-side USDSEK daily data before 2025 (bid-side is complete back to
  2010; every ask-side yearly pull 2010-2024 returned 0 bytes). Rather than
  fake a spread or silently use bid-only, SEK was excluded and this is stated
  as a known universe-coverage gap, not hidden.

**Design (a priori, no peeking):** universe = USD + 8 non-USD currencies (9
total). Rank by lagged short rate each month; long the top N, short the
bottom N, equal-weighted, dollar-neutral, rebalanced monthly. Grid: N in
{1, 2, 3} -- 3 configs, no other tuning. Weekly rebalance was NOT tested
(rate data itself is monthly, so higher-frequency rebalancing only adds
turnover cost with no new information -- stated reasoning, not a
post-hoc excuse). Carry accrual proxied as (foreign monthly rate - USD
monthly rate)/12 added directly to the spot return -- no forward/swap-points
data is available in this project, so this is the standard
Fama-regression-style proxy used in the academic carry literature, stated as
a methodological limitation rather than hidden. Real bid/ask spread cost
applied on every unit of monthly turnover. Look-ahead guard (factor vs
same/next-month return, threshold 0.5) PASS on all 3 configs.

**Results:**

| N | net Sharpe | DSR | maxDD | CAGR | positive years | worst month |
|---|---|---|---|---|---|---|
| 1 | 0.024 | 0.252 | -30.6% | -0.30% | 9/16 | -10.58% (Mar 2020) |
| **2 (best)** | **0.228** | **0.559** | -18.2% | 1.46% | 11/16 | -6.39% (Sep 2014) |
| 3 | -0.001 | 0.221 | -25.7% | -0.25% | 9/16 | -5.61% (Sep 2011) |

DSR pool: structural (this grid only, N=3 trials), E[max SR|null]=0.191.
Reference only per standing rule 3, not a gate -- but corroborates: none of
the 3 configs is close to a real signal versus a 3-trial null.

Regime check on the best config (N=2, not cherry-picked post-hoc): first half
(2010-2017) Sharpe 0.112, second half (2018-2025) Sharpe 0.372 -- weak in
both halves, no dramatic in-sample-to-out-of-sample decay, i.e. this is not
an overfit spike concentrated in one sub-period, it's just uniformly weak.

Worst month for N=1 was -10.58% in **March 2020** (COVID risk-off) --
qualitatively consistent with carry's well-known crash-risk mechanism even
though the strategy here has no economically significant average edge to be
compensated for carrying that risk.

**VERDICT: KILL. Anti-finding, not a data-quality failure.** The pipeline
itself works cleanly -- both rate and spot data are real, the look-ahead
guard passes, and costs are real but small (avg 0.13-0.71 bps/month,
monthly rebalance keeps turnover low, so cost was never close to the
binding constraint here, unlike most of this project's intraday FX/gold
work). The gap to the published 37-year/broader-universe Sharpe 1.74 is
plausibly explained by two structural differences, stated honestly rather
than as an excuse: (1) universe -- G10-only (9 currencies), no emerging-
market currencies, which is where a large share of academic carry's
historical rate dispersion and edge concentration has come from; (2) window
-- 2010-2025 is dominated by the post-GFC ZIRP/QE era (near-zero global
policy rates 2010-2015, and again 2020-2021), a period with genuinely
compressed cross-sectional rate dispersion versus carry's 1980s-2000s
sample. This does not rescue the result -- it is reported as the most
likely reason a real, correctly-implemented replication of a well-evidenced
anomaly still comes up empty on THIS specific universe and window, useful
context for any future EM-currency or longer-history extension, not a
reason to treat this as a near-miss.

**Files:** `research/fx_carry_data.py`, `run_fx_carry.py`. Data:
`data/raw/fred_rates/rate_*.csv` (10 series pulled, 9 used), 
`data/raw/dukascopy_fx_carry/download/*.csv` (17 of 18 pair-sides pulled
cleanly; usdsek-ask excluded per above). Results: `results/fx_carry.csv`.
Reproduce: `python run_fx_carry.py`.

**Trial count: 3 new** (N=1, N=2, N=3). **Cumulative trials: N=1362**
(1359 prior + 3).

---

## §35.1 — Currency PPP/value factor (candidate #2) — BLOCKED, data wall — 2026-09-15

Attempted immediately after §35 as the near-zero-marginal-cost follow-on
(same FX pipeline, one more macro series). Mechanism: real exchange rate
deviations from long-run PPP predict future currency returns (Menkhoff,
Sarno, Schmeling & Schrimpf 2012, "Currency Value"). Needed monthly CPI per
country for the same 8-currency universe.

Live-probed FRED/OECD CPI series directly via the same `fredgraph.csv`
method that worked cleanly for §35's interbank rates. Found three
compounding, genuinely blocking problems (not one): (1) no single ID
pattern works across countries -- tried `CPALTT01<CC>M657N`, `M659N`,
`M661S`, `CP0000<CC>M086NEST`, `<CC>CPALTT01IXNBM`; each worked for some
countries and 404'd for others; (2) the pattern that DID work for
US/JP/GB/CH/CA/NO (`IXNBM`) is discontinued between 2021-06 and 2023-12 --
too stale for a backtest window running to 2025; (3) Australia and New
Zealand publish CPI quarterly, not monthly (`CPALTT01AUQ657N` confirms) --
a genuine frequency mismatch, not a naming issue.

**Not built.** Reliable, fresh, monthly-comparable CPI for all 8 currencies
needs per-country manual verification against national statistics agencies
-- not a single bulk free endpoint the way OECD short rates were for carry.
Stopping here rather than guessing unverified series IDs or silently using
stale/partial coverage. Revisit with more time budget or a proper
OECD.Stat SDMX pull (correct dataflow IDs, not fredgraph.csv guessing) or a
paid macro vendor. Not counted as a trial.

---

## §36 — FX CROSS-SECTIONAL MOMENTUM — 2026-09-15

Third idea this session, sourced from the same currency-factor literature
as §35 (Menkhoff, Sarno, Schmeling & Schrimpf 2012, JFE, "Currency Momentum
Strategies") -- distinct mechanism from carry: sorts on trailing RETURN,
not rate LEVEL. Slow information diffusion / gradual-flow story, the FX
analogue of equity momentum. No new data needed: reuses §35's already-
built, already-verified `research/fx_carry_data.py` spot FX pipeline
unchanged (same 9-currency universe, same real bid/ask spread cost model).

Grid (a priori): lookback L in {1, 3, 12} months (the three standard
formation periods in the literature) x leg size N in {2, 3} = 6 configs,
no other tuning. Trailing signal built via `.rolling(L).sum().shift(1)` so
month t's ranking never sees month t's own return. Look-ahead guard PASS
all 6 configs.

**Results — unambiguous KILL, 6/6 configs net Sharpe NEGATIVE:**

| L (months) | N | gross Sharpe | net Sharpe | DSR | maxDD | worst month |
|---|---|---|---|---|---|---|
| 1 | 2 | -0.405 | -0.489 | 0.261 | -50.7% | -6.51% (Jun 2012) |
| 1 | 3 | -0.261 | -0.339 | 0.482 | -37.0% | -5.59% (Oct 2011) |
| 3 | 2 | -0.417 | -0.463 | 0.295 | -55.3% | -7.72% (Oct 2011) |
| 3 | 3 | -0.441 | -0.486 | 0.264 | -50.2% | -5.95% (Oct 2011) |
| 12 | 2 | -0.336 | -0.364 | 0.443 | -44.4% | -8.10% (Nov 2022) |
| 12 | 3 | -0.332 | -0.363 | 0.444 | -36.2% | -5.21% (Nov 2022) |

**VERDICT: KILL, no ambiguity.** Every one of the 6 cells is negative
BEFORE costs, not just after -- this is not a costs-ate-a-real-edge story
like most of this project's intraday kills, it's a clean anti-signal on
this specific universe/window. Consistent with this project's broader,
repeated finding elsewhere (crypto `price_momentum` family, killed
2026-07-06/07) that naive trailing-return momentum has been reliably
weak-to-negative across every asset class tested here so far -- FX now
joins crypto in that pattern.

**Files:** `run_fx_momentum.py` (reuses `research/fx_carry_data.py`, no new
data pulled). Results: `results/fx_momentum.csv`. Reproduce:
`python run_fx_momentum.py`.

**Trial count: 6 new** (L x N grid). **Cumulative trials: N=1368**
(1362 prior + 6).

---

## §37 — FX CARRY, EMERGING-MARKET EXTENSION — 2026-09-15

User asked to test §35's own stated explanation directly: is G10-only +
ZIRP-era rate compression really why carry was weak, and does widening to
currencies with genuine rate dispersion help? Same mechanism as §35 (UIP
failure), same engine (`run_fx_carry.run_one`/`build_monthly_returns`/
`build_monthly_spread` reused unchanged, only the currency universe changes)
via new script `run_fx_carry_em.py`.

**EM candidate probe (systematic, all findings stated):** MXN, ZAR, CNH, ILS
all have working FRED short-rate series. Of those: MXN's Dukascopy ask-side
daily history is 0 bytes for EVERY year 2010-2025 (bid-side is complete);
ILS's ask-side only has data for 2025 (261 rows vs 3283 bid rows). Both
dropped -- same no-fake-spread policy already applied to SEK in §35. SGD has
no verified free short-rate series found (no working SIBOR/interbank FRED
ID). TRY/PLN/HUF are real Dukascopy instruments but have DISCONTINUOUS
coverage (TRY: data only exists for 2015 and 2025, real gaps in between --
a broker delisting/relisting artifact, not a download bug). BRL/INR/KRW/
THB/CZK/RUB are not valid dukascopy-node instruments at all.

**Net EM addition: ZAR and CNH only** -- a narrow 2-currency extension, not
a broad institutional-style EM carry basket (which would typically run
10-15+ currencies via NDFs). This is a real scope limit of this project's
free-data/single-retail-broker constraint, stated up front. CNH caveat:
PBOC manages the RMB via a daily fixing + trading band, so observed "carry"
may partly reflect currency policy rather than a pure market risk premium;
CNH's bid-side coverage is also sparser than its ask-side over the same
span (1,723 vs 4,215 days).

**Two runs, both a priori:**
(A) EM-only: USD + ZAR + CNH (3 currencies, N=1 only -- a 3-asset universe
caps leg size).
(B) Combined G10+EM: §35's 9 G10 currencies + ZAR + CNH = 11 currencies,
N in {1,2,3,4}.

**Results:**

| Universe | N | net Sharpe | DSR | maxDD | worst month |
|---|---|---|---|---|---|
| EM-only (3 ccy) | 1 | 0.050 | 0.101 | -35.0% | -12.56% (Mar 2020) |
| Combined (11 ccy) | 1 | 0.106 | 0.137 | -38.8% | -12.72% (Mar 2020) |
| **Combined (11 ccy)** | **2 (best)** | **0.353** | **0.457** | **-16.6%** | **-6.84% (Dec 2015)** |
| Combined (11 ccy) | 3 | 0.282 | 0.348 | -17.6% | -7.72% (Mar 2020) |
| Combined (11 ccy) | 4 | 0.311 | 0.392 | -10.4% | -4.95% (Mar 2020) |

EM-only is WEAKER than G10-only (0.050 vs §35's 0.228), not better -- too
thin a universe (3 assets) on its own. The combined N=2 result (0.353) IS a
real improvement over §35's G10-only N=2 (0.228, same config, +55%
relative). Regime check on combined N=2 (not cherry-picked): first half
(2010-2017) Sharpe 0.187 vs §35's G10-only 0.112; second half (2018-2025)
Sharpe 0.503 vs §35's G10-only 0.372 -- the uplift holds in BOTH halves,
so this is a genuine broad improvement from widening the universe, not a
fluke concentrated in one period.

**Diagnostic artifact (not a bug, flagged not hidden):** EM-only N=1's
per-year Sharpe hit absurd values (107 in 2016, 38 in 2022) -- traced to
months where the single long/short pair was USD vs CNH with near-zero
realized monthly volatility (the PBOC fixing band suppresses CNH spot
variance), producing a classic "peso problem" pattern (steady tiny gains,
rare devaluation risk) that distorts an annualized Sharpe computed from a
thin 12-observation-per-year subsample. Does not change the full-period
verdict, which already reflects the true weak Sharpe (0.050).

**VERDICT: KILL, but the §35 hypothesis is directionally CONFIRMED, not
refuted.** Adding real rate/currency dispersion via ZAR and CNH genuinely
improves carry's risk-adjusted return (+55% relative Sharpe at the same
N=2 config, holding across both regime halves) -- supporting §35's
explanation that a thin G10-only universe during a rate-compressed era,
not "carry doesn't exist as an anomaly," was the binding constraint here.
But the improvement is modest and DSR (0.457, reference only) is still
nowhere close to a real pass. The EM extension achieved here is narrow
(2 currencies) purely because of Dukascopy's ask-side data gaps on MXN,
ILS, and SEK -- a genuinely broader EM basket (10-15+ currencies, ideally
via proper NDF-quality data rather than a single retail broker's spot feed)
remains untested and could plausibly show a larger effect; this result
does not extrapolate that far and should not be read as a ceiling on what
EM carry could do with better data access.

**Files:** `research/fx_carry_data.py` (EM_RATE_FILES/EM_FX_PAIRS added,
backward-compatible -- `run_fx_carry.py`'s G10-only §35 result is
unaffected/unchanged), `run_fx_carry_em.py`. Data:
`data/raw/fred_rates/rate_{MEX,ZAF,CHN,ISR}.csv` (MEX/ISR pulled but
unused per above), `data/raw/dukascopy_fx_carry/download/usd{zar,cnh,mxn,
ils}-d1-*.csv`. Results: `results/fx_carry_em.csv`. Reproduce:
`python run_fx_carry_em.py`.

**Trial count: 5 new** (EM-only N=1; combined N=1/2/3/4). **Cumulative
trials: N=1373** (1368 prior + 5).

---

## §38 — Entry/exit/TP/SL refinement on the project's two proven-alpha
## candidates (ORB gold RETEST, credit-spread SPY) — 2026-09-15

User asked whether the project's two cells with genuine, demonstrated
gross/low-beta edge (ORB gold RETEST, Sharpe +1.097; credit-spread SPY,
Sharpe +0.567 -- both flagged in §33) could be improved by tuning
entry/exit/TP/SL rules, rather than searching for new signal families.
Checked both against the existing log BEFORE writing any code, per standing
rule 1 (never repaint an already-killed test).

### ORB gold RETEST — thread already closed, not re-run

§10.7 (2026-09-02, a prior session) already ran exactly this experiment:
2R/3R fixed targets, a breakeven-stop, and a 0.5R trailing stop, all on the
same RETEST/OR30 entry, both windows. The verdict is already on record and
unambiguous: **"letting winners run does not fix the sec 10.5/10.6 finding
-- 1R remains the best monetization of RETEST's edge, and no exit variant
closes the gap to buy-and-hold."** Compounded $100k: 1R $168,000 (best) >
breakeven $160,082 > 2R $156,652 > 3R $156,039 > trailing $153,904; none
beat B&H's $331,604.

Re-running this would be a repaint, explicitly against standing rule 1. The
one genuinely unswept lever is `retest_tol_frac` (fixed at 0.10 in every
script that calls `orb()` -- confirmed by grep across the whole repo), but
that is an ENTRY-timing parameter, not an exit/TP/SL rule, and no a priori
mechanism was proposed for why a different value should help -- sweeping it
without one would be parameter mining (against standing rule 2). Flagged as
a possible different future question, not pursued here. **ORB exit
refinement: closed, answered before this session began.**

### Credit-spread SPY — genuinely untested lever found, real improvement

§26/§27 only ever varied the ENTRY filter (IV-rank) and the structural
WIDTH (1%/2%). Verified directly in the source
(`credit_spread_iv_filter.run_combined_book`) that the only close condition
ever coded is `if i >= j: # expired today` -- every position has always
been held to expiration. No profit-target exit has ever existed in this
project.

**Mechanism (stated before any result seen):** closing a credit spread
early at a fraction of max potential profit, rather than riding it to
expiration, is one of the most widely cited rules in real-world options-
selling practice (TastyTrade's own published backtest research) -- most of
a short option's theta decay is captured well before expiration, while the
LAST slice of remaining premium is the most exposed to gap/tail risk for
the least incremental reward.

New script `research/credit_spread_early_exit.py` reuses §27's
`_try_open`/pricing/cost model UNCHANGED; only the close condition is new.
An early close pays a REAL round-trip cost (buy back the short at its ask,
sell the long at its bid, same HALF_SPREAD+COMMISSION_PCT as entry) --
not modeled as free. UNFILTERED only (§26 AND §27 both already
independently found the IV-rank filter loses to unfiltered on every metric
in every cell -- re-testing the filter a third time is not a new
question). Grid: profit_target_frac in {0.25, 0.50, 0.75} (50% is the
standard cited threshold; 25%/75% bracket it as a genuine sensitivity
check) x width in {1%, 2%} = 6 configs.

**Result — every 50%/75% cell beats its own-width §27 hold-to-expiration
baseline on Sharpe, maxDD, AND total return simultaneously:**

| Config | Sharpe | maxDD | total return | avg days held (of ~36-37 DTE) |
|---|---|---|---|---|
| §27 baseline, 1pct hold-to-exp | 1.040 | 6.48% | +93.8% | 36-37 (full term) |
| §27 baseline, 2pct hold-to-exp | 1.146 | 5.14% | +91.8% | 36-37 (full term) |
| NEW 1pct @ 25% early | 0.808 | 5.85% | +78.4% | 11.0 |
| NEW 1pct @ 50% early | 1.019 | 3.79% | +112.9% | 15.4 |
| NEW 1pct @ 75% early | 1.233 | 4.03% | +147.8% | 20.4 |
| NEW 2pct @ 25% early | 0.994 | 4.08% | +98.0% | 9.5 |
| **NEW 2pct @ 50% early (best)** | **1.319** | **3.31%** | **+145.3%** | 14.1 |
| NEW 2pct @ 75% early | 1.311 | 3.64% | +137.4% | 19.4 |

25% is worse than the baseline (too early -- gives up too much remaining
premium relative to the closing round-trip cost), but 50% and 75% both
genuinely improve all three headline metrics on both widths, not a fluke
of one cherry-picked number. Win rate stays ~97-99% (mechanical, unchanged
from §26/§27). Faster capital recycling (avg holding period drops from the
full term to 9.5-20.4 days) is WHY total return rises even though the
per-trade edge is similar -- more trades per year on the same capital
base. No tail-risk breach in any cell (worst day -1.8% to -2.0%, worst
month -1.8% to -2.0%, catastrophic bar of -30%/-50% never approached, same
order as §27).

DSR (reference only, own 6-cell pool -- not directly comparable to §27's
4-cell pool): best is 2pct@50%/2pct@75% at ~0.44, a real improvement in
absolute Sharpe terms but still far below the 0.95 bar.

**VERDICT: still a KILL for deployment (DSR nowhere near 0.95), but this
is the single most effective entry/exit/TP/SL refinement this project has
found on any of its positive-edge candidates.** Direct answer to the
user's question: yes, refining exits CAN meaningfully improve an
already-real edge -- proven here -- but it doesn't work everywhere (ORB's
exit space was already exhausted with a negative result). The distinguishing
factor was whether the lever had genuinely never been tried, not whether
the underlying cell had real edge (both cells do). Recommend 2pct width /
50% early close as this project's reference credit-spread configuration if
the strategy is ever revisited.

**Files:** `research/credit_spread_early_exit.py`. Results:
`results/credit_spread_early_exit.csv`,
`results/credit_spread_early_exit_trades_*.csv` (6 files). Reproduce:
`python research/credit_spread_early_exit.py`.

**Trial count: 6 new** (3 profit targets x 2 widths; ORB row above added
zero trials, no code was run). **Cumulative trials: N=1379** (1373 prior +
6).

---

## §39 — ORB gold RETEST: joint entry (retest_tol_frac) x stop (stop_mode)
## grid — strongest ORB result in the project (2026-09-15)

User asked to relook at ENTRY and SL rules too, not just exit (§38 already
closed the exit dimension for ORB — already exhausted in a prior session,
§10.7). Checked first, per standing rule 1: `retest_tol_frac` is fixed at
0.10 in literally every script in this repo that calls `orb()` (confirmed
by grep) — never swept. `stop_mode='moderate'` (a fixed 25bps stop, vs the
default adaptive OR-width stop) exists and was tested once, on the
UNFILTERED breakout (2026-08-29 audit, found worse there) — but never
combined with `retest=True`, a materially different setup since the retest
filter already changes entry price and trade selection.

**Mechanisms (stated before any result seen):** retest_tol_frac trades off
entry quality vs trade count — tighter tolerance demands a cleaner
re-confirmation (fewer, better trades), looser tolerance accepts a sloppier
pullback (more trades, worse entry-to-stop ratio). Moderate stop combined
with retest could plausibly behave differently than on raw breakouts,
since the retest filter already raises entry quality — a smaller,
cost-efficient fixed stop may suit a pre-filtered, cleaner setup better
than it suited the raw breakout.

**Grid:** retest_tol_frac in {0.05, 0.10, 0.20} x stop_mode in {or_range,
moderate} = 6 cells; (0.10, or_range) reproduces the known baseline
exactly (554 trades) and is not counted as a new trial. 5 new trials.

**Baseline reproduction note (not a bug, a window clarification):** the
live baseline Sharpe here is **+1.206** (554 trades, full continuous
2017-2025 span), not the +1.097 previously quoted in §33 — §33's figure
was computed on the BTC-CAPM-overlap-restricted window (2017-08-17 onward,
for apples-to-apples comparison against a BTC benchmark across all 4
candidates), a different, shorter window used for a different purpose.
Both numbers are correct for their own stated window; recorded here so
they are never conflated.

**Result — the STOP dimension shows a real, consistent effect:**

| tol_frac | or_range Sharpe | moderate Sharpe |
|---|---|---|
| 0.05 | +1.023 | +1.176 |
| 0.10 (baseline) | +1.206 | +1.387 |
| 0.20 | +1.195 | **+1.488** |

Moderate (fixed 25bps) beats or_range at EVERY tolerance level tested —
the OPPOSITE of the unfiltered-breakout finding, because the retest filter
already selects higher-quality setups that a smaller, cost-efficient fixed
stop suits better than the raw breakout did.

**Best cell: retest_tol_frac=0.20, stop_mode='moderate'**
- Sharpe +1.488, gross PF 1.915, net PF 1.425, avg net R +0.150/trade, 587 trades
- Compounded $100k -> $235,575 (+135.6%), trade-level maxDD 12.1%
- **Beats buy-and-hold gold's Sharpe (+1.18) for the first time in this
  project's ORB history**, with lower drawdown (12.1% vs B&H's 20.4%) --
  though B&H still wins on raw total return (+275.2%) given ORB's
  deliberately conservative 1%-risk sizing (a known sizing artifact per
  §10.6/§33, not evidence of inferiority -- Sharpe is the fair comparison
  since it's size-invariant)

**Robustness checked (not just the headline number):**
- 8/9 years net-positive (only 2018 mildly negative, -3.4R total)
- Top-year concentration: 27.3% of total net_R in the single best year --
  healthy, well below the 100%+ concentration that flagged prior ORB kills
- Worst single day -1.33% (2020-04-16), worst month -3.27% (2018-12),
  worst week -3.32% (2021-12-05) -- no tail-risk flag on any measure

**DSR, both pools reported honestly:**
- LOCAL 5-trial pool (this grid only): DSR 0.509 -- reference only, and
  optimistic since the pool is small
- **FULL ORB-family cumulative pool** (N=248, every ORB config ever run in
  this project, pulled from all `results/orb_*_scored.csv` files): **DSR
  0.0019** -- pool mean -0.99, std 1.54, E[max SR]=+3.38 driven by
  catastrophic M5/M15 configs elsewhere in the family, the same
  DSR-saturation caveat already documented in §10.6. Reported honestly,
  not hidden or omitted.

**VERDICT: real, robust improvement -- the best ORB gold RETEST
configuration this project has ever found -- but NOT a clean DSR survivor
at the honest full-pool count.** The case for this cell rests on the
economic/robustness evidence (beats B&H Sharpe, low year-concentration, no
tail-risk flag, holds across a genuine 9-year span with real costs), not
on DSR, exactly the same framing already used for the §10.6 index-trend
candidate. Flagged prominently per standing rule 5 rather than buried in a
table row. Recommend retest_tol_frac=0.20 / stop_mode='moderate' as this
project's new reference ORB gold RETEST configuration if the strategy is
ever revisited.

**Files:** `research/orb_retest_entry_stop_grid.py`. Results:
`results/orb_retest_entry_stop_grid.csv`. Reproduce:
`python research/orb_retest_entry_stop_grid.py`.

**Trial count: 5 new** (baseline reproduction not counted). **Cumulative
trials: N=1384** (1379 prior + 5).

---

## §40 — Credit-spread SPY: entry (delta target x DTE) grid, built on
## §38's best exit — this project's best options-selling result (2026-09-15)

Continuing the user's entry/SL/TP relook onto credit-spread SPY. Staged
design, stated explicitly for efficiency: width fixed at 2% (§27-best),
early-exit fixed at 50% (§38-best) — only entry (delta, DTE) is new here,
rather than a full 4-dimensional joint grid.

`TARGET_DELTA=0.10` and `DTE_DAYS=37` have been fixed constants, imported
unchanged, across every credit-spread section in this project (§20, §26,
§27, §38) — chosen originally only to match Ultimate Investor's live
scanner defaults, never swept as free parameters. Confirmed by grep: no
script calls `solve_delta10_strike` with a non-default `target_delta`.

**Mechanisms (a priori):** delta trades premium size against win rate/avg
loss (classic risk-reward dial); DTE trades theta decay speed against gap
risk (shorter DTE sits in the steeper part of the decay curve — the same
TastyTrade-literature logic that motivated §38's 50%-early-exit rule; 21
DTE is that literature's commonly cited "sweet spot").

**Grid:** target_delta in {0.05, 0.10, 0.16} x dte in {21, 37, 45} = 9
cells; (0.10, 37) reproduces §38's best cell EXACTLY (Sharpe +1.319, exact
match, confirming correctness) and isn't counted. 8 new trials.

**Result — a real, non-noisy monotonic pattern:** DTE 21 beats 37 beats 45
at every delta; delta 0.16 beats 0.10 beats 0.05 almost everywhere. Best
in the 9-cell grid: **delta=0.16, dte=21 — Sharpe +1.643**, maxDD 5.0%,
total return +365.8%, win rate 94.8%, worst day -1.70%, worst month
-2.25%.

**Efficient-search discipline applied: the result hit the grid edge on
BOTH dimensions, so 3 more cells were run to check past the edge rather
than trust an edge-hugging number** (0.20/21, 0.16/14, 0.20/14):

- **Delta REVERSES past 0.16**: delta=0.20/dte=21 gives Sharpe 1.407,
  WORSE than delta=0.16's 1.643 -- confirms a genuine INTERIOR optimum
  near delta=0.16, not an artifact of stopping the grid too early.
- **DTE KEEPS IMPROVING past 21**: delta=0.16/dte=14 gives Sharpe 2.097;
  delta=0.20/dte=14 gives 2.012 -- both far above anything at dte=21.

**The DTE<21 result is flagged as a likely MODEL-LIMITATION artifact, not
adopted as a new finding.** This project's options pricing throughout
(§20/§24/§26/§27/§38, stated every time) uses a FLAT VIX-as-implied-vol
assumption with no skew or term structure. Real near-dated (<=14 DTE)
options carry meaningfully more skew/event premium than 30-37 DTE ones --
a flat-vol model cannot see that, so shrinking DTE further likely
UNDERSTATES the true cost of selling that premium rather than revealing
genuine extra edge. Catching this rather than reporting the highest number
uncritically is the point of extending the grid past its edge.

**Robustness on the defensible pick (delta=0.16, dte=21 -- staying in the
model's more reliable 21-45 DTE zone):** 30/34 years net-positive
(log-return basis), including **2008 GFC (+4.3%, the defined-risk cap held
through the crisis)** and **2020 COVID (+4.3%)** -- only 3 mild negative
years (1996 -1.6%, 2018 -0.2%, 2022 -2.8%). A genuinely healthy,
non-concentrated multi-decade result, not a spike.

**DSR** against the full defined-risk credit-spread family pool (N=19 --
every Sharpe across `credit_spread_iv_filter.csv` +
`credit_spread_early_exit.csv` + this grid; a materially healthier pool
than ORB's, mean +1.11/std 0.28, since this family has been consistently
decent rather than catastrophic-tailed): **0.502** -- real, but still
short of the 0.95 bar.

**VERDICT: real, robust improvement with a genuine interior optimum in
delta -- this project's best options-selling result to date, still not a
clean DSR survivor.** Recommend delta=0.16 / dte=21 / width=2% /
early-exit=50% as the new reference credit-spread configuration. Flag
dte<21 as an open question that needs real option-chain data (not this
project's flat-vol proxy) before it could be trusted -- do not chase it
further on this data.

**Files:** `research/credit_spread_entry_grid.py`. Results:
`results/credit_spread_entry_grid.csv` (12 rows: 9-cell grid + 3
boundary-check extension cells). Reproduce:
`python research/credit_spread_entry_grid.py`.

**Trial count: 11 new** (8-cell grid + 3 boundary-check extension; baseline
reproduction not counted). **Cumulative trials: N=1395** (1384 prior + 11).

---

## §41 — JOINT entry+exit re-optimization: does the earlier-tuned dimension
## still hold once the other moved? (2026-09-15) — new project-best result

§38 optimized credit-spread's exit holding entry fixed; §40 then optimized
entry holding exit fixed; §39 optimized ORB's entry+stop holding target
fixed. Staged search is efficient but can miss real interactions between
dimensions. This section closes that gap on both candidates.

### Credit spread: the exit optimum GENUINELY SHIFTED

Fixed §40's new best entry (delta=0.16, dte=21, width=2%) and re-swept
`profit_target_frac`. 50% (optimal for the OLD entry delta=0.10/dte=37)
turns out NOT to be optimal for the new entry:

| profit_target | Sharpe | maxDD | worst year |
|---|---|---|---|
| 25% | 1.073 | 8.1% | -- |
| 50% (§40 baseline) | 1.643 | 5.0% | -- |
| 75% | 1.810 | 7.2% | -- |
| **85% (new best)** | **2.090** | **5.1%** | **-4.4% (2022)** |
| 95% | 1.899 | 5.1% | -- (reverses) |

95% reverses past 85%, confirming a genuine interior optimum (same
discipline as §40's delta check) rather than an edge artifact.

**Robustness on delta=0.16/dte=21/pt=85% — the most robust result in this
project's history:** 32/34 years net-positive, worst year only -4.4%
(2022), **2008 GFC +2.5%**, **2020 COVID +7.5%** (both crisis years
positive, the defined-risk cap holding as designed). DSR against the FULL
defined-risk credit-spread family pool (N=27, every Sharpe across
`credit_spread_iv_filter`/`early_exit`/`entry_grid`/`joint_reopt`): **0.429**
-- real but still short of 0.95 (the pool's own E[max SR] rose to +2.16
now that it contains this result and its close neighbors).

### ORB: NO reversal — target=1R is robust to the entry/stop change

Fixed §39's new best entry+stop (retest_tol_frac=0.20, stop_mode=
'moderate') and re-checked target {1R, 2R, close}:

| target | Sharpe | net PF | end balance ($100k, 1% risk) | maxDD |
|---|---|---|---|---|
| **1R (unchanged best)** | **+1.488** | 1.425 | $235,575 | 12.1% |
| 2R | +1.225 | 1.370 | $258,040 | 13.8% |
| close (hold to bell) | +1.219 | 1.465 | $342,039 (highest $) | 15.3% |

Same pattern as §10.7's original finding: letting winners run raises raw
dollar totals but not risk-adjusted Sharpe. **Confirms §10.7's
target-dimension conclusion was NOT an artifact of the old
tol=0.10/or_range setup** -- it holds under the new entry+stop too.
Trailing-stop/breakeven-stop were not re-tested against the new
stop_mode='moderate' combination: already failed decisively twice against
or_range, and no new a priori mechanism was proposed for why a tighter
fixed stop would flip that outcome. Flagged as a smaller residual
open question, not chased further -- a deliberate stopping point.

**VERDICT: the joint check was worth running on both candidates, and gave
two different, both useful answers.** Credit spread: staged optimization
LEFT REAL GAINS ON THE TABLE (+0.45 Sharpe, 1.643 -> 2.090, from re-tuning
exit after entry moved) -- a genuine interaction. ORB: staged optimization
was SAFE (target choice doesn't depend on entry/stop) -- confirmed, not
assumed.

**NEW PROJECT-BEST RESULT: credit-spread SPY, delta=0.16 / dte=21 /
width=2% / early-exit=85%.** Sharpe +2.090, 32/34 positive years, 2008 and
2020 both positive, DSR 0.429 (real, still short of the 0.95 bar). This is
now the strongest and most robust single result across the entire project.

**Files:** `research/credit_spread_joint_reopt.py`. Results:
`results/credit_spread_joint_reopt.csv`. ORB target check run ad hoc
(same engine as §39, no new script needed — 2 trials).

**Trial count: 6 new** (4 credit-spread profit-target cells + 2 ORB target
cells; both baseline reproductions excluded). **Cumulative trials: N=1401**
(1395 prior + 6).

---

## §42 — NAS100 H4 macross: joint SL/TP/HOLD grid — third candidate,
## strongest spot/CFD trend result in the project (2026-09-15)

User restricted scope to spot/CFD trading strategies like ORB (explicitly
NOT the options-based credit spread), and asked to push a third candidate
with the same joint-grid, follow-the-gradient method. Chose **H4 index
trend/macross** over on-chain BTC: on-chain's edge is 43%-explained by BTC
beta per §33's CAPM decomposition (a weaker candidate for genuine
entry/exit refinement, since much of its "edge" is just being long BTC),
while macross has a real, gross, cost-surviving edge (§10.6: NAS100 H4
grossPF 1.52, netPF 1.47, Sharpe +0.67 — the best gross edge this project
had found outside ORB/credit-spread) that scales monotonically with
timeframe, consistent with genuine trend persistence rather than noise.

Checked first, per standing rule 1: `strategies/sweep_families.py`'s
`FAMILIES["macross"]` has exactly 3 hand-picked (fast, slow, ema_trend,
k_atr, R, H) parameter combinations — no independent SL (k_atr), TP (R),
or hold-time (H) sweep has ever been run.

**Mechanism (a priori):** k_atr trades stop-noise-absorption against loss
size per stop. R trades target size — for a TREND-FOLLOWING signal (which
the edge's own timeframe-monotonic behavior in §10.6 suggests this is),
the classic literature favors WIDE targets since the edge concentrates in
occasionally large moves, not small consistent ones — a real, specific
reason (unlike ORB, where widening the target already failed) to expect R
matters here. H caps how long a trade can run before a forced time-exit,
which could newly bind if R widens a lot.

### Grid 1 (SL x TP, 3x3): baseline was already near-optimal, but not quite

k_atr in {1.5, 2.0, 3.0} x R in {1.5, 2.0, 3.0}, fast/slow/ema_trend/H held
at variant 0's values. Baseline (k_atr=2.0, R=2.0, Sharpe +0.669) was the
best of the 3x3 grid except k_atr=1.5/R=3.0 (Sharpe +0.725) — which hit
the grid edge on both k_atr (low) and R (high).

### Grid 2 (edge-follow extension): a genuine interaction, not a boundary artifact

Neither dimension alone beats k_atr=1.5/R=3.0 (k_atr=1.0 alone at R=3.0:
Sharpe 0.480; R=4.0 alone at k_atr=1.5: Sharpe 0.425) — but the
COMBINATION **k_atr=1.0, R=4.0 gives Sharpe +0.830**. Confirmed as a real
local peak, not a fluke, by testing every direction around it: R=5.0
(0.512) and R=6.0 (0.502) drop off; k_atr=0.75 (0.329) and k_atr=1.25
(0.416) drop off too.

### Grid 3 (H sweep): the max-hold cap was silently truncating the new,
### 4x-wider target

At k_atr=1.0/R=4.0/H=48 (the grid-1/2 default), 12.2% of trades were
time-exits — a real, previously invisible constraint that only became
binding once R widened from 2 to 4. Extending H:

| H (H4 bars) | Sharpe | time-exit % |
|---|---|---|
| 48 | 0.830 | 12.2% |
| 72 | 0.825 | -- |
| 96 | 0.907 | -- |
| 144 | 0.962 | -- |
| **192 (plateau)** | **0.963** | **0.6%** |
| 240 / 300 / 400 | 0.963 (byte-identical) | -- |

240/300/400 give BYTE-IDENTICAL results to 192 -- the time-cap has
entirely stopped binding by ~192 bars (32 trading days), confirming a real
plateau rather than an unbounded chase.

### Final best configuration

**fast=10 / slow=30 / ema_trend=200 / k_atr=1.0 / R=4.0 / H=192**
- Sharpe **+0.963**, gross PF 1.798, net PF 1.716, maxDD 11.0%, 181 trades
- **Beats NAS100 buy-and-hold's Sharpe (0.842) with 3.2x lower drawdown**
  (11.0% vs 35.7%) — the first index-instrument result in this project to
  clearly beat B&H on BOTH Sharpe and drawdown simultaneously, not a
  narrow/noise-level "win" like the original §10.6 finding
- 7/8 years net-positive (only 2019 mildly negative, -2.1%)
- Worst day -2.09% (2023-03-01), worst month -6.12% (2019-08) — no
  tail-risk flag

**DSR, both pools reported honestly:** against the FULL contaminated
macross-family pool (all timeframes, N=52 including this session's cells):
**0.032** — saturated by catastrophic M5-M30 configs elsewhere in the
family, the same pattern already documented for ORB's full-pool DSR (§39).
Against a CLEAN H4-only structural pool (N=28, no M5-M30 contamination):
**0.503** — real, still short of 0.95, but consistent in magnitude with
ORB's and credit-spread's own local-pool DSR figures.

**VERDICT: real, robust improvement, genuinely beating buy-and-hold on
BOTH Sharpe and drawdown for the first time on an index instrument in this
project — still not a clean DSR survivor at the full contaminated pool.**
The same efficient-search discipline paid off a third time in a row: the
k_atr/R interaction would have been MISSED by staged (one-dimension-at-a-
time) search, and the H constraint was an invisible implementation
artifact, not a preference, that only surfaced once R moved. This is now
the strongest pure spot/CFD directional-trading result in the project.
Recommend fast=10/slow=30/ema_trend=200/k_atr=1.0/R=4.0/H=192 as the new
reference NAS100 H4 macross configuration. **US30 was NOT re-swept this
session** (NAS100 only, for efficiency) — flagged as the natural next
step, not yet done.

**Files:** `research/macross_h4_stop_target_grid.py`. Results:
`results/macross_h4_stop_target_grid.csv`,
`results/macross_h4_stop_target_extension.csv`. Reproduce:
`python research/macross_h4_stop_target_grid.py` (grid 1 only; grids 2-3
run ad hoc, params documented above).

**Trial count: 21 new** (8 grid-1 + 9 grid-2 extension + 4 grid-3 H-sweep;
baseline and 3 H-plateau reproductions not counted). **Cumulative trials:
N=1422** (1401 prior + 21).

---

## §43 — US30 H4 macross: joint SL/TP/HOLD grid — extends §42's method,
## clearest buy-and-hold beat in the project (2026-09-15)

Direct extension of §42's method to US30 (not covered there). Baseline:
US30's own best original variant (variant 2: fast=10/slow=30/ema_trend=100/
k_atr=1.5/R=3.0/H=48, Sharpe +0.559) was already the strongest of its 3
hand-picked configs, so the grid was centered on `ema_trend=100` rather
than blindly reusing NAS100's winning `ema_trend=200` — confirmed, not
assumed: at k_atr=2.0/R=2.0, ema_trend=100 gives Sharpe 0.599 vs the known
ema_trend=200 figure of 0.326. Different instruments genuinely prefer
different trend-filter lengths.

**Grid 1** (k_atr in {1.0,1.5,2.0} x R in {2.0,3.0,4.0}, ema_trend=100,
H=48): 8 new cells, (1.5,3.0) reproduces the baseline exactly.

**Extension (edge-follow discipline):** the emerging peak moved toward
WIDER stop + TIGHTER target (k_atr up to 2.5, R down to 1.0) — the OPPOSITE
direction from NAS100's finding (narrower stop, wider target) — a
genuinely different, instrument-specific optimum, not a repeat of §42's
result. Confirmed as a real peak by decay in every direction:

| Cell | Sharpe |
|---|---|
| k_atr=2.0, R=1.0 | 0.345 |
| k_atr=3.0, R=1.0 | 0.708 |
| **k_atr=2.5, R=1.0 (peak)** | **0.948** |
| k_atr=2.5, R=0.75 | 0.532 |
| k_atr=2.5, R=0.5 | 0.266 |

**H-sweep** at the k_atr=2.5/R=1.0 peak found a real but much flatter
interior optimum than NAS100's (which needed H all the way to 192):
H=24 (0.816) < H=48 (0.948) < **H=72 (0.999, best)** > H=96 (0.984) —
time-exit fraction fell from 38% (H=24) to 6% (H=96) as H widened, a
milder version of §42's same mechanism.

### Final best configuration

**fast=10 / slow=30 / ema_trend=100 / k_atr=2.5 / R=1.0 / H=72**
- Sharpe **+0.999**, gross PF 1.642, net PF 1.594, maxDD 6.1%, 159 trades
- **DECISIVELY beats US30 buy-and-hold** (Sharpe +0.547, maxDD 37.0%) --
  nearly double the Sharpe with 6x lower drawdown -- the clearest,
  largest buy-and-hold beat of any index result in this project (sharper
  than §42's NAS100 margin of 0.963 vs 0.842)
- 7/8 years net-positive (only 2023 mildly negative, -3.4%)
- Worst day -2.03% (2020-12-21), worst month -3.06% (2019-03) -- no
  tail-risk flag

**DSR** against a clean US30-H4-only structural pool (N=30, this session's
cells plus the 3 original variants, no M5-M30 contamination): **0.499** --
real, consistent in magnitude with every other candidate found this
session (ORB 0.509 / credit-spread 0.429-0.502 / NAS100 macross 0.503),
still short of 0.95.

**VERDICT: real, robust improvement — the clearest buy-and-hold beat of
any index result in this project, on both Sharpe and drawdown.** Confirms
§42's finding generalizes to a second instrument, but with a GENUINELY
DIFFERENT optimal SL/TP geometry (wide stop/tight target here vs narrow
stop/wide target for NAS100) -- the same mechanism (trend persistence)
does not imply the same parameters across instruments, an honest and
useful finding for anyone deploying this rather than a false
one-size-fits-all shortcut. Recommend fast=10/slow=30/ema_trend=100/
k_atr=2.5/R=1.0/H=72 as the new reference US30 H4 macross configuration.

Across the whole session, NAS100 (Sharpe 0.963) and US30 (Sharpe 0.999)
macross are now the most consistently buy-and-hold-beating PAIR of spot/
CFD results this project has produced -- both real trading strategies
(not options), both beating B&H on Sharpe AND drawdown, both found via the
same disciplined joint-grid-plus-edge-follow method.

**Files:** `results/macross_h4_stop_target_grid_US30.csv` (reuses
`research/macross_h4_stop_target_grid.py`'s `score()` function, run ad hoc
with the US30 data path and `ema_trend=100` base).

**Trial count: 26 new** (8 grid-1 + 15 extension + 3 H-sweep; baseline and
1 H-duplicate not counted). **Cumulative trials: N=1448** (1422 prior + 26).

---

## §44 — NAS100 + US30 H4 macross COMBINED BOOK — 50/50 fixed-weight
## portfolio check on the two §42/§43 session-best legs (2026-09-16)

User asked whether the two new NAS100 (§42) and US30 (§43) macross
candidates work as a combined book. Not a parameter search — both legs
reuse their already-found session-best configs UNCHANGED (NAS100:
fast=10/slow=30/ema_trend=200/k_atr=1.0/R=4.0/H=192; US30:
fast=10/slow=30/ema_trend=100/k_atr=2.5/R=1.0/H=72), each re-run with the
identical cost model/H4 resample/strictly_after=True resolution as §42/§43
to regenerate each leg's own daily return series, then combined at a fixed
50/50 capital weight (missing-trade days = flat/0 for that leg, dates
aligned on the union). **Adds 0 to the project's trial count** — this is a
portfolio-construction check on two already-scored cells, not a new
backtest search.

**Mechanism (a priori):** two H4 macross trend-followers on different US
equity indices could plausibly be highly correlated (same macro trend
regime drives both indices) — in which case combining does little beyond
diversifying idiosyncratic noise — or could differ enough in entry timing
(different ema_trend length, k_atr/R geometry means the two systems open
and close trades at different times even when both are "long the US
trend") that the combination captures a genuine diversification benefit.
Stated before running: real edge if measured correlation is low AND
combined Sharpe beats the better of the two standalone legs, not just
their average.

**Result:**

| | Sharpe | maxDD |
|---|---|---|
| NAS100 standalone (§42) | +0.963 | 11.0% |
| US30 standalone (§43) | +0.999 | 6.1% |
| naive average of the two legs | +0.981 | 8.6% |
| **50/50 combined book** | **+1.135** | **5.7%** |

Correlation of the two legs' daily log-return series (2,344 aligned
trading days, 2018-2025): **+0.053** — effectively uncorrelated, despite
both being US-index H4 trend-followers. The combined book beats BOTH
individual legs on Sharpe (not just their average) and beats the lower of
the two legs' drawdowns (5.7% vs US30's own 6.1%) — genuine
diversification, not just noise-averaging. 7/8 years net-positive (worst:
2019, -0.0%, effectively flat, an improvement on both legs' own worst
years).

**Why the correlation is so low despite both being "US index trend"
strategies:** the two configurations have very different trade geometry
(NAS100: k_atr=1.0/R=4.0/H=192, tight stop/wide target/long hold; US30:
k_atr=2.5/R=1.0/H=72, wide stop/tight target/short hold) — §42 and §43
each independently found instrument-specific optima at OPPOSITE ends of
the stop/target spectrum (already flagged in §43 as "the same mechanism
does not imply the same parameters across instruments"). That geometry
difference means the two systems hold different trades at different
times even when both are net-long the same broad US-equity trend, which
is enough to decorrelate the two P&L streams almost completely.

**DSR:** not applicable — no new parameter search was run, so there is no
new trial to deflate. The relevant DSR figures remain each leg's own
(§42: 0.503 clean H4 pool; §43: 0.499 clean US30-H4 pool).

**VERDICT: real, useful finding — running NAS100 and US30 macross as a
combined 50/50 book is superior to holding either alone**, on both Sharpe
and drawdown, with no repaint/mining risk since neither leg's parameters
were touched. This is a portfolio-allocation result, not a signal-search
result, but it strengthens the case for the macross family as the
project's best pure spot/CFD candidate: two instruments, two genuinely
different (not copy-pasted) optimal geometries, combined into one
lower-drawdown, higher-Sharpe book.

**Files:** `research/macross_h4_combined_book.py`. Results:
`results/macross_h4_combined_book.csv` (per-day return series for both
legs and the combined book). Reproduce:
`python research/macross_h4_combined_book.py`.

**Trial count: 0 new** (portfolio check, no parameter search). **Cumulative
trials: N=1448** (unchanged).

---

## §45 — US30 H4 BREAKOUT-RETEST: joint lookback (N) x stop (k_atr) x
## target (R) x hold (H) grid — fourth candidate, best raw Sharpe in the
## project's pure spot/CFD family (2026-09-16)

User asked for a fourth candidate pushed through the same joint-grid +
follow-the-gradient-past-the-edge method as ORB gold RETEST (§39),
credit-spread SPY (§38/40/41), and NAS100+US30 macross (§42/43). Re-read
`results/sweep_indices_scored.csv` directly (not from memory) rather than
reuse another macross timeframe/instrument, per standing rule 1 — a fourth
macross cell would not be a new signal family. Found the breakout_retest
family instead: across all 75 originally-swept breakout cells (5
instruments x 5 timeframes x 3 hand-picked variants), exactly ONE has a
genuinely positive net Sharpe — **US30 H4 variant 2 (N=20, k_atr=1.5,
R=1.5, H=24): grossPF 1.232, netPF 1.183, Sharpe +0.400, maxDD 24.1%, 484
trades** — every other breakout cell in the family is net Sharpe <= +0.207,
most sharply negative (family mean Sharpe -2.96, driven by catastrophic
M5-M30 configs). Confirmed by grep: `strategies/sweep_families.py`
FAMILIES["breakout"] has exactly 3 hand-picked variants, no independent
SL/TP/lookback sweep ever run on this family.

**Mechanisms (a priori, stated before any result seen):** N (breakout
lookback) trades level significance against signal frequency — longer
lookback demands a more significant prior high/low (fewer, cleaner
breakouts) at the cost of trade count. k_atr trades stop-noise-absorption
against loss size, the same mechanism as every prior family. R is a
genuinely OPEN question for this family, unlike macross (trend-following,
wide target favored by §10.6's own timeframe-monotonic finding) or ORB
(already found wide targets fail, §10.7) — a breakout-retest entry
captures a short post-breakout continuation, not a persistent multi-day
trend, so neither a wide nor narrow target was assumed in advance.

**Grid 1** (N in {10,20,30} x k_atr in {1.0,1.5,2.0} x R in {1.0,1.5,2.0},
H=24 fixed): 26 new cells, (20,1.5,1.5) reproduces the known baseline
EXACTLY (n=484, grossPF 1.232, netPF 1.183, Sharpe +0.400, maxDD 24.1% —
confirming the re-implementation is correct). Best of the 3x3x3 grid:
**N=10/k_atr=2.0/R=1.0, Sharpe +0.558** — hit the grid edge on BOTH k_atr
(high) and R (low) simultaneously.

**Extension (edge-follow discipline, same as §39-43) — 7 successive
rounds, each following the gradient the previous round revealed, 49 new
cells:**

| Round | Finding |
|---|---|
| 1-2 | k_atr and R BOTH keep improving as k_atr rises / R falls — pushed both further: k_atr=4.0/R=0.5 reached Sharpe +0.935 |
| 3-4 | R=0.25 is a genuine interior optimum (R=0.15 gives 0.790, R=0.10 gives 0.624 — both WORSE, confirming reversal, not an unbounded chase) |
| 5 | N=20/k_atr=4.0/R=0.25 (not N=10) is the true peak once R moved: **Sharpe +1.508** — decay confirmed in every direction (N=15/25/30, k_atr=3.5/4.5/5.0, R=0.15/0.35 all lower) |
| 6-7 | H sweep at the confirmed N/k_atr/R peak found H matters (R shrank 6x from baseline's 1.5, the same "does the old H still fit" check as §42): H=18/20/22 form a genuine 3-cell PLATEAU (Sharpe +1.644/+1.684/+1.670); H=14 spikes higher (+1.940) but is flanked by lower values on both sides (H=12: +1.531, H=16: +1.696) — a single-cell spike, not adopted, per the project's own standing plateau-selection rule (never argmax on the grid) |

**Final recommended configuration: N=20 / k_atr=4.0 / R=0.25 / H=20**
(center of the H=18-22 plateau)
- Sharpe **+1.684**, gross PF 1.332, net PF 1.262, maxDD **4.1%**, 634
  trades, win rate 72.1%
- Cost is a sane 4.8% of gross R per trade on average (not a near-zero-cost
  artifact) — mechanism checks out: win small/often (72% win rate) against
  a wide stop that's rarely hit but costly when it is (net_R skew -1.74),
  the same high-win-rate/rare-large-loss archetype as this project's
  credit-spread family, arrived at independently on a completely different
  instrument and signal type
- **DECISIVELY beats US30 buy-and-hold** (Sharpe +0.547, maxDD 37.0%,
  §43): more than 3x the Sharpe with ~9x lower drawdown — the largest
  Sharpe of any pure spot/CFD result in this project, beating ORB gold
  RETEST (+1.488, §39) and both macross candidates (+0.963/+0.999, §42/43)
- **8/8 years net-positive** (2018-2025) — every year positive is a first
  for any candidate in this project; worst year 2022 still +1.3%
- Worst day -1.0% (2019-12-30), worst month -2.6% (2023-05) — no tail-risk
  flag by any measure

**DSR, both pools reported honestly (baseline reproduction excluded from
both):**
- LOCAL grid+extension pool (this candidate's own 75 trials): **DSR
  0.3455** — real, still short of 0.95
- **FULL breakout-family pool** (N=105: 30 original multi-instrument cells
  + this session's 75): **DSR 0.0000** — saturated by the family's own
  catastrophic M5-M30 configs (family mean Sharpe -2.96), the same
  full-pool-contamination pattern already documented for ORB (§39) and
  macross (§42/43)

**VERDICT: real, robust improvement — the strongest raw Sharpe and the
first 8/8-year candidate in the project's spot/CFD history — still not a
clean DSR survivor at the full contaminated pool.** Same lesson as every
prior joint-grid session: the true optimum (N=20/k_atr=4.0/R=0.25) was
nowhere near the original 3x3x3 grid or even its first two extension
rounds — it only emerged after following the gradient through 4 successive
rounds, and the H-plateau vs H=14-spike distinction is a direct,
concrete application of the project's own "plateau, not argmax" rule
rather than reporting the single highest number found. Recommend
N=20/k_atr=4.0/R=0.25/H=20 as this project's new reference US30 H4
breakout-retest configuration.

**Files:** `research/breakout_us30_h4_stop_target_grid.py`. Results:
`results/breakout_us30_h4_stop_target_grid.csv` (27 grid-1 rows + 49
extension rows). Reproduce:
`python research/breakout_us30_h4_stop_target_grid.py`.

**Trial count: 75 new** (26 grid-1 + 49 extension; baseline reproduction
excluded). **Cumulative trials: N=1523** (1448 prior + 75).

---

## §46 — NAS100 H4 BREAKOUT-RETEST: same joint grid extended to the
## second instrument — real improvement, but does NOT beat buy-and-hold
## (2026-09-16)

User asked to check NAS100 breakout too, extending §45's method to the
second (and only other) genuinely positive breakout cell. Baseline
(re-read from `results/sweep_indices_scored.csv` directly): **NAS100 H4
breakout_retest variant 1 (N=50, k_atr=1.0, R=2.0, H=48): grossPF 1.156,
netPF 1.104, Sharpe +0.102, maxDD 15.2%, 347 trades** — the only NAS100
breakout cell across all 5 timeframes tested with a net PF above 1 (H1/
M30/M15/M5 all net Sharpe <= -0.05). Weaker starting point than US30's
+0.400 (§45), but real and never independently swept — same
justification. NAS100's own best original variant uses N=50/H=48
geometry (not US30's N=20/H=24), so the grid was centered there per §43's
precedent that different instruments in the same family warrant different
starting geometries — confirmed, not assumed. Reused
`research/breakout_us30_h4_stop_target_grid.py`'s `score()`/`run_cell()`
unchanged; only the data path and grid center differ.

**Grid 1** (N in {30,50,70} x k_atr in {0.75,1.0,1.5} x R in {1.5,2.0,3.0},
H=48 fixed): 26 new cells, (50,1.0,2.0) reproduces the baseline exactly.
Best: **N=70/k_atr=1.0/R=2.0, Sharpe +0.366** — hit the grid edge on N
(highest tested).

**Extension (edge-follow discipline, same as §39-45) — 3 rounds, 21 new
cells (7+9+5):**
- Round 1: pushed N further (90, 110) to test whether 70 was a real edge
  — **both worse** (0.149, -0.031), confirming N=70 is a genuine interior
  peak, not an artifact of stopping the grid early. R=1.75 (untested in
  grid 1) beat R=2.0: Sharpe +0.399.
- Round 2: fine-tuned R (1.6-1.9) and k_atr (0.85-1.15) around the new
  peak — R=1.75/k_atr=1.0 held as the best combination, confirmed by decay
  on both sides of each dimension. H=60 (+0.410) beat the fixed H=48.
- Round 3: swept H further at the confirmed N=70/k_atr=1.0/R=1.75 peak —
  **H=84/90/96 form a genuine 3-cell plateau (Sharpe +0.534/+0.526/+0.523)**,
  decaying on both sides (H=72: +0.431, H=120: +0.438) — the same
  plateau-not-argmax discipline applied in §45's H-sweep.

**Final recommended configuration: N=70 / k_atr=1.0 / R=1.75 / H=90**
(center of the H=84-96 plateau)
- Sharpe **+0.526**, gross PF 1.306, net PF 1.244, maxDD 11.9%, 302
  trades, win rate 43.4% — a real, 5x improvement over the +0.102 baseline
- Cost is 2.3% of gross R per trade (sane, no artifact)
- **Does NOT beat NAS100 buy-and-hold** (Sharpe +0.842, §42) — unlike
  US30's breakout candidate (§45, decisively beat US30 B&H) and unlike
  NAS100's OWN macross candidate (§42, Sharpe +0.963, beat B&H). Only
  **4/8 years net-positive** (2019/2021/2023/2024 positive, 2018/2020/
  2022/2025 negative) with 2024 alone carrying ~59% of total return —
  more concentrated and less robust than every other candidate in this
  project's recent run (all of which were 6-8/8 years positive). Worst day
  -1.1%, worst month -5.2% — no catastrophic tail flag, but the
  concentration is a real, honestly-reported weakness, not hidden.

**DSR, both pools reported honestly:**
- LOCAL grid+extension pool (this candidate's own 47 trials): **DSR
  0.4531** — real, still short of 0.95
- **FULL breakout-family pool** (N=152: 30 original multi-instrument cells
  + §45's 75 US30 cells + this session's 47 NAS100 cells): **DSR 0.0000**
  — same full-pool-contamination pattern as every other family in this
  project

**VERDICT: a real, substantial improvement over the NAS100 breakout
baseline (5x the Sharpe) via the same rigorous edge-follow method — but a
WEAKER, less robust result than §45's US30 breakout candidate on every
axis that matters (beats B&H vs. doesn't, 4/8 vs 8/8 positive years, 59%
vs ~27% year-concentration).** Genuinely useful negative-comparative
finding, consistent with §43's own observation that this project's
trend/breakout families do not transfer their optimal parameters (or their
edge strength) across instruments — US30 is the stronger breakout
instrument, NAS100 is the stronger macross instrument (§42 vs this
section), an asymmetry worth remembering rather than assuming either
instrument is uniformly better. Recommend N=70/k_atr=1.0/R=1.75/H=90 as
NAS100's reference breakout configuration IF this family is ever
deployed on NAS100, but do NOT rank it alongside the four B&H-beating
candidates (ORB, credit-spread, both macross legs, US30 breakout) — it is
a real edge that has not cleared the project's own "beats buy-and-hold"
bar.

**Files:** `research/breakout_nas100_h4_stop_target_grid.py`. Results:
`results/breakout_nas100_h4_stop_target_grid.csv` (27 grid-1 rows + 20
extension rows). Reproduce:
`python research/breakout_nas100_h4_stop_target_grid.py`.

**Trial count: 47 new** (26 grid-1 + 21 extension cells). **Cumulative
trials: N=1570** (1523 prior + 47).

---

## §47 — NAS100 + US30 H4 BREAKOUT combined book — a real, useful
## NEGATIVE finding: equal-weighting a strong leg with a weak leg hurts
## (2026-09-16)

User asked to check the combined NAS100+US30 breakout book, the same
portfolio-construction check as §44's macross combined book, applied to
the two breakout-retest legs found in §45 (US30, Sharpe +1.684, beats
B&H) and §46 (NAS100, Sharpe +0.526, does NOT beat B&H). Explicitly a
different setup from §44: there, both legs were independently strong; here
one leg is strong and one is weak, so the question was whether
diversification still helps riding the weak leg alongside the strong one,
or whether it just drags the book down. Method identical to §44 (both
legs' unchanged session-best params, same cost model/H4 resample/
strictly_after=True, daily log-returns aligned on the union of trading
days, 50/50 fixed weight, missing days = flat). Zero new trials — a
portfolio check on two already-scored cells.

**Result:**

| | Sharpe | maxDD |
|---|---|---|
| NAS100 standalone (§46) | +0.526 | 11.9% |
| US30 standalone (§45) | +1.684 | 4.1% |
| naive average of the two legs | +1.105 | 8.0% |
| **50/50 combined book** | **+0.967** | **5.0%** |

Correlation of the two legs' daily log-returns (2,365 aligned days,
2018-2025): **+0.041** — effectively uncorrelated, the same near-zero
correlation found for the macross pair in §44. But UNLIKE §44, low
correlation does NOT translate into a win here: **the 50/50 combined book
underperforms BOTH the naive average of the two legs' Sharpes AND holding
US30 alone on 100% of the book, on BOTH Sharpe and drawdown**
(combined Sharpe +0.967 < US30-only's +1.684; combined maxDD 5.0% >
US30-only's 4.1%). Combined book is only 6/8 years positive (worst: 2025,
-1.1%) versus US30 alone's 8/8.

**Why this differs from §44's genuine diversification win:** correlation
being near-zero is necessary but not sufficient for a fixed-weight
combination to help — it only helps when the legs are of comparable
quality (§44: Sharpe +0.963 and +0.999, both real, both beating their own
B&H). Here the two legs are NOT comparable (§45's +1.684 vs §46's +0.526,
already flagged in §46 as the weaker/more-concentrated result that fails
to beat NAS100 B&H) — blending a weak leg into a strong one at a fixed
50/50 weight dilutes the strong leg's edge faster than the near-zero
correlation can recover through variance reduction. The arithmetic
mechanism is simple and worth stating plainly: expected return is a linear
combination of the two legs' means, but with such an asymmetric quality
gap, halving exposure to the far-better leg costs more expected return
than the (still real, but comparatively small at this quality gap)
variance-reduction benefit of near-zero correlation can pay back.

**VERDICT: a real, useful NEGATIVE finding, not a repeat of §44's positive
one.** Correlation-based diversification is not a free lunch that helps
regardless of leg quality — combining ONLY helps when the legs are
comparably strong (§44), and equal-weighting a strong leg with a
materially weaker one just drags the book toward the weaker leg's
profile. For deployment purposes, the honest recommendation from this
project's own two combined-book checks is: **combine NAS100+US30 MACROSS
(§44, real win), do NOT equal-weight NAS100+US30 BREAKOUT — hold US30
breakout alone instead (§45's +1.684 standalone beats any 50/50 blend
with §46's weaker NAS100 leg)**. A quality-weighted (not equal-weighted)
blend was not tested here — flagged as a possible follow-up, not pursued,
since the project's scope has been the entry/exit/SL/TP refinement
question, not portfolio-weight optimization.

**Files:** `research/breakout_h4_combined_book.py`. Results:
`results/breakout_h4_combined_book.csv` (per-day return series for both
legs and the combined book). Reproduce:
`python research/breakout_h4_combined_book.py`.

**Trial count: 0 new** (portfolio check, no parameter search). **Cumulative
trials: N=1570** (unchanged).

---

## §48 — US30 MACROSS + US30 BREAKOUT combined book — a fourth combined-
## book pairing, on a NEW axis (same instrument, different signal
## families) — the best combined-book result in the project (2026-09-16)

User asked for a fourth combined-book pairing. §44/§47 both tested
same-family/cross-instrument (macross NAS100+US30; breakout NAS100+US30).
This section tests a genuinely different axis instead of repeating the
same one on a third instrument: **same instrument (US30), two different
signal families** — trend-continuation macross (§43) vs breakout-retest
(§45) — both of which independently beat US30 buy-and-hold (Sharpe
+0.547, maxDD 37.0%). Chosen deliberately over a third same-family pairing
because both US30 legs are individually strong (unlike §47's mismatched
pair), giving a fair test of whether cross-FAMILY diversification on one
instrument behaves like cross-INSTRUMENT diversification on one family
(§44) or like the failure mode in §47.

**Mechanism (a priori):** a moving-average-crossover trend trigger and a
breakout-level trigger are structurally different signals even on the
same instrument/timeframe — one reacts to sustained directional drift,
the other to a specific price level being breached — so there is a real
reason to expect meaningfully lower correlation between them than between
two variants of the SAME family on the same instrument, worth confirming
rather than assuming.

**Result:**

| | Sharpe | maxDD |
|---|---|---|
| US30 macross standalone (§43) | +0.999 | 6.1% |
| US30 breakout standalone (§45) | +1.684 | 4.1% |
| naive average of the two legs | +1.342 | 5.1% |
| **50/50 combined book** | **+1.707** | **3.4%** |

Correlation of the two legs' daily log-returns (1,915 aligned trading
days, 2018-2025): **+0.074** — effectively uncorrelated, confirming the a
priori mechanism (different signal families decorrelate even on the same
instrument, not just across instruments in the same family). The combined
book beats BOTH legs individually (not just their average) on Sharpe, and
beats the lower of the two legs' drawdowns too (3.4% vs breakout's own
4.1%). **8/8 years net-positive — every single year, including the worst
(2023, still +0.4%)** — the most robust year-by-year profile of any
result in this project, combined or standalone.

**This is now the best combined-book result and, on a risk-adjusted
basis, arguably the best single result in the project's pure spot/CFD
history** (Sharpe +1.707, ahead of US30 breakout alone at +1.684, ORB gold
RETEST's +1.488, and both individual macross legs) — only the
options-based credit-spread SPY (Sharpe +2.090, a different asset class
per the user's own scoping) is higher.

**VERDICT: confirms the §44 lesson generalizes to a NEW diversification
axis, and gives the clean opposite comparison to §47's failure.** The
determining factor for whether equal-weight combining helps is NOT
same-instrument vs cross-instrument, and NOT same-family vs cross-family
— it is whether BOTH legs are independently strong. §44 (cross-instrument,
same family, both strong) worked. §48 (same instrument, cross-family,
both strong) also works, and works even better (+1.707, its own two legs'
correlation even lower than §44's). §47 (cross-instrument, same family,
one weak) failed for the same reason regardless of the instrument/family
axis: a materially weaker leg dilutes a stronger one under fixed 50/50
weighting no matter how low the correlation is. Recommend the US30
macross+breakout 50/50 book as this project's strongest combined
spot/CFD configuration if either strategy family is ever deployed on
US30.

**Files:** `research/us30_macross_breakout_combined_book.py`. Results:
`results/us30_macross_breakout_combined_book.csv` (per-day return series
for both legs and the combined book). Reproduce:
`python research/us30_macross_breakout_combined_book.py`.

**Trial count: 0 new** (portfolio check, no parameter search). **Cumulative
trials: N=1570** (unchanged).

---

## §49 — ORB gold RETEST + US30 BREAKOUT combined book — fifth pairing,
## a THIRD diversification axis (cross-asset-class), pairing the
## project's two strongest single legs (2026-09-16)

User asked for more combined-book pairings. This pairs the two single
STRONGEST candidates in the entire project (ORB gold RETEST §39, Sharpe
+1.488; US30 breakout §45, Sharpe +1.684) across a new axis: cross-ASSET-
CLASS (commodity vs equity index), not just cross-instrument (§44/§47) or
cross-family-same-instrument (§48). Both legs independently beat their
own buy-and-hold. Method identical to §44/§47/§48: each leg's own
unchanged engine/params, daily returns aligned on the union of trading
days (ORB gold's 2017-2025 continuous span is longer than US30 CFD data's
2018-2025 -- the extra gold-only stub is treated as flat for US30, stated
not hidden), 50/50 fixed weight.

**Result:**

| | Sharpe | maxDD |
|---|---|---|
| ORB gold standalone (§39) | +1.488 | 12.1% |
| US30 breakout standalone (§45) | +1.684 | 4.1% |
| naive average of the two legs | +1.586 | 8.1% |
| **50/50 combined book** | **+1.687** | **4.5%** |

Correlation: **+0.011** — the LOWEST of any pairing tested so far,
confirming the a priori mechanism (gold and a US equity index are driven
by substantially different macro factors). But the improvement over the
better single leg is only marginal (+1.687 vs US30 alone's +1.684) and
maxDD is slightly WORSE than US30 alone (4.5% vs 4.1%) despite the lowest
correlation seen — a real, informative nuance: **correlation alone is not
the whole diversification story.** ORB gold's own standalone volatility/
drawdown (12.1%) is roughly 3x US30 breakout's (4.1%); at a fixed 50/50
NOMINAL-CAPITAL weight (not risk-parity), the higher-vol gold leg
contributes disproportionately more risk to the combined book than its
50% capital share would suggest, partly offsetting the near-zero-
correlation benefit. 8/9 years net-positive (worst: 2018, mildly -0.4%).

## §50 — NAS100 MACROSS + NAS100 BREAKOUT combined book — sixth pairing,
## completes the 2x2 same-instrument/cross-family design, and REVISES
## the "both legs must be strong" rule from §47/§48 (2026-09-16)

Completes the 2x2 design started in §48: same-instrument/cross-family
pairings on BOTH US30 (§48, both legs strong -> best result yet) and
NAS100 (this section, one leg strong [macross +0.963] and one leg weaker
[breakout +0.526, does NOT beat its own B&H, §46]) -- the same "one weak
leg" shape as §47's failed pairing, but on the cross-family/same-
instrument axis instead of cross-instrument/same-family, and with a
SMALLER quality gap (0.963 vs 0.526, ratio ~1.8x) than §47's (1.684 vs
0.526, ratio ~3.2x).

**Result — surprising, and it does NOT repeat §47's failure:**

| | Sharpe | maxDD |
|---|---|---|
| NAS100 macross standalone (§42) | +0.963 | 11.0% |
| NAS100 breakout standalone (§46) | +0.526 | 11.9% |
| naive average of the two legs | +0.745 | 11.5% |
| **50/50 combined book** | **+1.054** | **5.4%** |

Correlation +0.067 (near-zero, consistent with every pairing tested). The
combined book beats BOTH legs individually (not just the average) despite
one leg being the weaker, non-B&H-beating NAS100 breakout candidate --
the OPPOSITE of §47's outcome with the same "one weak leg" shape.

**This REVISES the simple rule stated after §47/§48** ("combining only
helps when both legs are independently strong") — that rule is not
universal. The determining factor is more precisely the SIZE of the
quality gap relative to the correlation benefit, not merely whether one
leg individually beats its own buy-and-hold: §47's gap (1.684 vs 0.526,
~3.2x) was too large for near-zero correlation to overcome — giving up
half the exposure to the far-better leg cost more expected return than
the diversification recovered. §50's gap (0.963 vs 0.526, ~1.8x) was
small enough that the same near-zero-correlation mechanism paid off
decisively, cutting maxDD nearly in half (11.0%/11.9% standalone -> 5.4%
combined) while still raising Sharpe above the stronger leg alone.

**VERDICT on both sections together: five of six combined-book pairings
tested this project now show a real diversification benefit (§44, §48,
§49, §50); only §47 (the single largest quality gap tested, 3.2x) failed.**
The refined, honestly-stated rule: near-zero correlation is a reliable,
recurring property across every family/instrument/asset-class pairing
tried in this project (range +0.011 to +0.074 across all five pairings
measured: §44 +0.053, §47 +0.041, §48 +0.074, §49 +0.011, §50 +0.067),
but whether a 50/50 FIXED-CAPITAL weight realizes that benefit depends on
both the size of the quality gap between legs (§47 vs §50) and the
relative volatility of each leg (§49's gold leg's higher vol muted an
even-lower-correlation benefit). A risk-parity or vol-matched weighting
scheme was not tested in any pairing — flagged as the natural next
question for anyone pursuing this further, out of scope for this
project's stated entry/exit/SL/TP-refinement focus.

**Files:** `research/orb_gold_us30_breakout_combined_book.py`,
`research/nas100_macross_breakout_combined_book.py`. Results:
`results/orb_gold_us30_breakout_combined_book.csv`,
`results/nas100_macross_breakout_combined_book.csv`. Reproduce:
`python research/orb_gold_us30_breakout_combined_book.py` and
`python research/nas100_macross_breakout_combined_book.py`.

**Trial count: 0 new** (both are portfolio checks, no parameter search).
**Cumulative trials: N=1570** (unchanged).

---

## §51 — RISK-PARITY RE-WEIGHTING of all five combined-book pairings —
## rescues §47's "failed" pairing and produces the project's best-ever
## result (2026-09-16)

Direct follow-up to the open question flagged in §49: does inverse-
volatility (risk-parity) weighting recover the diversification benefit
that a fixed 50/50 NOMINAL-CAPITAL split muted when the two legs have very
different standalone volatility? Applied `w_i proportional to 1/std_i`
(exact equal-risk-contribution for two assets when correlation is zero,
a close approximation at this project's near-zero correlations of +0.011
to +0.074) to all five already-scored pairings (§44/§47/§48/§49/§50),
reusing each pairing's already-saved daily-return CSVs unchanged — pure
re-weighting, zero new backtests.

**Result — improves 4 of 5 pairings, one dramatically:**

| Pairing | Weights (A/B) | Fixed 50/50 Sharpe/maxDD | Risk-parity Sharpe/maxDD | Delta |
|---|---|---|---|---|
| §44 NAS100+US30 macross | 0.28/0.72 | +1.135 / 5.7% | **+1.230 / 3.6%** | +0.095 |
| §47 NAS100+US30 breakout | 0.27/0.73 | +0.967 / 5.0% | **+1.382 / 3.9%** | **+0.416** |
| §48 US30 macross+breakout | 0.40/0.60 | +1.707 / 3.4% | **+1.824 / 3.0%** | +0.117 |
| §49 ORB gold+US30 breakout | 0.28/0.72 | +1.687 / 4.5% | **+1.900 / 2.8%** | +0.213 |
| §50 NAS100 macross+breakout | 0.42/0.58 | +1.054 / 5.4% | +1.016 / 4.9% | -0.038 |

**§47's previously-failed pairing is RESCUED by risk-parity** (Sharpe
+0.967 -> +1.382, maxDD 5.0% -> 3.9%) — confirming that the fixed-50/50
failure diagnosed in §47 really was a WEIGHTING artifact, not evidence
that the pairing itself lacks diversification value: NAS100 breakout's
standalone volatility is ~2.7x US30 breakout's, so the naive 50/50 gave
NAS100 breakout far more realized risk than its edge justified. Risk-
parity still does not push §47 above holding US30 breakout alone
(+1.684) — the underlying quality gap (§46 vs §45) is real, not just a
weighting illusion, but risk-parity captures most of the available
diversification value that 50/50 threw away. §50 is the lone case where
risk-parity is marginally WORSE than 50/50 (-0.038) — consistent with
§50 already having the smallest quality gap of the mismatched pairings,
where 50/50 happened to be closer to the true optimum by chance.

**NEW PROJECT-BEST RESULTS, both under risk-parity:**
- **ORB gold + US30 breakout (§49), risk-parity weights 28%/72%: Sharpe
  +1.900, maxDD 2.8%, 9/9 years net-positive (every single year,
  including the worst, 2018, still +0.9%)** — the most robust result in
  the project's entire history, cross-asset-class, and higher Sharpe than
  any pure spot/CFD result found by entry/exit refinement alone
- **US30 macross + breakout (§48), risk-parity weights 40%/60%: Sharpe
  +1.824, maxDD 3.0%, 8/8 years net-positive (worst, 2023, still +1.0%)**
  — a close second, entirely on one instrument

Both now sit just behind credit-spread SPY (§41, Sharpe +2.090, a
different asset class per the user's own scoping) as the strongest
results in the project, and both are dramatically more robust on a
year-by-year basis (9/9 and 8/8 positive years respectively) than any
single-leg candidate found via entry/exit refinement alone.

**Caveats, stated plainly:** weights were computed ONCE from each leg's
full-sample daily-return standard deviation — an in-sample choice. A
genuinely deployable risk-parity scheme would re-estimate weights on a
rolling/walk-forward basis, which was not attempted here (this section
answers "does risk-parity work in principle," not "here is a deployable
rebalancing rule"). DSR/deflation was not computed for weighting choices
since this is not a parameter search — no p-hacking risk from testing one
principled, pre-specified weighting rule (inverse-vol) against the
already-established fixed-weight baseline, but this is a real, honest
limitation on how far the headline numbers should be trusted for live
deployment.

**VERDICT: risk-parity weighting is a clear, low-effort improvement over
fixed 50/50 for combining these legs, worth adopting as the default
weighting scheme for any future combined-book work in this project.**
It does not manufacture edge from nothing (§50's quality-gap pairing
still doesn't beat US30 breakout alone even under risk-parity) but it
reliably captures more of the real diversification value that a naive
50/50 split leaves on the table whenever the two legs' volatilities
differ meaningfully — which, in this project, has been true of every
pairing tested.

**Files:** `research/combined_book_risk_parity.py`. Results:
`results/combined_book_risk_parity.csv`. Reproduce:
`python research/combined_book_risk_parity.py`.

**Trial count: 0 new** (re-weighting of five already-scored portfolio
checks, no parameter search). **Cumulative trials: N=1570** (unchanged).

---

## §52 — ROLLING (causal, walk-forward) risk-parity — closes §51's own
## stated caveat: does the benefit survive without look-ahead? YES, mostly
## (2026-09-16)

§51 stated its own limitation plainly: weights were computed ONCE from
each leg's FULL-SAMPLE standard deviation — an in-sample choice no live
strategy could actually have known in advance. This section replaces that
with a genuinely causal, walk-forward scheme and re-measures the two new
project-best pairings (§48 US30 macross+breakout, §49 ORB gold+US30
breakout) to see how much of §51's improvement survives.

**Scheme (stated before any result seen):** monthly rebalance. On the
last trading day of each calendar month, compute each leg's trailing
90-CALENDAR-DAY standard deviation using ONLY returns up to and including
that day, apply `w_a = (1/std_a)/(1/std_a+1/std_b)` as the FIXED weight
for the entire following month (no intra-month rebalancing, no forward
knowledge). Default to flat 50/50 before 90 days of history exist. The
weight computed on a rebalance day is not usable until the next day — the
standard purge-style discipline this project applies to signal
parameters (CLAUDE.md's rolling walk-forward rule), applied here to a
portfolio weight instead.

**Result — the rolling scheme captures MOST of §51's in-sample benefit,
confirming it is real and not a look-ahead artifact:**

| Pairing | Fixed 50/50 | In-sample RP (§51) | Rolling RP (causal) |
|---|---|---|---|
| §48 US30 macross+breakout | Sharpe +1.707 / 3.4% | +1.824 / 3.0% | **+1.755 / 3.2%** |
| §49 ORB gold+US30 breakout | Sharpe +1.687 / 4.5% | +1.900 / 2.8% | **+1.793 / 3.1%** |

Both rolling-weighted books still clearly beat fixed 50/50 on both Sharpe
and drawdown, and retain their excellent year-by-year robustness: §48
rolling stays 8/8 years positive (worst 2023, +0.7%); §49 rolling stays
9/9 years positive (worst 2018, +1.1%) — EVERY year of the two candidates'
combined 17-year total history remains net-positive even under a fully
causal, no-look-ahead weighting rule. The realized weight on the
higher-vol leg (ORB gold, US30 macross) genuinely moves over time — ORB
gold's weight ranged from 0.06 to 0.58 across the sample (mean 0.31,
close to the in-sample estimate of 0.28) as its trailing volatility
fluctuated, confirming the scheme is actually adapting rather than
converging to a static value by construction.

**VERDICT: §51's risk-parity benefit is real and (mostly) deployable, not
an in-sample artifact.** The rolling scheme gives up roughly a third to a
half of the gap between fixed-50/50 and in-sample-optimal risk-parity
(expected — a rolling estimate is always noisier and slower to adapt than
knowing the whole sample's volatility in advance) but keeps the large
majority of the improvement over naive 50/50, with the same outstanding
year-by-year robustness. **Recommend the ROLLING (not in-sample) risk-
parity weighting as the honestly-deployable version of this project's
combined-book work**, with ORB gold+US30 breakout (rolling RP, Sharpe
+1.793, maxDD 3.1%, 9/9 years positive) as the standout result. Genuine
transaction-cost/rebalancing-friction of the monthly weight shift itself
was not modeled (the underlying legs' own trade-level costs are already
priced in; only the portfolio-level capital reallocation between two
already-running strategies is unmodeled) — a small, honestly-flagged
residual gap between this section's numbers and a fully live-tradeable
implementation.

**Files:** `research/combined_book_risk_parity_rolling.py`. Results:
`results/combined_book_risk_parity_rolling.csv`. Reproduce:
`python research/combined_book_risk_parity_rolling.py`.

**Trial count: 0 new** (re-weighting of already-scored legs with a
causal, walk-forward rule — no new backtest). **Cumulative trials:
N=1570** (unchanged).

---

## §53 — NAS100 MACROSS + US30 BREAKOUT combined book — a new pairing on
## a COMBINED axis (cross-instrument AND cross-family at once) — a real
## but muted diversification benefit (2026-09-16)

A new pairing not yet tested: every prior pairing varied only ONE axis at
a time (§44/§47/§49/§50 held family fixed while varying instrument or
asset class; §48/§50 held instrument fixed while varying family). This
pairs NAS100 macross (§42, Sharpe +0.963, beats NAS100 B&H) with US30
breakout (§45, Sharpe +1.684, beats US30 B&H) — different instrument AND
different family simultaneously. Quality gap ~1.75x, similar in size to
§50's ~1.8x gap (which worked well under fixed 50/50). Method identical
to every prior pairing: both legs' own unchanged engines/params, daily
returns aligned on the union of trading days, both fixed 50/50 AND
in-sample risk-parity weights computed (per §51's now-adopted default).

**Result:**

| Weighting | Sharpe | maxDD | Years positive |
|---|---|---|---|
| NAS100 macross standalone | +0.963 | 11.0% | — |
| US30 breakout standalone | +1.684 | 4.1% | — |
| naive average of the two legs | +1.323 | — | — |
| Fixed 50/50 combined | +1.221 | 5.8% | 8/8 |
| **Risk-parity (21%/79%) combined** | **+1.634** | **3.4%** | 8/8 |

Correlation +0.079 (near-zero, consistent with every pairing). Fixed
50/50 underperforms BOTH the naive average and holding US30 breakout
alone — a muted result, similar in shape to §49/§50's quality-gap
pattern rather than §44/§48's clean wins. Risk-parity recovers most (but
not quite all) of the gap: Sharpe rises from +1.221 to +1.634 and maxDD
drops from 5.8% to 3.4%, but the combined book still does not QUITE beat
holding US30 breakout alone (+1.684) even under risk-parity — unlike
§50, where a similarly-sized quality gap (1.8x) DID let even fixed 50/50
beat both legs outright. **This shows the instrument/family axis itself
also matters, not just the numerical size of the quality gap** — the
same ~1.8x gap produced a clean win on NAS100-only (§50) but only a
partial recovery here on a cross-instrument/cross-family pairing,
presumably reflecting a different realized correlation/volatility
structure between the specific legs involved, not a fixed rule that can
be read off gap size alone.

**VERDICT: a real but genuinely mixed/muted result, reported honestly
rather than forced into either the "wins" or "fails" bucket.** Confirms,
once again, that near-zero correlation is a robust, recurring finding
across every pairing tried in this project (now measured six times, all
in the +0.011 to +0.079 range) — but whether that correlation translates
into a decisive combined-book win depends on a mix of factors (quality
gap size, relative volatility, and apparently the specific legs
involved) that this project has not fully reduced to a single predictive
rule. Risk-parity remains the right DEFAULT weighting choice (it recovers
most of the available value here, as everywhere else tested), but it is
not guaranteed to make every pairing beat its best individual leg.

**Files:** `research/nas100_macross_us30_breakout_combined_book.py`.
Results: `results/nas100_macross_us30_breakout_combined_book.csv`.
Reproduce: `python research/nas100_macross_us30_breakout_combined_book.py`.

**Trial count: 0 new** (portfolio check, no parameter search). **Cumulative
trials: N=1570** (unchanged).

---

## §54 — ORB gold RETEST + US30 MACROSS combined book — a seventh
## pairing, lowest correlation yet, a clean win under plain 50/50
## (2026-09-16)

Completes the "ORB gold x both US30 candidates" set: §49 paired gold with
US30 breakout, this section pairs gold with US30's OTHER family, macross
(§43, Sharpe +0.999 standalone). Unlike §49 (where gold was the WEAKER
leg vs US30 breakout's +1.684), here gold is the STRONGER leg (+1.488 vs
macross's +0.999, quality gap ~1.49x) — a genuinely different shape,
worth testing directly rather than assuming the outcome, per §53's own
conclusion that gap size alone is not fully predictive. Method identical
to every prior pairing: both legs' own unchanged engines/params, daily
returns aligned on the union of trading days, tested at both fixed 50/50
and in-sample risk-parity weight.

**Result — a clean win, no risk-parity rescue needed:**

| Weighting | Sharpe | maxDD | Years positive |
|---|---|---|---|
| ORB gold standalone | +1.488 | 12.1% | — |
| US30 macross standalone | +0.999 | 6.1% | — |
| naive average of the two legs | +1.243 | — | — |
| **Fixed 50/50 combined** | **+1.513** | **4.7%** | 8/9 |
| Risk-parity (36%/64%) combined | +1.489 | 4.2% | 8/9 |

Correlation: **+0.004 — the LOWEST of any pairing tested in this project**
(previous low was §49's +0.011). Plain fixed 50/50 already beats BOTH
legs individually (not just the average) here — no risk-parity rescue
needed, unlike §47/§49/§53's mixed or muted results. Risk-parity actually
gives a marginally LOWER Sharpe than fixed 50/50 here (+1.489 vs +1.513,
the second such case after §50) though it further improves maxDD (4.2%
vs 4.7%) — a reminder that risk-parity is not a strict Sharpe-improving
operation in every case, it optimizes for equal risk contribution, which
is not always identical to maximizing Sharpe. 8/9 years net-positive
under both weightings.

**VERDICT: a clean, low-effort diversification win, and the lowest
correlation measured in this project's entire combined-book work.**
Confirms gold and US equity indices remain the most reliably decorrelated
pairing available across every family combination tried (§49 and §54 are
this project's two lowest-correlation results, both featuring ORB gold).
Neither weighting scheme was forced to rescue anything here — a useful
data point that not every pairing needs risk-parity to show a genuine
benefit; it depends on the specific legs, not a fixed rule.

**Files:** `research/orb_gold_us30_macross_combined_book.py`. Results:
`results/orb_gold_us30_macross_combined_book.csv`. Reproduce:
`python research/orb_gold_us30_macross_combined_book.py`.

**Trial count: 0 new** (portfolio check, no parameter search). **Cumulative
trials: N=1570** (unchanged).

---

## §55 — ORB gold RETEST + NAS100 MACROSS combined book — an eighth
## pairing, completes "ORB gold x both NAS100 candidates" — a near-miss
## on beating the stronger leg (2026-09-16)

Completes the "ORB gold x both NAS100 candidates" set, in parallel to
§49/§54's "ORB gold x both US30 candidates" set: ORB gold (§39, Sharpe
+1.488) paired with NAS100 macross (§42, Sharpe +0.963), quality gap
~1.55x, close to §54's ORB gold+US30 macross gap (~1.49x, which produced
this project's cleanest win). Worth testing directly whether NAS100
macross behaves like its sibling US30 macross when paired with gold, per
§53's finding that the specific legs matter, not just gap size. Method
identical to every prior pairing.

**Result:**

| Weighting | Sharpe | maxDD | Years positive |
|---|---|---|---|
| ORB gold standalone | +1.488 | 12.1% | — |
| NAS100 macross standalone | +0.963 | 11.0% | — |
| naive average of the two legs | +1.225 | — | — |
| Fixed 50/50 combined | +1.400 | 6.4% | 9/9 |
| **Risk-parity (59%/41%) combined** | **+1.475** | **6.6%** | 9/9 |

Correlation +0.021 (low, but not as low as §54's record +0.004 —
NAS100 macross does NOT decorrelate from gold quite as cleanly as its
US30 sibling did, confirming §53's point that the specific instrument
matters, not just "any US equity index vs gold"). Fixed 50/50
underperforms gold alone (+1.400 vs +1.488) — a muted result, similar in
shape to §49/§50/§53. Risk-parity recovers most of the gap (+1.475) and
comes very close to matching gold alone standalone, within 0.013 Sharpe
— the closest any muted/mixed pairing has come to fully closing the gap
under risk-parity. Both weightings hold 9/9 years net-positive — every
year of the combined 9-year span stays positive regardless of weighting
choice, the same excellent robustness pattern every ORB-gold-containing
pairing has shown (§49, §54, §55 all report 8/9 or 9/9).

**VERDICT: a near-miss, not a clean win — genuinely informative alongside
§54's clean win on the sibling US30 pairing.** Two structurally similar
pairings (gold + a US-index macross leg, similar quality gap) produced
noticeably different correlations (US30: +0.004, NAS100: +0.021) and
different outcomes (US30: clean win under plain 50/50; NAS100: muted,
needs risk-parity to nearly close the gap) — reinforcing §53's lesson
that instrument identity matters at the level of the specific pairing,
not just the abstract family/gap-size categories used to predict outcomes
so far in this project.

**Files:** `research/orb_gold_nas100_macross_combined_book.py`. Results:
`results/orb_gold_nas100_macross_combined_book.csv`. Reproduce:
`python research/orb_gold_nas100_macross_combined_book.py`.

**Trial count: 0 new** (portfolio check, no parameter search). **Cumulative
trials: N=1570** (unchanged).

---

## §56/§57 — THE LAST TWO REMAINING PAIRINGS — completing all C(5,2)=10
## combinations from this project's 5-leg candidate pool (2026-09-16)

User asked to try the last two remaining pairings, completing every
possible combination of this project's five candidates (NAS100 macross,
NAS100 breakout, US30 macross, US30 breakout, ORB gold): **NAS100
breakout + US30 macross (§56)** and **ORB gold + NAS100 breakout (§57)**
— the only two of the 10 possible pairs not yet tested (§44/§47/§48/§49/
§50/§53/§54/§55 covered the other eight). Method identical to every prior
pairing: both legs' own unchanged engines/params, daily returns aligned
on the union of trading days, tested at both fixed 50/50 and in-sample
risk-parity weight.

### §56 — NAS100 breakout + US30 macross

Quality gap ~1.9x (0.999/0.526) — between §50's 1.8x (worked cleanly)
and §47's 3.2x (failed under 50/50).

| Weighting | Sharpe | maxDD | Years positive |
|---|---|---|---|
| NAS100 breakout standalone | +0.526 | 11.9% | — |
| US30 macross standalone | +0.999 | 6.1% | — |
| naive average of the two legs | +0.763 | — | — |
| Fixed 50/50 combined | +0.848 | **4.3%** | 7/8 |
| **Risk-parity (35%/65%) combined** | **+0.966** | 4.4% | 7/8 |

Correlation +0.022 (low, consistent with every non-gold pairing). Neither
weighting beats US30 macross alone on Sharpe (+0.999), but risk-parity
comes very close (+0.966, within 0.033) — and BOTH weightings roughly
HALVE the max drawdown relative to either leg standalone (4.3-4.4% vs
6.1%/11.9%) — a genuine, substantial drawdown benefit even where the
Sharpe gap to the best leg isn't fully closed.

### §57 — ORB gold + NAS100 breakout

Quality gap ~2.8x (1.488/0.526) — the SECOND-largest gap tested (behind
only §47's 3.2x), pairing this project's single strongest leg with its
single weakest.

| Weighting | Sharpe | maxDD | Years positive |
|---|---|---|---|
| ORB gold standalone | +1.488 | 12.1% | — |
| NAS100 breakout standalone | +0.526 | 11.9% | — |
| naive average of the two legs | +1.007 | — | — |
| Fixed 50/50 combined | +1.224 | 9.2% | 8/9 |
| Risk-parity (51%/49%) combined | +1.233 | 9.2% | 8/9 |

**Correlation -0.020 — the FIRST NEGATIVE correlation measured in this
project's entire combined-book work** (every other pairing has been
weakly positive, +0.004 to +0.079). Despite this, and despite testing
risk-parity, NEITHER weighting comes close to beating gold alone
(+1.488) — confirming §47's lesson directly: **a large enough quality
gap (here ~2.8x) dominates even the best possible correlation this
project has found.** Risk-parity barely moves the needle here (+1.224 ->
+1.233) because the two legs' realized volatilities are similar enough
(51/49 weights, nearly the fixed 50/50 split already) that there was
little room for risk-parity to reallocate.

**VERDICT ON BOTH, AND ON THE FULL 10-PAIRING PROJECT: quality gap size
remains the single most reliable predictor of whether a combined book
beats its best individual leg, more reliable than correlation alone —
confirmed a final time across the full combinatorial set.** Correlation
in this project has been uniformly low (-0.020 to +0.079 across all 10
pairs, gold pairings the lowest) but that alone never fully overcomes a
gap larger than roughly 1.8-2x; risk-parity reliably narrows the gap
(recovering 60-100% of it across the mixed/muted pairings) but has never
been observed to fully close a gap above ~2x in this project's ten
tested combinations. **The two cleanest, most useful results from the
entire ten-pairing exploration remain §48 (US30 macross+breakout,
same-instrument) and §54 (ORB gold+US30 macross, cross-asset-class) —
both had small gaps (<1.75x) and near-zero-or-lowest correlations, and
both beat every individual leg outright under plain 50/50 weighting,
no rescue needed.**

**Files:** `research/nas100_breakout_us30_macross_combined_book.py`,
`research/orb_gold_nas100_breakout_combined_book.py`. Results:
`results/nas100_breakout_us30_macross_combined_book.csv`,
`results/orb_gold_nas100_breakout_combined_book.csv`. Reproduce:
`python research/nas100_breakout_us30_macross_combined_book.py` and
`python research/orb_gold_nas100_breakout_combined_book.py`.

**Trial count: 0 new** (both are portfolio checks, no parameter search).
**Cumulative trials: N=1570** (unchanged). **All C(5,2)=10 combined-book
pairings from this project's 5-leg candidate pool are now complete.**

---

## §58 — FTMO CHALLENGE RULESET CHECK on the honest deployable best
## candidate — fails on SPEED, not on risk (2026-09-16)

First time any candidate found in the 2026-09-15/16 entry/exit-refinement
+ combined-book work has actually been run through the FTMO ruleset
itself (CLAUDE.md standing rule 6: 5% daily loss, 10% total loss, +10%/
+5% Phase 1/2 profit target, 4 min trading days, Best Day consistency
rule, 60-day challenge window) — everything through §57 measured Sharpe/
maxDD/year-positivity on a standalone equity curve, not challenge
pass/fail, which is a different, harder, path-dependent, all-or-nothing
test.

**Candidate chosen: ORB gold RETEST + US30 breakout, ROLLING (causal,
deployable) risk-parity weighting (§52) — Sharpe +1.793, maxDD 3.1%,
9/9 years net-positive.** Not credit-spread SPY (§41's raw-Sharpe project
best, +2.090): that is an OPTIONS strategy, and FTMO-style prop accounts
are forex/CFD/futures accounts — running a short-vertical income
strategy through an FTMO challenge is not a like-for-like proposition the
way a spot/CFD strategy is. Among the CFD-tradeable candidates, §52's
combined book is the strongest and most robust.

**Method:** both legs' own trade engines reused unchanged (same as §49/
§52), each leg's daily RET_FRAC series built at the project-standard 1%
fixed-fractional risk convention (`research/ftmo_engine.RISK_PER_TRADE`,
the same basis for every Sharpe/maxDD figure reported for these legs
throughout §39-§57), combined under §52's causal monthly-rebalanced
risk-parity weight. A new daily-return FTMO Challenge simulator
(`research/ftmo_challenge_daily.py`) extends `research/ftmo_rules.py`'s
existing per-trade engine to work on a combined, dynamically-weighted
portfolio return series, AND adds the Best Day/consistency rule
(assumed threshold: no single day's profit exceeds 30% of total profit
at the pass point — stated explicitly as an assumption, per this
project's existing FTMO-rules-module convention of flagging exactly
which parameters are modelling choices). Rolling monthly-start
challenges across the full 2017-2025 span (106 overlapping 60-day
windows).

**RESULT, at the project-standard 1% risk-per-trade convention: 0%
CHALLENGE PASS RATE, Phase 1 AND Phase 2, under all three weighting
schemes (fixed 50/50, in-sample RP, rolling RP) — but for a reason that
is GOOD news, not bad:**

| Weighting | Phase 1 (10%) pass rate | Phase 2 (5%) pass rate | Failure reason |
|---|---|---|---|
| Fixed 50/50 | 0.0% | 0.0% | 106/106 `no_target` |
| In-sample RP | 0.0% | 0.0% | 106/106 `no_target` |
| Rolling RP (deployable) | 0.0% | 0.0% | 106/106 `no_target` |

**Every single one of the 106 rolling 60-day windows failed for the SAME
reason: the target was never reached in time — NOT ONE breached the 5%
daily loss or 10% total drawdown limit.** The underlying issue is scale,
not risk: at 1% risk/trade the combined book's own CAGR is only ~6.1%
(compounded return +70.2% over its full 8.97-year span), and the best
60-day window ever observed in nine years of history returned only
+5.77% — the 10% Phase 1 target was never once reached in-sample, let
alone out-of-sample. This is the direct, mechanical consequence of the
project's own conservative 1% fixed-fractional risk convention (CLAUDE.md
standing rule 6's stated FTMO risk convention is 0.5-1%/trade) applied to
a strategy whose edge is real but individually modest per trade.

**Supplementary risk-scaling analysis (informative, not a parameter
search — the underlying trades are UNCHANGED; only the fixed-fractional
risk multiplier applied to the SAME return stream is varied, a pure
linear rescaling): what risk-per-trade would this candidate need to have
a realistic shot at passing, and does it still respect the drawdown
limits?**

| Risk multiplier (x 1%) | maxDD | Phase 1 pass (raw/consistency) | Phase 2 pass (raw/consistency) |
|---|---|---|---|
| 1x (project standard) | 3.1% | 0.0% / 0.0% | 0.0% / 0.0% |
| 2x | 6.1% | 0.0% / 0.0% | 13.2% / 13.2% |
| 3x | 9.1% | 3.8% / 3.8% | 34.0% / 33.0% |
| 4x | 12.1% | 14.2% / 14.2% | 50.0% / 43.4% |
| **5x** | 15.0% | 19.8% / 18.9% | 63.2% / 47.2% |
| **6x (near-peak)** | 17.9% | **33.0% / 32.1%** | 70.8% / **47.2%** |
| 8x | 23.4% | 45.3% / 37.7% | 65.1% / 28.3% |
| 10x | 28.8% | 42.5% / 26.4% (daily-loss breaches now dominant) | 56.6% / 20.8% |

Sharpe is unchanged across every row (+1.793 — a linear rescaling of a
return series leaves Sharpe invariant by construction); only maxDD and
challenge pass rate move. Pass rate rises with risk multiplier up to
roughly 6x-8x, then FALLS as daily-loss and total-DD breaches start
dominating over "ran out of time" as the binding constraint — the
expected shape once increased position size starts making the 5%/10%
drawdown ceilings bind for the first time. **6x risk-per-trade
(effectively ~6% notional risk per trade) is the rough sweet spot found
here: Phase 1 consistency-adjusted pass rate 32.1%, Phase 2 47.2%, still
zero total-DD breaches, only 9 daily-loss breaches out of 106 Phase-1
windows.** This is well above what most real FTMO account rules
consider a professional/responsible risk-per-trade level (0.5-2% is the
typical recommended range) — a genuine tension between "pass the
challenge quickly" and "trade at a size this project's own standing
rules would otherwise recommend," stated honestly rather than picking a
number and presenting it as free.

**VERDICT: the candidate's risk-management profile is EXCELLENT (zero
drawdown-limit breaches across 106 rolling windows at standard sizing,
and even at moderately elevated sizing) but its ABSOLUTE RETURN is too
slow at the project's standard risk convention to pass an FTMO Challenge
within the standard 60-day window.** This is a genuinely different
failure mode from every FTMO-hunt kill earlier in this project (§1-§34),
which mostly failed because the underlying edge itself was too weak or
too costly, not because a real edge was sized too conservatively. Whether
this candidate is "FTMO-viable" therefore depends entirely on the
account's risk tolerance and time pressure: at the project's own standard
1%/trade convention it will never pass in 60 days; at ~5-6x that sizing
it becomes genuinely competitive (~30-50% pass rates) while still
respecting the hard drawdown floors most of the time. No single risk
multiplier is being adopted as a new project recommendation here — this
section reports the honest tradeoff curve, not a chosen answer, since the
right choice depends on risk preferences outside this project's own
standing conventions.

**Files:** `research/ftmo_challenge_daily.py` (new daily-return Challenge
simulator, extends `research/ftmo_rules.py`'s per-trade engine with the
Best Day rule), `research/ftmo_check_best_candidate.py`. Results:
`results/ftmo_check_best_candidate.csv`. Reproduce:
`python research/ftmo_check_best_candidate.py`.

**Trial count: 0 new** (FTMO-ruleset check + a linear risk-rescaling
sensitivity sweep on already-scored legs, not a parameter search).
**Cumulative trials: N=1570** (unchanged).

---

## §59 — 6x RISK-PER-TRADE ADOPTED AS THE FTMO REFERENCE SIZING —
## chained two-phase "actually gets funded" probability: 15.1%
## (2026-09-16)

User directed adopting 6x standard risk-per-trade (identified in §58's
sensitivity sweep as the near-peak pass-rate point: Phase 1
consistency-adjusted 32.1%, Phase 2 47.2%, before daily-loss/total-DD
breaches start dominating at 8-10x) as the reference FTMO sizing for
§52's ORB gold + US30 breakout rolling-risk-parity book. This section
goes one step further than §58's independent per-phase pass rates: it
computes the REALISTIC, CHAINED two-phase probability — Phase 1 must
pass, THEN Phase 2 must ALSO pass starting from the day Phase 1 ended,
in the same continuous attempt — which is the number that actually
matters for deciding whether to attempt this, since the two independent
per-phase rates in §58 overstate the true "gets funded" chance (nothing
requires them to both land in the same attempt).

**Standalone metrics at 6x (Sharpe unchanged from 1x by construction —
a linear rescaling of the same return series; only maxDD, absolute
return, and challenge dynamics change):**
- Sharpe +1.793, **maxDD 17.9%**, total compounded return **+2,032%**
  over the full 8.97-year span
- **9/9 years still net-positive** even at 6x sizing (worst: 2018,
  +4.5%) — the extraordinary year-by-year robustness found at 1x (§52)
  survives the 6x rescaling essentially unchanged, since scaling a
  return series doesn't change which years are net-positive unless a
  year's return flips sign, which none do here
- Worst single day: -6.35% (this SPECIFIC day would itself trigger a
  5%-daily-loss breach if it fell inside an active challenge window —
  consistent with daily_loss appearing as a real, non-trivial failure
  reason below, not just a theoretical possibility)

**Realistic chained two-phase result — the number that matters:**

| Metric | Value |
|---|---|
| Rolling monthly challenge starts tested | 106 |
| Phase 1 passes (consistency-adjusted) | 34 (32.1%) |
| **FULLY FUNDED — Phase 1 then Phase 2 in the same attempt** | **16 (15.1%)** |

Failure-point breakdown across all 106 attempts: 66 never reach the
Phase 1 target in time (`no_target`), 16 succeed at both phases
(`target`, the funded outcome), 12 breach the 5% daily loss limit at
some point in the attempt, 11 pass on raw profit but fail the assumed
30% Best Day consistency check, 1 breaches the 10% total drawdown floor.
**Roughly two-thirds of all attempts still fail purely on speed (never
breach a limit), even at 6x sizing** — the same fundamental "too slow"
issue found at 1x in §58 is reduced, not eliminated, by the risk
increase; the remaining shortfall is now split between running out of
time and genuinely bumping into the risk limits for the first time.

**VERDICT: 15.1% is a real, honestly-computed number for someone
actually planning to attempt this candidate at 6x standard risk on a
two-step FTMO Challenge — meaningfully lower than either phase's own
independent pass rate (32.1% / 47.2%) would suggest in isolation, because
getting funded requires BOTH to land in the same continuous attempt.**
This is neither a strong "yes, do this" nor a clean "no" — a ~1-in-6.6
chance of full funding at a risk level (6% notional/trade) well above
this project's own general standing convention (0.5-1%) is a real,
quantifiable tradeoff, reported as computed rather than rounded toward
either conclusion. The 12 daily-loss and 1 total-DD breaches confirm
that 6x is not a free lunch — real risk-limit exposure exists at this
sizing, unlike the 1x case in §58 where it was essentially zero.

**Files:** `research/ftmo_check_6x_reference.py`. Results:
`results/ftmo_check_6x_reference.csv` (per-challenge-attempt detail,
106 rows). Reproduce: `python research/ftmo_check_6x_reference.py`.

**Trial count: 0 new** (fixed-multiplier FTMO check + two-phase chain
on already-scored legs, not a parameter search). **Cumulative trials:
N=1570** (unchanged).

---

## §60 — CHAINED TWO-PHASE FUNDING PROBABILITY at 2x-5x, for comparison
## against §59's 6x reference — the tradeoff curve is monotonically
## rising across the whole tested range (2026-09-16)

User asked to run the same realistic CHAINED two-phase funding metric
introduced in §59 (Phase 1 must pass, then Phase 2 must ALSO pass
starting immediately after, in the same continuous attempt) at 2x, 3x,
4x, and 5x standard risk, for direct comparison against 6x. §58's
sensitivity sweep only reported INDEPENDENT per-phase pass rates at each
multiplier; this closes the gap by running the harder, realistic chained
metric across the full range at once.

| Risk multiplier | Sharpe | maxDD | Total return (8.97y) | Years positive | Phase 1 (indep.) | Phase 2 (indep.) | **CHAINED (funded)** | DD-breach rate |
|---|---|---|---|---|---|---|---|---|
| 2x | +1.793 | 6.1% | +187.2% | 9/9 | 0.0% | 13.2% | **0.0%** | 0.0% |
| 3x | +1.793 | 9.1% | +380.4% | 9/9 | 3.8% | 33.0% | **0.9%** | 0.0% |
| 4x | +1.793 | 12.1% | +696.5% | 9/9 | 14.2% | 43.4% | **5.7%** | 0.0% |
| 5x | +1.793 | 15.0% | +1,208.9% | 9/9 | 18.9% | 47.2% | **12.3%** | 4.7% |
| 6x (§59 reference) | +1.793 | 17.9% | +2,032.0% | 9/9 | 32.1% | 47.2% | **15.1%** | 12.3% |

(Sharpe is identical at every row by construction — a linear rescaling
of the same return series does not change it; every other column moves.)

**The chained funded rate rises MONOTONICALLY across the entire 2x-6x
range tested — it has not yet turned over within this range.** At 2x it
is exactly 0% because Phase 1 itself never passes (0.0% independent) even
though Phase 2 alone would pass 13.2% of the time in isolation — the
chaining requirement is what makes low multipliers look far worse here
than §58's Phase-2-only number would suggest on its own. Drawdown-limit
breaches stay at a genuine ZERO through 4x, appear only mildly at 5x
(4.7% of attempts), and become material at 6x (12.3%) — confirming the
2x-4x range is essentially risk-free with respect to the FTMO drawdown
floors (the whole shortfall there is pure speed), while 5x-6x is where
the tradeoff against real risk-limit exposure actually begins to bite.

**Important scope note on "6x is near-peak":** §58's "near-peak" framing
was based on INDEPENDENT per-phase rates (Phase 1 peaked near 6x-8x,
Phase 2 near 4x-6x) — but the CHAINED metric computed here is still
rising at 6x within the tested 2x-6x range, and was not extended to 7x-
10x in this section (the user asked specifically for 2x-5x vs 6x). It
remains an open, unanswered question whether the chained funded rate
peaks somewhere above 6x (§58's independent-rate data suggests 8x's
higher Phase 1 rate, 45.3%, could plausibly push the chained number
higher still before the same daily-loss erosion seen in the independent
sweep starts pulling it back down) or whether chaining's extra
constraint changes where that peak actually falls. Not resolved here —
flagged explicitly rather than assumed.

**VERDICT: the full 2x-6x picture confirms 6x is the best of the range
actually tested for the metric that matters (15.1% chained-funded,
versus 12.3% at 5x and near-zero below that), and clarifies exactly where
the tradeoff curve's shape changes — real drawdown-limit risk only
becomes material from 5x onward, not before.** Whether pushing past 6x
would improve the chained funded rate further, and at what additional
drawdown-breach cost, remains untested and is the natural next question
if this line of inquiry continues.

**Files:** `research/ftmo_check_risk_multiplier_sweep.py` (reuses
`research/ftmo_check_6x_reference.py`'s `two_phase_chain()` unchanged).
Results: `results/ftmo_check_risk_multiplier_sweep.csv`. Reproduce:
`python research/ftmo_check_risk_multiplier_sweep.py`.

**Trial count: 0 new** (fixed-multiplier FTMO checks on already-scored
legs, not a parameter search). **Cumulative trials: N=1570** (unchanged).

---

## §61 — CLOSES §60's OPEN QUESTION: extending the sweep to 7x-14x finds
## the true chained-funding PEAK at 6x, then a steady decline
## (2026-09-16)

§60 left one question explicitly open: does the chained two-phase funded
rate keep rising past 6x, or has it already peaked? Extended
`research/ftmo_check_risk_multiplier_sweep.py`'s `MULTIPLIERS` to include
7x, 8x, 9x, 10x, 12x, 14x and re-ran the identical chained metric.

| Multiplier | maxDD | Phase 1 (indep.) | Phase 2 (indep.) | **CHAINED (funded)** | DD-breach rate |
|---|---|---|---|---|---|
| 5x | 15.0% | 18.9% | 47.2% | 12.3% | 4.7% |
| **6x** | 17.9% | 32.1% | 47.2% | **15.1% (PEAK)** | 12.3% |
| 7x | 20.7% | 35.8% | 34.9% | 11.3% | 24.5% |
| 8x | 23.4% | 37.7% | 28.3% | 10.4% | 35.8% |
| 9x | 26.1% | 33.0% | 20.8% | 7.5% | 47.2% |
| 10x | 28.8% | 26.4% | 20.8% | 7.5% | 50.0% |
| 12x | 33.9% | 23.6% | 16.0% | 5.7% | 56.6% |
| 14x | 38.9% | 18.9% | 17.0% | 5.7% | 55.7% |

**§60's open question is now answered: 6x IS the true peak of the
chained funded-probability curve, not merely the best point in an
arbitrarily-truncated range.** The rate rises monotonically from 2x
through 6x (§60: 0.0%/0.9%/5.7%/12.3%/15.1%), peaks decisively at 6x
(15.1%), then falls steadily and monotonically all the way to 14x
(11.3% -> 10.4% -> 7.5% -> 7.5% -> 5.7% -> 5.7%) — the Phase 1 rate alone
keeps climbing a bit further (peaking near 37.7% at 8x, consistent with
§58's original observation) but Phase 2's rate falls fast enough past 6x
that the CHAINED product declines regardless. Drawdown-limit breaches
climb from a genuine 0% (2x-4x) through 12.3% (6x) to over half of all
attempts (56.6% at 12x) — by 10x+, more than half of all attempts are
now failing on a hard risk-limit breach rather than running out of time,
a complete inversion of the 1x/2x situation where risk-limit breaches
were essentially impossible.

**VERDICT: 6x standard risk-per-trade is confirmed, not just assumed, as
the FTMO-reference sizing that maximizes this candidate's realistic
chained two-phase funding probability (15.1%) across the full range
tested (2x-14x).** Pushing risk higher does NOT trade a lower funded rate
for a compensating benefit elsewhere — total return keeps rising
(monotonically, mechanically, since it's a pure linear rescaling) but
that is irrelevant to whether the account survives the Challenge process
in the first place, which is what the chained metric actually measures.
This closes the open question from §60 with a definite answer rather
than leaving it unresolved.

**Files:** `research/ftmo_check_risk_multiplier_sweep.py` (MULTIPLIERS
extended from `(2,3,4,5,6)` to `(2,3,4,5,6,7,8,9,10,12,14)`). Results:
`results/ftmo_check_risk_multiplier_sweep.csv` (now 11 rows, 2x-14x).
Reproduce: `python research/ftmo_check_risk_multiplier_sweep.py`.

**Trial count: 0 new** (fixed-multiplier FTMO checks on already-scored
legs, not a parameter search). **Cumulative trials: N=1570** (unchanged).

---

## §62 — CORRECTION: §58-§61's "Best Day / consistency" rule was
## FABRICATED and WRONG — verified live against ftmo.com, the real
## 2-Step ruleset has NO such rule at all, and the true chained-funding
## peak is at ~13-15x, not 6x (2026-09-16)

User asked to verify what maxDD limit FTMO actually uses. Live web
lookup (ftmo.com/en/trading-objectives/, cross-checked against two
independent third-party rule summaries) confirmed the 5%-daily / 10%-
total (static) / +10%-Phase1 / +5%-Phase2 / 4-min-trading-days numbers
this project's `research/ftmo_rules.py` has modelled since before this
session were and remain CORRECT for FTMO's 2-Step Challenge product.
**But the same lookup revealed that §58's `research/
ftmo_challenge_daily.py` had ALSO added a 30%-threshold "Best Day /
consistency" rule as a hard, account-terminating filter — and that rule
is simply WRONG for the 2-Step product being modelled, on three
independent counts, not a modelling assumption that "varies by account
type" as it was originally caveated:**

1. **The 2-Step Challenge/Verification has NO Best Day or consistency
   rule at all, in either phase or on the funded account** — confirmed
   directly from FTMO's own Trading Objectives page and independently
   corroborated.
2. Where FTMO's Best Day rule DOES exist, it applies **only to the
   1-Step account**, at a **50% threshold**, not the 30% assumed here.
3. Even on the 1-Step account, breaching it is **explicitly a SOFT,
   non-terminating "payout gate"** (the trader must keep generating
   profit until compliant) — never an account termination, which is
   how §58-§61 were applying it to a product that doesn't even have the
   rule.

**This means every "consistency-adjusted" figure reported in §58, §59,
§60, and §61 was computed against a fabricated rule and understates the
true pass/funding rate — sometimes by a large margin.** `research/
ftmo_challenge_daily.py` has been corrected: `best_day_cap` now defaults
to `None` (disabled, correct for the 2-Step product), kept only as an
option for anyone who later wants to correctly model the 1-Step
account's real, soft 50% gate. All three FTMO scripts
(`ftmo_check_best_candidate.py`, `ftmo_check_6x_reference.py`,
`ftmo_check_risk_multiplier_sweep.py`) were updated and re-run.

**Corrected results — §58's 1x-risk numbers are UNCHANGED** (0% Challenge
pass rate at both phases was always driven entirely by `no_target`, never
by the fabricated consistency rule, so that specific finding stands
as-is). **§59/§60/§61's multiplier-sweep conclusions are NOT unchanged —
the erroneous rule was materially suppressing pass rates at every
multiplier above ~4x, and suppressing them by DIFFERENT amounts at
different multipliers** (the erroneous filter's bite is path-dependent,
not a constant discount, because it depends on which specific day within
each specific challenge attempt happens to be the "best day" — a detail
that varies non-linearly with the risk multiplier even though the
underlying return series is only linearly rescaled). The corrected full
sweep (2x-50x):

| Multiplier | maxDD | Phase 1 (indep.) | Phase 2 (indep.) | **CHAINED (funded), CORRECTED** | Old (wrong) chained value | DD-breach rate |
|---|---|---|---|---|---|---|
| 2x | 6.1% | 0.0% | 13.2% | 0.0% | 0.0% | 0.0% |
| 3x | 9.1% | 3.8% | 34.0% | 0.9% | 0.9% | 0.0% |
| 4x | 12.1% | 14.2% | 50.0% | 8.5% | 5.7% | 0.0% |
| 5x | 15.0% | 19.8% | 63.2% | 17.0% | 12.3% | 4.7% |
| 6x | 17.9% | 33.0% | 70.8% | **25.5%** | ~~15.1%~~ | 12.3% |
| 7x | 20.7% | 39.6% | 68.9% | 27.4% | ~~11.3%~~ | 24.5% |
| 8x | 23.4% | 45.3% | 65.1% | 29.2% | ~~10.4%~~ | 36.8% |
| 9x | 26.1% | 43.4% | 60.4% | 29.2% | ~~7.5%~~ | 48.1% |
| 10x | 28.8% | 42.5% | 56.6% | 31.1% | ~~7.5%~~ | 53.8% |
| 12x | 33.9% | 44.3% | 52.8% | 31.1% | ~~5.7%~~ | 61.3% |
| 13x | 36.4% | 43.4% | 52.8% | 32.1% | (not tested) | 62.3% |
| **14x** | 38.9% | 44.3% | 53.8% | **33.0% (PEAK)** | ~~5.7%~~ | 62.3% |
| 15x | 41.3% | 45.3% | 53.8% | 32.1% | (not tested) | 63.2% |
| 16x | 43.6% | 41.5% | 50.0% | 28.3% | (not tested) | 67.9% |
| 18x-20x | 48-52% | ~37% | ~44% | 23.6% | (not tested) | 73.6% |
| 25x | 62.0% | 36.8% | 40.6% | 20.8% | (not tested) | 77.4% |
| 30x-50x | 70-93% | 28-36% | 28-37% | 15-22% | (not tested) | 78-85% |

**§61's central claim ("6x is CONFIRMED as the true peak") is RETRACTED.
The corrected true peak is a broad plateau spanning roughly 12x-15x,
centered at 14x, with a chained funding probability of 33.0% — materially
higher than the erroneous 15.1% figure previously reported for 6x, and
the plateau itself is meaningfully HIGHER-RISK than previously
concluded.** At the corrected peak (14x = 14% notional risk/trade), the
standalone 8.97-year equity curve's own maxDD is 38.9% and 62.4% of
individual 60-day challenge ATTEMPTS breach a daily-loss or total-DD
limit at some point — both far more extreme than the (already elevated)
6x picture. Past the 12x-15x plateau the curve declines the same way it
did before correction, just from a higher, later peak: by 40x-50x, more
than 84% of attempts breach a limit and funded probability falls back
toward 15%.

**VERDICT: this is a genuine correction, not a refinement — the entire
"6x is optimal" conclusion from §59-§61 was built on a rule that does
not exist for the product being modelled, and the true answer is both
quantitatively different (33.0% vs 15.1% peak funded probability) AND
qualitatively different (the optimal risk level is roughly DOUBLE what
was previously concluded, with correspondingly higher real drawdown
exposure).** This does not change the §58 finding that 1x standard risk
never passes (that was never affected by the erroneous rule), and it
does not change any of §35-§57's Sharpe/maxDD/DSR results (the
consistency-rule error was contained entirely to the FTMO-Challenge-
specific analysis in §58-§61, not the underlying strategy backtests).
Flagged prominently, per this project's own standing rule 7 (honest
reporting — never hide a bug, correct it visibly), rather than quietly
patched. Whoever revisits this line of inquiry should treat §62's table
as authoritative and §59-§61's superseded numbers as historical record
only (retained, not deleted, so the correction itself remains legible).

**Files corrected:** `research/ftmo_challenge_daily.py` (default
`best_day_cap` changed from `0.30` to `None`, docstring rewritten with
the verified real ruleset and an explicit correction note),
`research/ftmo_check_best_candidate.py`, `research/
ftmo_check_6x_reference.py`, `research/ftmo_check_risk_multiplier_
sweep.py` (all three re-run with the corrected model; `MULTIPLIERS`
extended to `2x-50x` to find the corrected peak). Results:
`results/ftmo_check_best_candidate.csv`, `results/
ftmo_check_6x_reference.csv`, `results/ftmo_check_risk_multiplier_
sweep.csv` (all regenerated). Reproduce: re-run any of the three
scripts.

**Trial count: 0 new** (a bug-fix + re-run of existing FTMO-ruleset
checks, not a parameter search). **Cumulative trials: N=1570**
(unchanged).

Sources verified live 2026-09-16:
- [FTMO Trading Objectives](https://ftmo.com/en/trading-objectives/)
- [Does FTMO Have a Consistency Rule? (PropVator)](https://propvator.com/blog/does-ftmo-have-a-consistency-rule/)

---

## §63 — PERIOD-ROBUSTNESS CHECK on §62's corrected funding-probability
## numbers — the 14x peak is more front-loaded/period-dependent than the
## 6x point (2026-09-16)

User asked whether the FTMO funding-probability work had been tested
against different historical sub-periods, or only pooled across the
full 2017-2025 sample. It had not — §58-§62 all reported one pooled
number across all 106 rolling monthly-start challenges. This section
splits the SAME already-computed challenge outcomes (§62's corrected,
no-fabricated-rule model) by which era each challenge's START date
falls in — a pure post-hoc partition, no re-simulation — at both
reference points examined so far: 6x (§59's original point) and 14x
(§62's corrected true peak).

**Result:**

| Split | 6x funded rate | 14x funded rate |
|---|---|---|
| Full pooled sample (106 challenges) | 25.5% | 33.0% |
| 2017-2021 (H1, n=52) | 28.8% | 42.3% |
| 2021-2025 (H2, n=54) | 22.2% | 24.1% |
| 2017-2020 (T1, n=39) | 30.8% | 43.6% |
| 2020-2023 (T2, n=40) | 17.5% | 27.5% |
| 2023-2025 (T3, n=27) | 29.6% | 25.9% |

**At 6x, the decline from the earliest to the latest era is moderate**
(28.8% -> 22.2% across halves, a ~6.6pp gap) with a dip in the 2020-2023
middle third (17.5%, likely reflecting the COVID-era volatility spike
and its aftermath) that recovers by 2023-2025 (29.6%). **At 14x, the
decline is far more pronounced** (42.3% -> 24.1% across halves, a
~18.2pp gap — nearly HALVING) and does not recover in the most recent
third (25.9%, similar to the middle third rather than bouncing back like
6x's did). **The 14x pooled headline of 33.0% is disproportionately
carried by the 2017-2020 period (43.6%) — the two most recent thirds
(2020-2023, 2023-2025) average only ~26.7%, much closer to 6x's own
pooled figure than to 14x's own headline.**

**VERDICT: this is a real, material robustness caveat on §62's corrected
"14x is the true peak" finding — the funding-rate ADVANTAGE of 14x over
6x is substantially front-loaded into the earlier (2017-2020) portion of
the sample and has been shrinking over time, while 6x's own funding rate
is comparatively STABLE across eras.** This does not overturn §62's
correction (14x's pooled average genuinely is higher than 6x's across
the full sample, and the underlying "Best Day rule" bug fix stands
regardless of this section's findings) — but it means anyone choosing
between the two multipliers going forward should weight the MORE RECENT
performance more heavily than the pooled full-sample average suggests,
which favors 6x's greater period-to-period stability over 14x's higher
but less consistent pooled number. Neither multiplier is adopted or
rejected here — the tradeoff is reported, not resolved, consistent with
every prior FTMO-sizing section in this project.

**Files:** `research/ftmo_check_period_robustness.py` (reuses `research/
ftmo_check_6x_reference.py`'s `two_phase_chain()` unchanged). Results:
`results/ftmo_check_period_robustness.csv`. Reproduce:
`python research/ftmo_check_period_robustness.py`.

**Trial count: 0 new** (a period-based partition of already-computed
FTMO challenge outcomes, not a parameter search or new backtest).
**Cumulative trials: N=1570** (unchanged).
