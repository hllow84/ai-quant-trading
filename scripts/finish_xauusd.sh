#!/usr/bin/env bash
# Detached finisher: wait for the XAUUSD download to write ALL_DONE, then run the
# bid/ask merge to produce the single clean spot file. Independent of any terminal.
set -u
REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
LOG="$REPO/data/raw/dukascopy_tmp/download.log"
FLOG="$REPO/data/raw/dukascopy_tmp/finish.log"
MERGE="$REPO/scripts/merge_xauusd.py"

echo "=== finisher started $(date) ===" >> "$FLOG"
# Wait up to ~3h for the download to complete.
for i in $(seq 1 180); do
  if grep -q "ALL_DONE" "$LOG" 2>/dev/null; then
    echo "ALL_DONE seen at $(date) — running merge" >> "$FLOG"
    cd "$REPO"
    python "$MERGE" >> "$FLOG" 2>&1
    echo "MERGE_DONE $(date)" >> "$FLOG"
    exit 0
  fi
  sleep 60
done
echo "TIMEOUT: ALL_DONE not seen within 3h ($(date))" >> "$FLOG"
exit 1
