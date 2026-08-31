#!/usr/bin/env python3
"""
download_dxy_cew.py — daily closes for the cross-asset lead-lag test
(STATE_OF_PLAY section 19): the real ICE US Dollar Index and the EM-
currency-ETF comparison asset.

DXY SOURCE — stated, as required: the task offered UUP (an ETF proxy) or
"a better free DXY source if one exists." Checked: yfinance serves
**DX-Y.NYB**, the actual ICE US Dollar Index (not an ETF wrapper), with
full history back to 1971 vs UUP's 2007 inception and UUP's own expense-
ratio/tracking-error noise on top of the index it tracks. DX-Y.NYB is used
instead of UUP for exactly that reason — it is the real index, not a
proxy of a proxy.

CEW: WisdomTree Emerging Currency Strategy Fund, the specific EM-currency
ETF the task named. Inception 2009-06-02.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)

TICKERS = {"DX-Y.NYB": "DXY (real ICE US Dollar Index)", "CEW": "WisdomTree EM Currency Strategy Fund"}
MAX_RETRIES = 5


def fetch_one(ticker: str) -> pd.DataFrame | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download(ticker, period="max", interval="1d",
                             auto_adjust=True, actions=False, progress=False, threads=False)
            if df is None or df.empty:
                raise ValueError("empty frame")
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
        except Exception as e:
            print(f"  [{ticker}] attempt {attempt}/{MAX_RETRIES} failed: {e}", flush=True)
            time.sleep(2 * attempt)
    return None


def main() -> None:
    report_rows = []
    for ticker, label in TICKERS.items():
        print(f"[{ticker}] fetching daily ({label}) ...", flush=True)
        df = fetch_one(ticker)
        if df is None:
            print(f"[{ticker}] FAILED.", flush=True)
            continue
        out = pd.DataFrame({"close": df["Close"]})
        out.index = pd.DatetimeIndex(out.index).tz_localize(None).normalize()
        out.index.name = "date"
        safe_name = ticker.replace("-", "").replace(".", "")
        out_path = DATA / f"{safe_name}_daily_yfinance.csv"
        out.to_csv(out_path)
        report_rows.append(dict(ticker=ticker, label=label, bars=len(out),
                                start=str(out.index.min().date()), end=str(out.index.max().date())))
        print(f"    saved {out_path.name} ({len(out):,} rows, {out.index.min().date()} -> {out.index.max().date()})",
              flush=True)

    rep = pd.DataFrame(report_rows)
    rep.to_csv(DATA / "dxy_cew_report.csv", index=False)
    print("\nDone.")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
