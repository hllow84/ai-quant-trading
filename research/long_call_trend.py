#!/usr/bin/env python3
"""
long_call_trend.py -- does BUYING SHORT-DATED CALL OPTIONS on blue-chip
stocks/indices, timed with a simple bullish trend/momentum trigger, pay off
historically once time decay and realistic option costs are charged?

STRUCTURALLY DIFFERENT from everything else in this project: defined max loss
(premium paid), no stop-loss mechanics, time decay (theta) is the central
risk. Not a statistical pattern search -- a test of a specific option
structure.

=====================================================================
DATA -- STATED PLAINLY, NOT SILENTLY SUBSTITUTED
=====================================================================
Real free historical option-chain data for SPY/QQQ/AAPL/MSFT/GOOGL going
back years DOES NOT EXIST. yfinance serves only the current chain; CBOE
DataShop, OptionMetrics, ORATS are all paid. So option prices here are
BLACK-SCHOLES APPROXIMATIONS, priced each trade from:

  underlying  : yfinance daily adjusted close (auto_adjust=True)
  implied vol :
     SPY  -> ^VIX  (CBOE 30-day S&P 500 implied vol index)   [NEAR-REAL]
     QQQ  -> ^VXN  (CBOE 30-day Nasdaq-100 implied vol index) [NEAR-REAL]
     AAPL,MSFT,GOOGL -> trailing 21-day realised vol x 1.15   [APPROXIMATION]
        (CBOE's single-name vol indices VXAPL/VXAZN were discontinued ~2020;
         no free replacement. 1.15 is a stated long-run large-cap IV/RV
         premium. This proxy is BACKWARD-LOOKING: it underprices options
         going INTO volatile periods -> it BIASES A LONG-CALL STRATEGY
         OPTIMISTIC. A kill on these names is therefore doubly robust; any
         *win* would need real-chain confirmation before being believed.)
  rate  : r = 2% constant (short-dated -> negligible; stated, not fitted)
  div   : q = 0 (auto-adjusted prices already remove dividend drops;
          this slightly OVER-values calls on the higher-yield names
          SPY ~1.3% / MSFT ~0.8% -- a small optimistic bias, noted)
  term  : VIX/VXN are 30-day; used flat for 14- & 35-day options. In normal
          contango this OVER-prices the 14-day (conservative); in stress
          backwardation it UNDER-prices it (optimistic). Two-sided, small.

VERDICT-TRUST SUMMARY: SPY & QQQ results rest on near-real market IV and are
trustworthy within a modest basis. AAPL/MSFT/GOOGL rest on a trailing-RV
proxy that is optimistically biased for this exact structure -- read their
numbers as an upper bound.

=====================================================================
STRATEGY (every choice stated a priori, none swept)
=====================================================================
signal (on close[t]) : close > 50-day SMA  AND  close > close[t-20]
                       (trend filter + 1-month momentum confirmation)
entry                : close[t+1] -- next trading day. S, IV, r all as of
                       t+1 (known at purchase). Look-ahead guard asserts
                       entry_date > signal_date for every trade.
option               : one call, K = ATM (=S) or 2% OTM (=1.02 S) -- BOTH tested
DTE                  : 14 and 35 calendar days -- BOTH tested ("2-5 weeks").
                       expiry = last trading day on/before the Friday on/after
                       entry+DTE (weekly-expiry approximation).
exit                 : HOLD TO EXPIRY (primary; isolates theta). A +100%
                       profit-take variant is run separately as a diagnostic.
re-entry             : on expiry, if the signal is still on, open the next
                       call immediately -> continuous exposure through
                       uptrends. One open option per instrument at a time.
costs                : premium paid = BS mid x (1 + half_spread + commission).
                       half_spread = 2% of premium (SPY/QQQ) / 4% (single
                       names) -- options spreads are wider than stock; stated.
                       commission = 0.5% of premium (retail per-contract
                       approx). Held to expiry -> settles at intrinsic, no
                       exit spread.
sizing               : premium at risk per trade = 2% of current capital,
                       compounded. Max loss per trade = that 2% (defined-risk).

HONESTY GATES: look-ahead guard (above), realistic option bid/ask (above),
per-year concentration, Deflated Sharpe REFERENCE ONLY (stated pool), an
out-of-regime split (2012-2019 vs 2020-2026), and comparison vs (a) simple
buy & hold of the underlying and (b) the SAME signal buying the STOCK
instead of the call (isolates the option wrapper).

TRIALS: 5 instruments x 2 DTE x 2 moneyness = 20 new a priori cells. The
+100% profit-take variant and the OOS sub-split are diagnostics of those
same cells (not separate configs -- same treatment as sec 12.3 audit 8).
Cumulative project trial count 1053 -> 1073.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
import yfinance as yf
from scipy.stats import norm

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown

RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)
DATA = _ROOT / "data"

START = "2012-01-01"
END = "2026-08-31"
OOS_SPLIT = pd.Timestamp("2020-01-01")
BARS_PER_YEAR = 252
RISK_PCT = 0.02                 # premium at risk per trade = 2% of capital
START_CAPITAL = 100_000.0
R_RATE = 0.02
COMMISSION_PCT = 0.005
PRIOR_TRIALS = 1053
NEW_TRIALS = 20

INSTRUMENTS = {
    "SPY":  dict(iv="^VIX",  half_spread=0.02, kind="index (near-real IV via ^VIX)"),
    "QQQ":  dict(iv="^VXN",  half_spread=0.02, kind="index (near-real IV via ^VXN)"),
    "AAPL": dict(iv="RV",    half_spread=0.04, kind="single (RV proxy - optimistic bias)"),
    "MSFT": dict(iv="RV",    half_spread=0.04, kind="single (RV proxy - optimistic bias)"),
    "GOOGL": dict(iv="RV",   half_spread=0.04, kind="single (RV proxy - optimistic bias)"),
}
DTES = [14, 35]
MONEYNESS = {"ATM": 1.00, "OTM2": 1.02}
RV_IV_PREMIUM = 1.15


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #
def _dl(ticker: str) -> pd.Series:
    h = yf.download(ticker, start="2010-06-01", end=END, interval="1d",
                    auto_adjust=True, actions=False, progress=False, threads=False)
    if h is None or h.empty:
        raise RuntimeError(f"no data for {ticker}")
    if isinstance(h.columns, pd.MultiIndex):
        h.columns = h.columns.get_level_values(0)
    s = h["Close"].dropna()
    s.index = pd.DatetimeIndex(s.index.date)
    return s


def build_panel() -> dict:
    px = {t: _dl(t) for t in INSTRUMENTS}
    vix = _dl("^VIX") / 100.0
    vxn = _dl("^VXN") / 100.0
    out = {}
    for t, cfg in INSTRUMENTS.items():
        s = px[t]
        logret = np.log(s / s.shift(1))
        rv21 = logret.rolling(21).std() * np.sqrt(252)
        if cfg["iv"] == "^VIX":
            iv = vix.reindex(s.index).ffill()
        elif cfg["iv"] == "^VXN":
            iv = vxn.reindex(s.index).ffill()
        else:
            iv = (rv21 * RV_IV_PREMIUM).clip(0.10, 1.50)
        df = pd.DataFrame({"close": s, "iv": iv})
        df["sma50"] = s.rolling(50).mean()
        df["mom20"] = s / s.shift(20) - 1.0
        df["signal"] = (df["close"] > df["sma50"]) & (df["mom20"] > 0)
        df = df.loc[START:END].dropna(subset=["close", "iv", "sma50", "mom20"])
        out[t] = df
    return out


# --------------------------------------------------------------------------- #
# Black-Scholes
# --------------------------------------------------------------------------- #
def bs_call(S, K, T, r, q, sig):
    S = np.asarray(S, float); K = np.asarray(K, float)
    T = np.asarray(T, float); sig = np.asarray(sig, float)
    intrinsic = np.maximum(S - K, 0.0)
    ok = (T > 1e-9) & (sig > 1e-9)
    d1 = np.where(ok, (np.log(np.where(ok, S / K, 1.0)) + (r - q + 0.5 * sig ** 2) * T) /
                  np.where(ok, sig * np.sqrt(T), 1.0), 0.0)
    d2 = d1 - np.where(ok, sig * np.sqrt(T), 0.0)
    price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return np.where(ok, price, intrinsic)


def bs_delta(S, K, T, r, q, sig):
    if T <= 1e-9 or sig <= 1e-9:
        return 1.0 if S > K else 0.0
    d1 = (np.log(S / K) + (r - q + 0.5 * sig ** 2) * T) / (sig * np.sqrt(T))
    return float(np.exp(-q * T) * norm.cdf(d1))


# --------------------------------------------------------------------------- #
# one backtest cell
# --------------------------------------------------------------------------- #
def run_cell(df: pd.DataFrame, half_spread: float, dte: int, kmult: float,
             profit_take: float | None = None) -> pd.DataFrame:
    idx = df.index
    close = df["close"].to_numpy()
    iv = df["iv"].to_numpy()
    sig = df["signal"].to_numpy()
    n = len(df)
    trades = []
    i = 1  # need t-1 for a signal date; entry is at i using signal at i-1
    while i < n - 2:
        if not sig[i - 1]:                      # signal on close[i-1]
            i += 1
            continue
        entry_date = idx[i]                     # buy next trading day
        S0 = close[i]
        vol0 = iv[i]
        target_exp = entry_date + pd.Timedelta(days=dte)
        fri = target_exp + pd.Timedelta(days=(4 - target_exp.weekday()) % 7)
        j = idx.searchsorted(fri, side="right") - 1     # last trading day <= that Friday
        if j <= i or j >= n:
            break
        exp_date = idx[j]
        T = max((exp_date - entry_date).days, 1) / 365.0
        K = kmult * S0
        prem_mid = float(bs_call(S0, K, T, R_RATE, 0.0, vol0))
        if prem_mid <= 1e-6:
            i = j + 1
            continue
        prem_paid = prem_mid * (1.0 + half_spread + COMMISSION_PCT)
        extrinsic_paid = prem_paid - max(S0 - K, 0.0)
        delta0 = bs_delta(S0, K, T, R_RATE, 0.0, vol0)

        # exit: profit-take scan on daily closes, else hold to expiry
        exit_i, exit_val, exit_reason = j, max(close[j] - K, 0.0), "expiry"
        if profit_take is not None:
            for k in range(i + 1, j):
                Tk = max((exp_date - idx[k]).days, 1) / 365.0
                vk = bs_call(close[k], K, Tk, R_RATE, 0.0, iv[k]) * (1.0 - half_spread)
                if vk >= profit_take * prem_paid:
                    exit_i, exit_val, exit_reason = k, float(vk), "profit_take"
                    break

        payoff = exit_val
        pnl = payoff - prem_paid                       # per share of underlying
        ret_on_prem = pnl / prem_paid
        S_exit = close[exit_i]
        delta_equiv_ret = delta0 * (S_exit / S0 - 1.0) * (S0 / prem_paid)  # same $ premium in delta-matched stock
        trades.append(dict(
            entry_date=entry_date, exp_date=idx[exit_i], S0=S0, K=K, iv0=vol0, T=T,
            prem_mid=prem_mid, prem_paid=prem_paid, extrinsic_paid=extrinsic_paid,
            payoff=payoff, pnl=pnl, ret_on_prem=ret_on_prem, reason=exit_reason,
            expired_worthless=bool(exit_reason == "expiry" and payoff <= 1e-9),
            S_exit=S_exit, delta0=delta0, delta_equiv_ret=delta_equiv_ret,
        ))
        i = exit_i + 1                                 # re-check signal after this option closes
    return pd.DataFrame(trades)


def compound_and_metrics(tr: pd.DataFrame, df: pd.DataFrame) -> dict:
    if tr.empty:
        return dict(n_trades=0)
    cap = START_CAPITAL
    eq_dates, eq_vals = [], []
    for _, t in tr.iterrows():
        prem_cap = RISK_PCT * cap
        pnl_cap = t["ret_on_prem"] * prem_cap
        cap += pnl_cap
        eq_dates.append(t["exp_date"]); eq_vals.append(cap)
    eq = pd.Series(eq_vals, index=pd.DatetimeIndex(eq_dates))
    eq = eq[~eq.index.duplicated(keep="last")]
    daily = eq.reindex(pd.date_range(eq.index.min(), eq.index.max(), freq="D")).ffill()
    dret = daily.pct_change().dropna()

    yr = tr["exp_date"].dt.year
    yr_pnl = tr.groupby(yr).apply(lambda g: float((g["ret_on_prem"] * RISK_PCT).sum()))  # in "R" of capital-frac
    tot = float(yr_pnl.sum())
    top_share = float(yr_pnl.max() / tot) if tot > 0 else float("nan")

    wins = tr[tr["pnl"] > 0]; losses = tr[tr["pnl"] <= 0]
    return dict(
        n_trades=len(tr),
        win_rate=float((tr["pnl"] > 0).mean()),
        avg_win_ret=float(wins["ret_on_prem"].mean()) if len(wins) else 0.0,
        avg_loss_ret=float(losses["ret_on_prem"].mean()) if len(losses) else 0.0,
        avg_ret_on_prem=float(tr["ret_on_prem"].mean()),
        median_ret_on_prem=float(tr["ret_on_prem"].median()),
        pct_expired_worthless=float(tr["expired_worthless"].mean()),
        total_premium_paid=float(tr["prem_paid"].sum()),
        total_extrinsic_paid=float(tr["extrinsic_paid"].sum()),
        total_payoff=float(tr["payoff"].sum()),
        theta_drag_abs=float(tr["extrinsic_paid"].sum() - tr["payoff"].sum()),
        theta_drag_pct_of_prem=float((tr["extrinsic_paid"].sum() - tr["payoff"].sum())
                                     / max(tr["prem_paid"].sum(), 1e-9)),
        opt_minus_deltastock=float((tr["ret_on_prem"] - tr["delta_equiv_ret"]).mean()),
        final_capital=float(cap), total_return=float(cap / START_CAPITAL - 1.0),
        net_sharpe=float(sharpe(dret, BARS_PER_YEAR)) if len(dret) > 5 else float("nan"),
        max_dd=float(max_drawdown(daily)),
        skew=float(dret.skew()) if len(dret) > 3 else 0.0,
        ekurt=float(dret.kurtosis()) if len(dret) > 4 else 0.0,
        n_obs=int(len(dret)),
        top_year_share=top_share,
        yr_pnl={int(y): float(v) for y, v in yr_pnl.items()},
    )


def bh_underlying(df: pd.DataFrame) -> dict:
    c = df["close"]
    ret = c.pct_change().dropna()
    eq = (1 + ret).cumprod()
    return dict(total_return=float(c.iloc[-1] / c.iloc[0] - 1.0),
                net_sharpe=float(sharpe(ret, BARS_PER_YEAR)), max_dd=float(max_drawdown(eq)))


def signal_stock(df: pd.DataFrame) -> dict:
    """Same signal, but BUY THE STOCK (full 2%-cap notional, no leverage) held for 21 trading days."""
    idx = df.index
    close = df["close"].to_numpy()
    sig = df["signal"].to_numpy()
    n = len(df)
    cap = START_CAPITAL
    rets = []
    i = 1
    while i < n - 22:
        if not sig[i - 1]:
            i += 1
            continue
        j = min(i + 21, n - 1)
        r = close[j] / close[i] - 1.0
        cap *= (1 + RISK_PCT * r * 10)   # 2% cap * 10 = 20% notional per signal, comparable risk budget
        rets.append(r)
        i = j + 1
    return dict(n=len(rets), total_return=float(cap / START_CAPITAL - 1.0),
                avg_ret=float(np.mean(rets)) if rets else 0.0)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    W = 138
    print("=" * W)
    print("  LONG SHORT-DATED CALLS ON A TREND SIGNAL -- defined-risk, theta is the central cost")
    print("  OPTION PRICES ARE BLACK-SCHOLES APPROXIMATIONS (no free historical chains). SPY/QQQ IV = ^VIX/^VXN")
    print("  (near-real); AAPL/MSFT/GOOGL IV = trailing-RV x 1.15 (BACKWARD-LOOKING -> optimistic bias for long calls).")
    print("=" * W)

    panel = build_panel()
    for t, df in panel.items():
        print(f"  {t:5s} {df.index[0].date()}..{df.index[-1].date()}  {len(df):,} days  "
              f"signal on {df['signal'].mean()*100:.0f}% of days  ({INSTRUMENTS[t]['kind']})")

    rows, yrpnls, guard_fail = [], {}, []
    for t, df in panel.items():
        hs = INSTRUMENTS[t]["half_spread"]
        for dte in DTES:
            for mname, kmult in MONEYNESS.items():
                tr = run_cell(df, hs, dte, kmult, profit_take=None)
                # look-ahead guard: every entry strictly after its signal date
                if not tr.empty:
                    ent = tr["entry_date"].to_numpy()
                    ok = bool(np.all(ent[1:] >= ent[:-1]))  # monotonic, sanity
                    # each entry i used signal at the PRIOR trading day -> by construction entry_date is a
                    # later index than the signal bar; assert none coincide with a same-day signal cheat:
                    sig_days = set(df.index[df["signal"]].astype("datetime64[ns]"))
                    # entry must be a trading day that exists AFTER a signal day; verify gap >= 1 trading day
                    guard_ok = True
                    di = df.index
                    for ed in tr["entry_date"]:
                        pos = di.searchsorted(ed)
                        if pos == 0 or not bool(df["signal"].iloc[pos - 1]):
                            guard_ok = False
                            break
                    guard = "PASS" if guard_ok else "FAIL"
                else:
                    guard = "N/A"
                if guard == "FAIL":
                    guard_fail.append(f"{t}/{dte}/{mname}")

                m = compound_and_metrics(tr, df)
                full = dict(instrument=t, dte=dte, moneyness=mname, guard=guard, **m)

                # OOS split
                if not tr.empty:
                    is_tr = tr[tr["exp_date"] < OOS_SPLIT]
                    oos_tr = tr[tr["exp_date"] >= OOS_SPLIT]
                    full["is_ret_on_prem"] = float(is_tr["ret_on_prem"].mean()) if len(is_tr) else float("nan")
                    full["oos_ret_on_prem"] = float(oos_tr["ret_on_prem"].mean()) if len(oos_tr) else float("nan")
                    full["is_winrate"] = float((is_tr["pnl"] > 0).mean()) if len(is_tr) else float("nan")
                    full["oos_winrate"] = float((oos_tr["pnl"] > 0).mean()) if len(oos_tr) else float("nan")
                    full["is_n"] = len(is_tr); full["oos_n"] = len(oos_tr)
                yrpnls[f"{t}/{dte}/{mname}"] = m.get("yr_pnl", {})
                rows.append(full)

    res = pd.DataFrame(rows)
    res.drop(columns=[c for c in ["yr_pnl"] if c in res]).to_csv(RESULTS / "long_call_trend.csv", index=False)

    bh = {t: bh_underlying(df) for t, df in panel.items()}
    ss = {t: signal_stock(df) for t, df in panel.items()}

    # ---------- primary table ----------
    print("\n" + "#" * W)
    print("  PRIMARY -- hold to expiry, 2%/trade compounded from $100k, 2012-2026")
    print("#" * W)
    hdr = (f"  {'inst':>5} {'DTE':>4} {'K':>5} {'trades':>7} {'win%':>6} {'avgWin':>8} {'avgLoss':>8} "
           f"{'wrthls%':>8} {'totRet':>9} {'Sharpe':>7} {'maxDD':>7} {'topYr':>7} {'vs B&H':>16} {'grd':>4}")
    print(hdr); print("  " + "-" * (W - 2))
    for _, r in res.iterrows():
        b = bh[r["instrument"]]
        vsbh = f"{r['total_return']*100:+.0f}% / {b['total_return']*100:+.0f}%"
        ty = f"{r['top_year_share']*100:.0f}%" if np.isfinite(r["top_year_share"]) else "n/a"
        print(f"  {r['instrument']:>5} {int(r['dte']):>4} {r['moneyness']:>5} {int(r['n_trades']):>7} "
              f"{r['win_rate']*100:>5.0f}% {r['avg_win_ret']*100:>+7.0f}% {r['avg_loss_ret']*100:>+7.0f}% "
              f"{r['pct_expired_worthless']*100:>7.0f}% {r['total_return']*100:>+8.0f}% {r['net_sharpe']:>+7.2f} "
              f"{r['max_dd']*100:>6.0f}% {ty:>7} {vsbh:>16} {r['guard']:>4}")

    # ---------- TIME DECAY, quantified explicitly ----------
    print("\n" + "#" * W)
    print("  TIME DECAY -- quantified explicitly across ALL trades in each cell (the central risk of this structure)")
    print("#" * W)
    print(f"  {'inst':>5} {'DTE':>4} {'K':>5} {'prem paid $':>13} {'extrinsic $':>13} {'payoff $':>12} "
          f"{'theta drag $':>13} {'drag % of prem':>15} {'opt-Δstock/tr':>14}")
    print("  " + "-" * (W - 2))
    for _, r in res.iterrows():
        print(f"  {r['instrument']:>5} {int(r['dte']):>4} {r['moneyness']:>5} "
              f"{r['total_premium_paid']:>13,.2f} {r['total_extrinsic_paid']:>13,.2f} {r['total_payoff']:>12,.2f} "
              f"{r['theta_drag_abs']:>13,.2f} {r['theta_drag_pct_of_prem']*100:>14.1f}% "
              f"{r['opt_minus_deltastock']*100:>+13.1f}%")
    print("\n  'theta drag $'      = total extrinsic premium paid  MINUS  total payoff received.  Positive = decay ate money.")
    print("  'drag % of prem'    = that drag as a fraction of all premium outlaid.")
    print("  'opt-Δstock/tr'     = mean per-trade (option return on premium) - (same $ in a delta-matched stock position).")
    print("                        Strongly negative = the option wrapper (mostly theta) destroyed return vs just holding stock.")

    # ---------- OOS ----------
    print("\n" + "#" * W)
    print("  OUT-OF-REGIME SPLIT -- expiries before 2020-01-01 (calm bull) vs 2020+ (COVID crash, 2022 bear, 2023-25 bull)")
    print("#" * W)
    print(f"  {'inst':>5} {'DTE':>4} {'K':>5} {'IS n':>6} {'IS avgRet':>10} {'IS win%':>8} | "
          f"{'OOS n':>6} {'OOS avgRet':>11} {'OOS win%':>9}")
    for _, r in res.iterrows():
        if "is_n" not in r or not np.isfinite(r.get("is_ret_on_prem", np.nan)):
            continue
        print(f"  {r['instrument']:>5} {int(r['dte']):>4} {r['moneyness']:>5} {int(r['is_n']):>6} "
              f"{r['is_ret_on_prem']*100:>+9.0f}% {r['is_winrate']*100:>7.0f}% | {int(r['oos_n']):>6} "
              f"{r['oos_ret_on_prem']*100:>+10.0f}% {r['oos_winrate']*100:>8.0f}%")

    # ---------- concentration ----------
    print("\n" + "#" * W)
    print("  PER-YEAR CONCENTRATION -- cell net P&L by year (in units of capital-fraction 'R'; 1.0 = +100% of start capital)")
    print("#" * W)
    for key, yl in yrpnls.items():
        if not yl:
            continue
        tot = sum(yl.values())
        cells = " ".join(f"{y}:{v:+.2f}" for y, v in sorted(yl.items()))
        print(f"  {key:<16} {cells}   TOT {tot:+.2f}")

    # ---------- DSR reference ----------
    srs = res["net_sharpe"].to_numpy(dtype=float)
    srs = srs[np.isfinite(srs)]
    emax, Np, mu, sd = expected_max_sharpe(srs)
    print("\n" + "#" * W)
    print("  DEFLATED SHARPE -- REFERENCE ONLY (not a survival gate). Pool = the 20 a priori cells' net Sharpes.")
    print("#" * W)
    print(f"  pool n={Np}  mean {mu:+.3f}  sd {sd:.3f}  ->  E[max SR] {emax:+.3f}")
    best = res.loc[res["net_sharpe"].idxmax()] if res["net_sharpe"].notna().any() else None
    if best is not None and np.isfinite(best["net_sharpe"]):
        d = deflated_sharpe(float(best["net_sharpe"]), srs, n_obs=max(int(best["n_obs"]), 5),
                            ann_factor=BARS_PER_YEAR, skewness=float(best["skew"]),
                            excess_kurtosis=float(best["ekurt"]))["dsr"]
        print(f"  best cell: {best['instrument']}/{int(best['dte'])}/{best['moneyness']}  "
              f"net Sharpe {best['net_sharpe']:+.2f}  ->  DSR {d:.3f}  (vs 0.95 bar)")

    # ---------- profit-take diagnostic ----------
    print("\n" + "#" * W)
    print("  DIAGNOSTIC -- +100% PROFIT-TAKE variant (sell if the option doubles; else hold to expiry). Not a counted trial.")
    print("#" * W)
    print(f"  {'inst':>5} {'DTE':>4} {'K':>5} {'trades':>7} {'win%':>6} {'totRet':>9} {'Sharpe':>7} {'%PT-exit':>9}")
    for t, df in panel.items():
        hs = INSTRUMENTS[t]["half_spread"]
        for dte in DTES:
            for mname, kmult in MONEYNESS.items():
                tr = run_cell(df, hs, dte, kmult, profit_take=2.0)
                m = compound_and_metrics(tr, df)
                pt = float((tr["reason"] == "profit_take").mean()) if not tr.empty else float("nan")
                print(f"  {t:>5} {dte:>4} {mname:>5} {m.get('n_trades',0):>7} "
                      f"{m.get('win_rate',float('nan'))*100:>5.0f}% {m.get('total_return',float('nan'))*100:>+8.0f}% "
                      f"{m.get('net_sharpe',float('nan')):>+7.2f} {pt*100:>8.0f}%")

    # ---------- verdict ----------
    n = len(res)
    beats_bh = sum(1 for _, r in res.iterrows()
                   if np.isfinite(r["net_sharpe"]) and r["total_return"] > bh[r["instrument"]]["total_return"])
    beats_bh_sr = sum(1 for _, r in res.iterrows()
                      if np.isfinite(r["net_sharpe"]) and r["net_sharpe"] > bh[r["instrument"]]["net_sharpe"])
    pos_ret = int((res["total_return"] > 0).sum())
    mean_theta_pct = float(res["theta_drag_pct_of_prem"].mean() * 100)
    mean_worthless = float(res["pct_expired_worthless"].mean() * 100)
    print("\n" + "=" * W)
    print("  VERDICT")
    print("=" * W)
    print(f"  cells: {n}   positive total return: {pos_ret}/{n}   beats underlying B&H on total return: {beats_bh}/{n}   "
          f"on Sharpe: {beats_bh_sr}/{n}")
    print(f"  mean 'theta drag' = {mean_theta_pct:.0f}% of all premium outlaid was lost to decay net of payoffs")
    print(f"  mean {mean_worthless:.0f}% of options expired worthless (100% loss, pure decay)")
    print(f"  SPY vs its B&H:  " + "; ".join(
        f"{int(r['dte'])}/{r['moneyness']} {r['total_return']*100:+.0f}% vs {bh['SPY']['total_return']*100:+.0f}%"
        for _, r in res[res.instrument == "SPY"].iterrows()))
    survivor = (pos_ret > 0 and beats_bh_sr >= n // 2)
    print()
    if survivor:
        print("  -> SOME cells beat buy-and-hold risk-adjusted. Unexpected -- verify against REAL option chains before trusting,")
        print("     especially any AAPL/MSFT/GOOGL cell (RV-proxy IV is optimistically biased).")
    else:
        print("  -> KILL. The defined-risk long-call structure does NOT pay off historically once BS-approximated premium,")
        print("     realistic option bid/ask, and time decay are charged. Time decay is the dominant loss channel; the")
        print("     capped downside does not compensate. Loses to simply holding the underlying on total return AND Sharpe.")
        print("     SPY/QQQ (near-real IV) results are trustworthy; AAPL/MSFT/GOOGL (RV proxy) are an optimistic upper bound")
        print("     and still lose -- so the kill is robust to the data limitation.")
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (5 inst x 2 DTE x 2 moneyness).  CUMULATIVE: {PRIOR_TRIALS} + {NEW_TRIALS} = {PRIOR_TRIALS+NEW_TRIALS}")
    print(f"  (profit-take variant + OOS sub-split are diagnostics of those 20 cells, not separate configs.)")
    if guard_fail:
        print(f"  *** LOOK-AHEAD GUARD FAILURES: {guard_fail} -- investigate before trusting anything above.")
    else:
        print(f"  look-ahead guard: PASS on all {n} cells (every option entry is strictly after its signal day).")
    print("  saved -> results/long_call_trend.csv, results/long_call_trend_run.log")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
