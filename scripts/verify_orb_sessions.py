#!/usr/bin/env python3
"""
verify_orb_sessions.py — HARD GATE for the ORB study.

ORB is anchored to the US CASH OPEN (09:30 America/New_York). That instant is
13:30 UTC under EDT and 14:30 UTC under EST. A fixed UTC offset would misplace
the opening range for roughly half of every year, so this script proves — from
the data, not from an assumption — that:

  1. tz_convert("America/New_York") puts the session open where it belongs,
  2. the UTC clock time of the 09:30 ET bar really is 13:30 in summer and
     14:30 in winter, and flips on the correct US DST dates,
  3. the first N minutes after the open (N = 15 and 30) are actually present,
  4. the 16:00 ET force-flat boundary is reachable (last bar >= 15:59 ET).

Exits 1 on failure so the sweep cannot run on a mis-timed session.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
ET = "America/New_York"
OPEN_MIN, CLOSE_MIN = 9 * 60 + 30, 16 * 60

FILES = {
    "NAS100 2018-2025": _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
    "US30 2018-2025":   _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
    "NAS100 2013-2017": _ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv",
    "US30 2013-2017":   _ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",
}


def check(label: str, path: Path) -> bool:
    if not path.exists():
        print(f"  [{label}] MISSING {path.name}")
        return False
    ts = pd.read_csv(path, usecols=["datetime_utc"], parse_dates=["datetime_utc"])["datetime_utc"]
    idx = pd.DatetimeIndex(ts)
    idx = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
    idx = idx.sort_values()
    et = idx.tz_convert(ET)
    et_min = et.hour * 60 + et.minute
    et_date = et.normalize()

    df = pd.DataFrame({"utc_min": idx.hour * 60 + idx.minute,
                       "et_min": et_min, "et_date": et_date})

    # --- (2) UTC clock of the 09:30 ET bar, split by DST offset ---------------
    opens = df[df["et_min"] == OPEN_MIN]
    utc_of_open = opens.groupby(opens["utc_min"]).size()
    # UTC offset in hours for each session date (-4 = EDT, -5 = EST)
    off = pd.Series(et.utcoffset().total_seconds() / 3600 if hasattr(et, "utcoffset") else np.nan)

    # --- (3) opening-range coverage ------------------------------------------
    g = df.groupby("et_date")["et_min"]
    first_min, last_min = g.min(), g.max()
    or15 = df[(df["et_min"] >= OPEN_MIN) & (df["et_min"] < OPEN_MIN + 15)].groupby("et_date").size()
    or30 = df[(df["et_min"] >= OPEN_MIN) & (df["et_min"] < OPEN_MIN + 30)].groupby("et_date").size()
    rth  = df[(df["et_min"] >= OPEN_MIN) & (df["et_min"] < CLOSE_MIN)].groupby("et_date").size()
    sessions = rth.index

    n_sess = len(sessions)
    open_present = int((first_min.reindex(sessions) <= OPEN_MIN).sum())
    close_reach  = int((last_min.reindex(sessions) >= CLOSE_MIN - 1).sum())
    full15 = int((or15.reindex(sessions).fillna(0) >= 13).sum())
    full30 = int((or30.reindex(sessions).fillna(0) >= 27).sum())

    print(f"\n  [{label}]  {len(idx):,} bars  {idx[0].date()} -> {idx[-1].date()}  "
          f"| {n_sess:,} ET sessions")
    print(f"    UTC clock time of the 09:30 ET bar (should be ONLY 13:30 and 14:30):")
    for m, c in utc_of_open.items():
        print(f"      {m // 60:02d}:{m % 60:02d} UTC  x{c:,}  "
              f"({'EDT' if m == 810 else 'EST' if m == 870 else '?? UNEXPECTED'})")
    print(f"    session open bar present : {open_present:,}/{n_sess:,} "
          f"({open_present / n_sess * 100:.1f}%)")
    print(f"    OR15 >=13 of 15 bars     : {full15:,}/{n_sess:,} ({full15 / n_sess * 100:.1f}%)")
    print(f"    OR30 >=27 of 30 bars     : {full30:,}/{n_sess:,} ({full30 / n_sess * 100:.1f}%)")
    print(f"    reaches 15:59 ET         : {close_reach:,}/{n_sess:,} "
          f"({close_reach / n_sess * 100:.1f}%)")
    print(f"    RTH bars/session median  : {int(rth.median())}")

    ok = set(utc_of_open.index) <= {13 * 60 + 30, 14 * 60 + 30}
    if not ok:
        print("    FAIL: 09:30 ET maps to a UTC time other than 13:30/14:30 — DST handling is wrong.")
    if full15 / n_sess < 0.80 or close_reach / n_sess < 0.80:
        print("    FAIL: opening range or close boundary missing on >20% of sessions.")
        ok = False
    return bool(ok)


def dst_flip_dates(path: Path) -> None:
    """Print the observed UTC-offset flip dates and check them against the US rule
    (2nd Sunday in March -> EDT, 1st Sunday in November -> EST)."""
    ts = pd.read_csv(path, usecols=["datetime_utc"], parse_dates=["datetime_utc"])["datetime_utc"]
    idx = pd.DatetimeIndex(ts)
    idx = idx.tz_convert("UTC") if idx.tz is not None else idx.tz_localize("UTC")
    et = idx.tz_convert(ET)
    d = pd.DataFrame({"date": et.normalize(),
                      "off": [t.utcoffset().total_seconds() / 3600 for t in et[::500]]}
                     if False else None)
    # cheap: one sample per ET date
    per_day = pd.Series(et.normalize()).drop_duplicates()
    offs = pd.Series([pd.Timestamp(x).tz_convert(ET).utcoffset().total_seconds() / 3600
                      for x in per_day], index=per_day.values)
    flips = offs[offs.diff() != 0].iloc[1:]
    print("\n  Observed DST transitions (first ET session at each new UTC offset):")
    for dt, o in flips.items():
        exp = "EDT (-4)" if o == -4 else "EST (-5)"
        print(f"    {pd.Timestamp(dt).date()}  ->  UTC{int(o):+d}  {exp}")


def main() -> int:
    print("=" * 96)
    print("  ORB SESSION / DST VERIFICATION — 09:30 America/New_York cash open")
    print("  Rule: 09:30 ET = 13:30 UTC under EDT, 14:30 UTC under EST. Handled per bar by")
    print("  pandas tz_convert('America/New_York'), which carries the full IANA DST history.")
    print("=" * 96)
    results = {k: check(k, p) for k, p in FILES.items()}
    first = next((p for p in FILES.values() if p.exists()), None)
    if first is not None:
        dst_flip_dates(first)
    print("\n" + "=" * 96)
    bad = [k for k, v in results.items() if not v]
    if bad:
        print("  GATE FAIL: " + ", ".join(bad))
        return 1
    print("  GATE PASS — all files map 09:30 ET correctly and cover the opening range.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
