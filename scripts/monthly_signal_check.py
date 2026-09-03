#!/usr/bin/env python3
"""
monthly_signal_check.py -- MANUAL MONITOR. Prints the current target basket
for the audited cross-sectional momentum rotation strategy (N=12, K=5,
200-day SMA market filter, base 17-ETF universe -- STATE_OF_PLAY.md sections
12/12.1-12.4).

Supports BOTH rebalance cadences studied in STATE_OF_PLAY sec 12.6:
    --freq monthly   (default) -- check on the last trading day of every
                                  calendar month. Reacts fastest to the
                                  200-day-SMA risk-off signal; best cadence
                                  in the 2000-2009 crash window.
    --freq quarterly           -- check only on the last trading day of a
                                  calendar QUARTER (Mar/Jun/Sep/Dec month-end).
                                  Maximised full-period compounded return in
                                  sec 12.6 (+1010% vs monthly +732%), at
                                  roughly half the turnover / cost load.

WHY --freq only changes the DATE GATE, not the signal math: sec 12.6
established that the ranking + market-filter computation in
research/momentum_rotation.py::build_weights() is IDENTICAL at every cadence
-- only the frequency of acting on it changes. In the backtest that
decimation is `rebalance_step`; in a live monitor it is "only run on the
right day". So this script reuses live/signals.py::generate_signal()
UNCHANGED (which calls build_weights() unchanged, now with the sec-12.6
signal_freq/rebalance_step params wired through) and the ONLY cadence logic
here is is_last_trading_day_of_period(freq). Each cadence logs to its own
file so month-over-month / quarter-over-quarter comparisons stay like-for-like.

*** INFORMATIONAL ONLY. This script places NO orders and connects to NO
*** broker. You place trades yourself, manually, in whatever brokerage
*** account you actually use -- this just tells you what the audited signal
*** says to hold.
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
LOG_FIELDS = ["date", "risk_off", "tickers", "signal_source"]

QUARTER_END_MONTHS = (3, 6, 9, 12)   # calendar-quarter month-ends
LOG_FILE_BY_FREQ = {
    "monthly": LOG_DIR / "monthly_picks.csv",
    "quarterly": LOG_DIR / "quarterly_picks.csv",
}
PERIOD_WORD = {"monthly": "month", "quarterly": "quarter"}


def is_last_trading_day_of_period(freq: str, as_of: dt.date | None = None) -> bool:
    """
    True iff `as_of` (default: today) is the last NYSE trading day of the
    period selected by `freq`:
      - "monthly"   : last trading day of the calendar MONTH
      - "quarterly" : last trading day of the calendar QUARTER, i.e. the
                      month-end of March / June / September / December

    NYSE trading-calendar check via pandas_market_calendars (same intent as
    live/broker.py::is_last_trading_day_of_month(), which uses Alpaca's
    calendar -- this script has no Alpaca dependency). "Last trading day of
    the quarter" is just "last trading day of the month AND the month is a
    quarter-end", which is exactly how sec 12.6's quarterly cadence
    (every 3rd month-end) lands on calendar quarters.
    """
    import pandas_market_calendars as mcal

    as_of = as_of or dt.date.today()
    nyse = mcal.get_calendar("NYSE")
    sched = nyse.schedule(start_date=as_of, end_date=as_of + dt.timedelta(days=10))
    days = [d.date() for d in sched.index]
    if not days or days[0] != as_of:
        return False  # today isn't even a trading day
    later_this_month = [d for d in days[1:] if (d.year, d.month) == (as_of.year, as_of.month)]
    if later_this_month:
        return False  # a later trading day exists this month -> not month-end
    if freq == "quarterly":
        return as_of.month in QUARTER_END_MONTHS
    return True


def read_last_logged_picks(log_file: Path) -> dict | None:
    if not log_file.exists():
        return None
    with open(log_file, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None


def log_picks(log_file: Path, row: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    is_new = not log_file.exists()
    with open(log_file, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--freq", choices=["monthly", "quarterly"], default="monthly",
                    help="rebalance cadence to check against (default: monthly). "
                         "quarterly = last trading day of Mar/Jun/Sep/Dec only (STATE_OF_PLAY sec 12.6).")
    ap.add_argument("--force", action="store_true",
                    help="bypass the last-trading-day-of-period gate (for testing on any day)")
    ap.add_argument("--no-log", action="store_true",
                    help="print the report but don't write to the per-cadence picks log")
    args = ap.parse_args()

    freq = args.freq
    period = PERIOD_WORD[freq]
    log_file = LOG_FILE_BY_FREQ[freq]

    print("=" * 72)
    print(f"{freq.upper()} MOMENTUM ROTATION SIGNAL CHECK -- INFORMATIONAL ONLY")
    print("This script places NO orders and connects to NO broker. You place")
    print("trades yourself, manually, in whatever brokerage account you use.")
    print("=" * 72)

    if not args.force and not is_last_trading_day_of_period(freq):
        print(f"\nToday is not the last NYSE trading day of the {period}. No signal "
              f"check needed yet -- run this again on the last trading day of the "
              f"{period}, or pass --force to preview anyway.")
        return 0

    # generate_signal() is cadence-invariant (sec 12.6): the ranking + SMA
    # filter is identical at every frequency, so both cadences call it with the
    # monthly defaults and the cadence is enforced by the date gate above.
    result = generate_signal(signal_freq="M", rebalance_step=1)
    if not result["signal_computed"]:
        print(f"\nNo signal could be computed today: {result.get('reason')}")
        return 1

    weights = result["target_weights"]
    risk_off = result["risk_off"]
    signal_date = result["signal_date"].date()
    held = weights[weights > 0].sort_values(ascending=False)
    tickers = list(held.index)

    print(f"\nCadence: {freq}  (checking on the last trading day of each {period})")
    print(f"Signal date: {signal_date}")
    print(f"Market filter: {'RISK-OFF (SPY below its 200-day SMA)' if risk_off else 'RISK-ON (SPY above its 200-day SMA)'}")

    if risk_off:
        print(f"\nThis {period}: move to IEF (bonds) -- the market filter is defensive.")
    else:
        print(f"\nThis {period}, hold these 5 ETFs, equal-weighted at 20% each:")
        for t, w in held.items():
            print(f"  {t:<6} {w:.0%}")

    last = read_last_logged_picks(log_file)
    if last is not None:
        last_tickers = last["tickers"].split(",") if last["tickers"] else []
        added = sorted(set(tickers) - set(last_tickers))
        removed = sorted(set(last_tickers) - set(tickers))
        print(f"\nLast logged {freq} picks ({last['date']}): "
              f"{', '.join(last_tickers) if last_tickers else '(none)'}")
        if added or removed:
            print(f"Changed since then -- added: {', '.join(added) or '(none)'}; "
                  f"removed: {', '.join(removed) or '(none)'}")
        else:
            print(f"No change since last logged {period}.")
    else:
        print(f"\nNo prior logged {freq} picks found -- this is the first recorded run for this cadence.")

    print(f"\n>>> This {period}, hold: {', '.join(tickers)}. If you are not already "
          f"holding exactly these, rebalance to them (manually, in your own "
          f"brokerage account). <<<")

    if not args.no_log:
        if last is not None and last["date"] == str(signal_date):
            print(f"\nAlready logged for {signal_date} in {log_file.name} -- not "
                  f"duplicating the entry (re-run detected).")
        else:
            log_picks(log_file, {
                "date": str(signal_date),
                "risk_off": risk_off,
                "tickers": ",".join(tickers),
                "signal_source": f"momentum_rotation N=12 K=5 SMA=200 {freq}",
            })
            print(f"\nLogged to {log_file.relative_to(REPO)}")
    else:
        print("\n--no-log: not written to the picks log.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
