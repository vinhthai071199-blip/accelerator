@echo off
title YT Server - May chu tai video cua ban
cd /d "%~dp0"
powershell -NoProfile -Command "try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',8799); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 (
    echo LOI: Cong 8799 dang ban (cua so server cu van chay). Tat het cua so server cu roi chay lai.
    pause
    exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
    echo LOI: Khong thay Node.js. Cai o https://nodejs.org/ roi chay lai.
    pause
    exit /b 1
)
if not exist "..\tools\yt-dlp.exe" (
    echo LOI: Thieu tools\yt-dlp.exe. Tai o https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe
    echo      roi bo vao thu muc tools.
    pause
    exit /b 1
)
if not exist "..\tools\ffmpeg.exe" (
    echo LOI: Thieu tools\ffmpeg.exe. Tai ban essentials o https://www.gyan.dev/ffmpeg/builds/
    echo      giai nen lay ffmpeg.exe bo vao thu muc tools.
    pause
    exit /b 1
)
echo Giua cua so nay mo de admin tai video. Tat cua so = tat server.
echo.
node server.js
pause
