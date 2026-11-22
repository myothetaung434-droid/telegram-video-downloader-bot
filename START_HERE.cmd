@echo off
setlocal
cd /d "%~dp0"
title Telegram Video Downloader Bot
where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell is not available.
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_windows.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo Startup finished with an error. See the message above.
echo Press any key to close this window.
pause >nul
exit /b %RESULT%