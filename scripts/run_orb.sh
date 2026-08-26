#!/usr/bin/env bash
# run_orb.sh — the full Opening Range Breakout study, chained in ONE process.
#
#   STEP 1  verify_orb_sessions.py   HARD GATE. Proves from the data that 09:30
#           America/New_York lands at 13:30 UTC under EDT and 14:30 UTC under
#           EST, that the DST flips fall on the correct US dates, and that the
#           opening range and the 16:00 ET close boundary are actually present.
#           A fixed UTC offset would misplace the opening range for half of
#           every year, so this gate blocks the sweep on failure.
#   STEP 2  run_orb.py               2018-2025, 12 configs.
#   STEP 3  run_orb_pre2018.py       2013-09-30 -> 2017-12-29, the SAME 12 cells
#           via module rebinding, then the cell-by-cell comparison.
#
# Chained in one process so nothing can be killed independently; launch detached
# via the .cmd wrapper (STATE_OF_PLAY "Operational notes"). Do NOT add a watcher
# process — that is how the original index run died at 27/32 files.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1
LOG="$REPO/results/orb_run.log"
: > "$LOG"

say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

say "STEP 1/3 — verify ORB sessions + DST mapping (hard gate)"
if ! py -3.14 scripts/verify_orb_sessions.py >>"$LOG" 2>&1; then
  say "VERIFY FAILED — refusing to run the backtest. See $LOG"
  exit 1
fi
say "verify PASS"

say "STEP 2/3 — ORB 2018-2025 (in regime)"
if ! py -3.14 run_orb.py >>"$LOG" 2>&1; then
  say "IN-REGIME RUN FAILED. See $LOG"
  exit 1
fi
say "in-regime run complete"

say "STEP 3/3 — ORB 2013-2017 (out of regime) + comparison"
if ! py -3.14 run_orb_pre2018.py >>"$LOG" 2>&1; then
  say "OUT-OF-REGIME RUN FAILED. See $LOG"
  exit 1
fi
say "ALL DONE — results/orb.csv, orb_pre2018.csv, orb_scored*.csv, orb_trades*.csv"
