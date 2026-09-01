#!/usr/bin/env python3
"""
download_btcusdt_m1_binance.py — pull real Binance spot 1-MINUTE OHLCV for
BTC/USDT, 2018-01-01 -> now, to data/BTCUSDT_M1_2018_2025_binance.csv.

WHY THIS EXISTS
---------------
The ORB entry-filter study (STATE_OF_PLAY sec 10.x follow-up) needs M1 for
every instrument. The repo already has M1 for XAUUSD, NAS100, US30 but crypto
only exists at M15/H1/H4 (scripts/download_crypto_ohlcv.py deliberately skipped
M1). The user authorised a one-off M1 pull for BTCUSDT only (ETH skipped —
"same as BTC for trend").

SOURCE — exchange-native, matching the repo's crypto data policy
---------------------------------------------------------------
Primary: data.binance.vision — Binance's OWN published archive of monthly
1m kline zips. This is the authoritative exchange candle, not a resample, and
has no REST rate limit, so ~8.5 years of M1 pulls in a couple of minutes.
Fallback for any month the archive has not published yet (usually the current
month): ccxt fetch_ohlcv pagination against the live Binance REST API — the
exact tool scripts/download_crypto_ohlcv.py uses.

SCHEMA — identical to the existing crypto CSVs (download_crypto_ohlcv.py
::to_repo_frame), so run scripts consume it with no special-casing:
    datetime_utc (INDEX = bar CLOSE time = open_time + 1min), mid_open,
    mid_high, mid_low, mid_close, volume, spread
Binance kline timestamps are OPEN time; +1min shifts to close time so the row
is fully known at its stamp (repo convention, matches research/gold_data.py).

SPREAD — stated, not fabricated. Free historical per-bar bid/ask is not
available for crypto (fetchOHLCV is trade-based). Same convention as
download_crypto_ohlcv.py and STATE_OF_PLAY sec 12/13: a live top-of-book
spread measured fresh from Binance at pull time, applied as a CONSTANT bps
assumption across the series (price-scaled per bar). It is negligible next to
the 20 bps taker-fee that dominates crypto cost in run_sweep_crypto.py — that
asymmetry is reported, not hidden. If the live measure fails, fall back to the
value sec 13 already documents (~0.0013 bps for BTCUSDT).

GAPS: crypto trades 24/7/365, so any gap > 1.5x the bar is a real problem and
is verified explicitly at the end (same check as download_crypto_ohlcv.py).
"""
from __future__ import annotations

import io
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "BTCUSDT_M1_2018_2025_binance.csv"

SYMBOL_VISION = "BTCUSDT"
SYMBOL_CCXT = "BTC/USDT"
START = pd.Timestamp("2018-01-01", tz="UTC")
END = pd.Timestamp.now(tz="UTC")
BAR = pd.Timedelta(minutes=1)
FALLBACK_SPREAD_BPS = 0.0013     # STATE_OF_PLAY sec 13, BTCUSDT top-of-book, if live measure fails

VISION_MONTHLY = "https://data.binance.vision/data/spot/monthly/klines/{sym}/1m/{sym}-1m-{ym}.zip"
VISION_DAILY = "https://data.binance.vision/data/spot/daily/klines/{sym}/1m/{sym}-1m-{ymd}.zip"

# Binance kline CSV columns (no header in the archive files)
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
              "quote_vol", "n_trades", "taker_base", "taker_quote", "ignore"]


def _fetch_zip_csv(url: str) -> pd.DataFrame | None:
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                blob = resp.read()
            zf = zipfile.ZipFile(io.BytesIO(blob))
            name = zf.namelist()[0]
            with zf.open(name) as fh:
                df = pd.read_csv(fh, header=None, names=KLINE_COLS)
            return df
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"    {url.rsplit('/', 1)[-1]}: HTTP {e.code}, retry {attempt}/3", flush=True)
            time.sleep(2 * attempt)
        except Exception as e:  # noqa: BLE001
            print(f"    {url.rsplit('/', 1)[-1]}: {e}, retry {attempt}/3", flush=True)
            time.sleep(2 * attempt)
    return None


def _month_range(start: pd.Timestamp, end: pd.Timestamp):
    m = pd.Timestamp(year=start.year, month=start.month, day=1, tz="UTC")
    while m <= end:
        yield m
        m = (m + pd.offsets.MonthBegin(1)).tz_localize(None).tz_localize("UTC") \
            if m.tz is None else (m + pd.offsets.MonthBegin(1))


def fetch_from_vision() -> tuple[pd.DataFrame, list[str]]:
    frames, missing_months = [], []
    for m in _month_range(START, END):
        ym = m.strftime("%Y-%m")
        df = _fetch_zip_csv(VISION_MONTHLY.format(sym=SYMBOL_VISION, ym=ym))
        if df is None:
            # try that month day-by-day (covers the current, not-yet-archived month)
            day_frames = []
            d = m
            nxt = m + pd.offsets.MonthBegin(1)
            while d < min(nxt, END + pd.Timedelta(days=1)):
                ddf = _fetch_zip_csv(VISION_DAILY.format(sym=SYMBOL_VISION, ymd=d.strftime("%Y-%m-%d")))
                if ddf is not None:
                    day_frames.append(ddf)
                d += pd.Timedelta(days=1)
            if day_frames:
                df = pd.concat(day_frames, ignore_index=True)
                print(f"  {ym}: {len(df):,} rows (daily files)", flush=True)
            else:
                missing_months.append(ym)
                print(f"  {ym}: MISSING from archive -> ccxt fallback", flush=True)
                continue
        else:
            print(f"  {ym}: {len(df):,} rows", flush=True)
        frames.append(df)
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), missing_months


