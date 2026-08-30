#!/usr/bin/env python3
"""
download_momentum_universe.py — pull daily adjusted-close OHLCV for the
cross-sectional momentum rotation universe via yfinance.

Universe:
  11 SPDR sector ETFs: XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC
  6 asset-class ETFs:  TLT GLD IEF IWM EFA EEM
  1 benchmark:         SPY

Pulls MAXIMUM available history per ticker (period="max"), auto_adjust=True
(dividend/split-adjusted close). Retries on failure. Saves one CSV per ticker
to /data plus a merged wide-format adjusted-close panel. Reports actual first/
last bar dates per ticker -- no backfilling, no estimating.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO = Path(__file__).parent.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)

SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
ASSET_ETFS = ["TLT", "GLD", "IEF", "IWM", "EFA", "EEM"]
BENCHMARK = ["SPY"]
UNIVERSE = SECTOR_ETFS + ASSET_ETFS + BENCHMARK

MAX_RETRIES = 5


def fetch_one(ticker: str) -> pd.DataFrame | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download(
                ticker, period="max", interval="1d",
                auto_adjust=True, actions=False, progress=False, threads=False,
            )
            if df is None or df.empty:
                raise ValueError("empty frame")
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index.name = "date"
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.columns = ["open", "high", "low", "close", "volume"]
            return df
        except Exception as e:
            print(f"  [{ticker}] attempt {attempt}/{MAX_RETRIES} failed: {e}")
            time.sleep(2 * attempt)
    return None


def main():
    report_rows = []
    panel = {}
    for tkr in UNIVERSE:
        print(f"Pulling {tkr} ...")
        df = fetch_one(tkr)
        if df is None:
            print(f"  [{tkr}] FAILED after {MAX_RETRIES} attempts -- ABORTING")
            sys.exit(1)
        out_path = DATA / f"{tkr}_daily_yfinance.csv"
        df.to_csv(out_path)
        n_gaps = _count_gaps(df)
        report_rows.append({
            "ticker": tkr,
            "start": df.index[0].date().isoformat(),
            "end": df.index[-1].date().isoformat(),
            "n_bars": len(df),
            "weekday_gap_days_gt3": n_gaps,
            "min_close": round(float(df["close"].min()), 2),
            "max_close": round(float(df["close"].max()), 2),
        })
        panel[tkr] = df["close"]
        print(f"  [{tkr}] {df.index[0].date()} -> {df.index[-1].date()}  ({len(df)} bars)")

    report = pd.DataFrame(report_rows)
    report.to_csv(DATA / "momentum_universe_report.csv", index=False)
    print("\n=== PER-TICKER REPORT ===")
    print(report.to_string(index=False))

    merged = pd.DataFrame(panel).sort_index()
    merged.to_csv(DATA / "momentum_universe_adjclose.csv")
    print(f"\nMerged adjusted-close panel saved: {merged.shape[0]} rows x {merged.shape[1]} cols")
    print(f"Panel spans {merged.index[0].date()} -> {merged.index[-1].date()}")


def _count_gaps(df: pd.DataFrame) -> int:
    idx = df.index.to_series()
    deltas = idx.diff().dt.days.dropna()
    # weekday-to-weekday gap should be 1-3 days (weekend); flag anything else > 3
    return int((deltas > 3).sum())


if __name__ == "__main__":
    main()
