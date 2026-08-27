#!/usr/bin/env bash
# run_m1.sh — chained M1 pipeline: verify gate -> in regime -> matched control
#             + out of regime -> comparison. Single process, detached via .cmd.
#
# The verify step is a HARD GATE (scripts/verify_m1.py exits 1). If the data or
# either method identity fails, the sweep does not run at all.
set -u
cd "$(dirname "$0")/.."
LOG="results/m1_run.log"
PY="py -3.14"

{
  echo "==============================================================================="
  echo " M1 TIMEFRAME ROW — chained run started $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "==============================================================================="

  echo; echo "### STEP 1/3 — DATA + METHOD GATE"
  $PY scripts/verify_m1.py
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "GATE FAILED (exit $rc) — sweep BLOCKED. Nothing further ran."
    exit $rc
  fi

  echo; echo "### STEP 2/3 — IN REGIME 2018-2025 (45 configs: 3 inst x 5 fam x 3 var)"
  $PY run_sweep_m1.py
  echo "step 2 exit: $?"

  echo; echo "### STEP 3/3 — MATCHED RTH CONTROL + OUT OF REGIME 2013-2017 (30 + 30)"
  $PY run_sweep_m1_pre2018.py
  echo "step 3 exit: $?"

  echo; echo "==============================================================================="
  echo " FINISHED $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "==============================================================================="
} > "$LOG" 2>&1
