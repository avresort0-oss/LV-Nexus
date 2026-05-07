@echo off
color 0D
echo ===================================================
echo    LV Nexus - SSH Upload Script
echo ===================================================
echo.

:: 1. Set Remote to SSH
echo [*] Switching to SSH protocol...
git remote set-url origin git@github.com:avresort0-oss/LV-Nexus.git

:: 2. Network Optimizations
git config --global core.compression 0
git config --global http.postBuffer 524288000

:: 3. Attempt Upload
echo [*] Pushing to GitHub via SSH...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Project uploaded via SSH!
) else (
    echo.
    echo [!] SSH Push failed. 
    echo Make sure you have added your SSH Key to GitHub:
    echo https://github.com/settings/keys
)

pause
