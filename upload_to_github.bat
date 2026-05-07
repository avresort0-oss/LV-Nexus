@echo off
color 0A
echo ===================================================
echo     LV Nexus - Premium GitHub Uploader
echo ===================================================
echo.

:: Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed on your system!
    echo Please install Git from https://git-scm.com/downloads
    pause
    exit /b
)

:: Initialize Git
echo [*] Initializing Git repository...
git init

:: Add all files
echo [*] Adding files to Git...
git add .

:: Commit
echo [*] Committing files...
git commit -m "🚀 Initial Release: LV Nexus v2.1.0 - Premium Edition"

:: Get GitHub URL from user
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/avresort0-oss/LV-Nexus.git): "

:: Setup branch and remote
echo [*] Setting up main branch...
git branch -M main

echo [*] Linking to GitHub...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

:: Push to GitHub
echo [*] Uploading to GitHub (Please wait)...
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ===================================================
    echo     SUCCESS! Project uploaded successfully!
    echo ===================================================
) else (
    echo ===================================================
    echo     FAILED! Please check the error message above.
    echo ===================================================
)
pause
