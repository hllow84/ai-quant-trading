# Manual Trading Rules — ORB Gold RETEST + US30 Breakout-Retest

**Status as of 2026-09-17.** This document covers the ONLY two building
blocks in this project that have cleared a genuine multi-year
out-of-regime test (STATE_OF_PLAY §67/§68): **ORB gold RETEST**
(standalone) and the **US30 breakout-retest** leg, combined as the
**§52 book** (rolling risk-parity). Every other candidate found in this
project (NAS100 macross, US30 macross, US30 momentum, and the US30
macross+breakout combined book) **failed** the out-of-regime check and
is deliberately excluded from this document — see "What's NOT here and
why" at the bottom.

**Read the warnings section before trading any of this with real money.**

---

## 0. Before you trade this at all

- This is a **backtested** system. It has never been forward-tested on a
  live feed, paper or otherwise. Real fills, real spread widening around
  news, and your specific broker's execution quality have never been
  checked against the model.
- The 1% risk-per-trade convention below is the project's **backtesting**
  convention, not a recommendation for your real risk tolerance. Decide
  your own real per-trade risk (many traders start materially smaller —
  0.25–0.5% — when moving a backtested system to real money) before
  position-sizing anything.
- The DSR (deflated Sharpe ratio) statistical bar has **not** been
  cleared for any candidate in this project, including these two. The
  case for this specific pair rests on economic evidence (beats its own
  buy-and-hold, holds up out-of-regime, no tail-risk flag) — not on a
  statistically airtight result.
- You need a broker with **real spot gold** (XAUUSD, not a futures
  proxy) and a **US30 CFD**, both with genuine bid/ask spreads you can
  see, to have any chance of matching this backtest's assumptions.

---

## 1. ORB Gold RETEST — the core rules

**Instrument:** XAUUSD (spot gold), mid-price logic, real bid/ask spread
charged as a cost.

**Timeframe:** 1-minute bars, but only during the US cash session.

**Session window (America/New_York time — convert to your own timezone,
respecting US daylight saving):**
- Session open: **09:30 ET**
- Session close (force-flat): **16:00 ET**
- A session is skipped entirely if you don't have at least ~300 of the
  ~390 minutes of that session's data (i.e. don't trade a session that
  opened very late or is otherwise a broken/holiday-shortened day).

### Step 1 — Build the Opening Range (OR)

- Watch the first **30 minutes** after 09:30 ET (i.e. 09:30–10:00 ET).
- OR high = the highest price traded in that window.
- OR low = the lowest price traded in that window.
- OR width = OR high − OR low.
- If that 30-minute window is missing more than ~15% of its data (bad
  feed, gap, etc.), skip the day.
- If OR high == OR low (a dead/degenerate range), skip the day.

### Step 2 — Watch for a breakout, AFTER 10:00 ET only

- From 10:00 ET onward, watch for the first bar whose price trades
  beyond the OR:
  - **Long side armed** if price trades ≥ OR high.
  - **Short side armed** if price trades ≤ OR low.
- Whichever side breaks **first** wins. If a single 1-minute bar
  somehow breaks both sides at once, skip the day entirely (too
  ambiguous to resolve cleanly).
- Only one trade per instrument per day. No re-entry, no reversal.

### Step 3 — Wait for the RETEST (do not enter on the raw break)

This is the key filter — it is what separates this version from a plain
(and much worse) opening-range breakout:

- After the breakout bar, watch every subsequent bar **for the rest of
  that same session**.
- **Long side:** you are looking for some later bar's LOW to come back
  down to within **20% of the OR width** above the OR high
  (i.e. price pulls back to `OR high + 0.20 × OR width` or lower, without
  falling below the OR high itself again in an unfavorable way — see the
  cancellation rule next).
- **Short side:** symmetric — a later bar's HIGH must come back up to
  within 20% of the OR width below the OR low.
- **Cancellation rule:** if, before the retest happens, any bar's
  **close** trades back through the broken level (long: closes back
  below OR high; short: closes back above OR low), the setup is
  **cancelled for the day**. There is no fallback trade — you simply
  don't trade that instrument that day.
- If the session ends (16:00 ET) with no valid retest and no
  cancellation, there is also no trade.

### Step 4 — Entry, stop, and target

- **Entry:** a limit order at the broken OR level itself (OR high for a
  long, OR low for a short) — filled on the retest, not at the breakout
  price.
