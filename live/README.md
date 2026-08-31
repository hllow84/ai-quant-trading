# Live (paper-first) infrastructure — cross-sectional momentum rotation

Deploys the audited strategy from `STATE_OF_PLAY.md` sections 12/12.1/12.2/12.3
exactly as tested: **N=12 month lookback, top K=5, 200-day SMA market filter,
monthly rebalance, base 17-ETF universe** (11 SPDR sectors + 6 asset-class
ETFs). This is the strongest audited cell. Nothing here re-derives or re-tunes
the strategy — `research/momentum_rotation.py::build_weights()` is imported
and called unchanged; see `live/signals.py`'s module docstring for exactly how
today's live signal is extracted from it without modifying that file.

**Current status: paper trading only.** `live/config.py`'s `PAPER_ONLY = True`
must be manually edited to ever place a real-money order, and even then a
hard-coded gate refuses to trade live until 3 real paper months are logged
(see "The paper-trading gate" below).

## 1. Setup

### 1a. Alpaca account
1. Create a free account at https://alpaca.markets.
2. Open the **Paper Trading** dashboard (https://app.alpaca.markets/paper/dashboard/overview)
   — this is a real paper account against Alpaca's live API, not a separate simulator.
3. Generate a paper API key/secret pair from that dashboard.

### 1b. Python dependencies
Installed already in this environment: `alpaca-py`, `python-dotenv`, `yfinance`,
`pandas`, `numpy`. If setting up fresh:
```
pip install alpaca-py python-dotenv yfinance pandas numpy
```

### 1c. API keys
```
copy live\.env.example live\.env
```
Edit `live/.env` and fill in `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` with the
**paper** keys from step 1a. `live/.env` is git-ignored (`.gitignore` has
`live/.env` and a blanket `.env` rule) — verified never to be committed.

### 1d. Smoke test
```
python live\rebalance.py --dry-run --force
```
`--force` bypasses the last-trading-day-of-month gate so you can test on any
day; `--dry-run` computes and prints everything (signal, target weights,
position-cap adjustment, proposed trades) but places no orders and does not
touch `live/state/state.json`. Confirm it prints a plausible 5-ETF basket (or
100% IEF if SPY is below its 200-day SMA) before doing anything else.

## 2. What each file does

| file | role |
|---|---|
| `config.py` | all tunables in one place: strategy config (reused, not re-tuned), risk limits, gates. `PAPER_ONLY` lives here. |
| `broker.py` | Alpaca `TradingClient` wrapper — account state, positions, trading calendar, order placement. Price data for the *signal* comes from yfinance, not Alpaca, so the live signal matches the audited backtest's data source. |
| `signals.py` | pulls the 17-ETF+SPY panel via yfinance and calls `research/momentum_rotation.py::build_weights()` unchanged to compute today's target weights. |
| `risk.py` | hard risk checks: weight-sum/negative-weight sanity check, 25% position cap, kill-switch drawdown check. |
| `state.py` | tiny local JSON state file (`live/state/state.json`, git-ignored): peak equity, kill-switch status, paper/total rebalance counters. |
| `logging_utils.py` | append-only CSV logs: `live/logs/orders_log.csv` (every order) and `live/logs/equity_log.csv` (every run's account snapshot). |
| `rebalance.py` | the main monthly pipeline — run this. |
| `monitor.py` | decay detection — run monthly after `rebalance.py`. |
| `run_rebalance.bat` | Task Scheduler entry point. |

## 3. The hard risk limits (code-enforced, in `risk.py`)

1. **Position cap — 25% of account value per ETF, always.** The audited
   strategy's defensive leg is a 100% allocation to IEF when SPY is below its
   200-day SMA. This cap **overrides that by design**, per the task's explicit
   instruction ("even if the model calls for more"): a risk-off signal will
   hold ~25% IEF / ~75% cash live, not 100% IEF as backtested. This is a
   real, deliberate departure from the audited allocation — stated here so
   it isn't rediscovered as a surprise later, and accounted for in
   `monitor.py`'s comparison.
2. **Kill switch — halt on >15% drawdown from peak equity.** Checked every
   run, before signal generation. Once tripped it stays tripped
   (`kill_switch_active: true` in `state.json`) across every subsequent run
   until a human clears it by hand after reviewing why it fired. No new
   orders are placed while active.
3. **Signal sanity check — refuse to trade on a malformed signal.** If
   target weights don't sum to 1.0 ± 1%, or contain a negative, the run
   raises and halts before any order is computed or placed.

## 4. The paper-trading gate

`config.PAPER_ONLY = True` is the default and must be **manually edited** to
`False` to ever place a real order — never toggled by a flag, env var, or
config override. Even with `PAPER_ONLY = False`:
- The pipeline refuses to trade live until `state.json`'s
  `paper_rebalance_count` ≥ `REQUIRED_PAPER_MONTHS` (3).
- A live run additionally requires typing the exact phrase
  `I UNDERSTAND THIS IS REAL MONEY` at an interactive prompt — a scheduled
  (non-interactive) run cannot satisfy this and will refuse automatically.

**What "3 successful paper months" means before considering real capital:**
at least 3 real monthly rebalances logged on Alpaca PAPER
(`paper_rebalance_count` in `state.json` incremented by an actual completed
`rebalance.py` run, not a `--dry-run`), with no unresolved kill-switch trip
and no unexplained order failures in `live/logs/orders_log.csv`. This is a
floor, not a green light — also review `monitor.py`'s output before flipping
`PAPER_ONLY`.

## 5. Manual review for the first few rebalances

The first `MANUAL_REVIEW_REBALANCES` (3) rebalances — paper or live, counted
by `state.json`'s `total_rebalance_count` — print the full proposed trade
list and require typing `YES` at an interactive prompt before any order is
placed. A scheduled (non-interactive) run during this window refuses
automatically rather than hanging on stdin — **run `rebalance.py` by hand for
the first 3 months**, then let the scheduler take over.

## 6. Scheduling (Windows Task Scheduler)

`rebalance.py` is safe to run daily — it's a no-op on every day that isn't
the actual last NYSE trading day of the month (checked via Alpaca's own
trading calendar, so holidays are handled correctly).

1. Open Task Scheduler → **Create Task…**
2. General tab: name it `momentum-rotation-rebalance`; "Run whether user is
   logged on or not" if you want it to fire unattended.
3. Triggers tab → New: Daily, recurring, start date any day, **repeat** not
   needed — instead set it to trigger daily and rely on the script's own
   month-end check. (Simplest: trigger daily; the script is a no-op except
   on the real last trading day.)
4. Actions tab → New → Program/script:
   `C:\Claude Code\AI Quant Trading\crypto-factor-lab\live\run_rebalance.bat`
5. Conditions/Settings tabs: defaults are fine.
6. Save. Output/errors land in `live/logs/scheduler_run.log`.

**Do not enable this until past the manual-review window (section 5)** — a
scheduled run during that window will safely refuse rather than hang, but it
won't place the trade either, so you'd be relying on remembering to run it by
hand anyway for the first 3 months. Set the scheduled task up once you're
past that gate.

## 7. Monitoring / decay detection

Run monthly, any time after `rebalance.py`:
```
python live\monitor.py
```
Builds a monthly live-return series from `live/logs/equity_log.csv`, computes
trailing Sharpe/CAGR, and compares against:
- the audited backtest's expected Sharpe range (0.51–0.64, sec 12.1), with a
  wide soft-tolerance band (0.0–1.5) before even a warning fires — a single
  noisy month in a monthly-rebalance series shouldn't trigger alarm;
- SPY buy-and-hold CAGR over the identical live window (pulled fresh).

**Stop-live rule, stated plainly:** stop trading this strategy live if, for
2 consecutive monthly monitor runs, trailing-12-month live Sharpe is negative
**and** trailing-12-month live CAGR underperforms SPY by more than 10
percentage points. That combination means live behavior no longer resembles
any audited perturbation variant (all of which stayed solidly positive-Sharpe
and beat SPY risk-adjusted — sec 12.1/12.3). The kill switch (section 3) is a
separate, harder, automatic halt on drawdown alone and doesn't wait for this
monthly check.

## 8. Known, stated limitations

- The 25% position cap changes the defensive leg's live behavior vs. the
  backtest (section 3.1) — expect live risk-off periods to look different
  from the backtested 100%-IEF allocation.
- `monitor.py`'s Sharpe is computed on monthly snapshots taken at rebalance
  time, not daily NAV — consistent with the strategy's own monthly cadence,
  but noisier than a daily-return Sharpe until enough months accumulate.
- Alpaca fractional/notional market orders are logged with `status` at
  submission time (e.g. `accepted`), not confirmed fill price/quantity —
  `orders_log.csv`'s `price_at_order` is the prior day's reference close from
  the signal panel, not the actual fill price. Reconcile against Alpaca's own
  order history for exact fills if needed.
