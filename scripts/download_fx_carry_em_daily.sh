#!/usr/bin/env bash
# Download daily bid/ask spot FX for the EM carry extension (MXN, ZAR, CNH, ILS
# vs USD). Same convention as download_fx_carry_daily.sh. SGD/TRY/PLN/HUF/BRL/
# INR/KRW/THB/CZK/RUB were probed and excluded (no usable Dukascopy coverage or
# no verified free rate series — see research_log.md 2026-09-15 EM carry row).
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
OUT="$REPO/data/raw/dukascopy_fx_carry"
DL="$OUT/download"
LOG="$OUT/download_em.log"
mkdir -p "$DL"

PAIRS="usdmxn usdzar usdcnh usdils"
FROM="2010-01-01"
TO="2026-01-01"
PRICES="bid ask"

echo "=== FX carry EM daily download started $(date) ===" >> "$LOG"

for PAIR in $PAIRS; do
  for P in $PRICES; do
    FN="${PAIR}-d1-${P}"
    TARGET="$DL/${FN}.csv"
    DONE="$DL/${FN}.done"
    if [ -f "$DONE" ]; then
      echo "SKIP ${FN}" >> "$LOG"
      continue
    fi
    ok=0
    for attempt in 1 2 3 4; do
      echo "--- ${FN} attempt ${attempt} $(date) ---" >> "$LOG"
      rm -f "$TARGET"
      npx --yes dukascopy-node \
        -i "$PAIR" -from "$FROM" -to "$TO" -t d1 -p "$P" \
        -v -vu units -f csv -utc 0 \
        -r 10 -rp 3000 -re -fr \
        -dir "$DL" -fn "$FN" >> "$LOG" 2>&1
      n=$(wc -l < "$TARGET" 2>/dev/null || echo 0)
      if [ -f "$TARGET" ] && [ "$n" -gt 1500 ]; then
        echo "OK ${FN}: ${n} lines" >> "$LOG"
        touch "$DONE"
        ok=1
        break
      fi
      echo "RETRY ${FN} (attempt ${attempt}: only ${n} rows)" >> "$LOG"
      sleep 5
    done
    if [ "$ok" -ne 1 ]; then
      echo "FAIL ${FN} after 4 attempts (kept $(wc -l < "$TARGET" 2>/dev/null || echo 0) rows)" >> "$LOG"
    fi
  done
done

echo "=== FX carry EM daily download finished $(date) ===" >> "$LOG"
echo "ALL_DONE" >> "$LOG"
