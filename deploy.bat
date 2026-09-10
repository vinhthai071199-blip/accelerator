@echo off
chcp 65001 >nul
title AcceleratorAres - Tu Deploy
echo ============================================
echo   ACCELERATORARES - TU DEPLOY LEN WEB
echo ============================================
echo.

set REPO_DIR=%~dp0
cd /d "%REPO_DIR%"

echo [1/4] Chuan bi file...
if exist "%REPO_DIR%Acceleratorares.html" (
    copy /Y "%REPO_DIR%Acceleratorares.html" "%REPO_DIR%index.html" >nul
    echo       Lay tu Acceleratorares.html.
) else (
    echo       Dung index.html co san.
)
echo       Xong.

echo [2/4] Luu len GitHub...
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
    echo LOI: Deploy that bai. Neu moi cai lai may, chay: vercel login
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