def fetch_from_ccxt(since_ms: int) -> pd.DataFrame:
    import ccxt  # local import: only needed for the tail

    ex = ccxt.binance({"enableRateLimit": True})
    end_ms = int(END.timestamp() * 1000)
    rows, cur = [], since_ms
    while cur < end_ms:
        for attempt in range(1, 6):
            try:
                batch = ex.fetch_ohlcv(SYMBOL_CCXT, timeframe="1m", since=cur, limit=1000)
                break
            except Exception as e:  # noqa: BLE001
                print(f"    ccxt attempt {attempt}/5: {e}", flush=True)
                time.sleep(2 * attempt)
        else:
            raise RuntimeError(f"ccxt gave up at since={cur}")
        if not batch:
            break
        rows.extend(batch)
        nxt = batch[-1][0] + 1
        if nxt <= cur:
            break
        cur = nxt
        if len(batch) < 1000:
            break
    return pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume"])


def measure_live_spread_bps() -> float:
    try:
        import ccxt

        ob = ccxt.binance({"enableRateLimit": True}).fetch_order_book(SYMBOL_CCXT, limit=5)
        bid, ask = ob["bids"][0][0], ob["asks"][0][0]
        return (ask - bid) / ((ask + bid) / 2) * 1e4
    except Exception as e:  # noqa: BLE001
        print(f"  live spread measure failed ({e}); using documented {FALLBACK_SPREAD_BPS} bps", flush=True)
        return FALLBACK_SPREAD_BPS


def main() -> None:
    print(f"BTCUSDT M1  {START.date()} -> {END.date()}  (target {OUT.name})", flush=True)
    print("Primary source: data.binance.vision monthly 1m kline archive\n", flush=True)

    vision, missing = fetch_from_vision()
    if vision.empty:
        raise SystemExit("archive returned nothing — aborting")

    vision = vision[["open_time", "open", "high", "low", "close", "volume"]].copy()
    # Binance switched open_time from milliseconds to MICROSECONDS in some 2025+
    # archive files. Convert PER ROW (a whole-column test would rescale the ms
    # rows too once a single us row is present — the bug that silently dropped
    # 2018-2024 on the first run).
    ot = pd.to_numeric(vision["open_time"], errors="coerce")
    ot = ot.where(ot < 1e15, ot / 1000.0)   # us -> ms only where needed
    vision["open_time"] = ot.round().astype("int64")
    # A handful of 2018 archive rows carry a non-minute-aligned open_time
    # (e.g. ...814789 ms). Binance 1m klines are minute-aligned by definition;
    # drop the malformed rows rather than emit fractional-second bar stamps.
    misaligned = (vision["open_time"] % 60_000) != 0
    if misaligned.any():
        print(f"  dropping {int(misaligned.sum())} non-minute-aligned archive rows", flush=True)
        vision = vision.loc[~misaligned]

    have_until_ms = int(vision["open_time"].max())
    tail = pd.DataFrame()
    if missing or (END.timestamp() * 1000 - have_until_ms) > 2 * 60_000:
        print(f"\nFilling tail via ccxt from {pd.to_datetime(have_until_ms + 60_000, unit='ms', utc=True)}",
              flush=True)
        tail = fetch_from_ccxt(have_until_ms + 60_000)
        print(f"  ccxt tail: {len(tail):,} rows", flush=True)

    raw = pd.concat([vision, tail], ignore_index=True) if not tail.empty else vision
    raw = raw.drop_duplicates(subset="open_time").sort_values("open_time").reset_index(drop=True)

    idx = pd.to_datetime(raw["open_time"], unit="ms", utc=True) + BAR
    out = pd.DataFrame({
        "mid_open": pd.to_numeric(raw["open"]).to_numpy(),
        "mid_high": pd.to_numeric(raw["high"]).to_numpy(),
        "mid_low": pd.to_numeric(raw["low"]).to_numpy(),
        "mid_close": pd.to_numeric(raw["close"]).to_numpy(),
        "volume": pd.to_numeric(raw["volume"]).to_numpy(),
    }, index=idx)
    out.index.name = "datetime_utc"
    out = out[(out.index > START) & (out.index <= END + BAR)]

    spread_bps = measure_live_spread_bps()
    out["spread"] = out["mid_close"] * (spread_bps / 1e4)

    # ---- gap check (24/7 series) ----
    gaps = out.index.to_series().diff().dropna()
    big = gaps[gaps > 1.5 * BAR]
    print(f"\nRows: {len(out):,}   {out.index[0]} -> {out.index[-1]}", flush=True)
    print(f"spread assumption: {spread_bps:.4f} bps  (median ${out['spread'].median():.5f})", flush=True)
    print(f"gaps > 1.5x bar: {len(big)}", flush=True)
    if len(big):
        print("  largest:", flush=True)
        for ts, g in big.sort_values(ascending=False).head(10).items():
            print(f"    before {ts}: {g}", flush=True)
    px = out["mid_close"]
    print(f"price range: ${px.min():,.2f} - ${px.max():,.2f}", flush=True)
    assert 3000 < px.min() and px.max() < 250_000, "BTC price sanity check failed"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT)
    print(f"\nwrote {OUT}  ({OUT.stat().st_size / 1e6:.0f} MB)", flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
