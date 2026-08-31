#!/usr/bin/env python3
"""
download_vix_svxy.py — daily VIX and SVXY closes for the volatility-risk-
premium test (STATE_OF_PLAY section 20).

VIX (^VIX): CBOE Volatility Index, implied vol of S&P 500 options.
SVXY: ProShares Short VIX Short-Term Futures ETF, available since 2011 —
      the tradeable short-vol proxy the task named. Its REAL historical
      price already embeds the fund's own expense ratio and VIX-futures
      roll cost/contango drag, and (critically for this study) its REAL
      2018-02-05 "Volmageddon" crash: ProShares deleveraged SVXY from -1x
      to -0.5x VIX-futures exposure immediately after that session because
      the product came close to a wipeout the way its cousin XIV (which
      was terminated) did. Using the actual traded price series means that
      tail event is genuinely in the data, not modeled around.
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

TICKERS = {"^VIX": "vix", "SVXY": "svxy"}
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
    for ticker, name in TICKERS.items():
        print(f"[{ticker}] fetching daily ...", flush=True)
        df = fetch_one(ticker)
        if df is None:
            print(f"[{ticker}] FAILED.", flush=True)
            continue
        out = pd.DataFrame({"open": df["Open"], "high": df["High"], "low": df["Low"], "close": df["Close"]})
        out.index = pd.DatetimeIndex(out.index).tz_localize(None).normalize()
        out.index.name = "date"
        out = out.dropna()
        out_path = DATA / f"{name}_daily_yfinance.csv"
        out.to_csv(out_path)
        report_rows.append(dict(ticker=ticker, bars=len(out),
                                start=str(out.index.min().date()), end=str(out.index.max().date())))
        print(f"    saved {out_path.name} ({len(out):,} rows, {out.index.min().date()} -> {out.index.max().date()})",
              flush=True)

    rep = pd.DataFrame(report_rows)
    rep.to_csv(DATA / "vix_svxy_report.csv", index=False)
    print("\nDone.")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
