#!/usr/bin/env python3
"""
scripts/orderbook_capture.py -- PREPARATORY INFRASTRUCTURE (not yet deployed,
not yet collecting). Follow-up to section 30 (research_log / STATE_OF_PLAY):
continuous L2 order-book + trade-flow capture for BTCUSDT (and, configurably,
ETHUSDT) via Binance's free, no-API-key public websocket market-data streams.

WHY THIS EXISTS NOW: section 30 found that free REST-based on-chain data
(exchange flow, whale balances) doesn't exist without a paid subscription,
and that even the weaker free proxy (active addresses) trades at most 1
signal/day. Order-book microstructure is a genuinely different, faster
signal category this project has never captured — but building the
BACKTEST requires HISTORY, and no free vendor sells historical L2 book data
for crypto. The only way to get it is to capture it forward from today, on
an always-on host. This script IS that capture tool. It cannot be run to
completion in this project's normal working environment: background
processes here die when the terminal session ends (this project's own
standing rule -- see feedback_background_tasks memory / CLAUDE.md), and a
laptop that sleeps or reboots loses the connection. A genuine multi-week
capture needs a real always-on host — see
docs/orderbook_capture_vps_deployment.md for a $5/month VPS walkthrough.
This script was smoke-tested against the live Binance stream (see the run
log referenced in STATE_OF_PLAY §30 follow-up) to confirm the message
format and file output are correct; it has NOT been left running, and no
data has been collected yet.

======================================================================
PRE-REGISTERED METRIC DEFINITIONS -- stated NOW, before any order-book
history exists, so a future backtest cannot tune these after seeing a
result. Whatever gets tested later must use these definitions, or state
explicitly and up front why a different one is used instead.
======================================================================

1. DEPTH-N ORDER BOOK IMBALANCE (OBI_N):
       OBI_N(t) = (sum(bid_qty[1..N]) - sum(ask_qty[1..N]))
                  / (sum(bid_qty[1..N]) + sum(ask_qty[1..N]))
   Range [-1, +1]. Positive = book is bid-heavy (more resting buy interest
   near the touch than sell interest). Computed at N = 10 AND N = 20 (the
   full depth Binance's `depth20@100ms` stream provides) so a later study
   can compare both without a second capture. This is the standard
   book-pressure metric in the market-microstructure literature (e.g. Cont,
   Kukanov & Stoikov 2014, "The Price Impact of Order Book Events").

2. NOTIONAL-BAND OBI (robust to tick-size / level-count gaming):
       OBI_band(t) using cumulative bid/ask QUANTITY within +/-25 bps of the
       mid price (BAND_BPS = 25, stated up front), same imbalance formula
       as (1). A price-band metric is less sensitive to how many discrete
       price levels happen to sit within that band.

3. TRADE-FLOW IMBALANCE (TFI), aggressor side, from the aggTrade stream:
       TFI(t, W) = (buyVol - sellVol) / (buyVol + sellVol)
       over a trailing window W = 60 seconds (stated up front). Binance's
       aggTrade `m` field is `true` when the buyer is the MAKER (i.e. a
       sell-initiated/aggressor trade) and `false` when the buyer is the
       TAKER (buy-initiated) -- sellVol accumulates on m=true, buyVol on
       m=false.

4. SAMPLING & STORAGE:
       Raw depth snapshots are captured at the stream's native cadence
       (Binance pushes `depth20@100ms` roughly every 100ms) and raw trade
       prints are captured tick-by-tick -- both persisted verbatim
       (gzip-compressed JSON Lines, one file per UTC day per stream) so
       nothing is thrown away. IN PARALLEL, the three metrics above are
       aggregated to ONE-SECOND bars and written to a compact CSV
       (`features_1s_<SYMBOL>_<date>.csv`) for actual future backtest use.
       A 1-second feature bar (not raw sub-second ticks) is the unit a
       later study would test, because it can be honestly aggregated
       further to this project's existing minimum tested bar (M1) without
       any look-ahead, and sub-100ms execution realism is a separate,
       harder claim this project has not made and is not making here.

5. HYPOTHESISED DIRECTION (pre-registered, NOT to be flipped after seeing
   collected data): OBI(t) > 0 (bid-heavy) is read as short-term buy
   pressure, hypothesised bullish for the next few M1 bars; OBI(t) < 0 is
   read as bearish. TFI is read the same way (positive = bullish). NO
   entry threshold is fixed yet -- picking one now would be a number
   invented with no distributional data behind it. The honest plan is: the
   FIRST real capture batch is used ONLY to compute the empirical
   distribution of OBI/TFI (e.g. a threshold at the trailing 95th
   percentile of |OBI|), decided from that distribution BEFORE any P&L is
   computed on a second, later batch -- an explicit train/test split in
   time, not a threshold chosen to maximise backtested returns.

======================================================================
USAGE (local smoke test; see the VPS doc for real deployment)
======================================================================
    python scripts/orderbook_capture.py --symbols btcusdt --out data/orderbook_capture
    (Ctrl-C to stop; SIGTERM is handled the same way for systemd.)
"""
from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import logging
import signal
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import websockets

