@echo off
title YT Server PUBLIC - Tu nuoi tunnel
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
    echo LOI: Thieu tools\yt-dlp.exe.
    pause
    exit /b 1
)
if not exist "..\tools\ffmpeg.exe" (
    echo LOI: Thieu tools\ffmpeg.exe.
    pause
    exit /b 1
)
if not exist "..\tools\cloudflared.exe" (
    echo LOI: Thieu tools\cloudflared.exe.
    pause
    exit /b 1
)
echo Mo server + tu nuoi tunnel (chet tu dung lai, doi link tu cap nhat web).
echo GIU CUA SO NAY MO khi muon moi admin dung duoc.
echo Dia chi public xem trong yt-server\tun-url.txt
echo.
set YT_TUNNEL=1
node server.js
pause
