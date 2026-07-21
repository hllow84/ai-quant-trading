#!/usr/bin/env bash
# Full index pipeline, start to finish, unattended and detach-safe.
#
#   Step 1  resume the M1 bid/ask download   (resumable via .done markers)
#   Step 2  rebuild BOTH merged files from scratch (stale files deleted first)
#   Step 3  VERIFY coverage — hard gate, sweep is skipped if this fails
#   Step 4  run the 150-config sweep         (resumable via results/markers_idx/)
#
# Replaces the old chain_indices.sh, which polled the download log from a
# SEPARATE process; when the terminal closed, the downloader and the watcher
# both died and nothing resumed. Here every step is sequential in ONE process,
# so there is nothing to lose track of and re-running resumes cleanly.
#
# Safe to re-run at any point: every step is idempotent.
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
LOG="$REPO/results/pipeline_indices.log"
mkdir -p "$REPO/results"

say() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

say "================= PIPELINE START (pid $$) ================="
cd "$REPO" || { say "FATAL: cannot cd to repo"; exit 1; }

# ---------------------------------------------------------------- Step 1
say "STEP 1/4  resuming index M1 download (skips completed .done files)"
bash "$REPO/scripts/download_indices.sh"
DL_RC=$?
say "STEP 1 exit=$DL_RC"

DLOG="$REPO/data/raw/idx_tmp/download.log"
DONE_CT=$(ls "$REPO/data/raw/idx_tmp/download/"*.done 2>/dev/null | wc -l)
FAIL_CT=$(grep -c "^FAILED " "$DLOG" 2>/dev/null || echo 0)
say "download markers: ${DONE_CT}/32 complete, ${FAIL_CT} hard failures"

if [ "$DONE_CT" -lt 32 ]; then
  say "WARNING: only ${DONE_CT}/32 files present — merge will report MISSING files"
  say "         and the verify gate will then block the sweep. That is intended."
fi

# ---------------------------------------------------------------- Step 2
say "STEP 2/4  rebuilding merged files from scratch"
for F in NAS100_M1_2018_2025_cfd_dukascopy.csv US30_M1_2018_2025_cfd_dukascopy.csv; do
  if [ -f "$REPO/data/$F" ]; then
    say "  deleting stale $F ($(wc -l < "$REPO/data/$F") lines)"
    rm -f "$REPO/data/$F"
  fi
done
python "$REPO/scripts/merge_indices.py" >> "$LOG" 2>&1
say "STEP 2 merge exit=$?"

# ---------------------------------------------------------------- Step 3
say "STEP 3/4  verifying merged file coverage (HARD GATE)"
python "$REPO/scripts/verify_indices.py" >> "$LOG" 2>&1
VRC=$?
say "STEP 3 verify exit=$VRC"

if [ "$VRC" -ne 0 ]; then
  say "VERIFICATION FAILED — refusing to run the sweep on incomplete data."
  say "Re-run scripts/run_all_indices.sh once the missing files are downloaded."
  say "================= PIPELINE HALTED ================="
  exit 1
fi

# ---------------------------------------------------------------- Step 4
say "STEP 4/4  running the 150-config index sweep"
python "$REPO/run_sweep_indices.py" >> "$LOG" 2>&1
say "STEP 4 sweep exit=$?"

say "================= PIPELINE COMPLETE ================="
