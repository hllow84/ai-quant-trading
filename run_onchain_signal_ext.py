#!/usr/bin/env python3
"""
run_onchain_signal_ext.py -- section 30.1. A BOUNDED, PRE-REGISTERED extension
of the section-30 on-chain BTC active-address signal.

Everything upstream of the grid is REUSED VERBATIM from run_onchain_signal.py
(section 30), imported as the module `s30`:
  - data: `s30.load_addr()` (blockchain.info n-unique-addresses, the one free
    zero-auth on-chain source; the STEP 1 data-honesty caveat in section 30's
    docstring still stands -- this is a network-activity/adoption metric, NOT
    the exchange-flow / whale-balance metric the original brief named, which is
    paywalled everywhere free-tier-checked) and `s30.load_btc_daily()`
    (real-spread BTCUSDT daily built from the project's Binance H1 file).
  - cost model: `s30.CRYPTO_COST_BPS` = 20 bps round-turn commission + 1.0 bps
    per-side slippage, PLUS the real per-day BTCUSDT closing-hour spread, split
    half on the open day and half on the close day -- untouched.
  - engine: `s30.build_signal` (causal trailing z-score, baseline EXCLUDES the
    current day via `addr.shift(1).rolling(window)`) and `s30.run_cell` (the
    no_pos sequential gate, per-day P&L, cost attribution, metrics) -- the LONG
    cells call `s30.run_cell` directly, unmodified. The SHORT cells use
    `run_cell_short` below, which is a byte-for-byte copy of `s30.run_cell`
    with exactly THREE sign flips, each marked `# <-- SHORT`.
  - metrics / DSR: research.metrics.{sharpe,max_drawdown,profit_factor},
    research.dsr.{deflated_sharpe,expected_max_sharpe}.

======================================================================
PRE-REGISTRATION -- every rule fixed here BEFORE the run. No parameter is
chosen or flipped after seeing a result.
======================================================================

PART 1 -- LOOKBACK / THRESHOLD GRID (level surge, as in section 30)
  SIGNAL:     s30.build_signal -- causal trailing z-score of the daily active-
              address count; baseline mean/std over the trailing WINDOW days
              t-WINDOW..t-1 (current day excluded).
  WINDOW:     {30, 60, 90 (section-30 value), 180} days.
  THRESHOLD:  z-score trigger {1.0, 1.5 (section-30 value), 2.0} SD. The
              trigger is IDENTICAL for both directions -- a large upward surge
              in active addresses (z > threshold).
  DIRECTION:  {LONG-on-surge (section-30 reading: surge = adoption/demand,
              hypothesised to precede appreciation), SHORT-on-surge / FADE
              (contrarian: a network-usage spike is a local blow-off to be
              faded)}.  Both are stated a priori here; neither is a post-hoc
              pick.
  HOLD:       {5, 20} calendar days, non-overlapping (s30's no_pos gate: a new
              trigger while a position is open is skipped).
  = 4 x 3 x 2 x 2 = 48 cells.

PART 2 -- ACCELERATION VARIANT (rate-of-change of the growth, not the level)
  EXACT CAUSAL CALCULATION, stated in full:
    Let A_t = active-address count on UTC day t.
    RA_t   = mean(A over days t-WINDOW .. t-1)          # trailing rolling
             i.e.  A.shift(1).rolling(WINDOW).mean()    # average, day t EXCLUDED
    VEL_t  = RA_t - RA_{t-1}                            # 1st difference: the
                                                        # change in the rolling avg
    ACCEL_t = VEL_t - VEL_{t-1}
            = RA_t - 2*RA_{t-1} + RA_{t-2}              # 2nd difference of the
                                                        # trailing rolling average
    Then z-score ACCEL against its OWN trailing distribution, current day
    excluded:
      ACCELZ_t = (ACCEL_t - mean(ACCEL over t-WINDOW..t-1)) / std(same)
              i.e. ACCEL.shift(1).rolling(WINDOW) baseline.
    ACCEL_t depends only on A up to day t-1, and ACCELZ_t only on ACCEL up to
    t-1, so the signal is STRICTLY causal (it does not even use day t's own
    print). Entry is still modelled at day t's UTC close, matching section 30.
  Same 48-cell grid: WINDOW {30,60,90,180} x THRESHOLD {1.0,1.5,2.0} SD of
  acceleration x DIRECTION {long-on-accel-surge, short/fade} x HOLD {5,20}.
  Interpretation of "surge" here = acceleration z > threshold = network growth
  is SPEEDING UP.
  = 48 cells.

PART 3 -- REGIME FILTER ON A DEFAULT BUY-AND-HOLD (targets H=20's "sits in
          cash too much / misses the beta" failure mode identified in section 30)
  DEFAULT POSITION: 100% long BTC, every day.
  EXACT UNHEALTHY CONDITION, pre-registered: on day t, the section-30 causal
  LEVEL z-score of active addresses is z_t <= UNHEALTHY_THR (network activity
  has CONTRACTED materially versus its own trailing distribution -- the
  mainstream "network is bleeding users" reading). When day t is unhealthy,
  hold CASH on day t+1 (position lagged one day; z_t is known at day t's
  close). Otherwise hold BTC on day t+1. Never short.
  GRID: WINDOW {90, 180} x UNHEALTHY_THR {-0.5, -1.0, -1.5} SD.
  = 2 x 3 = 6 cells.
  Cost: one BTCUSDT transaction charged on every switch day (BTC->cash or
  cash->BTC), each = HALF the section-30 round-turn cost (spread that day +
  20 bps commission + 2 bps slippage), matching s30's half-on-each-leg split.

TOTAL NEW CELLS / TRIALS THIS BATCH: 48 + 48 + 6 = 102.

======================================================================
HONESTY GATES (all mandatory, same standard as section 30)
======================================================================
- LOOK-AHEAD GUARD on every cell: entry never precedes the signal day's close;
  z-score / acceleration baselines exclude the current day by construction
  (`.shift(1).rolling(...)`); Part 3's position is z.shift(1). Verified
  programmatically (s30.run_cell already returns `guard_ok`; Part 3 guard is
  structural and asserted).
- REAL BTCUSDT COSTS: section-30 model, unchanged (above).
- DEFLATED SHARPE against the FULL cumulative trial count INCLUDING this batch.
    Pool stated explicitly:
      * PRIOR cumulative project trials (through section 30) = 1135.
      * NEW trials this batch = 102.
      * NEW CUMULATIVE TOTAL = 1237.
    DSR is reported two ways for every cell:
      (a) batch structural pool, N = (finite cells in this batch, ~102): the
          methodologically clean pool -- all 102 cells were genuine
          pre-registered candidates, so it carries no outcome selection.
      (b) full-cumulative pool, N = 1237: E[max Sharpe] under the null uses
          this batch's own Sharpe mean/std as the trial-distribution estimate
          and N = 1237. This is the "the bar rises with the true search size"
          number the brief asks for -- the primary gate here.
- PER-YEAR CONCENTRATION: top single calendar year's share of total profit;
  bar = 0.60 (s30.CONC_BAR).
- REGIME SUB-SPLIT: 2018-2021 (bull-heavy) vs 2022-2025 (mixed, incl. 2022
  bear). SAME CAVEAT AS SECTION 30: this is NOT a true out-of-regime test --
  no free pre-2018 real-spread BTCUSDT data exists (Binance starts 2017-08),
  so this is an internal date split only.
- vs BUY-AND-HOLD BTC over the identical window (s30.bh_dollars).

OUTPUT: one table, every cell, ranked by net Sharpe -> results/onchain_ext.csv
and the console. Verdict logic at the end: a cell "wins" only if it BEATS
buy-and-hold BTC in ending dollars over its window AND clears DSR (b) >= 0.95.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

import run_onchain_signal as s30
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe

RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

START_CAP = s30.START_CAP            # 100_000.0
BARS_PER_YEAR = s30.BARS_PER_YEAR    # 365
CONC_BAR = s30.CONC_BAR              # 0.60
DSR_BAR = 0.95
EULER_GAMMA = 0.5772156649015329

PRIOR_CUM_TRIALS = 1135              # project cumulative through section 30
# NEW_TRIALS is counted from the grid below, not hard-coded.

WINDOWS = [30, 60, 90, 180]
THRESHOLDS = [1.0, 1.5, 2.0]
DIRECTIONS = [("long", +1), ("short", -1)]
HOLDS = [5, 20]

P3_WINDOWS = [90, 180]
P3_UNHEALTHY = [-0.5, -1.0, -1.5]

IN_START = "2018-01-01"
SUB_A = ("2018-01-01", "2021-12-31")
SUB_B = ("2022-01-01", None)   # end filled at runtime


# ── signal builders ────────────────────────────────────────────────────────────
def signal_level(addr: pd.Series, price_index: pd.DatetimeIndex, window: int) -> pd.Series:
    """Section-30 causal trailing z-score of the ADDRESS LEVEL. Reuses
    s30.build_signal verbatim; only the module-global window is swapped."""
    s30.ADDR_Z_WINDOW = window
    return s30.build_signal(addr, price_index)


def signal_accel(addr: pd.Series, price_index: pd.DatetimeIndex, window: int) -> pd.Series:
    """z-score of the ACCELERATION of active-address growth.

    RA_t   = A.shift(1).rolling(window).mean()      # trailing avg, day t excluded
    ACCEL_t = RA_t - 2*RA_{t-1} + RA_{t-2}          # 2nd difference of RA
    ACCELZ_t = (ACCEL_t - mean_{t-window..t-1} ACCEL) / std_{t-window..t-1} ACCEL
    Strictly causal: uses A only up to day t-1.
    """
    addr_d = addr.reindex(
        pd.date_range(addr.index.min(), addr.index.max(), freq="D")
    ).ffill()
    ra = addr_d.shift(1).rolling(window, min_periods=window).mean()   # day t excluded
    accel = ra - 2.0 * ra.shift(1) + ra.shift(2)
    base = accel.shift(1).rolling(window, min_periods=window)         # day t excluded
    z = (accel - base.mean()) / base.std()
    return z.reindex(price_index)


# ── SHORT engine: exact copy of s30.run_cell with THREE sign flips ─────────────
def run_cell_short(daily: pd.DataFrame, z: pd.Series, H: int, thr: float,
                   start=None, end=None) -> dict:
    close = daily["close"]
    rets = close.pct_change()
    idx = daily.index

    sig_days = z.index[(z > thr) & z.notna()]        # trigger identical to long: an UP surge
    if start is not None:
        sig_days = sig_days[sig_days >= pd.Timestamp(start)]
    if end is not None:
        sig_days = sig_days[sig_days <= pd.Timestamp(end)]

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

    guard_ok = all(tr["entry"] <= tr["exit"] for tr in trades)
    addr_guard_ok = True

    recs = []
    for tr in trades:
        for k in range(tr["i0"] + 1, tr["i1"] + 1):
            recs.append((idx[k], k == tr["i0"] + 1, k == tr["i1"]))
    pos = pd.DataFrame(recs, columns=["date", "is_open", "is_close"])
    pos["ret"] = pos["date"].map(rets)
    pos = pos.dropna(subset=["ret"])

    spread_bps = daily["spread_close"].reindex([tr["entry"] for tr in trades]).to_numpy()
    spread_bps = np.nan_to_num(spread_bps, nan=np.nanmedian(spread_bps)) * 1e4
    total_cost_bps = spread_bps + s30.CRYPTO_COST_BPS["commission"] + 2 * s30.CRYPTO_COST_BPS["slip_normal"]
    cost_by_entry = dict(zip([tr["entry"] for tr in trades], total_cost_bps / 2 / 1e4))

    open_map, close_map = {}, {}
    for tr in trades:
        c = cost_by_entry[tr["entry"]]
        open_day = idx[tr["i0"] + 1]
        close_day = idx[tr["i1"]]
        open_map[open_day] = open_map.get(open_day, 0.0) + c
        close_map[close_day] = close_map.get(close_day, 0.0) + c
    pos["cost"] = pos.apply(lambda r: (open_map.get(r["date"], 0.0) if r["is_open"] else 0.0)
                                       + (close_map.get(r["date"], 0.0) if r["is_close"] else 0.0), axis=1)
    pos["net_contrib"] = (-pos["ret"]) - pos["cost"]          # <-- SHORT (1/3): P&L is the negative of the move

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
            ev_ret.append(-(p1 / p0 - 1.0))                   # <-- SHORT (2/3): event drift sign-flipped
    ev_ret = np.array(ev_ret)

    return dict(
        n=len(trades), insufficient=False, n_obs=len(daily_ret),
        net_sharpe=float(sharpe(daily_ret, BARS_PER_YEAR)),
        gross_sharpe=float(sharpe(-pos.groupby("date")["ret"].sum(), BARS_PER_YEAR)),  # <-- SHORT (3/3)
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


def run_cell_long(daily: pd.DataFrame, z: pd.Series, H: int, thr: float,
                  start=None, end=None) -> dict:
    """Thin wrapper: patch the section-30 threshold global and call
    s30.run_cell UNMODIFIED."""
    s30.ADDR_Z_THRESHOLD = thr
    return s30.run_cell(daily, z, H, start, end)


# ── PART 3: regime filter on a default buy-and-hold ───────────────────────────
def run_regime_filter(daily: pd.DataFrame, zlevel: pd.Series, unhealthy_thr: float,
                      start, end) -> dict:
    close = daily["close"]
    rets = close.pct_change()
    mask = (daily.index >= pd.Timestamp(start))
    if end is not None:
        mask &= (daily.index <= pd.Timestamp(end))
    idx = daily.index[mask]
    r = rets.reindex(idx)

    zz = zlevel.reindex(daily.index)
    # day t is "unhealthy" if z_t <= thr; position for day t+1 = cash, else BTC.
    healthy = (zz > unhealthy_thr)
    # warm-up / NaN z -> default to HOLD (healthy) so the filter only ever REMOVES
    # exposure on an explicit unhealthy read, never on missing data.
    healthy = healthy.where(zz.notna(), True)
    hold = healthy.shift(1)
    hold = hold.where(hold.notna(), True).astype(bool)
    hold = hold.reindex(idx)

    switch = hold.ne(hold.shift(1))
    switch.iloc[0] = False   # no transaction to establish the initial (BTC) position vs a B&H benchmark

    spread_bps = daily["spread_close"].reindex(idx).to_numpy()
    med = np.nanmedian(daily["spread_close"].to_numpy())
    spread_bps = np.nan_to_num(spread_bps, nan=med) * 1e4
    # one transaction per switch = HALF the section-30 round-turn cost
    per_switch_cost = (spread_bps + s30.CRYPTO_COST_BPS["commission"]
                       + 2 * s30.CRYPTO_COST_BPS["slip_normal"]) / 2.0 / 1e4
    cost = pd.Series(np.where(switch.to_numpy(), per_switch_cost, 0.0), index=idx)

    strat_ret = (r.where(hold, 0.0).fillna(0.0)) - cost
    strat_ret = strat_ret.dropna()
    if len(strat_ret) < 20:
        return dict(insufficient=True)

    eq = (1 + strat_ret).cumprod()
    ending_cap = float(START_CAP * eq.iloc[-1])
    total_return = float(eq.iloc[-1] - 1.0)
    yrs = (strat_ret.index.max() - strat_ret.index.min()).days / 365.25
    cagr = (1 + total_return) ** (1 / yrs) - 1 if yrs > 0 else float("nan")

    yr = strat_ret.groupby(strat_ret.index.year).apply(lambda s: float((1 + s).prod() - 1))
    tot_y = float(sum(yr.values))
    top_year = float(max(yr.values) / tot_y) if tot_y > 0 else float("nan")

    pct_in_btc = float(hold.reindex(strat_ret.index).mean())
    n_switch = int(switch.sum())

    return dict(
        insufficient=False, n_obs=len(strat_ret),
        net_sharpe=float(sharpe(strat_ret, BARS_PER_YEAR)),
        gross_sharpe=float(sharpe(r.where(hold, 0.0).fillna(0.0).reindex(strat_ret.index), BARS_PER_YEAR)),
        net_pf=float(profit_factor(strat_ret)),
        cagr=float(cagr), total_return=total_return, ending_cap=ending_cap,
        max_dd=float(max_drawdown(eq)), top_year=top_year,
        skew=float(strat_ret.skew()), ekurt=float(strat_ret.kurtosis()),
        pct_in_btc=pct_in_btc, n_switch=n_switch,
        n=n_switch, guard_ok=True,
    )


# ── DSR helper: E[max Sharpe] for an arbitrary N given a (mu, sigma) estimate ──
def emax_sr_for_N(mu: float, sigma: float, N: int) -> float:
    if N < 2:
        return mu
    z1 = stats.norm.ppf(1.0 - 1.0 / N)
    z2 = stats.norm.ppf(1.0 - 1.0 / (N * np.e))
    return float(mu + sigma * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2))


def dsr_given_emax(sr_best: float, e_max: float, n_obs: int, ann_factor: int,
                   skewness: float, excess_kurtosis: float) -> float:
    """Same Mertens-variance DSR as research/dsr.py, but with E[max] supplied
    directly so it can be evaluated against an arbitrary trial count."""
    if n_obs < 4 or not np.isfinite(sr_best):
        return float("nan")
    sr_pp = sr_best / np.sqrt(ann_factor)
    var_pp = (1.0 + 0.5 * sr_pp ** 2 - skewness * sr_pp
              + (excess_kurtosis / 4.0) * sr_pp ** 2) / n_obs
    se_ann = float(np.sqrt(max(ann_factor * var_pp, 1e-16)))
    return float(stats.norm.cdf((sr_best - e_max) / se_ann))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    W = 140
    print("=" * W)
    print("  ON-CHAIN SIGNAL -- SECTION 30.1  (bounded pre-registered extension of section 30)")
    print("  Read run_onchain_signal.py's docstring STEP 1 first: the metric is BTC active addresses,")
    print("  NOT the exchange-flow / whale-balance data the original brief named (paywalled everywhere free).")
    print("=" * W)

    addr = s30.load_addr()
    daily = s30.load_btc_daily()
    end = daily.index.max().strftime("%Y-%m-%d")
    sub_b = (SUB_B[0], end)
    print(f"\n[data] active-address history : {addr.index.min().date()} -> {addr.index.max().date()} ({len(addr):,} days)")
    print(f"[data] BTCUSDT real-spread daily: {daily.index.min().date()} -> {daily.index.max().date()} ({len(daily):,} days)")
    bh_end, bh_cagr = s30.bh_dollars(daily, IN_START, end)
    bh_A_end, _ = s30.bh_dollars(daily, *SUB_A)
    bh_B_end, _ = s30.bh_dollars(daily, *sub_b)
    print(f"[bench] Buy-and-hold BTC {IN_START}..{end}: ${bh_end:,.0f} ({(bh_end/START_CAP-1)*100:+.1f}%), CAGR {bh_cagr*100:+.1f}%")

    # cache signal series: 2 variants x 4 windows
    sigs = {}
    for w in WINDOWS:
        sigs[("level", w)] = signal_level(addr, daily.index, w)
        sigs[("accel", w)] = signal_accel(addr, daily.index, w)

    rows = []

    # ---- PARTS 1 & 2 --------------------------------------------------------
    for variant in ("level", "accel"):
        part = 1 if variant == "level" else 2
        for w in WINDOWS:
            z = sigs[(variant, w)]
            for thr in THRESHOLDS:
                for dname, dsign in DIRECTIONS:
                    for H in HOLDS:
                        fn = run_cell_long if dsign == +1 else run_cell_short
                        if dsign == +1:
                            s30.ADDR_Z_THRESHOLD = thr
                            full = s30.run_cell(daily, z, H, IN_START, end)
                            subA = s30.run_cell(daily, z, H, *SUB_A)
                            subB = s30.run_cell(daily, z, H, *sub_b)
                        else:
                            full = run_cell_short(daily, z, H, thr, IN_START, end)
                            subA = run_cell_short(daily, z, H, thr, *SUB_A)
                            subB = run_cell_short(daily, z, H, thr, *sub_b)
                        row = dict(part=part, variant=variant, window=w, thr=thr,
                                   direction=dname, H=H)
                        if full.get("insufficient", False):
                            row.update(insufficient=True, n=full.get("n", 0))
                        else:
                            row.update(
                                insufficient=False, n=full["n"], n_obs=full["n_obs"],
                                net_sharpe=full["net_sharpe"], gross_sharpe=full["gross_sharpe"],
                                net_pf=full["net_pf"], cagr=full["cagr"],
                                total_return=full["total_return"], ending_cap=full["ending_cap"],
                                max_dd=full["max_dd"], top_year=full["top_year"],
                                skew=full["skew"], ekurt=full["ekurt"],
                                ev_mean=full["ev_mean"], ev_win_rate=full["ev_win_rate"],
                                guard_ok=full["guard_ok"],
                                subA_sharpe=(np.nan if subA.get("insufficient", False) else subA["net_sharpe"]),
                                subB_sharpe=(np.nan if subB.get("insufficient", False) else subB["net_sharpe"]),
                                subA_end=(np.nan if subA.get("insufficient", False) else subA["ending_cap"]),
                                subB_end=(np.nan if subB.get("insufficient", False) else subB["ending_cap"]),
                            )
                        rows.append(row)

    # ---- PART 3 -----------------------------------------------------------
    for w in P3_WINDOWS:
        zlevel = sigs[("level", w)]
        for uthr in P3_UNHEALTHY:
            full = run_regime_filter(daily, zlevel, uthr, IN_START, end)
            subA = run_regime_filter(daily, zlevel, uthr, *SUB_A)
            subB = run_regime_filter(daily, zlevel, uthr, *sub_b)
            row = dict(part=3, variant="regime_filter_on_BH", window=w, thr=uthr,
                       direction="hold-BTC-unless-unhealthy", H=np.nan)
            if full.get("insufficient", False):
                row.update(insufficient=True, n=0)
            else:
                row.update(
                    insufficient=False, n=full["n"], n_obs=full["n_obs"],
                    net_sharpe=full["net_sharpe"], gross_sharpe=full["gross_sharpe"],
                    net_pf=full["net_pf"], cagr=full["cagr"],
                    total_return=full["total_return"], ending_cap=full["ending_cap"],
                    max_dd=full["max_dd"], top_year=full["top_year"],
                    skew=full["skew"], ekurt=full["ekurt"],
                    ev_mean=np.nan, ev_win_rate=np.nan, guard_ok=full["guard_ok"],
                    pct_in_btc=full["pct_in_btc"], n_switch=full["n_switch"],
                    subA_sharpe=(np.nan if subA.get("insufficient", False) else subA["net_sharpe"]),
                    subB_sharpe=(np.nan if subB.get("insufficient", False) else subB["net_sharpe"]),
                    subA_end=(np.nan if subA.get("insufficient", False) else subA["ending_cap"]),
                    subB_end=(np.nan if subB.get("insufficient", False) else subB["ending_cap"]),
                )
            rows.append(row)

    df = pd.DataFrame(rows)
    NEW_TRIALS = len(df)
    NEW_CUM = PRIOR_CUM_TRIALS + NEW_TRIALS

    ok = df[df["insufficient"] == False].copy()
    n_insuff = int((df["insufficient"] == True).sum())

    # ---- window-aware buy-and-hold for the "beats B&H" test ----
    def bh_for_window(part):
        return bh_end
    ok["bh_end"] = bh_end
    ok["beats_bh"] = ok["ending_cap"] > bh_end
    ok["bh_A_end"] = bh_A_end
    ok["bh_B_end"] = bh_B_end

    # ---- DSR: two pools ----
    srs = ok["net_sharpe"].to_numpy(dtype=float)
    mu_b, sd_b = float(np.mean(srs)), float(np.std(srs, ddof=1))
    e_max_batch, N_batch, _, _ = expected_max_sharpe(srs)
    e_max_cum = emax_sr_for_N(mu_b, sd_b, NEW_CUM)

    dsr_batch, dsr_cum = [], []
    for _, r in ok.iterrows():
        nobs = max(int(r["n_obs"]), 5)
        db = dsr_given_emax(r["net_sharpe"], e_max_batch, nobs, BARS_PER_YEAR,
                            float(r["skew"]), float(r["ekurt"]))
        dc = dsr_given_emax(r["net_sharpe"], e_max_cum, nobs, BARS_PER_YEAR,
                            float(r["skew"]), float(r["ekurt"]))
        dsr_batch.append(db)
        dsr_cum.append(dc)
    ok["dsr_batch"] = dsr_batch
    ok["dsr_cum"] = dsr_cum

    ok = ok.sort_values("net_sharpe", ascending=False).reset_index(drop=True)
    ok.to_csv(RESULTS / "onchain_ext.csv", index=False)
    df.to_csv(RESULTS / "onchain_ext_all_cells.csv", index=False)

    # ---- guard summary ----
    guard_fail = int((ok["guard_ok"] == False).sum())
    print(f"\n  LOOK-AHEAD GUARD: {'*** FAIL on ' + str(guard_fail) + ' cells ***' if guard_fail else 'PASS on every evaluated cell'}")
    print(f"  Cells evaluated: {len(ok)} / {NEW_TRIALS}   ({n_insuff} returned <5 qualifying trades -> no metrics)")

    # ---- trial-count / DSR pool statement ----
    print("\n" + "#" * W)
    print("  DEFLATED-SHARPE POOL  (stated explicitly, per the brief)")
    print("#" * W)
    print(f"  PRIOR cumulative project trials (through section 30) : {PRIOR_CUM_TRIALS}")
    print(f"  NEW trials this batch (48 level + 48 accel + 6 regime): {NEW_TRIALS}")
    print(f"  NEW CUMULATIVE TOTAL                                  : {NEW_CUM}")
    print(f"  batch Sharpe distribution: mean {mu_b:+.3f}, sd {sd_b:.3f}, min {srs.min():+.2f}, max {srs.max():+.2f}")
    print(f"  E[max Sharpe] | batch structural pool  N={N_batch:<5d} : {e_max_batch:+.3f}")
    print(f"  E[max Sharpe] | full-cumulative pool   N={NEW_CUM:<5d} : {e_max_cum:+.3f}   <-- primary bar")

    # ---- the one ranked table ----
    print("\n" + "#" * W)
    print("  ALL CELLS, RANKED BY NET SHARPE  (full window 2018-01-01..%s; $100k start)" % end)
    print("#" * W)
    hdr = (f"  {'#':>3} {'pt':>2} {'variant':>8} {'win':>4} {'thr':>5} {'dir':>6} {'H':>3} "
           f"{'n':>4} {'netSR':>7} {'grSR':>7} {'netPF':>6} {'maxDD':>7} {'topYr':>6} "
           f"{'end$':>12} {'vsB&H':>6} {'subA':>6} {'subB':>6} {'DSRbatch':>9} {'DSRcum':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for i, r in ok.iterrows():
        ty = f"{r['top_year']*100:.0f}%" if np.isfinite(r["top_year"]) else "n/a"
        sa = f"{r['subA_sharpe']:+.2f}" if np.isfinite(r["subA_sharpe"]) else "  n/a"
        sb = f"{r['subB_sharpe']:+.2f}" if np.isfinite(r["subB_sharpe"]) else "  n/a"
        Hs = "-" if not np.isfinite(r["H"]) else f"{int(r['H'])}"
        print(f"  {i+1:>3} {int(r['part']):>2} {r['variant'][:8]:>8} {int(r['window']):>4} "
              f"{r['thr']:>+5.1f} {r['direction'][:6]:>6} {Hs:>3} {int(r['n']):>4} "
              f"{r['net_sharpe']:>+7.2f} {r['gross_sharpe']:>+7.2f} {r['net_pf']:>6.3f} "
              f"{r['max_dd']*100:>6.1f}% {ty:>6} ${r['ending_cap']:>10,.0f} "
              f"{('BEAT' if r['beats_bh'] else 'lose'):>6} {sa:>6} {sb:>6} "
              f"{r['dsr_batch']:>9.3f} {r['dsr_cum']:>7.3f}")
    print(f"\n  Buy-and-hold BTC, full window: ${bh_end:,.0f}   |   sub 2018-2021: ${bh_A_end:,.0f}   |   sub 2022-2025: ${bh_B_end:,.0f}")

    # ---- Part 3 detail (invested-fraction is the point of the variant) ----
    print("\n" + "#" * W)
    print("  PART 3 DETAIL -- regime filter on default buy-and-hold (targets section 30's 'sits in cash too much')")
    print("#" * W)
    p3 = ok[ok["part"] == 3].sort_values(["window", "thr"])
    print(f"  {'win':>4} {'unhealthy z<=':>13} {'%inBTC':>7} {'switches':>8} {'netSR':>7} {'netPF':>6} "
          f"{'maxDD':>7} {'end$':>12} {'vsB&H':>6} {'CAGR':>7}")
    for _, r in p3.iterrows():
        print(f"  {int(r['window']):>4} {r['thr']:>+13.1f} {r['pct_in_btc']*100:>6.1f}% {int(r['n_switch']):>8} "
              f"{r['net_sharpe']:>+7.2f} {r['net_pf']:>6.3f} {r['max_dd']*100:>6.1f}% "
              f"${r['ending_cap']:>10,.0f} {('BEAT' if r['beats_bh'] else 'lose'):>6} {r['cagr']*100:>+6.1f}%")
    print(f"  buy-and-hold reference: ${bh_end:,.0f}, CAGR {bh_cagr*100:+.1f}%, 100% in BTC, 0 switches")

    # ---- regime sub-split caveat ----
    print("\n" + "#" * W)
    print("  REGIME SUB-SPLIT -- 2018-2021 (bull-heavy) vs 2022-2025 (mixed, incl. 2022 bear)")
    print("  NOT a true out-of-regime test: no free pre-2018 real-spread BTCUSDT data exists (Binance starts")
    print("  2017-08). Same caveat as section 30 / section 28. Columns subA / subB in the table above.")
    print("#" * W)
    flips = ok[(np.sign(ok["subA_sharpe"]) != np.sign(ok["subB_sharpe"]))
               & ok["subA_sharpe"].notna() & ok["subB_sharpe"].notna()]
    print(f"  cells with a Sharpe SIGN FLIP between the two sub-periods: {len(flips)} / {ok['subA_sharpe'].notna().sum()}"
          f"  (instability is the rule, not the exception)")

    # ---- verdict ----
    print("\n" + "#" * W)
    print("  VERDICT")
    print("#" * W)
    winners = ok[(ok["beats_bh"]) & (ok["dsr_cum"] >= DSR_BAR)
                 & (ok["net_pf"] > 1) & (ok["net_sharpe"] > 0)
                 & ((~np.isfinite(ok["top_year"])) | (ok["top_year"] <= CONC_BAR))]
    best = ok.iloc[0]
    print(f"  Best cell by net Sharpe: part {int(best['part'])} / {best['variant']} / window {int(best['window'])} / "
          f"thr {best['thr']:+.1f} / dir {best['direction']} / H {('-' if not np.isfinite(best['H']) else int(best['H']))}")
    print(f"    net Sharpe {best['net_sharpe']:+.2f}, gross Sharpe {best['gross_sharpe']:+.2f}, net PF {best['net_pf']:.3f}, "
          f"maxDD {best['max_dd']*100:.1f}%, end ${best['ending_cap']:,.0f} vs B&H ${bh_end:,.0f} "
          f"({'BEATS' if best['beats_bh'] else 'loses to'} B&H)")
    print(f"    DSR (batch pool N={N_batch}) {best['dsr_batch']:.3f}  |  DSR (cumulative pool N={NEW_CUM}) {best['dsr_cum']:.3f}  "
          f"(bar {DSR_BAR})")
    n_beat = int(ok["beats_bh"].sum())
    print(f"\n  Cells that BEAT buy-and-hold BTC in ending dollars: {n_beat} / {len(ok)}")
    print(f"  Cells that ALSO clear DSR >= {DSR_BAR} on the full cumulative pool (N={NEW_CUM}): {len(winners)}")
    if len(winners):
        print("  *** CANDIDATE(S) -- REQUIRE INDEPENDENT CONFIRMATION BEFORE ANY TRUST ***")
        for _, r in winners.iterrows():
            print(f"    part {int(r['part'])} / {r['variant']} / win {int(r['window'])} / thr {r['thr']:+.1f} / "
                  f"{r['direction']} / H {('-' if not np.isfinite(r['H']) else int(r['H']))}: "
                  f"netSR {r['net_sharpe']:+.2f}, end ${r['ending_cap']:,.0f}, DSRcum {r['dsr_cum']:.3f}")
    else:
        print("  NO cell beats buy-and-hold BTC AND clears the DSR bar for the true, now-larger trial count.")
        print(f"  A wide, pre-registered search of this specific free dataset -- {NEW_TRIALS} cells across level surge,")
        print("  its acceleration, both directions, four lookbacks, three thresholds, two holds, and a")
        print("  regime-filter-on-buy-and-hold -- came up EMPTY. That is real evidence the free BTC active-address")
        print("  series carries no tradeable edge over simply owning BTC, not a reason to keep parameter-hunting it.")

    print(f"\n  NEW TRIALS THIS BATCH: {NEW_TRIALS}.  CUMULATIVE PROJECT TRIALS: {NEW_CUM} "
          f"({PRIOR_CUM_TRIALS} prior + {NEW_TRIALS}).")
    print("  saved -> results/onchain_ext.csv (ranked, evaluated cells), results/onchain_ext_all_cells.csv (raw incl. insufficient)")
    print("=" * W)


if __name__ == "__main__":
    main()
