#!/usr/bin/env bash
# Full basket pipeline, unattended and detach-safe.
#
#   Step 1  download H1 bid+ask for the 4 NEW indices  (resumable .done markers)
#   Step 2  merge all 6 H1 base files (4 downloaded + 2 derived from M1)
#   Step 3  VERIFY all 6 — hard gate, sweep is skipped on failure
#   Step 4  108-config sweep + 18 equal-risk baskets + benchmarks
#
# All steps sequential in ONE process (the terminal-close lesson from the index
# run: a separate watcher process dies with the terminal and nothing resumes).
# Safe to re-run at any point — every step is idempotent.
set -u

REPO="C:/Claude Code/AI Quant Trading/crypto-factor-lab"
LOG="$REPO/results/pipeline_basket.log"
mkdir -p "$REPO/results"

say() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

say "================= BASKET PIPELINE START (pid $$) ================="
cd "$REPO" || { say "FATAL: cannot cd to repo"; exit 1; }

# ---------------------------------------------------------------- Step 1
say "STEP 1/4  downloading H1 bid+ask for GER40 / UK100 / JP225 / SPX500"
bash "$REPO/scripts/download_basket.sh"
say "STEP 1 exit=$?"

DL="$REPO/data/raw/basket_tmp/download"
DONE_CT=$(ls "$DL"/*.done 2>/dev/null | wc -l)
FAIL_CT=$(grep -c "^FAILED " "$REPO/data/raw/basket_tmp/download.log" 2>/dev/null || echo 0)
say "download markers: ${DONE_CT}/64 complete, ${FAIL_CT} hard failures"

# ---------------------------------------------------------------- Step 2
say "STEP 2/4  merging 6 H1 base files (4 downloaded + NAS100/US30 derived from M1)"
python "$REPO/scripts/merge_basket.py" >> "$LOG" 2>&1
say "STEP 2 merge exit=$?  (non-zero just means some instrument was incomplete; verify decides)"

# ---------------------------------------------------------------- Step 3
say "STEP 3/4  verifying all 6 H1 files (HARD GATE)"
python "$REPO/scripts/verify_basket.py" >> "$LOG" 2>&1
VRC=$?
say "STEP 3 verify exit=$VRC"

if [ "$VRC" -ne 0 ]; then
  say "VERIFICATION FAILED — refusing to run the basket sweep on incomplete data."
  say "Re-run scripts/run_all_basket.sh once the missing files are downloaded."
  say "================= BASKET PIPELINE HALTED ================="
  exit 1
fi

# ---------------------------------------------------------------- Step 4
say "STEP 4/4  running the 108-config sweep + 18 baskets"
python "$REPO/run_basket_trend.py" >> "$LOG" 2>&1
say "STEP 4 sweep exit=$?"

say "================= BASKET PIPELINE COMPLETE ================="
