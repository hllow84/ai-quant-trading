# CLAUDE.md — AI Quant Trading Lab (repo root)

Read this at the start of every session in this repo. These are standing rules that
apply without reminders. The parent folder `C:\Claude Code\AI Quant Trading\CLAUDE.md`
holds the longer crypto-factor-research context; this file is the enforced rulebook for
ALL work in `crypto-factor-lab` (crypto factors AND forex/gold FTMO strategies).

## START HERE
**Read `STATE_OF_PLAY.md` (repo root) before doing anything else — start with its
top banner and the 2026-09-15/16 blockquote right before section 1, which is the
current one-stop summary.** Short version: the original FTMO-ruleset hunt (§1-§34,
no viable edge across ~1085 trials) is superseded by later work. As of 2026-09-16
(cumulative trial count N=1570) there are **four real candidates that beat their
own instrument's buy-and-hold** — ORB gold RETEST (XAUUSD, Sharpe +1.488, §39),
credit-spread SPY (options, Sharpe +2.090, §41), NAS100 H4 macross (Sharpe +0.963,
§42) and US30 H4 macross (Sharpe +0.999, §43) — plus US30 H4 breakout-retest
(Sharpe +1.684, §45, the strongest single spot/CFD leg). All ten pairwise
combined-books of these candidates (plus the weaker NAS100 breakout, §46) were
tested (§44-§57): the honest, deployable best is **ORB gold + US30 breakout under
rolling (causal, no-look-ahead) risk-parity weighting — Sharpe +1.793, maxDD 3.1%,
9/9 years net-positive (§52)**. None of these clears this project's DSR bar against
its full contaminated family pool — every verdict rests on stated economic/
robustness evidence, not DSR. **This candidate WAS run through the FTMO ruleset
itself (§58): 0% Challenge pass rate at the project's standard 1% risk/trade
convention, but for a genuinely different reason than every earlier FTMO-hunt
kill — it never once breaches the 5% daily or 10% total drawdown limit across 106
rolling 60-day windows, it simply never compounds fast enough to hit the +10%/+5%
Phase 1/2 target in time (best-ever 60-day return in 9 years was +5.77%). §59-§61
then swept risk-per-trade multipliers computing a chained two-phase funded
probability (Phase 1 must pass, THEN Phase 2 must also pass in the same attempt) —
**but §62 (verified live against ftmo.com) found and corrected a fabricated "Best
Day/consistency" rule those sections had applied: FTMO's actual 2-Step
Challenge/Verification product (the one being modelled, 5%/10%/10%/5%/4-days) has
NO such rule at all — it exists only on the 1-Step account, at 50% not 30%, and
even there is a soft non-terminating gate, never an account termination.**
Correcting this MATERIALLY changes the conclusion: the true chained-funding peak
is a broad 12x-15x plateau (centered at 14x, ~33% funded probability, maxDD ~39%),
not 6x (~15% funded, maxDD 18%) as §61 had wrongly concluded — roughly DOUBLE the
optimal risk level, with correspondingly higher real drawdown exposure. §58's
"1x never passes, purely on speed" finding is unaffected (it was never driven by
the erroneous rule). **§63 then checked period-robustness and found 14x's
advantage is front-loaded: split by era, 14x's funded rate falls from 42.3%
(2017-2021) to 24.1% (2021-2025), nearly halving, while 6x is comparatively
stable (28.8% -> 22.2%) — the two most recent thirds of history average ~26.7%
under 14x, much closer to 6x's own number than to 14x's pooled headline.** Neither
multiplier is adopted as a final recommendation; §62's correction stands, but §63
is a real reason to weight recent performance over the full-sample pooled average
when actually choosing a sizing. Treat §62+§63 together as authoritative over
§59-§61's superseded numbers. **2026-09-17 (§64-§66, N=1570→1645):** a fifth
signal family (momentum) was pushed through the joint grid method on US30
H4 and found a genuine buy-and-hold-beating candidate (Sharpe +1.010, maxDD
19.0%, OOS holds, 6/8 years positive) — but it is structurally the weakest
of the five candidates (maxDD 1.4x-4.6x the others, low 30% win rate, needed
three edge-following rounds), added to the pool but not recommended standalone
(§64). The FTMO ruleset was run on a second combined book (US30 macross +
US30 breakout, §48): despite near-identical Sharpe/maxDD to §52's book, it
funds materially worse at every multiplier (16.0% vs 25.5% at 6x, 22.3% vs
33.0% at 14x) — §52's ORB gold + US30 breakout book remains the best FTMO
candidate, now confirmed against a real second comparison (§65). A causal
walk-forward risk-multiplier rule (pick the largest multiplier whose trailing,
no-look-ahead maxDD stays under a cap) was tested to resolve §62/§63's 6x-
vs-14x tradeoff: an EXPANDING trailing window is degenerate (picks one
multiplier forever, never adapts — a methodological trap now documented), but
a ROLLING 2-year window at a 20% cap beats fixed 6x on the same challenge
pool (30.5% vs 28.0% funded) while staying more stable across eras than
14x — the closest thing to an actual resolution of the sizing question,
though still a single stated rule, not a swept optimum (§66).
**2026-09-17 §67 (CRITICAL — read before any live-money discussion):** the
out-of-regime test that killed every prior "winner" in this project (index
basket, Sneaky Pivot, original ORB) was finally run on the actual §39-§66
refined candidates, using continuous real-spread NAS100/US30 H1 data
2013-2017 and a XAUUSD 2017 stub. **4 of 5 individual candidates FAIL**
(NAS100 macross, US30 macross Sharpe -1.175, US30 breakout, US30 momentum
Sharpe -0.966/maxDD 45.9%) — same failure signature as every earlier
candidate. **The §48/§65 combined book (US30 macross+breakout) also fails,
losing money out-of-regime** (Sharpe -0.70/-0.61, total return -8.9%/-7.6%,
1/5 years positive). Only ORB gold RETEST and the §52 ORB gold+US30
breakout book "survive," but both rest on a THIN single-year (2017) gold
sample, not a robust multi-year confirmation. **Do not treat any
2018-2025-only backtest result in this project as sufficient grounds for
live deployment** — this is exactly the failure mode the project's own
out-of-regime convention exists to catch, and it caught it again.
**2026-09-17 §68 (UPGRADES §67 for two candidates):** completed the
XAUUSD 2013-2017 M1 backfill (`data/XAUUSD_M1_2013_2017_spot_
dukascopy.csv`, 1.63M rows, real spread) that §67 was missing. Re-ran ORB
gold RETEST and the §52 combined book on the FULL 5-year window instead
of the thin 2017 stub: **ORB gold RETEST now has genuine multi-year
confirmation** (Sharpe +1.457, 5/5 years positive, decisively beats a
NEGATIVE gold buy-and-hold of −0.304 — profits through an actual bear/
chop regime). **The §52 deployable combined book (ORB gold + US30
breakout, rolling risk-parity) is 5/5 years net-positive across the full
out-of-regime window, Sharpe +1.280, maxDD 3.4%** — the strongest
evidence any candidate in this project has produced. This does NOT
rescue the 4 candidates that failed §67 (NAS100 macross, US30 macross,
US30 breakout-vs-B&H, US30 momentum, or the US30 macross+breakout
combined book) — their failures were not data-limited. It meaningfully
upgrades the case for the §52 book specifically, but does not alone
clear every remaining pre-live gate (DSR still not cleared; FTMO 1x pass
rate still 0%; live broker execution still unvalidated).
**2026-09-18 (§69-§71, N=1645→1646):** the MT5 EA (§68's translation)
compiled clean (0 errors/0 warnings) and is now attached and running on
the account-holder's free FTMO MT5 demo — AutoTrading and the ET-
timezone log check both confirmed passing; no live trade has fired yet
(§69/§70). In parallel, CFTC Commitment-of-Traders positioning was
tested on gold as the first genuinely new information category since
on-chain data — the classic hedger-smart-money COT Index hypothesis
(commercial net position at a 3yr-percentile extreme) KILLED decisively
(Sharpe −0.477 vs buy-and-hold +0.578, §71). Does not rule out other COT
framings (speculative extremes, rate-of-change, other instruments) —
those are separate future tests, not a post-hoc flip of this result.
The alpha search continued (§72-§85, closing COT across 3 instruments/
2 framings, then testing VIX/Fed-balance-sheet/Google-Trends): all
killed standalone, but VIX (§79/§83) and real-yield (§75/§82) combined
with each other showed a genuine diversification benefit (§84,
correlation −0.199, combined Sharpe +0.432 beats both legs) — the
sleeve doesn't beat ORB gold RETEST on Sharpe when paired with it
(§85, confirms the project's quality-gap rule), but **§86-§87 found it
produces a new project-best FTMO chained funded probability: 35.7% at
6x risk (was 33.0% at 14x), verified apples-to-apples on the identical
full 2013-2025 window.** This is an FTMO-survival finding specifically
(the headline book still has the better standalone Sharpe, +1.613 vs
+1.182) — same standing caveats apply (one 13-year history, overlapping
challenge windows, DSR never cleared, live execution never validated).
**§88 checked whether the new 6x peak is more era-stable than the old
14x one (as §63's original finding might suggest) — it does NOT
clearly hold; both books show real but different sub-period
variability, and §88 also revises §63's own conclusion, which turns
out to be window-dependent (the headline book's 14x peak is actually
stable across halves on the fuller 2013-2025 span; only §63's shorter
2017-2025 window showed the steep decline).**
**2026-09-18 §89 (SECOND MILESTONE):** adding the VIX/real-yield
sleeve to the FULL §52 book (ORB gold + US30 breakout, not just ORB
gold alone) produces a THIRD project-best: 3-way rolling risk-parity
FTMO chained funded probability of **37.7% at 14x** (vs the 2-leg
headline's 33.1%/14x and the 2-leg new book's 35.7%/6x). Standalone
Sharpe (+1.477) still trails the 2-leg headline book's (+1.613) — an
FTMO-survival improvement specifically, same honest framing as
§86-§88. Checked immediately for era-stability: real but moderate
decline across halves (41.6%→33.8%) and thirds (39.2%→42.3%→31.4%),
with the most recent third still beating the headline book's own T3
(25.5%).
`research_log.md` has the per-test detail.

## Standing Rules (enforced every session, no reminders needed)

1. **File location — never Downloads.** All generated files stay inside this repo
   (`C:\Claude Code\AI Quant Trading\crypto-factor-lab`) in the correct subfolder:
   - Pine scripts → `/strategies_pine`
   - Data (CSV/parquet) → `/data` (raw pulls in `/data/raw`, cleaned in `/data`)
   - Python scripts / downloaders → `/scripts`
   - Research/engine modules → `/research`
   - Docs & notes → `/docs`, `/notes`
   NEVER save to `C:\Users\Harve\Downloads` or any path outside the repo.

2. **Execute fully and self-correct.** Carry tasks to completion. Only stop for a real
   decision a non-coder must make — and when you do, state it in plain English with a
   recommended default they can accept in one word.

3. **Retry before reporting failure.** On failed downloads/commands, retry with more
   attempts, longer timeouts, and smaller chunks before declaring failure. Report
   results and outcomes, not step-by-step narration.

4. **Environment is known — do not re-ask.** Python 3.14.0 is installed and working
   (pandas, numpy, matplotlib). Node/npx available. NEVER use `vectorbt`,
   the QuantConnect API, or `yfinance GC=F` (CME futures — no bid/ask spread). These
   are permanently ruled out.

5. **Real spot data only.** Forex/gold data must be genuine SPOT with a bid/ask spread.
   Always state the timezone. Sanity-check the price range before use
   (XAUUSD spot ≈ $1,200–$3,500+; EURUSD ≈ $1.00–$1.25). Reject futures/CFD proxies
   that lack a real spread.

6. **Cost completeness.** Every backtest includes real spread + commission + slippage
   in the P&L before any metric is reported. FTMO strategies must ALSO simulate the
   full FTMO ruleset: 5% daily drawdown limit, 10% max total drawdown limit, profit
   target, minimum trading days, and the Best Day (consistency) rule.

7. **Honest reporting.** Never inflate results or hide look-ahead / point-in-time bugs.
   Flag incomplete data, contaminated data, or thin trade counts explicitly. Never
   report a Sharpe before costs; never report an optimized result without its plateau;
   always state raw AND deflated Sharpe.

8. **Research log.** Log every strategy/variant tested plus its result in
   `research_log.md` at the repo root. One row per test.

9. **DSR — use `research/dsr.py`, never `metrics.py`'s version.** The one in
   `metrics.py` is broken two ways (annualised numerator over a per-period standard
   error, ~10.8x too small; plus a deflation pool contaminated by structurally
   doomed configs) and returns only 0.0000 or 1.0000. It is kept intact solely so
   historical verdicts are not silently restated. Always STATE the deflation pool.
   Prefer `structural_pool()` (a priori TF x family); `floor_pool()` selects on
   outcome and makes passing easier, so it is a sensitivity check only. Any DSR
   figure in `research_log.md` dated before 2026-07-22 is unreliable.

## Data source notes
- **Gold/forex spot with spread:** Dukascopy via `dukascopy-node` (bid and ask pulled
  separately, then merged to a spread). Timezone = UTC (`-utc 0`). Correct retry flags
  are `-r <n>` / `-rp <ms>` / `-re` / `-fr` (NOT `--retry-count` / `--pause-between-retries`).
- **Crypto:** exchange-native via ccxt (Binance/Bybit reference venues) — OHLCV, funding
  rate, open interest, long/short ratio. Zero data cost. Data venue ≠ execution venue.
- Glassnode only when a free factor set is exhausted.
