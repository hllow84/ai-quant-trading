"""
download_fed_balance_sheet.py — Pull the Federal Reserve's total assets
(FRED series WALCL, the weekly H.4.1 balance-sheet release), free, no key.
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "WALCL_fed_balance_sheet_fred.csv"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL"


def fetch(retries: int = 5) -> pd.DataFrame:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(URL, timeout=60)
            resp.raise_for_status()
            df = pd.read_csv(StringIO(resp.text))
            if df.empty:
                raise ValueError("empty response from FRED CSV endpoint")
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"[attempt {attempt}/{retries}] fetch failed: {e}", file=sys.stderr)
    raise RuntimeError(f"FRED fetch failed after {retries} attempts: {last_err}")


def main() -> None:
    df = fetch()
    df.columns = ["date", "walcl"]
    df["date"] = pd.to_datetime(df["date"])
    df["walcl"] = pd.to_numeric(df["walcl"], errors="coerce")
    df = df.dropna(subset=["walcl"]).sort_values("date").reset_index(drop=True)

    assert df["date"].is_monotonic_increasing
    assert df["date"].duplicated().sum() == 0
    span_days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    assert span_days > 365 * 15, f"suspiciously short history: {span_days} days"
    # Sane range: Fed assets in $ millions, ranged ~$700B to ~$9T since 2002.
    assert df["walcl"].between(5e5, 1.2e7).all(), "WALCL out of sane range"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()}")
    print(f"Range: ${df['walcl'].min()/1e6:.2f}T -> ${df['walcl'].max()/1e6:.2f}T")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
