#!/usr/bin/env bash
# run_pre2018_compare.sh — STATE_OF_PLAY §5 step 3, the out-of-regime test.
#
# Chains verify (HARD GATE) -> pre-2018 run -> matched 2018-2025 run in ONE
# process, so nothing can be killed independently. Launch detached via the .cmd
# wrapper (see STATE_OF_PLAY "Operational notes"); a watcher process must NOT be
# used, since that is how the original index run died at 27/32 files.
#
# Two runs, identical strategy code and params, differing only in window:
#   pre2018 : 2013-09-30 -> 2017-12-29, split 2016-01-01 (~53/47 IS/OOS)
#   new5    : 2018-01-02 -> 2025-12-31, split 2022-01-01 (50/50 IS/OOS)
# Both on the SAME 5 indices, so this isolates REGIME, not basket membership.
# The 50/50-in-each-window split is an evaluation cut, not a re-tune: no strategy
# parameter is touched in either run.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1
LOG="$REPO/results/pipeline_pre2018.log"
: > "$LOG"

say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

say "STEP 1/3 — verify pre-2018 H1 files (hard gate)"
if ! python scripts/verify_pre2018.py >>"$LOG" 2>&1; then
  say "VERIFY FAILED — refusing to run the backtest. See $LOG"
  exit 1
fi
say "verify PASS"

say "STEP 2/3 — pre-2018 out-of-regime run (2013_2017, split 2016-01-01)"
python run_basket_pre2018.py --suffix 2013_2017 --split 2016-01-01 --tag pre2018 \
  --label "2013-09-30 -> 2017-12-29 (OUT OF REGIME)" >>"$LOG" 2>&1
say "pre2018 exit=$?"

say "STEP 3/3 — matched in-regime baseline (2018_2025, same 5 indices, split 2022-01-01)"
python run_basket_pre2018.py --suffix 2018_2025 --split 2022-01-01 --tag new5 \
  --label "2018-01-02 -> 2025-12-31 (IN REGIME, matched 5 indices)" >>"$LOG" 2>&1
say "new5 exit=$?"

say "DONE — results/basket_results_pre2018.csv, results/basket_results_new5.csv"
