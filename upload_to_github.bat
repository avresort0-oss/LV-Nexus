@echo off
color 0A
echo ===================================================
echo     LV Nexus - Auto GitHub Uploader (Premium)
echo ===================================================
echo.

:: Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed! Download from https://git-scm.com/downloads
    pause
    exit /b
)

:: Setup Git commit
echo [*] Setting up Git...
git add .
git commit -m "🚀 Initial Release: LV Nexus v2.1.0 - Premium Edition" >nul 2>&1
git branch -M main >nul 2>&1

:: Check if GitHub CLI (gh) is installed
gh --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] GitHub CLI detected! Creating repository automatically...
    echo [*] Checking authentication...
    gh auth status >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] You are not logged into GitHub CLI. 
        echo [!] Please run this command first: gh auth login
        pause
        exit /b
    )
    
    echo [*] Creating 'LV-Nexus' repository and uploading...
    gh repo create LV-Nexus --public --source=. --remote=origin --push
    
    if %errorlevel% equ 0 (
        echo ===================================================
        echo     SUCCESS! Automatically uploaded to your GitHub!
        echo ===================================================
        pause
        exit /b
    )
)

:: Fallback if GitHub CLI is not installed or failed
echo.
echo [!] GitHub CLI not found or failed. We will use the direct URL method.
echo [!] Please go to https://github.com/new and create an empty repository named 'LV-Nexus'
echo.
set /p REPO_URL="Enter your EXACT GitHub Repository URL (e.g. https://github.com/avresort0-oss/LV-Nexus.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] You didn't enter a URL! Please try again and paste the link.
    pause
    exit /b
)

echo [*] Linking to GitHub...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo [*] Uploading to GitHub (Please wait)...
git push -u origin main

if %errorlevel% equ 0 (
    echo ===================================================
    echo     SUCCESS! Project uploaded successfully!
    echo ===================================================
) else (
    echo ===================================================
    echo     FAILED! Make sure the repository exists on GitHub.
    echo ===================================================
)
pause
