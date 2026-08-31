#!/usr/bin/env python3
"""
download_momentum_countries.py — daily adjusted-close panel for the
country/region-equity-ETF momentum-rotation generalisation test
(STATE_OF_PLAY section 17).

UNIVERSE, every ticker's role stated (10 ranked instruments + 1 benchmark):

    EWJ   Japan
    EWG   Germany
    EWU   United Kingdom
    EWZ   Brazil
    INDA  India
    FXI   China (large-cap)
    EFA   developed markets ex-US/Canada (broad regional -- deliberately
          included per the task's explicit instruction, even though it
          overlaps EWJ/EWG/EWU in composition; this generalisation test is
          about whether the MECHANISM works on a country/region
          cross-section, not about building a non-overlapping universe)
    EEM   broad emerging markets (same rationale -- overlaps EWZ/INDA/FXI)
    SPY   United States (explicitly a RANKED competitor here, unlike the
          original ETF study where it was the excluded benchmark -- the
          task asks for the US to be one country among many in this test)
    IEF   intermediate US treasuries -- DEFENSIVE leg, the SAME instrument
          the original study used, reused unchanged (a genuinely different,
          lower-volatility asset class with clean multi-decade history --
          crypto has no equivalent, this universe does)

BENCHMARK (NEW, since SPY is now a ranked competitor and can't also be the
filter basis): ACWI (MSCI All-Country World Index ETF) -- a genuinely
global, market-cap-weighted equity benchmark, filling the same role SPY
played in the original study (excluded from ranking, used only for the
causal 200-day SMA risk-on/risk-off filter and as the buy-and-hold
comparison). Inception 2008-03-28 (verified below), which sets the
effective start of this test.

11 instruments total (10 ranked + ACWI benchmark). Data source and method
identical to scripts/download_momentum_universe.py: yfinance, period="max",
auto_adjust=True, real verified start dates, no backfilling.
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

BENCHMARK = "ACWI"
UNIVERSE = {
    "EWJ": "Japan", "EWG": "Germany", "EWU": "United Kingdom", "EWZ": "Brazil",
    "INDA": "India", "FXI": "China (large-cap)", "EFA": "developed ex-US/Canada (broad)",
    "EEM": "emerging markets (broad)", "SPY": "United States", "IEF": "DEFENSIVE (US treasuries)",
}
MAX_RETRIES = 5


def fetch_one(ticker: str) -> pd.Series | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download(ticker, period="max", interval="1d",
                             auto_adjust=True, actions=False, progress=False, threads=False)
            if df is None or df.empty:
                raise ValueError("empty frame")
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close = df["Close"].copy()
            close.index = pd.DatetimeIndex(close.index).tz_localize(None).normalize()
            return close
        except Exception as e:
            print(f"  [{ticker}] attempt {attempt}/{MAX_RETRIES} failed: {e}", flush=True)
            time.sleep(2 * attempt)
    return None


def main() -> None:
    closes = {}
    report_rows = []
    all_tickers = {BENCHMARK: "benchmark/market-filter basis, excluded from ranking"}
    all_tickers.update(UNIVERSE)

    for ticker, role in all_tickers.items():
        print(f"[{ticker}] fetching daily adjusted close ({role}) ...", flush=True)
        s = fetch_one(ticker)
        if s is None:
            print(f"[{ticker}] FAILED after {MAX_RETRIES} retries.", flush=True)
            continue
        closes[ticker] = s
        report_rows.append(dict(ticker=ticker, role=role, bars=len(s),
                                start=str(s.index.min().date()), end=str(s.index.max().date())))
        print(f"    {len(s):,} bars, {s.index.min().date()} -> {s.index.max().date()}", flush=True)

    panel = pd.DataFrame(closes).sort_index()
    panel.index.name = "date"
    out_path = DATA / "momentum_countries_adjclose.csv"
    panel.to_csv(out_path)

    rep = pd.DataFrame(report_rows)
    rep.to_csv(DATA / "momentum_countries_report.csv", index=False)
    print(f"\nSaved {out_path.name} ({len(panel):,} rows, {len(panel.columns)} columns)")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
