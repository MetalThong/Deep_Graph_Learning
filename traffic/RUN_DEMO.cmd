@echo off
cd /d "%~dp0"
if exist "..\demo\.venv\Scripts\python.exe" (
  "..\demo\.venv\Scripts\python.exe" run_demo.py
) else (
  py -3 --version >nul 2>&1
  if not errorlevel 1 (
    py -3 run_demo.py
  ) else (
    python run_demo.py
  )
)
pause
