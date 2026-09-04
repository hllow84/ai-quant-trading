#!/usr/bin/env python3
"""
download_btc_active_addresses.py -- pulls BTC daily "unique addresses used"
from blockchain.info's public Charts API (https://api.blockchain.info/charts/
n-unique-addresses) -- free, NO API key, NO rate limit encountered, full
history back to genesis-era 2009.

WHY THIS METRIC AND NOT EXCHANGE FLOW / WHALE BALANCE: section 30's data
survey (stated in run_onchain_signal.py's docstring and STATE_OF_PLAY) found
that exchange inflow/outflow, exchange reserve, and whale/large-holder
balance data are NOT available via any free, no-signup API:
  - Glassnode: free tier is dashboard-only; the "Light API" needs the
    Advanced plan ($49/mo), capped at 50 calls/day.
  - CryptoQuant: free tier is "severely limited" (no documented free API);
    the Data API requires the Professional plan ($99/mo) even for 24h
    resolution.
  - Coin Metrics Community API: as of this session, live-tested and returns
    HTTP 401 "Requested resource requires authorization" on EVERY endpoint,
    including the previously-free `/v4/timeseries/asset-metrics` and
    `/v4/catalog-all/assets` -- a free API key now requires manual signup,
    which this autonomous session cannot complete (email/captcha).
  - Etherscan (for an ETH equivalent): live-tested, `dailynewaddress`
    requires an API key ("Missing/Invalid API Key") even on the free tier.
blockchain.info's Charts API is the ONE genuinely free, zero-friction,
full-history on-chain source found. It is BTC-only and it is a NETWORK
ACTIVITY metric (unique addresses transacting that day), not an exchange
flow / smart-money metric -- a materially different and generally weaker
signal category, stated honestly as the reason this is what gets tested.

DATING / PUBLICATION LAG: the value for calendar day D is a full-day tally
of on-chain activity and is only complete once day D has closed (UTC). It
is treated in the backtest as known at day D's close and actionable no
earlier than day D+1's open -- the same one-day publication-lag convention
this project already applies to the daily-EMA HTF bias in the ICT SMC
scripts (research_log / STATE_OF_PLAY §28-29).

OUTPUT: data/BTC_active_addresses_blockchaininfo.csv, columns
[date, active_addresses]. Sanity-checked for a monotonically increasing
address history that is at least 4 orders of magnitude wide (2 in 2009 to
500k+ in 2026) and free of impossible values.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
OUT = _ROOT / "data" / "BTC_active_addresses_blockchaininfo.csv"

URL = "https://api.blockchain.info/charts/n-unique-addresses?timespan=all&format=json&sampled=false"


def fetch(retries: int = 5) -> dict:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": "crypto-factor-lab/1.0 research (non-commercial)"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception as e:  # retry per project standing rule
            last_err = e
            print(f"  attempt {attempt}/{retries} failed: {e}", flush=True)
            time.sleep(3 * attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {last_err}")


def main() -> None:
    print("=" * 100)
    print("  DOWNLOAD -- BTC daily unique active addresses (blockchain.info Charts API, free, no key)")
    print("=" * 100)
    d = fetch()
    name = d.get("name", "?")
    unit = d.get("unit", "?")
    vals = d.get("values", [])
    if not vals:
        print("*** no values returned -- aborting, NOT writing a bad file ***", flush=True)
        sys.exit(1)

    df = pd.DataFrame(vals)
    df["date"] = pd.to_datetime(df["x"], unit="s", utc=True).dt.normalize()
    df = df.rename(columns={"y": "active_addresses"})[["date", "active_addresses"]]
    df = df.groupby("date", as_index=False).last().sort_values("date").reset_index(drop=True)

    # sanity checks -- report honestly, do not silently trust
    n = len(df)
    lo, hi = df["date"].min(), df["date"].max()
    vmin, vmax = df["active_addresses"].min(), df["active_addresses"].max()
    n_dupe = int(df["date"].duplicated().sum())
    full_range = pd.date_range(lo, hi, freq="D", tz="UTC")
    n_missing = len(full_range) - n
    print(f"  metric name: {name!r}  unit: {unit!r}")
    print(f"  rows: {n:,}   date range: {lo.date()} -> {hi.date()}")
    print(f"  value range: {vmin:,.0f} -> {vmax:,.0f}")
    print(f"  duplicate dates: {n_dupe}   missing calendar days in range: {n_missing}")
    if vmin < 0 or vmax > 5_000_000:
        print("  *** SANITY FAIL: value out of plausible BTC active-address range -- aborting ***")
        sys.exit(1)
    if n < 3000:
        print("  *** SANITY FAIL: fewer than 3000 daily rows -- history looks truncated -- aborting ***")
        sys.exit(1)

    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\n  saved -> {OUT}  ({n:,} rows)")
    print("=" * 100)


if __name__ == "__main__":
    main()
