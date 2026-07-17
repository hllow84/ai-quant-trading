# MA-CCI Swing Strategy — Backtest Specification (v1)

> Purpose: a precise, machine-readable version of the **Option A (MA-CCI swing)**
> system plus the **Phase 4 risk/sizing/exit** rules, ready to hand to Claude Code
> and a backtesting harness.
>
> Items marked **[DEFAULT]** are choices the source strategy left undefined. They
> are sensible starting values — change any of them and re-test. This is a research
> spec, not financial advice.

---

## 0. Important scope note

- **Option B (TradersGPS) is deliberately excluded.** Its core indicators
  (Cumulation of Momentum, Trend Impulse Factor, the signal arrows) are proprietary
  to a paid product and their formulas are not public, so they cannot be reproduced
  or honestly backtested. Do not approximate them and call the result "TradersGPS."
- This spec is **long-side complete**; short rules are the exact mirror and are
  listed in §3.3.

---

## 1. Instrument, timeframe, costs

- **Market:** US equities (rules apply equally to SGX).
- **Bar size:** Daily. (Swing system, 2–5 day holds.)
- **Core test instrument:** ONE liquid US stock (e.g., AAPL). **Benchmark:** SPY.
- **Tick size:** $0.01 for US stocks priced ≥ $1.00. "1 bid" in the source = 1 tick.
  Read the real tick from the data feed where possible rather than hardcoding.
- **Costs to model (never assume free/perfect fills):**
  - Commission **[DEFAULT 0.05% per side]** (approximates IBKR retail).
  - Slippage **[DEFAULT 1 tick]** on stop entries and exits.

---

## 2. Indicators

| Name | Definition | Default |
|---|---|---|
| MA20 | Simple moving average of close, 20 bars | SMA **[DEFAULT]** (EMA optional) |
| MA40 | Simple moving average of close, 40 bars | SMA **[DEFAULT]** |
| CCI | Commodity Channel Index | period **20 [DEFAULT]** (14 is a common alt) |
| Slope lookback | bars used to judge MA direction | **3 bars [DEFAULT]** |

"Sloping upward" is defined precisely as: `MA[today] > MA[3 bars ago]`.
"Sloping downward": `MA[today] < MA[3 bars ago]`.

---

## 3. Entry / exit engine (Phase 3, Option A)

### 3.1 Long setup — ALL conditions true on the same "signal bar"
1. **Trend stack:** `MA20 > MA40`
2. **Both rising:** `MA20[0] > MA20[-3]` AND `MA40[0] > MA40[-3]`
3. **Pullback momentum:** `CCI < -100`
4. **Pullback depth:** bar `low <= MA20` (the low touched or pierced the 20MA)
5. **Held the trend:** bar `close > MA40`

A bar meeting all five is a **qualified long signal**.

### 3.2 Long entry trigger (the bar AFTER a qualified signal)
- Working order: **buy stop at `prior day high + 1 tick`**.
- Trailing behaviour: if unfilled and a new qualified signal forms, move the buy
  stop to the *new* prior-day-high + 1 tick.
- **Order lifetime [DEFAULT]:** keep the buy stop working while the trend condition
  (`MA20 > MA40`) holds; **cancel** the pending order if that breaks before a fill.
- Fill price = stop level + slippage.

### 3.3 Short setup (mirror) and trigger
1. `MA20 < MA40`
2. `MA20[0] < MA20[-3]` AND `MA40[0] < MA40[-3]`
3. `CCI > +100`
4. bar `high >= MA20`
5. bar `close < MA40`
- Trigger: **sell-short stop at `prior day low − 1 tick`**, same trailing/lifetime logic.

---

## 4. Risk, sizing, and exits (Phase 4)

### 4.1 Position sizing (risk-based)
```
risk_per_share = Entry − InitialStop        (for longs; reverse for shorts)
S = floor( (Portfolio × MaxRisk%) / risk_per_share )
```
- **MaxRisk% [DEFAULT 1%]** of portfolio equity per trade.
- Cap position at **[DEFAULT 20%]** of portfolio value and at available cash.
- (Source wrote `Entry − Exit`; "Exit" here = the initial stop price.)

