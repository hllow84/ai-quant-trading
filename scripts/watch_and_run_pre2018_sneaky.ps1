# watch_and_run_pre2018_sneaky.ps1 -- wait for the pre-2018 M1 download, then fire
# the out-of-regime re-run of Strategy 2 automatically.
#
# WHY A WATCHER AND NOT A CHAINED COMMAND: the downloader can spend a long time in
# HTTP 429 backoff, and its own retry logic reruns a whole instrument up to five
# times. "&&" would fire the re-run on the first non-zero exit. This polls for the
# two PROMOTED data files instead, which only appear after the downloader's sanity
# gate passes (per-year bar floors, price band, negative-spread rate). If the gate
# fails, no file is written, and this correctly refuses to run.
#
# ASCII ONLY, DELIBERATELY. Windows PowerShell 5.1 reads a BOM-less .ps1 as
# Windows-1252, so a UTF-8 em-dash decodes to a byte that the parser treats as a
# smart quote and every string after it breaks. Keep this file 7-bit.
#
# Launch detached so it survives the terminal:
#   Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass',
#     '-File','scripts\watch_and_run_pre2018_sneaky.ps1' -WindowStyle Hidden
$ErrorActionPreference = 'Stop'

$repo    = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $repo 'data'
$tmp     = Join-Path $repo 'data\raw\pre2018_m1_tmp'
$log     = Join-Path $repo 'results\pre2018_sneaky_watch.log'
$runLog  = Join-Path $repo 'results\sneaky_pivot_pre2018_run.log'

$targets = @(
    (Join-Path $dataDir 'NAS100_M1RTH_2013_2017_cfd_dukascopy.csv'),
    (Join-Path $dataDir 'US30_M1RTH_2013_2017_cfd_dukascopy.csv')
)

function Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding utf8
}

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Log "watcher started (pid $PID); waiting for $($targets.Count) data files"

# Poll every 60s. 14h ceiling: the clean-run rate is ~1h/instrument, so anything
# past 14h means the rate limiter won, not that we are nearly there.
$deadline   = (Get-Date).AddHours(14)
$graceLeft  = 10          # polls to wait after the downloader exits before giving up
$lastReport = Get-Date

while ($true) {
    $have = @($targets | Where-Object { Test-Path $_ })
    if ($have.Count -eq $targets.Count) {
        Log "both data files present -- starting the re-run"
        break
    }

    if ((Get-Date) -gt $deadline) {
        Log "ABORT: 14h deadline passed with $($have.Count)/$($targets.Count) files. Re-run NOT started."
        exit 1
    }

    # Is the downloader still alive?
    $alive = $false
    $pidFile = Join-Path $tmp 'pid.txt'
    if (Test-Path $pidFile) {
        $dlPid = (Get-Content $pidFile -Raw).Trim()
        if ($dlPid -match '^\d+$') {
            $alive = [bool](Get-Process -Id ([int]$dlPid) -ErrorAction SilentlyContinue)
        }
    }
    if (-not $alive) {
        $graceLeft--
        if ($graceLeft -le 0) {
            $msg = "ABORT: downloader is gone and only $($have.Count)/$($targets.Count) files exist. "
            $msg += "Either its sanity gate failed or it was killed -- check download.log. Re-run NOT started."
            Log $msg
            exit 1
        }
        Log "downloader not running; $graceLeft grace polls left"
    } else {
        $graceLeft = 10
    }

    # Heartbeat every 15 minutes so the log shows progress, not just silence.
    if (((Get-Date) - $lastReport).TotalMinutes -ge 15) {
        $counts = foreach ($n in 'NAS100', 'US30') {
            $d = Join-Path $tmp "$n.days.done"
            if (Test-Path $d) { "{0} {1}d" -f $n, ((Get-Content $d).Count) } else { "$n 0d" }
        }
        Log ("waiting -- " + ($counts -join ', ') + " of 1110 each")
        $lastReport = Get-Date
    }

    Start-Sleep -Seconds 60
}

Log "launching run_sneaky_pivot_pre2018.py"
$code = 1
Push-Location $repo
try {
    & py -3.14 run_sneaky_pivot_pre2018.py *>&1 | Tee-Object -FilePath $runLog
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
Log "re-run finished with exit code $code -- output in results/sneaky_pivot_pre2018_run.log"
