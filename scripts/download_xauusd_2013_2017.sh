#!/usr/bin/env bash
# Fills the real out-of-regime data gap flagged in STATE_OF_PLAY §67: XAUUSD
# only had a 2017 single-year stub, not a full 2013-2017 window like
# NAS100/US30's out-of-regime data. Pulls XAUUSD M1 bid+ask 2013-2017,
# year by year, same proven Dukascopy path as scripts/download_xauusd.sh
# (which built the 2018-2025 file). Confirmed data exists this far back via
# an earlier probe (data/raw/xau_probe/x2003.csv, real spot gold prices
# ~$362/oz in 2003). Resumable via .done markers.
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
OUT="$REPO/data/raw/xau_2013_2017"
DL="$OUT/download"
LOG="$OUT/download.log"
mkdir -p "$DL"

YEARS="2013 2014 2015 2016 2017"
PRICES="bid ask"

echo "=== XAUUSD M1 2013-2017 backfill started $(date) ===" >> "$LOG"

for Y in $YEARS; do
  FROM="${Y}-01-01"
  TO_END="$((Y+1))-01-01"
  for P in $PRICES; do
    FN="xauusd-m1-${P}-${Y}"
    TARGET="$DL/${FN}.csv"
    DONE="$DL/${FN}.done"
    if [ -f "$DONE" ]; then
      echo "SKIP ${FN} (.done present, $(wc -l < "$TARGET" 2>/dev/null) lines)" >> "$LOG"
      continue
    fi
    ok=0
    for attempt in 1 2 3 4 5; do
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
      sleep 10
    done
    if [ "$ok" -ne 1 ]; then
      echo "FAIL ${FN} after 5 attempts (kept $(wc -l < "$TARGET" 2>/dev/null) rows)" >> "$LOG"
    fi
  done
done

echo "=== XAUUSD M1 2013-2017 backfill finished $(date) ===" >> "$LOG"
echo "ALL_DONE" >> "$LOG"
