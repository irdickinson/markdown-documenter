# build.ps1 — package Markdown Documenter into a Windows exe
# Usage: .\build.ps1 [-Version "1.0.0"]
param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$ZipName = "MarkdownDocumenter-v$Version-win64.zip"
$DistDir = "dist\MarkdownDocumenter"

Write-Host "==> Cleaning previous build..." -ForegroundColor Cyan
if (Test-Path "dist")  { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

Write-Host "==> Running PyInstaller..." -ForegroundColor Cyan
pyinstaller markdown-documenter.spec
if (-not $?) { Write-Host "PyInstaller failed." -ForegroundColor Red; exit 1 }

Write-Host "==> Creating output folder inside bundle..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force "$DistDir\output" | Out-Null

Write-Host "==> Zipping $DistDir -> $ZipName..." -ForegroundColor Cyan
if (Test-Path $ZipName) { Remove-Item $ZipName }
Compress-Archive -Path $DistDir -DestinationPath $ZipName

Write-Host ""
Write-Host "Done!  ->  $ZipName" -ForegroundColor Green
Write-Host ""
Write-Host "To create a GitHub Release:" -ForegroundColor Yellow
Write-Host "  gh release create v$Version `"$ZipName`" --title `"Markdown Documenter v$Version`" --notes `"Initial release of Markdown Documenter`"" -ForegroundColor White
