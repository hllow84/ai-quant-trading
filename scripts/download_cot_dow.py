"""
download_cot_dow.py — Pull CFTC Commitment of Traders (Legacy Futures-Only
Combined) reports for CBOT Dow Jones Industrial Average (E-mini, $5) futures.

See scripts/cot_download_common.py for the shared fetch/validate/save logic
and full source/schedule notes.

DATA LIMITATION (found while building this, stated up front rather than
discovered mid-analysis): this contract's CFTC reporting STOPS at
2022-02-01 — the series does not continue to the present the way GOLD and
EURO FX do (checked live: no other "DOW"-named market picks up afterward;
the E-mini Dow's COT reporting appears to have lapsed, likely an open-
interest/reporting-threshold issue for this smaller-notional contract, not
a data-pull bug on this project's side). Any signal test using this file
is therefore NECESSARILY a 2013-2022 partial window, not a like-for-like
match to the GOLD (Sec71-Sec73) or EUR (Sec74) full 2013-2025 tests —
flagged explicitly in research/run_cot_dow_signal.py's own output, not
hidden.
"""

from __future__ import annotations

from pathlib import Path

from cot_download_common import fetch_and_save

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "COT_DOW_legacy_futures_only.csv"
MARKET_NAME = "DOW JONES INDUSTRIAL AVG- x $5 - CHICAGO BOARD OF TRADE"


def main() -> None:
    fetch_and_save(MARKET_NAME, OUT_PATH, min_years=15)


if __name__ == "__main__":
    main()
