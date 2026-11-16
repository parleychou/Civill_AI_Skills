param(
    [Parameter(Mandatory = $true)][ValidateSet('status', 'close', 'start', 'gama', 'restart', 'prompts', 'click')]
    [string]$Action,
    # .yjk to open on start/restart. pgw_g refuses to run with no project open.
    [string]$Project,
    [string]$Exe = 'D:\PenguinTrunkBranch\YJKSDK\run\x64\Release\yjks.exe',
    # For -Action click: the top-level window handle and the button name, both as listed by -Action prompts.
    [long]$Hwnd,
    [string]$Button,
    [int]$TimeoutSeconds = 120
)
# Close / start YJK (yjks.exe) and start GAMA by typing pgw_g into YJK's command line.
# Exit codes: 0 done; 2 a prompt window is open and needs a decision (listed on stdout); 1 failure.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'yjk-win.ps1')

# Text that marks GAMA's (or YJK's) offer to reopen an earlier file. Those offers are always declined.
$PreviousFilePattern = '上次|之前|最近|恢复|previous|recent|last|restore'
$DeclineNames = @('否', '否(N)', '否(&N)', '不打开', '取消', 'No', '&No', 'Cancel', '新建', '新文件')

function Write-Prompts($prompts) {
    foreach ($w in $prompts) {
        "PROMPT hwnd=$($w.Hwnd) class=$($w.Class) title='$($w.Title)'"
        foreach ($t in $w.Texts) { "  text: $t" }
        foreach ($b in $w.Buttons) { "  button: '$b'" }
    }
}

function Wait-Exit($proc, [int]$seconds, $knownWindows) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 800
        if (-not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) { return $true }
        $prompts = @(Get-YjkPrompts $proc.Id $knownWindows)
        if ($prompts.Count) { Write-Prompts $prompts; exit 2 }
    }
    return $false
}

function Close-Yjk {
    $p = Get-YjkProcess
    if (-not $p) { 'yjks not running'; return }
    $known = @(Get-YjkTopWindows $p.Id | ForEach-Object { $_.Hwnd })
    "closing yjks pid=$($p.Id) title='$([YW]::Text((Get-YjkMainWindow $p.Id)))'"
    [void][YW]::PostMessage((Get-YjkMainWindow $p.Id), $WM_CLOSE, [IntPtr]::Zero, [IntPtr]::Zero)
    if (-not (Wait-Exit $p $TimeoutSeconds $known)) { throw "yjks pid=$($p.Id) did not exit within $TimeoutSeconds s and showed no prompt." }
    "closed at $(Get-Date -Format HH:mm:ss)"
}

function Start-Yjk {
    if (Get-YjkProcess) { throw 'yjks is already running; close it first (or use -Action restart).' }
    if (-not (Test-Path $Exe)) { throw "yjks.exe not found at $Exe" }
    $argList = @()
    if ($Project) {
        if (-not (Test-Path $Project)) { throw "project not found: $Project" }
        $argList = @('"' + $Project + '"')
    }
    $p = if ($argList.Count) { Start-Process -FilePath $Exe -ArgumentList $argList -WorkingDirectory (Split-Path $Exe) -PassThru }
         else { Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -PassThru }
    "started yjks pid=$($p.Id)"
    $stem = if ($Project) { [IO.Path]::GetFileNameWithoutExtension($Project) } else { $null }
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        $p.Refresh()
        if ($p.HasExited) { throw "yjks exited during start (code $($p.ExitCode))." }
        $prompts = @(Get-YjkPrompts $p.Id @())
        if ($prompts.Count) { Write-Prompts $prompts; exit 2 }
        $main = Get-YjkMainWindow $p.Id
        if ($main -eq [IntPtr]::Zero) { continue }
        if ((Get-YjkCommandEdit $main) -eq [IntPtr]::Zero) { continue }
        $title = [YW]::Text($main)
        if ($stem -and $title -notlike "*$stem*") { continue }
        Start-Sleep -Seconds 3
        "ready at $(Get-Date -Format HH:mm:ss) title='$title'"
        return
    }
    throw "yjks did not become ready within $TimeoutSeconds s."
}

function Start-Gama {
    $p = Get-YjkProcess
    if (-not $p) { throw 'yjks is not running.' }
    if (@(Get-YjkTopWindows $p.Id | Where-Object { $_.Title -like '*Y-GAMA*' }).Count) { 'GAMA already open'; return }
    $known = @(Get-YjkTopWindows $p.Id | ForEach-Object { $_.Hwnd })
    $edit = Send-YjkCommand (Get-YjkMainWindow $p.Id) 'pgw_g'
    'sent pgw_g'
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 1500
        $line = [YW]::Text($edit)
        if ($line -like '*不支持无文档*') { throw "YJK refused pgw_g: '$line'. Open a project first (-Project)." }
        foreach ($w in @(Get-YjkPrompts $p.Id $known)) {
            $all = (@($w.Title) + $w.Texts) -join ' '
            if ($all -match $PreviousFilePattern) {
                $decline = $w.Buttons | Where-Object { $DeclineNames -contains $_ } | Select-Object -First 1
                if ($decline) {
                    "declining previous-file offer: '$all' -> '$decline'"
                    Invoke-YjkButton $w.Hwnd $decline
                    $known += $w.Hwnd
                    continue
                }
            }
            Write-Prompts @($w); exit 2
        }
        $gama = Get-YjkTopWindows $p.Id | Where-Object { $_.Title -like '*Y-GAMA*' } | Select-Object -First 1
        if ($gama) { "GAMA open at $(Get-Date -Format HH:mm:ss) title='$($gama.Title)'"; return }
    }
    throw "GAMA did not open within $TimeoutSeconds s."
}

switch ($Action) {
    'status' {
        $p = Get-YjkProcess
        if (-not $p) { 'yjks not running'; break }
        $main = Get-YjkMainWindow $p.Id
        "yjks pid=$($p.Id) started=$($p.StartTime) project='$([YW]::Text($main))'"
        Get-YjkTopWindows $p.Id | Where-Object { $_.Class -ne 'Internet Explorer_Hidden' } | ForEach-Object { "  window hwnd=$($_.Hwnd) class=$($_.Class) title='$($_.Title)'" }
        $e = Get-YjkCommandEdit $main
        if ($e -ne [IntPtr]::Zero) { "  command line: '$([YW]::Text($e))'" }
    }
    'close' { Close-Yjk }
    'start' { Start-Yjk }
    'gama' { Start-Gama }
    'restart' { Close-Yjk; Start-Yjk; Start-Gama }
    'prompts' {
        $p = Get-YjkProcess
        if (-not $p) { 'yjks not running'; break }
        $prompts = @(Get-YjkPrompts $p.Id @())
        if ($prompts.Count) { Write-Prompts $prompts } else { 'no prompt windows' }
    }
    'click' {
        if (-not $Hwnd -or -not $Button) { throw '-Hwnd and -Button are required for click.' }
        Invoke-YjkButton ([IntPtr]$Hwnd) $Button
        "clicked '$Button' in hwnd=$Hwnd"
    }
}
