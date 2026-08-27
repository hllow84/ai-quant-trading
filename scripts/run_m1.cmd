@echo off
REM Detach-safe launcher for the M1 timeframe row (verify gate -> in regime ->
REM matched control + out of regime). A .cmd wrapper with the ABSOLUTE path to
REM Git bash is required: bash is not on cmd.exe's PATH, and Start-Process with
REM a nested-quoted path exits instantly without running (STATE_OF_PLAY sec 8).
"C:\Program Files\Git\bin\bash.exe" -c "'/c/Claude Code/AI Quant Trading/crypto-factor-lab/scripts/run_m1.sh'"
