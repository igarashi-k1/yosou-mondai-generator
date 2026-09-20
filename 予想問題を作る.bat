@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

echo Generating new practice questions...
echo.

where python >nul 2>nul
if not errorlevel 1 (
    set "PYCMD=python"
    goto :run
)
where py >nul 2>nul
if not errorlevel 1 (
    set "PYCMD=py"
    goto :run
)

echo [ERROR] Python was not found on this computer.
echo Please install Python from https://www.python.org/downloads/
echo and make sure to check "Add python.exe to PATH" during setup.
echo.
pause
exit /b 1

:run
"%PYCMD%" generate_yosou_mondai.py --count 25
if errorlevel 1 (
    echo.
    echo [ERROR] Question generation failed. See the message above.
    pause
    exit /b 1
)

echo.
echo Done. If the browser did not open automatically, double-click
echo the newest .html file in this folder to open it.
echo.
pause
