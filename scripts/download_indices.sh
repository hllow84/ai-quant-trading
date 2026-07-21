#!/usr/bin/env bash
# Download US index CFD M1 OHLCV from Dukascopy, BID and ASK separately,
# year by year, 2018-2025. Bid+ask are merged later to produce a real spread.
#
# Instrument IDs were taken from the dukascopy-node Instrument enum (dist/index.js),
# NOT guessed, and verified by price range on a probe pull (2024-03-04):
#   usatechidxusd -> 18,306  = Nasdaq-100   (NDX was ~18,300)
#   usa30idxusd   -> 39,052  = Dow-30       (DJIA was ~39,000)
#
# Resumable via .done markers: a (instrument,year,price) is skipped only if
# fully completed. All output stays inside the repo. Timezone = UTC (-utc 0).
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
OUT="$REPO/data/raw/idx_tmp"
DL="$OUT/download"
LOG="$OUT/download.log"
mkdir -p "$DL"

INSTRUMENTS="usatechidxusd usa30idxusd"
YEARS="2018 2019 2020 2021 2022 2023 2024 2025"
PRICES="bid ask"

echo "=== index M1 download started $(date) ===" >> "$LOG"

for I in $INSTRUMENTS; do
for Y in $YEARS; do
  FROM="${Y}-01-01"
  TO_END="$((Y+1))-01-01"   # exclusive end so Dec 31 is included
  for P in $PRICES; do
    FN="${I}-m1-${P}-${Y}"
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
        -i "$I" -from "$FROM" -to "$TO_END" -t m1 -p "$P" \
        -v -vu units -f csv -utc 0 \
        -bs 50 -bp 250 -r 10 -rp 3000 -re -fr \
        -dir "$DL" -fn "$FN" >> "$LOG" 2>&1
      # accept only a non-trivial file (a year of index M1 is >>1000 lines)
      if [ -f "$TARGET" ] && [ "$(wc -l < "$TARGET")" -gt 1000 ]; then
        touch "$DONE"
        echo "OK ${FN}: $(wc -l < "$TARGET") lines" >> "$LOG"
        ok=1
        break
      fi
      echo "RETRY ${FN} (attempt ${attempt} produced too few lines)" >> "$LOG"
      sleep 10
    done
    [ "$ok" -eq 1 ] || echo "FAILED ${FN} after 5 attempts" >> "$LOG"
  done
done
done

echo "=== index M1 download finished $(date) ===" >> "$LOG"
