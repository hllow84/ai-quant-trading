@echo off
REM Detach-safe launcher for the pre-2018 out-of-regime comparison.
REM Uses a .cmd wrapper so Start-Process never has to nest quotes around a path
REM containing spaces — doing that made the process exit instantly without running.
"C:\Program Files\Git\bin\bash.exe" -c "'/c/Claude Code/AI Quant Trading/crypto-factor-lab/scripts/run_pre2018_compare.sh'"
