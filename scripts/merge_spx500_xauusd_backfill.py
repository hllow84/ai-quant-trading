"""Merge the backfill Dukascopy pulls (scripts/download_spx500_xauusd_backfill.sh)
into clean bid/ask+spread datasets, same schema as the existing repo files so
research/gold_data.py loaders work unchanged:

    timestamp, datetime_utc, bid_open, bid_high, bid_low, bid_close,
    ask_open, ask_high, ask_low, ask_close, spread, volume

Outputs:
    data/SPX500_M1_2013_2025_cfd_dukascopy.csv   (usa500idxusd, spread in points)
    data/XAUUSD_M1_2003_2017_spot_dukascopy.csv  (xauusd, spread in $/oz)

Timezone: UTC (Dukascopy -utc 0). Spread = ask_close - bid_close.
"""
import os
import sys
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = ["timestamp", "datetime_utc",
        "bid_open", "bid_high", "bid_low", "bid_close",
        "ask_open", "ask_high", "ask_low", "ask_close",
        "spread", "volume"]


def _load_side(src, prefix, years, price):
    frames = []
    for y in years:
        f = os.path.join(src, f"{prefix}-m1-{price}-{y}.csv")
        if not os.path.exists(f):
            print(f"  MISSING {os.path.basename(f)}")
            continue
        if os.path.getsize(f) == 0:
            print(f"  EMPTY   {os.path.basename(f)} (pre-archive year)")
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


def merge(src, prefix, years, out_path, lo_exp, hi_exp, min_year_rows):
    print(f"\n{'='*70}\n{prefix} -> {os.path.basename(out_path)}\n{'='*70}")
    print("BID:")
    bid = _load_side(src, prefix, years, "bid")
    print("ASK:")
    ask = _load_side(src, prefix, years, "ask")
    if bid is None or ask is None:
        print(f"ERROR: missing bid or ask for {prefix}; not writing.")
        return False

    bid = bid.rename(columns={c: f"bid_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.rename(columns={c: f"ask_{c}" for c in ["open", "high", "low", "close"]})
    ask = ask.drop(columns=[c for c in ["volume"] if c in ask.columns])

    m = pd.merge(bid, ask, on="timestamp", how="inner")
    m["datetime_utc"] = pd.to_datetime(m["timestamp"], unit="ms", utc=True) \
        .dt.strftime("%Y-%m-%d %H:%M:%S+00:00")
    m["spread"] = (m["ask_close"] - m["bid_close"]).round(4)
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
    print(f"bid_close range : {lo:,.2f} .. {hi:,.2f}")
    print(f"spread min/med/max: {m['spread'].min():.4f} / {med_sp:.4f} / {m['spread'].max():.4f}"
          f"  ({1e4*med_sp/med_px:.3f} bps)")
    print(f"negative spreads: {neg} ({100*neg/len(m):.3f}%)")
    print(f"rows per year   : {per_year}")

    problems = []
    if not (lo >= lo_exp and hi <= hi_exp):
        problems.append(f"price {lo:.1f}..{hi:.1f} outside band {lo_exp}-{hi_exp}")
    if neg > len(m) * 0.001:
        problems.append(f"{neg} negative spreads (>0.1%)")
    # Hard gate only for 2013+ (the window the out-of-regime tests actually use
    # and where full M1 coverage is guaranteed). Pre-2013 gold M1 can be genuinely
    # thinner; report it, do not block on it. The first year is always exempt
    # (2003 gold starts in May; 2013 SPX ask starts in Sept).
    thin_hard = [int(y) for y, n in per_year.items()
                 if min_year_rows and n < min_year_rows
                 and int(y) >= 2013 and int(y) != years[0]]
    thin_soft = [int(y) for y, n in per_year.items()
                 if min_year_rows and n < min_year_rows
                 and int(y) < 2013 and int(y) != years[0]]
    if thin_soft:
        print(f"NOTE: thin pre-2013 years {thin_soft} (< {min_year_rows} rows) -- advisory only")
    if thin_hard:
        problems.append(f"thin years {thin_hard} (< {min_year_rows} rows)")
    if problems:
        print("GATE FAILED: " + " | ".join(problems) + "  -- NOT writing " + os.path.basename(out_path))
        return False

    m.to_csv(out_path, index=False)
    print(f"WROTE {out_path}  ({os.path.getsize(out_path)/1e6:.0f} MB)")
    return True


def main():
    ok = True
    ok &= merge(
        os.path.join(REPO, "data", "raw", "xau_bf", "download"),
        "xauusd", list(range(2003, 2018)),
        os.path.join(REPO, "data", "XAUUSD_M1_2003_2017_spot_dukascopy.csv"),
        lo_exp=300, hi_exp=2100, min_year_rows=150_000)
    ok &= merge(
        os.path.join(REPO, "data", "raw", "spx_bf", "download"),
        "usa500idxusd", list(range(2013, 2026)),
        os.path.join(REPO, "data", "SPX500_M1_2013_2025_cfd_dukascopy.csv"),
        lo_exp=1000, hi_exp=8000, min_year_rows=55_000)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
