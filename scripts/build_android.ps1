# Moodwave Android PowerShell Build Script
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$AndroidDir = Join-Path $ProjectRoot "android"

Write-Host "=== Building Moodwave Android Application (Debug) ===" -ForegroundColor Cyan
Write-Host "Android Directory: $AndroidDir"

Set-Location -Path $AndroidDir

$GradleBat = Join-Path $AndroidDir "gradlew.bat"
if (Test-Path $GradleBat) {
    & $GradleBat assembleDebug $args
} else {
    Write-Error "gradlew.bat not found in $AndroidDir"
    exit 1
}
