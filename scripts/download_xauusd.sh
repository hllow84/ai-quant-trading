#!/usr/bin/env bash
# Download XAUUSD (spot gold) M1 OHLCV from Dukascopy, BID and ASK separately,
# year by year, 2018-2025. Bid+ask are merged later to produce a real spread.
# Resumable via .done markers: a (year,price) is skipped only if fully completed.
# All output stays inside the repo. Timezone = UTC (Dukascopy -utc 0).
# Tuned for single-process throughput: large batch, short pause; Dukascopy
# rate-limits ACROSS processes, so we run ONE process and lean on batch concurrency.
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
OUT="$REPO/data/raw/dukascopy_tmp"
DL="$OUT/download"
LOG="$OUT/download.log"
mkdir -p "$DL"

YEARS="2018 2019 2020 2021 2022 2023 2024 2025"
PRICES="bid ask"

echo "=== XAUUSD M1 download started $(date) ===" >> "$LOG"

for Y in $YEARS; do
  FROM="${Y}-01-01"
  TO_END="$((Y+1))-01-01"   # exclusive end so Dec 31 is included
  for P in $PRICES; do
    FN="xauusd-m1-${P}-${Y}"
    TARGET="$DL/${FN}.csv"
    DONE="$DL/${FN}.done"
    if [ -f "$DONE" ]; then
      echo "SKIP ${FN} (.done present, $(wc -l < "$TARGET" 2>/dev/null) lines)" >> "$LOG"
      continue
    fi
    ok=0
    for attempt in 1 2 3 4; do
      echo "--- ${FN} attempt ${attempt} $(date) ---" >> "$LOG"
      rm -f "$TARGET"
      npx --yes dukascopy-node \
        -i xauusd -from "$FROM" -to "$TO_END" -t m1 -p "$P" \
        -v -vu units -f csv -utc 0 \
        -bs 50 -bp 250 -r 10 -rp 3000 -re -fr \
        -dir "$DL" -fn "$FN" >> "$LOG" 2>&1
      n=$(wc -l < "$TARGET" 2>/dev/null || echo 0)
      # a full year of M1 gold has ~250k-370k rows; treat >150k as complete
      if [ -f "$TARGET" ] && [ "$n" -gt 150000 ]; then
        echo "OK ${FN}: ${n} lines" >> "$LOG"
        touch "$DONE"
        ok=1
        break
      fi
      echo "RETRY ${FN} (attempt ${attempt}: only ${n} rows)" >> "$LOG"
      sleep 8
    done
    if [ "$ok" -ne 1 ]; then
      echo "FAIL ${FN} after 4 attempts (kept $(wc -l < "$TARGET" 2>/dev/null) rows)" >> "$LOG"
    fi
  done
done

echo "=== XAUUSD M1 download finished $(date) ===" >> "$LOG"
echo "ALL_DONE" >> "$LOG"
