#!/usr/bin/env bash
# Backfill EURUSD M1 spot for the RETEST OR30/1R generalization test (this
# strategy has never been run on any forex pair -- only gold, three equity
# indices). Pulls the SAME two windows every other ORB test in this project
# uses: 2013-2017 (out-of-regime) and 2018-2025 (in-regime), 13 years total.
#
# Dukascopy's EURUSD archive is the deepest of any instrument this repo has
# pulled (the flagship pair, continuous history well before 2013) -- unlike
# XAUUSD/SPX500 in scripts/download_spx500_xauusd_backfill.sh, there is no
# earliest-availability question here; 2013-01-01 is chosen because it matches
# the out-of-regime window already used for NAS100/US30 (STATE_OF_PLAY sec
# 10.5), not because the archive requires it.
#
# Method = the repo's proven Dukascopy path: plain `npx dukascopy-node` CLI,
# ONE process, BID and ASK pulled separately then merged to a real spread by
# scripts/merge_eurusd_backfill.py. Timezone UTC (-utc 0). Resumable: a
# (job).done marker skips a completed (year,side).
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
DL="$REPO/data/raw/eurusd_bf/download"
LOG="$REPO/results/eurusd_backfill_download.log"
mkdir -p "$DL"

echo "=== EURUSD backfill download started $(date) ===" | tee -a "$LOG"

pull_year() {
  local Y="$1" P="$2" MIN="$3"
  local FROM="${Y}-01-01" TO="$((Y+1))-01-01"
  local FN="eurusd-m1-${P}-${Y}"
  local TARGET="$DL/${FN}.csv" DONE="$DL/${FN}.done"
  if [ -f "$DONE" ]; then
    echo "SKIP ${FN} (.done, $(wc -l < "$TARGET" 2>/dev/null) lines)" | tee -a "$LOG"
    return 0
  fi
  local attempt n
  for attempt in 1 2 3 4 5; do
    echo "--- ${FN} attempt ${attempt} $(date) ---" >> "$LOG"
    rm -f "$TARGET"
    npx --yes dukascopy-node \
      -i eurusd -from "$FROM" -to "$TO" -t m1 -p "$P" \
      -v -vu units -f csv -utc 0 \
      -bs 50 -bp 250 -r 10 -rp 3000 -re -fr \
      -dir "$DL" -fn "$FN" >> "$LOG" 2>&1
    n=$(wc -l < "$TARGET" 2>/dev/null || echo 0)
    if [ -f "$TARGET" ] && [ "$n" -gt "$MIN" ]; then
      echo "OK ${FN}: ${n} lines" | tee -a "$LOG"
      touch "$DONE"
      return 0
    fi
    echo "RETRY ${FN} (attempt ${attempt}: ${n} rows)" | tee -a "$LOG"
    sleep 12
  done
  echo "FAILED ${FN} after 5 attempts (${n} rows kept)" | tee -a "$LOG"
  return 1
}

# EURUSD M1 continuous (24/5) full year ~370k-520k rows; >300k = complete.
for Y in 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
  for P in bid ask; do
    pull_year "$Y" "$P" 300000
  done
done

echo "=== EURUSD backfill download finished $(date) ===" | tee -a "$LOG"
echo "ALL_DONE" | tee -a "$LOG"

echo "--- running merge ---" | tee -a "$LOG"
python "$REPO/scripts/merge_eurusd_backfill.py" >> "$LOG" 2>&1
echo "MERGE_DONE ($?)" | tee -a "$LOG"
