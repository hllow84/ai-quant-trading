"""
broker.py -- thin wrapper around Alpaca's TradingClient. Alpaca is used for
account state, positions, the trading calendar, and order execution ONLY --
price data for the signal itself comes from yfinance (see signal.py) to match
the audited backtest's data source exactly.
"""
from __future__ import annotations

import datetime as dt

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import GetCalendarRequest, MarketOrderRequest

from live.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_ONLY

_client: TradingClient | None = None


def get_client() -> TradingClient:
    global _client
    if _client is None:
        if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
            raise RuntimeError(
                "ALPACA_API_KEY / ALPACA_SECRET_KEY not set. Copy live/.env.example "
                "to live/.env and fill in real values."
            )
        _client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_ONLY)
    return _client


def get_account() -> dict:
    acct = get_client().get_account()
    return {
        "equity": float(acct.equity),
        "cash": float(acct.cash),
        "buying_power": float(acct.buying_power),
        "portfolio_value": float(acct.portfolio_value),
        "account_number": acct.account_number,
        "status": str(acct.status),
    }


def get_positions() -> dict[str, dict]:
    """symbol -> {qty, market_value, avg_entry_price}"""
    out = {}
    for p in get_client().get_all_positions():
        out[p.symbol] = {
            "qty": float(p.qty),
            "market_value": float(p.market_value),
            "avg_entry_price": float(p.avg_entry_price),
        }
    return out


def is_last_trading_day_of_month(as_of: dt.date | None = None) -> bool:
    """
    Uses Alpaca's authoritative NYSE trading calendar (handles holidays
    correctly, unlike a naive weekday check) to determine whether `as_of`
    (default: today) is the last trading day of its calendar month.
    """
    as_of = as_of or dt.date.today()
    end = as_of + dt.timedelta(days=10)
    req = GetCalendarRequest(start=as_of, end=end)
    days = get_client().get_calendar(req)
    if not days or days[0].date != as_of:
        return False  # today isn't even a trading day
    for d in days[1:]:
        if d.date.month == as_of.month and d.date.year == as_of.year:
            return False  # a later trading day exists this month
        break  # first entry after as_of is in a different month -> True
    return True


def place_notional_order(symbol: str, notional: float, side: OrderSide) -> dict:
    """
    Places a fractional-share market order sized in dollars. `notional` must
    be positive; direction comes from `side`.
    """
    if notional <= 0:
        raise ValueError(f"notional order size must be positive, got {notional}")
    req = MarketOrderRequest(
        symbol=symbol,
        notional=round(notional, 2),
        side=side,
        time_in_force=TimeInForce.DAY,
    )
    order = get_client().submit_order(req)
    return {
        "id": str(order.id),
        "symbol": order.symbol,
        "side": str(order.side),
        "notional": float(order.notional) if order.notional else None,
        "qty": float(order.qty) if order.qty else None,
        "status": str(order.status),
        "submitted_at": str(order.submitted_at),
    }
