"""
download_google_trends_gold.py — Pull Google Trends search interest for
"buy gold" (US), monthly, 2013-2025, via pytrends (unofficial free wrapper
around Google's own public Trends UI — no API key, but rate-limited/CAPTCHA-
prone; this project has no paid alternative for retail-attention data).

Google Trends returns a 0-100 index RELATIVE TO THE REQUESTED WINDOW, not an
absolute count — re-pulling with a different date range can shift the scale.
This is stated explicitly, not hidden, and is why the exact window (2013-01-01
to 2025-12-31, matching this project's gold data window) must be reproduced
if this data is ever re-pulled for a follow-up.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "google_trends_buy_gold_us.csv"

KEYWORD = "buy gold"
GEO = "US"
TIMEFRAME = "2013-01-01 2025-12-31"


def fetch(retries: int = 5) -> pd.DataFrame:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            pytrends = TrendReq(hl="en-US", tz=0)
            pytrends.build_payload([KEYWORD], timeframe=TIMEFRAME, geo=GEO)
            df = pytrends.interest_over_time()
            if df.empty:
                raise ValueError("empty response from Google Trends")
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"[attempt {attempt}/{retries}] fetch failed: {e}", file=sys.stderr)
            time.sleep(5 * attempt)
    raise RuntimeError(f"Google Trends fetch failed after {retries} attempts: {last_err}")


def main() -> None:
    df = fetch()
    df = df.drop(columns=["isPartial"], errors="ignore")
    df = df.rename(columns={KEYWORD: "search_interest"})
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])

    assert df["date"].is_monotonic_increasing
    span_days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    assert span_days > 365 * 10, f"suspiciously short history: {span_days} days"
    assert df["search_interest"].between(0, 100).all(), "search interest out of [0,100] range"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Keyword: {KEYWORD!r}  Geo: {GEO}  Timeframe: {TIMEFRAME}")
    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()}")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
