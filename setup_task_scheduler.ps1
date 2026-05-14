# Register Windows Task Scheduler: daily auto git commit & push
# Run this script ONCE as Administrator

$TaskName    = "MacroMonitor_AutoCommit"
$ScriptPath  = "C:\Users\13339\OneDrive\Desktop\宏观指标监控\auto_commit.ps1"
$TriggerTime = "08:00"

$Action = New-ScheduledTaskAction `
    -Execute  "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime

$Principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -StartWhenAvailable `
    -WakeToRun $false

Register-ScheduledTask `
    -TaskName  $TaskName `
    -Action    $Action `
    -Trigger   $Trigger `
    -Principal $Principal `
    -Settings  $Settings `
    -Force

Write-Host ""
Write-Host "Task registered : $TaskName"
Write-Host "Script          : $ScriptPath"
Write-Host "Daily trigger   : $TriggerTime"
Write-Host ""
Write-Host "View   : Get-ScheduledTask -TaskName '$TaskName' | Format-List *"
Write-Host "Run now: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Remove : Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"