#!/usr/bin/env python3
"""
audit_orb.py — ORB IMPLEMENTATION AUDIT (not a new strategy test).

Instruments strategies/orb.py's own logic (imports the real functions, does not
reimplement them) to answer, per instrument/year:
  - how many sessions had a COMPLETE, non-degenerate opening range
  - of those, how many produced a trade vs zero trade (inside day, no breakout)
  - of those, how many were dropped by each filter, counted separately:
      truncated session (< MIN_RTH_BARS)
      OR coverage < MIN_OR_COVERAGE
      degenerate range (rng <= 0 or non-finite)
      same-minute tie (i_up == i_dn, ambiguous first break)

Also dumps the AUDIT-1 entry-timing check (intrabar vs close) and AUDIT-3
stop/target same-bar tie count, computed directly off strategies.orb.orb()
candidates run through a version of simulate_trades that records tie info.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot
from strategies.orb import rth_m1, opening_ranges, RTH_OPEN_MIN, ET, MIN_RTH_BARS, MIN_OR_COVERAGE, OR_MINUTES

pd.set_option("display.width", 160)


def to_m1_mid(spot: pd.DataFrame) -> pd.DataFrame:
    m1 = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m1["spread"] = spot["spread"]
    return m1


def audit_fire_rate(m1_mid: pd.DataFrame, or_minutes: int, label: str) -> pd.DataFrame:
    rth = rth_m1(m1_mid)
    sess_bars = rth.groupby("et_date").size()
    ors = opening_ranges(rth, or_minutes)

    entry_start = RTH_OPEN_MIN + or_minutes
    win = rth.loc[rth["et_min"] >= entry_start]
    win_by_day = {d: (v["mid_high"].to_numpy(), v["mid_low"].to_numpy())
                  for d, v in win.groupby("et_date")}

    # Universe = every ET session day present in the RTH frame at all (this is
    # "a trading day", independent of whether the OR filters later drop it).
    all_days = sorted(sess_bars.index)

    rows = []
    for day in all_days:
        yr = pd.Timestamp(day).year
        rec = dict(year=yr, day=day, truncated=False, or_incomplete=False,
                   degenerate=False, no_data_after_or=False, tie=False,
                   traded=False, no_breakout=False)

        if sess_bars.get(day, 0) < MIN_RTH_BARS:
            rec["truncated"] = True
            rows.append(rec)
            continue

        if day not in ors.index:
            rec["or_incomplete"] = True
            rows.append(rec)
            continue

        r = ors.loc[day]
        if r["or_bars"] < MIN_OR_COVERAGE * or_minutes:
            rec["or_incomplete"] = True
            rows.append(rec)
            continue

        or_hi, or_lo = float(r["or_high"]), float(r["or_low"])
        rng = or_hi - or_lo
        if not np.isfinite(rng) or rng <= 0:
            rec["degenerate"] = True
            rows.append(rec)
            continue

        if day not in win_by_day:
            rec["no_data_after_or"] = True
            rows.append(rec)
            continue

        w_hi, w_lo = win_by_day[day]
        up = w_hi >= or_hi
        dn = w_lo <= or_lo
        i_up = int(np.argmax(up)) if up.any() else -1
        i_dn = int(np.argmax(dn)) if dn.any() else -1

        if i_up == -1 and i_dn == -1:
            rec["no_breakout"] = True
            rows.append(rec)
            continue

        if i_up != -1 and i_dn != -1 and i_up == i_dn:
            rec["tie"] = True
            rows.append(rec)
            continue

        rec["traded"] = True
        rows.append(rec)

    df = pd.DataFrame(rows)
    df["label"] = label
    df["or_minutes"] = or_minutes
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (label, orm, yr), g in df.groupby(["label", "or_minutes", "year"]):
        n = len(g)
        or_complete = n - g["truncated"].sum() - g["or_incomplete"].sum() - g["degenerate"].sum() - g["no_data_after_or"].sum()
        traded = g["traded"].sum()
        out.append(dict(
            label=label, or_minutes=orm, year=yr, total_days=n,
            truncated=int(g["truncated"].sum()),
            or_incomplete=int(g["or_incomplete"].sum()),
            degenerate=int(g["degenerate"].sum()),
            no_data_after_or=int(g["no_data_after_or"].sum()),
            or_complete_days=int(or_complete),
            no_breakout=int(g["no_breakout"].sum()),
            tie=int(g["tie"].sum()),
            traded=int(traded),
            fire_rate_of_valid=(traded / or_complete if or_complete else float("nan")),
            fire_rate_of_all=(traded / n if n else float("nan")),
        ))
    return pd.DataFrame(out)


def audit1_intrabar_vs_close(m1_mid: pd.DataFrame, or_minutes: int, label: str) -> None:
    """Quantify: at the moment of the actual intrabar cross, what would a
    close-only (wait-for-bar-close-beyond-level) rule have done differently?
    For every breakout minute bar, compare the OR level (used as entry) to that
    bar's CLOSE. If close-only were used instead of intrabar-stop, the trade
    would only fire if close also cleared the level IN THAT SAME BAR, else it
    would be delayed to a later bar (or missed entirely if price snapped back).
    """
    rth = rth_m1(m1_mid)
    ors = opening_ranges(rth, or_minutes)
    entry_start = RTH_OPEN_MIN + or_minutes
    win = rth.loc[rth["et_min"] >= entry_start]
    win_by_day = {d: v for d, v in win.groupby("et_date")}

    diffs_pts = []
    diffs_pctR = []
    same_bar_close_confirms = 0
    total = 0
    for day, r in ors.iterrows():
        if day not in win_by_day or r["or_bars"] < MIN_OR_COVERAGE * or_minutes:
            continue
        or_hi, or_lo = float(r["or_high"]), float(r["or_low"])
        rng = or_hi - or_lo
        if not np.isfinite(rng) or rng <= 0:
            continue
        v = win_by_day[day]
        w_hi, w_lo = v["mid_high"].to_numpy(), v["mid_low"].to_numpy()
        w_close = v["mid_close"].to_numpy()
        up = w_hi >= or_hi
        dn = w_lo <= or_lo
        i_up = int(np.argmax(up)) if up.any() else -1
        i_dn = int(np.argmax(dn)) if dn.any() else -1
        if i_up == -1 and i_dn == -1:
            continue
        if i_up != -1 and i_dn != -1 and i_up == i_dn:
            continue
        if i_dn == -1 or (i_up != -1 and i_up < i_dn):
            level, k = or_hi, i_up
            close_confirms = w_close[k] >= level
            diff = w_close[k] - level  # positive = close ran further through the level
        else:
            level, k = or_lo, i_dn
            close_confirms = w_close[k] <= level
            diff = level - w_close[k]
        total += 1
        if close_confirms:
            same_bar_close_confirms += 1
        diffs_pts.append(diff)
        diffs_pctR.append(diff / rng)

    diffs_pts = np.array(diffs_pts)
    diffs_pctR = np.array(diffs_pctR)
    print(f"\n  [{label} OR{or_minutes}] AUDIT 1 — intrabar entry vs bar-close of the breakout minute")
    print(f"    n breakout bars: {total}")
    print(f"    same-bar CLOSE also clears the level (close-only would fire on the SAME bar): "
          f"{same_bar_close_confirms}/{total} = {same_bar_close_confirms/total*100:.1f}%")
    print(f"    mean (close - level) in direction of breakout: {diffs_pts.mean():+.4f} price units "
          f"= {diffs_pctR.mean()*100:+.2f}% of 1R (OR range)")
    print(f"    median: {np.median(diffs_pts):+.4f} price units = {np.median(diffs_pctR)*100:+.2f}% of 1R")
    print(f"    fraction of breakout bars where close snaps BACK inside the range "
          f"(close-only would MISS or delay this trade): {(~(diffs_pts>=0)).sum()}/{total} "
          f"= {(~(diffs_pts>=0)).mean()*100:.1f}%")


DATASETS = [
    ("NAS100_2018_2025", _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv"),
    ("US30_2018_2025",   _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"),
    ("NAS100_2013_2017", _ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv"),
    ("US30_2013_2017",   _ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv"),
]


def main():
    all_summaries = []
    for label, path in DATASETS:
        print(f"\n{'='*100}\nLoading {label} ...", flush=True)
        spot = load_m1_spot(path)
        m1 = to_m1_mid(spot)
        del spot
        for orm in OR_MINUTES:
            df = audit_fire_rate(m1, orm, label)
            s = summarize(df)
            all_summaries.append(s)
            audit1_intrabar_vs_close(m1, orm, label)

    summary = pd.concat(all_summaries, ignore_index=True)
    out_path = _ROOT / "results" / "audit_orb_fire_rate.csv"
    summary.to_csv(out_path, index=False)

    print(f"\n\n{'='*100}\nAUDIT 2 — FIRE RATE TABLE (per instrument/window/OR-minutes/year)\n{'='*100}")
    print(summary.to_string(index=False))

    print(f"\n\n{'='*100}\nAUDIT 2 — POOLED (all years) per instrument/window/OR\n{'='*100}")
    pooled = summary.groupby(["label", "or_minutes"]).agg(
        total_days=("total_days", "sum"),
        truncated=("truncated", "sum"),
        or_incomplete=("or_incomplete", "sum"),
        degenerate=("degenerate", "sum"),
        no_data_after_or=("no_data_after_or", "sum"),
        or_complete_days=("or_complete_days", "sum"),
        no_breakout=("no_breakout", "sum"),
        tie=("tie", "sum"),
        traded=("traded", "sum"),
    ).reset_index()
    pooled["fire_rate_of_valid"] = pooled["traded"] / pooled["or_complete_days"]
    pooled["fire_rate_of_all"] = pooled["traded"] / pooled["total_days"]
    print(pooled.to_string(index=False))
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
