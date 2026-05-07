@echo off
color 0B
echo ===================================================
echo    LV Nexus - Final GitHub Identity Setup
echo ===================================================
echo.

:: 1. Setup Git Identity
echo [*] Configuring Git Identity...
git config --global user.email "avresort0@gmail.com"
git config --global user.name "avresort0"

:: 2. Setup SSH Remote
echo [*] Setting remote to SSH...
git remote set-url origin git@github.com:avresort0-oss/LV-Nexus.git

:: 3. Network Fixes
git config --global http.postBuffer 524288000
git config --global core.compression 0

echo.
echo ===================================================
echo    IDENTITY SET UP SUCCESSFULLY
echo ===================================================
echo.
echo [*] Attempting to push project...
git add .
git commit -m "🚀 Production Release: LV Nexus v2.1.0"
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Your project is now live on GitHub!
) else (
    echo.
    echo [!] Upload failed. This is usually because your SSH Key 
    echo     is not added to your GitHub account.
    echo.
    echo To fix this:
    echo 1. Open PowerShell and run: ssh-keygen -t ed25519 -C "avresort0@gmail.com"
    echo 2. Press Enter 3 times.
    echo 3. Go to C:\Users\Admin\.ssh\id_ed25519.pub and copy the text.
    echo 4. Add it to https://github.com/settings/keys
)

pause