- **Stop:** a **fixed 25 basis points** (0.25%) of the entry price away
  from entry (NOT the opposite side of the OR — this project tested
  both and the fixed 25bps stop is the one that survived). Long: stop =
  entry × (1 − 0.0025). Short: stop = entry × (1 + 0.0025).
- **1R** = the stop distance (25bps of entry price).
- **Target:** exactly **1R** (i.e. 25bps of entry price in your favor).
  This is a 1:1 reward:risk trade by design — the edge here comes from
  win rate and retest filtering, not from a big reward multiple.
- **Force-flat:** if neither stop nor target is hit by 16:00 ET, close
  the position at the market at the session close. No overnight holds
  on this leg, ever.
- **Same-bar tie rule:** if a single bar's range would hit both your
  stop AND your target, treat it as a **stop** (the conservative
  assumption this project always uses).

### Quick reference table — ORB Gold RETEST

| Parameter | Value |
|---|---|
| Instrument | XAUUSD spot |
| Opening range window | 09:30–10:00 ET (30 min) |
| Entry method | Wait for break, then wait for retest (limit fill at the broken level) |
| Retest tolerance | 20% of OR width |
| Cancel condition | A close back through the broken level before retest |
| Stop | Fixed 25 bps of entry price |
| Target | 1R (= stop distance) |
| Force-flat | 16:00 ET, same day |
| Trades/day | At most 1 |

---

## 2. US30 Breakout-Retest — the second leg

**Instrument:** US30 CFD, mid-price logic, real spread + commission +
slippage charged.

**Timeframe:** 4-hour bars (H4), 24-hour continuous — no session
restriction (unlike the gold leg).

### Step 1 — Track the rolling 20-bar range

- On every completed H4 bar, look at the **prior 20 H4 bars'** high and
  low (i.e. a trailing 20-bar channel, NOT including the current bar).
- Rolling high = max of those 20 bars' highs.
- Rolling low = min of those 20 bars' lows.

### Step 2 — Entry condition (breakout WITH a same-bar retest wick)

- **Long entry:** the current H4 bar's CLOSE is above the rolling high,
  AND that same bar's LOW touched down to (or below) the rolling high
  at some point intrabar — i.e. it broke out and wicked back to "retest"
  the level within the same 4-hour bar, then closed strong.
- **Short entry:** symmetric — close below the rolling low, and that
  bar's high touched up to (or above) the rolling low.