### 4.2 Tiered scale-in — **OPTIONAL LAYER, leave OFF for the first tests**
- Tranche 1 = **50%** of `S` on the first trigger.
- Tranche 2 = **+30%** on the next qualified trigger while the position is open and
  `price > average entry`.
- Tranche 3 = **+20%** on the following qualified trigger, same condition.
- If no further qualified triggers occur, remain at current size.
- *Test the engine with a single full-size entry first; add scaling only once the
  core is shown to work, so you can measure what scaling actually changes.*

### 4.3 Stops & exits (longs; mirror for shorts). Whichever fires first wins.
1. **Initial stop:** `prior day low − 1 tick` at time of entry. **[DEFAULT]**
   (Source alt: "most recent swing low" — needs its own definition if used.)
2. **Breakeven stop:** once `price ≥ Entry × 1.05` (a >5% move), raise stop to `Entry`.
3. **Trailing stop:** each day set stop to `prior day low − 1 tick`, but **only ever
   ratchet in the favorable direction** (never loosen a stop).
4. **Time stop ("fire the stock"):** if still open at the close of **Day 5** of the
   holding period, exit at the **next open**.

### 4.4 Profit target
- **The source does not define a numeric target**, yet the time stop references a
  "profit objective." **[DEFAULT: no fixed target]** — exits are governed entirely by
  the stops in §4.3. Optional configurable target: e.g., take profit at **2R**
  (twice the initial risk-per-share). Test both.

---

## 5. Context layers (Phases 1–2) — add ONLY after the core works

> These need multi-asset data and a stock universe. Keep them **OFF** for the
> single-instrument core test, then add one at a time.

### 5.1 Market regime gate (Phase 1)
- Index basket **[DEFAULT]:** S&P 500, Nasdaq 100, Dow, FTSE 100, DAX, Nikkei 225,
  Hang Seng, STI.
- "Green" = index `close > previous close` that day.
- `bullish` if > 50% green → **longs enabled, shorts disabled**; `bearish` if < 50%
  → shorts enabled, longs disabled.

### 5.2 Universe filter (Phase 2)
- Last price `> $0.50`.
- 20-day average daily volume `> 500,000` shares.

### 5.3 Relative strength (Phase 1.3)
- `RS = stock_return(20d) − benchmark_return(20d)`. **[DEFAULT lookback 20 bars]**
- Longs require `RS > 0`; rank candidates by `RS` descending and trade the top
  **[DEFAULT N = 5]**.
- ⚠️ A universe backtest **must** use survivorship-bias-aware data (include delisted
  names) or results will be falsely flattering.

---

## 6. What the harness must report after every backtest
- Net return **vs simple buy-and-hold** over the same window (always side by side).
- **In-sample vs out-of-sample** results (develop on IS, confirm on OOS once).
- Max drawdown, Sharpe (or similar), win rate, number of trades, average days held,
  total commission + slippage paid.
- **Overfit flags:** too few trades, suspiciously high return, or a large gap
  between in-sample and out-of-sample performance.

---

## 7. Recommended build & test order
1. **Core:** long-only §3.1–3.2 + §4.1 (single full entry) + §4.3 stops, one stock, daily.
2. Add **shorts** (§3.3) and the **regime gate** (§5.1).
3. Add **universe screen + relative strength** (§5.2–5.3) — needs good data.
4. Add **tiered scale-in** (§4.2).
5. Re-run out-of-sample after each layer; keep only what genuinely helps.

---

## 8. Decisions you may want to revisit (all flagged [DEFAULT] above)
- CCI period (20 vs 14); SMA vs EMA for the moving averages.
- Slope definition (3-bar lookback).
- Profit target (none vs 2R).
- Initial stop basis (prior-day low vs swing low).
- Per-trade risk % (1%) and max position size (20%).
- Index basket and RS lookback/top-N.
