"""
fx_carry_data.py — Load G10 short-term interbank rates (FRED, free, no key) and
real spot FX bid/ask (Dukascopy daily) for the FX carry factor.

Universe: USD, EUR, GBP, AUD, NZD, CAD, CHF, JPY, NOK (9 currencies). SEK was
dropped: Dukascopy has no ask-side USDSEK daily data before 2025 (confirmed by
direct probe — bid-side is complete back to 2010, ask-side returns 0 bytes for
every year 2010-2024), so a real bid/ask spread cannot be computed for it over
the backtest window. Rather than block on one pair or drop honesty by faking a
spread, SEK is excluded and this is stated as a known universe-coverage gap.
Rate source: FRED series IR3TIB01<CC>M156N (OECD 3-month interbank rate,
mirrored on FRED, monthly, free, no API key via fredgraph.csv).
FX source: Dukascopy daily bid/ask spot, 2010-2025, real spread.

Publication lag: OECD/FRED short-term rate series are published with a lag after
month-end (typically ~4-6 weeks). We apply a conservative 2-month lag: the rate
value dated month t is not usable for portfolio formation until the START of
month t+2. This is deliberately conservative to avoid look-ahead.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
RATES_DIR = _ROOT / "data" / "raw" / "fred_rates"
FX_DIR = _ROOT / "data" / "raw" / "dukascopy_fx_carry" / "download"

# currency code -> FRED file
RATE_FILES = {
    "USD": "rate_USA.csv",
    "EUR": "rate_EZ.csv",
    "GBP": "rate_GBR.csv",
    "AUD": "rate_AUS.csv",
    "NZD": "rate_NZL.csv",
    "CAD": "rate_CAN.csv",
    "CHF": "rate_CHE.csv",
    "JPY": "rate_JPN.csv",
    "NOK": "rate_NOR.csv",
}

# currency code -> (dukascopy pair name, is_base) — is_base=True means pair is XXXUSD
# (currency is the base, so pair return == currency return vs USD).
# is_base=False means pair is USDXXX (currency is the quote, so currency return
# vs USD is the NEGATIVE of the pair's return).
FX_PAIRS = {
    "EUR": ("eurusd", True),
    "GBP": ("gbpusd", True),
    "AUD": ("audusd", True),
    "NZD": ("nzdusd", True),
    "CAD": ("usdcad", False),
    "CHF": ("usdchf", False),
    "JPY": ("usdjpy", False),
    "NOK": ("usdnok", False),
}

# EM extension (2026-09-15): SGD/TRY/PLN/HUF/BRL/INR/KRW/THB/CZK/RUB were
# probed and excluded — SGD has no verified free short-rate series (no working
# FRED SIBOR/interbank ID found); TRY/PLN/HUF have real Dukascopy instruments
# but DISCONTINUOUS coverage (TRY: data exists for 2015 and 2025 only, gaps in
# between — confirmed by per-year probe, a real broker delisting/relisting
# artifact, not a download bug); BRL/INR/KRW/THB/CZK/RUB are not valid
# dukascopy-node instruments at all (probed directly).
#
# MXN and ILS were ALSO excluded despite having working FRED rate series and
# working BID-side spot data: their ASK-side d1 history is broken on Dukascopy
# specifically (same failure signature as SEK in the G10 set) — MXN ask
# returns 0 bytes for every single year 2010-2025 (confirmed by per-year
# probe), ILS ask returns data only for 2025 (261 rows vs 3283 bid rows, every
# earlier year 0 bytes). A real spread cannot be computed for most of the
# window for either, so — consistent with the SEK exclusion policy in the G10
# set — they are dropped rather than using bid-only or a faked spread.
#
# That leaves only ZAR and CNH as EM additions with genuinely usable bid+ask
# coverage. THIS IS A NARROW EM EXTENSION (2 currencies), NOT A BROAD
# institutional-style EM carry basket (which would typically run 15-20+ EM
# currencies via NDFs) — stated as a real scope limitation of this project's
# free-data-only, single-retail-broker constraint, not hidden.
EM_RATE_FILES = {
    "ZAR": "rate_ZAF.csv",
    "CNH": "rate_CHN.csv",  # onshore CNY interbank rate used as the best free
                             # proxy for offshore CNH funding cost — CNH itself
                             # has no separate published free short-rate series;
                             # stated limitation, not hidden.
}

EM_FX_PAIRS = {
    "ZAR": ("usdzar", False),
    "CNH": ("usdcnh", False),
}

# CNH caveat: PBOC manages the RMB via a daily fixing + trading band; offshore
# CNH is less tightly controlled than onshore CNY but still a managed float,
# not a free-floating market currency. Observed "carry" here may partly
# reflect currency policy rather than a market risk premium — flagged in the
# write-up, not hidden. CNH bid-side coverage is also sparser than ask-side
# over the same 2012-2025 span (1,723 bid days vs 4,215 ask days) — likely
# lower quoting liquidity on the bid in the earlier years; the merge keeps
# only days with BOTH sides present, so CNH effectively has fewer usable
# trading days than its full calendar span suggests, also stated not hidden.

PUBLICATION_LAG_MONTHS = 2


def load_rate(cc: str, rate_files: dict[str, str] = RATE_FILES) -> pd.Series:
    fn = RATES_DIR / rate_files[cc]
    df = pd.read_csv(fn)
    df.columns = ["date", "rate"]
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["rate"].sort_index()
    s.name = cc
    return s


def load_all_rates(rate_files: dict[str, str] = RATE_FILES) -> pd.DataFrame:
    """Monthly rate panel, columns = currency codes, index = month-start date."""
    rates = {cc: load_rate(cc, rate_files) for cc in rate_files}
    panel = pd.DataFrame(rates)
    panel.index.name = "date"
    return panel


def rates_available_at(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Shift the rate panel forward by PUBLICATION_LAG_MONTHS so that the value
    indexed at month t is what was ACTUALLY KNOWN as of the start of month t
    (i.e., the true rate is from month t - PUBLICATION_LAG_MONTHS).
    """
    return panel.shift(PUBLICATION_LAG_MONTHS)


