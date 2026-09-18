"""
download_vix.py — Pull the full daily VIX history from CBOE's own public CSV
endpoint. Free, no API key, no rate limit encountered. Daily since 1990.
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "VIX_history_cboe.csv"
URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"


def fetch(retries: int = 5) -> pd.DataFrame:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(URL, timeout=60)
            resp.raise_for_status()
            df = pd.read_csv(StringIO(resp.text))
            if df.empty:
                raise ValueError("empty response from CBOE endpoint")
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"[attempt {attempt}/{retries}] fetch failed: {e}", file=sys.stderr)
    raise RuntimeError(f"VIX fetch failed after {retries} attempts: {last_err}")


def main() -> None:
    df = fetch()
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)

    assert df["date"].is_monotonic_increasing
    assert df["date"].duplicated().sum() == 0
    span_days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    assert span_days > 365 * 15, f"suspiciously short history: {span_days} days"
    assert df["close"].between(5, 100).all(), "VIX close out of sane range"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()}")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
