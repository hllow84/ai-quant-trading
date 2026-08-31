#!/usr/bin/env python3
"""
download_crypto_momentum_universe.py — daily close panel for the crypto-
sector momentum-rotation generalisation test (STATE_OF_PLAY section 17).

UNIVERSE, every category stated (12 pairs, real Binance spot, via ccxt --
same tooling as scripts/download_crypto_ohlcv.py):

    BTC   -- benchmark/market-filter basis ONLY (excluded from ranking),
             the same role SPY plays in the original ETF universe: crypto's
             dominant, most commonly used "is the market risk-on or
             risk-off" gauge (~50%+ of total crypto market cap).
    ETH   -- L1 smart-contract platform (the leading one)
    SOL   -- L1 smart-contract platform (alternative, high-throughput)
    BNB   -- exchange-native L1 token
    ADA   -- L1 smart-contract platform (alternative)
    AVAX  -- L1 smart-contract platform (alternative)
    UNI   -- DeFi sector (leading DEX governance token)
    AAVE  -- DeFi sector (leading lending-protocol token)
    LINK  -- oracle / cross-chain infrastructure sector
    SAND  -- gaming / metaverse sector
    MANA  -- gaming / metaverse sector (a second name in the same sector,
             deliberately, so the sector isn't represented by only one coin)
    DOGE  -- meme-coin sector (large-cap, structurally distinct category --
             no smart-contract platform, no utility thesis, pure attention/
             liquidity-driven)

11 ranked instruments (all but BTC) across 6 distinct categories -- within
the task's stated 8-12 asset target. All are real Binance spot pairs
against USDT, pulled the same way (period="max" via ccxt paginated
fetch_ohlcv) as every other crypto pull in this repo.

DEFENSIVE LEG: no crypto equivalent of IEF (a genuinely different, lower-
volatility asset class with a clean multi-decade daily price history)
exists. Modelled explicitly as CASH_USD -- a synthetic constant-price
column (flat, 0% daily return, no yield). This is a stated, conservative
simplification: real USD or stablecoin holdings typically earn some yield,
so this UNDERSTATES the defensive leg's true return -- the safe direction
to be wrong in, consistent with this project's standing convention (state
12: "the safe direction to be wrong"). CASH_USD is added programmatically
below, not downloaded.

Depth verified via since=0 (not assumed): BTC/ETH 2017-08-17, BNB
2017-11-06, ADA 2018-04-17, LINK 2019-01-16, DOGE 2019-07-05, MANA
2020-08-06, SAND 2020-08-14, SOL 2020-08-11, UNI 2020-09-17, AVAX
2020-09-22, AAVE 2020-10-15. build_weights() already handles partial-
universe availability (a ticker absent from a signal date's ranking pool
if it has no data yet, exactly as XLRE/XLC were handled in the original
17-ETF study) -- no backfilling, no estimating.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import ccxt
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)

BENCHMARK = "BTC/USDT"
UNIVERSE = {
    "ETH": ("ETH/USDT", "L1 smart-contract platform (leading)"),
    "SOL": ("SOL/USDT", "L1 smart-contract platform (alt, high-throughput)"),
    "BNB": ("BNB/USDT", "exchange-native L1 token"),
    "ADA": ("ADA/USDT", "L1 smart-contract platform (alt)"),
    "AVAX": ("AVAX/USDT", "L1 smart-contract platform (alt)"),
    "UNI": ("UNI/USDT", "DeFi (DEX governance)"),
    "AAVE": ("AAVE/USDT", "DeFi (lending protocol)"),
    "LINK": ("LINK/USDT", "oracle / infrastructure"),
    "SAND": ("SAND/USDT", "gaming / metaverse"),
    "MANA": ("MANA/USDT", "gaming / metaverse"),
    "DOGE": ("DOGE/USDT", "meme-coin"),
}
START = pd.Timestamp("2017-08-17", tz="UTC")  # BTC/ETH inception; earlier than needed for the rest, harmless
END = pd.Timestamp.now(tz="UTC")
MAX_RETRIES = 5
LIMIT = 1000


def fetch_full_history(ex: ccxt.binance, symbol: str) -> pd.DataFrame:
    since = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)
    rows = []
    while since < end_ms:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                batch = ex.fetch_ohlcv(symbol, timeframe="1d", since=since, limit=LIMIT)
                break
            except Exception as e:
                print(f"    attempt {attempt}/{MAX_RETRIES} failed: {e}", flush=True)
                time.sleep(2 * attempt)
        else:
            raise RuntimeError(f"{symbol}: giving up after {MAX_RETRIES} retries at since={since}")
        if not batch:
            break
        rows.extend(batch)
        next_since = batch[-1][0] + 1
        if next_since <= since:
            break
        since = next_since
        if len(batch) < LIMIT:
            break
    df = pd.DataFrame(rows, columns=["open_time_ms", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset="open_time_ms").sort_values("open_time_ms").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["open_time_ms"], unit="ms", utc=True).dt.normalize()
    return df.set_index("date")["close"]


def main() -> None:
    ex = ccxt.binance({"enableRateLimit": True})
    ex.load_markets()

    closes = {}
    report_rows = []
    all_pairs = {"BTC": (BENCHMARK, "benchmark/market-filter basis, excluded from ranking")}
    all_pairs.update(UNIVERSE)

    for label, (symbol, category) in all_pairs.items():
        print(f"[{label}] fetching daily close, {symbol} ...", flush=True)
        s = fetch_full_history(ex, symbol)
        closes[label] = s
        report_rows.append(dict(ticker=label, symbol=symbol, category=category,
                                bars=len(s), start=str(s.index[0].date()), end=str(s.index[-1].date())))
        print(f"    {len(s):,} daily bars, {s.index[0].date()} -> {s.index[-1].date()}", flush=True)

    panel = pd.DataFrame(closes).sort_index()
    panel["CASH_USD"] = 1.0  # synthetic defensive leg: flat price, 0% daily return, no yield (conservative)
    panel.index = panel.index.tz_localize(None)  # match the tz-naive convention of every other panel in this repo
    panel.index.name = "date"
    out_path = DATA / "momentum_crypto_adjclose.csv"
    panel.to_csv(out_path)

    rep = pd.DataFrame(report_rows)
    rep.to_csv(DATA / "momentum_crypto_report.csv", index=False)
    print(f"\nSaved {out_path.name} ({len(panel):,} rows, {len(panel.columns)} columns incl. CASH_USD)")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
