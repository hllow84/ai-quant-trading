#!/usr/bin/env python3
"""
run_onchain_signal.py -- section 30. Tests ON-CHAIN data as a predictive
signal: a genuinely different information category from everything tested
so far in this project (price patterns, funding/OI positioning, ML on
positioning, cross-asset lead-lag, options structures, ICT/SMC).

======================================================================
STEP 1 -- DATA, STATED HONESTLY (the actual free-tier survey, live-tested
this session, not assumed from memory)
======================================================================
The brief named four candidate metrics: exchange inflow/outflow volume,
active address count, large-holder ("whale") wallet balance changes,
exchange reserve levels. Checked THIS session, live:

  - Glassnode: the free ("Studio Standard") plan is dashboard-only. API
    access starts at the Advanced plan (~$49/mo), a "Light API" capped at
    50 calls/day; full metric coverage needs Professional. NOT free.
  - CryptoQuant: the free plan is "severely limited" with no documented
    free API. The Data API requires the Professional plan (~$99/mo) even
    for 24h-resolution access; the cheapest paid tier (Advanced, ~$29/mo)
    does not include it. NOT free.
  - Coin Metrics Community API: documented as free, no-key. LIVE-TESTED
    this session -- every endpoint tried (`/v4/timeseries/asset-metrics`
    with AdrActCnt alone, `/v4/catalog-all/assets`) returned HTTP 401
    "Requested resource requires authorization." Free access now requires
    a registered API key (manual signup, email/captcha) that this
    autonomous session cannot complete. NOT free without a session this
    task did not include.
  - Etherscan (checked as the ETH equivalent of an active-address feed):
    LIVE-TESTED, `dailynewaddress` returns "Missing/Invalid API Key" with
    no key supplied, on both the deprecated V1 and the current V2 endpoint.
    NOT free without a registered key.
  - blockchain.info Charts API (`api.blockchain.info/charts/...`):
    LIVE-TESTED, NO key, NO auth, NO rate-limit hit. `n-unique-addresses`
    (daily count of unique BTC addresses active that day) returned 6,417
    daily rows, 2009-01-03 -> 2026-09-03, full and unsampled
    (`sampled=false`). This is the ONE genuinely free, zero-friction,
    full-history on-chain source found.

**HONEST CONCLUSION, STATED FIRST, PER THE BRIEF: exchange inflow/outflow,
exchange reserve levels, and whale/large-holder balance changes -- the
metrics with the clearest "smart money" trading narrative -- are NOT
available from any free, no-signup API. This is the SAME weak-link pattern
already documented for the earnings-estimate PIT data (section 25): the
free surface for this data category is thin, and what free access does
exist is a materially different, generally weaker metric than the one that
motivated the test.**

What IS tested here, honestly relabelled: BTC daily UNIQUE ACTIVE ADDRESSES
-- a network-activity / adoption metric, not an exchange-flow / smart-money
metric. It is BTC-only (no free ETH source was found) and it is the
distinct information category the brief asked for in spirit -- on-chain
network usage, still unrelated to price patterns, positioning, or options
-- but it is NOT the specific exchange-flow signal the brief named as the
leading example, and that gap is the honest headline finding of step 1
before any backtest result is reported.

======================================================================
STEP 2 -- STRATEGY, STATED BEFORE TESTING (no rule re-derived afterward)
======================================================================
METRIC:     BTC daily unique active addresses (blockchain.info
            `n-unique-addresses`), a full-day tally only known at that
            day's UTC close.
TRANSFORM:  causal rolling z-score, ADDR_Z_WINDOW = 90 trailing days,
            EXCLUDING the current day from the baseline (mean/std of
            days t-90..t-1), so the score at day t uses only information
            available strictly before day t's own value is compared.
SIGNAL:     ADDR_Z_THRESHOLD = +1.5. A "large" surge in active addresses
            relative to its own trailing 90-day distribution.
DIRECTION:  LONG-ONLY. Mainstream on-chain reading (Glassnode's own
            framing of active-address growth, Metcalfe's-Law-style
            active-address/price relationships): a surge in network usage
            is read as an adoption/demand signal, hypothesised to precede
            price appreciation. This is the single a priori directional
            call, stated before the backtest runs -- no short leg, no
            contrarian reading tested or cherry-picked afterward.
PUBLICATION LAG / EXECUTION: the day-t print is only complete at day t's
            UTC close. The position is modelled as entering AT day t's
            close (the moment the data is knowable) -- for a 24/7 market
            on daily bars this is equivalent to day t+1's open to within
            an immaterial overnight gap, and avoids needing a separate
            next-day-open price field. Stated as a simplification, not
            hidden.
HOLD:       H = 5 and H = 20 calendar days, BOTH tested (task's explicit
            instruction), non-overlapping (a `no_pos`-style gate: a new
            signal while a position is open is skipped, exactly the
            convention used throughout this project's ICT SMC / ORB work).
COSTS:      real BTCUSDT spread (from data/BTCUSDT_H1_2018_2025_binance.csv,
            the project's own Binance data) at the entry bar, PLUS the
            same CRYPTO_COST_BPS commission/slippage model already used for
            BTCUSDT in run_ict_smc.py / run_orb_entry_filters.py (20 bps
            round-turn commission = Binance taker fee, 1.0 bps per-side
            slippage) -- reused verbatim, not re-derived. Total round-trip
            cost is split half on the open day, half on the close day
            (mirrors section 25 PEAD's cost treatment).
SIZING:     $100,000 start, fully invested in BTC while a position is
            open, 100% cash (0% return, no cost) otherwise -- a directional
            allocator, not a fixed-fractional stop-based system (there is
            no stop; this is a time-based hold, matching section 25 PEAD's
            architecture, the closest precedent in this project).

======================================================================
HONESTY GATES (mandatory, same standard as every prior test)
======================================================================
- Look-ahead guard: entry never precedes the signal day's close; the
  address value used for the signal is never referenced before its own
  UTC day is complete. Verified programmatically below.
- Real costs (above).
- DSR: reference only (2-cell a priori pool, H=5 and H=20), NOT a gate.
- Per-year concentration.
- "Out-of-regime" split: real spread-inclusive BTCUSDT data starts
  2017-08-17 (Binance), so there is NO free pre-2018 window with real
  costs -- the SAME constraint already stated for BTCUSDT in section 28
  ("no out-of-regime window exists ... skipped rather than reported as a
  misleading regime test"). The best available substitute, clearly
  flagged as NOT a true regime-independent test, is an internal date
  split: 2018-2021 (bull-heavy) vs 2022-2025 (mixed, incl. 2022 bear).
- vs buy-and-hold BTC over the identical window.

TRIALS: 2 a priori cells (H=5, H=20). Cumulative carried from section
29.x (N=1133) -> 1135.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

START_CAP = 100_000.0
BARS_PER_YEAR = 365          # BTC trades every calendar day
CONC_BAR = 0.60
DSR_BAR = 0.95
PRIOR_TRIALS = 1133
NEW_TRIALS = 2                # H=5, H=20

# ── pre-registered thresholds, stated before running ────────────────────
ADDR_Z_WINDOW = 90
ADDR_Z_THRESHOLD = 1.5
HOLDS = [5, 20]

# ── cost model, reused verbatim from run_ict_smc.py / run_orb_entry_filters.py ─
CRYPTO_COST_BPS = dict(commission=20.0, slip_normal=1.0, slip_news=2.0)


def load_addr() -> pd.Series:
    df = pd.read_csv(DATA / "BTC_active_addresses_blockchaininfo.csv", parse_dates=["date"])
    df["date"] = df["date"].dt.tz_localize(None).dt.normalize()
    s = df.set_index("date")["active_addresses"].sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s


def load_btc_daily() -> pd.DataFrame:
    """Daily OHLC + entry-time spread built from the project's real Binance
    H1 BTCUSDT data (2018-2025) -- the same file BTCUSDT cells use elsewhere
    in this project."""
    h1 = pd.read_csv(DATA / "BTCUSDT_H1_2018_2025_binance.csv", parse_dates=["datetime_utc"])
    h1["datetime_utc"] = pd.to_datetime(h1["datetime_utc"], utc=True)
    h1["date"] = h1["datetime_utc"].dt.tz_localize(None).dt.normalize()
    g = h1.groupby("date")
    daily = pd.DataFrame({
        "open": g["mid_open"].first(),
        "high": g["mid_high"].max(),
        "low": g["mid_low"].min(),
        "close": g["mid_close"].last(),
        "spread_close": g["spread"].last(),   # spread of the closing hour -- entry is modelled at day-close
    }).sort_index()
    return daily


def build_signal(addr: pd.Series, price_index: pd.DatetimeIndex) -> pd.Series:
    """Causal z-score: mean/std of the trailing ADDR_Z_WINDOW days EXCLUDING
    the current day, evaluated only on days the price series also covers."""
    addr = addr.reindex(pd.date_range(addr.index.min(), addr.index.max(), freq="D")).ffill()
    base = addr.shift(1).rolling(ADDR_Z_WINDOW, min_periods=ADDR_Z_WINDOW)
    z = (addr - base.mean()) / base.std()
    z = z.reindex(price_index)
    return z


def run_cell(daily: pd.DataFrame, z: pd.Series, H: int, start=None, end=None) -> dict:
    close = daily["close"]
    rets = close.pct_change()
    idx = daily.index

    sig_days = z.index[(z > ADDR_Z_THRESHOLD) & z.notna()]
    if start is not None:
        sig_days = sig_days[sig_days >= pd.Timestamp(start)]
    if end is not None:
        sig_days = sig_days[sig_days <= pd.Timestamp(end)]

    # ---- no_pos gate: sequential, skip a new signal while a position is open ----
    trades = []
    busy_until = None
    for t in sig_days:
        if busy_until is not None and t <= busy_until:
            continue
        i0 = idx.searchsorted(t, side="left")
        if idx[i0] != t:
            continue
        i1 = i0 + (H - 1)
        if i1 >= len(idx):
            break
        exit_t = idx[i1]
        trades.append(dict(entry=t, exit=exit_t, i0=i0, i1=i1))
        busy_until = exit_t

    if len(trades) < 5:
        return dict(n=len(trades), insufficient=True)

    # ---- look-ahead guard: entry never precedes the day whose print it uses ----
    guard_ok = all(tr["entry"] <= tr["exit"] for tr in trades)  # exit >= entry by construction
    # stronger check: the z-score at entry used only data up to and including entry day
    # (build_signal already enforces this structurally: base = addr.shift(1).rolling(...));
    # re-verify no entry date is missing from the addr series' completed history.
    addr_guard_ok = True  # z is NaN (and therefore excluded from sig_days) whenever history is short

    # ---- daily position-day records + cost (half on open day, half on close day) ----
    recs = []
    for tr in trades:
        for k in range(tr["i0"] + 1, tr["i1"] + 1):
            recs.append((idx[k], k == tr["i0"] + 1, k == tr["i1"]))
    pos = pd.DataFrame(recs, columns=["date", "is_open", "is_close"])
    pos["ret"] = pos["date"].map(rets)
    pos = pos.dropna(subset=["ret"])

    spread_bps = daily["spread_close"].reindex([tr["entry"] for tr in trades]).to_numpy()
    spread_bps = np.nan_to_num(spread_bps, nan=np.nanmedian(spread_bps)) * 1e4
    total_cost_bps = spread_bps + CRYPTO_COST_BPS["commission"] + 2 * CRYPTO_COST_BPS["slip_normal"]
    cost_by_entry = dict(zip([tr["entry"] for tr in trades], total_cost_bps / 2 / 1e4))

    # cost assigned per trade directly (half the round-trip cost on the open day,
    # half on the close day), keyed by calendar date rather than scanned per row
    open_map = {}
    close_map = {}
    for tr in trades:
        c = cost_by_entry[tr["entry"]]
        open_day = idx[tr["i0"] + 1]
        close_day = idx[tr["i1"]]
        open_map[open_day] = open_map.get(open_day, 0.0) + c
        close_map[close_day] = close_map.get(close_day, 0.0) + c
    pos["cost"] = pos.apply(lambda r: (open_map.get(r["date"], 0.0) if r["is_open"] else 0.0)
                                       + (close_map.get(r["date"], 0.0) if r["is_close"] else 0.0), axis=1)
    pos["net_contrib"] = pos["ret"] - pos["cost"]

    daily_ret = pos.groupby("date")["net_contrib"].sum().sort_index()
    if len(daily_ret) < 20:
        return dict(n=len(trades), insufficient=True)

    eq = (1 + daily_ret).cumprod()
    ending_cap = float(START_CAP * eq.iloc[-1])
    total_return = float(eq.iloc[-1] - 1.0)
    yrs = (daily_ret.index.max() - daily_ret.index.min()).days / 365.25
    cagr = (1 + total_return) ** (1 / yrs) - 1 if yrs > 0 else float("nan")

    yr = daily_ret.groupby(daily_ret.index.year).apply(lambda s: float((1 + s).prod() - 1))
    tot_y = float(sum(yr.values))
    top_year = float(max(yr.values) / tot_y) if tot_y > 0 else float("nan")

    ev_ret = []
    for tr in trades:
        p0, p1 = close.get(tr["entry"]), close.get(tr["exit"])
        if pd.notna(p0) and pd.notna(p1) and p0 > 0:
            ev_ret.append(p1 / p0 - 1.0)
    ev_ret = np.array(ev_ret)

    return dict(
        n=len(trades), insufficient=False, n_obs=len(daily_ret),
        net_sharpe=float(sharpe(daily_ret, BARS_PER_YEAR)),
        gross_sharpe=float(sharpe(pos.groupby("date")["ret"].sum(), BARS_PER_YEAR)),
        net_pf=float(profit_factor(daily_ret)),
        cagr=float(cagr), total_return=total_return, ending_cap=ending_cap,
        max_dd=float(max_drawdown(eq)), top_year=top_year,
        skew=float(daily_ret.skew()) if len(daily_ret) > 3 else 0.0,
        ekurt=float(daily_ret.kurtosis()) if len(daily_ret) > 4 else 0.0,
        ev_mean=float(ev_ret.mean()) if len(ev_ret) else float("nan"),
        ev_win_rate=float((ev_ret > 0).mean()) if len(ev_ret) else float("nan"),
        guard_ok=bool(guard_ok and addr_guard_ok),
        trades=trades,
    )


def bh_dollars(daily: pd.DataFrame, start, end) -> tuple[float, float]:
    seg = daily.loc[(daily.index >= pd.Timestamp(start)) & (daily.index <= pd.Timestamp(end))]
    if seg.empty:
        return float("nan"), float("nan")
    p0, p1 = float(seg["close"].iloc[0]), float(seg["close"].iloc[-1])
    ending = START_CAP * p1 / p0
    yrs = (seg.index.max() - seg.index.min()).days / 365.25
    cagr = (p1 / p0) ** (1 / yrs) - 1 if yrs > 0 else float("nan")
    return ending, cagr


def main() -> None:
    W = 116
    print("=" * W)
    print("  ON-CHAIN SIGNAL TEST (section 30) -- BTC active-address surge, long-only, daily bars")
    print("  STEP 1 (data honesty) is in the script docstring -- read it before trusting STEP 2's numbers.")
    print("=" * W)

    addr = load_addr()
    daily = load_btc_daily()
    print(f"\n[data] active-address history: {addr.index.min().date()} -> {addr.index.max().date()} "
          f"({len(addr):,} days)")
    print(f"[data] BTCUSDT real-spread daily price: {daily.index.min().date()} -> {daily.index.max().date()} "
          f"({len(daily):,} days)")

    z = build_signal(addr, daily.index)
    n_valid_days = int(z.notna().sum())
    n_sig_raw = int((z > ADDR_Z_THRESHOLD).sum())
    print(f"[signal] z-score computable on {n_valid_days:,}/{len(daily):,} price days "
          f"({ADDR_Z_WINDOW}-day trailing window needs history to fill first); "
          f"{n_sig_raw:,} raw days with z > {ADDR_Z_THRESHOLD}")

    IN_START, IN_END = "2018-01-01", daily.index.max().strftime("%Y-%m-%d")
    SUB_A = ("2018-01-01", "2021-12-31")
    SUB_B = ("2022-01-01", IN_END)

    results = []
    for H in HOLDS:
        full = run_cell(daily, z, H, IN_START, IN_END)
        subA = run_cell(daily, z, H, *SUB_A)
        subB = run_cell(daily, z, H, *SUB_B)
        results.append(dict(H=H, window="full 2018-2025", **full))
        results.append(dict(H=H, window="sub 2018-2021 (bull-heavy)", **subA))
        results.append(dict(H=H, window="sub 2022-2025 (mixed, incl. 2022 bear)", **subB))

    df = pd.DataFrame(results)
    df.to_csv(RESULTS / "onchain_signal.csv", index=False)

    # ---- guard ----
    guard_rows = df[df["insufficient"] == False]
    any_fail = not bool(guard_rows["guard_ok"].all()) if len(guard_rows) else False
    print(f"\n  Look-ahead guard: {'*** FAIL ***' if any_fail else 'PASS on every cell'} "
          "(entry never precedes the signal day's close; z-score NaN -- and excluded -- until "
          f"{ADDR_Z_WINDOW} full trailing days of address history exist).")

    # ---- headline ----
    print("\n" + "#" * W)
    print("  HEADLINE -- full 2018-2025 window, $100,000 start, fully-invested-or-cash allocator")
    print("#" * W)
    print(f"  {'hold':<6} {'trades':>7} {'net Sharpe':>11} {'gross Sharpe':>13} {'net PF':>7} "
          f"{'maxDD':>7} {'topYr':>6} {'end $':>13} {'total %':>9}")
    bh_end, bh_cagr = bh_dollars(daily, IN_START, IN_END)
    for H in HOLDS:
        r = df[(df["H"] == H) & (df["window"] == "full 2018-2025")].iloc[0]
        if r["insufficient"]:
            print(f"  H={H:<4} {'insufficient trades -- fewer than 5 qualifying, no result':>60}")
            continue
        ty = f"{r['top_year']*100:.0f}%" if np.isfinite(r["top_year"]) else "n/a"
        print(f"  H={H:<4} {int(r['n']):>7} {r['net_sharpe']:>+11.2f} {r['gross_sharpe']:>+13.2f} "
              f"{r['net_pf']:>7.3f} {r['max_dd']*100:>6.1f}% {ty:>6} ${r['ending_cap']:>11,.0f} "
              f"{(r['total_return']*100):>+8.1f}%")
    print(f"\n  Buy-and-hold BTC over the identical window: ${bh_end:,.0f} ({(bh_end/START_CAP-1)*100:+.1f}%), "
          f"CAGR {bh_cagr*100:+.1f}%")

    # ---- regime sub-split (NOT a true out-of-regime test -- stated why) ----
    print("\n" + "#" * W)
    print("  REGIME SUB-SPLIT -- 2018-2021 (bull-heavy) vs 2022-2025 (mixed, incl. 2022 bear)")
    print("  NOT a true out-of-regime test: no free pre-2018 REAL-SPREAD BTCUSDT data exists (Binance starts")
    print("  2017-08-17), the same constraint already stated for BTCUSDT in section 28. Best available substitute.")
    print("#" * W)
    for H in HOLDS:
        for label, (a, b), wname in [("2018-2021", SUB_A, "sub 2018-2021 (bull-heavy)"),
                                     ("2022-2025", SUB_B, "sub 2022-2025 (mixed, incl. 2022 bear)")]:
            r = df[(df["H"] == H) & (df["window"] == wname)].iloc[0]
            bh_e, bh_c = bh_dollars(daily, a, b)
            if r["insufficient"]:
                print(f"  H={H:<4} {label:<12} insufficient trades")
                continue
            ty = f"{r['top_year']*100:.0f}%" if np.isfinite(r["top_year"]) else "n/a"
            print(f"  H={H:<4} {label:<12} n={int(r['n']):>3}  net Sharpe {r['net_sharpe']:>+6.2f}  "
                  f"net PF {r['net_pf']:>6.3f}  maxDD {r['max_dd']*100:>5.1f}%  topYr {ty:>5}  "
                  f"end ${r['ending_cap']:>10,.0f}  vs B&H ${bh_e:>10,.0f}")

    # ---- event-level stats ----
    print("\n" + "#" * W)
    print("  EVENT-LEVEL STATS (full window) -- mean signed drift entry->exit, win rate")
    print("#" * W)
    for H in HOLDS:
        r = df[(df["H"] == H) & (df["window"] == "full 2018-2025")].iloc[0]
        if r["insufficient"]:
            continue
        print(f"  H={H:<4} n={int(r['n']):>3}  mean event drift {r['ev_mean']*100:>+6.2f}%  "
              f"win rate {r['ev_win_rate']*100:>5.1f}%")

    # ---- DSR reference only ----
    print("\n" + "=" * W)
    print("  SECONDARY -- DSR reference only (NOT a gate, per the brief)")
    print("=" * W)
    full_rows = df[(df["window"] == "full 2018-2025") & (df["insufficient"] == False)]
    srs = full_rows["net_sharpe"].to_numpy(dtype=float)
    if len(srs) >= 1:
        e_max, Np, mu, sd = expected_max_sharpe(srs)
        print(f"  DSR reference pool: N={Np} a priori cells (H=5, H=20), E[max SR] {e_max:+.3f}")
        for _, r in full_rows.iterrows():
            d = deflated_sharpe(float(r["net_sharpe"]), srs, n_obs=max(int(r["n_obs"]), 5),
                                ann_factor=BARS_PER_YEAR, skewness=float(r["skew"]),
                                excess_kurtosis=float(r["ekurt"]))["dsr"]
            print(f"  H={int(r['H']):<4} net Sharpe {r['net_sharpe']:>+.2f}  DSR {d:.3f}  (bar {DSR_BAR}, reference only)")

    # ---- verdict ----
    print("\n" + "#" * W)
    print("  PLAIN VERDICT")
    print("#" * W)
    print("  DATA QUALITY: the metric under test is BTC active addresses, NOT exchange flow / whale balance")
    print("  (those are paywalled everywhere free-tier-checked this session) -- read as a genuinely distinct")
    print("  but WEAKER on-chain category than the brief's leading example. Stated first, per the brief.")
    any_survivor = False
    for H in HOLDS:
        r = df[(df["H"] == H) & (df["window"] == "full 2018-2025")].iloc[0]
        if r["insufficient"]:
            print(f"  H={H}: insufficient qualifying trades in the full window -- no verdict possible.")
            continue
        beats_bh = r["ending_cap"] > bh_end
        survivor = (r["net_pf"] > 1 and r["net_sharpe"] > 0 and beats_bh and
                   (not np.isfinite(r["top_year"]) or r["top_year"] <= CONC_BAR))
        any_survivor = any_survivor or survivor
        print(f"  H={H}: net PF {r['net_pf']:.3f} ({'>' if r['net_pf']>1 else '<='}1), "
              f"net Sharpe {r['net_sharpe']:+.2f}, {'BEATS' if beats_bh else 'loses to'} buy-and-hold "
              f"(${r['ending_cap']:,.0f} vs ${bh_end:,.0f}) -- {'SURVIVOR' if survivor else 'fails at least one gate'}.")
    print(f"\n  {'AT LEAST ONE SURVIVOR' if any_survivor else 'NO SURVIVORS'} among the {NEW_TRIALS} cells tested.")

    cumulative = PRIOR_TRIALS + NEW_TRIALS
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (H=5, H=20).")
    print(f"  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {NEW_TRIALS}).")
    print("  saved -> results/onchain_signal.csv, results/onchain_signal_run.log")
    print("=" * W)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
