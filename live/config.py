"""
config.py -- all live-trading configuration in one place.

Strategy config here is NOT re-tuned: N=12, K=5, 200-day SMA, monthly rebalance,
base 17-instrument universe is the strongest audited cell from STATE_OF_PLAY.md
sections 12/12.1/12.2/12.3. `research/momentum_rotation.py` is imported, never
re-derived.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIVE_DIR = Path(__file__).resolve().parent
LOGS_DIR = LIVE_DIR / "logs"
STATE_DIR = LIVE_DIR / "state"
LOGS_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

ENV_PATH = LIVE_DIR / ".env"
load_dotenv(ENV_PATH)

import os  # noqa: E402

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")

# ── PAPER-TRADING GATE ──────────────────────────────────────────────────────
# This MUST be manually changed to False to ever place a real-money order.
# Do not flip this via a CLI flag, env var, or config override -- it must be a
# deliberate, reviewed source-code edit, per the standing rule that the paper
# gate is not easy to bypass accidentally.
PAPER_ONLY = True

if not PAPER_ONLY:
    print(
        "\n"
        "############################################################\n"
        "#  WARNING: PAPER_ONLY = False in live/config.py.          #\n"
        "#  This process will place REAL-MONEY orders on a LIVE     #\n"
        "#  Alpaca account if the paper-rebalance-count gate below  #\n"
        "#  is satisfied. This is not a drill.                      #\n"
        "############################################################\n"
    )

# Number of consecutive real monthly rebalances that must be logged on Alpaca
# PAPER before PAPER_ONLY = False is allowed to actually place a live order.
# Enforced in rebalance.py against live/state/state.json's paper_rebalance_count.
REQUIRED_PAPER_MONTHS = 3

# Number of the FIRST rebalances (paper or live) that require a manual keypress
# confirmation after the proposed trade list is printed, before any order is
# placed. Counted from live/state/state.json's total_rebalance_count.
MANUAL_REVIEW_REBALANCES = 3

# ── strategy config -- reused, not re-tuned ─────────────────────────────────
N_MONTHS = 12
TOP_K = 5
SMA_WINDOW = 200
MARKET_FILTER = True
REBALANCE_STEP = 1  # monthly

# ── hard risk limits (code-enforced) ────────────────────────────────────────
POSITION_CAP = 0.25          # no single ETF position > 25% of account value
KILL_SWITCH_DRAWDOWN = 0.15  # halt all new orders if equity falls >15% from peak
WEIGHT_SUM_TOLERANCE = 0.01  # target weights must sum to 1.0 +/- this, no negatives

# ── data pull ────────────────────────────────────────────────────────────
# yfinance, same source/method as research/momentum_rotation.py's audited data
# (scripts/download_momentum_universe.py) -- NOT Alpaca market data -- so the
# live signal is computed on the exact same data source the backtest was
# validated against. Alpaca is used for account state and order execution only.
SIGNAL_LOOKBACK_DAYS = 760  # >2 years: covers 200d SMA + 12mo lookback with margin

# ── monitoring ───────────────────────────────────────────────────────────
BACKTEST_SHARPE_LOW = 0.51    # audited DSR-pool Sharpe range, STATE_OF_PLAY.md sec 12.1
BACKTEST_SHARPE_HIGH = 0.64
# Wide tolerance band around the backtest range before even a soft warning
# fires -- deliberately generous (roughly the full audited perturbation
# neighborhood from sec 12.3 audit 8, 0.52-0.64, widened further) so normal
# month-to-month noise in a live monthly-rebalance series doesn't cry wolf.
MONITOR_SHARPE_WIDE_LOW = 0.0
MONITOR_SHARPE_WIDE_HIGH = 1.5
MONITOR_MIN_MONTHS_FOR_SHARPE = 3       # fewer than this, don't report a Sharpe at all
MONITOR_MIN_MONTHS_FOR_FULL_COMPARE = 12  # fewer than this, label vs-backtest comparison "PARTIAL"
STOP_RULE_UNDERPERFORM_SPY_CAGR_PP = 10.0  # percentage points
STOP_RULE_CONSECUTIVE_RUNS = 2
