"""
Smoke test for ccxt_adapter.py — requires live network access.

Skipped by default. Run explicitly with:
    pytest tests/test_ccxt_smoke.py -v -m network

Or: pytest tests/test_ccxt_smoke.py -v --run-network
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

pytestmark = pytest.mark.skip(reason="Network test — run manually with: pytest tests/test_ccxt_smoke.py -v")


def test_fetch_ohlcv_btcusdt():
    from data.adapters.ccxt_adapter import fetch_ohlcv
    df = fetch_ohlcv("BTC/USDT", "1h", "2024-01-01", "2024-01-03", venue="binance")
    assert not df.empty, "OHLCV fetch returned empty DataFrame"
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.index.tz is not None, "Index must be tz-aware UTC"
    print(f"  OHLCV rows: {len(df)}, first: {df.index[0]}, last: {df.index[-1]}")


def test_fetch_funding_rate_history():
    from data.adapters.ccxt_adapter import fetch_funding_rate_history
    df = fetch_funding_rate_history("BTC/USDT", "2024-01-01", "2024-01-10", venue="binance")
    assert not df.empty, "Funding rate fetch returned empty DataFrame"
    assert "funding_rate" in df.columns
    print(f"  Funding rows: {len(df)}, range: {df['funding_rate'].describe()}")


def test_fetch_open_interest_history():
    from data.adapters.ccxt_adapter import fetch_open_interest_history
    df = fetch_open_interest_history("BTC/USDT", "1h", "2024-01-01", "2024-01-03", venue="binance")
    assert not df.empty, "Open interest fetch returned empty DataFrame"
    assert "open_interest" in df.columns
    print(f"  OI rows: {len(df)}")
