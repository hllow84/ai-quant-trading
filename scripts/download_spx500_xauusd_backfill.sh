#!/usr/bin/env bash
# Backfill the ORB "not runnable" data gaps (STATE_OF_PLAY sec 10.5 follow-up),
# scoped to 2017 onwards per the user's instruction ("do all instruments from
# 2017 onwards only"):
#
#   1. SPX500 M1 2017-2025 - the repo held SPX500 at H1 only, so the ORB opening
#      range could not be built at all. Pull usa500idxusd M1 bid+ask.
#   2. XAUUSD M1 2017       - the repo's XAUUSD M1 starts 2018-01; this adds the
#      one pre-2018 year so gold has a 2017 out-of-regime slice.
#
# NAS100/US30 already have 2017 (data/*_M1RTH_2013_2017_*.csv) + 2018-2025
# (data/*_M1_2018_2025_*.csv), so no pull is needed for them.
# BTCUSDT already covers 2017-08-17 onwards (download_btcusdt_m1_binance.py).
#
# Method = the repo's proven Dukascopy path: plain `npx dukascopy-node` CLI, ONE
# process, BID and ASK separately then merged to a real spread by
# scripts/merge_spx500_xauusd_backfill.py. Timezone UTC (-utc 0). Resumable: a
# (job).done marker skips a completed (instrument,year,side).
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
SPX_DL="$REPO/data/raw/spx_bf/download"
XAU_DL="$REPO/data/raw/xau_bf/download"
LOG="$REPO/results/backfill_download.log"
mkdir -p "$SPX_DL" "$XAU_DL"

echo "=== backfill download started $(date) ===" | tee -a "$LOG"

# args: <instrument-id> <out-dir> <fn-prefix> <year> <price> <min-rows>
pull_year() {
  local I="$1" DL="$2" PFX="$3" Y="$4" P="$5" MIN="$6"
  local FROM="${Y}-01-01" TO="$((Y+1))-01-01"
  local FN="${PFX}-m1-${P}-${Y}"
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
      -i "$I" -from "$FROM" -to "$TO" -t m1 -p "$P" \
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

# ---- 1. XAUUSD M1 2017 (gold M1 full year ~250k-370k rows; >150k = complete) ----
for P in bid ask; do
  pull_year xauusd "$XAU_DL" xauusd 2017 "$P" 150000
done

# ---- 2. SPX500 M1 2017-2025 (index M1 year >> 1000 rows) ----
for Y in 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
  for P in bid ask; do
    pull_year usa500idxusd "$SPX_DL" usa500idxusd "$Y" "$P" 1000
  done
done

echo "=== backfill download finished $(date) ===" | tee -a "$LOG"
echo "ALL_DONE" | tee -a "$LOG"

# ---- 3. merge ----
echo "--- running merge ---" | tee -a "$LOG"
python "$REPO/scripts/merge_spx500_xauusd_backfill.py" >> "$LOG" 2>&1
echo "MERGE_DONE ($?)" | tee -a "$LOG"
