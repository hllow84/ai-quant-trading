# MASTER PROMPT — Paste this into Claude Code and let it run

Copy everything below the line and paste it into your Claude Code terminal session.
Claude Code will install everything, write the strategy, run backtests, fix its own
errors, optimise parameters, and produce a final results report. You do not need to
intervene.

---

## PREREQUISITES (do these once before pasting the prompt)
1. Python 3.9+ installed on your machine (check: python --version in terminal)
2. That's it. Claude Code installs everything else.

---

## PASTE THIS INTO CLAUDE CODE:

---

You are an expert quantitative trader and Python developer. Your job is to build,
run, and optimise a complete backtesting system for the ICT Smart Money Concepts
strategy on Gold (XAUUSD) using the H4 timeframe. Work fully autonomously — install
all dependencies, fix all errors yourself, and do not stop until you have produced
a complete results report. Never ask me for help unless you are completely stuck
after 3 self-correction attempts.

## YOUR MISSION

Build a Python backtesting system that:
1. Downloads 7+ years of Gold (GC=F) H4 OHLCV data from Yahoo Finance
2. Implements the full ICT SMC strategy (all components below)
3. Runs a baseline backtest and prints key metrics
4. Runs parameter optimisation across all configurable inputs
5. Saves a final results report as results/ICT_SMC_results.csv
6. Saves an equity curve chart as results/equity_curve.png
7. Prints a clean summary table of the top 10 parameter combinations

Fix all import errors, data errors, and logic errors yourself before asking for help.

## DEPENDENCIES TO INSTALL (pip install these first)

pip install yfinance pandas numpy matplotlib vectorbt ta

## FULL ICT SMC STRATEGY — implement ALL of these components

### 1. HTF BIAS — Daily 50 EMA
- Calculate 50-period EMA on daily close data
- Resample H4 data to daily, compute EMA, merge back to H4
- Bullish bias: H4 close > Daily 50 EMA
- Bearish bias: H4 close < Daily 50 EMA

### 2. MARKET STRUCTURE — Swing highs/lows, BOS, CHoCH
- Pivot high: high is higher than pivot_len bars on each side
- Pivot low: low is lower than pivot_len bars on each side
- Track last confirmed swing high and swing low
- BOS bullish: close crosses above last swing high
- BOS bearish: close crosses below last swing low
- CHoCH bullish: structure was bearish, now bull BOS
- CHoCH bearish: structure was bullish, now bear BOS
- Track market structure state: 1=bullish, -1=bearish

### 3. LIQUIDITY SWEEP
- Bullish sweep: low < last swing low AND close > last swing low (same bar)
- Bearish sweep: high > last swing high AND close < last swing high (same bar)
- After a sweep, start a window of sweep_window bars to find displacement

### 4. DISPLACEMENT — Institutional candle
- Calculate 20-bar rolling average of candle body size (abs(close - open))
- Bullish displacement: close > open AND body > avg_body * disp_mult
- Bearish displacement: close < open AND body > avg_body * disp_mult
- When displacement occurs within sweep_window bars of a sweep, find the OB

### 5. ORDER BLOCKS
- Bullish OB: last bearish candle (close < open) before the bullish displacement
  - OB high = open of that candle (body top)
  - OB low = close of that candle (body bottom)
- Bearish OB: last bullish candle (close > open) before the bearish displacement
  - OB high = close of that candle (body top)
  - OB low = open of that candle (body bottom)
- OB is active until: price closes through the opposite end OR age > ob_max_bars
- Entry: price retraces INTO the OB zone (between OB low and OB high)

### 6. FAIR VALUE GAPS (FVG)
- Bullish FVG: high[i-2] < low[i] — gap between 2-bars-ago high and current low
  - FVG zone: from high[i-2] to low[i]
- Bearish FVG: low[i-2] > high[i] — gap between 2-bars-ago low and current high
  - FVG zone: from high[i] to low[i-2]
- Store last 3 active FVGs of each type
- Entry: price is inside an active FVG zone
- Invalidate: when price fully closes through the FVG

### 7. PREMIUM / DISCOUNT ZONES (additional confluence)
- Find the last major swing range: from last swing low to last swing high
- Equilibrium = midpoint of that range (50% level)
- Discount zone: price below equilibrium — only take LONG entries from here
- Premium zone: price above equilibrium — only take SHORT entries from here
- This prevents buying near resistance and selling near support

### 8. KILL ZONES (UTC time filter)
- London Kill Zone: 07:00–10:00 UTC
- New York Kill Zone: 13:30–16:00 UTC
- Only allow entries during these windows
- H4 bars: check if bar open time falls within either window

### 9. OB + FVG STACKING (highest confluence)
- Preferred entry: when active OB zone overlaps with active FVG zone
- These overlapping zones = Point of Interest (POI)
- Allow single entries (OB only or FVG only) as secondary signals

## ENTRY CONDITIONS

LONG entry (all must be true):
- bullish_bias (close > daily_ema50)
- market_structure == bullish
- active bullish OB exists AND (price in OB OR price in bullish FVG)
- price in discount zone (below swing range midpoint)
- kill zone active
- no open position

SHORT entry (all must be true):
- bearish_bias (close < daily_ema50)
- market_structure == bearish
- active bearish OB exists AND (price in OB OR price in bearish FVG)
- price in premium zone (above swing range midpoint)
- kill zone active
- no open position

## STOP LOSS AND TAKE PROFIT
- Long SL: bull_ob_low - (5 * pip_size)
- Long TP: entry + (entry - SL) * rr_ratio
- Short SL: bear_ob_high + (5 * pip_size)
- Short TP: entry - (SL - entry) * rr_ratio
- pip_size for Gold: 0.01

## POSITION SIZING
- Risk 0.5% of equity per trade
- Lot size = (equity * risk_pct) / (abs(entry - SL) / pip_size)

## PARAMETERS TO OPTIMISE (run all combinations)

pivot_len:    [3, 5, 7]
sweep_window: [3, 5, 7]
disp_mult:    [1.3, 1.5, 1.8]
ob_max_bars:  [30, 50, 80]
rr_ratio:     [1.5, 2.0, 2.5]
use_premium_discount: [True, False]
use_killzone: [True, False]

Total combinations: 3 × 3 × 3 × 3 × 3 × 2 × 2 = 972 combinations
Run ALL 972. Use vectorbt for speed.

## METRICS TO CALCULATE FOR EACH COMBINATION

- Total return %
- Profit factor (gross profit / gross loss)
- Win rate %
- Total trades
- Max drawdown %
- Sharpe ratio
- Average RR achieved
- Calmar ratio (return / max drawdown)

## OUTPUT

1. Print top 10 combinations sorted by profit factor (minimum 30 trades, PF > 1.3)
2. Save full results to results/ICT_SMC_results.csv
3. Plot equity curve of the BEST combination to results/equity_curve.png
4. Print a summary box with the single best parameter set

## ERROR HANDLING RULES

- If yfinance download fails, retry 3 times with 5 second delays
- If vectorbt throws an error, fall back to a manual loop backtest
- If any parameter combination produces divide-by-zero, skip it gracefully
- If data has gaps, forward-fill them (do not drop bars)
- Print progress every 100 combinations so I can see it working
- At the end, always produce output even if some combinations failed

## SELF-CORRECTION RULES

- If you encounter any error, read the full traceback, fix the root cause, and retry
- Do not ask me for help unless you have failed to fix an error 3 times in a row
- After fixing an error, re-run from the point of failure (not from the beginning)
- Log all errors and fixes to results/debug.log

Start now. Install dependencies first, then build and run everything.

---
