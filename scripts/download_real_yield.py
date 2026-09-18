"""
download_real_yield.py — Pull the 10-Year Treasury Inflation-Indexed Security
(TIPS) Constant Maturity real yield (FRED series DFII10), daily, since 2003.

Source: FRED's own public CSV export endpoint (fred.stlouisfed.org/graph/
fredgraph.csv?id=DFII10). Free, no API key, no rate limit encountered.
Published by the Federal Reserve/Treasury the same trading day (H.15 release,
~16:15 ET) — same-day availability, unlike COT's multi-day publication lag.

WHY THIS SERIES: real (inflation-adjusted) interest rates are the most
widely-documented macro driver of gold prices in the literature — gold pays
no yield, so rising real rates raise its opportunity cost (bearish) and
falling/negative real rates lower it (bullish). This is stated BEFORE any
signal is built or tested (research/run_real_yield_gold_signal.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "DFII10_real_yield_fred.csv"

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10"


def fetch(retries: int = 5) -> pd.DataFrame:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(URL, timeout=60)
            resp.raise_for_status()
            from io import StringIO
            df = pd.read_csv(StringIO(resp.text))
            if df.empty:
                raise ValueError("empty response from FRED CSV endpoint")
            return df
        except Exception as e:  # noqa: BLE001 — retry loop, re-raised below if exhausted
            last_err = e
            print(f"[attempt {attempt}/{retries}] fetch failed: {e}", file=sys.stderr)
    raise RuntimeError(f"FRED fetch failed after {retries} attempts: {last_err}")


def main() -> None:
    df = fetch()
    df.columns = ["date", "dfii10"]
    df["date"] = pd.to_datetime(df["date"])
    df["dfii10"] = pd.to_numeric(df["dfii10"], errors="coerce")
    df = df.dropna(subset=["dfii10"]).sort_values("date").reset_index(drop=True)

    assert df["date"].is_monotonic_increasing, "dates not sorted"
    assert df["date"].duplicated().sum() == 0, "duplicate dates"
    span_days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    assert span_days > 365 * 15, f"suspiciously short history: {span_days} days"
    # Sanity range: real 10y yields have ranged roughly -1.5% to +2.5% since 2003.
    assert df["dfii10"].between(-3.0, 4.0).all(), "real yield out of sane range"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()}")
    print(f"Real yield range: {df['dfii10'].min():.2f}% -> {df['dfii10'].max():.2f}%")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
