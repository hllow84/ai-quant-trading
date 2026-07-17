"""Merge per-year Dukascopy XAUUSD M1 bid + ask CSVs into one clean spot dataset
with a real bid/ask spread column.

Input : data/raw/dukascopy_tmp/download/xauusd-m1-{bid,ask}-{year}.csv
        (columns: timestamp[ms epoch UTC], open, high, low, close, volume)
Output: data/XAUUSD_M1_2018_2025_spot_dukascopy.csv
        columns: timestamp, datetime_utc, bid_open, bid_high, bid_low, bid_close,
                 ask_open, ask_high, ask_low, ask_close, spread, volume

Timezone: UTC (Dukascopy downloaded with -utc 0).
Spread  : ask_close - bid_close, in USD price units per oz.
"""
import glob
import os
import sys
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "data", "raw", "dukascopy_tmp", "download")
OUT = os.path.join(REPO, "data", "XAUUSD_M1_2018_2025_spot_dukascopy.csv")

YEARS = range(2018, 2026)


def load(price):
    frames = []
    for y in YEARS:
        f = os.path.join(SRC, f"xauusd-m1-{price}-{y}.csv")
        if not os.path.exists(f):
            print(f"  MISSING {os.path.basename(f)}")
            continue
        df = pd.read_csv(f)
        if df.empty:
            print(f"  EMPTY   {os.path.basename(f)}")
            continue
        frames.append(df)
        print(f"  loaded  {os.path.basename(f)}: {len(df):,} rows")
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset="timestamp").sort_values("timestamp")
    return out


def main():
    print("Loading BID files:")
    bid = load("bid")
    print("Loading ASK files:")
    ask = load("ask")
    if bid is None or ask is None:
        print("ERROR: missing bid or ask data; aborting merge.")
        sys.exit(1)

    bid = bid.rename(columns={c: f"bid_{c}" for c in
                              ["open", "high", "low", "close"]})
    ask = ask.rename(columns={c: f"ask_{c}" for c in
                              ["open", "high", "low", "close"]})
    # keep volume from bid stream
    bid = bid.rename(columns={"volume": "volume"})
    ask = ask.drop(columns=[c for c in ["volume"] if c in ask.columns])

    m = pd.merge(bid, ask, on="timestamp", how="inner")
    m["datetime_utc"] = pd.to_datetime(m["timestamp"], unit="ms", utc=True)
    m["spread"] = (m["ask_close"] - m["bid_close"]).round(4)

    cols = ["timestamp", "datetime_utc",
            "bid_open", "bid_high", "bid_low", "bid_close",
            "ask_open", "ask_high", "ask_low", "ask_close",
            "spread", "volume"]
    m = m[cols].sort_values("timestamp").reset_index(drop=True)

    # ---- sanity checks ----
    lo, hi = m["bid_close"].min(), m["bid_close"].max()
    print("\n=== SANITY CHECK ===")
    print(f"rows              : {len(m):,}")
    print(f"date range (UTC)  : {m['datetime_utc'].min()}  ->  {m['datetime_utc'].max()}")
    print(f"bid_close range   : {lo:.2f}  ->  {hi:.2f}")
    print(f"spread  min/med/max: {m['spread'].min():.4f} / {m['spread'].median():.4f} / {m['spread'].max():.4f}")
    neg = (m["spread"] < 0).sum()
    print(f"negative spreads  : {neg} ({100*neg/len(m):.3f}%)")
    if not (1000 <= lo and hi <= 4000):
        print("WARNING: price range outside expected spot gold band (~1200-3500).")
    else:
        print("OK: price range consistent with SPOT gold (not futures).")

    m.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")
    print(f"File size: {os.path.getsize(OUT)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
