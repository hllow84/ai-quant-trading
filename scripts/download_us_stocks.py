#!/usr/bin/env python3
"""
download_us_stocks.py — pull daily adjusted OHLC for 6 large-cap, diverse-
sector US stocks via yfinance, for the individual-stocks leg of the price-
pattern re-test (STATE_OF_PLAY.md sections 9-11 precedent, never previously
run on single names).

UNIVERSE (5-10 large-cap, diverse sectors, as specified) — 6 chosen:
    AAPL  Technology
    JPM   Financials
    XOM   Energy
    JNJ   Health Care
    WMT   Consumer Staples
    CAT   Industrials
All S&P 500 constituents, among the most liquid single names in their
sectors, decades of daily history (no survivorship concern for THIS test —
these are all still-trading names, chosen for liquidity/diversity, not
picked with hindsight of which ones would look good in a backtest).

INTRADAY HISTORY — checked empirically, reported honestly, and why this
script pulls DAILY only:
    yfinance 60m bars: ~1 year of history available.
    yfinance 15m bars: ~60 days of history available.
    yfinance 1d bars : decades (AAPL back to 1980, all 6 names to well
                        before 2010).
That is nowhere near enough for a genuine out-of-regime test (this repo's
standing convention is an 8-year in-regime window plus a separate multi-year
holdout — STATE_OF_PLAY.md sec 7 rule 3). Per the task's explicit fallback:
DAILY bars are used instead, stated here as a real limitation, not silently
worked around. The 5-family grid's parameters (all expressed in BARS) then
rescale to TRADING DAYS instead of minutes/hours — the same honest rescaling
the M1 row (sec 11) did in the opposite direction: ATR 14 -> 14 trading
days, EMA 200 -> 200 trading days, max hold H -> H trading days.

SPREAD/COST — no real intraday bid/ask is available from yfinance daily
bars (same limitation STATE_OF_PLAY.md sec 12 documented for ETF data). A
stated, conservative bps assumption stands in, matching that section's own
convention for liquid instruments: 2 bps round-turn spread. Real NBBO
spreads on these 6 names are typically well under 2bps for a full share
lot, so this is conservative, not generous.

WINDOW: 2010-01-01 -> today, matching the in-regime (2018-2025) / out-of-
regime (2010-2017) split this repo already uses for FX/index families
(STATE_OF_PLAY.md sec 9.3, sec 11), so the individual-stocks leg reuses the
SAME split convention rather than inventing a new one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)

TICKERS = {
    "AAPL": "Technology", "JPM": "Financials", "XOM": "Energy",
    "JNJ": "Health Care", "WMT": "Consumer Staples", "CAT": "Industrials",
}
START = "2010-01-01"
SPREAD_BPS = 2.0  # stated conservative round-turn assumption, sec 12 convention
MAX_RETRIES = 5


def fetch_one(ticker: str) -> pd.DataFrame | None:
    import time
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = yf.download(ticker, start=START, interval="1d",
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


def to_repo_frame(raw: pd.DataFrame) -> pd.DataFrame:
    idx = pd.DatetimeIndex(raw.index).tz_localize("UTC") if raw.index.tz is None \
        else pd.DatetimeIndex(raw.index).tz_convert("UTC")
    out = pd.DataFrame({
        "mid_open": raw["Open"].to_numpy(),
        "mid_high": raw["High"].to_numpy(),
        "mid_low": raw["Low"].to_numpy(),
        "mid_close": raw["Close"].to_numpy(),
        "volume": raw["Volume"].to_numpy(),
    }, index=idx)
    out.index.name = "datetime_utc"
    out["spread"] = out["mid_close"] * (SPREAD_BPS / 1e4)
    return out


def verify_no_gaps(frame: pd.DataFrame, label: str) -> None:
    gaps = frame.index.to_series().diff().dropna().dt.days
    bad = gaps[gaps > 6]  # a week+ with no trading day is worth a look (holidays cluster but rarely exceed this)
    print(f"    [{label}] {len(frame):,} daily bars, {frame.index[0].date()} -> {frame.index[-1].date()}, "
          f"gaps > 6 calendar days: {len(bad)}", flush=True)
    if len(bad):
        for ts, g in bad.sort_values(ascending=False).head(5).items():
            print(f"      gap ending {ts.date()}: {g} days", flush=True)


def main() -> None:
    report_rows = []
    for ticker, sector in TICKERS.items():
        print(f"[{ticker}] fetching daily from {START} ...", flush=True)
        raw = fetch_one(ticker)
        if raw is None:
            print(f"[{ticker}] FAILED after {MAX_RETRIES} retries — skipped.", flush=True)
            continue
        frame = to_repo_frame(raw)
        verify_no_gaps(frame, ticker)
        out_path = DATA / f"{ticker}_D1_2010_2025_yfinance.csv"
        frame.to_csv(out_path)
        print(f"    saved {out_path.name} ({len(frame):,} rows)", flush=True)
        report_rows.append(dict(ticker=ticker, sector=sector, bars=len(frame),
                                 start=str(frame.index[0].date()), end=str(frame.index[-1].date()),
                                 spread_bps=SPREAD_BPS, path=out_path.name))

    rep = pd.DataFrame(report_rows)
    rep.to_csv(DATA / "us_stocks_report.csv", index=False)
    print("\nDone.")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