DEPTH_LEVELS_N = (10, 20)      # pre-registered OBI depths
BAND_BPS = 25.0                # pre-registered notional-band width
TFI_WINDOW_SEC = 60            # pre-registered trade-flow window
FEATURE_INTERVAL_SEC = 1.0     # pre-registered aggregation bar
RECONNECT_BACKOFF = [1, 2, 5, 10, 30, 60]   # seconds, then repeats at 60

STREAM_HOST = "wss://stream.binance.com:9443/stream"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def day_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


class SymbolState:
    """Per-symbol rolling state: latest depth snapshot + trailing trade window."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: list[tuple[float, float]] = []   # [(price, qty), ...] best-first
        self.asks: list[tuple[float, float]] = []
        self.last_depth_ts: float | None = None
        self.trades: deque[tuple[float, float, bool]] = deque()  # (ts, qty, is_sell_aggressor)

    def update_depth(self, bids, asks, ts: float) -> None:
        self.bids = [(float(p), float(q)) for p, q in bids]
        self.asks = [(float(p), float(q)) for p, q in asks]
        self.last_depth_ts = ts

    def add_trade(self, ts: float, qty: float, is_sell_aggressor: bool) -> None:
        self.trades.append((ts, qty, is_sell_aggressor))
        cutoff = ts - TFI_WINDOW_SEC
        while self.trades and self.trades[0][0] < cutoff:
            self.trades.popleft()

    # ---- pre-registered metrics, computed from current state ----
    def obi(self, n: int) -> float | None:
        if not self.bids or not self.asks:
            return None
        bq = sum(q for _, q in self.bids[:n])
        aq = sum(q for _, q in self.asks[:n])
        tot = bq + aq
        return (bq - aq) / tot if tot > 0 else None

    def obi_band(self, band_bps: float) -> float | None:
        if not self.bids or not self.asks:
            return None
        mid = (self.bids[0][0] + self.asks[0][0]) / 2.0
        lo = mid * (1 - band_bps / 1e4)
        hi = mid * (1 + band_bps / 1e4)
        bq = sum(q for p, q in self.bids if p >= lo)
        aq = sum(q for p, q in self.asks if p <= hi)
        tot = bq + aq
        return (bq - aq) / tot if tot > 0 else None

    def tfi(self) -> float | None:
        if not self.trades:
            return None
        buy = sum(q for _, q, is_sell in self.trades if not is_sell)
        sell = sum(q for _, q, is_sell in self.trades if is_sell)
        tot = buy + sell
        return (buy - sell) / tot if tot > 0 else None

    def mid(self) -> float | None:
        if not self.bids or not self.asks:
            return None
        return (self.bids[0][0] + self.asks[0][0]) / 2.0

    def spread_bps(self) -> float | None:
        if not self.bids or not self.asks:
            return None
        m = self.mid()
        return (self.asks[0][0] - self.bids[0][0]) / m * 1e4 if m else None


class Writer:
    """Handles day-rotated, gzip-compressed raw JSONL + a plain-CSV feature file."""

    def __init__(self, out_dir: Path, symbol: str):
        self.out_dir = out_dir
        self.symbol = symbol
        self._raw_fh = None
        self._raw_day = None
        self._feat_fh = None
        self._feat_day = None

    def _raw_path(self, day: str) -> Path:
        d = self.out_dir / "raw" / self.symbol
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{self.symbol}_{day}.jsonl.gz"

    def _feat_path(self, day: str) -> Path:
        d = self.out_dir / "features_1s"
        d.mkdir(parents=True, exist_ok=True)
        return d / f"features_1s_{self.symbol}_{day}.csv"

    def write_raw(self, kind: str, payload: dict, ts: float) -> None:
        day = day_str(datetime.fromtimestamp(ts, tz=timezone.utc))
        if day != self._raw_day:
            if self._raw_fh:
                self._raw_fh.close()
            self._raw_fh = gzip.open(self._raw_path(day), "at", encoding="utf-8")
            self._raw_day = day
        self._raw_fh.write(json.dumps({"kind": kind, "ts": ts, **payload}) + "\n")

    def rotate_raw(self) -> None:
        """Close and reopen the raw gzip file so it accumulates as a sequence
        of complete, independently-decompressible gzip members (Python's
        gzip reader handles concatenated members transparently). A hard
        kill (power loss, OOM-kill, systemd escalating stop -> SIGKILL) then
        only loses the LAST, still-open member instead of corrupting the
        whole day's file -- confirmed necessary by this script's own smoke
        test: a hard-killed run left the raw file's final gzip member
        truncated (EOFError on full-file read), while every already-closed
        member before it read back cleanly."""
        if self._raw_fh:
            self._raw_fh.close()
            self._raw_fh = gzip.open(self._raw_path(self._raw_day), "at", encoding="utf-8")

    def write_feature_row(self, ts: float, row: dict) -> None:
        day = day_str(datetime.fromtimestamp(ts, tz=timezone.utc))
        if day != self._feat_day:
            if self._feat_fh:
                self._feat_fh.close()
            new_file = not self._feat_path(day).exists()
            self._feat_fh = open(self._feat_path(day), "a", encoding="utf-8", newline="")
            self._feat_day = day
            if new_file:
                self._feat_fh.write(",".join(row.keys()) + "\n")
        self._feat_fh.write(",".join(str(v) for v in row.values()) + "\n")

    def flush(self) -> None:
        if self._raw_fh:
            self._raw_fh.flush()
        if self._feat_fh:
            self._feat_fh.flush()

    def close(self) -> None:
        if self._raw_fh:
            self._raw_fh.close()
        if self._feat_fh:
            self._feat_fh.close()


def build_stream_url(symbols: list[str]) -> str:
    parts = []
    for s in symbols:
        parts.append(f"{s}@depth20@100ms")
        parts.append(f"{s}@aggTrade")
    return f"{STREAM_HOST}?streams={'/'.join(parts)}"


async def feature_ticker(states: dict[str, SymbolState], writers: dict[str, Writer], stop: asyncio.Event) -> None:
    """Every FEATURE_INTERVAL_SEC, snapshot the pre-registered metrics per symbol."""
    log = logging.getLogger("feature_ticker")
    while not stop.is_set():
        await asyncio.sleep(FEATURE_INTERVAL_SEC)
        ts = utc_now().timestamp()
        for sym, st in states.items():
            if st.last_depth_ts is None:
                continue
            row = {
                "ts_utc": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "mid": st.mid(),
                "spread_bps": st.spread_bps(),
                f"obi_{DEPTH_LEVELS_N[0]}": st.obi(DEPTH_LEVELS_N[0]),
                f"obi_{DEPTH_LEVELS_N[1]}": st.obi(DEPTH_LEVELS_N[1]),
                f"obi_band{int(BAND_BPS)}bps": st.obi_band(BAND_BPS),
                f"tfi_{TFI_WINDOW_SEC}s": st.tfi(),
                "depth_age_sec": round(ts - st.last_depth_ts, 3) if st.last_depth_ts else None,
            }
            try:
                writers[sym].write_feature_row(ts, row)
            except Exception as e:
                log.warning("feature write failed for %s: %s", sym, e)


async def run_capture(symbols: list[str], out_dir: Path, stop: asyncio.Event) -> None:
    log = logging.getLogger("orderbook_capture")
    states = {s: SymbolState(s) for s in symbols}
    writers = {s: Writer(out_dir, s) for s in symbols}
    ticker_task = asyncio.create_task(feature_ticker(states, writers, stop))

    url = build_stream_url(symbols)
    backoff_i = 0
    n_msgs = 0
    last_log = utc_now().timestamp()

    try:
        while not stop.is_set():
            try:
                log.info("connecting to %s", url)
                async with websockets.connect(url, open_timeout=15, ping_interval=20, ping_timeout=20) as ws:
                    backoff_i = 0
                    log.info("connected")
                    while not stop.is_set():
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                        ts = utc_now().timestamp()
                        msg = json.loads(raw)
                        stream = msg.get("stream", "")
                        data = msg.get("data", {})
                        sym = stream.split("@")[0]
                        st = states.get(sym)
                        if st is None:
                            continue
                        if "depth20" in stream:
                            st.update_depth(data.get("bids", []), data.get("asks", []), ts)
                            writers[sym].write_raw("depth", data, ts)
                        elif "aggTrade" in stream:
                            is_sell_aggressor = bool(data.get("m"))
                            qty = float(data.get("q", 0.0))
                            st.add_trade(ts, qty, is_sell_aggressor)
                            writers[sym].write_raw("trade", data, ts)
                        n_msgs += 1
                        if ts - last_log > 60:
                            log.info("alive: %d messages received in the last ~60s window", n_msgs)
                            n_msgs = 0
                            last_log = ts
                            for w in writers.values():
                                w.flush()
                                w.rotate_raw()   # close a complete gzip member every ~60s (see rotate_raw docstring)
            except (asyncio.TimeoutError, websockets.ConnectionClosed, OSError) as e:
                if stop.is_set():
                    break
                delay = RECONNECT_BACKOFF[min(backoff_i, len(RECONNECT_BACKOFF) - 1)]
                backoff_i += 1
                log.warning("connection issue (%s: %s) -- reconnecting in %ds", type(e).__name__, e, delay)
                await asyncio.sleep(delay)
    finally:
        stop.set()
        ticker_task.cancel()
        for w in writers.values():
            w.close()
        log.info("shutdown complete, all files flushed and closed")


def setup_logging(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "capture.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding="utf-8")],
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", default="btcusdt", help="comma-separated lowercase symbols, e.g. btcusdt,ethusdt")
    ap.add_argument("--out", default="data/orderbook_capture", help="output directory")
    args = ap.parse_args()

    symbols = [s.strip().lower() for s in args.symbols.split(",") if s.strip()]
    out_dir = Path(args.out)
    setup_logging(out_dir)
    log = logging.getLogger("main")
    log.info("PRE-REGISTERED metrics: OBI_%d, OBI_%d, OBI_band%dbps, TFI_%ds, feature bar %.0fs",
             *DEPTH_LEVELS_N, int(BAND_BPS), TFI_WINDOW_SEC, FEATURE_INTERVAL_SEC)
    log.info("symbols=%s  out=%s", symbols, out_dir)

    stop = asyncio.Event()

    async def runner():
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:
                pass  # Windows: SIGTERM handler unsupported, Ctrl-C (SIGINT) still works
        await run_capture(symbols, out_dir, stop)

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
