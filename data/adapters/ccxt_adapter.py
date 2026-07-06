"""
ccxt_adapter.py — Exchange data fetcher with parquet cache.

Pulls OHLCV, funding rate, open interest, long/short ratio via ccxt.
Venues are parametrised — data venue != execution venue.
Cache key encodes: source · asset · metric · resolution · asof_date
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

try:
    import ccxt
    _CCXT_AVAILABLE = True
except ImportError:
    _CCXT_AVAILABLE = False

try:
    import pyarrow  # noqa: F401
    _PARQUET_ENGINE = "pyarrow"
except ImportError:
    _PARQUET_ENGINE = None

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

_EXCHANGE_CACHE: dict[str, object] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_exchange(venue: str):
    if not _CCXT_AVAILABLE:
        raise ImportError("ccxt is not installed. Run: pip install ccxt")
    if venue not in _EXCHANGE_CACHE:
        cls = getattr(ccxt, venue)
        _EXCHANGE_CACHE[venue] = cls({"enableRateLimit": True})
    return _EXCHANGE_CACHE[venue]


def _to_ms(dt: str | datetime) -> int:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _cache_path(source: str, asset: str, metric: str, resolution: str, asof: str) -> Path:
    asset_safe = asset.replace("/", "-")
    return CACHE_DIR / f"{source}__{asset_safe}__{metric}__{resolution}__{asof}.parquet"


def _load_cache(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    if _PARQUET_ENGINE:
        return pd.read_parquet(path)
    return pd.read_parquet(path)  # pandas will use fastparquet if available


def _save_cache(df: pd.DataFrame, path: Path) -> None:
    if _PARQUET_ENGINE:
        df.to_parquet(path, engine=_PARQUET_ENGINE)
    else:
        df.to_parquet(path)


def _ts_filter(df: pd.DataFrame, since: str, until: str) -> pd.DataFrame:
    lo = pd.Timestamp(since, tz="UTC")
    hi = pd.Timestamp(until, tz="UTC")
    return df.loc[(df.index >= lo) & (df.index < hi)]


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_ohlcv(
    symbol: str,
    timeframe: str,
    since: str,
    until: str,
    venue: str = "binance",
) -> pd.DataFrame:
    """
    Fetch OHLCV bars. Returns DataFrame indexed by UTC timestamp,
    columns: [open, high, low, close, volume].
    """
    asof = date.today().isoformat()
    cpath = _cache_path(venue, symbol, "ohlcv", timeframe, asof)
    cached = _load_cache(cpath)
    if cached is not None:
        return _ts_filter(cached, since, until)

    exchange = _get_exchange(venue)
    since_ms = _to_ms(since)
    until_ms = _to_ms(until)

    rows: list = []
    cursor = since_ms
    while cursor < until_ms:
        batch = exchange.fetch_ohlcv(symbol, timeframe, since=cursor, limit=1000)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1][0]
        if last_ts <= cursor:
            break
        cursor = last_ts + 1
        if last_ts >= until_ms:
            break

    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp").sort_index()
    df = df[~df.index.duplicated(keep="first")]
    _save_cache(df, cpath)
    return _ts_filter(df, since, until)


# ── Two-venue spread ───────────────────────────────────────────────────────────

class SpreadAlignmentError(ValueError):
    """Raised when the two OHLCV series have more than max_drop_pct non-overlapping bars."""


def fetch_ohlcv_spread(
    symbol_a: str,
    symbol_b: str,
    timeframe: str,
    since: str,
    until: str,
    venue_a: str = "binance",
    venue_b: str = "coinbase",
    max_drop_pct: float = 0.02,
) -> tuple[pd.Series, pd.Series]:
    """
    Fetch OHLCV close from two venues, inner-join on UTC timestamps.

    Raises SpreadAlignmentError if more than max_drop_pct of bars are dropped
    by the inner join.

    Returns
    -------
    (spread, asset_returns)
        spread        : close_b - close_a, name="spread"
        asset_returns : pct_change of close_a (reference venue for trading)
    """
    df_a = fetch_ohlcv(symbol_a, timeframe, since, until, venue_a)
    df_b = fetch_ohlcv(symbol_b, timeframe, since, until, venue_b)

    n_a = len(df_a)
    n_b = len(df_b)

    joined = df_a[["close"]].join(df_b[["close"]], how="inner", lsuffix="_a", rsuffix="_b")

    n_joined   = len(joined)
    n_universe = max(n_a, n_b)
    n_dropped  = n_universe - n_joined
    drop_pct   = n_dropped / n_universe if n_universe > 0 else 0.0

    print(
        f"\nAlignment: {venue_a}/{symbol_a}={n_a} bars, "
        f"{venue_b}/{symbol_b}={n_b} bars\n"
        f"  Inner join: {n_joined} bars aligned, {n_dropped} dropped ({drop_pct:.2%})"
    )

    if drop_pct > max_drop_pct:
        ts_a    = set(df_a.index)
        ts_b    = set(df_b.index)
        only_a  = sorted(ts_a - ts_b)
        only_b  = sorted(ts_b - ts_a)
        sample_a = [str(t)[:19] for t in only_a[:5]]
        sample_b = [str(t)[:19] for t in only_b[:5]]
        raise SpreadAlignmentError(
            f"Alignment failed: {n_dropped}/{n_universe} = {drop_pct:.2%} bars dropped "
            f"(threshold {max_drop_pct:.0%}).\n"
            f"  Only in {venue_a}/{symbol_a}: {len(only_a)} bars (sample: {sample_a})\n"
            f"  Only in {venue_b}/{symbol_b}: {len(only_b)} bars (sample: {sample_b})\n"
            f"Common causes: exchange maintenance gaps, different listing dates, "
            f"API coverage limits, or timezone offset."
        )

    spread  = (joined["close_b"] - joined["close_a"]).rename("spread")
    returns = joined["close_a"].pct_change().rename("asset_return")
    return spread, returns


def fetch_funding_rate_history(
    symbol: str,
    since: str,
    until: str,
    venue: str = "binance",
) -> pd.DataFrame:
    """
    Fetch perpetual funding rate history. Returns DataFrame indexed by UTC timestamp,
    column: [funding_rate].
    """
    asof = date.today().isoformat()
    cpath = _cache_path(venue, symbol, "funding_rate", "8h", asof)
    cached = _load_cache(cpath)
    if cached is not None:
        return _ts_filter(cached, since, until)

    exchange = _get_exchange(venue)
    since_ms = _to_ms(since)
    until_ms = _to_ms(until)

    rows: list = []
    cursor = since_ms
    while cursor < until_ms:
        batch = exchange.fetch_funding_rate_history(symbol, since=cursor, limit=1000)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1]["timestamp"]
        if last_ts <= cursor:
            break
        cursor = last_ts + 1
        if last_ts >= until_ms:
            break

    if not rows:
        return pd.DataFrame(columns=["funding_rate"])

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    rate_col = "fundingRate" if "fundingRate" in df.columns else df.columns[1]
    df = df.set_index("timestamp")[[rate_col]].rename(columns={rate_col: "funding_rate"})
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    _save_cache(df, cpath)
    return _ts_filter(df, since, until)


def fetch_open_interest_history(
    symbol: str,
    timeframe: str,
    since: str,
    until: str,
    venue: str = "binance",
) -> pd.DataFrame:
    """
    Fetch open interest history. Returns DataFrame indexed by UTC timestamp,
    column: [open_interest].
    """
    asof = date.today().isoformat()
    cpath = _cache_path(venue, symbol, "open_interest", timeframe, asof)
    cached = _load_cache(cpath)
    if cached is not None:
        return _ts_filter(cached, since, until)

    exchange = _get_exchange(venue)
    since_ms = _to_ms(since)
    until_ms = _to_ms(until)

    rows: list = []
    cursor = since_ms
    while cursor < until_ms:
        batch = exchange.fetch_open_interest_history(symbol, timeframe, since=cursor, limit=1000)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1]["timestamp"]
        if last_ts <= cursor:
            break
        cursor = last_ts + 1
        if len(batch) < 1000:
            break

    if not rows:
        return pd.DataFrame(columns=["open_interest"])

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    oi_col = next((c for c in ("openInterestValue", "openInterest") if c in df.columns), df.columns[1])
    df = df.set_index("timestamp")[[oi_col]].rename(columns={oi_col: "open_interest"})
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    _save_cache(df, cpath)
    return _ts_filter(df, since, until)


def fetch_long_short_ratio(
    symbol: str,
    timeframe: str,
    since: str,
    until: str,
    venue: str = "binance",
) -> pd.DataFrame:
    """
    Fetch long/short ratio history. Returns DataFrame indexed by UTC timestamp,
    column: [long_short_ratio].
    """
    asof = date.today().isoformat()
    cpath = _cache_path(venue, symbol, "long_short_ratio", timeframe, asof)
    cached = _load_cache(cpath)
    if cached is not None:
        return _ts_filter(cached, since, until)

    exchange = _get_exchange(venue)
    since_ms = _to_ms(since)
    until_ms = _to_ms(until)

    rows: list = []
    cursor = since_ms
    while cursor < until_ms:
        batch = exchange.fetch_long_short_ratio_history(symbol, timeframe, since=cursor, limit=500)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1]["timestamp"]
        if last_ts <= cursor:
            break
        cursor = last_ts + 1
        if len(batch) < 500:
            break

    if not rows:
        return pd.DataFrame(columns=["long_short_ratio"])

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    ls_col = next(
        (c for c in ("longShortRatio", "longAccount", "longRatio") if c in df.columns),
        df.columns[1],
    )
    df = df.set_index("timestamp")[[ls_col]].rename(columns={ls_col: "long_short_ratio"})
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="first")]
    _save_cache(df, cpath)
    return _ts_filter(df, since, until)
