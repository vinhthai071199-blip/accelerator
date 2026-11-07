@echo off
chcp 65001 >nul
title AcceleratorAres - Tu Deploy
echo ============================================
echo   ACCELERATORARES - TU DEPLOY LEN WEB
echo ============================================
echo.

set REPO_DIR=%~dp0
cd /d "%REPO_DIR%"

REM PowerShell chan chay .ps1 -> luon dung file .cmd de tranh loi "Not authorized"
set VERCEL=vercel.cmd
where vercel.cmd >nul 2>&1
if errorlevel 1 set VERCEL=vercel

echo [0/4] Kiem tra dang nhap Vercel...
%VERCEL% whoami
if errorlevel 1 (
    echo.
    echo LOI: Chua dang nhap Vercel. Chay: %VERCEL% login
    pause
    exit /b 1
)
echo       OK.

echo [1/4] Chuan bi file...
echo       Dung Acceleratorares.html co san.
echo       Xong.

echo [2/4] Luu len GitHub...
git add -A
git -c user.name="vinhthai071199-blip" -c user.email="vinhthai071199-blip@users.noreply.github.com" commit -m "Update website"
if errorlevel 1 (
    echo       Khong co thay doi de commit, bo qua.
)
git push origin master
if errorlevel 1 (
    echo.
    echo LOI: Push that bai. Kiem tra mang hoac quyen GitHub.
    pause
    exit /b 1
)
echo       Xong.

echo [3/4] Deploy len Vercel (cho khoang 30 giay)...
%VERCEL% deploy --prod --yes
if errorlevel 1 (
    echo.
    echo LOI: Deploy that bai. Thu: %VERCEL% login
    pause
    exit /b 1
)

echo.
echo ============================================
echo   DEPLOY THANH CONG!
echo   https://acceleratorares.vercel.app/
echo   (Neu chua thay doi, nhan Ctrl+F5)
echo ============================================
echo.
start "" "https://acceleratorares.vercel.app/"
pause
