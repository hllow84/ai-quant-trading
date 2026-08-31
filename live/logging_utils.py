"""
logging_utils.py -- append-only CSV logs for orders and account equity.
Both files live in live/logs/ (git-ignored, matched by the repo's blanket
*.csv rule) so they persist locally across runs without polluting git.
"""
from __future__ import annotations

import csv
from pathlib import Path

from live.config import LOGS_DIR

ORDER_LOG = LOGS_DIR / "orders_log.csv"
EQUITY_LOG = LOGS_DIR / "equity_log.csv"

ORDER_FIELDS = [
    "timestamp", "signal_date", "ticker", "side", "notional_usd", "qty",
    "price_at_order", "order_id", "status", "signal_source",
]
EQUITY_FIELDS = ["timestamp", "signal_date", "equity", "cash", "peak_equity", "drawdown"]


def _append_row(path: Path, fields: list[str], row: dict) -> None:
    is_new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if is_new:
            w.writeheader()
        w.writerow(row)


def log_order(row: dict) -> None:
    _append_row(ORDER_LOG, ORDER_FIELDS, row)


def log_equity(row: dict) -> None:
    _append_row(EQUITY_LOG, EQUITY_FIELDS, row)
