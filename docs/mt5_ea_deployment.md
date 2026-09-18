# Deploying the MT5 EA — ORB Gold RETEST + US30 Breakout Combined

Covers `strategies_mt5/ORB_Gold_RETEST_US30_Breakout_Combined.mq5`. Read
`docs/manual_trading_rules.md` first for what this actually does and why
only these two strategies are automated (every other candidate in this
project failed the out-of-regime check — see STATE_OF_PLAY §67/§68).

**Compile status (2026-09-18): PASSED, 0 errors / 0 warnings**, via
MetaEditor64's command-line `/compile` flag against the FTMO Global Markets
MT5 Terminal's own `MQL5/Include` tree (so it compiled against the exact
`Trade.mqh`/`CTrade` headers that terminal ships). The compiled
`ORB_Gold_RETEST_US30_Breakout_Combined.ex5` is committed alongside the
`.mq5` source. This is a syntax/type-check pass only — it confirms the EA
builds cleanly, not that its logic is correct; nothing below about symbol
names, timezone behavior, or live testing is resolved by a clean compile.

## 1. Get the FTMO free demo (no cost, no card)

- Go to FTMO's Free Trial page and choose **MT5** as the platform, any
  account size (this is purely for testing the EA's behavior, not a real
  Challenge attempt).
- You'll get MT5 login credentials for a demo server. Download the
  official **MetaTrader 5** terminal if you don't already have it running
  (separate from your existing FTMO MT4/MT5 installs if those are tied to
  different accounts).

## 2. Compile the EA

**Already done (2026-09-18) against this machine's FTMO MT5 Terminal install
— 0 errors, 0 warnings.** If you're deploying to a DIFFERENT MT5 terminal
(a different broker/VPS), recompile there too, since `.ex5` binaries are
tied to the MetaEditor build that produced them and it's cheap insurance:

1. Copy `strategies_mt5/ORB_Gold_RETEST_US30_Breakout_Combined.mq5` into
   that terminal's `MQL5/Experts/` data folder (MT5 → File → Open Data
   Folder → `MQL5/Experts/`).
2. Open it in MetaEditor (F4 inside MT5, or launch it directly) and press
   **F7** (Compile), or run MetaEditor64.exe with `/compile:"<path to the
   .mq5>" /log:"<path>"` from the command line. Fix any compiler errors
   before proceeding.

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

## 8. v2 — `ORB_Gold_US30_VIX_RealYield_4Leg_Combined.mq5` (written
2026-09-18, adds Legs 3+4)

Covers the newer 4-leg EA, built the same session STATE_OF_PLAY §86-§93
found the 3-way combined book (ORB gold RETEST + US30 breakout +
VIX/real-yield sleeve, rolling risk-parity) produces a new project-best
FTMO chained funded probability (38.3% at 13x, vs the 2-leg book's
33.1% at 14x). **Compiled clean, 0 errors/0 warnings, same machine/
terminal as v1** — but Legs 3/4 and their WebRequest/CSV-parsing
plumbing are BRAND NEW MQL5 code, written and compiled in a single
session under real time pressure, with NO prior live-forward-test
history the way Legs 1/2 already have from v1's demo run. Treat this
as materially higher-risk on first deployment than v1 was.

**What's new:**
- **Leg 3 (VIX spike signal):** long gold when VIX's 120-day z-score
  ≥ +1.25 (flight to safety), short when ≤ −1.25. Fetches CBOE's free
  public VIX history CSV live, once per UTC calendar day.
- **Leg 4 (real-yield trend signal):** long gold when the 10yr TIPS
  real yield (FRED DFII10) has fallen over the last 20 trading days,
  short when it's risen. Fetches FRED's free public CSV, once per UTC
  calendar day.
- Both legs are **continuously-held directional positions with NO
  STOP-LOSS and NO TARGET** — this matches exactly how they were
  backtested (a daily mark-to-market return series, not a stop/target
  trade), but it is a real, stated difference from Legs 1/2 (which DO
  have stops). An uncapped adverse gap on these two legs is possible.
  Watch this closely.
- Sleeve sizing (`InpSleeveWeightPct`, default 10%, split 50/50 across
  Legs 3/4) is a **fixed-weight approximation** of the backtested
  causal rolling risk-parity scheme (not implemented here, same
  category of gap as v1's `RiskParity_TODO()` for Legs 1/2) — chosen
  from §90's in-sample finding that the sleeve's own optimal weight is
  small (~10%), not the full deployable scheme.

**Required one-time setup before attaching v2 (do this BEFORE
attaching, or every fetch will fail silently into the log):**

1. MT5 → **Tools → Options → Expert Advisors** tab.
2. Check **"Allow WebRequest for listed URL"**.
3. Add BOTH of these URLs to the list, exactly:
   - `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`
   - `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10`
4. Click OK. If you skip this, the Experts log will show
   `[SLEEVE] ERROR: WebRequest failed ... error=4060` — that error code
   specifically means "URL not in the allowed list."

**Switching from v1 to v2:** remove the v1 EA from its chart first
(right-click → Expert Advisors → Remove) before attaching v2 — do NOT
run both at once, since v1's Legs 1/2 and v2's Legs 1/2 use the SAME
magic numbers (39100/45100) and would double up orders exactly like
the original double-attachment mistake caught in §69/§70.

**What to watch for, specific to v2:**
- **`[SLEEVE]` log lines** each day: confirm both fetches succeed
  (`recomputed: VIX signal=... real-yield signal=...`), and sanity
  check the printed VIX level / real-yield value against a real
  financial data source occasionally — a parsing bug that silently
  reads garbage would be very hard to notice otherwise.
- **Insufficient-history messages** (`not enough history yet`) are
  expected to disappear immediately — both endpoints return their FULL
  free history (thousands of rows) in one request, so 120/21-day
  windows are satisfied from the very first successful fetch, unlike a
  cold-start signal that would need weeks to warm up.
- **No stop-loss on Legs 3/4** — check equity/margin exposure
  regularly, since neither leg will self-limit a loss the way Legs 1/2
  do.

This EA has NEVER been forward-tested even for one day — everything in
`docs/manual_trading_rules.md` §0's warnings applies at least as
strongly here as it did for v1's first deployment.
