#!/usr/bin/env python3
"""
positioning_ml.py -- can a SHALLOW GRADIENT-BOOSTED MODEL find a non-obvious
pattern in crypto positioning data (funding rate + open interest) that the
simple threshold rule of STATE_OF_PLAY section 18 missed?

Section 18 tested a SIMPLE CONTRARIAN THRESHOLD on funding/OI extremes and
killed it (gross PF ~1.00, no edge). This is a genuinely different question:
does the SAME underlying positioning data contain a more complex signal an
ML model can extract? The critical honesty check is FEATURE IMPORTANCE --
if price-derived control features dominate, the model found nothing new in
positioning and is just re-discovering price patterns (already empty across
1000+ trials). If positioning features genuinely drive predictions, that is
the first real finding of this kind in the project.

DATA -- reused verbatim from section 18 (scripts/download_crypto_funding_oi.py,
notes/crypto_data_availability.md):
  - Funding rate: Binance USD-M, 8h cadence, full history.
  - Open interest: Bybit v5, 1h cadence (Binance OI is 30-day retention only).
  - Cross-venue split stated, not hidden. Bybit OI is the shallow leg and
    sets the usable window: BTC ~2020-11 after 90d percentile warmup, ETH
    ~2021-01.

FEATURES
  positioning (from funding + OI, aligned + lagged with section 18's OWN
  causal machinery -- run_positioning_reversal.align_feature: merge_asof
  backward + 1 extra H1-bar lag; verify_feature_causality asserts every
  source timestamp is strictly before its bar):
    funding_rate, funding_pctl (90d causal rank), funding_roc_8h/24h,
    funding_dev_90d, oi_pctl (90d causal rank), oi_roc_1h/24h/7d,
    oi_accel, funding_x_oi, funding_x_oi_signed, positioning_skew,
    funding_extremity
  price-derived CONTROLS, explicitly prefixed ctrl_ (the whole point is to
  measure whether the model leans on these instead of positioning):
    ctrl_ret_1h/24h/7d, ctrl_vol_24h, ctrl_rsi_14, ctrl_dist_ma168,
    ctrl_hilo_24h
  Every feature is additionally shifted one more H1 bar before use, so a
  prediction at bar t uses only information from <= t-1.

LABEL: forward simple return close[t+H]/close[t]-1, tested at H = 4h and 24h.

MODEL: LightGBM regressor, deliberately shallow + regularized (num_leaves 15,
max_depth 4, lr 0.03, min_child_samples 200, subsample 0.8, colsample 0.7,
reg_lambda 5, reg_alpha 1, <=400 trees early-stopped). The point is testing
whether the DATA carries signal, not building the deepest model.

VALIDATION
  - Strict time-ordered split 60 / 15 / 25 (train / early-stop val / SEALED
    test). No shuffle. H-bar purge at every boundary (labels overlap H bars).
  - Walk-forward: 4 expanding-window folds, per-fold test IC + net Sharpe.
  - Look-ahead guard: verify_feature_causality (funding + OI) PASS asserted;
    all price controls are trailing-window only, then shifted +1 bar.
  - Real crypto costs on the strategy conversion: 20 bps taker round-turn
    (CRYPTO_COST_BPS) + 2 bps slippage round-turn + funding paid on every 8h
    stamp held (charged on the paying side, conservative).
  - Deflated Sharpe: REFERENCE ONLY (not a gate). Pool = the 4 a priori
    "both-features" cells (BTC/ETH x 4h/24h). Stated.
  - Per-year concentration on the sealed-test strategy net return.
  - Out-of-regime: the sealed final 25% IS a strict out-of-sample regime;
    additionally an earliest-half -> latest-half generalization is reported.

ABLATION (the decisive test): for every (instrument, horizon) the model is
trained THREE ways -- positioning features only, ctrl_ (price) features only,
and both -- and their sealed-test IC / net Sharpe compared. If ctrl-only ~=
both and positioning-only ~= 0, the model's signal is price, not positioning.

TRIALS: 4 new a priori cells (BTC, ETH x horizons 4h, 24h -- the "both
features" models predicting forward returns). The positioning-only and
ctrl-only ablations and the walk-forward folds are diagnostics of those same
4 cells, not separate configs (same treatment as section 12.3 audit 8's
perturbation runs). Cumulative project trial count 1049 -> 1053.
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

import lightgbm as lgb
from scipy.stats import spearmanr

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown
from run_sweep_crypto import load_bars, CRYPTO_COST_BPS
from run_positioning_reversal import (
    load_funding, load_oi, align_feature, verify_feature_causality,
)

RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

BARS_PER_YEAR = 365                    # crypto: real obs every calendar day
HORIZONS = {"4h": 4, "24h": 24}
INSTRUMENTS = {
    "BTCUSDT": _ROOT / "data" / "BTCUSDT_H1_2018_2025_binance.csv",
    "ETHUSDT": _ROOT / "data" / "ETHUSDT_H1_2018_2025_binance.csv",
}
PRIOR_TRIALS = 1049
NEW_TRIALS = 4                         # BTC/ETH x 4h/24h, "both features"

TAKER_RT_BPS = CRYPTO_COST_BPS["commission"]          # 20 bps round-turn
SLIP_RT_BPS = 2.0 * CRYPTO_COST_BPS["slip_normal"]    # 1 bps/side -> 2 round-turn
COST_RT_FRAC = (TAKER_RT_BPS + SLIP_RT_BPS) / 1e4     # ~0.0022

LGB_PARAMS = dict(
    objective="regression", n_estimators=400, learning_rate=0.03,
    num_leaves=15, max_depth=4, min_child_samples=200,
    subsample=0.8, subsample_freq=1, colsample_bytree=0.7,
    reg_lambda=5.0, reg_alpha=1.0, random_state=42, n_jobs=-1, verbose=-1,
)

POS_FEATURES = [
    "funding_rate", "funding_pctl", "funding_roc_8h", "funding_roc_24h",
    "funding_dev_90d", "oi_pctl", "oi_roc_1h", "oi_roc_24h", "oi_roc_7d",
    "oi_accel", "funding_x_oi", "funding_x_oi_signed", "positioning_skew",
    "funding_extremity",
]
CTRL_FEATURES = [
    "ctrl_ret_1h", "ctrl_ret_24h", "ctrl_ret_7d", "ctrl_vol_24h",
    "ctrl_rsi_14", "ctrl_dist_ma168", "ctrl_hilo_24h",
]
ALL_FEATURES = POS_FEATURES + CTRL_FEATURES


# --------------------------------------------------------------------------- #
# feature construction
# --------------------------------------------------------------------------- #
def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def build_frame(inst: str, horizon_bars: int) -> tuple[pd.DataFrame, pd.Timestamp, dict]:
    m = load_bars(INSTRUMENTS[inst])
    close = m["mid_close"]

    funding = load_funding(inst)          # funding_time, funding_rate, funding_pctl
    oi = load_oi(inst)                     # oi_time, open_interest, oi_pctl

    f_rate, f_src = align_feature(m.index, funding, "funding_time", "funding_rate")
    f_pctl, _ = align_feature(m.index, funding, "funding_time", "funding_pctl")
    oi_lvl, o_src = align_feature(m.index, oi, "oi_time", "open_interest")
    oi_pctl, _ = align_feature(m.index, oi, "oi_time", "oi_pctl")

    causal = dict(
        funding=verify_feature_causality(m.index, f_src),
        oi=verify_feature_causality(m.index, o_src),
    )

    df = pd.DataFrame(index=m.index)

    # ---- positioning features (all from already-causal, already-lagged series)
    df["funding_rate"] = f_rate
    df["funding_pctl"] = f_pctl
    df["funding_roc_8h"] = f_rate - f_rate.shift(8)
    df["funding_roc_24h"] = f_rate - f_rate.shift(24)
    df["funding_dev_90d"] = f_rate - f_rate.rolling(24 * 90, min_periods=24 * 30).mean()
    df["oi_pctl"] = oi_pctl
    df["oi_roc_1h"] = oi_lvl.pct_change(1)
    df["oi_roc_24h"] = oi_lvl.pct_change(24)
    df["oi_roc_7d"] = oi_lvl.pct_change(24 * 7)
    df["oi_accel"] = df["oi_roc_24h"] - df["oi_roc_7d"] / 7.0
    df["funding_x_oi"] = (f_pctl / 100.0) * (oi_pctl / 100.0)
    df["funding_x_oi_signed"] = f_rate * (oi_pctl / 100.0)
    df["positioning_skew"] = np.sign(f_rate) * df["oi_roc_24h"]
    df["funding_extremity"] = (f_pctl - 50.0).abs()

    # ---- price-derived CONTROLS (trailing windows only)
    df["ctrl_ret_1h"] = close.pct_change(1)
    df["ctrl_ret_24h"] = close.pct_change(24)
    df["ctrl_ret_7d"] = close.pct_change(24 * 7)
    df["ctrl_vol_24h"] = close.pct_change().rolling(24).std()
    df["ctrl_rsi_14"] = _rsi(close, 14)
    df["ctrl_dist_ma168"] = close / close.rolling(168).mean() - 1.0
    df["ctrl_hilo_24h"] = (m["mid_high"].rolling(24).max() - m["mid_low"].rolling(24).min()) / close

    # one extra bar of lag on EVERY feature: prediction at t uses info <= t-1
    df[ALL_FEATURES] = df[ALL_FEATURES].shift(1)

    # label: forward simple return over the horizon
    df["fwd_ret"] = close.shift(-horizon_bars) / close - 1.0
    df["close"] = close
    df["funding_rate_raw_fwd"] = f_rate      # for funding-cost accounting on the strategy

    # usable window: OI start + 90d percentile warmup + a small buffer
    start = oi["oi_time"].min() + pd.Timedelta(days=90) + pd.Timedelta(hours=2)
    df = df[df.index >= start]

    keep = ALL_FEATURES + ["fwd_ret", "close", "funding_rate_raw_fwd"]
    df = df[keep].replace([np.inf, -np.inf], np.nan).dropna(subset=ALL_FEATURES + ["fwd_ret"])
    return df, start, causal


# --------------------------------------------------------------------------- #
# strategy conversion + metrics
# --------------------------------------------------------------------------- #
def strategy_from_predictions(test: pd.DataFrame, pred: np.ndarray, thr: float,
                              horizon_bars: int) -> dict:
    """
    Non-overlapping H-bar holds. Long if pred > +thr, short if pred < -thr,
    else flat. Real costs: taker+slip round-turn + funding paid on every 8h
    stamp held (paying side assumed -- conservative).
    """
    idx = test.index
    close = test["close"].to_numpy()
    fr = test["funding_rate_raw_fwd"].to_numpy()
    n = len(test)
    i = 0
    trades = []
    while i < n - horizon_bars:
        s = pred[i]
        if s > thr:
            direction = 1
        elif s < -thr:
            direction = -1
        else:
            i += 1
            continue
        j = i + horizon_bars
        gross = direction * (close[j] / close[i] - 1.0)
        # funding: ~ one 8h stamp per 8 hourly bars held, charged as a cost
        n_stamps = max(1, horizon_bars // 8)
        seg = fr[i:j]
        mean_abs_funding = float(np.nanmean(np.abs(seg))) if len(seg) else 0.0
        funding_cost = n_stamps * mean_abs_funding
        net = gross - COST_RT_FRAC - funding_cost
        trades.append((idx[j], direction, gross, net))
        i = j  # non-overlapping
    if not trades:
        return dict(n_trades=0)

    tr = pd.DataFrame(trades, columns=["exit_time", "dir", "gross", "net"]).set_index("exit_time")
    daily = tr["net"].groupby(tr.index.normalize()).sum()
    full_idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D", tz="UTC")
    daily = daily.reindex(full_idx).fillna(0.0)
    eq = (1 + daily).cumprod()
    wins = tr.loc[tr["net"] > 0, "net"].sum()
    losses = -tr.loc[tr["net"] < 0, "net"].sum()
    yr = tr.index.year
    yr_net = tr.groupby(yr)["net"].sum()
    tot = float(yr_net.sum())
    top_share = float(yr_net.max() / tot) if tot > 0 else float("nan")
    return dict(
        n_trades=len(tr), n_long=int((tr["dir"] == 1).sum()), n_short=int((tr["dir"] == -1).sum()),
        gross_ret_total=float(tr["gross"].sum()), net_ret_total=tot,
        net_sharpe=float(sharpe(daily, BARS_PER_YEAR)),
        net_pf=float(wins / losses) if losses > 0 else float("inf"),
        max_dd=float(max_drawdown(eq)), win_rate=float((tr["net"] > 0).mean()),
        equity_final=float(eq.iloc[-1]), top_year_share=top_share,
        yr_net={int(y): float(v) for y, v in yr_net.items()},
        avg_cost_frac=float(COST_RT_FRAC),
    )


def buy_and_hold(test: pd.DataFrame) -> dict:
    close = test["close"]
    daily = close.resample("1D").last().dropna()
    ret = daily.pct_change().dropna()
    eq = (1 + ret).cumprod() * (1 - COST_RT_FRAC / 2)
    return dict(net_sharpe=float(sharpe(ret, BARS_PER_YEAR)), max_dd=float(max_drawdown(eq)),
                net_ret_total=float(eq.iloc[-1] - 1.0))


def ic(pred: np.ndarray, y: np.ndarray) -> float:
    if len(y) < 20 or np.std(pred) == 0:
        return float("nan")
    return float(spearmanr(pred, y).correlation)


# --------------------------------------------------------------------------- #
# model fitting
# --------------------------------------------------------------------------- #
def fit_predict(train_X, train_y, val_X, val_y, test_X) -> tuple[lgb.LGBMRegressor, np.ndarray]:
    model = lgb.LGBMRegressor(**LGB_PARAMS)
    model.fit(train_X, train_y, eval_set=[(val_X, val_y)], eval_metric="l2",
              callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)])
    return model, model.predict(test_X)


def time_split(df: pd.DataFrame, horizon_bars: int) -> tuple:
    n = len(df)
    i_tr, i_val = int(n * 0.60), int(n * 0.75)
    p = horizon_bars  # purge overlapping labels at each boundary
    train = df.iloc[: i_tr - p]
    val = df.iloc[i_tr : i_val - p]
    test = df.iloc[i_val:]
    return train, val, test


def walk_forward(df: pd.DataFrame, feats: list[str], horizon_bars: int, n_folds: int = 4) -> list[dict]:
    n = len(df)
    p = horizon_bars
    first = int(n * 0.40)
    step = (n - first) // n_folds
    out = []
    for k in range(n_folds):
        tr_end = first + k * step
        te_end = first + (k + 1) * step if k < n_folds - 1 else n
        train = df.iloc[: tr_end - p]
        te = df.iloc[tr_end:te_end]
        if len(train) < 2000 or len(te) < 200:
            continue
        i_v = int(len(train) * 0.85)
        tr2, va = train.iloc[: i_v - p], train.iloc[i_v:]
        _, pred = fit_predict(tr2[feats], tr2["fwd_ret"], va[feats], va["fwd_ret"], te[feats])
        thr = np.quantile(np.abs(pred), 0.66)
        strat = strategy_from_predictions(te, pred, thr, horizon_bars)
        out.append(dict(fold=k + 1, train_n=len(tr2), test_n=len(te),
                        test_from=str(te.index[0].date()), test_to=str(te.index[-1].date()),
                        test_ic=ic(pred, te["fwd_ret"].to_numpy()),
                        net_sharpe=strat.get("net_sharpe", float("nan")),
                        n_trades=strat.get("n_trades", 0)))
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    W = 132
    print("=" * W)
    print("  POSITIONING-DATA ML TEST -- can a shallow GBM find signal in funding/OI that section 18's threshold rule missed?")
    print(f"  cost/round-turn: {TAKER_RT_BPS:.0f}bps taker + {SLIP_RT_BPS:.0f}bps slip = {COST_RT_FRAC*1e4:.0f}bps, "
          f"+ funding paid per 8h stamp held.  ann.factor {BARS_PER_YEAR}.")
    print("=" * W)

    primary_rows, ablation_rows, wf_rows, importance_rows, perm_rows = [], [], [], [], []
    causal_all = {}

    for inst in INSTRUMENTS:
        for hlabel, hbars in HORIZONS.items():
            df, start, causal = build_frame(inst, hbars)
            causal_all[f"{inst}/{hlabel}"] = causal
            train, val, test = time_split(df, hbars)
            print(f"\n[{inst} / {hlabel}]  rows={len(df):,}  window {df.index[0].date()}..{df.index[-1].date()}  "
                  f"| train {len(train):,}  val {len(val):,}  SEALED test {len(test):,} "
                  f"({test.index[0].date()}..{test.index[-1].date()})")
            print(f"  feature causality: funding={'PASS' if causal['funding'] else 'FAIL'} "
                  f"oi={'PASS' if causal['oi'] else 'FAIL'}")

            bh = buy_and_hold(test)

            # ---- ablation: positioning-only / ctrl-only / both ----
            for fset_name, feats in [("positioning", POS_FEATURES), ("price_ctrl", CTRL_FEATURES),
                                     ("both", ALL_FEATURES)]:
                model, pred = fit_predict(train[feats], train["fwd_ret"], val[feats], val["fwd_ret"],
                                          test[feats])
                test_ic = ic(pred, test["fwd_ret"].to_numpy())
                thr = np.quantile(np.abs(model.predict(train[feats])), 0.66)
                strat = strategy_from_predictions(test, pred, thr, hbars)
                row = dict(instrument=inst, horizon=hlabel, feature_set=fset_name,
                           n_features=len(feats), best_iter=model.best_iteration_,
                           test_ic=test_ic, n_trades=strat.get("n_trades", 0),
                           net_sharpe=strat.get("net_sharpe", float("nan")),
                           net_pf=strat.get("net_pf", float("nan")),
                           max_dd=strat.get("max_dd", float("nan")),
                           net_ret_total=strat.get("net_ret_total", float("nan")),
                           win_rate=strat.get("win_rate", float("nan")),
                           top_year_share=strat.get("top_year_share", float("nan")),
                           bh_sharpe=bh["net_sharpe"], bh_ret_total=bh["net_ret_total"],
                           bh_max_dd=bh["max_dd"])
                ablation_rows.append(row)
                if fset_name == "both":
                    row_p = dict(row); row_p["yr_net"] = strat.get("yr_net", {})
                    primary_rows.append(row_p)

                    # gain importance (split-gain), grouped
                    gains = pd.Series(model.booster_.feature_importance(importance_type="gain"),
                                      index=feats).sort_values(ascending=False)
                    gsum = gains.sum() or 1.0
                    pos_share = gains[gains.index.isin(POS_FEATURES)].sum() / gsum
                    ctrl_share = gains[gains.index.isin(CTRL_FEATURES)].sum() / gsum
                    for rank, (fname, g) in enumerate(gains.items(), 1):
                        importance_rows.append(dict(instrument=inst, horizon=hlabel, rank=rank,
                                                    feature=fname, gain_share=float(g / gsum),
                                                    kind="price_ctrl" if fname in CTRL_FEATURES else "positioning"))
                    print(f"  [both] test IC {test_ic:+.4f} | net Sharpe {strat.get('net_sharpe', float('nan')):+.2f} "
                          f"({strat.get('n_trades', 0)} trades) vs B&H {bh['net_sharpe']:+.2f}")
                    print(f"         GAIN importance share:  positioning {pos_share*100:5.1f}%   "
                          f"price_ctrl {ctrl_share*100:5.1f}%")
                    print(f"         top 6: " + ", ".join(f"{k}={v/gsum*100:.0f}%" for k, v in gains.head(6).items()))

                    # permutation importance on the SEALED test (IC drop)
                    rng = np.random.default_rng(0)
                    base_ic = test_ic
                    for fname in feats:
                        Xp = test[feats].copy()
                        Xp[fname] = rng.permutation(Xp[fname].to_numpy())
                        d_ic = base_ic - ic(model.predict(Xp), test["fwd_ret"].to_numpy())
                        perm_rows.append(dict(instrument=inst, horizon=hlabel, feature=fname,
                                              ic_drop=float(d_ic),
                                              kind="price_ctrl" if fname in CTRL_FEATURES else "positioning"))

            # ---- walk-forward (both features) ----
            for r in walk_forward(df, ALL_FEATURES, hbars):
                r.update(instrument=inst, horizon=hlabel)
                wf_rows.append(r)

    prim = pd.DataFrame(primary_rows)
    abla = pd.DataFrame(ablation_rows)
    imp = pd.DataFrame(importance_rows)
    perm = pd.DataFrame(perm_rows)
    wf = pd.DataFrame(wf_rows)
    prim.drop(columns=["yr_net"]).to_csv(RESULTS / "positioning_ml_primary.csv", index=False)
    abla.to_csv(RESULTS / "positioning_ml_ablation.csv", index=False)
    imp.to_csv(RESULTS / "positioning_ml_importance.csv", index=False)
    perm.to_csv(RESULTS / "positioning_ml_perm_importance.csv", index=False)
    wf.to_csv(RESULTS / "positioning_ml_walkforward.csv", index=False)

    # ================= REPORT =================
    print("\n\n" + "#" * W)
    print("  RESULTS -- SEALED TEST (final 25%, strict out-of-sample)")
    print("#" * W)
    print(f"  {'inst':>8} {'H':>4} {'test IC':>9} {'trades':>7} {'net SR':>8} {'net PF':>7} "
          f"{'maxDD':>7} {'net ret':>9} {'top-yr':>7} | {'B&H SR':>7} {'B&H ret':>9} {'beats B&H?':>11}")
    print("  " + "-" * (W - 4))
    for _, r in prim.iterrows():
        beats = np.isfinite(r["net_sharpe"]) and r["net_sharpe"] > r["bh_sharpe"]
        ty = f"{r['top_year_share']*100:.0f}%" if np.isfinite(r["top_year_share"]) else "n/a"
        print(f"  {r['instrument']:>8} {r['horizon']:>4} {r['test_ic']:>+9.4f} {int(r['n_trades']):>7} "
              f"{r['net_sharpe']:>+8.2f} {r['net_pf']:>7.3f} {r['max_dd']*100:>6.1f}% "
              f"{r['net_ret_total']*100:>+8.1f}% {ty:>7} | {r['bh_sharpe']:>+7.2f} {r['bh_ret_total']*100:>+8.1f}% "
              f"{('BEATS' if beats else 'loses'):>11}")

    print("\n" + "#" * W)
    print("  ABLATION -- positioning-only vs price-ctrl-only vs both (sealed test).  THE decisive honesty check.")
    print("#" * W)
    print(f"  {'inst':>8} {'H':>4} {'feature set':>13} {'test IC':>9} {'net SR':>8} {'net PF':>7} {'trades':>7} {'net ret':>9}")
    print("  " + "-" * (W - 4))
    for (inst, h), g in abla.groupby(["instrument", "horizon"], sort=False):
        for _, r in g.iterrows():
            print(f"  {inst:>8} {h:>4} {r['feature_set']:>13} {r['test_ic']:>+9.4f} {r['net_sharpe']:>+8.2f} "
                  f"{r['net_pf']:>7.3f} {int(r['n_trades']):>7} {r['net_ret_total']*100:>+8.1f}%")
        print("  " + "-" * (W - 4))

    print("\n" + "#" * W)
    print("  FEATURE IMPORTANCE -- gain share, positioning vs price control (both-feature model)")
    print("#" * W)
    for (inst, h), g in imp.groupby(["instrument", "horizon"], sort=False):
        pos = g[g["kind"] == "positioning"]["gain_share"].sum()
        ctrl = g[g["kind"] == "price_ctrl"]["gain_share"].sum()
        print(f"\n  {inst} / {h}:   positioning {pos*100:5.1f}%   |   price_ctrl {ctrl*100:5.1f}%")
        for _, r in g.head(8).iterrows():
            bar = "#" * max(1, int(r["gain_share"] * 60))
            print(f"     {r['rank']:>2}. {r['feature']:<22} {r['kind']:<11} {r['gain_share']*100:5.1f}%  {bar}")

    # aggregate permutation importance
    print("\n" + "#" * W)
    print("  PERMUTATION IMPORTANCE on the sealed test (mean IC drop when a feature is shuffled)")
    print("#" * W)
    pagg = (perm.groupby(["feature", "kind"])["ic_drop"].mean().reset_index()
            .sort_values("ic_drop", ascending=False))
    pos_drop = pagg[pagg["kind"] == "positioning"]["ic_drop"].clip(lower=0).sum()
    ctrl_drop = pagg[pagg["kind"] == "price_ctrl"]["ic_drop"].clip(lower=0).sum()
    tot_drop = (pos_drop + ctrl_drop) or 1.0
    print(f"  positioning share of total positive IC-drop: {pos_drop/tot_drop*100:.1f}%   "
          f"price_ctrl share: {ctrl_drop/tot_drop*100:.1f}%")
    for _, r in pagg.head(10).iterrows():
        print(f"     {r['feature']:<22} {r['kind']:<11} mean IC drop {r['ic_drop']:+.4f}")

    print("\n" + "#" * W)
    print("  WALK-FORWARD (expanding window, both features) -- per-fold sealed test IC and strategy net Sharpe")
    print("#" * W)
    if not wf.empty:
        print(f"  {'inst':>8} {'H':>4} {'fold':>4} {'test window':>25} {'train n':>8} {'test n':>7} {'test IC':>9} {'net SR':>8} {'trades':>7}")
        for _, r in wf.iterrows():
            print(f"  {r['instrument']:>8} {r['horizon']:>4} {int(r['fold']):>4} "
                  f"{r['test_from']+'..'+r['test_to']:>25} {int(r['train_n']):>8,} {int(r['test_n']):>7,} "
                  f"{r['test_ic']:>+9.4f} {r['net_sharpe']:>+8.2f} {int(r['n_trades']):>7}")
        wf_pos_ic = wf["test_ic"].mean()
        wf_pos_sr = wf["net_sharpe"].mean()
        wf_frac_ic_pos = float((wf["test_ic"] > 0).mean())
        print(f"\n  mean fold test IC {wf_pos_ic:+.4f}  ({wf_frac_ic_pos*100:.0f}% of folds IC>0)  |  "
              f"mean fold net Sharpe {wf_pos_sr:+.2f}")

    # DSR reference only -- pool = the 4 "both" cells
    pool = prim["net_sharpe"].to_numpy(dtype=float)
    emax, Np, mu, sd = expected_max_sharpe(pool)
    print("\n" + "#" * W)
    print("  DEFLATED SHARPE -- REFERENCE ONLY (not a survival gate). Pool = the 4 a priori 'both' cells.")
    print("#" * W)
    print(f"  pool Sharpes {np.round(pool,3).tolist()}  ->  E[max SR] {emax:+.3f}  (mu {mu:+.3f}, sd {sd:.3f})")
    for _, r in prim.iterrows():
        if np.isfinite(r["net_sharpe"]):
            d = deflated_sharpe(float(r["net_sharpe"]), pool, n_obs=max(int(r["n_trades"]), 5),
                                ann_factor=BARS_PER_YEAR)["dsr"]
            print(f"     {r['instrument']} {r['horizon']}: net Sharpe {r['net_sharpe']:+.2f}  DSR {d:.3f}")

    # concentration
    print("\n" + "#" * W)
    print("  PER-YEAR CONCENTRATION -- sealed-test strategy net return by calendar year (both features)")
    print("#" * W)
    for r in primary_rows:
        yl = r.get("yr_net", {})
        if not yl:
            print(f"  {r['instrument']} {r['horizon']}: no trades")
            continue
        tot = sum(yl.values())
        cells = "  ".join(f"{y}:{v*100:+.1f}%" for y, v in sorted(yl.items()))
        ty = f"{r['top_year_share']*100:.0f}%" if np.isfinite(r["top_year_share"]) else "n/a (total<=0)"
        print(f"  {r['instrument']} {r['horizon']}: {cells}   total {tot*100:+.1f}%   top-year share {ty}")

    # ---- verdict ----
    print("\n" + "=" * W)
    print("  VERDICT")
    print("=" * W)
    imp_g = imp.groupby(["instrument", "horizon"]).apply(
        lambda g: pd.Series(dict(pos=g[g.kind == "positioning"]["gain_share"].sum(),
                                 ctrl=g[g.kind == "price_ctrl"]["gain_share"].sum()))).reset_index()
    mean_pos = imp_g["pos"].mean() * 100
    mean_ctrl = imp_g["ctrl"].mean() * 100
    n_beats = int(sum(np.isfinite(r["net_sharpe"]) and r["net_sharpe"] > r["bh_sharpe"] for r in primary_rows))
    mean_ic = prim["test_ic"].mean()
    mean_sr = prim["net_sharpe"].mean()
    # ablation summary: does positioning-only carry anything vs price-only?
    abla_pivot = abla.pivot_table(index=["instrument", "horizon"], columns="feature_set",
                                  values="test_ic")
    pos_only_mean_ic = abla_pivot["positioning"].mean()
    ctrl_only_mean_ic = abla_pivot["price_ctrl"].mean()
    both_mean_ic = abla_pivot["both"].mean()
    print(f"  mean sealed-test IC (both features): {mean_ic:+.4f}   mean strategy net Sharpe: {mean_sr:+.2f}   "
          f"beats B&H: {n_beats}/4")
    print(f"  mean GAIN importance:   positioning {mean_pos:.1f}%   |   price control {mean_ctrl:.1f}%")
    print(f"  ablation mean test IC:  positioning-only {pos_only_mean_ic:+.4f}   "
          f"price-ctrl-only {ctrl_only_mean_ic:+.4f}   both {both_mean_ic:+.4f}")
    price_dominates = mean_ctrl > mean_pos and abs(pos_only_mean_ic) < abs(ctrl_only_mean_ic)
    real_signal = (mean_pos > 55.0 and pos_only_mean_ic > 0.02
                   and mean_sr > 0 and n_beats >= 3)
    print()
    if real_signal:
        print("  -> POSITIONING FEATURES GENUINELY DRIVE THE MODEL and the signal survives costs / B&H.")
        print("     This would be the first real finding of this kind in the project -- verify hard before trusting.")
    elif price_dominates:
        print("  -> THE MODEL LEANS ON PRICE-DERIVED CONTROL FEATURES, NOT POSITIONING.")
        print("     Whatever it learned is a re-discovery of price patterns -- already proven empty across 1000+")
        print("     trials in this project. The positioning data adds nothing an ML model can exploit either.")
        print("     KILL -- equivalent to everything already killed. Closes the ML-on-positioning thread.")
    else:
        print("  -> NO EXPLOITABLE SIGNAL FROM EITHER FEATURE GROUP (IC ~ 0, strategy does not beat B&H after costs).")
        print("     The shallow GBM finds nothing in the positioning data that section 18's threshold rule missed.")
        print("     KILL -- closes the ML-on-positioning thread.")

    print(f"\n  NEW TRIALS THIS RUN: {NEW_TRIALS} (BTC/ETH x 4h/24h, 'both features').  "
          f"CUMULATIVE: {PRIOR_TRIALS} + {NEW_TRIALS} = {PRIOR_TRIALS + NEW_TRIALS}")
    print(f"  (positioning-only / price-ctrl-only ablations and walk-forward folds are diagnostics of those 4 cells,")
    print(f"   not separate configs -- same treatment as STATE_OF_PLAY sec 12.3 audit 8 perturbations.)")
    print("  saved -> results/positioning_ml_{primary,ablation,importance,perm_importance,walkforward}.csv")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
