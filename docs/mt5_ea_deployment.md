# Deploying the MT5 EA — ORB Gold RETEST + US30 Breakout Combined

Covers `strategies_mt5/ORB_Gold_RETEST_US30_Breakout_Combined.mq5`, written
2026-09-17, **not yet compiled or tested**. Read `docs/manual_trading_rules.md`
first for what this actually does and why only these two strategies are
automated (every other candidate in this project failed the out-of-regime
check — see STATE_OF_PLAY §67/§68).

## 1. Get the FTMO free demo (no cost, no card)

- Go to FTMO's Free Trial page and choose **MT5** as the platform, any
  account size (this is purely for testing the EA's behavior, not a real
  Challenge attempt).
- You'll get MT5 login credentials for a demo server. Download the
  official **MetaTrader 5** terminal if you don't already have it running
  (separate from your existing FTMO MT4/MT5 installs if those are tied to
  different accounts).

## 2. Compile the EA

1. Open MetaEditor (F4 inside MT5, or launch it directly).
2. File → Open → navigate to
   `strategies_mt5/ORB_Gold_RETEST_US30_Breakout_Combined.mq5`
   (copy it into your MT5 `MQL5/Experts/` data folder first — MT5 → File →
   Open Data Folder → `MQL5/Experts/`).
3. Press **F7** (Compile). Fix any compiler errors before proceeding — this
   has not been compiled yet in this session, so treat the first compile as
   a real checkpoint, not a formality.

## 3. Find your broker's EXACT symbol names

Every broker names gold and the Dow index CFD slightly differently. Before
running the EA:

1. In MT5, open **Market Watch** (Ctrl+M).
2. Right-click → **Symbols** → search for "gold" and "dow"/"30"/"US30".
3. Note the EXACT strings (e.g. `XAUUSD`, `XAUUSD.raw`, `US30.cash`, `US30`,
   `DJ30`, `DJI30` — all seen across different brokers/servers).
4. Set `InpGoldSymbol` and `InpUS30Symbol` in the EA's input parameters to
   match EXACTLY. If they're wrong, `OnInit()` will fail with an explicit
   error naming which one didn't resolve — it will not fail silently.

## 4. Attach and configure

1. Drag the compiled EA from the Navigator panel onto ANY chart (the chart
   symbol/timeframe you attach it to doesn't matter — the EA references
   both symbols directly via `InpGoldSymbol`/`InpUS30Symbol`, independent
   of the chart it's running on).
2. In the EA's **Common** tab, check "Allow Algo Trading".
3. In MT5's toolbar, make sure **AutoTrading** (the button, or Ctrl+E) is
   enabled globally.
4. Tools → Options → **Expert Advisors** tab: enable "Allow WebRequest" is
   NOT needed (the news filter uses MT5's built-in Calendar API, not
   WebRequest) — but do check that "Allow DLL imports" etc. are left at
   their defaults; nothing here needs them.
5. Review every input in the EA's dialog before clicking OK — especially
   `InpGoldSymbol`/`InpUS30Symbol` (step 3) and the risk percentages
   (`InpGoldRiskPct`/`InpUS30RiskPct`, default 0.5/0.5 = the "simple
   50/50" split from `docs/manual_trading_rules.md`).

## 5. What to actually watch for during the demo period

- **Timezone correctness (the single most important thing to verify).**
  Cross-check the EA's own log output ("[GOLD] OR built: ...") against
  the actual 09:30–10:00 ET clock time on a reliable source (e.g. a world
  clock). The EA computes this from `TimeGMT()` (true UTC, derived from
  your Windows/VPS OS timezone settings) plus a hardcoded US DST
  calculation — it does NOT trust the broker server's own clock/DST
  behavior. **If your trading PC/VPS's Windows timezone is not set
  correctly, this whole leg will silently misfire.** Verify the VPS/PC
  clock against real UTC before trusting anything else.
- **Symbol resolution.** Confirm `OnInit()` printed "initialised" with no
  errors in the Experts log tab.
- **Trade log messages.** Every entry, cancellation, and force-flat is
  logged with the `[GOLD]`/`[US30]` prefix (toggle via `InpVerboseLog`) —
  read these daily for the first few weeks and compare against what you'd
  expect from `docs/manual_trading_rules.md`'s rules by eye.
- **News filter.** If `InpUseNewsFilter` is on and MT5's Calendar isn't
  populated (some demo servers sync it more slowly than live), entries
  could be silently skipped — check the Experts log for "within FTMO news
  blackout window" messages; if you never see real trades at all, verify
  Calendar data is present (Toolbox → Calendar tab should show upcoming
  events).

## 6. Known simplifications vs. the Python backtest — read before trusting live results

- **Sizing is fixed 50/50, not the rolling risk-parity scheme** that
  produced the project's best backtested number (§52). This EA
  implements the "simple version" from `docs/manual_trading_rules.md`
  §3 only. The monthly rebalance logic is a real, scoped follow-up, not
  yet built (see `RiskParity_TODO()` in the EA source).
- **Gold retest entries are simulated as immediate market orders** once
  the retest condition is detected on a timer tick (every
  `InpTimerSeconds`, default 20s), not a resting limit order at the exact
  broken level. In fast markets this could realize a slightly worse fill
  than the backtest's idealized limit-fill assumption.
- **US30 entries happen shortly after the H4 bar closes** (on the next
  timer tick), not exactly at the close print — a small, usually
  immaterial timing gap given 4-hour bars.
- Neither of these should change the STRATEGY's identity, but both are
  real, stated reasons live results could differ modestly from the
  backtest — exactly why the free demo period exists before any real
  money is involved.

## 7. Before moving past the free demo

Do not treat "the EA ran without crashing" as sufficient. Before
considering a paid FTMO Challenge:

- Let it run through at least a handful of full ORB sessions and a few H4
  breakout signals on both legs.
- Compare realized entries/stops/targets against what you'd have expected
  reading `docs/manual_trading_rules.md`'s rules by hand for the same
  days.
- Re-read `docs/manual_trading_rules.md` §0's pre-trade warnings — none of
  them are resolved just because the EA compiles and runs.
