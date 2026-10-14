@echo off
title YT Server - Tailscale rieng (nhanh, on dinh)
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
where tailscale >nul 2>nul
if errorlevel 1 (
    echo LOI: Chua cai Tailscale. Cai o https://tailscale.com/download/windows
    echo      roi mo app Tailscale dang nhap (Google/Microsoft) truoc.
    pause
    exit /b 1
)
tailscale status >nul 2>nul
if errorlevel 1 (
    echo LOI: Tailscale chua dang nhap. Mo app Tailscale (goc phai man hinh) dang nhap truoc.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('tailscale ip -4') do set TSIP=%%i
echo.
echo ============================================================
echo  Dia chi CO DINH de dan vao o may chu tren admin/đien thoai:
echo      http://%TSIP%:8799
echo  (Chi dan 1 LAN DUY NHAT, mo tat bao nhieu lan cung khong doi)
echo  Dien thoai cai Tailscale + dang nhap CUNG tai khoan nay.
echo ============================================================
echo.
echo Giua cua so nay + cua so server mo khi muon dung.
echo.
start "YT Server - May chu tai" node server.js
pause
