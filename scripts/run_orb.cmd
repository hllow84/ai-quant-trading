@echo off
REM Detach-safe launcher for the ORB study (verify gate -> in-regime -> out-of-regime).
REM A .cmd wrapper avoids nesting quotes around a path containing spaces in
REM Start-Process, which made the process exit instantly without running.
"C:\Program Files\Git\bin\bash.exe" -c "'/c/Claude Code/AI Quant Trading/crypto-factor-lab/scripts/run_orb.sh'"
