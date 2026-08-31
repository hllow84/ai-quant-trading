#!/usr/bin/env python3
"""
rebalance.py -- monthly signal-to-order pipeline. Meant to be run once per
day near/after market close via a scheduler (see live/README.md); it is a
no-op on any day that isn't the actual last NYSE trading day of the month,
so scheduling it daily in the last few days of each month is safe.

Order of operations (each step can halt the run -- nothing downstream of a
halt executes):
  1. Kill-switch check (state.json) -- refuse immediately if already tripped.
  2. Pull account equity, update peak, check the 15% drawdown kill switch.
  3. Confirm today is the last trading day of the month (Alpaca calendar),
     unless --force.
  4. PAPER_ONLY / paper-rebalance-count gate.
  5. Generate the signal (live/signals.py) -- reuses build_weights() exactly.
     A malformed signal (bad sum, negative weight) raises and halts here.
  6. Apply the 25% position cap.
  7. Diff target vs current holdings into a trade list.
  8. Manual keypress review for the first MANUAL_REVIEW_REBALANCES runs.
  9. Execute orders, log every one, update state.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from alpaca.trading.enums import OrderSide

from live import broker, config, logging_utils, state as state_mod
from live.risk import RiskViolation, apply_position_cap, update_peak_and_check_kill_switch
from live.signals import generate_signal

MIN_TRADE_USD = 5.00  # skip dust trades below this notional


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                     help="bypass the last-trading-day-of-month gate (manual testing only)")
    ap.add_argument("--dry-run", action="store_true",
                     help="compute and print everything, place no orders, do not update state")
    args = ap.parse_args()

    st = state_mod.load_state()
    now = state_mod.now_iso()

    print(f"=== momentum rotation rebalance run -- {now} ===")
    print(f"Alpaca mode: {'PAPER' if config.PAPER_ONLY else 'LIVE (REAL MONEY)'}")

    if st["kill_switch_active"]:
        print(
            f"\nKILL SWITCH ACTIVE (tripped {st['kill_switch_triggered_at']}, "
            f"drawdown {st['kill_switch_drawdown']:.1%}). No new orders will be placed. "
            f"Clear it manually in live/state/state.json (kill_switch_active: false) "
            f"only after reviewing why it tripped."
        )
        return 1

    # -- 2. equity / kill switch -----------------------------------------
    acct = broker.get_account()
    equity = acct["equity"]
    new_peak, triggered, dd = update_peak_and_check_kill_switch(equity, st["peak_equity"])
    st["peak_equity"] = new_peak

    logging_utils.log_equity({
        "timestamp": now, "signal_date": "", "equity": equity,
        "cash": acct["cash"], "peak_equity": new_peak, "drawdown": dd,
    })

    if triggered:
        st["kill_switch_active"] = True
        st["kill_switch_triggered_at"] = now
        st["kill_switch_drawdown"] = dd
        state_mod.save_state(st)
        print(
            f"\nKILL SWITCH TRIPPED: equity {equity:,.2f} is {dd:.1%} below peak "
            f"{new_peak:,.2f} (limit {config.KILL_SWITCH_DRAWDOWN:.0%}). "
            f"Halting -- no orders placed. Manual review required before clearing."
        )
        return 1
    state_mod.save_state(st)  # persist peak_equity even when not triggered

    # -- 3. last-trading-day-of-month gate --------------------------------
    if not args.force and not broker.is_last_trading_day_of_month():
        print("Today is not the last NYSE trading day of the month. No action taken.")
        return 0

    # -- 4. paper-trading gate ---------------------------------------------
    if not config.PAPER_ONLY:
        if st["paper_rebalance_count"] < config.REQUIRED_PAPER_MONTHS:
            print(
                f"\nREFUSING TO TRADE LIVE: PAPER_ONLY is False but only "
                f"{st['paper_rebalance_count']}/{config.REQUIRED_PAPER_MONTHS} paper "
                f"monthly rebalances have been logged. Run on paper "
                f"({config.REQUIRED_PAPER_MONTHS - st['paper_rebalance_count']} more month(s)) "
                f"before flipping PAPER_ONLY in live/config.py."
            )
            return 1
        if not sys.stdin.isatty():
            print(
                "\nREFUSING TO TRADE LIVE: real-money confirmation requires an "
                "interactive terminal (this run has no stdin -- e.g. a scheduled "
                "task). Run rebalance.py by hand for a live-money rebalance."
            )
            return 1
        confirm = input(
            "\nYou are about to place REAL-MONEY orders. Type exactly "
            "'I UNDERSTAND THIS IS REAL MONEY' to continue: "
        )
        if confirm.strip() != "I UNDERSTAND THIS IS REAL MONEY":
            print("Confirmation phrase not matched. Aborting, no orders placed.")
            return 1

    # -- 5. signal ----------------------------------------------------------
    try:
        sig = generate_signal()
    except RiskViolation as e:
        print(f"\nSIGNAL REJECTED by sanity check: {e}\nRefusing to trade. No orders placed.")
        return 1

    if not sig["signal_computed"]:
        print(f"\nNo signal produced today: {sig.get('reason')}. No action taken.")
        return 0

    target_weights = sig["target_weights"]
    signal_date = sig["signal_date"]
    print(f"\nSignal date: {signal_date.date()}   risk_off={sig['risk_off']}")
    print("Raw target weights:")
    print(target_weights[target_weights > 0].to_string())

    # -- 6. position cap ------------------------------------------------
    capped_weights = apply_position_cap(target_weights)
    if not capped_weights.equals(target_weights):
        print("\nPosition cap applied (25% ceiling) -- capped weights:")
        print(capped_weights[capped_weights > 0].to_string())
        uninvested = 1.0 - float(capped_weights.sum())
        print(f"Uninvested (cash) fraction after cap: {uninvested:.2%}")

    # -- 7. diff into trade list --------------------------------------------
    positions = broker.get_positions()
    target_dollars = (capped_weights * equity).to_dict()
    trades = []
    for ticker in capped_weights.index:
        current_val = positions.get(ticker, {}).get("market_value", 0.0)
        target_val = target_dollars[ticker]
        delta = target_val - current_val
        if abs(delta) < MIN_TRADE_USD:
            continue
        trades.append({
            "ticker": ticker, "side": "buy" if delta > 0 else "sell",
            "notional_usd": abs(delta), "current_val": current_val, "target_val": target_val,
        })
    # sell every current position not in target universe at all (shouldn't
    # happen in normal operation, but don't leave orphaned holdings silently)
    for ticker, pos in positions.items():
        if ticker not in capped_weights.index and pos["market_value"] > MIN_TRADE_USD:
            trades.append({
                "ticker": ticker, "side": "sell", "notional_usd": pos["market_value"],
                "current_val": pos["market_value"], "target_val": 0.0,
            })

    if not trades:
        print("\nNo trades needed -- current holdings already match target weights.")
        if not args.dry_run:
            st["total_rebalance_count"] += 1
            if config.PAPER_ONLY:
                st["paper_rebalance_count"] += 1
            st["last_rebalance_date"] = str(signal_date.date())
            state_mod.save_state(st)
        return 0

    print("\nProposed trades:")
    print(f"{'ticker':<6} {'side':<5} {'notional_usd':>14} {'current':>12} {'target':>12}")
    for tr in sorted(trades, key=lambda x: x["side"]):  # sells first
        print(f"{tr['ticker']:<6} {tr['side']:<5} {tr['notional_usd']:>14,.2f} "
              f"{tr['current_val']:>12,.2f} {tr['target_val']:>12,.2f}")

    if args.dry_run:
        print("\n--dry-run: no orders placed, state not updated.")
        return 0

    # -- 8. manual review gate -----------------------------------------------
    if st["total_rebalance_count"] < config.MANUAL_REVIEW_REBALANCES:
        if not sys.stdin.isatty():
            print(
                f"\nManual review required (rebalance #{st['total_rebalance_count'] + 1} of "
                f"the first {config.MANUAL_REVIEW_REBALANCES}) but this run has no interactive "
                f"terminal (e.g. a scheduled task). Run rebalance.py by hand to confirm the "
                f"first {config.MANUAL_REVIEW_REBALANCES} rebalances -- aborting, no orders placed."
            )
            return 1
        confirm = input(
            f"\nManual review required (rebalance #{st['total_rebalance_count'] + 1} of "
            f"the first {config.MANUAL_REVIEW_REBALANCES}). Type YES to place these orders: "
        )
        if confirm.strip() != "YES":
            print("Not confirmed. Aborting, no orders placed, state not updated.")
            return 1

    # -- 9. execute -----------------------------------------------------------
    signal_source = (
        f"momentum_rotation N={config.N_MONTHS} K={config.TOP_K} "
        f"SMA={config.SMA_WINDOW} monthly risk_off={sig['risk_off']}"
    )
    ref_prices = sig["adjclose_tail"].iloc[-1]
    sells = [t for t in trades if t["side"] == "sell"]
    buys = [t for t in trades if t["side"] == "buy"]
    for tr in sells + buys:  # free up cash from sells before spending it on buys
        side = OrderSide.SELL if tr["side"] == "sell" else OrderSide.BUY
        try:
            order = broker.place_notional_order(tr["ticker"], tr["notional_usd"], side)
            status = order["status"]
            order_id = order["id"]
        except Exception as e:
            print(f"ORDER FAILED for {tr['ticker']} {tr['side']} ${tr['notional_usd']:.2f}: {e}")
            status, order_id = f"FAILED: {e}", ""
        logging_utils.log_order({
            "timestamp": state_mod.now_iso(), "signal_date": str(signal_date.date()),
            "ticker": tr["ticker"], "side": tr["side"], "notional_usd": round(tr["notional_usd"], 2),
            "qty": "", "price_at_order": float(ref_prices.get(tr["ticker"], float("nan"))),
            "order_id": order_id, "status": status, "signal_source": signal_source,
        })
        print(f"  {tr['ticker']:<6} {tr['side']:<5} ${tr['notional_usd']:>10,.2f}  -> {status}")

    st["total_rebalance_count"] += 1
    if config.PAPER_ONLY:
        st["paper_rebalance_count"] += 1
    st["last_rebalance_date"] = str(signal_date.date())
    state_mod.save_state(st)

    print(f"\nRebalance complete. paper_rebalance_count={st['paper_rebalance_count']}, "
          f"total_rebalance_count={st['total_rebalance_count']}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"\nSETUP ERROR: {e}")
        raise SystemExit(1)
