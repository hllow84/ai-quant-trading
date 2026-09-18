"""
download_cot_gold.py — Pull the full history of CFTC Commitment of Traders
(Legacy Futures-Only Combined) reports for COMEX Gold.

Source: CFTC's own public Socrata dataset (publicreporting.cftc.gov), resource
id 6dca-aqww = "Legacy Report: Futures Only, Combined (Old and Other)". Free,
no API key, no rate limit encountered. Weekly data, Tuesday positions,
published the following Friday ~15:30 ET (CFTC's own stated schedule) — the
~3-4 calendar day gap between report_date and actual publication is the
publication lag any causal backtest MUST respect (handled downstream in
research/cot_signal.py via a shift, not here).

Fields kept: report date, open interest, non-commercial long/short/spread,
commercial long/short, non-reportable long/short — the standard Legacy
Futures-Only breakdown used by the classic "COT Index" (Williams) method.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "COT_GOLD_legacy_futures_only.csv"

BASE_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
MARKET_NAME = "GOLD - COMMODITY EXCHANGE INC."

COLUMNS = [
    "report_date_as_yyyy_mm_dd",
    "open_interest_all",
    "noncomm_positions_long_all",
    "noncomm_positions_short_all",
    "noncomm_postions_spread_all",
    "comm_positions_long_all",
    "comm_positions_short_all",
    "nonrept_positions_long_all",
    "nonrept_positions_short_all",
]


def fetch(retries: int = 5) -> pd.DataFrame:
    params = (
        f"$where=market_and_exchange_names='{MARKET_NAME}'"
        f"&$select={','.join(COLUMNS)}"
        f"&$order=report_date_as_yyyy_mm_dd ASC"
        f"&$limit=5000"
    )
    url = f"{BASE_URL}?{quote(params, safe='=&,$()')}"

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            rows = resp.json()
            if not rows:
                raise ValueError("empty response from CFTC Socrata endpoint")
            return pd.DataFrame(rows)
        except Exception as e:  # noqa: BLE001 — retry loop, re-raised below if exhausted
            last_err = e
            print(f"[attempt {attempt}/{retries}] fetch failed: {e}", file=sys.stderr)
    raise RuntimeError(f"COT fetch failed after {retries} attempts: {last_err}")


def main() -> None:
    df = fetch()
    df["report_date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"]).dt.date
    df = df.drop(columns=["report_date_as_yyyy_mm_dd"])

    numeric_cols = [c for c in df.columns if c != "report_date"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.sort_values("report_date").reset_index(drop=True)
    df = df[["report_date"] + numeric_cols]

    # Sanity checks before saving — never silently ship broken data.
    assert df["report_date"].is_monotonic_increasing, "report dates not sorted"
    assert df["report_date"].duplicated().sum() == 0, "duplicate report dates"
    assert (df["open_interest_all"] > 0).all(), "non-positive open interest found"
    span_days = (df["report_date"].iloc[-1] - df["report_date"].iloc[0]).days
    assert span_days > 365 * 15, f"suspiciously short history: {span_days} days"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['report_date'].iloc[0]} -> {df['report_date'].iloc[-1]}")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
