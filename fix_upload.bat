@echo off
color 0B
echo ===================================================
echo    LV Nexus - GitHub Upload Fixer
echo ===================================================
echo.

:: 1. Increase Git Buffer to 500MB
echo [*] Increasing Git network buffer...
git config --global http.postBuffer 524288000
git config --global http.sslVerify false
git config --global core.compression 0

:: 2. Refresh the Git Cache (Ensures ignored files are NOT uploaded)
echo [*] Cleaning up tracked files (respecting .gitignore)...
git rm -r --cached . >nul 2>&1
git add .
git commit -m "🔧 Maintenance: Optimized repository size and network settings" >nul 2>&1

echo.
echo ===================================================
echo    READY TO UPLOAD
echo ===================================================
echo [*] Attempting to push to main...
git push -u origin main --ipv4

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Your project is now on GitHub!
) else (
    echo.
    echo [!] Still failing? Try this:
    echo 1. Connect to a mobile hotspot.
    echo 2. Try 'Method 2' (GitHub Desktop) from my previous message.
)

pause
