# Win32 + UI Automation helpers for driving YJK (yjks.exe) and GAMA. Dot-source this file.
# Saved as UTF-8 with BOM: Windows PowerShell 5.1 reads BOM-less files as ANSI and breaks the Chinese literals.
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
if (-not ('YW' -as [type])) {
Add-Type -TypeDefinition @"
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class YW {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, int msg, IntPtr w, StringBuilder l);
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, int msg, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, int msg, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr h);
  public static List<IntPtr> Tops(uint pid) { var l = new List<IntPtr>(); EnumWindows((h, x) => { uint p; GetWindowThreadProcessId(h, out p); if (p == pid && IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero); return l; }
  public static List<IntPtr> Children(IntPtr p) { var l = new List<IntPtr>(); EnumChildWindows(p, (h, x) => { l.Add(h); return true; }, IntPtr.Zero); return l; }
  public static string Cls(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
  public static string Text(IntPtr h) { var s = new StringBuilder(2048); SendMessage(h, 0x000D, (IntPtr)2048, s); return s.ToString(); }
}
"@
}

$script:WM_CLOSE = 0x0010; $script:WM_CHAR = 0x0102
$script:WM_KEYDOWN = 0x0100; $script:WM_KEYUP = 0x0101; $script:VK_RETURN = 0x0D

function Get-YjkProcess { Get-Process yjks -ErrorAction SilentlyContinue | Select-Object -First 1 }

# YJK's own frame (class 'yjks'). Do not use Process.MainWindowHandle: once GAMA is open .NET reports GAMA's form.
function Get-YjkMainWindow([int]$ProcessId) {
    foreach ($h in [YW]::Tops([uint32]$ProcessId)) { if ([YW]::Cls($h) -eq 'yjks') { return $h } }
    return [IntPtr]::Zero
}

# Visible top-level windows of the process.
function Get-YjkTopWindows([int]$ProcessId) {
    foreach ($h in [YW]::Tops([uint32]$ProcessId)) {
        [pscustomobject]@{ Hwnd = [long]$h; Class = [YW]::Cls($h); Title = [YW]::Text($h) }
    }
}

# The command-line Edit: class Edit whose parent is the QChildWnd titled 命令行. Its text is the current prompt
# (normally '命令:'); YJK writes refusals into it, e.g. '<该命令不支持无文档状态下执行！>命令:'.
function Get-YjkCommandEdit([IntPtr]$MainHwnd) {
    foreach ($h in [YW]::Children($MainHwnd)) {
        if ([YW]::Cls($h) -eq 'Edit' -and [YW]::Text([YW]::GetParent($h)) -eq '命令行') { return $h }
    }
    return [IntPtr]::Zero
}

# Types a command into YJK's command line and presses Enter. Posting WM_CHAR works without focus.
function Send-YjkCommand([IntPtr]$MainHwnd, [string]$Command) {
    $edit = Get-YjkCommandEdit $MainHwnd
    if ($edit -eq [IntPtr]::Zero) { throw 'YJK command-line Edit not found.' }
    foreach ($ch in $Command.ToCharArray()) { [void][YW]::PostMessage($edit, $script:WM_CHAR, [IntPtr][int]$ch, [IntPtr]1) }
    [void][YW]::PostMessage($edit, $script:WM_KEYDOWN, [IntPtr]$script:VK_RETURN, [IntPtr]1)
    [void][YW]::PostMessage($edit, $script:WM_CHAR, [IntPtr]$script:VK_RETURN, [IntPtr]1)
    [void][YW]::PostMessage($edit, $script:WM_KEYUP, [IntPtr]$script:VK_RETURN, [IntPtr]0xC0000001)
    return $edit
}

# Windows that are never prompts: YJK main, its work-tree float, GAMA's main form, IE helper, WPF splash/progress.
function Test-YjkFixedWindow($w) {
    return $w.Class -in @('yjks', 'QFloatWnd', 'Internet Explorer_Hidden') `
        -or $w.Title -like '*Y-GAMA*' -or $w.Title -eq 'ProgressBarWindow'
}

# Top-level windows (not in $Known, not fixed) that carry at least one button: message boxes, Win32 dialogs and
# WPF/WinForms prompts alike. Read through UI Automation so WPF content is visible.
function Get-YjkPrompts([int]$ProcessId, $Known) {
    $A = [System.Windows.Automation.AutomationElement]
    $buttonCond = New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
    $textCond = New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty, [System.Windows.Automation.ControlType]::Text)
    foreach ($w in Get-YjkTopWindows $ProcessId) {
        if ($Known -contains $w.Hwnd -or (Test-YjkFixedWindow $w)) { continue }
        try {
            $e = $A::FromHandle([IntPtr]$w.Hwnd)
            $buttons = @($e.FindAll([System.Windows.Automation.TreeScope]::Descendants, $buttonCond) | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
            if (-not $buttons.Count) { continue }
            $texts = @($e.FindAll([System.Windows.Automation.TreeScope]::Descendants, $textCond) | ForEach-Object { $_.Current.Name } | Where-Object { $_ } | Select-Object -First 20)
            [pscustomobject]@{ Hwnd = $w.Hwnd; Class = $w.Class; Title = $w.Title; Texts = $texts; Buttons = $buttons }
        } catch { }
    }
}

# Presses a named button in a top-level window through UI Automation (Invoke pattern).
function Invoke-YjkButton([IntPtr]$WindowHwnd, [string]$Name) {
    $A = [System.Windows.Automation.AutomationElement]
    $cond = New-Object System.Windows.Automation.AndCondition(
        (New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)),
        (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $Name)))
    $b = $A::FromHandle($WindowHwnd).FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
    if (-not $b) { throw "button '$Name' not found in hwnd=$WindowHwnd" }
    $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
}
