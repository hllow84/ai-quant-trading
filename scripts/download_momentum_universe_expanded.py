#!/usr/bin/env python3
"""
download_momentum_universe_expanded.py -- pulls the ADDITIONAL instrument
classes for the widened cross-sectional momentum universe (run as a separate,
clearly-labeled step after the section 12 audit, per the audit brief):

  Commodities:      DBC (broad basket), USO (oil), UNG (nat gas), SLV (silver)
                     -- GLD already in the base universe
  International:    VGK (Europe), INDA (India), FXI (China)
  Factor:           MTUM (momentum factor), VTV (value factor)
  Mid-cap breadth:  MDY (S&P MidCap 400) -- IWM (small-cap) already in base

Same fetch logic as scripts/download_momentum_universe.py (period="max",
auto_adjust=True, retry-on-failure). Merges with the existing base panel
(data/momentum_universe_adjclose.csv) into data/momentum_universe_expanded_adjclose.csv
WITHOUT overwriting the original base file, so the section-12 audit stays
reproducible against the original 17-ETF universe.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO = Path(__file__).parent.parent
DATA = REPO / "data"

NEW_TICKERS = ["DBC", "USO", "UNG", "SLV", "VGK", "INDA", "FXI", "MTUM", "VTV", "MDY"]
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
    base = pd.read_csv(DATA / "momentum_universe_adjclose.csv", index_col=0, parse_dates=True).sort_index()

    report_rows = []
    panel = {t: base[t] for t in base.columns}
    for tkr in NEW_TICKERS:
        print(f"Pulling {tkr} ...")
        df = fetch_one(tkr)
        if df is None:
            print(f"  [{tkr}] FAILED after {MAX_RETRIES} attempts -- ABORTING")
            sys.exit(1)
        df.to_csv(DATA / f"{tkr}_daily_yfinance.csv")
        report_rows.append({
            "ticker": tkr, "start": df.index[0].date().isoformat(), "end": df.index[-1].date().isoformat(),
            "n_bars": len(df),
        })
        panel[tkr] = df["close"]
        print(f"  [{tkr}] {df.index[0].date()} -> {df.index[-1].date()}  ({len(df)} bars)")

    report = pd.DataFrame(report_rows)
    report.to_csv(DATA / "momentum_universe_expanded_report.csv", index=False)
    print("\n=== NEW TICKER REPORT ===")
    print(report.to_string(index=False))

    merged = pd.DataFrame(panel).sort_index()
    merged.to_csv(DATA / "momentum_universe_expanded_adjclose.csv")
    print(f"\nExpanded panel saved: {merged.shape[0]} rows x {merged.shape[1]} cols "
          f"({merged.index[0].date()} -> {merged.index[-1].date()})")


if __name__ == "__main__":
    main()
