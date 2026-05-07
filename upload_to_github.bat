@echo off
color 0A
echo ===================================================
echo     LV Nexus - Premium GitHub Uploader (Network Fix)
echo ===================================================
echo.

:: Setup Git
git add .
git commit -m "🚀 Initial Release: LV Nexus v2.1.0 - Premium Edition" >nul 2>&1
git branch -M main >nul 2>&1

:: Network Fixes
git config --global http.postBuffer 524288000
git config --global http.sslVerify false
git config --global core.compression 0

echo [*] Opening your browser to create a new repository...
timeout /t 2 >nul
start https://github.com/new

echo.
echo ===================================================
echo 1. Your browser should now be open on GitHub.
echo 2. Make sure you are logged into 'avresort0-oss'.
echo 3. Enter 'LV-Nexus' as the Repository Name.
echo 4. Click "Create repository" at the bottom.
echo 5. Copy the link (e.g. https://github.com/avresort0-oss/LV-Nexus.git)
echo ===================================================
echo.

set /p REPO_URL="Paste your GitHub Link here and press Enter: "

if "%REPO_URL%"=="" (
    echo [ERROR] You didn't enter a link! Please run the file again.
    pause
    exit /b
)

echo [*] Linking to GitHub...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo [*] Uploading your project (Attempt 1)...
git push -u origin main

if %errorlevel% neq 0 (
    echo [!] Network failed. Trying again using IPv4...
    timeout /t 3 >nul
    git push -u origin main --ipv4
)

if %errorlevel% equ 0 (
    echo ===================================================
    echo     SUCCESS! Project uploaded successfully!
    echo ===================================================
) else (
    echo ===================================================
    echo     FAILED! Your internet might be blocking GitHub.
    echo     Try connecting to a different Wi-Fi or Hotspot.
    echo ===================================================
)
pause
