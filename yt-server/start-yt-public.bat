@echo off
title YT Server PUBLIC - Cho moi admin dung chung
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
    echo LOI: Khong thay Node.js! Cai o https://nodejs.org/ roi chay lai.
    pause
    exit /b 1
)
if not exist "..\tools\yt-dlp.exe" (
    echo LOI: Thieu tools\yt-dlp.exe!
    pause
    exit /b 1
)
if not exist "..\tools\ffmpeg.exe" (
    echo LOI: Thieu tools\ffmpeg.exe!
    pause
    exit /b 1
)
if not exist "..\tools\cloudflared.exe" (
    echo LOI: Thieu tools\cloudflared.exe!
    pause
    exit /b 1
)
echo Mo server + mo cong ra internet...
echo GIU CA 2 CUA SO NAY MO khi muon moi admin dung duoc.
echo.
start "YT Server - May chu tai" node server.js
timeout /t 3 /nobreak >nul
"..\tools\cloudflared.exe" tunnel --url http://127.0.0.1:8799
pause
