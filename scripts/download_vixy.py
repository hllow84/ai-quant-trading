#!/usr/bin/env python3
"""
download_vixy.py — VIXY (ProShares VIX Short-Term Futures ETF, long vol)
daily close, for section 21's paired-hedge structure.

Why VIXY, not VXX (the task's suggested example): checked both. VXX (the
current iPath Series B note) only has data back to 2018-01-25 on yfinance
(the old Series A note matured and was replaced), which would truncate the
backtest window to ~8.5 years and drop most of section 20's SVXY window
(2011-10-04 onward). VIXY is the DIRECT long-vol counterpart to SVXY --
same ProShares family, same underlying VIX-futures construction, just the
opposite side -- and has data back to 2011-01-04, comfortably covering the
full SVXY window. Used instead of VXX for that reason, stated explicitly.
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
MAX_RETRIES = 5


def main() -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download("VIXY", period="max", interval="1d",
                             auto_adjust=True, actions=False, progress=False, threads=False)
            if df is None or df.empty:
                raise ValueError("empty frame")
            break
        except Exception as e:
            print(f"  attempt {attempt}/{MAX_RETRIES} failed: {e}", flush=True)
            time.sleep(2 * attempt)
    else:
        raise RuntimeError("failed to fetch VIXY")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    out = pd.DataFrame({"open": df["Open"], "high": df["High"], "low": df["Low"], "close": df["Close"]})
    out.index = pd.DatetimeIndex(out.index).tz_localize(None).normalize()
    out.index.name = "date"
    out = out.dropna()
    out_path = DATA / "vixy_daily_yfinance.csv"
    out.to_csv(out_path)
    print(f"saved {out_path.name} ({len(out):,} rows, {out.index.min().date()} -> {out.index.max().date()})")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
