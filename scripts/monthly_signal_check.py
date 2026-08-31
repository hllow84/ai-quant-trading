#!/usr/bin/env python3
"""
monthly_signal_check.py -- MANUAL MONITOR. Prints this month's target basket
for the audited cross-sectional momentum rotation strategy (N=12, K=5,
200-day SMA market filter, monthly rebalance, base 17-ETF universe --
STATE_OF_PLAY.md sections 12/12.1-12.4).

Reuses live/signals.py::generate_signal() UNCHANGED, which itself calls
research/momentum_rotation.py::build_weights() UNCHANGED -- nothing in this
script re-derives or re-tunes the signal. The only new logic here is the
last-trading-day-of-month gate (via pandas_market_calendars' NYSE calendar,
not Alpaca's, since this script has no broker dependency) and the
plain-English report / month-over-month log.

*** INFORMATIONAL ONLY. This script places NO orders and connects to NO
*** broker. You place trades yourself, manually, in whatever brokerage
*** account you actually use -- this just tells you what the audited signal
*** says to hold this month.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from live.signals import generate_signal  # reused unchanged, not reimplemented

LOG_DIR = REPO / "scripts" / "logs"
LOG_FILE = LOG_DIR / "monthly_picks.csv"
LOG_FIELDS = ["date", "risk_off", "tickers", "signal_source"]


def is_last_trading_day_of_month(as_of: dt.date | None = None) -> bool:
    """
    NYSE trading-calendar check, same intent as live/broker.py's
    is_last_trading_day_of_month() (which uses Alpaca's calendar) but sourced
    from pandas_market_calendars instead, since this script has no Alpaca
    dependency at all.
    """
    import pandas_market_calendars as mcal

    as_of = as_of or dt.date.today()
    nyse = mcal.get_calendar("NYSE")
    sched = nyse.schedule(start_date=as_of, end_date=as_of + dt.timedelta(days=10))
    days = [d.date() for d in sched.index]
    if not days or days[0] != as_of:
        return False  # today isn't even a trading day
    later_this_month = [d for d in days[1:] if d.year == as_of.year and d.month == as_of.month]
    return len(later_this_month) == 0


def read_last_logged_picks() -> dict | None:
    if not LOG_FILE.exists():
        return None
    with open(LOG_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def log_picks(row: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    is_new = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true",
                     help="bypass the last-trading-day-of-month gate (for testing on any day)")
    ap.add_argument("--no-log", action="store_true",
                     help="print the report but don't write to scripts/logs/monthly_picks.csv")
    args = ap.parse_args()

    print("=" * 72)
    print("MONTHLY MOMENTUM ROTATION SIGNAL CHECK -- INFORMATIONAL ONLY")
    print("This script places NO orders and connects to NO broker. You place")
    print("trades yourself, manually, in whatever brokerage account you use.")
    print("=" * 72)

    if not args.force and not is_last_trading_day_of_month():
        print("\nToday is not the last NYSE trading day of the month. No signal "
              "check needed yet -- run this again on the last trading day, or "
              "pass --force to preview anyway.")
        return 0

    result = generate_signal()
    if not result["signal_computed"]:
        print(f"\nNo signal could be computed today: {result.get('reason')}")
        return 1

    weights = result["target_weights"]
    risk_off = result["risk_off"]
    signal_date = result["signal_date"].date()
    held = weights[weights > 0].sort_values(ascending=False)
    tickers = list(held.index)

    print(f"\nSignal date: {signal_date}")
    print(f"Market filter: {'RISK-OFF (SPY below its 200-day SMA)' if risk_off else 'RISK-ON (SPY above its 200-day SMA)'}")

    if risk_off:
        print("\nThis month: move to IEF (bonds) -- the market filter is defensive.")
    else:
        print("\nThis month, hold these 5 ETFs, equal-weighted at 20% each:")
        for t, w in held.items():
            print(f"  {t:<6} {w:.0%}")

    last = read_last_logged_picks()
    if last is not None:
        last_tickers = last["tickers"].split(",") if last["tickers"] else []
        added = sorted(set(tickers) - set(last_tickers))
        removed = sorted(set(last_tickers) - set(tickers))
        print(f"\nLast logged picks ({last['date']}): {', '.join(last_tickers) if last_tickers else '(none)'}")
        if added or removed:
            print(f"Changed since then -- added: {', '.join(added) or '(none)'}; "
                  f"removed: {', '.join(removed) or '(none)'}")
        else:
            print("No change since last logged month.")
    else:
        print("\nNo prior logged picks found -- this is the first recorded run.")

    print(f"\n>>> This month, hold: {', '.join(tickers)}. If you are not already "
          f"holding exactly these, rebalance to them (manually, in your own "
          f"brokerage account). <<<")

    if not args.no_log:
        if last is not None and last["date"] == str(signal_date):
            print(f"\nAlready logged for {signal_date} -- not duplicating the entry "
                  f"(re-run detected).")
        else:
            log_picks({
                "date": str(signal_date),
                "risk_off": risk_off,
                "tickers": ",".join(tickers),
                "signal_source": "momentum_rotation N=12 K=5 SMA=200 monthly",
            })
            print(f"\nLogged to {LOG_FILE.relative_to(REPO)}")
    else:
        print("\n--no-log: not written to the picks log.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
