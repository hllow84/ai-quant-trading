@echo off
REM Detach-safe launcher for the full index pipeline.
REM Exists so Start-Process does not have to nest quotes around a path with
REM spaces, which silently made the process exit instantly instead of running.
"C:\Program Files\Git\bin\bash.exe" -c "'/c/Claude Code/AI Quant Trading/crypto-factor-lab/scripts/run_all_indices.sh'"
