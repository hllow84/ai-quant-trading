#!/usr/bin/env bash
# Backfill the two data gaps that make ORB cells "not runnable" (STATE_OF_PLAY
# sec 10.5 follow-up):
#
#   1. SPX500 M1 - the repo only had SPX500 at H1, so the ORB opening range
#      could not be built at all. Pull usa500idxusd M1 bid+ask 2013-2025.
#   2. XAUUSD M1 2013-2017 - the repo's XAUUSD M1 starts 2018-01, so gold had
#      no pre-2018 out-of-regime window. Pull xauusd M1 bid+ask 2013-2017.
#
# BTCUSDT has NO fix: Binance history starts 2017-08, so there is no pre-2018
# crypto regime at any resolution. Not attempted here.
#
# Method = the repo's proven Dukascopy path (scripts/download_indices.sh /
# download_xauusd.sh): plain `npx dukascopy-node` CLI, ONE process (Dukascopy
# rate-limits across processes), BID and ASK pulled separately then merged to a
# real spread by scripts/merge_spx500_xauusd_backfill.py. Timezone UTC (-utc 0).
# Resumable: a (job).done marker skips a completed (instrument,year,side).
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
    # A 0-row SPX500 year before the archive starts (~2013-09 for the ask side)
    # is legitimate; accept it. XAUUSD has full coverage from 2003, so an empty
    # XAUUSD year is a real failure and must keep retrying.
    if [ "$n" -le 1 ] && [ "$I" = "usa500idxusd" ] && [ "$Y" -le 2013 ]; then
      echo "EMPTY ${FN}: accepting (pre-archive year)" | tee -a "$LOG"
      : > "$TARGET"
      touch "$DONE"
      return 0
    fi
    echo "RETRY ${FN} (attempt ${attempt}: ${n} rows)" | tee -a "$LOG"
    sleep 12
  done
  echo "FAILED ${FN} after 5 attempts (${n} rows kept)" | tee -a "$LOG"
  return 1
}

# ---- 1. XAUUSD M1 2003-2017 (earliest available on Dukascopy = 2003-05-05).
#         Gold M1 year ~250k-370k rows; early/partial years thinner, so accept
#         >60k and let merge_spx500_xauusd_backfill.py apply the real per-year
#         gate (hard for 2013+, advisory before). 2003 starts in May. ----
for Y in 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017; do
  for P in bid ask; do
    pull_year xauusd "$XAU_DL" xauusd "$Y" "$P" 60000
  done
done

# ---- 2. SPX500 M1 2013-2025 (earliest with a real ASK side ~2013-09; 2010/2012
#         probed empty, same archive limit as US30). index M1 year >> 1000 rows ----
for Y in 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
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
