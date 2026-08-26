# Crypto derivatives data availability — PROBED 2026-08-22, not assumed

Method: `scripts/probe_crypto_endpoints.py` (endpoint reachability + field shape)
and `scripts/probe_crypto_depth.py` (bisection to the true earliest bar per
series per symbol). Same discipline as the Dukascopy `probe_earliest.mjs` work:
docs are optimistic, availability is measured per endpoint AND per symbol.

⚠️ Bisection granularity is 3 days, so every "start" below is ±3d. Identical
timestamps across symbols (e.g. three at 2020-10-21 19:13) are the bisection grid,
NOT a real shared listing moment.

## What IS obtainable

| Series | Venue | Endpoint | Earliest (BTC) | Notes |
|---|---|---|---|---|
| Perp OHLCV 1h + **taker-buy volume** + **trade count** | Binance USD-M | `/fapi/v1/klines` | 2019-09-06 | 12-field kline; ccxt DROPS fields 8-10, so hit REST directly |
| **Funding rate** (8h) | Binance USD-M | `/fapi/v1/fundingRate` | 2019-09-09 | full history, no retention limit |
| **Premium index** (perp-vs-index basis) 1h | Binance USD-M | `/fapi/v1/premiumIndexKlines` | 2019-12-23 | continuous basis, not just the 8h stamp |
| **Open interest** 1h | **Bybit v5** | `/v5/market/open-interest` | **2020-08-04** | limit 200 + `nextPageCursor`; deep history |
| **Long/short account ratio** 1h | **Bybit v5** | `/v5/market/account-ratio` | **2020-08-04** | buyRatio/sellRatio |
| Spot OHLCV 1h | Binance spot | `/api/v3/klines` | 2017-08-17 | for spot-perp basis / controls |
| Funding rate | Bybit v5 | `/v5/market/funding/history` | 2021-01 | 2020 returns empty — shallower than Binance |

### Per-symbol starts (±3d)

| Symbol | Bybit OI / LSR | Binance kline | Binance funding | Binance premium |
|---|---|---|---|---|
| BTCUSDT | 2020-08-04 | 2019-09-06 | 2019-09-09 | 2019-12-23 |
| ETHUSDT | 2020-10-21 | 2019-11-26 | 2019-11-26 | 2019-12-23 |
| LINKUSDT | 2020-10-21 | 2020-01-17 | 2020-01-17 | 2020-01-17 |
| LTCUSDT | 2020-10-21 | 2020-01-09 | 2020-01-09 | 2020-01-09 |
| ADAUSDT | 2021-03-16 | 2020-01-30 | 2020-01-19 | 2020-01-30 |
| XRPUSDT | 2021-05-12 | 2020-01-06 | 2020-01-06 | 2020-01-06 |
| DOGEUSDT | 2021-06-03 | 2020-07-11 | 2020-07-08 | 2020-07-11 |
| SOLUSDT | 2021-06-27 | 2020-09-13 | 2020-09-13 | 2020-09-13 |
| BNBUSDT | 2021-06-27 | 2020-02-10 | 2020-02-10 | 2020-02-10 |
| AVAXUSDT | 2021-09-13 | 2020-09-22 | 2020-09-22 | 2020-09-22 |

**Binding constraint: Bybit OI/LSR is the shallowest deep series.** A 10-asset
panel with OI+LSR present for every member starts **2021-09-13** (AVAX). BTC+ETH
alone start 2020-10-21. This is the same shape of problem as GER40's missing ask
in §6 — decide window vs breadth explicitly, do not silently shorten.

## What is NOT obtainable (stated plainly, not worked around)

| Series | Status |
|---|---|
| **Binance open interest history** | **~30 days only.** `startTime` before ~2026-07-25 returns HTTP 400 `-1130 parameter 'startTime' is invalid`. Verified at 2020/2024/2026-07 (all fail) vs 2026-08-01 (OK). Useless for a multi-year study — this is why OI comes from Bybit. |
| **Binance long/short ratios** (global account, top account, top position, taker) | **~30 days only.** Same -1130 wall on all four endpoints. |
| **Liquidations** | **Gone.** `/fapi/v1/allForceOrders` returns HTTP 404 (endpoint retired). No free multi-year liquidation history from either venue. |
| **Order-book snapshots / top-of-book depth** | **Not retrievable historically.** Neither venue serves historical L2. The *closest free proxy with real history* is the kline's taker-buy-vs-total volume split (signed aggressor flow) — that is what will be used, and it is a flow proxy, NOT book imbalance. Do not describe it as order-book imbalance. |

## Consequences for the study
1. OI and positioning skew come from **Bybit**, funding/basis/flow from **Binance**.
   Cross-venue is acceptable (both are top-2 perp venues; the repo's standing rule
   is data venue ≠ execution venue) but must be stated, and each feature labelled
   with its venue.
2. There is **no liquidation feature and no order-book feature.** Two of the five
   requested new inputs do not exist for free at multi-year depth. Reported, not
   substituted-for silently.
3. ccxt cannot be used for the klines: it discards taker-buy volume and trade
   count, which are the only genuine flow fields available. Direct REST required.
