#!/usr/bin/env bash
# Download H1 bid+ask OHLCV for the four NEW basket index CFDs, 2018-2025.
#
# WHY H1 AND NOT M1
# -----------------
# The basket study trades H4/H8/D1 signals. H1 aggregates EXACTLY into all three
# (4, 8, 24 bars), so H1 is a lossless base for the signal frames, and it is also
# the trade-RESOLUTION frame -- finer than every signal timeframe, so stop/target
# resolution is strictly more faithful than the prior run's resolve-on-signal-TF
# approach. M1 would add nothing for H4+ signals and would cost ~6-12h of
# downloading for 64 files instead of ~20 minutes.
#
# Timestamps are Dukascopy-native BAR-OPEN, matching the existing M1 files, so
# the whole downstream loader stack works unchanged.
#
# INSTRUMENT IDS — taken from the dukascopy-node Instrument enum and VERIFIED by
# price probe on 2024-03-04, not guessed:
#   deuidxeur    -> "Germany 40 Index"  probe 17,640-17,762  (real DAX  ~17,700) OK
#   gbridxgbp    -> "UK 100 Index"      probe  7,599- 7,682  (real FTSE ~ 7,650) OK
#   jpnidxjpy    -> "Japan 225 Index"   probe 39,756-40,246  (real N225 ~40,100) OK
#   usa500idxusd -> "USA 500 Index"     probe  5,064- 5,164  (real SPX  ~ 5,130) OK
#
# NAS100 (usatechidxusd) and US30 (usa30idxusd) are NOT re-downloaded — their H1
# base frames are derived from the existing M1 files by scripts/merge_basket.py.
#
# Resumable via .done markers. Empty-file failures were observed on the probe and
# cleared on retry, so retries are essential here.
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
OUT="$REPO/data/raw/basket_tmp"
DL="$OUT/download"
LOG="$OUT/download.log"
mkdir -p "$DL"

INSTRUMENTS="deuidxeur gbridxgbp jpnidxjpy usa500idxusd"
YEARS="2018 2019 2020 2021 2022 2023 2024 2025"
PRICES="bid ask"

echo "=== basket H1 download started $(date) ===" >> "$LOG"

for I in $INSTRUMENTS; do
for Y in $YEARS; do
  FROM="${Y}-01-01"
  TO_END="$((Y+1))-01-01"   # exclusive end so Dec 31 is included
  for P in $PRICES; do
    FN="${I}-h1-${P}-${Y}"
    TARGET="$DL/${FN}.csv"
    DONE="$DL/${FN}.done"
    if [ -f "$DONE" ]; then
      echo "SKIP ${FN} ($(wc -l < "$TARGET" 2>/dev/null) lines)" >> "$LOG"
      continue
    fi
    ok=0
    for attempt in 1 2 3 4 5 6; do
      rm -f "$TARGET"
      npx --yes dukascopy-node \
        -i "$I" -from "$FROM" -to "$TO_END" -t h1 -p "$P" \
        -v -vu units -f csv -utc 0 \
        -r 10 -rp 3000 -re -fr \
        -dir "$DL" -fn "$FN" >> "$LOG" 2>&1
      # a year of index H1 is ~5,000-6,500 bars; anything under 1000 is a failure
      if [ -f "$TARGET" ] && [ "$(wc -l < "$TARGET")" -gt 1000 ]; then
        touch "$DONE"
        echo "OK ${FN}: $(wc -l < "$TARGET") lines" >> "$LOG"
        ok=1
        break
      fi
      echo "RETRY ${FN} (attempt ${attempt} produced too few lines)" >> "$LOG"
      sleep 8
    done
    [ "$ok" -eq 1 ] || echo "FAILED ${FN} after 6 attempts" >> "$LOG"
  done
done
done

echo "=== basket H1 download finished $(date) ===" >> "$LOG"
