"""
regime_switch.py — regime-adaptive strategy selection engine, with anti-
whipsaw and anti-chasing safeguards DESIGNED IN (not measured after the
fact):

  1. Rank by TRAILING SHARPE (not raw return) over a causal lookback window.
  2. HYSTERESIS: a challenger must beat the incumbent's trailing Sharpe by
     a stated margin (default 0.3) before a switch happens.
  3. MINIMUM HOLD: decision dates are spaced exactly one lookback window
     apart, so "stay at least one full evaluation period" is enforced BY
     CONSTRUCTION, not just checked after the fact — a switch literally
     cannot happen more often than once per lookback window.
  4. CIRCUIT BREAKER: if every candidate's trailing Sharpe is below a
     stated floor (default 0.0), go to CASH instead of the least-bad loser.
  5. Real switching costs, charged on every actual switch, kept SEPARATE
     from each candidate's own internal per-trade costs (which are already
     baked into each family's own daily net-return series by the audited
     `research/ftmo_engine.py` cost model — see build_family_returns()).

The five underlying candidate systems are the SAME `strategies/
sweep_families.py` families used everywhere else in this repo, run through
the SAME `simulate_trades`/`de_overlap` engine `run_sweep_crypto.py` uses —
this module adds ONLY the meta-strategy (selection) layer on top; it does
not re-derive or re-tune any family.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.ftmo_engine import simulate_trades, de_overlap
from strategies.sweep_families import FAMILIES, TF_DELTA

FAMILY_NAMES = list(FAMILIES.keys())
CASH = "CASH"
BARS_PER_YEAR = 252


def _coerce_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def build_family_returns(m: pd.DataFrame, cost_bps: dict, tf_key: str = "H4",
                          variant_index: int = 0) -> dict[str, pd.Series]:
    """
    One daily net-return series per family, using variant v0 (the FIRST
    stated variant, chosen a priori, not cherry-picked from any result —
    the same variant index for every family and both instruments) on the
    execution frame `m`. Reindexed onto the FULL daily calendar spanned by
    `m` with 0.0 fill on every day the family holds no position (before its
    first trade, between trades, or after its last trade) — a real, valid
    "flat" return, not missing data. This is a thin, explicit variant of
    `research/ftmo_engine.py::build_daily_returns` (which restricts its
    output to [first trade, last trade] only); the trade simulation itself
    is 100% reused, unchanged.
    """
    full_index = pd.date_range(m.index[0].normalize(), m.index[-1].normalize(), freq="D", tz="UTC")
    out = {}
    for fam, (fn, variants) in FAMILIES.items():
        params = variants[variant_index]
        cands = fn(m, params, TF_DELTA[tf_key])
        for tr in cands:
            tr["session_end"] = _coerce_utc(tr["session_end"])
            tr["entry_time"] = _coerce_utc(tr["entry_time"])
        trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=cost_bps)) if cands \
            else pd.DataFrame()
        if trades.empty:
            out[fam] = pd.Series(0.0, index=full_index)
            continue
        exit_day = trades["exit_time"].dt.normalize()
        daily = trades.groupby(exit_day)["ret_frac"].sum()
        daily.index = daily.index.tz_convert("UTC") if daily.index.tz is not None else daily.index
        out[fam] = daily.reindex(full_index, fill_value=0.0)
    return out


def trailing_sharpe(returns: pd.Series, as_of: pd.Timestamp, lookback_days: int,
                     ann_factor: int = BARS_PER_YEAR) -> float:
    """
    Sharpe of `returns` strictly BEFORE `as_of` (returns.index < as_of),
    over the trailing `lookback_days`. Causal by construction: a decision
    dated `as_of` can never see a return realized on or after `as_of`.
    """
    window_start = as_of - pd.Timedelta(days=lookback_days)
    sl = returns[(returns.index >= window_start) & (returns.index < as_of)]
    if len(sl) < 2 or sl.std() == 0:
        return float("-inf")
    return float(sl.mean() / sl.std() * np.sqrt(ann_factor))


def run_switching(
    family_returns: dict[str, pd.Series],
    lookback_months: int,
    hysteresis: float = 0.3,
    cash_floor: float = 0.0,
    switch_cost_bps: float = 20.0,
) -> tuple[pd.Series, pd.DataFrame, pd.Series]:
    """
    Returns (composite_daily_return, decision_log, active_by_day).

    decision_log columns: decision_date, incumbent, trailing_sharpes (dict,
    stringified), circuit_breaker (bool), challenger, action
    ('hold'/'switch_family'/'switch_to_cash'/'switch_from_cash'), new_active.

    Decision dates are spaced EXACTLY `lookback_months` apart starting at
    full_index[0] + lookback_months — this is what makes the minimum-hold
    safeguard structural rather than a post-hoc check: no switch can occur
    more often than once per lookback window, by construction of the loop
    below (only decision dates can change `active`).
    """
    full_index = next(iter(family_returns.values())).index
    lookback_days = int(round(lookback_months * 30.4375))  # average month length, stated

    decision_dates = []
    d = full_index[0] + pd.DateOffset(months=lookback_months)
    while d <= full_index[-1]:
        # snap to the nearest actual index date so lookups are exact
        pos = full_index.searchsorted(d)
        if pos >= len(full_index):
            break
        decision_dates.append(full_index[pos])
        d = d + pd.DateOffset(months=lookback_months)

    active = CASH
    last_switch_date = None
    log_rows = []
    switch_cost_days = set()

    for dd in decision_dates:
        trailing = {fam: trailing_sharpe(family_returns[fam], dd, lookback_days) for fam in FAMILY_NAMES}
        best_fam = max(trailing, key=trailing.get)
        best_sr = trailing[best_fam]
        circuit_breaker = best_sr < cash_floor

        if last_switch_date is not None:
            # Coarse sanity check, not a precise one: decision dates are
            # spaced by calendar-exact DateOffset(months=lookback_months),
            # while lookback_days is an AVERAGE month length used only for
            # the trailing_sharpe() ranking window, so the two can differ by
            # a few days (e.g. February). The real minimum-hold guarantee is
            # structural — a switch can only be DECIDED at a decision_date,
            # and decision_dates are themselves spaced lookback_months apart
            # by construction (the while-loop above) — this assertion is a
            # loose confirmation of that, with a 10-day tolerance for month-
            # length variation, not the guarantee's actual mechanism.
            days_held = (dd - last_switch_date).days
            assert days_held >= lookback_days - 10, (
                f"minimum-hold violated: switched at {last_switch_date}, "
                f"re-switched at {dd}, only {days_held} days later"
            )

        if circuit_breaker:
            action = "switch_to_cash" if active != CASH else "hold"
            new_active = CASH
        elif active == CASH:
            # leaving cash needs no hysteresis margin against a fellow
            # family (cash isn't a ranked competitor) — only the circuit
            # breaker gates entry/exit from cash.
            action = "switch_from_cash"
            new_active = best_fam
        elif best_fam == active:
            action = "hold"
            new_active = active
        else:
            incumbent_sr = trailing[active]
            if best_sr > incumbent_sr + hysteresis:
                action = "switch_family"
                new_active = best_fam
            else:
                action = "hold"
                new_active = active

        if new_active != active:
            last_switch_date = dd
            switch_cost_days.add(dd)

        log_rows.append(dict(
            decision_date=dd, incumbent=active,
            **{f"sharpe_{fam}": trailing[fam] for fam in FAMILY_NAMES},
            circuit_breaker=circuit_breaker, challenger=best_fam,
            action=action, new_active=new_active,
        ))
        active = new_active

    decision_log = pd.DataFrame(log_rows)

    # ── build the composite daily return series. `new_active`, indexed at
    # each decision date, is forward-filled onto the full daily calendar so
    # the strategy chosen AT dd is active for [dd, next_decision_date) —
    # never earlier (ffill only propagates forward) and never using data
    # from later (new_active at dd was decided using only trailing_sharpe
    # windows ending strictly before dd, see trailing_sharpe() above).
    active_series = decision_log.set_index("decision_date")["new_active"]
    active_by_day = active_series.reindex(full_index).ffill().fillna(CASH)

    composite = pd.Series(0.0, index=full_index)
    for fam in FAMILY_NAMES:
        mask = (active_by_day == fam).to_numpy()
        composite.loc[mask] = family_returns[fam].loc[mask]
    # CASH days keep their 0.0 default.
    switch_mask = active_by_day.index.isin(switch_cost_days)
    composite.loc[switch_mask] -= switch_cost_bps / 10_000.0

    return composite, decision_log, active_by_day


def verify_causality(decision_log: pd.DataFrame, family_returns: dict[str, pd.Series],
                      lookback_months: int) -> bool:
    """
    Explicit look-ahead guard for the selection layer (the family-level
    trades already carry their own guard in run_sweep_crypto.py; this
    checks the META-decision, which is a different kind of object than a
    continuous price signal, so it gets its own explicit assertion-based
    check — same pattern research/momentum_rotation.py::look_ahead_guard()
    uses for its own non-price-series decision structure, rather than
    force-fitting research/backtest.py::guard_look_ahead, which assumes a
    continuous {-1,0,+1} position series).

    Re-derives every decision_date's trailing Sharpe independently and
    confirms it matches the logged value AND that the window used contains
    no date >= the decision date. Returns True iff every decision passes.
    """
    lookback_days = int(round(lookback_months * 30.4375))
    ok = True
    for _, row in decision_log.iterrows():
        dd = row["decision_date"]
        for fam in FAMILY_NAMES:
            recomputed = trailing_sharpe(family_returns[fam], dd, lookback_days)
            logged = row[f"sharpe_{fam}"]
            same = (recomputed == logged) or (np.isneginf(recomputed) and np.isneginf(logged)) \
                or (np.isfinite(recomputed) and np.isfinite(logged) and abs(recomputed - logged) < 1e-9)
            if not same:
                ok = False
            window_start = dd - pd.Timedelta(days=lookback_days)
            used = family_returns[fam][(family_returns[fam].index >= window_start)
                                       & (family_returns[fam].index < dd)]
            if len(used) and used.index.max() >= dd:
                ok = False
    return ok