- This only fires on the FIRST bar meeting the condition (rising-edge —
  if the prior bar already qualified, this bar doesn't re-trigger).
- Enter at the close of that H4 bar (market order at/near the H4 close).

### Step 3 — Stop, target, and holding cap

- Compute **ATR(14)** on H4 bars (simple 14-bar average of true range,
  not Wilder-smoothed).
- **Stop:** long = rolling-high level − 4.0 × ATR(14); short = rolling-low
  level + 4.0 × ATR(14). Note the stop is anchored to the BROKEN LEVEL,
  not to the entry price.
- **1R** = distance from entry (H4 close) to that stop.
- **Target:** only **0.25R** — a deliberately small target. (This
  strategy's edge comes from a very high win rate at a small target, not
  a big reward multiple — netPF ≈1.26, win rate ≈72% in-regime.)
- **Max hold:** 20 H4 bars (~3.3 days). If neither stop nor target is
  hit within that window, close at the market at that bar's price.
- **Same-bar tie rule:** stop wins on any bar that could hit both.

### Quick reference table — US30 Breakout-Retest

| Parameter | Value |
|---|---|
| Instrument | US30 CFD |
| Timeframe | H4 (4-hour bars), 24h continuous |
| Lookback | 20 H4 bars (rolling high/low) |
| Entry trigger | Close beyond the 20-bar range AND an intrabar wick back to the level, same bar |
| Stop | Broken level ± 4.0 × ATR(14) |
| Target | 0.25R |
| Max hold | 20 H4 bars (~3.3 days) |
| Trades/day | Not capped — driven by the H4 signal, typically a few per month |

---

## 3. Combining the two into the §52 book

Running both legs together, weighted, is what actually produced the
strongest backtested result (Sharpe +1.793 in-regime, +1.280 confirmed
out-of-regime, both 5/9 and 5/5 years positive respectively). Two ways
to size it, from simplest to most faithful:

### Simple version (good enough to start): fixed 50/50

Split your total risk budget in half between the two legs — e.g. if you
normally risk 1% of account equity per trade on a single strategy, risk
0.5% per gold RETEST trade and 0.5% per US30 breakout trade instead.
This alone captured most of the benefit in testing (Sharpe +1.707–1.408
across the in-regime and out-of-regime windows, vs. +1.793/+1.280 for
the more complex rolling version below).

### Faithful version: rolling risk-parity (what was actually backtested as "deployable")

- Once a month (on the last trading day of the calendar month), look
  back at the **trailing 90 calendar days** of each leg's own daily
  returns and compute each leg's standard deviation (volatility) over
  that window.
- Set next month's weight on gold = `(1/vol_gold) / (1/vol_gold + 1/vol_US30breakout)`.
  US30 gets the rest (`1 − that weight`).
- Use that weight for the ENTIRE following month, then recompute at the
  next month-end. (This is monthly-rebalanced and fully causal — it
  never uses data from after the day it's computed.)
- In backtest this typically lands gold somewhere around 25–40% weight
  and US30 breakout around 60–75%, because gold's per-trade risk (fixed
  25bps stop) is smaller in dollar-volatility terms than US30's ATR-based
  stops once compounded — but let the formula decide each month, don't
  hardcode a fixed split.
- Practically: if this is too much manual bookkeeping, the fixed 50/50
  version above is a reasonable simplification that gave up only a
  modest amount of Sharpe in testing.

---

## 4. What's NOT here, and why

Every other candidate this project found was tested against the SAME
out-of-regime check (2013–2017 real data) that these two passed, and
**failed it**:

| Candidate | Out-of-regime result | Why it's excluded here |
|---|---|---|
| NAS100 H4 macross | Sharpe −0.081 vs its own B&H +1.185 | Loses out-of-regime |
| US30 H4 macross | Sharpe **−1.175**, netPF 0.619 | Real money-loser out-of-regime |
| US30 breakout-retest (standalone, vs its own B&H) | Sharpe +0.377 but loses to B&H's +0.989 | Positive but not an edge over just holding US30 |
| US30 H4 momentum | Sharpe **−0.966**, maxDD 45.9% | Real money-loser, worst of all candidates |
| US30 macross + breakout combined book | Sharpe −0.61 to −0.70, −7.6% to −8.9% total return | Loses real money out-of-regime |
| Credit-spread SPY (options) | Not checked out-of-regime yet (options data doesn't extend back this far in this project) | No out-of-regime evidence either way — not included pending that check |

Do not manually trade any of the excluded strategies based on the
in-regime (2018–2025) numbers alone — that is exactly the failure mode
this project's out-of-regime test exists to catch, and it caught it for
all of these.

Note US30 breakout-retest's OWN standalone number technically still
loses to buy-and-hold out-of-regime — it earns its place here only as
the diversifying second leg of the combined book (where gold carries
the edge and US30 breakout adds a genuinely low-correlation return
stream without dragging the book negative), not as a standalone trade
on its own out-of-regime merits. If you want maximum out-of-regime
rigor, trade ORB gold RETEST alone rather than the combined book.

---

## 5. Practical execution notes

- **Data/charting:** you need 1-minute gold data with a visible bid/ask
  spread for the ORB leg, and H4 (or at least M1/M5 you can resample
  yourself) US30 data for the breakout leg.
- **Timezone discipline:** the gold leg's 09:30/16:00 ET window is the
  single most important detail to get right — a fixed UTC offset will
  silently misplace the opening range across US daylight saving
  transitions. Use a charting platform that lets you anchor sessions to
  America/New_York directly, not a manual UTC conversion.
- **Costs assumed in the backtest** (make sure your real broker isn't
  materially worse than this): gold — real spread + ~$0.03–0.10/oz
  slippage per side + $0.07/oz commission; US30 — real spread + 0.35bps
  commission + 0.15–0.50bps slippage per side. If your broker's spread
  or commission is meaningfully wider than this, the backtested edge
  will shrink or disappear — check before committing size.
- **Journal everything.** Since this has never been forward-tested, the
  single most valuable thing you can do in the first few months is keep
  a clean trade log (entry/exit reason, R-multiple, whether the rule was
  followed exactly) so any live/backtest divergence shows up fast.
