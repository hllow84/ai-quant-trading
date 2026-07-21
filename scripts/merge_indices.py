"""Merge per-year Dukascopy US index CFD M1 bid + ask CSVs into clean datasets
with a real bid/ask spread column. Same schema as the XAUUSD spot file, so
research/gold_data.py loaders work unchanged.

Instrument IDs come from the dukascopy-node Instrument enum (verified, not guessed):
    usatechidxusd -> Nasdaq-100 CFD   (probe 2024-03-04: 18,306)
    usa30idxusd   -> Dow-30 CFD       (probe 2024-03-04: 39,052)

Input : data/raw/idx_tmp/download/{instrument}-m1-{bid,ask}-{year}.csv
Output: data/{NAS100,US30}_M1_2018_2025_cfd_dukascopy.csv

Timezone: UTC (Dukascopy downloaded with -utc 0).
Spread  : ask_close - bid_close, in index points.
"""
import os
import sys
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "data", "raw", "idx_tmp", "download")
YEARS = range(2018, 2026)

# instrument id -> (output name, expected price band for the sanity check)
# Bands kept in sync with scripts/verify_indices.py — see the note there for why
# the NAS100 ceiling is 30,000: NDX genuinely traded to 26,255 in Oct 2025, so
# the old 25,000 bound flagged real data. This warning is advisory; the hard
# gate that can actually stop the pipeline lives in verify_indices.py.
INSTRUMENTS = {
    "usatechidxusd": ("NAS100", 5500, 30000),
    "usa30idxusd":   ("US30",  18000, 50000),
}


def load(instrument, price):
    frames = []
    for y in YEARS:
        f = os.path.join(SRC, f"{instrument}-m1-{price}-{y}.csv")
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
    return out.drop_duplicates(subset="timestamp").sort_values("timestamp")


def merge_one(instrument, name, lo_exp, hi_exp):
    print(f"\n{'='*66}\n{instrument} -> {name}\n{'='*66}")
    print("Loading BID files:")
    bid = load(instrument, "bid")
    print("Loading ASK files:")
    ask = load(instrument, "ask")
    if bid is None or ask is None:
        print(f"ERROR: missing bid or ask data for {instrument}; skipping.")
        return False

    bid = bid.rename(columns={c: f"bid_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.rename(columns={c: f"ask_{c}" for c in ["open", "high", "low", "close"]})
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
    med_px = m["bid_close"].median()
    med_sp = m["spread"].median()
    print("\n=== SANITY CHECK ===")
    print(f"rows               : {len(m):,}")
    print(f"date range (UTC)   : {m['datetime_utc'].min()}  ->  {m['datetime_utc'].max()}")
    print(f"bid_close range    : {lo:,.2f}  ->  {hi:,.2f}")
    print(f"spread min/med/max : {m['spread'].min():.4f} / {med_sp:.4f} / {m['spread'].max():.4f}  (index points)")
    print(f"median spread      : {1e4*med_sp/med_px:.3f} bps of price")
    neg = (m["spread"] < 0).sum()
    print(f"negative spreads   : {neg} ({100*neg/len(m):.3f}%)")
    if lo < lo_exp or hi > hi_exp:
        print(f"WARNING: price range outside expected {name} band ({lo_exp:,}-{hi_exp:,}).")
    else:
        print(f"OK: price range consistent with {name}.")

    out = os.path.join(REPO, "data", f"{name}_M1_2018_2025_cfd_dukascopy.csv")
    m.to_csv(out, index=False)
    print(f"\nWrote {out}")
    print(f"File size: {os.path.getsize(out)/1e6:.1f} MB")
    return True


def main():
    ok = [merge_one(i, *v) for i, v in INSTRUMENTS.items()]
    if not any(ok):
        sys.exit(1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
