# ============================================================
# JRJ AI Assistant - One-Click APK Build Script
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  JRJ AI Assistant - Building Android APK" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Locate or set Java 17
$JavaCandidates = @(
    "C:\Users\USER X\.jdk17\jdk-17.0.20.1+1",
    "C:\Program Files\Android\Android Studio\jbr",
    $env:JAVA_HOME
)

$FoundJava = $null
foreach ($cand in $JavaCandidates) {
    if ($cand -and (Test-Path "$cand\bin\javac.exe")) {
        $FoundJava = $cand
        break
    }
}

if (-not $FoundJava) {
    Write-Error "Could not locate JDK 17 with javac.exe. Please set JAVA_HOME."
}

$env:JAVA_HOME = $FoundJava
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
Write-Host "Using JDK: $env:JAVA_HOME" -ForegroundColor Green

Set-Location "$PSScriptRoot\android"

Write-Host "Running Gradle assembleDebug..." -ForegroundColor Yellow
.\gradlew.bat assembleDebug

$ApkPath = "$PSScriptRoot\android\app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path $ApkPath) {
    Write-Host "`nAPK BUILT SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "APK Location: $ApkPath" -ForegroundColor Cyan
    $Size = (Get-Item $ApkPath).Length / 1MB
    Write-Host ("Size: {0:N2} MB" -f $Size) -ForegroundColor Yellow
} else {
    Write-Host "`nBuild completed, please check outputs directory." -ForegroundColor Yellow
}
