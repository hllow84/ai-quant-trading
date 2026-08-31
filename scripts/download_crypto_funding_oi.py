#!/usr/bin/env python3
"""
download_crypto_funding_oi.py — funding rate (Binance) + open interest
(Bybit) history for BTC/ETH, for the positioning-extreme contrarian
reversal test (STATE_OF_PLAY section 18).

Reuses the conclusions of notes/crypto_data_availability.md (probed
2026-08-22, not re-derived here):
  - Funding rate: Binance USD-M `/fapi/v1/fundingRate` has full history,
    no retention limit. BTC from 2019-09-09, ETH from 2019-11-26.
  - Open interest: Binance's `/futures/data/openInterestHist` is
    ~30-DAY RETENTION ONLY (verified: startTime before ~2026-07-25 returns
    HTTP 400 -1130) — USELESS for a multi-year study. OI comes from
    **Bybit v5** `/v5/market/open-interest` instead, which has deep history:
    BTC from 2020-08-04, ETH from 2020-10-21 (±3 days, bisection probe).
  - Cross-venue (funding from Binance, OI from Bybit) is an accepted repo
    convention (data venue != execution venue) but is stated here, not
    hidden: the two venues' order books are correlated but not identical,
    so "OI is elevated" is Bybit's crowd, while price/funding are Binance's.

This is the SAME binding constraint the prior probe found: Bybit OI is the
shallow leg. BTC usable from ~2020-08-04, ETH from ~2020-10-21 — years
shorter than the funding-rate-only history, and shorter still than the H1
price panel already on disk (data/BTCUSDT_H1_2018_2025_binance.csv, from
2018-01-01). The strategy's usable window is therefore set by OI, not by
price or funding depth — stated plainly, not silently shortened.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib.parse import unquote

import pandas as pd
import requests

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)

FAPI = "https://fapi.binance.com"
BYBIT = "https://api.bybit.com"
TIMEOUT = 20
MAX_RETRIES = 5

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
FUNDING_START = pd.Timestamp("2019-08-01", tz="UTC")  # safely before either symbol's real start
OI_START = pd.Timestamp("2020-08-01", tz="UTC")        # safely before BTC's probed 2020-08-04 start
END = pd.Timestamp.now(tz="UTC")

S = requests.Session()
S.headers.update({"User-Agent": "research-download/1.0"})


def _get(url: str, params: dict) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = S.get(url, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            print(f"    HTTP {r.status_code}: {r.text[:160]} (attempt {attempt}/{MAX_RETRIES})", flush=True)
        except Exception as e:
            print(f"    {e.__class__.__name__}: {e} (attempt {attempt}/{MAX_RETRIES})", flush=True)
        time.sleep(2 * attempt)
    raise RuntimeError(f"giving up on {url} {params}")


def fetch_funding(symbol: str) -> pd.DataFrame:
    """Binance USD-M funding rate, 8h cadence, ascending, full history."""
    since = int(FUNDING_START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)
    rows = []
    while since < end_ms:
        d = _get(f"{FAPI}/fapi/v1/fundingRate", {"symbol": symbol, "startTime": since, "limit": 1000})
        if not d:
            break
        rows.extend(d)
        next_since = d[-1]["fundingTime"] + 1
        if next_since <= since:
            break
        since = next_since
        if len(d) < 1000:
            break
    df = pd.DataFrame(rows)
    df["funding_time"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True)
    df["funding_rate"] = df["fundingRate"].astype(float)
    return df[["funding_time", "funding_rate"]].drop_duplicates("funding_time").sort_values("funding_time")


def fetch_oi(symbol: str) -> pd.DataFrame:
    """
    Bybit v5 open interest, 1h cadence. Cursor-paginated, DESCENDING
    (newest first) -- walk backward from now until the cursor empties or
    we pass OI_START, per the empirically-verified behavior (see module
    docstring): unbounded startTime/endTime returns ~200 rows/page at true
    hourly granularity, newest first, `nextPageCursor` continues the walk.
    """
    rows = []
    cursor = None
    oldest_seen = END
    while oldest_seen > OI_START:
        params = {"category": "linear", "symbol": symbol, "intervalTime": "1h", "limit": 200}
        if cursor:
            params["cursor"] = unquote(cursor)
        d = _get(f"{BYBIT}/v5/market/open-interest", params)
        lst = (d.get("result") or {}).get("list") or []
        if not lst:
            break
        rows.extend(lst)
        oldest_seen = pd.Timestamp(int(lst[-1]["timestamp"]), unit="ms", tz="UTC")
        cursor = (d.get("result") or {}).get("nextPageCursor")
        if not cursor:
            break
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["oi_time"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms", utc=True)
    df["open_interest"] = df["openInterest"].astype(float)
    df = df[df["oi_time"] >= OI_START]
    return df[["oi_time", "open_interest"]].drop_duplicates("oi_time").sort_values("oi_time")


def main() -> None:
    report_rows = []
    for symbol in SYMBOLS:
        print(f"[{symbol}] fetching Binance funding rate (8h) ...", flush=True)
        funding = fetch_funding(symbol)
        f_path = DATA / f"{symbol}_funding_binance.csv"
        funding.to_csv(f_path, index=False)
        print(f"    {len(funding):,} funding obs, {funding['funding_time'].min()} -> {funding['funding_time'].max()}",
              flush=True)

        print(f"[{symbol}] fetching Bybit open interest (1h) ...", flush=True)
        oi = fetch_oi(symbol)
        oi_path = DATA / f"{symbol}_oi_bybit.csv"
        oi.to_csv(oi_path, index=False)
        print(f"    {len(oi):,} OI obs, {oi['oi_time'].min()} -> {oi['oi_time'].max()}", flush=True)

        # gap check: OI should be hourly; flag anything > 3h as a real gap
        gaps = oi["oi_time"].diff().dropna()
        bad = gaps[gaps > pd.Timedelta(hours=3)]
        print(f"    OI gaps > 3h: {len(bad)}" + (f" (worst: {bad.max()})" if len(bad) else ""), flush=True)

        report_rows.append(dict(
            symbol=symbol,
            funding_obs=len(funding), funding_start=str(funding["funding_time"].min()),
            funding_end=str(funding["funding_time"].max()),
            oi_obs=len(oi), oi_start=str(oi["oi_time"].min()) if not oi.empty else None,
            oi_end=str(oi["oi_time"].max()) if not oi.empty else None,
            oi_gaps_gt_3h=len(bad),
        ))

    rep = pd.DataFrame(report_rows)
    rep.to_csv(DATA / "crypto_funding_oi_report.csv", index=False)
    print("\nDone.")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
