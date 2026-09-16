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
§59-§61's superseded numbers. `research_log.md` has the per-test detail.

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
