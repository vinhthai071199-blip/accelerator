@echo off
title YT Server - Tailscale (dia chi co dinh, khong doi)
cd /d "%~dp0"
powershell -NoProfile -Command "try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',8799); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 (
    echo LOI: Cong 8799 dang ban (cua so server cu van chay)! Tat het cua so server cu roi chay lai.
    pause
    exit /b 1
)
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
where tailscale >nul 2>nul
if errorlevel 1 (
    echo LOI: Chua cai Tailscale! Cai o https://tailscale.com/download/windows
    echo      roi mo app Tailscale dang nhap (Google/Microsoft) truoc.
    pause
    exit /b 1
)
tailscale status >nul 2>nul
if errorlevel 1 (
    echo LOI: Tailscale chua dang nhap! Mo app Tailscale (goc phai man hinh) dang nhap truoc.
    pause
    exit /b 1
)
echo Mo server + mo cong Tailscale (dia chi CO DINH, khong doi moi lan mo)...
echo GIU CA 2 CUA SO NAY MO khi muon moi admin dung duoc.
echo.
start "YT Server - May chu tai" node server.js
timeout /t 3 /nobreak >nul
tailscale funnel 8799
pause
