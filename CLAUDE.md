# CLAUDE.md — AI Quant Trading Lab (repo root)

Read this at the start of every session in this repo. These are standing rules that
apply without reminders. The parent folder `C:\Claude Code\AI Quant Trading\CLAUDE.md`
holds the longer crypto-factor-research context; this file is the enforced rulebook for
ALL work in `crypto-factor-lab` (crypto factors AND forex/gold FTMO strategies).

## START HERE
**Read `STATE_OF_PLAY.md` (repo root) before doing anything else.** It is the
standalone briefing: what has been settled (the FTMO hunt is concluded — no viable
edge across 345 trials, with the structural reason), the one live lead (diversified
index trend-following on the macross family), the DSR gate repair, the open next
steps, and a full data/code inventory. `research_log.md` has the per-test detail.

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
