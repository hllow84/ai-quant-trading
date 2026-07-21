#!/usr/bin/env python3
"""Build the six H1 base files for the diversified index-trend basket.

Two sources, ONE output schema, so every instrument is treated identically:

  DOWNLOADED (4)  GER40, UK100, JP225, SPX500
        per-year H1 bid + ask CSVs -> merged with a real spread column.

  DERIVED (2)     NAS100, US30
        aggregated down from the existing M1 files (M1 -> H1). Re-downloading
        them at H1 would have been wasteful, and aggregating is exact.

Why every instrument is put on H1 rather than leaving NAS100/US30 at M1:
the basket must be apples-to-apples. If two of six members resolved trades on
M1 while the rest resolved on H1, their fill realism would differ and the
per-instrument comparison inside the basket would be biased. Same base
resolution everywhere.

Timestamp convention: BAR-OPEN (Dukascopy native, matching the M1 files), so
research/gold_data.py loaders work unchanged. A bar stamped T covers [T, T+1h),
so resolving a signal timestamped T from bar T onward is strictly forward-looking
-- no look-ahead.

Output: data/{NAME}_H1_2018_2025_cfd_dukascopy.csv
"""
import os
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "data", "raw", "basket_tmp", "download")
YEARS = range(2018, 2026)

OUT_COLS = ["timestamp", "datetime_utc",
            "bid_open", "bid_high", "bid_low", "bid_close",
            "ask_open", "ask_high", "ask_low", "ask_close",
            "spread", "volume"]

# id -> (output name, expected price lo, hi). Bands are generous on purpose:
# they catch a wrong instrument or a decimal error, not a legitimate new high.
DOWNLOADED = {
    "deuidxeur":    ("GER40",  8000, 30000),
    "gbridxgbp":    ("UK100",  4000, 12000),
    "jpnidxjpy":    ("JP225", 14000, 60000),
    "usa500idxusd": ("SPX500", 1800,  9000),
}

# existing M1 file -> (output name, lo, hi)
DERIVED = {
    "NAS100_M1_2018_2025_cfd_dukascopy.csv": ("NAS100", 5500, 30000),
    "US30_M1_2018_2025_cfd_dukascopy.csv":   ("US30",  18000, 50000),
}


def _finish(m, name, lo_exp, hi_exp):
    """Shared tail: spread, column order, sanity print, write."""
    m["datetime_utc"] = pd.to_datetime(m["timestamp"], unit="ms", utc=True)
    m["spread"] = (m["ask_close"] - m["bid_close"]).round(4)
    m = m[OUT_COLS].sort_values("timestamp").reset_index(drop=True)

    # Fail LOUDLY on epoch-unit corruption. A silent unit error once produced 1970
    # dates that still looked like a valid file; the sweep would have run on garbage.
    yr_lo, yr_hi = m["datetime_utc"].dt.year.min(), m["datetime_utc"].dt.year.max()
    if yr_lo < 2015 or yr_hi > 2030:
        raise ValueError(
            f"{name}: timestamps decode to years {yr_lo}-{yr_hi}, expected 2018-2025. "
            "This is an epoch-unit bug (ms vs us vs ns), not a data problem."
        )

    lo, hi = m["bid_close"].min(), m["bid_close"].max()
    med_px, med_sp = m["bid_close"].median(), m["spread"].median()
    neg = int((m["spread"] < 0).sum())
    print(f"  rows            : {len(m):,}")
    print(f"  range (UTC)     : {m['datetime_utc'].min()} -> {m['datetime_utc'].max()}")
    print(f"  bid_close range : {lo:,.2f} -> {hi:,.2f}")
    print(f"  spread median   : {med_sp:.4f} pts = {1e4*med_sp/med_px:.3f} bps of price")
    print(f"  negative spreads: {neg} ({100*neg/max(len(m),1):.3f}%)")
    if lo < lo_exp or hi > hi_exp:
        print(f"  WARNING: price outside expected {name} band ({lo_exp:,}-{hi_exp:,}).")
    else:
        print(f"  OK: price range consistent with {name}.")

    out = os.path.join(REPO, "data", f"{name}_H1_2018_2025_cfd_dukascopy.csv")
    m.to_csv(out, index=False)
    print(f"  wrote {out}  ({os.path.getsize(out)/1e6:.1f} MB)")
    return True


