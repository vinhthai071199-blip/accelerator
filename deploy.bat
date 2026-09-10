@echo off
chcp 65001 >nul
title AcceleratorAres - Tu Deploy
echo ============================================
echo   ACCELERATORARES - TU DEPLOY LEN WEB
echo ============================================
echo.

set SRC_DIR=%~dp0
set REPO_DIR=D:\Opencode Project

echo [1/4] Copy file vao thu muc lam viec...
copy /Y "%SRC_DIR%Acceleratorares.html" "%REPO_DIR%\index.html" >nul
copy /Y "%SRC_DIR%admin.html" "%REPO_DIR%\admin.html" >nul
copy /Y "%SRC_DIR%avatar.jpg" "%REPO_DIR%\avatar.jpg" >nul
copy /Y "%SRC_DIR%shop-logo.jpg" "%REPO_DIR%\shop-logo.jpg" >nul
if errorlevel 1 (
    echo LOI: Khong copy duoc file!
    pause
    exit /b 1
)
echo       Xong.

echo [2/4] Luu len GitHub...
cd /d "%REPO_DIR%"
git add -A
git -c user.name="vinhthai071199-blip" -c user.email="vinhthai071199-blip@users.noreply.github.com" commit -m "Update website"
git push origin master
if errorlevel 1 (
    echo.
    echo LOI: Push that bai. Kiem tra mang.
    pause
    exit /b 1
)
echo       Xong.

echo [3/4] Deploy len Vercel (cho khoang 30 giay)...
call vercel deploy --prod --yes
if errorlevel 1 (
    echo.
    echo LOI: Deploy that bai.
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
