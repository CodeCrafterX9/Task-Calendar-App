@echo off
cd /d "%~dp0"

title Task Calendar Builder

echo ==========================================
echo       TASK CALENDAR - EXE BUILDER
echo ==========================================
echo.

echo Building from:
echo %CD%
echo.

python -m PyInstaller --noconfirm --clean --onefile --windowed --name TaskCalendar "dayflow.py"

if errorlevel 1 (
    echo.
    echo ==========================================
    echo BUILD FAILED!
    echo ==========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo BUILD SUCCESSFUL!
echo ==========================================
echo.

echo EXE location:
echo %CD%\dist\TaskCalendar.exe
echo.

explorer "%CD%\dist"

pause
