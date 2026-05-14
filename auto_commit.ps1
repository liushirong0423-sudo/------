# Auto Git Commit & Push - Daily scheduled by Windows Task Scheduler

$RepoPath = "C:\Users\13339\OneDrive\Desktop\宏观指标监控"
$LogFile  = "$RepoPath\auto_commit.log"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $Message" -Encoding UTF8
}

Set-Location $RepoPath
Write-Log "===== START auto-commit ====="

# 1. Pull latest
Write-Log "git pull..."
$pullOut = git pull origin main 2>&1
Write-Log "$pullOut"

# 2. Check for changes
$gitStatus = git status --porcelain
if (-not $gitStatus) {
    Write-Log "Nothing to commit. Exit."
    Write-Log "===== END ====="
    exit 0
}

# 3. Stage all
git add -A 2>&1 | ForEach-Object { Write-Log "$_" }

# 4. Commit with timestamp
$dateStr   = Get-Date -Format "yyyy-MM-dd HH:mm"
$commitMsg = "Auto update: $dateStr"
Write-Log "Committing: $commitMsg"
git commit -m $commitMsg 2>&1 | ForEach-Object { Write-Log "$_" }

# 5. Push
Write-Log "git push..."
git push origin main 2>&1 | ForEach-Object { Write-Log "$_" }

Write-Log "===== DONE ====="