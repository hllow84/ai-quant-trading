# Papers With Backtest — new-category candidate sourcing (2026-09-14)

## Access method
Direct HTTPS/browser access to github.com was not used; instead the `gh` CLI (authenticated
GitHub API) pulled the org repo list and file contents directly — this worked cleanly, no
rate-limiting or structure problems encountered.

- Org: `paperswithbacktest` — repos of interest: `awesome-systematic-trading` (curated list +
  auto-generated replication table) and `pwb-toolbox` (data/backtesting toolbox, no strategy
  implementations currently).
- Catalogue README (`awesome-systematic-trading/README.md`) has a **generated** Strategies
  table: "Showing the 61 strongest of 1,687 replications that clear a t-statistic of 1.96 over
  at least 10 years, up to 12 per asset class." Sharpe is gross of costs, measured on each
  strategy's own active window (not a common calendar).
- The full 1,687-row catalogue lives in a Hugging Face dataset (`Strategies-NAV`) gated behind
  `HF_ACCESS_TOKEN` (set via `scripts/build_strategies_table.py`) — **not accessible here**, no
  token available. Everything below is sourced from the public top-61 table only, which is a
  legitimate (if partial) view: it's already the highest-t-stat subset.
- Cross-checked candidate data requirements against actual QuantConnect strategy source in
  `awesome-systematic-trading/static/strategies/*.py` (an older, hand-curated set of ~120
  Quantpedia-sourced implementations, not 1:1 with the new top-61 table but useful for seeing
  exactly what raw data a given strategy family needs).

## Ranked shortlist

| # | Strategy | Category | Published OOS evidence | Data needed | Status |
|---|---|---|---|---|---|
| 1 | [Good Carry, Bad Carry](https://paperswithbacktest.com/strategies/good-carry-bad-carry) | Currencies — rate-differential carry | Sharpe 1.74, t-stat 10.6, vol 4.6%, 37 years | Short-term interbank/policy rate per currency (for the long/short rate-differential ranking) + spot FX for the traded legs | **Buildable now** — spot FX via existing Dukascopy pipeline (already in repo, real bid/ask). Rate differentials: the `static/strategies/fx-carry-trade.py` Quantpedia reference implementation sources these from Quandl/OECD `KEI_IR3TIB01` short-term interbank rate series (monthly) — that specific OECD series is public and free via the OECD data API (no key), or equivalently FRED has comparable short-term rate series for major economies (free, needs a free API key). Neither is currently pulled in this repo — would be a new but zero-cost data source, not a paid blocker. |
| 2 | [Currency Value Factor (PPP strategy)](https://paperswithbacktest.com/strategies/) *(static-strategies reference, not in the top-61 table but same currency-factor family as #1)* | Currencies — PPP/value | Quantpedia reference strategy (not independently in the 61-row t-stat table, flagged as a buildable adjacent candidate) | CPI / PPP index per currency + spot FX | **ATTEMPTED 2026-09-15, BLOCKED — real data wall, not just low priority.** Live-probed FRED/OECD CPI series directly (same fredgraph.csv method that worked cleanly for #1's interbank rates): no single working ID pattern generalizes across countries, the patterns that did work for several countries (US/JP/GB/CH/CA/NO `IXNBM`) are discontinued 2021-2023 (too stale for a 2025-window backtest), and Australia/New Zealand publish CPI quarterly not monthly (a genuine frequency mismatch, not a naming issue). Would need per-country manual series verification against national statistics agencies, not a single bulk free endpoint. See research_log.md 2026-09-15 row for the full probe detail. Revisit with more time budget or a paid macro data source (e.g. a proper OECD.Stat SDMX pull with correct dataflow IDs, not fredgraph.csv guessing). |
| 3 | [Lessons from the Evolution of Foreign Exchange Trading Strategies](https://paperswithbacktest.com/strategies/lessons-from-the-evolution-of-foreign-exchange-trading-strategies) | Currencies — multi-factor FX (carry/momentum/value survey-style) | Sharpe 1.24, t-stat 7.4, vol 12.4%, 36 years | Not independently verified here (no QC reference implementation found in `static/strategies`); title indicates a combination/evolution of carry, momentum and value FX signals, so likely the same short-rate + CPI + spot-FX inputs as #1/#2 | **Likely buildable, unconfirmed** — flagging rather than committing; would need to actually pull the paper to confirm exact signal construction before build. Distinct from anything tested here (project's only FX work to date is Dukascopy-based ORB/ICT-SMC price-action, not carry/value). |
| 4 | [A Study Of Differences In Returns Between Large And Small Companies In Europe](https://paperswithbacktest.com/strategies/a-study-of-differences-in-returns-between-large-and-small-companies-in-europe) (and the cluster of adjacent Equities-table entries: "The Role of Beta and Size...", "Value and Size Effect: Now You See It, Now You Don't", "Fact, Fiction, and the Size Effect") | Equities — cross-sectional size/value factor | Sharpe 1.89 / 1.63 / 1.52 / 1.33, t-stats 11.4 / 9.6 / 9.3 / 8.1, 34–37 years | Point-in-time market cap + book-to-market (or CPI-deflated size decile assignment) across a broad, survivorship-bias-free European or US equity universe going back 30+ years, rebalanced periodically | **Blocked** — the QC reference implementation for this family (`small-capitalization-stocks-premium-anomaly.py`) leans on QuantConnect's built-in point-in-time fundamentals universe (`HasFundamentalData`, `MarketCap` across thousands of NYSE/AMEX/NASDAQ names since 2000). This repo has no equivalent: yfinance exposes only *current* fundamentals (no point-in-time history, and survivorship bias if the universe is built from today's index members). Genuine size/value replication needs CRSP/Compustat-grade point-in-time data, which this repo explicitly does not have access to. |
| 5 | [Media Tone Goes Viral: Global Evidence from the Currency Market](https://paperswithbacktest.com/strategies/media-tone-goes-viral-global-evidence-from-the-currency-market) | Derivatives/FX — non-price (media sentiment) | Sharpe 1.06, t-stat 6.5, vol 1.3%, 38 years | Historical news/media tone sentiment feed per currency, tied to timestamped articles | **Blocked** — no free equivalent exists at the needed historical depth (this class of data is typically RavenPack or similar paid textual-sentiment vendors). Flagged only because it's a genuinely novel non-price data source distinct from everything else in this table. |

## Recommendation
Build **#1 (Good Carry, Bad Carry)** first: it has the strongest published OOS evidence in the
list, is a genuinely new strategy family for this project (rate-differential carry, not price
momentum/breakout), and every input is free and already half-built (Dukascopy spot FX is in
place; only a new OECD/FRED short-rate puller is needed). #2 is a near-zero-marginal-cost
follow-on once #1's pipeline exists. #3 needs the source paper read before committing. #4 and #5
are documented here as explicitly blocked so they aren't re-proposed later without new data
access.
