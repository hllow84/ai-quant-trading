#!/usr/bin/env bash
# Wait for the index M1 download to finish, then merge -> sweep, unattended.
# Started after scripts/download_indices.sh so the whole Step1->Step2 pipeline
# completes without supervision.
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
LOG="$REPO/data/raw/idx_tmp/download.log"
CHAIN="$REPO/data/raw/idx_tmp/chain.log"

echo "=== chain started $(date) ===" >> "$CHAIN"

# 1. wait for the downloader to print its finish line (poll every 60s, cap 10h)
for i in $(seq 1 600); do
  if grep -q "index M1 download finished" "$LOG" 2>/dev/null; then
    echo "download finished, detected at $(date)" >> "$CHAIN"
    break
  fi
  sleep 60
done

if ! grep -q "index M1 download finished" "$LOG" 2>/dev/null; then
  echo "TIMEOUT waiting for download after 10h — proceeding with whatever landed" >> "$CHAIN"
fi

OK_CT=$(grep -c "^OK " "$LOG" 2>/dev/null || echo 0)
FAIL_CT=$(grep -c "^FAILED " "$LOG" 2>/dev/null || echo 0)
echo "download summary: OK=$OK_CT FAILED=$FAIL_CT (of 32 expected)" >> "$CHAIN"

# 2. merge bid+ask -> spread files
echo "--- merge $(date) ---" >> "$CHAIN"
cd "$REPO" && python scripts/merge_indices.py >> "$CHAIN" 2>&1
echo "merge exit=$?" >> "$CHAIN"

# 3. run the sweep (resumable; safe to re-run)
echo "--- sweep $(date) ---" >> "$CHAIN"
cd "$REPO" && python run_sweep_indices.py >> "$CHAIN" 2>&1
echo "sweep exit=$?" >> "$CHAIN"

echo "=== chain finished $(date) ===" >> "$CHAIN"