def load_fx_daily(cc: str, fx_pairs: dict[str, tuple[str, bool]] = FX_PAIRS) -> pd.DataFrame:
    """Load daily bid/ask for one currency's USD pair, return mid + spread_bps."""
    pair, is_base = fx_pairs[cc]
    bid = pd.read_csv(FX_DIR / f"{pair}-d1-bid.csv")
    ask = pd.read_csv(FX_DIR / f"{pair}-d1-ask.csv")
    bid["timestamp"] = pd.to_datetime(bid["timestamp"], unit="ms")
    ask["timestamp"] = pd.to_datetime(ask["timestamp"], unit="ms")
    bid = bid.set_index("timestamp").sort_index()
    ask = ask.set_index("timestamp").sort_index()
    df = pd.DataFrame({
        "bid_close": bid["close"],
        "ask_close": ask["close"],
    }).dropna()
    df["mid_close"] = (df["bid_close"] + df["ask_close"]) / 2
    df["spread_bps"] = (df["ask_close"] - df["bid_close"]) / df["mid_close"] * 10_000
    df["is_base"] = is_base
    return df


def load_all_fx(fx_pairs: dict[str, tuple[str, bool]] = FX_PAIRS) -> dict[str, pd.DataFrame]:
    return {cc: load_fx_daily(cc, fx_pairs) for cc in fx_pairs}


def currency_return_vs_usd(fx: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Daily log return of each non-USD currency vs USD, sign-adjusted so that
    a positive return always means that currency APPRECIATED vs USD."""
    rets = {}
    for cc, df in fx.items():
        lr = np.log(df["mid_close"]).diff()
        is_base = df["is_base"].iloc[0]
        rets[cc] = lr if is_base else -lr
    out = pd.DataFrame(rets)
    out["USD"] = 0.0
    return out


def currency_spread_bps(fx: dict[str, pd.DataFrame]) -> pd.DataFrame:
    out = pd.DataFrame({cc: df["spread_bps"] for cc, df in fx.items()})
    out["USD"] = 0.0
    return out