def load_side(instrument, price):
    frames = []
    for y in YEARS:
        f = os.path.join(SRC, f"{instrument}-h1-{price}-{y}.csv")
        if not os.path.exists(f):
            print(f"  MISSING {os.path.basename(f)}")
            continue
        df = pd.read_csv(f)
        if df.empty:
            print(f"  EMPTY   {os.path.basename(f)}")
            continue
        frames.append(df)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    return out.drop_duplicates(subset="timestamp").sort_values("timestamp")


def merge_downloaded(instrument, name, lo_exp, hi_exp):
    print(f"\n{'='*70}\n{instrument} -> {name}  (downloaded H1)\n{'='*70}")
    bid, ask = load_side(instrument, "bid"), load_side(instrument, "ask")
    if bid is None or ask is None:
        print(f"  ERROR: missing bid or ask for {instrument}; skipping.")
        return False
    bid = bid.rename(columns={c: f"bid_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.rename(columns={c: f"ask_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.drop(columns=[c for c in ["volume"] if c in ask.columns])
    return _finish(pd.merge(bid, ask, on="timestamp", how="inner"), name, lo_exp, hi_exp)


def derive_from_m1(fname, name, lo_exp, hi_exp):
    print(f"\n{'='*70}\n{fname} -> {name}  (derived M1 -> H1)\n{'='*70}")
    path = os.path.join(REPO, "data", fname)
    if not os.path.exists(path):
        print(f"  ERROR: source M1 file missing: {path}")
        return False

    df = pd.read_csv(path, usecols=["datetime_utc", "bid_open", "bid_high", "bid_low",
                                    "bid_close", "ask_open", "ask_high", "ask_low",
                                    "ask_close", "spread", "volume"],
                     parse_dates=["datetime_utc"])
    df = df.set_index("datetime_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    # label='left', closed='left' keeps the BAR-OPEN convention of the source M1
    # file, so the derived H1 matches the downloaded H1 exactly in meaning.
    r = df.resample("1h", label="left", closed="left")
    h1 = pd.DataFrame({
        "bid_open": r["bid_open"].first(), "bid_high": r["bid_high"].max(),
        "bid_low": r["bid_low"].min(),     "bid_close": r["bid_close"].last(),
        "ask_open": r["ask_open"].first(), "ask_high": r["ask_high"].max(),
        "ask_low": r["ask_low"].min(),     "ask_close": r["ask_close"].last(),
        "volume": r["volume"].sum(),
    }).dropna(subset=["bid_close"])

    h1 = h1.reset_index().rename(columns={"datetime_utc": "dt"})
    # as_unit("ns") is REQUIRED: pandas 2.x infers datetime64[us] from this CSV, so a
    # bare .astype("int64") yields MICROseconds. Dividing that by 1e6 produced seconds,
    # which read back as 1970 dates. Pin the unit rather than trusting the inferred one.
    h1["timestamp"] = pd.DatetimeIndex(h1["dt"]).tz_convert("UTC").as_unit("ns").astype("int64") // 10**6
    print(f"  aggregated {len(df):,} M1 bars -> {len(h1):,} H1 bars")
    return _finish(h1, name, lo_exp, hi_exp)


def main():
    ok = []
    for inst, v in DOWNLOADED.items():
        ok.append(merge_downloaded(inst, *v))
    for fname, v in DERIVED.items():
        ok.append(derive_from_m1(fname, *v))
    print(f"\n{'='*70}\n  {sum(ok)}/{len(ok)} instruments written.\n{'='*70}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
