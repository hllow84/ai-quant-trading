"""
download_cot_eur.py — Pull the full history of CFTC Commitment of Traders
(Legacy Futures-Only Combined) reports for CME Euro FX futures (EUR/USD).

See scripts/cot_download_common.py for the shared fetch/validate/save logic
and full source/schedule notes.
"""

from __future__ import annotations

from pathlib import Path

from cot_download_common import fetch_and_save

_ROOT = Path(__file__).parent.parent
OUT_PATH = _ROOT / "data" / "COT_EUR_legacy_futures_only.csv"
MARKET_NAME = "EURO FX - CHICAGO MERCANTILE EXCHANGE"


def main() -> None:
    fetch_and_save(MARKET_NAME, OUT_PATH)


if __name__ == "__main__":
    main()
