@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 deploy\local_control.py start
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3를 먼저 설치해 주세요. docs\PERSONAL_RECOVERY.md를 확인하세요.
    pause
    exit /b 1
  )
  python deploy\local_control.py start
)
if errorlevel 1 pause
