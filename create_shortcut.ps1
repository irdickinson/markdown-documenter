# create_shortcut.ps1 — creates a desktop shortcut to MarkdownDocumenter.exe
# Run this once after unzipping the release, from inside the MarkdownDocumenter folder.

$ExePath = Join-Path $PSScriptRoot "MarkdownDocumenter.exe"
$Desktop  = [System.Environment]::GetFolderPath("Desktop")
$LnkPath  = Join-Path $Desktop "Markdown Documenter.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($LnkPath)
$Shortcut.TargetPath       = $ExePath
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description      = "Markdown Documenter"
$Shortcut.Save()

Write-Host "Shortcut created at: $LnkPath" -ForegroundColor Green
