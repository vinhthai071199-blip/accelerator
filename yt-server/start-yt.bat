@echo off
title YT Server - May chu tai video cua ban
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
    echo LOI: Khong thay Node.js! Cai o https://nodejs.org/ roi chay lai.
    pause
    exit /b 1
)
if not exist "..\tools\yt-dlp.exe" (
    echo LOI: Thieu tools\yt-dlp.exe! Tai o https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe
    echo      roi bo vao thu muc tools.
    pause
    exit /b 1
)
if not exist "..\tools\ffmpeg.exe" (
    echo LOI: Thieu tools\ffmpeg.exe! Tai ban essentials o https://www.gyan.dev/ffmpeg/builds/
    echo      giai nen lay ffmpeg.exe bo vao thu muc tools.
    pause
    exit /b 1
)
echo Giua cua so nay mo de admin tai video. Tat cua so = tat server.
echo.
node server.js
pause
