@echo off
REM Wrapper for Windows Task Scheduler. Runs the monthly rebalance check.
REM Safe to schedule DAILY in the last few days of each month -- rebalance.py
REM itself checks whether today is actually the last NYSE trading day of the
REM month and is a no-op on every other day.
cd /d "C:\Claude Code\AI Quant Trading\crypto-factor-lab"
python live\rebalance.py >> live\logs\scheduler_run.log 2>&1
