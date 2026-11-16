---
name: yjk-gama-restart
description: Use when a test task needs YJK (yjks.exe) closed, started or restarted, or GAMA (Y-GAMA) started through YJK's pgw_g command — e.g. before deploying NSMcp DLLs, after a deploy, or to get the NSMcp host (port 52312) back for a live check. Not for production projects.
---

# Close / start YJK and start GAMA

The user allowed this on 2026-11-07 **for test tasks only**. Live tests run on the copy
`E:\2026\20261104mcptest\m.yjk`; never open or calculate a source project.

One script does everything, driving YJK's Win32 window with no keyboard focus or mouse:

```powershell
$y = "$env:USERPROFILE\.claude\skills\yjk-gama-restart\scripts\yjk-gama.ps1"
& $y -Action status                                   # process, windows, command-line text
& $y -Action close                                    # WM_CLOSE to YJK's frame, wait for exit
& $y -Action start -Project 'E:\2026\20261104mcptest\m.yjk'   # yjks.exe "<project>", wait for its command line
& $y -Action gama                                     # type pgw_g + Enter into the command line, wait for Y-GAMA
& $y -Action restart -Project 'E:\2026\20261104mcptest\m.yjk' # close + start + gama
& $y -Action prompts                                  # list open prompt windows (title, texts, buttons)
& $y -Action click -Hwnd <hwnd> -Button '<name>'      # press one button in a listed prompt
```

Run it in the PowerShell tool (Windows PowerShell 5.1) in the foreground, with a timeout of about 400000 ms for
`restart`. Measured on 2026-11-07: close takes about 1 s, start with a project about 25 s, and GAMA opens about 12 s
after `pgw_g`.

## Rules

- **`pgw_g` needs an open project.** With no document YJK writes
  `<该命令不支持无文档状态下执行！>命令:` into the command line and nothing starts. Always pass `-Project`; YJK opens a
  `.yjk` given as its first argument.
- **Never open a previous file in GAMA.** `-Action gama` declines a prompt whose text mentions
  上次/之前/最近/恢复/previous/recent/last/restore, by pressing 否/不打开/取消/No/Cancel/新建. GAMA normally opens
  "新文件" with no prompt.
- **Any other prompt stops the script** with its title, texts and buttons on stdout, for example a save-changes
  question on close. Read it, then decide:
  - On the test copy, a save question on close is answered 否 (do not write the project):
    `-Action click -Hwnd <hwnd> -Button 否`, then run `-Action close` again.
  - Anything unclear (licence, crash report, a question about a non-test project): stop and ask the user.
- Never stop ConsoleLauncher, devenv or test hosts. This skill only closes `yjks`.
- GAMA runs inside the `yjks` process, so closing YJK closes GAMA. The NSMcp host (`http://127.0.0.1:52312/mcp`)
  comes back once YJK has a project open. Check it with `get_runtime_capabilities`: `OpenProjectPath` and
  `OpenProjectGeneration` (the generation restarts at 1).
- After a restart, MCP calls that are guarded by `execute_tool` need `expectedHostProjectPath` (the folder root, e.g.
  `E:\2026\20261104mcptest\m`) and `expectedHostProjectGeneration` at the top level, beside `toolName`. The session
  token is in `%LOCALAPPDATA%\NSMcp\session.token` (header `X-NSMCP-Token`).

## How it works (if YJK changes)

- **YJK's frame** is the top-level window of class `yjks`. Do not use `Process.MainWindowHandle`: once GAMA is
  open, .NET returns GAMA's WinForms form.
- **The command line** is a Win32 `Edit` control, the child of the `QChildWnd` titled `命令行` (inside a
  `QControlBar`). Its text is the prompt `命令:`; the history is the sibling `ListBox`. Commands are posted as
  `WM_CHAR` per character, then `WM_KEYDOWN`/`WM_CHAR`/`WM_KEYUP` for `VK_RETURN`. No focus is needed.
- **GAMA's main window** is a WinForms form titled `盈建科数字化智能设计软件 Y-GAMA - <file>`. While it loads it shows
  WPF `HwndWrapper` windows (`ProgressBarWindow` and an untitled container). These have no buttons and are not prompts.
- **Prompts** are found through UI Automation: any new top-level window of the process with at least one Button.
  This covers Win32 `#32770`, WinForms and WPF dialogs alike. Buttons are pressed through UIA's `InvokePattern`.
- Both scripts are saved as **UTF-8 with BOM**. PowerShell 5.1 reads BOM-less files as ANSI and corrupts the
  Chinese literals. Keep the BOM when you edit them.
