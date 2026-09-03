"""Merge the EURUSD backfill Dukascopy pulls (scripts/download_eurusd_backfill.sh)
into clean bid/ask+spread datasets, same schema as every other repo M1 file so
research/gold_data.py loaders work unchanged:

    timestamp, datetime_utc, bid_open, bid_high, bid_low, bid_close,
    ask_open, ask_high, ask_low, ask_close, spread, volume

Outputs (split at the same 2017/2018 boundary every other ORB instrument uses):
    data/EURUSD_M1_2013_2017_spot_dukascopy.csv   (out-of-regime window)
    data/EURUSD_M1_2018_2025_spot_dukascopy.csv   (in-regime window)

Timezone: UTC (Dukascopy -utc 0). Spread = ask_close - bid_close, in price units
(EURUSD, so e.g. 0.00012 = 1.2 pips).
"""
import os
import sys
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = ["timestamp", "datetime_utc",
        "bid_open", "bid_high", "bid_low", "bid_close",
        "ask_open", "ask_high", "ask_low", "ask_close",
        "spread", "volume"]


def _load_side(src, years, price):
    frames = []
    for y in years:
        f = os.path.join(src, f"eurusd-m1-{price}-{y}.csv")
        if not os.path.exists(f) or os.path.getsize(f) == 0:
            print(f"  MISSING/EMPTY {os.path.basename(f)}")
            continue
        df = pd.read_csv(f)
        if df.empty:
            print(f"  EMPTY   {os.path.basename(f)}")
            continue
        frames.append(df)
        print(f"  loaded  {os.path.basename(f)}: {len(df):,} rows")
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset="timestamp").sort_values("timestamp")


def merge(src, years, out_path, lo_exp, hi_exp, min_year_rows):
    print(f"\n{'='*70}\neurusd {years[0]}-{years[-1]} -> {os.path.basename(out_path)}\n{'='*70}")
    print("BID:")
    bid = _load_side(src, years, "bid")
    print("ASK:")
    ask = _load_side(src, years, "ask")
    if bid is None or ask is None:
        print(f"ERROR: missing bid or ask; not writing {os.path.basename(out_path)}.")
        return False

    bid = bid.rename(columns={c: f"bid_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.rename(columns={c: f"ask_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.drop(columns=[c for c in ["volume"] if c in ask.columns])

    m = pd.merge(bid, ask, on="timestamp", how="inner")
    m["datetime_utc"] = pd.to_datetime(m["timestamp"], unit="ms", utc=True) \
        .dt.strftime("%Y-%m-%d %H:%M:%S+00:00")
    m["spread"] = (m["ask_close"] - m["bid_close"]).round(6)
    if "volume" not in m.columns:
        m["volume"] = 0.0
    m = m[COLS].sort_values("timestamp").reset_index(drop=True)

    lo, hi = m["bid_close"].min(), m["bid_close"].max()
    med_px, med_sp = m["bid_close"].median(), m["spread"].median()
    neg = int((m["spread"] < 0).sum())
    yr = pd.to_datetime(m["timestamp"], unit="ms", utc=True).dt.year
    per_year = yr.value_counts().sort_index().to_dict()
    print("\n=== SANITY ===")
    print(f"rows            : {len(m):,}")
    print(f"date range      : {m['datetime_utc'].iloc[0]}  ->  {m['datetime_utc'].iloc[-1]}")
    print(f"bid_close range : {lo:.5f} .. {hi:.5f}")
    print(f"spread min/med/max: {m['spread'].min():.6f} / {med_sp:.6f} / {m['spread'].max():.6f}"
          f"  ({1e4*med_sp:.2f} pips / {1e4*med_sp/med_px:.3f} bps)")
    print(f"negative spreads: {neg} ({100*neg/len(m):.3f}%)")
    print(f"rows per year   : {per_year}")

    problems = []
    if not (lo >= lo_exp and hi <= hi_exp):
        problems.append(f"price {lo:.4f}..{hi:.4f} outside band {lo_exp}-{hi_exp}")
    if neg > len(m) * 0.001:
        problems.append(f"{neg} negative spreads (>0.1%)")
    thin = [int(y) for y, n in per_year.items() if min_year_rows and n < min_year_rows]
    if thin:
        problems.append(f"thin years {thin} (< {min_year_rows} rows)")
    if problems:
        print("GATE FAILED: " + " | ".join(problems) + "  -- NOT writing " + os.path.basename(out_path))
        return False

    m.to_csv(out_path, index=False)
    print(f"WROTE {out_path}  ({os.path.getsize(out_path)/1e6:.0f} MB)")
    return True


def main():
    src = os.path.join(REPO, "data", "raw", "eurusd_bf", "download")
    ok = True
    ok &= merge(src, list(range(2013, 2018)),
                os.path.join(REPO, "data", "EURUSD_M1_2013_2017_spot_dukascopy.csv"),
                lo_exp=0.95, hi_exp=1.45, min_year_rows=300_000)
    ok &= merge(src, list(range(2018, 2026)),
                os.path.join(REPO, "data", "EURUSD_M1_2018_2025_spot_dukascopy.csv"),
                lo_exp=0.95, hi_exp=1.45, min_year_rows=300_000)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
