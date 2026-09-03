@echo off
REM ============================================================================
REM  run_monthly_check.bat -- double-click launcher for the momentum rotation
REM  monthly signal check. Safe to place a shortcut to this anywhere (desktop,
REM  taskbar); it always cd's to the repo by absolute path first.
REM
REM  Runs scripts/monthly_signal_check.py with --force so it works on ANY day.
REM  The script prints a big LIVE-SIGNAL vs PREVIEW-ONLY banner up top so a
REM  mid-month preview is never mistaken for a real rebalance-day signal.
REM  Then PAUSES so the window stays open whether the script succeeded,
REM  errored, or python was not found.
REM ============================================================================

cd /d "C:\Claude Code\AI Quant Trading\crypto-factor-lab"

python scripts\monthly_signal_check.py --force
set "EXITCODE=%ERRORLEVEL%"

echo.
if not "%EXITCODE%"=="0" (
    echo [run_monthly_check] script exited with code %EXITCODE% -- see messages above.
)

echo.
echo Press any key to close...
pause >nul
exit /b %EXITCODE%
